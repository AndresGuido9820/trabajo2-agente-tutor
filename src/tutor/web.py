"""Interfaz web simple: API REST sobre el mismo ``Agente`` (HU-11).

La web es otra UI, igual que la CLI: toda la lógica vive en ``Agente``.
Single-user local (sin auth), pensada para correr en la máquina del
estudiante con ``uv run tutor-web``. Las respuestas correctas de los
quizzes nunca viajan al navegador antes de calificar.
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tutor import db
from tutor.agente import ARCHIVO_DB, ARCHIVO_PERFIL, Agente, perfil_o_none
from tutor.config import (
    HORAS_PARA_REENCUENTRO,
    NOTA_APROBATORIA,
    PRECIOS_MODELO,
    PREGUNTAS_DIAGNOSTICO,
    Configuracion,
    cargar_configuracion,
)
from tutor.curso import (
    cargar_plan_md,
    guardar_curso,
    guardar_plan_md,
    plan_markdown,
    validar_temario,
)
from tutor.errores import ErrorBloqueada, ErrorConfiguracion, ErrorDatos, ErrorLLM
from tutor.evaluacion import Quiz, resumenes, validar_quiz
from tutor.exportar import paquete_zip
from tutor.imagenes import ilustrar_unidad
from tutor.llm import ClienteLLM, ClienteOpenAI, pedir_json
from tutor.models import Nivel, Objetivo, PerfilEstudiante
from tutor.perfil import guardar_perfil, validar_perfil_extraido
from tutor.prompts import (
    prompt_creacion,
    prompt_diagnostico,
    prompt_extraer_perfil,
    system_creacion,
    system_tutor,
)

logger = logging.getLogger(__name__)

RUTA_INDEX = Path(__file__).parent / "static" / "index.html"
RUTA_DIST = Path(__file__).parent / "static" / "dist"
HOST = "127.0.0.1"
PUERTO = 8017


class CuerpoPerfil(BaseModel):
    """Body de creación de perfil."""

    nivel: str
    objetivo: str
    experiencia: str = ""
    objetivo_detalle: str = ""
    lenguaje: str = ""


class CuerpoTurno(BaseModel):
    """Body de un turno de lección: la respuesta del estudiante."""

    mensaje: str


class CuerpoRespuestas(BaseModel):
    """Body de calificación: índice elegido por pregunta."""

    respuestas: list[int]


class CuerpoCheckpoint(BaseModel):
    """Body de respuesta a un checkpoint de la guía."""

    seccion: int
    opcion: int
    intento: int


class CuerpoMensaje(BaseModel):
    """Body de un turno del conversatorio."""

    mensaje: str = ""


class CuerpoPreguntaGuia(BaseModel):
    """Body de una pregunta al tutor durante la guía."""

    seccion: int
    mensaje: str


class CuerpoArtefacto(BaseModel):
    """Body de solicitud de mini-artefacto de una sección."""

    seccion: int


class CuerpoPromptCurso(BaseModel):
    """Body de creación de curso por prompt libre (HU-15)."""

    prompt: str


class CuerpoPlan(BaseModel):
    """Body de edición manual del plan del curso."""

    md: str


class CuerpoEstudio(BaseModel):
    """Body de un turno del estudio en chat (HU-16)."""

    mensaje: str | None = None
    unidad: int | None = None


class CuerpoDemo(BaseModel):
    """Body de la demo interactiva del chat (plan/v2/HU-27)."""

    unidad: int | None = None
    objetivo: int | None = None
    regenerar: bool = False


class CuerpoQuizIntermedio(BaseModel):
    """Body del mini-quiz que cierra un objetivo (plan/v2/HU-24)."""

    unidad: int
    respuestas: list[int]


class CuerpoRetoSuperado(BaseModel):
    """Body del reto de código superado (plan/v2/HU-28)."""

    unidad: int
    objetivo: int


class CuerpoPistaReto(BaseModel):
    """Body de la pista socrática del reto (plan/v2/HU-28)."""

    unidad: int
    codigo: str
    test_fallado: str


class ClaseDiseno(BaseModel):
    """Una clase dentro de la edición estructurada del diseño (HU-20)."""

    titulo: str
    objetivo: str
    conceptos: list[str]


class CuerpoDiseno(BaseModel):
    """Body de la edición estructurada del diseño del curso."""

    lenguaje: str
    clases: list[ClaseDiseno]


class CuerpoCursoPatch(BaseModel):
    """Body de edición de metadata de un curso (HU-29)."""

    nombre: str | None = None
    archivado: bool | None = None


class _SesionCurso:
    """Estado en memoria de un curso: su directorio, agente y sesión."""

    def __init__(self, directorio: Path, cliente: ClienteLLM) -> None:
        self.dir = directorio
        perfil = perfil_o_none(directorio)
        self.agente: Agente | None = (
            Agente(cliente, directorio, perfil) if perfil else None
        )
        self.quizzes: dict[int, Quiz] = {}
        self.creacion: list[tuple[str, str]] = []
        # Examen diagnóstico pendiente al crear el curso (HU-41).
        self.diagnostico: Quiz | None = None


class _Estado:
    """Estado del servidor: todos los cursos (HU-20) y el curso activo."""

    def __init__(self, configuracion: Configuracion, cliente: ClienteLLM) -> None:
        self.configuracion = configuracion
        self.cliente = cliente
        self._migrar_a_multicurso(configuracion.dir_datos)
        self.base = configuracion.dir_datos / "cursos"
        self.sesiones: dict[int, _SesionCurso] = {}
        if self.base.exists():
            for ruta in sorted(self.base.glob("*/tutor.db")):
                try:
                    curso_id = int(ruta.parent.name)
                except ValueError:
                    continue
                self.sesiones[curso_id] = _SesionCurso(ruta.parent, cliente)
        self.activo: int | None = min(self.sesiones) if self.sesiones else None

    @staticmethod
    def _migrar_a_multicurso(base: Path) -> None:
        """Mueve el formato de un solo curso a ``cursos/1/`` (una vez).

        IDEMPOTENTE: si ``cursos/`` ya existe, no hay nada que migrar —
        sin este candado, unos JSON legacy que quedaran en ``base`` se
        re-migraban en CADA arranque y aplastaban la BD real del curso 1
        (hallazgo 2026-07-21).
        """
        if (base / "cursos").exists():
            return
        db.migrar_json_legacy(base)  # JSON viejos → tutor.db si aplica
        vieja = base / ARCHIVO_DB
        if not vieja.exists():
            return
        destino = base / "cursos" / "1"
        destino.mkdir(parents=True, exist_ok=True)
        vieja.rename(destino / ARCHIVO_DB)
        if (base / "curso.md").exists():
            (base / "curso.md").rename(destino / "curso.md")
        logger.info("Curso existente migrado a %s", destino)

    def crear_curso(self) -> int:
        """Crea un curso vacío (se diseña conversando) y lo activa."""
        curso_id = max(self.sesiones, default=0) + 1
        directorio = self.base / str(curso_id)
        directorio.mkdir(parents=True, exist_ok=True)
        db.abrir(directorio / ARCHIVO_DB).close()
        self.sesiones[curso_id] = _SesionCurso(directorio, self.cliente)
        self.activo = curso_id
        return curso_id

    def sesion(self) -> _SesionCurso:
        """La sesión del curso activo.

        Raises:
            HTTPException: 409 si no hay ningún curso.
        """
        if self.activo is None or self.activo not in self.sesiones:
            raise HTTPException(409, "Crea un curso primero.")
        return self.sesiones[self.activo]

    # Propiedades de compatibilidad: los endpoints operan sobre el activo.
    @property
    def agente(self) -> Agente | None:
        if self.activo is None or self.activo not in self.sesiones:
            return None
        return self.sesiones[self.activo].agente

    @agente.setter
    def agente(self, valor: Agente | None) -> None:
        self.sesion().agente = valor

    @property
    def creacion(self) -> list[tuple[str, str]]:
        return self.sesion().creacion

    @property
    def quizzes(self) -> dict[int, Quiz]:
        return self.sesion().quizzes

    @property
    def ruta_db(self) -> Path:
        return self.sesion().dir / ARCHIVO_DB

    @property
    def dir_activo(self) -> Path:
        return self.sesion().dir

    def anotar(self, canal: str, rol: str, texto: str) -> None:
        """Agrega un mensaje al historial de una conversación (tabla chat)."""
        db.anotar_chat(self.ruta_db, canal, rol, texto)


def _disenar_curso(estado: _Estado, descripcion: str) -> None:
    """Genera el temario y persiste el plan del curso activo (HU-41)."""
    agente = estado.agente
    assert agente is not None
    temario = _con_llm_estatico(lambda: agente.curso).temario
    plan = plan_markdown(temario, descripcion)
    guardar_plan_md(estado.ruta_db, plan)
    (estado.dir_activo / "curso.md").write_text(plan, "utf-8")


def _con_llm_estatico(operacion: Callable[[], Any]) -> Any:
    """Versión de módulo de ``_con_llm`` (mapea ErrorLLM a 502)."""
    try:
        return operacion()
    except ErrorLLM as error:
        raise HTTPException(502, str(error)) from error


def crear_app(
    configuracion: Configuracion, cliente: ClienteLLM | None = None
) -> FastAPI:
    """Construye la aplicación web.

    Args:
        configuracion: Configuración efectiva.
        cliente: Cliente LLM; inyectable para pruebas (por defecto OpenAI).
    """
    estado = _Estado(configuracion, cliente or ClienteOpenAI(configuracion))
    app = FastAPI(title="Tutor de programación", docs_url=None, redoc_url=None)

    def _agente() -> Agente:
        """Agente activo o 409 si aún no hay perfil."""
        if estado.agente is None:
            raise HTTPException(409, "Primero crea tu perfil.")
        return estado.agente

    def _con_llm(operacion: Any) -> Any:
        """Ejecuta una operación mapeando errores de dominio a HTTP."""
        try:
            return operacion()
        except ErrorBloqueada as error:
            raise HTTPException(403, str(error)) from error
        except ErrorLLM as error:
            raise HTTPException(502, str(error)) from error

    if RUTA_DIST.exists():
        app.mount("/assets", StaticFiles(directory=RUTA_DIST / "assets"), "assets")

    @app.get("/")
    def raiz() -> FileResponse:
        """Sirve el front React (dist) o el HTML clásico si no hay build."""
        indice = RUTA_DIST / "index.html" if RUTA_DIST.exists() else RUTA_INDEX
        return FileResponse(indice, headers={"Cache-Control": "no-store"})

    @app.get("/api/estado")
    def api_estado() -> dict[str, Any]:
        """Perfil existente y temario con estados (lo genera si falta)."""
        if estado.agente is None:
            return {"perfil": False}
        agente = estado.agente
        curso = _con_llm(lambda: agente.curso)
        return {
            "perfil": True,
            "curso_id": estado.activo,
            "lenguaje": curso.temario.lenguaje,
            "puntos": agente.progreso.puntos,
            "racha": agente.progreso.racha,
            "nota_aprobatoria": NOTA_APROBATORIA,
            "unidad_actual": agente.unidad_actual,
            "unidades": [
                {
                    "indice": fila.indice,
                    "titulo": fila.titulo,
                    "objetivo": curso.temario.unidades[fila.indice].objetivo,
                    "conceptos": curso.temario.unidades[fila.indice].conceptos,
                    "estado": fila.estado.value,
                    "mejor_nota": fila.mejor_nota,
                    "completada": fila.indice in agente.progreso.completadas,
                }
                for fila in agente.filas_unidades()
            ],
        }

    @app.get("/api/cursos")
    def api_cursos() -> dict[str, Any]:
        """Todos los cursos del estudiante (menú "Mis cursos")."""
        cursos = []
        for curso_id, sesion in sorted(estado.sesiones.items()):
            nombre, lenguaje, aprobadas, total = "Curso sin diseñar", "", 0, 0
            if sesion.agente is not None:
                descripcion = sesion.agente.perfil.descripcion
                if sesion.agente.curso_ya_generado():
                    temario = sesion.agente.curso.temario
                    lenguaje = temario.lenguaje
                    total = len(temario.unidades)
                    aprobadas = sum(
                        1
                        for i in range(total)
                        if (sesion.agente.progreso.mejor_nota(i) or 0)
                        >= NOTA_APROBATORIA
                    )
                nombre = descripcion[:70] or f"Curso de {lenguaje or '…'}"
            meta = db.leer_meta_curso(sesion.dir / ARCHIVO_DB)
            cursos.append(
                {
                    "id": curso_id,
                    "nombre": str(meta["nombre"]) or nombre,
                    "archivado": bool(meta["archivado"]),
                    "lenguaje": lenguaje,
                    "aprobadas": aprobadas,
                    "total": total,
                    "activo": curso_id == estado.activo,
                }
            )
        return {"cursos": cursos}

    @app.patch("/api/cursos/{curso_id}")
    def api_editar_curso(curso_id: int, cuerpo: CuerpoCursoPatch) -> dict[str, Any]:
        """Renombra y/o archiva un curso (HU-29)."""
        if curso_id not in estado.sesiones:
            raise HTTPException(404, f"No existe el curso {curso_id}.")
        if cuerpo.nombre is not None and not cuerpo.nombre.strip():
            raise HTTPException(400, "El nombre no puede quedar vacío.")
        ruta = estado.sesiones[curso_id].dir / ARCHIVO_DB
        db.escribir_meta_curso(
            ruta,
            nombre=cuerpo.nombre.strip() if cuerpo.nombre is not None else None,
            archivado=cuerpo.archivado,
        )
        return {"ok": True}

    @app.delete("/api/cursos/{curso_id}")
    def api_borrar_curso(curso_id: int) -> dict[str, Any]:
        """Borra un curso moviéndolo a la papelera (HU-29, reversible)."""
        if curso_id not in estado.sesiones:
            raise HTTPException(404, f"No existe el curso {curso_id}.")
        sesion = estado.sesiones.pop(curso_id)
        papelera = estado.base / ".papelera"
        papelera.mkdir(parents=True, exist_ok=True)
        destino = papelera / f"{curso_id}-{db.ahora().replace(':', '-')}"
        shutil.move(str(sesion.dir), str(destino))
        if estado.activo == curso_id:
            estado.activo = min(estado.sesiones) if estado.sesiones else None
        logger.info("Curso %d movido a %s", curso_id, destino)
        return {"ok": True, "papelera": str(destino)}

    @app.post("/api/cursos")
    def api_crear_curso_nuevo() -> dict[str, Any]:
        """Crea un curso vacío (se diseña conversando) y lo activa."""
        return {"id": estado.crear_curso()}

    @app.get("/api/cursos/{curso_id}/exportar")
    def api_exportar_curso(curso_id: int) -> Response:
        """Paquete de estudio del curso (.zip de Markdown, HU-33)."""
        if curso_id not in estado.sesiones:
            raise HTTPException(404, f"No existe el curso {curso_id}.")
        try:
            datos = paquete_zip(estado.sesiones[curso_id].dir)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        return Response(
            content=datos,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="curso-{curso_id}.zip"'
            },
        )

    @app.post("/api/cursos/{curso_id}/activar")
    def api_activar_curso(curso_id: int) -> dict[str, Any]:
        """Cambia el curso activo (al que apuntan todos los endpoints)."""
        if curso_id not in estado.sesiones:
            raise HTTPException(404, f"No existe el curso {curso_id}.")
        estado.activo = curso_id
        return {"ok": True}

    @app.get("/api/diseno")
    def api_diseno() -> dict[str, Any]:
        """El diseño ESTRUCTURADO del curso (lo que el LLM recibe)."""
        agente = _agente()
        temario = _con_llm(lambda: agente.curso).temario
        return {
            "lenguaje": temario.lenguaje,
            "descripcion": agente.perfil.descripcion,
            "clases": [
                {
                    "indice": i,
                    "titulo": u.titulo,
                    "objetivo": u.objetivo,
                    "conceptos": u.conceptos,
                }
                for i, u in enumerate(temario.unidades)
            ],
        }

    @app.post("/api/diseno")
    def api_editar_diseno(cuerpo: CuerpoDiseno) -> dict[str, Any]:
        """Edición manual ESTRUCTURADA del diseño.

        Valida con las mismas reglas del temario (así el LLM siempre recibe
        datos limpios), persiste en la BD y regenera el plan Markdown.
        """
        agente = _agente()
        try:
            temario = validar_temario(
                {
                    "lenguaje": cuerpo.lenguaje,
                    "unidades": [
                        {
                            "titulo": c.titulo,
                            "objetivo": c.objetivo,
                            "conceptos": c.conceptos,
                        }
                        for c in cuerpo.clases
                    ],
                }
            )
        except (ValueError, KeyError) as error:
            raise HTTPException(400, f"Diseño inválido: {error}") from error
        curso = agente.curso
        curso.temario = temario
        guardar_curso(curso, estado.ruta_db)
        plan = plan_markdown(temario, agente.perfil.descripcion)
        guardar_plan_md(estado.ruta_db, plan)
        (estado.dir_activo / "curso.md").write_text(plan, "utf-8")
        return {"ok": True}

    def _validar_creacion(datos: Any) -> dict[str, Any]:
        """Valida el JSON del asesor de creación (mensaje/listo/perfil)."""
        if not isinstance(datos, dict) or "mensaje" not in datos:
            raise ValueError("falta el campo 'mensaje'")
        listo = bool(datos.get("listo"))
        if listo and not isinstance(datos.get("perfil"), dict):
            raise ValueError("con listo=true debe venir el perfil")
        return {
            "mensaje": str(datos["mensaje"]),
            "listo": listo,
            "perfil": datos.get("perfil"),
        }

    @app.post("/api/creacion")
    def api_creacion(cuerpo: CuerpoMensaje) -> dict[str, Any]:
        """Turno de la conversación que diseña el curso (HU-16).

        Cuando el asesor marca listo (el estudiante confirmó), crea el
        perfil, genera el temario y guarda el plan en ``curso.md``.
        """
        if estado.activo is None:
            estado.crear_curso()
        if estado.agente is not None:
            raise HTTPException(409, "Ya tienes un curso creado.")
        mensaje = cuerpo.mensaje.strip()
        if not mensaje:
            raise HTTPException(400, "Cuéntame qué quieres aprender.")

        turno = _con_llm(
            lambda: pedir_json(
                estado.cliente,
                system=system_creacion(),
                prompt=prompt_creacion(estado.creacion, mensaje),
                validar=_validar_creacion,
            )
        )
        estado.creacion.append((mensaje, turno["mensaje"]))
        estado.anotar("creacion", "yo", mensaje)
        estado.anotar("creacion", "tutor", turno["mensaje"])
        if not turno["listo"]:
            return {"mensaje": turno["mensaje"], "listo": False}

        descripcion = estado.creacion[0][0]
        try:
            perfil = validar_perfil_extraido(turno["perfil"], descripcion)
        except (ValueError, KeyError) as error:
            raise HTTPException(502, f"Perfil extraído inválido: {error}") from error
        guardar_perfil(perfil, estado.dir_activo / ARCHIVO_PERFIL)
        estado.agente = Agente(estado.cliente, estado.dir_activo, perfil)
        # Examen diagnóstico (HU-41): mide el conocimiento REAL antes de
        # diseñar el temario. Si su generación falla, el curso se crea
        # igual sin examen (degradación: el diagnóstico es un plus).
        try:
            # OJO: system_tutor, no system_creacion — el system del asesor
            # OBLIGA al contrato {mensaje, listo, perfil} y el modelo jamás
            # devolvería el quiz (visto contra la API real).
            quiz = pedir_json(
                estado.cliente,
                system=system_tutor(perfil),
                prompt=prompt_diagnostico(perfil),
                validar=lambda datos: validar_quiz(datos, 0, PREGUNTAS_DIAGNOSTICO),
            )
            estado.sesion().diagnostico = quiz
            return {
                "mensaje": turno["mensaje"],
                "listo": True,
                "diagnostico": [
                    {"enunciado": p.enunciado, "opciones": p.opciones}
                    for p in quiz.preguntas
                ],
            }
        except ErrorLLM:
            logger.warning("Diagnóstico no disponible; se crea el curso directo")
            _disenar_curso(estado, descripcion)
            return {"mensaje": turno["mensaje"], "listo": True, "diagnostico": None}

    @app.post("/api/diagnostico/calificar")
    def api_diagnostico_calificar(cuerpo: CuerpoRespuestas) -> dict[str, Any]:
        """Califica el examen diagnóstico y AHÍ SÍ diseña el curso (HU-41).

        El resultado (qué domina y qué falló) se incorpora al perfil, así
        el temario y todas las clases se calibran al conocimiento real.
        """
        sesion = estado.sesion()
        quiz = sesion.diagnostico
        if quiz is None:
            raise HTTPException(409, "No hay un examen diagnóstico pendiente.")
        if len(cuerpo.respuestas) != len(quiz.preguntas):
            raise HTTPException(400, f"Se esperaban {len(quiz.preguntas)} respuestas.")
        detalle = []
        dominados: list[str] = []
        brechas: list[str] = []
        for pregunta, respuesta in zip(quiz.preguntas, cuerpo.respuestas, strict=True):
            if not 0 <= respuesta < len(pregunta.opciones):
                raise HTTPException(400, f"Respuesta fuera de rango: {respuesta}")
            acierto = respuesta == pregunta.correcta
            (dominados if acierto else brechas).append(pregunta.concepto)
            detalle.append(
                {
                    "acierto": acierto,
                    "elegida": pregunta.opciones[respuesta],
                    "correcta": pregunta.opciones[pregunta.correcta],
                    "explicacion": pregunta.explicacion,
                }
            )
        sesion.diagnostico = None
        agente = _agente()
        resumen = (
            f"Diagnóstico inicial {len(dominados)}/{len(quiz.preguntas)}: "
            + (f"domina {', '.join(dominados)}" if dominados else "sin aciertos")
            + (f"; brechas en {', '.join(brechas)}" if brechas else "")
            + "."
        )
        # El diagnóstico entra al perfil: el temario y las clases lo usan.
        perfil = replace(
            agente.perfil,
            experiencia=(agente.perfil.experiencia + " " + resumen).strip(),
        )
        guardar_perfil(perfil, estado.dir_activo / ARCHIVO_PERFIL)
        estado.agente = Agente(estado.cliente, estado.dir_activo, perfil)
        _disenar_curso(estado, perfil.descripcion)
        return {
            "aciertos": len(dominados),
            "total": len(quiz.preguntas),
            "resumen": resumen,
            "detalle": detalle,
        }

    @app.post("/api/plan")
    def api_actualizar_plan(cuerpo: CuerpoPlan) -> dict[str, Any]:
        """Guarda el plan editado a mano (BD + copia curso.md)."""
        _agente()
        plan = cuerpo.md.strip()
        if not plan:
            raise HTTPException(400, "El plan no puede quedar vacío.")
        guardar_plan_md(estado.ruta_db, plan)
        (estado.dir_activo / "curso.md").write_text(plan, "utf-8")
        return {"ok": True}

    @app.get("/api/plan")
    def api_plan() -> dict[str, Any]:
        """El plan del curso (diseño en la BD; curso.md es la copia legible)."""
        agente = _agente()
        plan = cargar_plan_md(estado.ruta_db)
        if not plan:  # cursos creados antes de guardar el plan: reconstruir
            plan = plan_markdown(agente.curso.temario, agente.perfil.descripcion)
            guardar_plan_md(estado.ruta_db, plan)
        return {"md": plan}

    @app.post("/api/estudio")
    def api_estudio(cuerpo: CuerpoEstudio) -> dict[str, Any]:
        """Turno del estudio en chat continuo; con `unidad` (re)inicia esa lección."""
        agente = _agente()
        r = dict(_con_llm(lambda: agente.turno_estudio(cuerpo.mensaje, cuerpo.unidad)))
        canal = f"u{r['unidad']}"
        if cuerpo.mensaje:
            estado.anotar(canal, "yo", cuerpo.mensaje)
        estado.anotar(canal, "tutor", str(r["texto"]))
        return r

    @app.post("/api/estudio/quiz-intermedio")
    def api_quiz_intermedio(cuerpo: CuerpoQuizIntermedio) -> dict[str, Any]:
        """Califica el mini-quiz que cierra un objetivo del guion v2 (HU-24)."""
        agente = _agente()

        def operacion() -> dict[str, Any]:
            try:
                return agente.responder_quiz_intermedio(
                    cuerpo.unidad, cuerpo.respuestas
                )
            except ErrorDatos as error:
                raise HTTPException(409, str(error)) from error
            except ValueError as error:
                raise HTTPException(400, str(error)) from error

        r = _con_llm(operacion)
        estado.anotar(f"u{cuerpo.unidad}", "tutor", str(r["texto"]))
        return dict(r)

    @app.post("/api/estudio/reto-superado")
    def api_reto_superado(cuerpo: CuerpoRetoSuperado) -> dict[str, Any]:
        """Marca un reto de código como superado: +10 ⭐ una vez (HU-28)."""
        agente = _agente()

        def operacion() -> dict[str, Any]:
            try:
                return agente.reto_superado(cuerpo.unidad, cuerpo.objetivo)
            except ErrorDatos as error:
                raise HTTPException(409, str(error)) from error

        r = _con_llm(operacion)
        estado.anotar(f"u{cuerpo.unidad}", "tutor", str(r["texto"]))
        return dict(r)

    @app.post("/api/estudio/pista-reto")
    def api_pista_reto(cuerpo: CuerpoPistaReto) -> dict[str, Any]:
        """Pista socrática sobre el reto, con el código del estudiante."""
        agente = _agente()

        def operacion() -> str:
            try:
                return agente.pista_reto(
                    cuerpo.unidad, cuerpo.codigo, cuerpo.test_fallado
                )
            except ErrorDatos as error:
                raise HTTPException(409, str(error)) from error

        texto = _con_llm(operacion)
        estado.anotar(f"u{cuerpo.unidad}", "tutor", texto)
        return {"texto": texto}

    @app.post("/api/estudio/stream")
    def api_estudio_stream(cuerpo: CuerpoEstudio) -> StreamingResponse:
        """Turno del estudio transmitido por SSE (HU-35).

        Eventos: ``delta`` ({"texto": ...}), ``fin`` (mismo payload que
        /api/estudio) y ``error``. Si el cliente se desconecta a mitad, el
        turno se completa y persiste igual en el servidor.
        """
        agente = _agente()

        def _sse(evento: str, datos: dict[str, Any]) -> str:
            return f"event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"

        def _persistir(fin: dict[str, Any]) -> None:
            canal = f"u{fin['unidad']}"
            if cuerpo.mensaje:
                estado.anotar(canal, "yo", cuerpo.mensaje)
            estado.anotar(canal, "tutor", str(fin["texto"]))

        def eventos() -> Iterator[str]:
            turnos = agente.turno_estudio_stream(cuerpo.mensaje, cuerpo.unidad)
            try:
                for evento in turnos:
                    if "fin" in evento:
                        _persistir(evento["fin"])
                        yield _sse("fin", evento["fin"])
                    else:
                        yield _sse("delta", {"texto": evento["delta"]})
            except GeneratorExit:
                # Cliente desconectado: el turno se termina y persiste igual.
                for evento in turnos:
                    if "fin" in evento:
                        _persistir(evento["fin"])
                raise
            except (ErrorLLM, ErrorBloqueada, KeyError, IndexError) as error:
                yield _sse("error", {"detail": str(error)})

        return StreamingResponse(eventos(), media_type="text/event-stream")

    @app.get("/api/historial/{canal}")
    def api_historial(canal: str) -> dict[str, Any]:
        """Historial de una conversación ('creacion' o 'u<indice>')."""
        return {
            "mensajes": db.historial_con_ids(estado.ruta_db, canal),
            "ultimo_en": db.ultimo_mensaje_en(estado.ruta_db, canal),
            "horas_reencuentro": HORAS_PARA_REENCUENTRO,
        }

    @app.get("/api/buscar")
    def api_buscar(q: str = "") -> dict[str, Any]:
        """Búsqueda global (HU-37): clases y mensajes de TODOS los cursos."""
        consulta = q.strip()
        if len(consulta) < 2:
            return {"clases": [], "mensajes": []}
        clases: list[dict[str, Any]] = []
        mensajes: list[dict[str, Any]] = []
        for curso_id, sesion in sorted(estado.sesiones.items()):
            ruta = sesion.dir / ARCHIVO_DB
            meta = db.leer_meta_curso(ruta)
            etiqueta = str(meta["nombre"]) or f"Curso {curso_id}"
            if meta["archivado"]:
                etiqueta += " (archivado)"
            for c in db.buscar_clases(ruta, consulta, 8 - len(clases)):
                clases.append({"curso": curso_id, "curso_nombre": etiqueta, **c})
            for m in db.buscar_mensajes(ruta, consulta, 8 - len(mensajes)):
                mensajes.append({"curso": curso_id, "curso_nombre": etiqueta, **m})
            if len(clases) >= 8 and len(mensajes) >= 8:
                break
        return {"clases": clases, "mensajes": mensajes}

    @app.get("/api/clase/{indice}/imagen")
    def api_imagen_clase(indice: int) -> FileResponse:
        """Ilustración de la clase (HU-08, bonus): genera con cache.

        404 si el flag ``TUTOR_IMAGENES`` está apagado, la unidad no
        existe o la generación falló (la clase funciona igual sin imagen).
        """
        agente = _agente()
        if not configuracion.imagenes:
            raise HTTPException(404, "Las ilustraciones están desactivadas.")
        if not 0 <= indice < len(_con_llm(lambda: agente.curso).temario.unidades):
            raise HTTPException(404, f"No existe la clase {indice}.")
        unidad = agente.curso.temario.unidades[indice]
        ruta = ilustrar_unidad(
            estado.cliente,
            estado.dir_activo,
            indice,
            unidad.titulo,
            unidad.conceptos,
            agente.curso.temario.lenguaje,
        )
        if ruta is None:
            raise HTTPException(404, "No hay ilustración para esta clase.")
        return FileResponse(ruta, media_type="image/png")

    @app.get("/api/clase/{indice}/panel")
    def api_panel_clase(indice: int) -> dict[str, Any]:
        """Objetivos y avance de la clase para el panel lateral (HU-25)."""
        try:
            return _agente().panel_de_clase(indice)
        except IndexError as error:
            raise HTTPException(404, str(error)) from error

    @app.post("/api/clase/{indice}/reencuentro")
    def api_reencuentro(indice: int) -> dict[str, Any]:
        """Resumen de bienvenida al volver a una clase tras horas de pausa."""
        agente = _agente()

        def operacion() -> str:
            try:
                return agente.reencuentro(indice)
            except IndexError as error:
                raise HTTPException(404, str(error)) from error

        texto = _con_llm(operacion)
        estado.anotar(f"u{indice}", "tutor", texto)
        return {"texto": texto}

    @app.get("/api/estadisticas")
    def api_estadisticas() -> dict[str, Any]:
        """Métricas de aprendizaje del curso activo (vista Mi progreso)."""
        return _agente().estadisticas()

    @app.get("/api/repaso")
    def api_repaso() -> dict[str, Any]:
        """Cuántos ítems de repaso vencen hoy y cuándo es el próximo."""
        return _agente().estado_repaso()

    @app.post("/api/repaso/iniciar")
    def api_repaso_iniciar() -> dict[str, Any]:
        """Genera el quiz del repaso del día (409 si no hay vencidos)."""
        agente = _agente()

        def operacion() -> dict[str, Any]:
            try:
                quiz = agente.iniciar_repaso()
            except ErrorDatos as error:
                raise HTTPException(409, str(error)) from error
            return {
                "preguntas": [
                    {"enunciado": p.enunciado, "opciones": p.opciones}
                    for p in quiz.preguntas
                ]
            }

        return dict(_con_llm(operacion))

    @app.post("/api/repaso/calificar")
    def api_repaso_calificar(cuerpo: CuerpoRespuestas) -> dict[str, Any]:
        """Califica el repaso localmente y reprograma la cola 1-3-7."""
        try:
            return _agente().calificar_repaso(cuerpo.respuestas)
        except ErrorDatos as error:
            raise HTTPException(409, str(error)) from error
        except (IndexError, ValueError) as error:
            raise HTTPException(400, f"Respuestas inválidas: {error}") from error

    @app.get("/api/uso")
    def api_uso() -> dict[str, Any]:
        """Uso del LLM por día/carril con costo estimado (HU-39, global)."""
        filas = db.resumen_uso(configuracion.dir_datos / "uso.db")
        for fila in filas:
            precios = PRECIOS_MODELO.get(fila["modelo"])
            fila["costo_usd"] = (
                round(
                    fila["tokens_prompt"] / 1e6 * precios[0]
                    + fila["tokens_salida"] / 1e6 * precios[1],
                    4,
                )
                if precios
                else None
            )
        return {"uso": filas}

    @app.get("/api/conversaciones")
    def api_conversaciones() -> dict[str, Any]:
        """Cuántos mensajes tiene cada conversación (para la barra lateral)."""
        return {"canales": db.resumen_chats(estado.ruta_db)}

    @app.post("/api/artefacto")
    def api_artefacto_unidad(cuerpo: CuerpoDemo) -> dict[str, Any]:
        """Demo interactiva de la clase o de un objetivo (HU-27).

        Con ``objetivo`` la demo ilustra ESE objetivo del guion v2;
        ``regenerar`` invalida el cache de esa demo.
        """
        agente = _agente()
        unidad = cuerpo.unidad if cuerpo.unidad is not None else agente.unidad_actual

        def operacion() -> dict[str, Any]:
            try:
                return agente.artefacto(unidad, cuerpo.objetivo, cuerpo.regenerar)
            except ValueError as error:
                raise HTTPException(400, str(error)) from error

        return dict(_con_llm(operacion))

    @app.post("/api/curso")
    def api_crear_curso(cuerpo: CuerpoPromptCurso) -> dict[str, Any]:
        """Crea el curso desde una petición libre: "hazme un curso de…"."""
        if estado.activo is None:
            estado.crear_curso()
        texto = cuerpo.prompt.strip()
        if len(texto) < 8:
            raise HTTPException(400, "Cuéntame un poco más: ¿qué quieres aprender?")
        cliente = estado.cliente

        def operacion() -> PerfilEstudiante:
            return pedir_json(
                cliente,
                system="Eres un extractor preciso de perfiles de estudiantes.",
                prompt=prompt_extraer_perfil(texto),
                validar=lambda datos: validar_perfil_extraido(datos, texto),
            )

        perfil = _con_llm(operacion)
        guardar_perfil(perfil, estado.dir_activo / ARCHIVO_PERFIL)
        estado.agente = Agente(cliente, estado.dir_activo, perfil)
        return {"ok": True}

    @app.post("/api/perfil")
    def api_perfil(cuerpo: CuerpoPerfil) -> dict[str, Any]:
        """Crea el perfil del estudiante y arma la sesión del agente."""
        if estado.activo is None:
            estado.crear_curso()
        try:
            perfil = PerfilEstudiante(
                nivel=Nivel(cuerpo.nivel),
                experiencia=cuerpo.experiencia.strip(),
                objetivo=Objetivo(cuerpo.objetivo),
                objetivo_detalle=cuerpo.objetivo_detalle.strip(),
                lenguaje=cuerpo.lenguaje.strip().lower(),
            )
        except ValueError as error:
            raise HTTPException(400, f"Perfil inválido: {error}") from error
        guardar_perfil(perfil, estado.dir_activo / ARCHIVO_PERFIL)
        estado.agente = Agente(estado.cliente, estado.dir_activo, perfil)
        return {"ok": True}

    @app.post("/api/leccion/{indice}/iniciar")
    def api_iniciar_leccion(indice: int) -> dict[str, Any]:
        """Genera/carga el guion y devuelve el primer turno del tutor."""
        agente = _agente()

        def operacion() -> dict[str, Any]:
            try:
                guion = agente.iniciar_leccion(indice)
            except IndexError as error:
                raise HTTPException(404, str(error)) from error
            texto, terminada = agente.turno_leccion(indice, None)
            paso, total = agente.avance_leccion(indice)
            return {
                "objetivos": guion.objetivos,
                "ruta": [p.tipo for p in guion.pasos],
                "texto": texto,
                "paso": paso,
                "total": total,
                "terminada": terminada,
            }

        resultado: dict[str, Any] = _con_llm(operacion)
        return resultado

    @app.post("/api/leccion/{indice}/turno")
    def api_turno(indice: int, cuerpo: CuerpoTurno) -> dict[str, Any]:
        """Avanza la lección conversada con la respuesta del estudiante."""
        agente = _agente()

        def operacion() -> dict[str, Any]:
            try:
                texto, terminada = agente.turno_leccion(
                    indice, cuerpo.mensaje.strip() or "ok, sigamos"
                )
            except KeyError as error:
                raise HTTPException(409, "La lección no está iniciada.") from error
            paso, total = agente.avance_leccion(indice)
            return {
                "texto": texto,
                "paso": paso,
                "total": total,
                "terminada": terminada,
            }

        resultado: dict[str, Any] = _con_llm(operacion)
        return resultado

    @app.post("/api/guia/{indice}")
    def api_guia(indice: int) -> dict[str, Any]:
        """Guía interactiva de la unidad, SIN correctas/pistas/explicaciones."""
        agente = _agente()

        def operacion() -> Any:
            try:
                return agente.guia_de_unidad(indice)
            except IndexError as error:
                raise HTTPException(404, str(error)) from error

        guia = _con_llm(operacion)
        return {
            "puntos": agente.progreso.puntos,
            "secciones": [
                {
                    "objetivo": s.objetivo,
                    "contenido": s.contenido,
                    "checkpoint": {
                        "pregunta": s.checkpoint.pregunta,
                        "opciones": s.checkpoint.opciones,
                    },
                }
                for s in guia.secciones
            ],
        }

    @app.post("/api/guia/{indice}/checkpoint")
    def api_checkpoint(indice: int, cuerpo: CuerpoCheckpoint) -> dict[str, Any]:
        """Califica un checkpoint en el servidor y asigna puntos."""
        agente = _agente()
        try:
            r = agente.responder_checkpoint(
                indice, cuerpo.seccion, cuerpo.opcion, cuerpo.intento
            )
        except KeyError as error:
            raise HTTPException(409, "La guía no está generada.") from error
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        return {
            "correcto": r.correcto,
            "texto": r.texto,
            "revelada": r.revelada,
            "puntos": r.puntos,
            "puntos_totales": r.puntos_totales,
        }

    @app.post("/api/guia/{indice}/artefacto")
    def api_artefacto(indice: int, cuerpo: CuerpoArtefacto) -> dict[str, Any]:
        """Mini-artefacto HTML interactivo de la sección (iframe sandbox)."""
        agente = _agente()

        def operacion() -> str:
            try:
                return agente.artefacto_de_seccion(indice, cuerpo.seccion)
            except KeyError as error:
                raise HTTPException(409, "La guía no está generada.") from error
            except ValueError as error:
                raise HTTPException(400, str(error)) from error

        return {"html": _con_llm(operacion)}

    @app.post("/api/guia/{indice}/pregunta")
    def api_pregunta_guia(indice: int, cuerpo: CuerpoPreguntaGuia) -> dict[str, Any]:
        """Pregunta libre al tutor sobre la sección actual de la guía."""
        agente = _agente()

        def operacion() -> str:
            try:
                return agente.preguntar_guia(indice, cuerpo.seccion, cuerpo.mensaje)
            except KeyError as error:
                raise HTTPException(409, "La guía no está generada.") from error
            except ValueError as error:
                raise HTTPException(400, str(error)) from error

        return {"texto": _con_llm(operacion)}

    @app.post("/api/conversatorio/{indice}")
    def api_conversatorio(indice: int, cuerpo: CuerpoMensaje) -> dict[str, Any]:
        """Turno del conversatorio socrático de dudas tras reprobar."""
        agente = _agente()
        texto = _con_llm(lambda: agente.conversatorio(indice, cuerpo.mensaje))
        if cuerpo.mensaje:
            estado.anotar(f"u{indice}", "yo", cuerpo.mensaje)
        estado.anotar(f"u{indice}", "tutor", texto)
        return {"texto": texto}

    @app.post("/api/quiz/{indice}")
    def api_quiz(indice: int) -> dict[str, Any]:
        """Genera el quiz y lo devuelve SIN respuestas correctas."""
        agente = _agente()

        def operacion() -> Quiz:
            try:
                return agente.quiz_de_unidad(indice)
            except IndexError as error:
                raise HTTPException(404, str(error)) from error

        quiz = _con_llm(operacion)
        estado.quizzes[indice] = quiz
        return {
            "preguntas": [
                {"enunciado": p.enunciado, "opciones": p.opciones, "nivel": p.nivel}
                for p in quiz.preguntas
            ]
        }

    @app.post("/api/quiz/{indice}/calificar")
    def api_calificar(indice: int, cuerpo: CuerpoRespuestas) -> dict[str, Any]:
        """Califica el quiz en el servidor y registra el progreso."""
        agente = _agente()
        quiz = estado.quizzes.pop(indice, None)
        if quiz is None:
            raise HTTPException(409, "No hay un quiz activo para esa unidad.")
        try:
            resultado, detalle = agente.calificar_quiz(quiz, cuerpo.respuestas)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        estado.anotar(
            f"u{indice}",
            "sistema",
            f"🎯 Evaluación: {resultado.nota}/100 — "
            + ("aprobada 🎉" if resultado.nota >= NOTA_APROBATORIA else "a reintentar"),
        )
        agrupados = resumenes(detalle)
        return {
            "nota": resultado.nota,
            "aprobado": resultado.nota >= NOTA_APROBATORIA,
            "nota_aprobatoria": NOTA_APROBATORIA,
            "puntos_totales": agente.progreso.puntos,
            "conceptos_fallados": resultado.conceptos_fallados,
            "resumen_conceptos": agrupados["conceptos"],
            "resumen_niveles": agrupados["niveles"],
            "detalle": [
                {
                    "acierto": r.acierto,
                    "elegida": r.pregunta.opciones[r.respuesta],
                    "correcta": r.pregunta.opciones[r.pregunta.correcta],
                    "explicacion": r.pregunta.explicacion,
                }
                for r in detalle
            ],
        }

    @app.get("/api/progreso")
    def api_progreso() -> dict[str, Any]:
        """Tabla de avance del estudiante."""
        agente = _agente()
        return {
            "filas": [
                {
                    "indice": fila.indice,
                    "titulo": fila.titulo,
                    "vista": fila.indice in agente.progreso.vistas,
                    "intentos": agente.progreso.intentos(fila.indice),
                    "mejor_nota": fila.mejor_nota,
                }
                for fila in agente.filas_unidades()
            ]
        }

    return app


def main() -> int:
    """Arranca el servidor web local del tutor."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        configuracion = cargar_configuracion()
    except ErrorConfiguracion as error:
        print(f"Error: {error}")
        return 1
    print(f"Tutor web en http://{HOST}:{PUERTO}")
    uvicorn.run(crear_app(configuracion), host=HOST, port=PUERTO, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
