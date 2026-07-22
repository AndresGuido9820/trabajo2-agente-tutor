"""Cuestionario de perfil: captura, validación y persistencia (HU-01).

La lectura interactiva está separada de la validación: las funciones
``validar_*`` son puras y ``preguntar_perfil`` recibe la función de entrada
inyectada, de modo que todo es testeable sin terminal real.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path

from tutor.nucleo.errores import ErrorDatos
from tutor.nucleo.models import Nivel, Objetivo, PerfilEstudiante
from tutor.persistencia import db

logger = logging.getLogger(__name__)

VERSION_ESQUEMA = 1
_CAMPOS_REQUERIDOS = ("nivel", "objetivo", "objetivo_detalle", "lenguaje")

FuncionEntrada = Callable[[str], str]


def validar_opcion(texto: str, cantidad: int) -> int:
    """Valida una opción numérica de menú (1..cantidad).

    Args:
        texto: Entrada cruda del usuario.
        cantidad: Número de opciones disponibles.

    Returns:
        El índice elegido, en base 0.

    Raises:
        ValueError: Si la entrada no es un número o está fuera de rango.
    """
    texto = texto.strip()
    if not texto.isdigit():
        raise ValueError("Escribe el número de una de las opciones.")
    indice = int(texto) - 1
    if not 0 <= indice < cantidad:
        raise ValueError(f"Elige un número entre 1 y {cantidad}.")
    return indice


def validar_lenguaje(texto: str) -> str:
    """Normaliza el lenguaje preferido; vacío significa 'que el tutor decida'.

    Args:
        texto: Entrada cruda del usuario.

    Returns:
        El lenguaje en minúsculas sin espacios extremos, o "".

    Raises:
        ValueError: Si contiene caracteres que no parecen nombre de lenguaje.
    """
    lenguaje = texto.strip().lower()
    # "/" y "," permiten multi-tecnología ("html/css + javascript"), que es
    # lo que el asesor propone para cursos web (hallazgo 2026-07-21).
    if lenguaje and not all(c.isalnum() or c in "+#. -/," for c in lenguaje):
        raise ValueError("Eso no parece un nombre de lenguaje de programación.")
    return lenguaje


def _preguntar_hasta_validar(
    entrada: FuncionEntrada,
    mensaje: str,
    validar: Callable[[str], object],
) -> object:
    """Repite una pregunta hasta que la validación pase, mostrando el motivo."""
    while True:
        try:
            return validar(entrada(mensaje))
        except ValueError as error:
            print(f"  Entrada inválida: {error}")


def _elegir_de_enum[E](entrada: FuncionEntrada, titulo: str, opciones: list[E]) -> E:
    """Muestra un menú numerado para un enum y devuelve la opción elegida."""
    print(titulo)
    for numero, opcion in enumerate(opciones, start=1):
        print(f"  {numero}. {opcion.descripcion}")  # type: ignore[attr-defined]
    indice = _preguntar_hasta_validar(
        entrada, "> ", lambda t: validar_opcion(t, len(opciones))
    )
    assert isinstance(indice, int)
    return opciones[indice]


def preguntar_perfil(entrada: FuncionEntrada = input) -> PerfilEstudiante:
    """Ejecuta el cuestionario interactivo y devuelve un perfil válido.

    Args:
        entrada: Función tipo ``input`` (inyectable para pruebas).

    Returns:
        El perfil del estudiante ya validado.
    """
    print("\n¡Hola! Vamos a armar tu curso a la medida. Cuatro preguntas:\n")

    nivel = _elegir_de_enum(entrada, "¿Cuál es tu experiencia?", list(Nivel))
    experiencia = entrada(
        "¿Qué has hecho antes relacionado con programación? (Enter si nada)\n> "
    ).strip()
    objetivo = _elegir_de_enum(
        entrada, "\n¿Qué quieres lograr aprendiendo a programar?", list(Objetivo)
    )
    objetivo_detalle = ""
    if objetivo is Objetivo.OTRO:
        detalle = _preguntar_hasta_validar(
            entrada,
            "Cuéntame tu objetivo:\n> ",
            lambda t: t.strip() or _rechazar("Necesito una descripción."),
        )
        assert isinstance(detalle, str)
        objetivo_detalle = detalle
    lenguaje = _preguntar_hasta_validar(
        entrada,
        "\n¿Algún lenguaje preferido? (Enter para que yo elija)\n> ",
        validar_lenguaje,
    )
    assert isinstance(lenguaje, str)

    return PerfilEstudiante(
        nivel=nivel,
        experiencia=experiencia,
        objetivo=objetivo,
        objetivo_detalle=objetivo_detalle,
        lenguaje=lenguaje,
    )


def _rechazar(motivo: str) -> str:
    """Lanza ``ValueError`` con el motivo dado (auxiliar para lambdas)."""
    raise ValueError(motivo)


def validar_perfil_extraido(datos: object, descripcion: str) -> PerfilEstudiante:
    """Valida el perfil que el LLM extrajo de la petición libre (HU-15).

    Args:
        datos: JSON crudo del LLM.
        descripcion: La petición original del estudiante, que se conserva.

    Raises:
        ValueError: Si nivel/objetivo no corresponden a los enums o si el
            objetivo 'otro' llega sin detalle (se rellena con la petición).
    """
    if not isinstance(datos, dict):
        raise ValueError("se esperaba un objeto JSON")
    objetivo = Objetivo(str(datos["objetivo"]).strip().lower())
    detalle = str(datos.get("objetivo_detalle", "")).strip()
    if objetivo is Objetivo.OTRO and not detalle:
        detalle = descripcion
    # Un lenguaje raro del LLM no debe tumbar la creación: se degrada a ""
    # (que el tutor decida), que es el mismo significado que en el CLI.
    try:
        lenguaje = validar_lenguaje(str(datos.get("lenguaje", "")))
    except ValueError:
        lenguaje = ""
    return PerfilEstudiante(
        nivel=Nivel(str(datos["nivel"]).strip().lower()),
        experiencia=str(datos.get("experiencia", "")).strip(),
        objetivo=objetivo,
        objetivo_detalle=detalle,
        lenguaje=lenguaje,
        descripcion=descripcion,
    )


def guardar_perfil(perfil: PerfilEstudiante, ruta: Path) -> None:
    """Guarda el perfil en la base de datos ``ruta`` (tabla ``perfil``)."""
    datos = {
        "version": VERSION_ESQUEMA,
        "nivel": perfil.nivel.value,
        "experiencia": perfil.experiencia,
        "objetivo": perfil.objetivo.value,
        "objetivo_detalle": perfil.objetivo_detalle,
        "lenguaje": perfil.lenguaje,
        "descripcion": perfil.descripcion,
    }
    db.guardar_documento(ruta, "perfil", datos)
    logger.info("Perfil guardado en %s", ruta)


def cargar_perfil(ruta: Path) -> PerfilEstudiante | None:
    """Carga el perfil desde ``ruta``.

    Args:
        ruta: Archivo ``perfil.json``.

    Returns:
        El perfil, o ``None`` si el archivo no existe.

    Raises:
        ErrorDatos: Si el archivo existe pero es inválido (JSON corrupto,
            campos faltantes o valores fuera de los enums).
    """
    try:
        datos = db.cargar_documento(ruta, "perfil")
        if datos is None:
            return None
        faltantes = [c for c in _CAMPOS_REQUERIDOS if c not in datos]
        if faltantes:
            raise ValueError(f"faltan campos: {', '.join(faltantes)}")
        return PerfilEstudiante(
            nivel=Nivel(datos["nivel"]),
            experiencia=str(datos.get("experiencia", "")),
            objetivo=Objetivo(datos["objetivo"]),
            objetivo_detalle=str(datos["objetivo_detalle"]),
            lenguaje=str(datos["lenguaje"]),
            descripcion=str(datos.get("descripcion", "")),
        )
    except (
        sqlite3.DatabaseError,
        json.JSONDecodeError,
        ValueError,
        KeyError,
        TypeError,
    ) as error:
        raise ErrorDatos(
            f"El perfil guardado en {ruta} está corrupto ({error}). "
            "Bórralo o rehaz el cuestionario."
        ) from error
