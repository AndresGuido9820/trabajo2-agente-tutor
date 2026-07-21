"""Configuración de la aplicación: variables de entorno y constantes.

Toda constante ajustable del sistema vive aquí (RULES.md §2: sin números
mágicos). La API key solo se lee, nunca se registra en logs ni se muestra.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from tutor.errores import ErrorConfiguracion

MODELO_POR_DEFECTO = "gpt-5-mini"
DIR_DATOS_POR_DEFECTO = "./data"

# Precios por 1M de tokens (USD, entrada/salida) para la estimación de
# costo local (HU-39). Editables; un modelo ausente no estima costo.
PRECIOS_MODELO: dict[str, tuple[float, float]] = {
    "gpt-5": (1.25, 10.0),
    "gpt-5-mini": (0.25, 2.0),
    "gpt-5-nano": (0.05, 0.40),
}

# Límites de interacción con el LLM (ver plan/HU-02-cliente-llm.md).
# Los modelos razonadores pueden tardar 1-3 min en generaciones largas
# (artefactos, guías): un timeout corto convierte llamadas exitosas en
# reintentos inútiles (ver HALLAZGOS 2026-07-20 HU-16).
TIMEOUT_API_SEGUNDOS = 180.0
MAX_REINTENTOS_API = 3
MAX_REINTENTOS_PARSEO = 2
# Los modelos gpt-5 gastan tokens de razonamiento DENTRO de este límite;
# si es bajo, la respuesta puede llegar vacía (ver HALLAZGOS 2026-07-20).
MAX_TOKENS_RESPUESTA = 16384
BASE_BACKOFF_SEGUNDOS = 1.0

# Parámetros del curso (ver plan/HU-03 y HU-04)
MIN_UNIDADES = 5
MAX_UNIDADES = 8
PREGUNTAS_POR_QUIZ = 4

# Charla con el tutor (ver plan/HU-09): turnos de historial que se conservan
MAX_TURNOS_CHARLA = 8

# Reencuentro (plan/v2/HU-30): horas sin actividad para ofrecer el resumen
HORAS_PARA_REENCUENTRO = 8

# Guía interactiva y progresión (ver plan/HU-12)
NOTA_APROBATORIA = 70
PUNTOS_PRIMER_INTENTO = 10
PUNTOS_SEGUNDO_INTENTO = 5
PUNTOS_QUIZ_APROBADO = 30
MIN_SECCIONES_GUIA = 3
MAX_SECCIONES_GUIA = 5


@dataclass(frozen=True)
class Configuracion:
    """Valores efectivos de configuración de una ejecución."""

    api_key: str
    modelo: str
    dir_datos: Path
    # Carril conversacional (HU-39): vacío = usar ``modelo`` para todo.
    modelo_chat: str = ""


def cargar_configuracion(entorno: dict[str, str] | None = None) -> Configuracion:
    """Carga la configuración desde ``.env`` y el entorno del proceso.

    Args:
        entorno: Diccionario de variables a usar en lugar de ``os.environ``
            (inyectable para pruebas).

    Returns:
        La configuración efectiva.

    Raises:
        ErrorConfiguracion: Si falta ``OPENAI_API_KEY``.
    """
    if entorno is None:
        load_dotenv()
        entorno = dict(os.environ)

    api_key = entorno.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ErrorConfiguracion(
            "Falta OPENAI_API_KEY. Copia .env.example a .env y agrega tu "
            "API key de https://platform.openai.com/api-keys."
        )

    return Configuracion(
        api_key=api_key,
        modelo=entorno.get("TUTOR_MODEL", "").strip() or MODELO_POR_DEFECTO,
        dir_datos=Path(
            entorno.get("TUTOR_DATA_DIR", "").strip() or DIR_DATOS_POR_DEFECTO
        ),
        modelo_chat=entorno.get("TUTOR_MODEL_CHAT", "").strip(),
    )
