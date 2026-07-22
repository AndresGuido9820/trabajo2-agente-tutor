"""Evaluaciones: generación del quiz con el LLM y calificación local (HU-04).

El LLM genera las preguntas (con verificación exigida en el prompt); la
calificación es determinista y local: comparar índices. La nota y los
conceptos fallados se registran en el progreso (HU-05) y alimentan la
adaptación de lecciones siguientes (HU-03).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from tutor import prompts
from tutor.config import PESOS_NIVEL, PREGUNTAS_POR_QUIZ
from tutor.llm import ClienteLLM, pedir_json
from tutor.progreso import Resultado, crear_resultado

logger = logging.getLogger(__name__)

OPCIONES_POR_PREGUNTA = 4


@dataclass(frozen=True)
class Pregunta:
    """Pregunta de opción múltiple con explicación pedagógica.

    ``nivel`` (HU-26) etiqueta la dificultad Bloom y pesa en la nota;
    las preguntas antiguas sin nivel cargan como "comprender".
    """

    enunciado: str
    opciones: list[str]
    correcta: int
    explicacion: str
    concepto: str
    nivel: str = "comprender"


@dataclass(frozen=True)
class Quiz:
    """Quiz de una unidad."""

    unidad: int
    preguntas: list[Pregunta]


@dataclass(frozen=True)
class Retroalimentacion:
    """Detalle por pregunta que la CLI muestra al estudiante."""

    pregunta: Pregunta
    respuesta: int
    acierto: bool


def validar_quiz(datos: Any, unidad: int, num_preguntas: int) -> Quiz:
    """Convierte y valida el JSON crudo del LLM en un ``Quiz``.

    Raises:
        ValueError: Si el número de preguntas u opciones no es el esperado,
            el índice de la correcta está fuera de rango o hay campos vacíos.
    """
    crudas = datos["preguntas"]
    if not isinstance(crudas, list) or len(crudas) != num_preguntas:
        raise ValueError(f"se esperaban {num_preguntas} preguntas")
    preguntas = []
    for numero, cruda in enumerate(crudas):
        opciones = [str(o) for o in cruda["opciones"]]
        correcta = int(cruda["correcta"])
        if len(opciones) != OPCIONES_POR_PREGUNTA:
            raise ValueError(
                f"la pregunta {numero} debe tener {OPCIONES_POR_PREGUNTA} opciones"
            )
        if not 0 <= correcta < OPCIONES_POR_PREGUNTA:
            raise ValueError(f"índice 'correcta' inválido en la pregunta {numero}")
        enunciado = str(cruda["enunciado"]).strip()
        explicacion = str(cruda["explicacion"]).strip()
        concepto = str(cruda["concepto"]).strip()
        if not enunciado or not explicacion or not concepto:
            raise ValueError(f"la pregunta {numero} tiene campos vacíos")
        nivel = str(cruda.get("nivel", "comprender")).strip()
        if nivel not in PESOS_NIVEL:
            raise ValueError(
                f"nivel desconocido en la pregunta {numero}: {nivel} "
                f"(esperado: {', '.join(PESOS_NIVEL)})"
            )
        preguntas.append(
            Pregunta(
                enunciado=enunciado,
                opciones=opciones,
                correcta=correcta,
                explicacion=explicacion,
                concepto=concepto,
                nivel=nivel,
            )
        )
    return Quiz(unidad=unidad, preguntas=preguntas)


def generar_quiz(
    cliente: ClienteLLM,
    titulo_unidad: str,
    conceptos: list[str],
    leccion_md: str,
    unidad: int,
    system: str,
    preguntas_previas: list[str] | None = None,
    priorizar: list[str] | None = None,
    num_preguntas: int = PREGUNTAS_POR_QUIZ,
) -> Quiz:
    """Genera el quiz de una unidad a partir de su lección.

    Args:
        cliente: Cliente LLM a usar.
        titulo_unidad: Título de la unidad evaluada.
        conceptos: Conceptos evaluables (etiquetan cada pregunta).
        leccion_md: Lección fuente de las preguntas.
        unidad: Índice de la unidad (base 0).
        system: System prompt del tutor.
        preguntas_previas: Enunciados ya vistos; exige variantes (HU-13).
        priorizar: Conceptos fallados en mini-quices intermedios; el quiz
            los cubre primero (HU-24).
        num_preguntas: Tamaño del quiz (HU-26: 2 x objetivos, mínimo 6).

    Raises:
        ErrorLLM: Si el modelo no produce un quiz válido tras reintentos.
    """
    logger.info("Generando quiz de la unidad %d", unidad)
    return pedir_json(
        cliente,
        system=system,
        prompt=prompts.prompt_quiz(
            titulo_unidad=titulo_unidad,
            conceptos=conceptos,
            leccion_md=leccion_md,
            num_preguntas=num_preguntas,
            preguntas_previas=preguntas_previas,
            priorizar=priorizar,
        ),
        validar=lambda datos: validar_quiz(datos, unidad, num_preguntas),
    )


def validar_respuesta(texto: str, num_opciones: int) -> int:
    """Valida la respuesta del estudiante (letra a-d o número 1-4).

    Returns:
        Índice de la opción elegida, base 0.

    Raises:
        ValueError: Si la entrada no corresponde a una opción.
    """
    texto = texto.strip().lower()
    letras = "abcd"[:num_opciones]
    if len(texto) == 1 and texto in letras:
        return letras.index(texto)
    if texto.isdigit() and 1 <= int(texto) <= num_opciones:
        return int(texto) - 1
    raise ValueError(
        f"Responde con una letra (a-{letras[-1]}) o número (1-{num_opciones})."
    )


def calificar(
    quiz: Quiz, respuestas: list[int]
) -> tuple[Resultado, list[Retroalimentacion]]:
    """Califica localmente las respuestas del estudiante.

    Args:
        quiz: Quiz respondido.
        respuestas: Índice elegido por pregunta (mismo orden del quiz).

    Returns:
        El ``Resultado`` (nota 0-100 y conceptos fallados, listo para
        registrarse en el progreso) y la retroalimentación por pregunta.

    Raises:
        ValueError: Si el número de respuestas no coincide con el de preguntas.
    """
    if len(respuestas) != len(quiz.preguntas):
        raise ValueError(
            f"Se esperaban {len(quiz.preguntas)} respuestas, "
            f"llegaron {len(respuestas)}."
        )
    detalle = [
        Retroalimentacion(
            pregunta=pregunta,
            respuesta=respuesta,
            acierto=respuesta == pregunta.correcta,
        )
        for pregunta, respuesta in zip(quiz.preguntas, respuestas, strict=True)
    ]
    # Nota ponderada por nivel Bloom (HU-26): aplicar pesa 3x recordar.
    peso_total = sum(PESOS_NIVEL[r.pregunta.nivel] for r in detalle)
    peso_logrado = sum(PESOS_NIVEL[r.pregunta.nivel] for r in detalle if r.acierto)
    nota = round(100 * peso_logrado / peso_total)
    fallados = sorted({r.pregunta.concepto for r in detalle if not r.acierto})
    return crear_resultado(quiz.unidad, nota, fallados), detalle


def resumenes(detalle: list[Retroalimentacion]) -> dict[str, dict[str, list[int]]]:
    """Resumen [aciertos, total] por concepto y por nivel (HU-26).

    Alimenta la tarjeta de resultado y el conversatorio: dice QUÉ atacar.
    """
    por_concepto: dict[str, list[int]] = {}
    por_nivel: dict[str, list[int]] = {}
    for r in detalle:
        for clave, grupo in (
            (r.pregunta.concepto, por_concepto),
            (r.pregunta.nivel, por_nivel),
        ):
            fila = grupo.setdefault(clave, [0, 0])
            fila[0] += int(r.acierto)
            fila[1] += 1
    return {"conceptos": por_concepto, "niveles": por_nivel}
