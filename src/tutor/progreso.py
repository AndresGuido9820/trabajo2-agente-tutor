"""Progreso del estudiante: modelo y persistencia atómica (HU-05).

El progreso vive en ``progreso.json``, separado del perfil y del contenido
del curso: borrar el cache de lecciones no borra el avance. La escritura es
atómica (archivo temporal + rename) para tolerar interrupciones.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from tutor import db

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
    puntos: int = 0
    racha: int = 0
    mejor_racha: int = 0
    ultima_sesion: str = ""  # fecha ISO AAAA-MM-DD de la última sesión
    completadas: list[int] = field(default_factory=list)  # lecciones terminadas

    def completar(self, unidad: int) -> None:
        """Marca la lección de la unidad como completada en el chat (HU-16)."""
        if unidad not in self.completadas:
            self.completadas.append(unidad)

    def sumar_puntos(self, cantidad: int) -> None:
        """Acumula puntos ganados en checkpoints y evaluaciones (HU-12)."""
        if cantidad < 0:
            raise ValueError(f"Los puntos no pueden ser negativos: {cantidad}")
        self.puntos += cantidad

    def registrar_sesion(self, hoy: str) -> None:
        """Actualiza la racha diaria (HU-13, mecánica Duolingo sin castigos).

        El mismo día no suma; un día consecutivo suma 1; saltarse días
        reinicia la racha a 1 (sin vidas ni penalizaciones).
        """
        if self.ultima_sesion == hoy:
            return
        ayer = (date.fromisoformat(hoy) - timedelta(days=1)).isoformat()
        self.racha = self.racha + 1 if self.ultima_sesion == ayer else 1
        self.mejor_racha = max(self.mejor_racha, self.racha)
        self.ultima_sesion = hoy

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
    """Guarda el progreso en la base de datos ``ruta`` (transaccional)."""
    datos = {
        "version": VERSION_ESQUEMA,
        "puntos": progreso.puntos,
        "racha": progreso.racha,
        "mejor_racha": progreso.mejor_racha,
        "ultima_sesion": progreso.ultima_sesion,
        "completadas": progreso.completadas,
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
    db.guardar_documento(ruta, "progreso", datos)
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
    # Campos nuevos opcionales (retro-compatibilidad con progresos previos).
    return Progreso(
        vistas=vistas,
        resultados=resultados,
        puntos=int(datos.get("puntos", 0)),
        racha=int(datos.get("racha", 0)),
        mejor_racha=int(datos.get("mejor_racha", datos.get("racha", 0))),
        ultima_sesion=str(datos.get("ultima_sesion", "")),
        completadas=[int(u) for u in datos.get("completadas", [])],
    )


def cargar_progreso(ruta: Path) -> Progreso:
    """Carga el progreso desde ``ruta``.

    A diferencia del perfil, un archivo corrupto NO es fatal: se advierte y
    se arranca con progreso vacío (perder el historial es tolerable; impedir
    estudiar no).
    """
    try:
        datos = db.cargar_documento(ruta, "progreso")
        return _parsear(datos) if datos is not None else Progreso()
    except (
        sqlite3.DatabaseError,
        json.JSONDecodeError,
        ValueError,
        KeyError,
        TypeError,
    ) as error:
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
