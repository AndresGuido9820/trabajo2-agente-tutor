"""Cliente del LLM: interfaz, implementación OpenAI y salida JSON validada.

El código de negocio depende solo del protocolo ``ClienteLLM``; el proveedor
concreto (OpenAI) vive únicamente aquí (decisión en docs/INVESTIGACION.md §2).
Estrategia de errores (HU-02): reintentos con backoff exponencial para fallas
transitorias (conexión, 429, 5xx) y fallo inmediato para errores de cliente
(401, 400). La API key nunca se registra en logs.
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from collections.abc import Callable, Iterator
from typing import Any, Protocol

from openai import APIConnectionError, APIStatusError, OpenAI

from tutor.config import (
    BASE_BACKOFF_SEGUNDOS,
    MAX_REINTENTOS_API,
    MAX_REINTENTOS_PARSEO,
    MAX_TOKENS_RESPUESTA,
    TIMEOUT_API_SEGUNDOS,
    Configuracion,
)
from tutor.nucleo.errores import ErrorLLM
from tutor.persistencia import db

logger = logging.getLogger(__name__)

_CODIGOS_REINTENTABLES = frozenset({429})


class ClienteLLM(Protocol):
    """Contrato mínimo que el resto del código conoce del LLM."""

    def generar(self, system: str, prompt: str, carril: str = "potente") -> str:
        """Envía un prompt y devuelve el texto de la respuesta.

        ``carril`` elige el modelo (HU-39): "potente" para generaciones
        estructuradas, "chat" para turnos conversacionales.
        """
        ...

    def generar_stream(
        self, system: str, prompt: str, carril: str = "potente"
    ) -> Iterator[str]:
        """Como ``generar`` pero emite la respuesta en fragmentos (HU-35)."""
        ...


def espera_backoff(intento: int, azar: Callable[[], float] = random.random) -> float:
    """Calcula la espera del reintento ``intento`` (base 0) con jitter.

    Exponencial: ``base * 2**intento``, multiplicada por un factor aleatorio
    en [0.5, 1.5) para evitar reintentos sincronizados.
    """
    return BASE_BACKOFF_SEGUNDOS * (2.0**intento) * (0.5 + azar())


class _RespuestaVacia(Exception):
    """Respuesta sin contenido (interno; se reintenta como error transitorio)."""


def _es_reintentable(error: Exception) -> bool:
    """Decide si un error del SDK amerita reintento."""
    if isinstance(error, APIConnectionError | _RespuestaVacia):
        return True
    if isinstance(error, APIStatusError):
        codigo = error.status_code
        return codigo in _CODIGOS_REINTENTABLES or codigo >= 500
    return False


def _describir(error: Exception) -> str:
    """Mensaje corto y sin secretos para mostrar al usuario."""
    if isinstance(error, APIStatusError):
        return f"la API respondió {error.status_code}"
    if isinstance(error, APIConnectionError):
        return "no se pudo conectar con la API"
    if isinstance(error, _RespuestaVacia):
        return "la API devolvió una respuesta vacía"
    return type(error).__name__


class ClienteOpenAI:
    """Implementación de ``ClienteLLM`` sobre la API de OpenAI.

    Args:
        configuracion: Configuración efectiva (api key, modelo).
        cliente: Cliente del SDK ya construido (inyectable para pruebas).
        dormir: Función de espera (inyectable para pruebas sin demoras).
    """

    def __init__(
        self,
        configuracion: Configuracion,
        cliente: OpenAI | None = None,
        dormir: Callable[[float], None] = time.sleep,
        registrar: Callable[..., None] | None = None,
    ) -> None:
        """Inicializa el cliente; si no se inyecta SDK, lo crea con timeout.

        Args:
            configuracion: Configuración efectiva (api key, modelos).
            cliente: Cliente del SDK ya construido (inyectable para pruebas).
            dormir: Función de espera (inyectable para pruebas sin demoras).
            registrar: Hook de registro de uso; por defecto anota en la BD
                global ``dir_datos/uso.db`` (HU-39). Nunca rompe la llamada.
        """
        self._modelos = {
            "potente": configuracion.modelo,
            "chat": configuracion.modelo_chat or configuracion.modelo,
        }
        self._cliente = cliente or OpenAI(
            api_key=configuracion.api_key, timeout=TIMEOUT_API_SEGUNDOS
        )
        self._dormir = dormir
        ruta_uso = configuracion.dir_datos / "uso.db"
        self._registrar = registrar or (
            lambda **campos: db.anotar_uso(ruta_uso, **campos)
        )

    def generar(self, system: str, prompt: str, carril: str = "potente") -> str:
        """Envía un prompt con reintentos y devuelve el texto de la respuesta.

        Raises:
            ErrorLLM: Ante error no reintentable, respuesta vacía o al agotar
                ``MAX_REINTENTOS_API`` intentos.
        """
        modelo = self._modelos.get(carril, self._modelos["potente"])
        ultimo_error: Exception | None = None
        for intento in range(MAX_REINTENTOS_API):
            inicio = time.monotonic()
            try:
                respuesta = self._cliente.chat.completions.create(
                    model=modelo,
                    max_completion_tokens=MAX_TOKENS_RESPUESTA,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                )
                contenido = respuesta.choices[0].message.content
                if not contenido:
                    # Ocurre cuando el modelo agota el presupuesto en tokens
                    # de razonamiento (gpt-5): transitorio, se reintenta.
                    raise _RespuestaVacia("La API devolvió una respuesta vacía.")
                duracion_ms = int((time.monotonic() - inicio) * 1000)
                logger.info("LLM %s/%s respondió en %d ms", carril, modelo, duracion_ms)
                uso = getattr(respuesta, "usage", None)
                try:
                    self._registrar(
                        carril=carril,
                        modelo=modelo,
                        tokens_prompt=getattr(uso, "prompt_tokens", None),
                        tokens_salida=getattr(uso, "completion_tokens", None),
                        duracion_ms=duracion_ms,
                    )
                except Exception:  # el registro jamás rompe la generación
                    logger.warning("No se pudo registrar el uso del LLM")
                return contenido
            except (APIConnectionError, APIStatusError, _RespuestaVacia) as error:
                if not _es_reintentable(error):
                    raise ErrorLLM(
                        f"Error de la API sin reintento: {_describir(error)}. "
                        "Revisa tu configuración (API key, modelo)."
                    ) from error
                ultimo_error = error
                logger.warning(
                    "Intento %d/%d falló: %s",
                    intento + 1,
                    MAX_REINTENTOS_API,
                    _describir(error),
                )
                if intento < MAX_REINTENTOS_API - 1:
                    self._dormir(espera_backoff(intento))
        raise ErrorLLM(
            f"La API siguió fallando tras {MAX_REINTENTOS_API} intentos "
            f"({_describir(ultimo_error) if ultimo_error else 'desconocido'}). "
            "Tu progreso está guardado; inténtalo de nuevo en unos minutos."
        ) from ultimo_error

    def generar_imagen(self, prompt: str) -> bytes:
        """Genera una imagen PNG con la API de imágenes (HU-08, bonus).

        Sin reintentos: la imagen es opcional y el llamador degrada solo.

        Raises:
            Exception: Cualquier error del SDK (el llamador lo degrada).
        """
        from tutor.proveedor.imagenes import (
            MODELO_IMAGENES,
            TAMANO_IMAGEN,
            decodificar_b64,
        )

        respuesta = self._cliente.images.generate(
            model=MODELO_IMAGENES,
            prompt=prompt,
            size=TAMANO_IMAGEN,
            quality="low",
            n=1,
        )
        if not respuesta.data or not respuesta.data[0].b64_json:
            raise ValueError("La API de imágenes devolvió una respuesta vacía.")
        return decodificar_b64(respuesta.data[0].b64_json)

    def generar_stream(
        self, system: str, prompt: str, carril: str = "potente"
    ) -> Iterator[str]:
        """Emite la respuesta en fragmentos (SSE, HU-35).

        Los reintentos aplican solo a ABRIR el stream; una vez que empieza
        a emitir, un corte se propaga como ``ErrorLLM`` (el llamador decide
        el fallback). El uso se registra sin tokens (el SDK no los da en
        streaming sin opciones extra).

        Raises:
            ErrorLLM: Si no se pudo abrir el stream o llegó vacío.
        """
        modelo = self._modelos.get(carril, self._modelos["potente"])
        ultimo_error: Exception | None = None
        stream = None
        inicio = time.monotonic()
        for intento in range(MAX_REINTENTOS_API):
            try:
                stream = self._cliente.chat.completions.create(
                    model=modelo,
                    max_completion_tokens=MAX_TOKENS_RESPUESTA,
                    stream=True,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                )
                break
            except (APIConnectionError, APIStatusError) as error:
                if not _es_reintentable(error):
                    raise ErrorLLM(
                        f"Error de la API sin reintento: {_describir(error)}. "
                        "Revisa tu configuración (API key, modelo)."
                    ) from error
                ultimo_error = error
                logger.warning(
                    "Stream intento %d/%d falló: %s",
                    intento + 1,
                    MAX_REINTENTOS_API,
                    _describir(error),
                )
                if intento < MAX_REINTENTOS_API - 1:
                    self._dormir(espera_backoff(intento))
        if stream is None:
            raise ErrorLLM(
                f"La API siguió fallando tras {MAX_REINTENTOS_API} intentos "
                f"({_describir(ultimo_error) if ultimo_error else 'desconocido'})."
            ) from ultimo_error
        hubo_contenido = False
        try:
            for parte in stream:
                delta = parte.choices[0].delta.content if parte.choices else None
                if delta:
                    hubo_contenido = True
                    yield delta
        except (APIConnectionError, APIStatusError) as error:
            raise ErrorLLM(
                f"El stream se cortó a mitad: {_describir(error)}."
            ) from error
        if not hubo_contenido:
            raise ErrorLLM("La API devolvió un stream vacío.")
        duracion_ms = int((time.monotonic() - inicio) * 1000)
        logger.info("LLM stream %s/%s terminó en %d ms", carril, modelo, duracion_ms)
        try:
            self._registrar(
                carril=carril,
                modelo=modelo,
                tokens_prompt=None,
                tokens_salida=None,
                duracion_ms=duracion_ms,
            )
        except Exception:  # el registro jamás rompe la generación
            logger.warning("No se pudo registrar el uso del LLM")


class ExtractorCampoJSON:
    r"""Extrae el valor string de un campo de un JSON streameado (HU-35).

    Se alimenta con fragmentos crudos y devuelve los deltas DECODIFICADOS
    del valor del campo (maneja escapes ``\"``, ``\n``, ``\uXXXX`` incluso
    partidos entre fragmentos, porque re-escanea el buffer). El JSON crudo
    completo queda en ``crudo`` para validarlo al final.
    """

    def __init__(self, campo: str = "mensaje") -> None:
        """Prepara el extractor para ``campo``."""
        self.crudo = ""
        self._patron = f'"{campo}"'
        self._emitido = ""

    def alimentar(self, trozo: str) -> str:
        """Acumula un fragmento y devuelve el delta decodificado (o '')."""
        self.crudo += trozo
        valor = self._valor_actual()
        delta = valor[len(self._emitido) :]
        self._emitido = valor
        return delta

    def _valor_actual(self) -> str:
        """El valor del campo decodificado hasta donde llegó el buffer."""
        inicio = self.crudo.find(self._patron)
        if inicio < 0:
            return self._emitido  # el campo aún no aparece
        resto = self.crudo[inicio + len(self._patron) :]
        coincidencia = re.match(r'\s*:\s*"', resto)
        if not coincidencia:
            return self._emitido
        texto = resto[coincidencia.end() :]
        piezas: list[str] = []
        i = 0
        while i < len(texto):
            caracter = texto[i]
            if caracter == '"':
                break  # comilla de cierre sin escapar
            if caracter != "\\":
                piezas.append(caracter)
                i += 1
                continue
            # Secuencia de escape: si está incompleta al final del buffer,
            # se deja para el siguiente fragmento.
            if i + 1 >= len(texto):
                break
            siguiente = texto[i + 1]
            simples = {
                '"': '"',
                "\\": "\\",
                "/": "/",
                "n": "\n",
                "t": "\t",
                "r": "\r",
                "b": "\b",
                "f": "\f",
            }
            if siguiente in simples:
                piezas.append(simples[siguiente])
                i += 2
                continue
            if siguiente == "u":
                if i + 6 > len(texto):
                    break  # \uXXXX incompleto: esperar más datos
                piezas.append(chr(int(texto[i + 2 : i + 6], 16)))
                i += 6
                continue
            i += 2  # escape desconocido: se omite
        return "".join(piezas)


def extraer_json(texto: str) -> Any:
    """Parsea el JSON de una respuesta, tolerando fences ``` de Markdown.

    Raises:
        json.JSONDecodeError: Si el contenido no es JSON válido.
    """
    texto = texto.strip()
    if texto.startswith("```"):
        primera_linea = texto.find("\n")
        cierre = texto.rfind("```")
        if primera_linea != -1 and cierre > primera_linea:
            texto = texto[primera_linea + 1 : cierre].strip()
    return json.loads(texto)


