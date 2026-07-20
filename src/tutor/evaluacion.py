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
from tutor.config import PREGUNTAS_POR_QUIZ
from tutor.llm import ClienteLLM, pedir_json
from tutor.progreso import Resultado, crear_resultado

logger = logging.getLogger(__name__)

OPCIONES_POR_PREGUNTA = 4


@dataclass(frozen=True)
class Pregunta:
    """Pregunta de opción múltiple con explicación pedagógica."""

    enunciado: str
    opciones: list[str]
    correcta: int
    explicacion: str
    concepto: str


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
        preguntas.append(
            Pregunta(
                enunciado=enunciado,
                opciones=opciones,
                correcta=correcta,
                explicacion=explicacion,
                concepto=concepto,
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
) -> Quiz:
    """Genera el quiz de una unidad a partir de su lección.

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
            num_preguntas=PREGUNTAS_POR_QUIZ,
        ),
        validar=lambda datos: validar_quiz(datos, unidad, PREGUNTAS_POR_QUIZ),
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
    aciertos = sum(1 for r in detalle if r.acierto)
    nota = round(100 * aciertos / len(quiz.preguntas))
    fallados = sorted({r.pregunta.concepto for r in detalle if not r.acierto})
    return crear_resultado(quiz.unidad, nota, fallados), detalle
