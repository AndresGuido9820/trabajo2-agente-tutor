"""Ilustraciones de las clases generadas con IA (plan/HU-08, bonus).

Detrás del flag ``TUTOR_IMAGENES=1`` (por costo). La imagen es SIEMPRE
opcional: cualquier fallo degrada a un warning en el log y la clase
funciona igual. Cache en disco por clase (una sola llamada por unidad).
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)

MODELO_IMAGENES = "gpt-image-1"
TAMANO_IMAGEN = "1024x1024"


class GeneradorImagenes(Protocol):
    """Contrato mínimo: algo capaz de generar una imagen PNG."""

    def generar_imagen(self, prompt: str) -> bytes:
        """Devuelve los bytes PNG de la imagen generada."""
        ...


def ruta_imagen(dir_curso: Path, indice: int) -> Path:
    """Ruta cacheada de la ilustración de una clase."""
    return dir_curso / "imagenes" / f"unidad-{indice}.png"


def prompt_visual(titulo: str, conceptos: list[str], lenguaje: str) -> str:
    """Prompt de la ilustración: conceptual y sin texto (los LLM lo tipografían mal)."""
    return (
        "Ilustración editorial minimalista y cálida para una clase de "
        f"programación en {lenguaje} titulada «{titulo}». Representa "
        f"visualmente la idea de: {', '.join(conceptos[:3])}. Estilo flat "
        "con 3-4 colores, formas geométricas simples, fondo claro. "
        "SIN texto, SIN letras, SIN código escrito."
    )


def ilustrar_unidad(
    generador: GeneradorImagenes | Any,
    dir_curso: Path,
    indice: int,
    titulo: str,
    conceptos: list[str],
    lenguaje: str,
) -> Path | None:
    """Genera (o reutiliza de cache) la ilustración de una clase.

    Returns:
        La ruta del PNG, o ``None`` si el generador no soporta imágenes o
        la API falló (degradación silenciosa: warning en log, nunca rompe).
    """
    destino = ruta_imagen(dir_curso, indice)
    if destino.exists():
        return destino
    generar = getattr(generador, "generar_imagen", None)
    if generar is None:
        return None  # cliente sin soporte de imágenes (p. ej. dobles)
    try:
        datos = generar(prompt_visual(titulo, conceptos, lenguaje))
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(datos)
        logger.info("Ilustración de la clase %d guardada en %s", indice, destino)
        return destino
    except Exception as error:  # la imagen JAMÁS bloquea la clase
        logger.warning("No se pudo ilustrar la clase %d: %s", indice, error)
        return None


def decodificar_b64(b64: str) -> bytes:
    """Decodifica la respuesta base64 de la API de imágenes."""
    return base64.b64decode(b64)
