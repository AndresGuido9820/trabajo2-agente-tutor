"""Generación del curso: temario y lecciones bajo demanda con cache (HU-03).

El temario se genera una sola vez a partir del perfil; las lecciones se
generan al entrar a cada unidad y se cachean en ``curso.json`` (RF-3.3:
se puede navegar por unidades cuyo contenido aún no existe).
"""

from __future__ import annotations

import ast
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tutor.config import (
    MAX_SECCIONES_GUIA,
    MAX_UNIDADES,
    MIN_SECCIONES_GUIA,
    MIN_UNIDADES,
)
from tutor.ensenanza import prompts
from tutor.ensenanza.progreso import Progreso
from tutor.nucleo.models import PerfilEstudiante
from tutor.persistencia import db
from tutor.proveedor.llm import ClienteLLM, pedir_json

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
class PreguntaIntermedia:
    """Pregunta del mini-quiz que cierra un objetivo (plan/v2/HU-24)."""

    enunciado: str
    opciones: list[str]
    correcta: int
    explicacion: str
    concepto: str


@dataclass(frozen=True)
class QuizIntermedio:
    """Mini-quiz de 2 preguntas al cerrar un objetivo del guion v2.

    ``fin_paso`` es el índice (en la lista APLANADA de pasos) del último
    paso del objetivo: al completarlo, el quiz se dispara.
    """

    fin_paso: int
    preguntas: list[PreguntaIntermedia]


@dataclass(frozen=True)
class RetoCodigo:
    """Reto de código verificado en el navegador con Pyodide (HU-28).

    ``tests``: cada uno con ``llamada`` + (``esperado`` o
    ``stdout_contiene``); el harness JS los corre sobre el código del
    estudiante. Viajan al navegador a conciencia (trade-off documentado).
    """

    enunciado: str
    seed: str
    tests: list[dict[str, str | None]]


@dataclass(frozen=True)
class GuionLeccion:
    """Objetivos + paso a paso que la conversación de la lección sigue.

    Un guion v2 (HU-24) agrupa los pasos por objetivo; aquí se representa
    APLANADO (``pasos``) más las fronteras de cada objetivo
    (``intermedios``): así la maquinaria de avance/streaming de la
    conversación no cambia. ``intermedios`` vacío = guion v1.
    ``retos`` (HU-28) es paralelo a ``objetivos``; ``None`` = sin reto.
    """

    objetivos: list[str]
    pasos: list[PasoLeccion]
    intermedios: list[QuizIntermedio] = field(default_factory=list)
    retos: list[RetoCodigo | None] = field(default_factory=list)


@dataclass(frozen=True)
class Checkpoint:
    """Pregunta de verificación de una sección de la guía (HU-12)."""

    pregunta: str
    opciones: list[str]
    correcta: int
    pista: str
    explicacion: str
    concepto: str


@dataclass(frozen=True)
class SeccionGuia:
    """Una sección de la guía: enseña un objetivo y lo verifica."""

    objetivo: str
    contenido: str
    checkpoint: Checkpoint


@dataclass(frozen=True)
class Guia:
    """Guía interactiva de una unidad: una sección por objetivo."""

    secciones: list[SeccionGuia]


@dataclass
class Curso:
    """Temario + contenido generado hasta ahora (cache)."""

    temario: Temario
    lecciones: dict[int, str] = field(default_factory=dict)
    guiones: dict[int, GuionLeccion] = field(default_factory=dict)
    guias: dict[int, Guia] = field(default_factory=dict)
    # Mini-artefactos HTML por "unidad-seccion" (HU-14)
    artefactos: dict[str, str] = field(default_factory=dict)


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


def plan_markdown(temario: Temario, descripcion: str = "") -> str:
    """El plan del curso como Markdown (`curso.md`, mini-ventana en HU-16)."""
    lineas = [f"# Tu curso de {temario.lenguaje}", ""]
    if descripcion:
        lineas += [f"> Pedido: “{descripcion}”", ""]
    for numero, unidad in enumerate(temario.unidades, start=1):
        lineas += [
            f"## {numero}. {unidad.titulo}",
            "",
            f"**Objetivo:** {unidad.objetivo}",
            "",
            "Conceptos: " + ", ".join(unidad.conceptos),
            "",
        ]
    return "\n".join(lineas)


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

