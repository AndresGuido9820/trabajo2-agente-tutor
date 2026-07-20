"""Modelos de dominio del perfil del estudiante."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Nivel(Enum):
    """Nivel de experiencia declarado por el estudiante."""

    NUNCA = "nunca"
    BASICO = "basico"
    SCRIPTS = "scripts"

    @property
    def descripcion(self) -> str:
        """Texto que se muestra en el cuestionario."""
        return {
            Nivel.NUNCA: "Nunca he programado",
            Nivel.BASICO: "Sé algo básico (variables, condicionales)",
            Nivel.SCRIPTS: "He escrito scripts o programas pequeños",
        }[self]


class Objetivo(Enum):
    """Meta de aprendizaje del estudiante."""

    DATOS = "datos"
    FRONT = "front"
    BACK = "back"
    AUTOMATIZACION = "automatizacion"
    OTRO = "otro"

    @property
    def descripcion(self) -> str:
        """Texto que se muestra en el cuestionario."""
        return {
            Objetivo.DATOS: "Ciencia de datos / análisis",
            Objetivo.FRONT: "Desarrollo front-end",
            Objetivo.BACK: "Desarrollo back-end",
            Objetivo.AUTOMATIZACION: "Automatizar tareas",
            Objetivo.OTRO: "Otro (cuéntame)",
        }[self]


@dataclass(frozen=True)
class PerfilEstudiante:
    """Perfil que personaliza todo el curso (ver plan/HU-01).

    Attributes:
        nivel: Experiencia previa declarada.
        experiencia: Descripción libre de lo que ya ha hecho (puede ser "").
        objetivo: Meta de aprendizaje.
        objetivo_detalle: Detalle obligatorio cuando ``objetivo`` es ``OTRO``.
        lenguaje: Lenguaje preferido en minúsculas, o "" para que el tutor
            decida según el objetivo.
    """

    nivel: Nivel
    experiencia: str
    objetivo: Objetivo
    objetivo_detalle: str
    lenguaje: str

    def __post_init__(self) -> None:
        """Valida invariantes del perfil.

        Raises:
            ValueError: Si ``objetivo`` es ``OTRO`` sin ``objetivo_detalle``.
        """
        if self.objetivo is Objetivo.OTRO and not self.objetivo_detalle.strip():
            raise ValueError(
                "Un objetivo 'otro' requiere describirlo en objetivo_detalle."
            )