def pedir_json[T](
    cliente: ClienteLLM,
    system: str,
    prompt: str,
    validar: Callable[[Any], T],
    carril: str = "potente",
) -> T:
    """Pide una respuesta JSON al LLM y la valida, reintentando el parseo.

    Si la respuesta no es JSON válido o no pasa ``validar``, se reintenta
    incluyendo el error en el prompt (hasta ``MAX_REINTENTOS_PARSEO`` veces).

    Args:
        cliente: Cliente LLM a usar.
        system: System prompt.
        prompt: Prompt del usuario; debe describir el esquema esperado.
        validar: Función que convierte el JSON crudo al tipo de dominio y
            lanza ``ValueError``/``KeyError``/``TypeError`` si no cumple.
        carril: Carril de modelo a usar (HU-39): "potente" o "chat".

    Returns:
        El objeto validado.

    Raises:
        ErrorLLM: Si tras los reintentos el modelo no produce JSON válido.
    """
    prompt_actual = prompt
    ultimo_error: Exception | None = None
    for _ in range(MAX_REINTENTOS_PARSEO + 1):
        respuesta = cliente.generar(system, prompt_actual, carril)
        try:
            return validar(extraer_json(respuesta))
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
            ultimo_error = error
            logger.warning("Respuesta JSON inválida del modelo: %s", error)
            prompt_actual = (
                f"{prompt}\n\nTu respuesta anterior no cumplió el esquema "
                f"pedido (error: {error}). Responde ÚNICAMENTE el JSON "
                "corregido, sin texto adicional."
            )
    raise ErrorLLM(
        "El modelo no produjo una respuesta con el formato esperado tras "
        f"{MAX_REINTENTOS_PARSEO + 1} intentos ({ultimo_error})."
    ) from ultimo_error