# Guion v2 (HU-24): objetivos con su propia secuencia PRIMM y mini-quiz.
MIN_OBJETIVOS_GUION = 3
MAX_OBJETIVOS_GUION = 4
MIN_PASOS_OBJETIVO = 4
MAX_PASOS_OBJETIVO = 7
PREGUNTAS_INTERMEDIAS = 2


def _validar_pasos(crudos: Any, minimo: int, maximo: int) -> list[PasoLeccion]:
    """Valida una lista de pasos PRIMM (tipo del catálogo + instrucción)."""
    if not isinstance(crudos, list) or not minimo <= len(crudos) <= maximo:
        raise ValueError(f"se esperaban entre {minimo} y {maximo} pasos")
    pasos = []
    for numero, crudo in enumerate(crudos):
        tipo = str(crudo["tipo"]).strip()
        instruccion = str(crudo["instruccion"]).strip()
        if tipo not in prompts.TIPOS_PASO:
            raise ValueError(f"tipo de paso desconocido en el paso {numero}: {tipo}")
        if not instruccion:
            raise ValueError(f"el paso {numero} no tiene instrucción")
        pasos.append(PasoLeccion(tipo=tipo, instruccion=instruccion))
    return pasos


def _validar_pregunta_intermedia(crudo: Any) -> PreguntaIntermedia:
    """Valida una pregunta del mini-quiz (mismas reglas que el quiz)."""
    opciones = [str(o) for o in crudo["opciones"]]
    correcta = int(crudo["correcta"])
    if len(opciones) != 4:
        raise ValueError("la pregunta intermedia debe tener 4 opciones")
    if not 0 <= correcta < 4:
        raise ValueError("índice 'correcta' fuera de rango en pregunta intermedia")
    campos = {
        campo: str(crudo[campo]).strip()
        for campo in ("enunciado", "explicacion", "concepto")
    }
    if not all(campos.values()):
        raise ValueError("la pregunta intermedia tiene campos vacíos")
    return PreguntaIntermedia(
        enunciado=campos["enunciado"],
        opciones=opciones,
        correcta=correcta,
        explicacion=campos["explicacion"],
        concepto=campos["concepto"],
    )


def validar_reto(crudo: Any) -> RetoCodigo:
    """Valida un reto de código del guion v2 (HU-28).

    Raises:
        ValueError: Si el seed no parsea, faltan tests o están malformados.
    """
    enunciado = str(crudo["enunciado"]).strip()
    seed = str(crudo["seed"])
    if not enunciado:
        raise ValueError("el reto no tiene enunciado")
    try:
        ast.parse(seed)
    except SyntaxError as error:
        raise ValueError(f"el seed del reto no es Python válido: {error}") from error
    crudos = crudo["tests"]
    if not isinstance(crudos, list) or not 2 <= len(crudos) <= 4:
        raise ValueError("el reto lleva entre 2 y 4 tests")
    tests: list[dict[str, str | None]] = []
    for numero, t in enumerate(crudos):
        llamada = str(t["llamada"]).strip()
        esperado = t.get("esperado")
        stdout = t.get("stdout_contiene")
        if not llamada:
            raise ValueError(f"el test {numero} no tiene 'llamada'")
        if esperado is None and stdout is None:
            raise ValueError(
                f"el test {numero} necesita 'esperado' o 'stdout_contiene'"
            )
        tests.append(
            {
                "llamada": llamada,
                "esperado": str(esperado) if esperado is not None else None,
                "stdout_contiene": str(stdout) if stdout is not None else None,
            }
        )
    return RetoCodigo(enunciado=enunciado, seed=seed, tests=tests)


