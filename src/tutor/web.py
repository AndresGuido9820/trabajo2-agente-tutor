"""Interfaz web simple: API REST sobre el mismo ``Agente`` (HU-11).

La web es otra UI, igual que la CLI: toda la lógica vive en ``Agente``.
Single-user local (sin auth), pensada para correr en la máquina del
estudiante con ``uv run tutor-web``. Las respuestas correctas de los
quizzes nunca viajan al navegador antes de calificar.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from tutor import db
from tutor.agente import ARCHIVO_DB, ARCHIVO_PERFIL, Agente, perfil_o_none
from tutor.config import NOTA_APROBATORIA, Configuracion, cargar_configuracion
from tutor.curso import (
    cargar_plan_md,
    guardar_curso,
    guardar_plan_md,
    plan_markdown,
    validar_temario,
)
from tutor.errores import ErrorBloqueada, ErrorConfiguracion, ErrorLLM
from tutor.evaluacion import Quiz
from tutor.llm import ClienteLLM, ClienteOpenAI, pedir_json
from tutor.models import Nivel, Objetivo, PerfilEstudiante
from tutor.perfil import guardar_perfil, validar_perfil_extraido
from tutor.prompts import prompt_creacion, prompt_extraer_perfil, system_creacion

logger = logging.getLogger(__name__)

RUTA_INDEX = Path(__file__).parent / "static" / "index.html"
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


class ClaseDiseno(BaseModel):
    """Una clase dentro de la edición estructurada del diseño (HU-20)."""

    titulo: str
    objetivo: str
    conceptos: list[str]


class CuerpoDiseno(BaseModel):
    """Body de la edición estructurada del diseño del curso."""

    lenguaje: str
    clases: list[ClaseDiseno]


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
        """Mueve el formato de un solo curso a ``cursos/1/`` (una vez)."""
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

    @app.get("/")
    def raiz() -> FileResponse:
        """Sirve la página única del front (sin caché: siempre la última versión)."""
        return FileResponse(RUTA_INDEX, headers={"Cache-Control": "no-store"})

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
            cursos.append(
                {
                    "id": curso_id,
                    "nombre": nombre,
                    "lenguaje": lenguaje,
                    "aprobadas": aprobadas,
                    "total": total,
                    "activo": curso_id == estado.activo,
                }
            )
        return {"cursos": cursos}

    @app.post("/api/cursos")
    def api_crear_curso_nuevo() -> dict[str, Any]:
        """Crea un curso vacío (se diseña conversando) y lo activa."""
        return {"id": estado.crear_curso()}

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
        agente = estado.agente
        temario = _con_llm(lambda: agente.curso).temario
        plan = plan_markdown(temario, descripcion)
        guardar_plan_md(estado.ruta_db, plan)  # metadata del diseño en la BD
        (estado.dir_activo / "curso.md").write_text(plan, "utf-8")
        return {"mensaje": turno["mensaje"], "listo": True}

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

    @app.get("/api/historial/{canal}")
    def api_historial(canal: str) -> dict[str, Any]:
        """Historial de una conversación ('creacion' o 'u<indice>')."""
        return {"mensajes": db.historial_chat(estado.ruta_db, canal)}

    @app.get("/api/conversaciones")
    def api_conversaciones() -> dict[str, Any]:
        """Cuántos mensajes tiene cada conversación (para la barra lateral)."""
        return {"canales": db.resumen_chats(estado.ruta_db)}

    @app.post("/api/artefacto")
    def api_artefacto_unidad(cuerpo: CuerpoEstudio) -> dict[str, Any]:
        """Mini-artefacto interactivo de la unidad actual del chat."""
        agente = _agente()
        unidad = cuerpo.unidad if cuerpo.unidad is not None else agente.unidad_actual

        def operacion() -> str:
            try:
                return agente.artefacto_de_unidad(unidad)
            except ValueError as error:
                raise HTTPException(400, str(error)) from error

        return {"html": _con_llm(operacion)}

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
                {"enunciado": p.enunciado, "opciones": p.opciones}
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
        return {
            "nota": resultado.nota,
            "aprobado": resultado.nota >= NOTA_APROBATORIA,
            "nota_aprobatoria": NOTA_APROBATORIA,
            "puntos_totales": agente.progreso.puntos,
            "conceptos_fallados": resultado.conceptos_fallados,
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
