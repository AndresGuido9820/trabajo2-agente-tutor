"""Orquestador del tutor: conecta perfil, curso, evaluación y progreso (HU-06).

La UI no llama al LLM ni toca archivos directamente: todo pasa por el
``Agente``, que mantiene el estado de la sesión y persiste tras cada cambio.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

from tutor import db
from tutor.config import (
    MAX_TURNOS_CHARLA,
    NOTA_APROBATORIA,
    PUNTOS_ACIERTO_INTERMEDIO,
    PUNTOS_PRIMER_INTENTO,
    PUNTOS_QUIZ_APROBADO,
    PUNTOS_SEGUNDO_INTENTO,
)
from tutor.curso import (
    Curso,
    Guia,
    GuionLeccion,
    cargar_curso,
    generar_guia,
    generar_guion,
    generar_leccion,
    generar_temario,
    guardar_curso,
)
from tutor.errores import ErrorBloqueada, ErrorDatos, ErrorLLM
from tutor.evaluacion import Quiz, Retroalimentacion, calificar, generar_quiz
from tutor.llm import ClienteLLM, ExtractorCampoJSON, extraer_json, pedir_json
from tutor.models import PerfilEstudiante
from tutor.perfil import cargar_perfil, guardar_perfil
from tutor.progreso import Progreso, Resultado, cargar_progreso, guardar_progreso
from tutor.prompts import (
    prompt_artefacto,
    prompt_avance_leccion,
    prompt_charla,
    prompt_reencuentro,
    prompt_turno_leccion,
    system_charla,
    system_conversatorio,
    system_leccion,
    system_tutor,
)


def _validar_avance(datos: object) -> dict[str, object]:
    """Valida el JSON de un turno con decisión de avance."""
    if not isinstance(datos, dict) or "mensaje" not in datos or "avanza" not in datos:
        raise ValueError("se esperaban los campos 'avanza' y 'mensaje'")
    return {"avanza": bool(datos["avanza"]), "mensaje": str(datos["mensaje"])}


logger = logging.getLogger(__name__)

# Toda la persistencia vive en una sola base SQLite por estudiante (HU-19).
ARCHIVO_DB = "tutor.db"
ARCHIVO_PERFIL = ARCHIVO_DB
ARCHIVO_CURSO = ARCHIVO_DB
ARCHIVO_PROGRESO = ARCHIVO_DB


class EstadoUnidad(Enum):
    """Estado de una unidad para el menú de navegación."""

    BLOQUEADA = "bloqueada"
    PENDIENTE = "pendiente"
    VISTA = "vista"
    EVALUADA = "evaluada"
    APROBADA = "aprobada"


@dataclass(frozen=True)
class RespuestaCheckpoint:
    """Resultado de responder un checkpoint de la guía (HU-12)."""

    correcto: bool
    texto: str
    puntos: int
    puntos_totales: int
    revelada: bool


@dataclass
class _SesionLeccion:
    """Estado en memoria de una lección conversada (HU-10, ampliada HU-24)."""

    guion: GuionLeccion
    paso: int = 0
    historial: list[tuple[str, str]] = field(default_factory=list)
    # Guion v2 (HU-24): quiz intermedio pendiente (índice de objetivo),
    # objetivos ya resueltos y si el repaso del objetivo ya se usó.
    quiz_pendiente: int | None = None
    resueltos: set[int] = field(default_factory=set)
    repaso_usado: set[int] = field(default_factory=set)

    def objetivo_de_paso(self, paso: int) -> int:
        """Índice del objetivo (v2) al que pertenece un paso; 0 en v1."""
        for k, intermedio in enumerate(self.guion.intermedios):
            if paso <= intermedio.fin_paso:
                return k
        return max(len(self.guion.intermedios) - 1, 0)

    def detectar_cierre(self, paso_antes: int, terminada: bool) -> int | None:
        """Objetivo que se cerró en el último avance, si dispara quiz.

        Un objetivo cierra cuando el avance deja atrás su ``fin_paso`` (o
        la lección termina en él). Solo dispara si su quiz no se resolvió.
        """
        for k, intermedio in enumerate(self.guion.intermedios):
            cerrado = self.paso > intermedio.fin_paso or (
                terminada and self.paso == intermedio.fin_paso
            )
            if (
                cerrado
                and paso_antes <= intermedio.fin_paso
                and k not in self.resueltos
            ):
                return k
        return None


@dataclass(frozen=True)
class FilaUnidad:
    """Fila del menú: unidad + su estado + mejor nota si la hay."""

    indice: int
    titulo: str
    estado: EstadoUnidad
    mejor_nota: int | None


class Agente:
    """Sesión del tutor para un estudiante.

    Args:
        cliente: Cliente LLM (inyectable para pruebas).
        dir_datos: Carpeta de persistencia (perfil, curso, progreso).
        perfil: Perfil ya cargado/preguntado por el llamador.
    """

    def __init__(
        self, cliente: ClienteLLM, dir_datos: Path, perfil: PerfilEstudiante
    ) -> None:
        """Carga curso y progreso existentes; el temario se genera perezoso."""
        self._cliente = cliente
        self._dir = dir_datos
        self.perfil = perfil
        self.progreso: Progreso = cargar_progreso(dir_datos / ARCHIVO_PROGRESO)
        self._curso: Curso | None = cargar_curso(dir_datos / ARCHIVO_CURSO)
        # Historial de charla por unidad; vive solo en la sesión (HU-09).
        self._charlas: dict[int, list[tuple[str, str]]] = {}
        # Lecciones conversadas en curso; solo en la sesión (HU-10).
        self._lecciones_activas: dict[int, _SesionLeccion] = {}
        # Conversatorios de dudas por unidad; solo en la sesión (HU-12).
        self._conversatorios: dict[int, list[tuple[str, str]]] = {}
        # Enunciados del último quiz por unidad, para variantes (HU-13).
        self._quizzes_previos: dict[int, list[str]] = {}
        # Preguntas al tutor durante la guía, por unidad (HU-14).
        self._charlas_guia: dict[int, list[tuple[str, str]]] = {}
        # Estudio en chat continuo (HU-16): unidad donde va la conversación.
        self.unidad_actual: int = 0
        # Repaso del día en curso (HU-32): (quiz, ítems de la cola) o None.
        self._repaso_activo: tuple[Quiz, list[dict[str, Any]]] | None = None
        # Racha diaria (HU-13): la sesión de hoy cuenta al abrir el agente.
        self.progreso.registrar_sesion(date.today().isoformat())
        self.guardar()

    @property
    def curso(self) -> Curso:
        """El curso, generando el temario si aún no existe (una llamada LLM)."""
        if self._curso is None:
            temario = generar_temario(self._cliente, self.perfil)
            self._curso = Curso(temario=temario)
            guardar_curso(self._curso, self._dir / ARCHIVO_CURSO)
        return self._curso

    def curso_ya_generado(self) -> bool:
        """Indica si el temario ya existe (para que la UI avise antes de generar)."""
        return self._curso is not None

    def desbloqueada(self, indice: int) -> bool:
        """La unidad 1 siempre; las demás requieren aprobar la anterior."""
        if indice == 0:
            return True
        nota_anterior = self.progreso.mejor_nota(indice - 1)
        return nota_anterior is not None and nota_anterior >= NOTA_APROBATORIA

    def _exigir_desbloqueada(self, indice: int) -> None:
        """Candado de progresión (HU-12).

        Raises:
            IndexError: Si la unidad no existe (prima sobre el candado).
            ErrorBloqueada: Si falta aprobar la unidad anterior.
        """
        if not 0 <= indice < len(self.curso.temario.unidades):
            raise IndexError(f"No existe la unidad {indice}.")
        if not self.desbloqueada(indice):
            raise ErrorBloqueada(
                f"La unidad {indice + 1} está bloqueada: aprueba la unidad "
                f"{indice} (nota ≥ {NOTA_APROBATORIA}) para desbloquearla."
            )

    def filas_unidades(self) -> list[FilaUnidad]:
        """Estado de todas las unidades para el menú (RF-3.3)."""
        filas = []
        for indice, unidad in enumerate(self.curso.temario.unidades):
            nota = self.progreso.mejor_nota(indice)
            if nota is not None and nota >= NOTA_APROBATORIA:
                estado = EstadoUnidad.APROBADA
            elif nota is not None:
                estado = EstadoUnidad.EVALUADA
            elif not self.desbloqueada(indice):
                estado = EstadoUnidad.BLOQUEADA
            elif indice in self.progreso.vistas:
                estado = EstadoUnidad.VISTA
            else:
                estado = EstadoUnidad.PENDIENTE
            filas.append(
                FilaUnidad(
                    indice=indice,
                    titulo=unidad.titulo,
                    estado=estado,
                    mejor_nota=nota,
                )
            )
        return filas

    def leccion_ya_generada(self, indice: int) -> bool:
        """Indica si la lección ya está en cache (para el aviso de la UI)."""
        return indice in self.curso.lecciones

    def abrir_unidad(self, indice: int) -> str:
        """Devuelve la lección (generándola si hace falta) y marca la visita."""
        leccion = generar_leccion(
            self._cliente, self.perfil, self.curso, indice, self.progreso
        )
        guardar_curso(self.curso, self._dir / ARCHIVO_CURSO)
        self.progreso.marcar_vista(indice)
        self.guardar()
        return leccion

    def quiz_de_unidad(self, indice: int) -> Quiz:
        """Genera el quiz de la unidad (requiere abrir la lección primero).

        Raises:
            ErrorBloqueada: Si falta aprobar la unidad anterior.
        """
        self._exigir_desbloqueada(indice)
        if indice in self.curso.guias:
            # La guía ya enseña la unidad: el quiz se basa en ella (evita
            # generar además la lección Markdown: ~1 min menos de espera).
            leccion = "\n\n".join(
                f"### {s.objetivo}\n{s.contenido}"
                for s in self.curso.guias[indice].secciones
            )
            self.progreso.marcar_vista(indice)
            self.guardar()
        else:
            leccion = self.abrir_unidad(indice)
        unidad = self.curso.temario.unidades[indice]
        quiz = generar_quiz(
            self._cliente,
            titulo_unidad=unidad.titulo,
            conceptos=unidad.conceptos,
            leccion_md=leccion,
            unidad=indice,
            system=system_tutor(self.perfil),
            preguntas_previas=self._quizzes_previos.get(indice),
            priorizar=self.progreso.fallados_intermedios.get(str(indice)),
        )
        self._quizzes_previos[indice] = [p.enunciado for p in quiz.preguntas]
        return quiz

    def calificar_quiz(
        self, quiz: Quiz, respuestas: list[int]
    ) -> tuple[Resultado, list[Retroalimentacion]]:
        """Califica, registra el resultado y otorga puntos si aprueba.

        Los puntos por aprobar se dan solo la primera vez que la unidad
        alcanza la nota aprobatoria.
        """
        aprobada_antes = (
            self.progreso.mejor_nota(quiz.unidad) or 0
        ) >= NOTA_APROBATORIA
        resultado, detalle = calificar(quiz, respuestas)
        self.progreso.registrar(resultado)
        if resultado.nota >= NOTA_APROBATORIA and not aprobada_antes:
            self.progreso.sumar_puntos(PUNTOS_QUIZ_APROBADO)
        # Cada concepto fallado entra a la cola de repaso espaciado (HU-32).
        hoy = date.today().isoformat()
        for concepto in resultado.conceptos_fallados:
            self.progreso.programar_repaso(concepto, quiz.unidad, hoy)
        self.guardar()
        return resultado, detalle

    def guia_de_unidad(self, indice: int) -> Guia:
        """Guía interactiva de la unidad (con candado y cache; HU-12).

        Marca la unidad como vista y persiste.

        Raises:
            ErrorBloqueada: Si falta aprobar la unidad anterior.
            IndexError: Si la unidad no existe.
            ErrorLLM: Si la generación falla tras reintentos.
        """
        self._exigir_desbloqueada(indice)
        guia = generar_guia(
            self._cliente, self.perfil, self.curso, indice, self.progreso
        )
        guardar_curso(self.curso, self._dir / ARCHIVO_CURSO)
        self.progreso.marcar_vista(indice)
        self.guardar()
        return guia

    def responder_checkpoint(
        self, indice: int, seccion: int, opcion: int, intento: int
    ) -> RespuestaCheckpoint:
        """Califica localmente un checkpoint de la guía y asigna puntos.

        Puntos: acierto al intento 1 → ``PUNTOS_PRIMER_INTENTO``; al 2 →
        ``PUNTOS_SEGUNDO_INTENTO``; después, 0. Al fallar el intento 1 se
        devuelve la pista socrática; al fallar el 2 se revela la explicación.

        Raises:
            KeyError: Si la guía de la unidad no está generada.
            ValueError: Si la sección, opción o intento son inválidos.
        """
        guia = self.curso.guias[indice]
        if not 0 <= seccion < len(guia.secciones):
            raise ValueError(f"No existe la sección {seccion}.")
        checkpoint = guia.secciones[seccion].checkpoint
        if not 0 <= opcion < len(checkpoint.opciones):
            raise ValueError(f"Opción inválida: {opcion}.")
        if intento < 1:
            raise ValueError(f"Intento inválido: {intento}.")

        correcto = opcion == checkpoint.correcta
        if correcto:
            puntos = {1: PUNTOS_PRIMER_INTENTO, 2: PUNTOS_SEGUNDO_INTENTO}.get(
                intento, 0
            )
            self.progreso.sumar_puntos(puntos)
            self.guardar()
            return RespuestaCheckpoint(
                correcto=True,
                texto=checkpoint.explicacion,
                puntos=puntos,
                puntos_totales=self.progreso.puntos,
                revelada=True,
            )
        if intento == 1:
            return RespuestaCheckpoint(
                correcto=False,
                texto=checkpoint.pista,
                puntos=0,
                puntos_totales=self.progreso.puntos,
                revelada=False,
            )
        return RespuestaCheckpoint(
            correcto=False,
            texto=checkpoint.explicacion,
            puntos=0,
            puntos_totales=self.progreso.puntos,
            revelada=True,
        )

    def artefacto_de_seccion(self, indice: int, seccion: int) -> str:
        """Mini-artefacto HTML interactivo que ilustra la sección (HU-14).

        Se genera una vez y queda cacheado en el curso (persistido).

        Raises:
            KeyError: Si la guía de la unidad no está generada.
            ValueError: Si la sección no existe.
            ErrorLLM: Si la API falla tras los reintentos.
        """
        guia = self.curso.guias[indice]
        if not 0 <= seccion < len(guia.secciones):
            raise ValueError(f"No existe la sección {seccion}.")
        clave = f"{indice}-{seccion}"
        if clave in self.curso.artefactos:
            return self.curso.artefactos[clave]

        actual = guia.secciones[seccion]
        html = self._cliente.generar(
            system=system_tutor(self.perfil),
            prompt=prompt_artefacto(
                objetivo=actual.objetivo,
                contenido=actual.contenido,
                lenguaje=self.curso.temario.lenguaje,
            ),
        )
        # Tolerar fences de Markdown alrededor del HTML.
        html = html.strip()
        if html.startswith("```"):
            html = html.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        self.curso.artefactos[clave] = html
        guardar_curso(self.curso, self._dir / ARCHIVO_CURSO)
        return html

    def artefacto_de_unidad(self, indice: int) -> str:
        """Mini-artefacto interactivo de la unidad completa (chat, HU-16).

        Igual que el de sección, pero con el objetivo y conceptos de la
        unidad como material (no requiere guía generada).
        """
        if not 0 <= indice < len(self.curso.temario.unidades):
            raise ValueError(f"No existe la unidad {indice}.")
        clave = f"u{indice}"
        if clave in self.curso.artefactos:
            return self.curso.artefactos[clave]
        unidad = self.curso.temario.unidades[indice]
        html = self._cliente.generar(
            system=system_tutor(self.perfil),
            prompt=prompt_artefacto(
                objetivo=unidad.objetivo,
                contenido=(
                    f"Unidad: {unidad.titulo}\n"
                    f"Conceptos a ilustrar: {', '.join(unidad.conceptos)}"
                ),
                lenguaje=self.curso.temario.lenguaje,
            ),
        )
        html = html.strip()
        if html.startswith("```"):
            html = html.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        self.curso.artefactos[clave] = html
        guardar_curso(self.curso, self._dir / ARCHIVO_CURSO)
        return html

    def estado_repaso(self) -> dict[str, Any]:
        """Cuántos ítems vencen hoy y cuándo es el próximo (HU-32)."""
        self.progreso.purgar_repasos(len(self.curso.temario.unidades))
        hoy = date.today().isoformat()
        return {
            "pendientes": len(self.progreso.repasos_vencidos(hoy)),
            "proximo": self.progreso.proximo_repaso(),
        }

    def iniciar_repaso(self) -> Quiz:
        """Arma el quiz del repaso del día sobre los conceptos vencidos.

        Toma hasta 5 ítems (los más antiguos) y genera preguntas con esos
        conceptos como material. El mapeo de vuelta a la cola es por el
        campo ``concepto`` de cada pregunta.

        Raises:
            ErrorDatos: Si no hay ítems vencidos hoy.
            ErrorLLM: Si la generación falla tras reintentos.
        """
        self.progreso.purgar_repasos(len(self.curso.temario.unidades))
        hoy = date.today().isoformat()
        items = self.progreso.repasos_vencidos(hoy)[:5]
        if not items:
            raise ErrorDatos("No hay nada para repasar hoy.")
        unidades = self.curso.temario.unidades
        material = "\n".join(
            f"- {i['concepto']} (visto en la clase "
            f"'{unidades[i['clase']].titulo}': {unidades[i['clase']].objetivo})"
            for i in items
        )
        quiz = generar_quiz(
            self._cliente,
            titulo_unidad="Repaso del día",
            conceptos=[str(i["concepto"]) for i in items],
            leccion_md=(
                "Conceptos que el estudiante falló antes y debe repasar:\n" + material
            ),
            unidad=-1,  # el repaso no pertenece a una unidad
            system=system_tutor(self.perfil),
        )
        self._repaso_activo = (quiz, items)
        return quiz

    def calificar_repaso(self, respuestas: list[int]) -> dict[str, Any]:
        """Califica el repaso localmente y reprograma la cola 1-3-7.

        Un ítem cuenta como acertado si TODAS las preguntas de su concepto
        se respondieron bien; +3 puntos por pregunta acertada.

        Raises:
            ErrorDatos: Si no hay un repaso iniciado.
        """
        if self._repaso_activo is None:
            raise ErrorDatos("Inicia el repaso antes de calificarlo.")
        quiz, items = self._repaso_activo
        hoy = date.today().isoformat()
        aciertos_por_concepto: dict[str, list[bool]] = {}
        detalle = []
        for pregunta, respuesta in zip(quiz.preguntas, respuestas, strict=True):
            acierto = respuesta == pregunta.correcta
            aciertos_por_concepto.setdefault(pregunta.concepto.lower(), []).append(
                acierto
            )
            detalle.append(
                {
                    "acierto": acierto,
                    "elegida": pregunta.opciones[respuesta],
                    "correcta": pregunta.opciones[pregunta.correcta],
                    "explicacion": pregunta.explicacion,
                }
            )
        aciertos = sum(1 for d in detalle if d["acierto"])
        self.progreso.sumar_puntos(3 * aciertos)
        for item in items:
            resultados = aciertos_por_concepto.get(str(item["concepto"]).lower())
            if resultados is not None:
                self.progreso.resolver_repaso(
                    str(item["concepto"]), int(item["clase"]), all(resultados), hoy
                )
            # Sin pregunta para el ítem: sigue vencido, se repasa otro día.
        self._repaso_activo = None
        self.guardar()
        return {
            "aciertos": aciertos,
            "total": len(detalle),
            "detalle": detalle,
            "cola": self.progreso.cola_repaso,
        }

    def estadisticas(self) -> dict[str, Any]:
        """Métricas de aprendizaje para la vista "Mi progreso" (HU-31).

        Todo se agrega desde datos ya persistidos (resultados, chat,
        puntos); no escribe nada. Aproximaciones documentadas:
        - Aciertos por concepto: conceptos de la unidad evaluados menos los
          fallados en ese intento (el quiz no persiste sus preguntas).
        - Puntos por día: +30 el día del primer intento aprobado de cada
          unidad (los checkpoints no guardan fecha).
        - Tiempo estimado: nº de mensajes x 40 s.
        - Conceptos agrupados por minúsculas exactas (sin fuzzy).
        """
        unidades = self.curso.temario.unidades
        resultados = self.progreso.resultados

        notas: dict[str, list[int]] = {}
        for r in resultados:
            notas.setdefault(str(r.unidad), []).append(r.nota)

        conteo: dict[str, dict[str, Any]] = {}
        for r in resultados:
            de_unidad = (
                {c.lower() for c in unidades[r.unidad].conceptos}
                if 0 <= r.unidad < len(unidades)
                else set()
            )
            fallados = {c.lower() for c in r.conceptos_fallados}
            for c in de_unidad | fallados:
                fila = conteo.setdefault(c, {"c": c, "ok": 0, "mal": 0, "clase": None})
                if c in fallados:
                    fila["mal"] += 1
                    fila["clase"] = r.unidad
                elif c in de_unidad:
                    fila["ok"] += 1
        dominados = [f for f in conteo.values() if f["mal"] == 0 and f["ok"] >= 2]
        repasar = [f for f in conteo.values() if f["mal"] >= 1]
        for fila in dominados:
            fila.pop("clase")

        puntos_por_dia: dict[str, int] = {}
        aprobadas_vistas: set[int] = set()
        for r in resultados:
            if r.nota >= NOTA_APROBATORIA and r.unidad not in aprobadas_vistas:
                aprobadas_vistas.add(r.unidad)
                fecha = r.fecha[:10]
                puntos_por_dia[fecha] = (
                    puntos_por_dia.get(fecha, 0) + PUNTOS_QUIZ_APROBADO
                )

        mensajes_por_dia = db.actividad_chat(self._dir / ARCHIVO_DB)
        total_mensajes = sum(mensajes_por_dia.values())
        actividad = [
            {"fecha": f, "mensajes": n, "puntos": puntos_por_dia.get(f, 0)}
            for f, n in mensajes_por_dia.items()
        ]

        return {
            "actividad": actividad,
            "notas": notas,
            "conceptos": {
                "dominados": sorted(dominados, key=lambda f: -f["ok"]),
                "repasar": sorted(repasar, key=lambda f: -f["mal"]),
            },
            "totales": {
                "aprobadas": len(aprobadas_vistas),
                "total": len(unidades),
                "puntos": self.progreso.puntos,
                "racha": self.progreso.racha,
                "mejor_racha": self.progreso.mejor_racha,
                "minutos_estimados": total_mensajes * 40 // 60,
            },
        }

    def reencuentro(self, indice: int) -> str:
        """Resumen de bienvenida al volver a una clase (HU-30).

        Usa los últimos mensajes del historial persistente y el estado del
        progreso; NO avanza la lección.

        Raises:
            IndexError: Si la unidad no existe.
            ErrorLLM: Si la API falla tras los reintentos.
        """
        if not 0 <= indice < len(self.curso.temario.unidades):
            raise IndexError(f"No existe la unidad {indice}.")
        ultimos = db.historial_chat(self._dir / ARCHIVO_DB, f"u{indice}")[-12:]
        nota = self.progreso.mejor_nota(indice)
        partes = [
            "clase completada"
            if indice in self.progreso.completadas
            else "clase en curso",
        ]
        if nota is not None:
            partes.append(f"mejor nota en la evaluación: {nota}/100")
        fallados = self.progreso.conceptos_fallados_recientes()
        if fallados:
            partes.append(f"le costaron: {', '.join(fallados[:4])}")
        return self._cliente.generar(
            system=system_tutor(self.perfil),
            prompt=prompt_reencuentro(ultimos, "; ".join(partes)),
            carril="chat",
        )

    def preguntar_guia(self, indice: int, seccion: int, mensaje: str) -> str:
        """Pregunta libre al tutor mientras estudia una sección de la guía.

        El contexto es la sección actual (objetivo + contenido + enunciado
        del checkpoint, NUNCA su respuesta ni su explicación); el tutor
        responde con las reglas socráticas de charla (HU-09).

        Raises:
            KeyError: Si la guía de la unidad no está generada.
            ValueError: Si la sección no existe.
            ErrorLLM: Si la API falla tras los reintentos.
        """
        guia = self.curso.guias[indice]
        if not 0 <= seccion < len(guia.secciones):
            raise ValueError(f"No existe la sección {seccion}.")
        actual = guia.secciones[seccion]
        contexto = (
            f"### Objetivo que el estudiante está trabajando: {actual.objetivo}\n"
            f"{actual.contenido}\n\n"
            f"Checkpoint pendiente de esta sección (NO reveles ni insinúes su "
            f"respuesta): {actual.checkpoint.pregunta}"
        )
        historial = self._charlas_guia.setdefault(indice, [])
        respuesta = self._cliente.generar(
            system=system_charla(self.perfil),
            prompt=prompt_charla(contexto, historial, mensaje),
            carril="chat",
        )
        historial.append((mensaje, respuesta))
        del historial[:-MAX_TURNOS_CHARLA]
        return respuesta

    def conversatorio(self, indice: int, mensaje: str) -> str:
        """Turno del conversatorio socrático de dudas tras reprobar (HU-12).

        El contexto incluye la guía de la unidad y los conceptos fallados.
        ``mensaje`` vacío produce la apertura del tutor.

        Raises:
            ErrorLLM: Si la API falla tras los reintentos.
        """
        guia = self.curso.guias.get(indice)
        contexto = (
            "\n\n".join(f"### {s.objetivo}\n{s.contenido}" for s in guia.secciones)
            if guia
            else "(la guía no está disponible; usa los conceptos fallados)"
        )
        historial = self._conversatorios.setdefault(indice, [])
        respuesta = self._cliente.generar(
            system=system_conversatorio(
                self.perfil,
                self.progreso.conceptos_fallados_recientes(),
                desempeno=self._resumen_desempeno(indice),
            ),
            prompt=prompt_charla(contexto, historial, mensaje or "(inicia tú)"),
            carril="chat",
        )
        historial.append((mensaje, respuesta))
        del historial[:-MAX_TURNOS_CHARLA]
        return respuesta

    def iniciar_leccion(self, indice: int) -> GuionLeccion:
        """Prepara la lección conversada: guion (con cache) y sesión limpia.

        Marca la unidad como vista y persiste curso y progreso.

        Raises:
            ErrorBloqueada: Si falta aprobar la unidad anterior.
            IndexError: Si la unidad no existe.
            ErrorLLM: Si la generación del guion falla tras reintentos.
        """
        self._exigir_desbloqueada(indice)
        guion = generar_guion(
            self._cliente, self.perfil, self.curso, indice, self.progreso
        )
        guardar_curso(self.curso, self._dir / ARCHIVO_CURSO)
        self.progreso.marcar_vista(indice)
        self.guardar()
        self._lecciones_activas[indice] = _SesionLeccion(guion=guion)
        return guion

    def turno_leccion(
        self, indice: int, mensaje: str | None, apertura: str | None = None
    ) -> tuple[str, bool]:
        """Un turno de la lección conversada.

        Con ``mensaje=None`` produce el primer paso (``apertura`` permite
        saludar si el estudiante escribió algo casual al arrancar). Con un
        mensaje, el TUTOR decide si atiende el paso (reacciona y desarrolla
        el siguiente) o si es un saludo/duda (responde natural sin avanzar).

        Returns:
            El mensaje del tutor y si la lección quedó terminada.

        Raises:
            KeyError: Si la lección no fue iniciada con ``iniciar_leccion``.
            ErrorLLM: Si la API falla tras los reintentos.
        """
        sesion = self._lecciones_activas[indice]
        pasos = sesion.guion.pasos
        guion_texto = "\n".join(f"- {o}" for o in sesion.guion.objetivos)

        if mensaje is None:
            paso = pasos[sesion.paso]
            texto = self._cliente.generar(
                system=system_leccion(self.perfil),
                prompt=prompt_turno_leccion(
                    guion_texto=guion_texto,
                    numero_paso=sesion.paso + 1,
                    total_pasos=len(pasos),
                    paso_tipo=paso.tipo,
                    paso_instruccion=paso.instruccion,
                    historial=sesion.historial,
                    mensaje=None,
                    apertura=apertura,
                ),
                carril="chat",
            )
            sesion.historial.append((apertura or "", texto))
            del sesion.historial[:-MAX_TURNOS_CHARLA]
            return texto, len(pasos) == 1

        actual = pasos[sesion.paso]
        hay_siguiente = sesion.paso + 1 < len(pasos)
        siguiente = pasos[sesion.paso + 1] if hay_siguiente else None
        turno = pedir_json(
            self._cliente,
            system=system_leccion(self.perfil),
            prompt=prompt_avance_leccion(
                guion_texto=guion_texto,
                numero_paso=sesion.paso + 1,
                total_pasos=len(pasos),
                paso_actual=f"({actual.tipo}) {actual.instruccion}",
                paso_siguiente=(
                    f"({siguiente.tipo}) {siguiente.instruccion}" if siguiente else None
                ),
                historial=sesion.historial,
                mensaje=mensaje,
            ),
            validar=_validar_avance,
            carril="chat",
        )
        return self._cerrar_turno(sesion, mensaje, turno)

    def _cerrar_turno(
        self, sesion: _SesionLeccion, mensaje: str, turno: dict[str, object]
    ) -> tuple[str, bool]:
        """ÚNICO lugar que aplica la decisión de avance de un turno.

        Lo usan la variante clásica y la de streaming (HU-35): avanza el
        paso si corresponde, actualiza el historial y decide si terminó.
        """
        pasos = sesion.guion.pasos
        if turno["avanza"] and sesion.paso + 1 < len(pasos):
            sesion.paso += 1
        texto = str(turno["mensaje"])
        sesion.historial.append((mensaje, texto))
        del sesion.historial[:-MAX_TURNOS_CHARLA]
        terminada = bool(turno["avanza"]) and sesion.paso == len(pasos) - 1
        return texto, terminada

    def turno_leccion_stream(
        self, indice: int, mensaje: str | None, apertura: str | None = None
    ) -> Iterator[dict[str, Any]]:
        """Como ``turno_leccion`` pero emitiendo la respuesta en vivo (HU-35).

        Produce eventos ``{"delta": str}`` y cierra con
        ``{"fin": (texto, terminada)}``. La decisión de avance pasa por el
        mismo ``_cerrar_turno`` que la variante clásica.

        Raises:
            KeyError: Si la lección no fue iniciada.
            ErrorLLM: Si el stream falla o el JSON final es inválido.
        """
        sesion = self._lecciones_activas[indice]
        pasos = sesion.guion.pasos
        guion_texto = "\n".join(f"- {o}" for o in sesion.guion.objetivos)

        if mensaje is None:
            paso = pasos[sesion.paso]
            partes: list[str] = []
            for delta in self._cliente.generar_stream(
                system=system_leccion(self.perfil),
                prompt=prompt_turno_leccion(
                    guion_texto=guion_texto,
                    numero_paso=sesion.paso + 1,
                    total_pasos=len(pasos),
                    paso_tipo=paso.tipo,
                    paso_instruccion=paso.instruccion,
                    historial=sesion.historial,
                    mensaje=None,
                    apertura=apertura,
                ),
                carril="chat",
            ):
                partes.append(delta)
                yield {"delta": delta}
            texto = "".join(partes)
            sesion.historial.append((apertura or "", texto))
            del sesion.historial[:-MAX_TURNOS_CHARLA]
            yield {"fin": (texto, len(pasos) == 1)}
            return

        actual = pasos[sesion.paso]
        hay_siguiente = sesion.paso + 1 < len(pasos)
        siguiente = pasos[sesion.paso + 1] if hay_siguiente else None
        extractor = ExtractorCampoJSON("mensaje")
        for trozo in self._cliente.generar_stream(
            system=system_leccion(self.perfil),
            prompt=prompt_avance_leccion(
                guion_texto=guion_texto,
                numero_paso=sesion.paso + 1,
                total_pasos=len(pasos),
                paso_actual=f"({actual.tipo}) {actual.instruccion}",
                paso_siguiente=(
                    f"({siguiente.tipo}) {siguiente.instruccion}" if siguiente else None
                ),
                historial=sesion.historial,
                mensaje=mensaje,
            ),
            carril="chat",
        ):
            delta = extractor.alimentar(trozo)
            if delta:
                yield {"delta": delta}
        try:
            turno = _validar_avance(extraer_json(extractor.crudo))
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
            # Sin reintento aquí: el front hace fallback al turno clásico.
            raise ErrorLLM(
                f"El stream no produjo el formato esperado ({error})."
            ) from error
        yield {"fin": self._cerrar_turno(sesion, mensaje, turno)}

    def turno_estudio_stream(
        self, mensaje: str | None, unidad: int | None = None
    ) -> Iterator[dict[str, Any]]:
        """Variante en vivo de ``turno_estudio`` (HU-35).

        Emite ``{"delta": str}`` y cierra con ``{"fin": payload}`` donde el
        payload es idéntico al retorno de ``turno_estudio``.
        """
        if unidad is not None and mensaje is None:
            self.unidad_actual = unidad
            self.iniciar_leccion(unidad)
            paso_antes = 0
            turnos = self.turno_leccion_stream(unidad, None)
        else:
            if unidad is not None:
                self.unidad_actual = unidad
            actual = self.unidad_actual
            if actual not in self._lecciones_activas:
                self.iniciar_leccion(actual)
                paso_antes = 0
                turnos = self.turno_leccion_stream(actual, None, apertura=mensaje)
            else:
                paso_antes = self._lecciones_activas[actual].paso
                turnos = self.turno_leccion_stream(actual, mensaje or "ok, sigamos")
        resultado: tuple[str, bool] | None = None
        for evento in turnos:
            if "fin" in evento:
                resultado = evento["fin"]
            else:
                yield evento
        assert resultado is not None  # turno_leccion_stream siempre cierra
        texto, terminada = resultado
        yield {"fin": self._payload_estudio(texto, terminada, paso_antes)}

    def avance_leccion(self, indice: int) -> tuple[int, int]:
        """Paso actual (base 1) y total de la lección conversada activa."""
        sesion = self._lecciones_activas[indice]
        return sesion.paso + 1, len(sesion.guion.pasos)

    def turno_estudio(
        self, mensaje: str | None, unidad: int | None = None
    ) -> dict[str, object]:
        """Un turno del estudio en chat continuo (HU-16).

        Con ``unidad`` se (re)inicia esa lección (repaso incluido); sin ella
        continúa la lección activa. Al terminar el último paso, la unidad se
        marca como completada (el panel la tacha).

        Raises:
            ErrorBloqueada: Si la unidad pedida está bloqueada.
            ErrorLLM: Si la API falla tras los reintentos.
        """
        if unidad is not None and mensaje is None:
            # Entrar/repasar: (re)inicia la lección de esa clase.
            self.unidad_actual = unidad
            self.iniciar_leccion(unidad)
            paso_antes = 0
            texto, terminada = self.turno_leccion(unidad, None)
        else:
            # Continuar la conversación de la clase indicada (o la actual).
            if unidad is not None:
                self.unidad_actual = unidad
            actual = self.unidad_actual
            if actual not in self._lecciones_activas:
                self.iniciar_leccion(actual)
                paso_antes = 0
                texto, terminada = self.turno_leccion(actual, None, apertura=mensaje)
            else:
                paso_antes = self._lecciones_activas[actual].paso
                texto, terminada = self.turno_leccion(actual, mensaje or "ok, sigamos")
        return self._payload_estudio(texto, terminada, paso_antes)

    def _payload_estudio(
        self, texto: str, terminada: bool, paso_antes: int
    ) -> dict[str, object]:
        """Payload de un turno de estudio, con el estado del guion v2.

        ÚNICO lugar que marca la clase completada y dispara el quiz
        intermedio al cerrar un objetivo (HU-24): lo usan la variante
        clásica y la de streaming.
        """
        if terminada:
            self.progreso.completar(self.unidad_actual)
            self.guardar()
        sesion = self._lecciones_activas[self.unidad_actual]
        cierre = sesion.detectar_cierre(paso_antes, terminada)
        if cierre is not None:
            sesion.quiz_pendiente = cierre
        pendiente = sesion.quiz_pendiente
        paso, total = self.avance_leccion(self.unidad_actual)
        payload: dict[str, object] = {
            "texto": texto,
            "unidad": self.unidad_actual,
            "paso": paso,
            "total": total,
            "terminada": terminada,
        }
        if sesion.guion.intermedios:
            payload["objetivo"] = sesion.objetivo_de_paso(sesion.paso) + 1
            payload["objetivos_total"] = len(sesion.guion.objetivos)
            payload["quiz_intermedio"] = (
                [
                    {"enunciado": p.enunciado, "opciones": p.opciones}
                    for p in sesion.guion.intermedios[pendiente].preguntas
                ]
                if pendiente is not None
                else None
            )
        return payload

    def responder_quiz_intermedio(
        self, unidad: int, respuestas: list[int]
    ) -> dict[str, Any]:
        """Califica el mini-quiz del objetivo pendiente (HU-24, local).

        1+ aciertos → objetivo cumplido (+5 ⭐ por acierto). 0 aciertos la
        primera vez → repaso con explicación nueva y el MISMO quiz otra
        vez; a la segunda, el flujo avanza igual pero los conceptos quedan
        anotados para la evaluación final y la cola de repaso.

        Raises:
            ErrorDatos: Si no hay quiz intermedio pendiente.
            ValueError: Si las respuestas no calzan con las preguntas.
        """
        if unidad not in self._lecciones_activas:
            raise ErrorDatos("La clase no tiene una conversación activa.")
        sesion = self._lecciones_activas[unidad]
        k = sesion.quiz_pendiente
        if k is None:
            raise ErrorDatos("No hay un mini-quiz pendiente en esta clase.")
        preguntas = sesion.guion.intermedios[k].preguntas
        if len(respuestas) != len(preguntas):
            raise ValueError(f"se esperaban {len(preguntas)} respuestas")
        detalle = []
        for pregunta, respuesta in zip(preguntas, respuestas, strict=True):
            if not 0 <= respuesta < len(pregunta.opciones):
                raise ValueError(f"respuesta fuera de rango: {respuesta}")
            detalle.append(
                {
                    "acierto": respuesta == pregunta.correcta,
                    "correcta": pregunta.opciones[pregunta.correcta],
                    "explicacion": pregunta.explicacion,
                }
            )
        aciertos = sum(1 for d in detalle if d["acierto"])

        if aciertos == 0 and k not in sesion.repaso_usado:
            # Repaso único: explicación nueva con otro ejemplo, mismo quiz.
            sesion.repaso_usado.add(k)
            texto = self._cliente.generar(
                system=system_leccion(self.perfil),
                prompt=(
                    f"El estudiante falló las 2 preguntas del objetivo "
                    f'"{sesion.guion.objetivos[k]}". Vuelve a explicarlo en '
                    "4-6 frases con un EJEMPLO DISTINTO al que usaste, y "
                    "anímalo a reintentar el mini-quiz. Sin regañar."
                ),
                carril="chat",
            )
            return {
                "aciertos": 0,
                "cumplido": False,
                "repite": True,
                "detalle": detalle,
                "puntos_totales": self.progreso.puntos,
                "texto": texto,
            }

        # Cumplido (1+ aciertos, o segundo intento sin importar el resultado).
        sesion.resueltos.add(k)
        sesion.quiz_pendiente = None
        self.progreso.sumar_puntos(PUNTOS_ACIERTO_INTERMEDIO * aciertos)
        self.progreso.cumplir_objetivo(unidad, k)
        hoy = date.today().isoformat()
        for pregunta, d in zip(preguntas, detalle, strict=True):
            if not d["acierto"]:
                self.progreso.anotar_fallado_intermedio(unidad, pregunta.concepto)
                self.progreso.programar_repaso(pregunta.concepto, unidad, hoy)
        self.guardar()
        nota = f"{aciertos}/{len(preguntas)}"
        if aciertos == len(preguntas):
            texto = f"✅ ¡Objetivo cumplido ({nota})! Sigamos con el próximo."
        elif aciertos > 0:
            texto = (
                f"✅ Objetivo cumplido ({nota} — la que falló la "
                "reforzaremos en la evaluación). ¡Sigamos!"
            )
        else:
            texto = (
                f"Objetivo visto ({nota}). No pasa nada: esos conceptos "
                "quedan anotados y los repasaremos. ¡Sigamos!"
            )
        return {
            "aciertos": aciertos,
            "cumplido": True,
            "repite": False,
            "detalle": detalle,
            "puntos_totales": self.progreso.puntos,
            "texto": texto,
        }

    def charlar(self, indice: int, pregunta: str) -> str:
        """Responde una pregunta del estudiante sobre la unidad ``indice``.

        Mantiene un historial por unidad (solo en memoria) acotado a
        ``MAX_TURNOS_CHARLA`` turnos para controlar el tamaño del prompt.

        Raises:
            ErrorLLM: Si la API falla tras los reintentos.
        """
        leccion = self.curso.lecciones.get(indice) or self.abrir_unidad(indice)
        historial = self._charlas.setdefault(indice, [])
        respuesta = self._cliente.generar(
            system=system_charla(self.perfil),
            prompt=prompt_charla(leccion, historial, pregunta),
            carril="chat",
        )
        historial.append((pregunta, respuesta))
        del historial[:-MAX_TURNOS_CHARLA]
        return respuesta

    def _resumen_desempeno(self, indice: int) -> str:
        """Historial de intentos de la unidad para el theory-of-mind (HU-13)."""
        intentos = [r for r in self.progreso.resultados if r.unidad == indice]
        if not intentos:
            return ""
        lineas = [
            f"- Intento {n}: nota {r.nota}/100"
            + (
                f", falló: {', '.join(r.conceptos_fallados)}"
                if r.conceptos_fallados
                else ""
            )
            for n, r in enumerate(intentos, start=1)
        ]
        return "\n".join(lineas)

    def rehacer_perfil(self, nuevo_perfil: PerfilEstudiante) -> None:
        """Reemplaza el perfil y descarta el curso (el progreso se conserva)."""
        self.perfil = nuevo_perfil
        guardar_perfil(nuevo_perfil, self._dir / ARCHIVO_PERFIL)
        self._curso = None
        db.borrar_curso(self._dir / ARCHIVO_DB)
        logger.info("Perfil rehecho; el temario se regenerará.")

    def guardar(self) -> None:
        """Persiste el progreso (el curso se persiste al generar lecciones)."""
        guardar_progreso(self.progreso, self._dir / ARCHIVO_PROGRESO)


def perfil_o_none(dir_datos: Path) -> PerfilEstudiante | None:
    """Carga el perfil guardado; ante archivo corrupto devuelve ``None``.

    El cuestionario se rehace en ese caso (decisión HU-01: un perfil corrupto
    no debe impedir estudiar).
    """
    try:
        return cargar_perfil(dir_datos / ARCHIVO_PERFIL)
    except ErrorDatos as error:
        logger.warning("Perfil ilegible (%s); se rehará el cuestionario.", error)
        return None
