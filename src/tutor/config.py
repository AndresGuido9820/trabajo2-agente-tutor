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

# Límites de interacción con el LLM (ver plan/HU-02-cliente-llm.md)
TIMEOUT_API_SEGUNDOS = 60.0
MAX_REINTENTOS_API = 3
MAX_REINTENTOS_PARSEO = 2
MAX_TOKENS_RESPUESTA = 4096
BASE_BACKOFF_SEGUNDOS = 1.0

# Parámetros del curso (ver plan/HU-03 y HU-04)
MIN_UNIDADES = 5
MAX_UNIDADES = 8
PREGUNTAS_POR_QUIZ = 4


@dataclass(frozen=True)
class Configuracion:
    """Valores efectivos de configuración de una ejecución."""

    api_key: str
    modelo: str
    dir_datos: Path


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
    )
