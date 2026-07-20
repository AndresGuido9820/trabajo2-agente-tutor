"""Orquestador del tutor: conecta perfil, curso, evaluación y progreso (HU-06).

La UI no llama al LLM ni toca archivos directamente: todo pasa por el
``Agente``, que mantiene el estado de la sesión y persiste tras cada cambio.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from tutor.curso import (
    Curso,
    cargar_curso,
    generar_leccion,
    generar_temario,
    guardar_curso,
)
from tutor.errores import ErrorDatos
from tutor.evaluacion import Quiz, Retroalimentacion, calificar, generar_quiz
from tutor.llm import ClienteLLM
from tutor.models import PerfilEstudiante
from tutor.perfil import cargar_perfil, guardar_perfil
from tutor.progreso import Progreso, Resultado, cargar_progreso, guardar_progreso
from tutor.prompts import system_tutor

logger = logging.getLogger(__name__)

ARCHIVO_PERFIL = "perfil.json"
ARCHIVO_CURSO = "curso.json"
ARCHIVO_PROGRESO = "progreso.json"


class EstadoUnidad(Enum):
    """Estado de una unidad para el menú de navegación."""

    PENDIENTE = "pendiente"
    VISTA = "vista"
    EVALUADA = "evaluada"


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

    def filas_unidades(self) -> list[FilaUnidad]:
        """Estado de todas las unidades para el menú (RF-3.3)."""
        filas = []
        for indice, unidad in enumerate(self.curso.temario.unidades):
            nota = self.progreso.mejor_nota(indice)
            if nota is not None:
                estado = EstadoUnidad.EVALUADA
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
        """Genera el quiz de la unidad (requiere abrir la lección primero)."""
        leccion = self.abrir_unidad(indice)
        unidad = self.curso.temario.unidades[indice]
        return generar_quiz(
            self._cliente,
            titulo_unidad=unidad.titulo,
            conceptos=unidad.conceptos,
            leccion_md=leccion,
            unidad=indice,
            system=system_tutor(self.perfil),
        )

    def calificar_quiz(
        self, quiz: Quiz, respuestas: list[int]
    ) -> tuple[Resultado, list[Retroalimentacion]]:
        """Califica, registra el resultado en el progreso y persiste."""
        resultado, detalle = calificar(quiz, respuestas)
        self.progreso.registrar(resultado)
        self.guardar()
        return resultado, detalle

    def rehacer_perfil(self, nuevo_perfil: PerfilEstudiante) -> None:
        """Reemplaza el perfil y descarta el curso (el progreso se conserva)."""
        self.perfil = nuevo_perfil
        guardar_perfil(nuevo_perfil, self._dir / ARCHIVO_PERFIL)
        self._curso = None
        (self._dir / ARCHIVO_CURSO).unlink(missing_ok=True)
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
