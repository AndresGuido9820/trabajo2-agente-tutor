"""Progreso del estudiante: modelo y persistencia atómica (HU-05).

El progreso vive en ``progreso.json``, separado del perfil y del contenido
del curso: borrar el cache de lecciones no borra el avance. La escritura es
atómica (archivo temporal + rename) para tolerar interrupciones.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

VERSION_ESQUEMA = 1


@dataclass(frozen=True)
class Resultado:
    """Resultado de un intento de quiz de una unidad.

    Attributes:
        unidad: Índice de la unidad (base 0).
        nota: Calificación 0-100.
        conceptos_fallados: Conceptos de las preguntas falladas (alimenta la
            adaptación de lecciones siguientes, HU-03).
        fecha: Timestamp ISO 8601 en UTC.
    """

    unidad: int
    nota: int
    conceptos_fallados: list[str]
    fecha: str

    def __post_init__(self) -> None:
        """Valida los invariantes del resultado."""
        if not 0 <= self.nota <= 100:
            raise ValueError(f"Nota fuera de rango 0-100: {self.nota}")
        if self.unidad < 0:
            raise ValueError(f"Índice de unidad inválido: {self.unidad}")


def _ahora() -> str:
    """Timestamp ISO 8601 en UTC (segundos)."""
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class Progreso:
    """Avance del estudiante: unidades vistas y resultados de quizzes."""

    vistas: dict[int, str] = field(default_factory=dict)
    resultados: list[Resultado] = field(default_factory=list)

    def marcar_vista(self, unidad: int) -> None:
        """Registra la primera visita a una unidad (idempotente)."""
        self.vistas.setdefault(unidad, _ahora())

    def registrar(self, resultado: Resultado) -> None:
        """Agrega un resultado de quiz al historial."""
        self.resultados.append(resultado)

    def mejor_nota(self, unidad: int) -> int | None:
        """Mejor calificación de la unidad, o ``None`` si nunca se evaluó."""
        notas = [r.nota for r in self.resultados if r.unidad == unidad]
        return max(notas) if notas else None

    def intentos(self, unidad: int) -> int:
        """Cantidad de veces que se evaluó la unidad."""
        return sum(1 for r in self.resultados if r.unidad == unidad)

    def conceptos_fallados_recientes(self, maximo: int = 6) -> list[str]:
        """Últimos conceptos fallados (sin duplicados, más reciente primero).

        Alimenta el prompt de la siguiente lección para reforzarlos (HU-03).
        """
        conceptos: list[str] = []
        for resultado in reversed(self.resultados):
            for concepto in resultado.conceptos_fallados:
                if concepto not in conceptos:
                    conceptos.append(concepto)
                if len(conceptos) >= maximo:
                    return conceptos
        return conceptos


def guardar_progreso(progreso: Progreso, ruta: Path) -> None:
    """Serializa el progreso a ``ruta`` con escritura atómica."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {
        "version": VERSION_ESQUEMA,
        "vistas": {str(unidad): fecha for unidad, fecha in progreso.vistas.items()},
        "resultados": [
            {
                "unidad": r.unidad,
                "nota": r.nota,
                "conceptos_fallados": r.conceptos_fallados,
                "fecha": r.fecha,
            }
            for r in progreso.resultados
        ],
    }
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), "utf-8")
    os.replace(temporal, ruta)
    logger.debug("Progreso guardado en %s", ruta)


def _parsear(datos: Any) -> Progreso:
    """Convierte el JSON crudo en ``Progreso`` validando tipos."""
    vistas = {int(unidad): str(fecha) for unidad, fecha in datos["vistas"].items()}
    resultados = [
        Resultado(
            unidad=int(r["unidad"]),
            nota=int(r["nota"]),
            conceptos_fallados=[str(c) for c in r["conceptos_fallados"]],
            fecha=str(r["fecha"]),
        )
        for r in datos["resultados"]
    ]
    return Progreso(vistas=vistas, resultados=resultados)


def cargar_progreso(ruta: Path) -> Progreso:
    """Carga el progreso desde ``ruta``.

    A diferencia del perfil, un archivo corrupto NO es fatal: se advierte y
    se arranca con progreso vacío (perder el historial es tolerable; impedir
    estudiar no).
    """
    if not ruta.exists():
        return Progreso()
    try:
        return _parsear(json.loads(ruta.read_text("utf-8")))
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
        logger.warning(
            "Progreso corrupto en %s (%s); se arranca con progreso vacío.",
            ruta,
            error,
        )
        return Progreso()


def crear_resultado(unidad: int, nota: int, conceptos_fallados: list[str]) -> Resultado:
    """Crea un resultado con la fecha actual."""
    return Resultado(
        unidad=unidad,
        nota=nota,
        conceptos_fallados=conceptos_fallados,
        fecha=_ahora(),
    )
