"""Generación del curso: temario y lecciones bajo demanda con cache (HU-03).

El temario se genera una sola vez a partir del perfil; las lecciones se
generan al entrar a cada unidad y se cachean en ``curso.json`` (RF-3.3:
se puede navegar por unidades cuyo contenido aún no existe).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tutor import prompts
from tutor.config import MAX_UNIDADES, MIN_UNIDADES
from tutor.llm import ClienteLLM, pedir_json
from tutor.models import PerfilEstudiante
from tutor.progreso import Progreso

logger = logging.getLogger(__name__)

VERSION_ESQUEMA = 1


@dataclass(frozen=True)
class Unidad:
    """Una unidad del temario (el contenido puede no existir aún)."""

    titulo: str
    objetivo: str
    conceptos: list[str]


@dataclass(frozen=True)
class Temario:
    """Plan del curso completo, generado una sola vez por perfil."""

    lenguaje: str
    unidades: list[Unidad]


@dataclass(frozen=True)
class PasoLeccion:
    """Un paso del guion de la lección conversada (HU-10)."""

    tipo: str
    instruccion: str


@dataclass(frozen=True)
class GuionLeccion:
    """Objetivos + paso a paso que la conversación de la lección sigue."""

    objetivos: list[str]
    pasos: list[PasoLeccion]


@dataclass
class Curso:
    """Temario + lecciones y guiones generados hasta ahora (cache)."""

    temario: Temario
    lecciones: dict[int, str] = field(default_factory=dict)
    guiones: dict[int, GuionLeccion] = field(default_factory=dict)


def validar_temario(datos: Any) -> Temario:
    """Convierte y valida el JSON crudo del LLM en un ``Temario``.

    Raises:
        ValueError: Si faltan campos, hay tipos incorrectos o el número de
            unidades está fuera de [MIN_UNIDADES, MAX_UNIDADES].
    """
    lenguaje = str(datos["lenguaje"]).strip().lower()
    if not lenguaje:
        raise ValueError("el campo 'lenguaje' está vacío")
    crudas = datos["unidades"]
    if not isinstance(crudas, list):
        raise ValueError("'unidades' debe ser una lista")
    if not MIN_UNIDADES <= len(crudas) <= MAX_UNIDADES:
        raise ValueError(
            f"se esperaban entre {MIN_UNIDADES} y {MAX_UNIDADES} unidades, "
            f"llegaron {len(crudas)}"
        )
    unidades = []
    for numero, cruda in enumerate(crudas):
        titulo = str(cruda["titulo"]).strip()
        objetivo = str(cruda["objetivo"]).strip()
        conceptos = [str(c).strip() for c in cruda["conceptos"]]
        if not titulo or not objetivo or not conceptos:
            raise ValueError(f"la unidad {numero} tiene campos vacíos")
        unidades.append(Unidad(titulo=titulo, objetivo=objetivo, conceptos=conceptos))
    return Temario(lenguaje=lenguaje, unidades=unidades)


def generar_temario(cliente: ClienteLLM, perfil: PerfilEstudiante) -> Temario:
    """Genera el temario del curso adaptado al perfil.

    Raises:
        ErrorLLM: Si el modelo no produce un temario válido tras reintentos.
    """
    logger.info("Generando temario para objetivo=%s", perfil.objetivo.value)
    return pedir_json(
        cliente,
        system=prompts.system_tutor(perfil),
        prompt=prompts.prompt_temario(perfil),
        validar=validar_temario,
    )


def generar_leccion(
    cliente: ClienteLLM,
    perfil: PerfilEstudiante,
    curso: Curso,
    indice: int,
    progreso: Progreso,
) -> str:
    """Devuelve la lección de la unidad ``indice``, generándola si no existe.

    La lección generada queda cacheada en ``curso.lecciones`` (el llamador es
    responsable de persistir el curso con ``guardar_curso``).

    Raises:
        IndexError: Si ``indice`` no corresponde a una unidad del temario.
        ErrorLLM: Si la generación falla tras reintentos.
    """
    if not 0 <= indice < len(curso.temario.unidades):
        raise IndexError(f"No existe la unidad {indice}.")
    if indice in curso.lecciones:
        logger.debug("Lección %d servida desde cache", indice)
        return curso.lecciones[indice]

    logger.info("Generando lección de la unidad %d", indice)
    leccion = cliente.generar(
        system=prompts.system_tutor(perfil),
        prompt=prompts.prompt_leccion(
            temario=curso.temario,
            indice=indice,
            conceptos_fallados=progreso.conceptos_fallados_recientes(),
        ),
    )
    curso.lecciones[indice] = leccion
    return leccion


MIN_PASOS_GUION = 5
MAX_PASOS_GUION = 8


def validar_guion(datos: Any) -> GuionLeccion:
    """Convierte y valida el JSON crudo del guion de lección.

    Raises:
        ValueError: Si faltan objetivos, el número de pasos está fuera de
            rango o algún paso tiene tipo desconocido o instrucción vacía.
    """
    objetivos = [str(o).strip() for o in datos["objetivos"]]
    if not objetivos or not all(objetivos):
        raise ValueError("los objetivos no pueden estar vacíos")
    crudos = datos["pasos"]
    if not isinstance(crudos, list) or not (
        MIN_PASOS_GUION <= len(crudos) <= MAX_PASOS_GUION
    ):
        raise ValueError(
            f"se esperaban entre {MIN_PASOS_GUION} y {MAX_PASOS_GUION} pasos"
        )
    pasos = []
    for numero, crudo in enumerate(crudos):
        tipo = str(crudo["tipo"]).strip()
        instruccion = str(crudo["instruccion"]).strip()
        if tipo not in prompts.TIPOS_PASO:
            raise ValueError(f"tipo de paso desconocido en el paso {numero}: {tipo}")
        if not instruccion:
            raise ValueError(f"el paso {numero} no tiene instrucción")
        pasos.append(PasoLeccion(tipo=tipo, instruccion=instruccion))
    return GuionLeccion(objetivos=objetivos, pasos=pasos)


def generar_guion(
    cliente: ClienteLLM,
    perfil: PerfilEstudiante,
    curso: Curso,
    indice: int,
    progreso: Progreso,
) -> GuionLeccion:
    """Devuelve el guion de la unidad ``indice``, generándolo si no existe.

    Queda cacheado en ``curso.guiones`` (el llamador persiste con
    ``guardar_curso``).

    Raises:
        IndexError: Si ``indice`` no corresponde a una unidad del temario.
        ErrorLLM: Si la generación falla tras reintentos.
    """
    if not 0 <= indice < len(curso.temario.unidades):
        raise IndexError(f"No existe la unidad {indice}.")
    if indice in curso.guiones:
        return curso.guiones[indice]

    logger.info("Generando guion de la unidad %d", indice)
    guion = pedir_json(
        cliente,
        system=prompts.system_tutor(perfil),
        prompt=prompts.prompt_guion(
            temario=curso.temario,
            indice=indice,
            conceptos_fallados=progreso.conceptos_fallados_recientes(),
        ),
        validar=validar_guion,
    )
    curso.guiones[indice] = guion
    return guion


def guardar_curso(curso: Curso, ruta: Path) -> None:
    """Serializa el curso (temario + lecciones cacheadas) a ``ruta``."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {
        "version": VERSION_ESQUEMA,
        "lenguaje": curso.temario.lenguaje,
        "unidades": [
            {"titulo": u.titulo, "objetivo": u.objetivo, "conceptos": u.conceptos}
            for u in curso.temario.unidades
        ],
        "lecciones": {str(i): md for i, md in curso.lecciones.items()},
        "guiones": {
            str(i): {
                "objetivos": g.objetivos,
                "pasos": [
                    {"tipo": p.tipo, "instruccion": p.instruccion} for p in g.pasos
                ],
            }
            for i, g in curso.guiones.items()
        },
    }
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), "utf-8")


def cargar_curso(ruta: Path) -> Curso | None:
    """Carga el curso desde ``ruta``.

    Un archivo corrupto no es fatal: se advierte y se devuelve ``None`` para
    que el temario se regenere (cuesta una llamada; no bloquea al estudiante).
    """
    if not ruta.exists():
        return None
    try:
        datos = json.loads(ruta.read_text("utf-8"))
        temario = validar_temario(datos)
        lecciones = {int(i): str(md) for i, md in datos["lecciones"].items()}
        # "guiones" es opcional para retro-compatibilidad con cursos previos.
        guiones = {
            int(i): validar_guion(g) for i, g in datos.get("guiones", {}).items()
        }
        return Curso(temario=temario, lecciones=lecciones, guiones=guiones)
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
        logger.warning(
            "Curso corrupto en %s (%s); se regenerará el temario.", ruta, error
        )
        return None
