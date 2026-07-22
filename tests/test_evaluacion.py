import json

import pytest

from tutor.config import PREGUNTAS_POR_QUIZ
from tutor.ensenanza.evaluacion import (
    Quiz,
    calificar,
    generar_quiz,
    validar_quiz,
    validar_respuesta,
)
from tutor.nucleo.errores import ErrorLLM

from .conftest import ClienteLLMFalso


def pregunta_json(correcta=1, concepto="variables"):
    return {
        "enunciado": "¿Qué imprime x = 3; x = x + 1; print(x)?",
        "opciones": ["3", "4", "x + 1", "error"],
        "correcta": correcta,
        "explicacion": "La asignación reemplaza el valor.",
        "concepto": concepto,
    }


def quiz_json(n=PREGUNTAS_POR_QUIZ, **cambios):
    return {"preguntas": [pregunta_json(**cambios) for _ in range(n)]}


def quiz_ejemplo(correctas=(0, 1, 2, 3)):
    datos = {
        "preguntas": [pregunta_json(correcta=c, concepto=f"c{c}") for c in correctas]
    }
    return validar_quiz(datos, unidad=0, num_preguntas=len(correctas))


class TestValidarQuiz:
    def test_acepta_quiz_valido(self):
        quiz = validar_quiz(quiz_json(), unidad=2, num_preguntas=PREGUNTAS_POR_QUIZ)
        assert isinstance(quiz, Quiz)
        assert quiz.unidad == 2
        assert len(quiz.preguntas) == PREGUNTAS_POR_QUIZ

    def test_rechaza_numero_de_preguntas_incorrecto(self):
        with pytest.raises(ValueError, match="preguntas"):
            validar_quiz(quiz_json(n=2), unidad=0, num_preguntas=4)

    def test_rechaza_correcta_fuera_de_opciones(self):
        with pytest.raises(ValueError, match="correcta"):
            validar_quiz(quiz_json(correcta=7), unidad=0, num_preguntas=4)

    def test_rechaza_pregunta_con_menos_de_4_opciones(self):
        datos = quiz_json()
        datos["preguntas"][1]["opciones"] = ["a", "b"]
        with pytest.raises(ValueError, match="4 opciones"):
            validar_quiz(datos, unidad=0, num_preguntas=4)


class TestGenerarQuiz:
    def test_genera_con_leccion_y_conceptos_en_prompt(self):
        falso = ClienteLLMFalso([json.dumps(quiz_json())])
        quiz = generar_quiz(
            falso,
            titulo_unidad="Variables",
            conceptos=["variables", "tipos"],
            leccion_md="# La lección",
            unidad=0,
            system="soy el tutor",
        )
        assert len(quiz.preguntas) == PREGUNTAS_POR_QUIZ
        system, prompt = falso.llamadas[0]
        assert system == "soy el tutor"
        assert "# La lección" in prompt
        assert "variables, tipos" in prompt

    def test_json_invalido_reintenta_y_falla_claro(self):
        falso = ClienteLLMFalso(["basura"] * 3)
        with pytest.raises(ErrorLLM):
            generar_quiz(falso, "t", ["c"], "md", 0, "sys")


class TestValidarRespuesta:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [("a", 0), ("B", 1), (" c ", 2), ("d", 3), ("1", 0), ("4", 3)],
    )
    def test_acepta_letras_y_numeros(self, entrada, esperado):
        assert validar_respuesta(entrada, 4) == esperado

    @pytest.mark.parametrize("entrada", ["", "e", "0", "5", "ab", "sí"])
    def test_rechaza_entradas_invalidas(self, entrada):
        with pytest.raises(ValueError):
            validar_respuesta(entrada, 4)


class TestCalificar:
    def test_todo_correcto_da_100(self):
        quiz = quiz_ejemplo()
        resultado, detalle = calificar(quiz, [0, 1, 2, 3])
        assert resultado.nota == 100
        assert resultado.conceptos_fallados == []
        assert all(r.acierto for r in detalle)

    def test_todo_incorrecto_da_0_y_lista_conceptos(self):
        quiz = quiz_ejemplo()
        resultado, detalle = calificar(quiz, [1, 0, 0, 0])
        assert resultado.nota == 0
        assert resultado.conceptos_fallados == ["c0", "c1", "c2", "c3"]
        assert not any(r.acierto for r in detalle)

    def test_mixto_calcula_nota_proporcional(self):
        quiz = quiz_ejemplo()
        resultado, _ = calificar(quiz, [0, 1, 0, 0])
        assert resultado.nota == 50
        assert resultado.conceptos_fallados == ["c2", "c3"]

    def test_numero_de_respuestas_incorrecto_lanza_error(self):
        with pytest.raises(ValueError, match="respuestas"):
            calificar(quiz_ejemplo(), [0])
