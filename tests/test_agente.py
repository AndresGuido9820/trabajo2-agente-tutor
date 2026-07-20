import json

from tutor.agente import Agente, EstadoUnidad
from tutor.ui import Accion, parsear_accion

from .conftest import ClienteLLMFalso


def temario_respuesta():
    return json.dumps(
        {
            "lenguaje": "python",
            "unidades": [
                {
                    "titulo": f"Unidad {i}",
                    "objetivo": f"objetivo {i}",
                    "conceptos": ["variables", "tipos"],
                }
                for i in range(5)
            ],
        }
    )


def quiz_respuesta():
    return json.dumps(
        {
            "preguntas": [
                {
                    "enunciado": f"pregunta {i}",
                    "opciones": ["a", "b", "c", "d"],
                    "correcta": 0,
                    "explicacion": "porque sí",
                    "concepto": "variables",
                }
                for i in range(4)
            ]
        }
    )


class TestParsearAccion:
    def test_acciones_validas(self):
        assert parsear_accion("3", 5) == Accion("unidad", 2)
        assert parsear_accion("e 2", 5) == Accion("evaluar", 1)
        assert parsear_accion(" P ", 5) == Accion("progreso")
        assert parsear_accion("r", 5) == Accion("rehacer")
        assert parsear_accion("q", 5) == Accion("salir")

    def test_acciones_invalidas(self):
        import pytest

        for texto in ["", "9", "e 9", "e x", "hola", "0"]:
            with pytest.raises(ValueError):
                parsear_accion(texto, 5)


class TestAgente:
    def test_flujo_completo_con_llm_falso(self, tmp_path, perfil):
        """Integración: temario → lección bajo demanda → quiz → progreso."""
        falso = ClienteLLMFalso([temario_respuesta(), "# Lección 3", quiz_respuesta()])
        agente = Agente(cliente=falso, dir_datos=tmp_path, perfil=perfil)

        # Se puede navegar todas las unidades sin contenido generado (RF-3.3)
        filas = agente.filas_unidades()
        assert len(filas) == 5
        assert all(f.estado is EstadoUnidad.PENDIENTE for f in filas)

        # Entrar a una unidad no generada dispara la generación
        assert not agente.leccion_ya_generada(2)
        leccion = agente.abrir_unidad(2)
        assert leccion == "# Lección 3"
        assert agente.filas_unidades()[2].estado is EstadoUnidad.VISTA

        # Evaluar: quiz del LLM, calificación local, progreso actualizado
        quiz = agente.quiz_de_unidad(2)  # la lección sale del cache
        resultado, _detalle = agente.calificar_quiz(quiz, [0, 0, 1, 1])
        assert resultado.nota == 50
        assert agente.filas_unidades()[2].estado is EstadoUnidad.EVALUADA
        assert len(falso.llamadas) == 3  # temario + lección + quiz, sin extras

        # La persistencia sobrevive a una "nueva sesión"
        falso2 = ClienteLLMFalso([])
        agente2 = Agente(cliente=falso2, dir_datos=tmp_path, perfil=perfil)
        assert agente2.curso_ya_generado()
        assert agente2.progreso.mejor_nota(2) == 50
        assert agente2.abrir_unidad(2) == "# Lección 3"  # cache, sin LLM
        assert falso2.llamadas == []

    def test_rehacer_perfil_descarta_curso_pero_no_progreso(self, tmp_path, perfil):
        falso = ClienteLLMFalso([temario_respuesta(), "# L", quiz_respuesta()])
        agente = Agente(cliente=falso, dir_datos=tmp_path, perfil=perfil)
        quiz = agente.quiz_de_unidad(0)
        agente.calificar_quiz(quiz, [0, 0, 0, 0])

        agente.rehacer_perfil(perfil)
        assert not agente.curso_ya_generado()
        assert agente.progreso.mejor_nota(0) == 100  # el progreso se conserva
