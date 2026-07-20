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

from tutor.agente import ARCHIVO_PERFIL, Agente, perfil_o_none
from tutor.config import NOTA_APROBATORIA, Configuracion, cargar_configuracion
from tutor.errores import ErrorBloqueada, ErrorConfiguracion, ErrorLLM
from tutor.evaluacion import Quiz
from tutor.llm import ClienteLLM, ClienteOpenAI, pedir_json
from tutor.models import Nivel, Objetivo, PerfilEstudiante
from tutor.perfil import guardar_perfil, validar_perfil_extraido
from tutor.prompts import prompt_extraer_perfil

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


class _Estado:
    """Estado del servidor: agente (si hay perfil) y quizzes en curso."""

    def __init__(self, configuracion: Configuracion, cliente: ClienteLLM) -> None:
        self.configuracion = configuracion
        self.cliente = cliente
        perfil = perfil_o_none(configuracion.dir_datos)
        self.agente: Agente | None = (
            Agente(cliente, configuracion.dir_datos, perfil) if perfil else None
        )
        self.quizzes: dict[int, Quiz] = {}


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
        """Sirve la página única del front."""
        return FileResponse(RUTA_INDEX)

    @app.get("/api/estado")
    def api_estado() -> dict[str, Any]:
        """Perfil existente y temario con estados (lo genera si falta)."""
        if estado.agente is None:
            return {"perfil": False}
        agente = estado.agente
        curso = _con_llm(lambda: agente.curso)
        return {
            "perfil": True,
            "lenguaje": curso.temario.lenguaje,
            "puntos": agente.progreso.puntos,
            "racha": agente.progreso.racha,
            "nota_aprobatoria": NOTA_APROBATORIA,
            "unidades": [
                {
                    "indice": fila.indice,
                    "titulo": fila.titulo,
                    "estado": fila.estado.value,
                    "mejor_nota": fila.mejor_nota,
                }
                for fila in agente.filas_unidades()
            ],
        }

    @app.post("/api/curso")
    def api_crear_curso(cuerpo: CuerpoPromptCurso) -> dict[str, Any]:
        """Crea el curso desde una petición libre: "hazme un curso de…"."""
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
        guardar_perfil(perfil, estado.configuracion.dir_datos / ARCHIVO_PERFIL)
        estado.agente = Agente(cliente, estado.configuracion.dir_datos, perfil)
        return {"ok": True}

    @app.post("/api/perfil")
    def api_perfil(cuerpo: CuerpoPerfil) -> dict[str, Any]:
        """Crea el perfil del estudiante y arma la sesión del agente."""
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
        guardar_perfil(perfil, estado.configuracion.dir_datos / ARCHIVO_PERFIL)
        estado.agente = Agente(estado.cliente, estado.configuracion.dir_datos, perfil)
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