def validar_guion(datos: Any) -> GuionLeccion:
    """Convierte y valida el JSON crudo del guion (v1 plano o v2 por objetivos).

    v2 (HU-24): ``{"version": 2, "objetivos": [{objetivo, pasos, quiz}]}``
    se APLANA a una sola lista de pasos con las fronteras en
    ``intermedios`` (la conversación no distingue versiones).

    Raises:
        ValueError: Si faltan objetivos, los pasos están fuera de rango o
            algún paso/pregunta es inválido.
    """
    if int(datos.get("version", 1)) >= 2:
        crudos = datos["objetivos"]
        if not isinstance(crudos, list) or not (
            MIN_OBJETIVOS_GUION <= len(crudos) <= MAX_OBJETIVOS_GUION
        ):
            raise ValueError(
                f"se esperaban entre {MIN_OBJETIVOS_GUION} y "
                f"{MAX_OBJETIVOS_GUION} objetivos"
            )
        objetivos: list[str] = []
        pasos: list[PasoLeccion] = []
        intermedios: list[QuizIntermedio] = []
        retos: list[RetoCodigo | None] = []
        for crudo in crudos:
            objetivo = str(crudo["objetivo"]).strip()
            if not objetivo:
                raise ValueError("un objetivo del guion está vacío")
            objetivos.append(objetivo)
            pasos.extend(
                _validar_pasos(crudo["pasos"], MIN_PASOS_OBJETIVO, MAX_PASOS_OBJETIVO)
            )
            preguntas = [_validar_pregunta_intermedia(p) for p in crudo["quiz"]]
            if len(preguntas) != PREGUNTAS_INTERMEDIAS:
                raise ValueError(
                    f"cada objetivo lleva exactamente {PREGUNTAS_INTERMEDIAS} "
                    "preguntas intermedias"
                )
            intermedios.append(
                QuizIntermedio(fin_paso=len(pasos) - 1, preguntas=preguntas)
            )
            retos.append(validar_reto(crudo["reto"]) if crudo.get("reto") else None)
        return GuionLeccion(
            objetivos=objetivos, pasos=pasos, intermedios=intermedios, retos=retos
        )

    objetivos = [str(o).strip() for o in datos["objetivos"]]
    if not objetivos or not all(objetivos):
        raise ValueError("los objetivos no pueden estar vacíos")
    pasos = _validar_pasos(datos["pasos"], MIN_PASOS_GUION, MAX_PASOS_GUION)
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
        prompt=prompts.prompt_guion_v2(
            temario=curso.temario,
            indice=indice,
            conceptos_fallados=progreso.conceptos_fallados_recientes(),
        ),
        validar=validar_guion,
    )
    curso.guiones[indice] = guion
    return guion


def _validar_checkpoint(datos: Any, conceptos: list[str] | None = None) -> Checkpoint:
    """Valida el checkpoint de una sección de la guía."""
    opciones = [str(o) for o in datos["opciones"]]
    correcta = int(datos["correcta"])
    if len(opciones) != 4:
        raise ValueError("el checkpoint debe tener exactamente 4 opciones")
    if not 0 <= correcta < 4:
        raise ValueError("índice 'correcta' del checkpoint fuera de rango")
    campos = {
        campo: str(datos[campo]).strip()
        for campo in ("pregunta", "pista", "explicacion", "concepto")
    }
    if not all(campos.values()):
        raise ValueError("el checkpoint tiene campos vacíos")
    return Checkpoint(
        pregunta=campos["pregunta"],
        opciones=opciones,
        correcta=correcta,
        pista=campos["pista"],
        explicacion=campos["explicacion"],
        concepto=campos["concepto"],
    )


def validar_guia(datos: Any) -> Guia:
    """Convierte y valida el JSON crudo de la guía interactiva (HU-12).

    Raises:
        ValueError: Si el número de secciones está fuera de rango o alguna
            sección/checkpoint es inválido.
    """
    crudas = datos["secciones"]
    if not isinstance(crudas, list) or not (
        MIN_SECCIONES_GUIA <= len(crudas) <= MAX_SECCIONES_GUIA
    ):
        raise ValueError(
            f"se esperaban entre {MIN_SECCIONES_GUIA} y {MAX_SECCIONES_GUIA} secciones"
        )
    secciones = []
    for numero, cruda in enumerate(crudas):
        objetivo = str(cruda["objetivo"]).strip()
        contenido = str(cruda["contenido"]).strip()
        if not objetivo or not contenido:
            raise ValueError(f"la sección {numero} tiene campos vacíos")
        secciones.append(
            SeccionGuia(
                objetivo=objetivo,
                contenido=contenido,
                checkpoint=_validar_checkpoint(cruda["checkpoint"]),
            )
        )
    return Guia(secciones=secciones)


