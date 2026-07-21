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

# Repetición espaciada (HU-32): intervalos fijos en días. Un concepto
# fallado vence mañana; cada acierto avanza al siguiente; tras el último
# sale de la cola. Fallar en el repaso reinicia al primero.
INTERVALOS_REPASO = [1, 3, 7]


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
    # Cola de repaso espaciado (HU-32): ítems {concepto, clase, vence, nivel}.
    cola_repaso: list[dict[str, Any]] = field(default_factory=list)
    # Guion v2 (HU-24): objetivos cumplidos y conceptos fallados en los
    # mini-quices, por clase (clave: str(indice de clase)).
    objetivos_cumplidos: dict[str, list[int]] = field(default_factory=dict)
    fallados_intermedios: dict[str, list[str]] = field(default_factory=dict)
    # Resultado del mini-quiz por objetivo (HU-25): clase → objetivo →
    # {"aciertos": int, "total": int, "repaso": bool}.
    resultados_intermedios: dict[str, dict[str, dict[str, Any]]] = field(
        default_factory=dict
    )
    # Retos de código superados (HU-28): clase → índices de objetivo.
    retos_superados: dict[str, list[int]] = field(default_factory=dict)

    def superar_reto(self, clase: int, objetivo: int) -> bool:
        """Marca un reto como superado; ``False`` si ya lo estaba."""
        superados = self.retos_superados.setdefault(str(clase), [])
        if objetivo in superados:
            return False
        superados.append(objetivo)
        return True

    def cumplir_objetivo(
        self,
        clase: int,
        objetivo: int,
        aciertos: int = 0,
        total: int = 0,
        repaso: bool = False,
    ) -> None:
        """Marca un objetivo del guion v2 como cumplido (idempotente).

        Guarda además el resultado de su mini-quiz para el panel (HU-25).
        """
        cumplidos = self.objetivos_cumplidos.setdefault(str(clase), [])
        if objetivo not in cumplidos:
            cumplidos.append(objetivo)
        if total:
            self.resultados_intermedios.setdefault(str(clase), {})[str(objetivo)] = {
                "aciertos": aciertos,
                "total": total,
                "repaso": repaso,
            }

    def anotar_fallado_intermedio(self, clase: int, concepto: str) -> None:
        """Anota un concepto fallado en un mini-quiz (para la evaluación)."""
        fallados = self.fallados_intermedios.setdefault(str(clase), [])
        if concepto not in fallados:
            fallados.append(concepto)

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

    def _item_repaso(self, concepto: str, clase: int) -> dict[str, Any] | None:
        """El ítem de la cola para (concepto, clase), si existe."""
        for item in self.cola_repaso:
            if item["concepto"] == concepto.lower() and item["clase"] == clase:
                return item
        return None

    def programar_repaso(self, concepto: str, clase: int, hoy: str) -> None:
        """Un fallo entra (o reinicia) en la cola: vence mañana, nivel 0."""
        manana = (date.fromisoformat(hoy) + timedelta(days=1)).isoformat()
        item = self._item_repaso(concepto, clase)
        if item is None:
            item = {"concepto": concepto.lower(), "clase": clase}
            self.cola_repaso.append(item)
        item["vence"] = manana
        item["nivel"] = 0

    def repasos_vencidos(self, hoy: str) -> list[dict[str, Any]]:
        """Ítems vencidos hoy o antes, los más antiguos primero."""
        vencidos = [i for i in self.cola_repaso if i["vence"] <= hoy]
        return sorted(vencidos, key=lambda i: str(i["vence"]))

    def resolver_repaso(
        self, concepto: str, clase: int, acierto: bool, hoy: str
    ) -> None:
        """Reprograma un ítem tras repasarlo: avanza 1-3-7 o reinicia."""
        item = self._item_repaso(concepto, clase)
        if item is None:
            return
        if not acierto:
            self.programar_repaso(concepto, clase, hoy)
            return
        nivel = int(item["nivel"]) + 1
        if nivel >= len(INTERVALOS_REPASO):
            self.cola_repaso.remove(item)  # dominado: sale de la cola
            return
        item["nivel"] = nivel
        item["vence"] = (
            date.fromisoformat(hoy) + timedelta(days=INTERVALOS_REPASO[nivel])
        ).isoformat()

    def purgar_repasos(self, total_clases: int) -> None:
        """Quita ítems de clases que ya no existen (rediseño del curso)."""
        self.cola_repaso = [i for i in self.cola_repaso if i["clase"] < total_clases]

    def proximo_repaso(self) -> str | None:
        """Fecha del próximo vencimiento, o ``None`` con la cola vacía."""
        return min((str(i["vence"]) for i in self.cola_repaso), default=None)

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
        "cola_repaso": progreso.cola_repaso,
        "objetivos_cumplidos": progreso.objetivos_cumplidos,
        "fallados_intermedios": progreso.fallados_intermedios,
        "resultados_intermedios": progreso.resultados_intermedios,
        "retos_superados": progreso.retos_superados,
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
        cola_repaso=[
            {
                "concepto": str(i["concepto"]),
                "clase": int(i["clase"]),
                "vence": str(i["vence"]),
                "nivel": int(i["nivel"]),
            }
            for i in datos.get("cola_repaso", [])
        ],
        objetivos_cumplidos={
            str(clase): [int(o) for o in objetivos]
            for clase, objetivos in datos.get("objetivos_cumplidos", {}).items()
        },
        fallados_intermedios={
            str(clase): [str(c) for c in conceptos]
            for clase, conceptos in datos.get("fallados_intermedios", {}).items()
        },
        resultados_intermedios={
            str(clase): {
                str(objetivo): {
                    "aciertos": int(r["aciertos"]),
                    "total": int(r["total"]),
                    "repaso": bool(r["repaso"]),
                }
                for objetivo, r in resultados.items()
            }
            for clase, resultados in datos.get("resultados_intermedios", {}).items()
        },
        retos_superados={
            str(clase): [int(o) for o in objetivos]
            for clase, objetivos in datos.get("retos_superados", {}).items()
        },
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
