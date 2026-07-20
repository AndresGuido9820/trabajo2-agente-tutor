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
import time
from collections.abc import Callable
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
from tutor.errores import ErrorLLM

logger = logging.getLogger(__name__)

_CODIGOS_REINTENTABLES = frozenset({429})


class ClienteLLM(Protocol):
    """Contrato mínimo que el resto del código conoce del LLM."""

    def generar(self, system: str, prompt: str) -> str:
        """Envía un prompt y devuelve el texto de la respuesta."""
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
    ) -> None:
        """Inicializa el cliente; si no se inyecta SDK, lo crea con timeout."""
        self._modelo = configuracion.modelo
        self._cliente = cliente or OpenAI(
            api_key=configuracion.api_key, timeout=TIMEOUT_API_SEGUNDOS
        )
        self._dormir = dormir

    def generar(self, system: str, prompt: str) -> str:
        """Envía un prompt con reintentos y devuelve el texto de la respuesta.

        Raises:
            ErrorLLM: Ante error no reintentable, respuesta vacía o al agotar
                ``MAX_REINTENTOS_API`` intentos.
        """
        ultimo_error: Exception | None = None
        for intento in range(MAX_REINTENTOS_API):
            try:
                respuesta = self._cliente.chat.completions.create(
                    model=self._modelo,
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

    Returns:
        El objeto validado.

    Raises:
        ErrorLLM: Si tras los reintentos el modelo no produce JSON válido.
    """
    prompt_actual = prompt
    ultimo_error: Exception | None = None
    for _ in range(MAX_REINTENTOS_PARSEO + 1):
        respuesta = cliente.generar(system, prompt_actual)
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