def generar_guia(
    cliente: ClienteLLM,
    perfil: PerfilEstudiante,
    curso: Curso,
    indice: int,
    progreso: Progreso,
) -> Guia:
    """Devuelve la guía de la unidad ``indice``, generándola si no existe.

    Queda cacheada en ``curso.guias`` (el llamador persiste con
    ``guardar_curso``).

    Raises:
        IndexError: Si ``indice`` no corresponde a una unidad del temario.
        ErrorLLM: Si la generación falla tras reintentos.
    """
    if not 0 <= indice < len(curso.temario.unidades):
        raise IndexError(f"No existe la unidad {indice}.")
    if indice in curso.guias:
        return curso.guias[indice]

    logger.info("Generando guía de la unidad %d", indice)
    guia = pedir_json(
        cliente,
        system=prompts.system_tutor(perfil),
        prompt=prompts.prompt_guia(
            temario=curso.temario,
            indice=indice,
            conceptos_fallados=progreso.conceptos_fallados_recientes(),
        ),
        validar=validar_guia,
    )
    curso.guias[indice] = guia
    return guia


def _guion_a_json(g: GuionLeccion) -> dict[str, Any]:
    """Serializa el guion; v2 conserva la agrupación por objetivos."""
    if not g.intermedios:
        return {
            "objetivos": g.objetivos,
            "pasos": [{"tipo": p.tipo, "instruccion": p.instruccion} for p in g.pasos],
        }
    grupos = []
    inicio = 0
    retos = g.retos or [None] * len(g.objetivos)
    for objetivo, intermedio, reto in zip(
        g.objetivos, g.intermedios, retos, strict=True
    ):
        grupos.append(
            {
                "objetivo": objetivo,
                "pasos": [
                    {"tipo": p.tipo, "instruccion": p.instruccion}
                    for p in g.pasos[inicio : intermedio.fin_paso + 1]
                ],
                "quiz": [
                    {
                        "enunciado": p.enunciado,
                        "opciones": p.opciones,
                        "correcta": p.correcta,
                        "explicacion": p.explicacion,
                        "concepto": p.concepto,
                    }
                    for p in intermedio.preguntas
                ],
                "reto": {
                    "enunciado": reto.enunciado,
                    "seed": reto.seed,
                    "tests": reto.tests,
                }
                if reto
                else None,
            }
        )
        inicio = intermedio.fin_paso + 1
    return {"version": 2, "objetivos": grupos}


def _guia_a_json(g: Guia) -> dict[str, Any]:
    """Serializa la guía interactiva de una clase."""
    return {
        "secciones": [
            {
                "objetivo": s.objetivo,
                "contenido": s.contenido,
                "checkpoint": {
                    "pregunta": s.checkpoint.pregunta,
                    "opciones": s.checkpoint.opciones,
                    "correcta": s.checkpoint.correcta,
                    "pista": s.checkpoint.pista,
                    "explicacion": s.checkpoint.explicacion,
                    "concepto": s.checkpoint.concepto,
                },
            }
            for s in g.secciones
        ]
    }


def guardar_curso(curso: Curso, ruta: Path) -> None:
    """Persiste el diseño del curso en la BD.

    Fila ``curso`` (diseño y metadata) + una fila por clase con su
    definición, su prompt/guion y su contenido generado.
    """
    with db.abrir(ruta) as conexion:
        fila = conexion.execute("SELECT creado_en FROM curso WHERE id = 1").fetchone()
        # INSERT OR REPLACE reemplaza la fila ENTERA: todo campo que no se
        # liste vuelve a su default. plan_md, nombre y archivado se preservan
        # explícitamente (hallazgo 2026-07-21: cada lección generada borraba
        # el nombre del curso).
        conexion.execute(
            "INSERT OR REPLACE INTO curso"
            "(id, lenguaje, plan_md, artefactos, prompts_version, creado_en, "
            "nombre, archivado) "
            "VALUES(1, ?, COALESCE((SELECT plan_md FROM curso WHERE id=1), ''), "
            "?, ?, ?, "
            "COALESCE((SELECT nombre FROM curso WHERE id=1), ''), "
            "COALESCE((SELECT archivado FROM curso WHERE id=1), 0))",
            (
                curso.temario.lenguaje,
                json.dumps(curso.artefactos, ensure_ascii=False),
                prompts.PROMPTS_VERSION,
                fila[0] if fila else db.ahora(),
            ),
        )
        for indice, unidad in enumerate(curso.temario.unidades):
            guion = curso.guiones.get(indice)
            guia = curso.guias.get(indice)
            conexion.execute(
                "INSERT OR REPLACE INTO clases"
                "(indice, titulo, objetivo, conceptos, guion, leccion_md, guia, "
                "actualizado_en) VALUES(?,?,?,?,?,?,?,?)",
                (
                    indice,
                    unidad.titulo,
                    unidad.objetivo,
                    json.dumps(unidad.conceptos, ensure_ascii=False),
                    json.dumps(_guion_a_json(guion), ensure_ascii=False)
                    if guion
                    else None,
                    curso.lecciones.get(indice),
                    json.dumps(_guia_a_json(guia), ensure_ascii=False)
                    if guia
                    else None,
                    db.ahora(),
                ),
            )


def guardar_plan_md(ruta: Path, plan_md: str) -> None:
    """Guarda el plan Markdown del curso en la BD (metadata del diseño)."""
    with db.abrir(ruta) as conexion:
        conexion.execute("UPDATE curso SET plan_md = ? WHERE id = 1", (plan_md,))


def cargar_plan_md(ruta: Path) -> str:
    """El plan Markdown del curso, o '' si no existe."""
    if not ruta.exists():
        return ""
    with db.abrir(ruta) as conexion:
        fila = conexion.execute("SELECT plan_md FROM curso WHERE id = 1").fetchone()
    return fila[0] if fila else ""


def cargar_curso(ruta: Path) -> Curso | None:
    """Carga el diseño del curso desde la BD ``ruta``.

    Una BD corrupta no es fatal: se advierte y se devuelve ``None`` para
    que el temario se regenere (cuesta una llamada; no bloquea al estudiante).
    """
    if not ruta.exists():
        return None
    try:
        with db.abrir(ruta) as conexion:
            fila = conexion.execute(
                "SELECT lenguaje, artefactos FROM curso WHERE id = 1"
            ).fetchone()
            if not fila:
                return None
            filas_clases = conexion.execute(
                "SELECT indice, titulo, objetivo, conceptos, guion, leccion_md, "
                "guia FROM clases ORDER BY indice"
            ).fetchall()
        unidades: list[Unidad] = []
        lecciones: dict[int, str] = {}
        guiones: dict[int, GuionLeccion] = {}
        guias: dict[int, Guia] = {}
        for indice, titulo, objetivo, conceptos, guion, leccion, guia in filas_clases:
            unidades.append(
                Unidad(
                    titulo=str(titulo),
                    objetivo=str(objetivo),
                    conceptos=[str(c) for c in json.loads(conceptos)],
                )
            )
            if leccion:
                lecciones[int(indice)] = str(leccion)
            if guion:
                guiones[int(indice)] = validar_guion(json.loads(guion))
            if guia:
                guias[int(indice)] = validar_guia(json.loads(guia))
        if not MIN_UNIDADES <= len(unidades) <= MAX_UNIDADES:
            raise ValueError(f"número de clases inválido: {len(unidades)}")
        artefactos = {
            str(clave): str(html) for clave, html in json.loads(fila[1]).items()
        }
        return Curso(
            temario=Temario(lenguaje=str(fila[0]), unidades=unidades),
            lecciones=lecciones,
            guiones=guiones,
            guias=guias,
            artefactos=artefactos,
        )
    except (
        sqlite3.DatabaseError,
        json.JSONDecodeError,
        ValueError,
        KeyError,
        TypeError,
    ) as error:
        logger.warning(
            "Curso corrupto en %s (%s); se regenerará el temario.", ruta, error
        )
        return None
