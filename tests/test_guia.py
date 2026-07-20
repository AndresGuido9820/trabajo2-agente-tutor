import json

import pytest

from tutor.agente import Agente, EstadoUnidad
from tutor.config import (
    NOTA_APROBATORIA,
    PUNTOS_PRIMER_INTENTO,
    PUNTOS_QUIZ_APROBADO,
    PUNTOS_SEGUNDO_INTENTO,
)
from tutor.curso import validar_guia
from tutor.errores import ErrorBloqueada

from .conftest import ClienteLLMFalso
from .test_agente import quiz_respuesta, temario_respuesta


def guia_json(n_secciones=3):
    return {
        "secciones": [
            {
                "objetivo": f"objetivo {i}",
                "contenido": f"contenido de la sección {i}",
                "checkpoint": {
                    "pregunta": f"¿pregunta {i}?",
                    "opciones": ["a", "b", "c", "d"],
                    "correcta": 1,
                    "pista": f"pista socrática {i}",
                    "explicacion": f"explicación {i}",
                    "concepto": "variables",
                },
            }
            for i in range(n_secciones)
        ]
    }


def guia_respuesta():
    return json.dumps(guia_json())


def agente_nuevo(tmp_path, perfil, respuestas):
    falso = ClienteLLMFalso([temario_respuesta(), *respuestas])
    return Agente(cliente=falso, dir_datos=tmp_path, perfil=perfil), falso


class TestValidarGuia:
    def test_acepta_guia_valida(self):
        guia = validar_guia(guia_json())
        assert len(guia.secciones) == 3
        assert guia.secciones[0].checkpoint.correcta == 1

    @pytest.mark.parametrize("n", [2, 6])
    def test_rechaza_numero_de_secciones_fuera_de_rango(self, n):
        with pytest.raises(ValueError, match="secciones"):
            validar_guia(guia_json(n))

    def test_rechaza_checkpoint_sin_pista(self):
        datos = guia_json()
        datos["secciones"][1]["checkpoint"]["pista"] = " "
        with pytest.raises(ValueError, match="vacíos"):
            validar_guia(datos)

    def test_rechaza_checkpoint_con_3_opciones(self):
        datos = guia_json()
        datos["secciones"][0]["checkpoint"]["opciones"] = ["a", "b", "c"]
        with pytest.raises(ValueError, match="4 opciones"):
            validar_guia(datos)


class TestCheckpoints:
    def test_acierto_primer_intento_da_10_y_explica(self, tmp_path, perfil):
        agente, _ = agente_nuevo(tmp_path, perfil, [guia_respuesta()])
        agente.guia_de_unidad(0)
        r = agente.responder_checkpoint(0, seccion=0, opcion=1, intento=1)
        assert r.correcto and r.revelada
        assert r.puntos == PUNTOS_PRIMER_INTENTO
        assert r.texto == "explicación 0"
        assert agente.progreso.puntos == PUNTOS_PRIMER_INTENTO

    def test_fallo_da_pista_sin_revelar_y_segundo_acierto_da_5(self, tmp_path, perfil):
        agente, _ = agente_nuevo(tmp_path, perfil, [guia_respuesta()])
        agente.guia_de_unidad(0)
        r1 = agente.responder_checkpoint(0, seccion=0, opcion=0, intento=1)
        assert not r1.correcto and not r1.revelada
        assert r1.texto == "pista socrática 0" and r1.puntos == 0

        r2 = agente.responder_checkpoint(0, seccion=0, opcion=1, intento=2)
        assert r2.correcto and r2.puntos == PUNTOS_SEGUNDO_INTENTO
        assert agente.progreso.puntos == PUNTOS_SEGUNDO_INTENTO

    def test_dos_fallos_revelan_explicacion_sin_puntos(self, tmp_path, perfil):
        agente, _ = agente_nuevo(tmp_path, perfil, [guia_respuesta()])
        agente.guia_de_unidad(0)
        agente.responder_checkpoint(0, 0, opcion=0, intento=1)
        r = agente.responder_checkpoint(0, 0, opcion=2, intento=2)
        assert not r.correcto and r.revelada
        assert r.texto == "explicación 0" and agente.progreso.puntos == 0

    def test_los_puntos_persisten_entre_sesiones(self, tmp_path, perfil):
        agente, _ = agente_nuevo(tmp_path, perfil, [guia_respuesta()])
        agente.guia_de_unidad(0)
        agente.responder_checkpoint(0, 0, opcion=1, intento=1)
        agente2 = Agente(ClienteLLMFalso([]), tmp_path, perfil)
        assert agente2.progreso.puntos == PUNTOS_PRIMER_INTENTO


class TestProgresion:
    def test_unidad_bloqueada_hasta_aprobar_anterior(self, tmp_path, perfil):
        agente, _ = agente_nuevo(tmp_path, perfil, [])
        assert agente.curso is not None  # fuerza la carga del temario
        assert agente.desbloqueada(0)
        assert not agente.desbloqueada(1)
        with pytest.raises(ErrorBloqueada, match="bloqueada"):
            agente.guia_de_unidad(1)
        with pytest.raises(ErrorBloqueada):
            agente.quiz_de_unidad(1)

    def test_quiz_aprobado_desbloquea_y_suma_puntos(self, tmp_path, perfil):
        agente, _ = agente_nuevo(tmp_path, perfil, ["# lección", quiz_respuesta()])
        quiz = agente.quiz_de_unidad(0)
        resultado, _ = agente.calificar_quiz(quiz, [0, 0, 0, 0])  # 100
        assert resultado.nota >= NOTA_APROBATORIA
        assert agente.desbloqueada(1)
        assert agente.progreso.puntos == PUNTOS_QUIZ_APROBADO
        assert agente.filas_unidades()[0].estado is EstadoUnidad.APROBADA
        assert agente.filas_unidades()[1].estado is EstadoUnidad.PENDIENTE

    def test_reprobar_no_desbloquea_y_aprobar_solo_paga_una_vez(self, tmp_path, perfil):
        agente, _ = agente_nuevo(
            tmp_path, perfil, ["# lección", quiz_respuesta(), quiz_respuesta()]
        )
        quiz = agente.quiz_de_unidad(0)
        agente.calificar_quiz(quiz, [1, 1, 1, 1])  # 0: reprobado
        assert not agente.desbloqueada(1)
        assert agente.progreso.puntos == 0

        quiz2 = agente.quiz_de_unidad(0)
        agente.calificar_quiz(quiz2, [0, 0, 0, 0])  # 100: aprueba
        assert agente.progreso.puntos == PUNTOS_QUIZ_APROBADO


class TestConversatorio:
    def test_incluye_guia_conceptos_fallados_y_reglas(self, tmp_path, perfil):
        agente, falso = agente_nuevo(
            tmp_path,
            perfil,
            [guia_respuesta(), quiz_respuesta(), "hola, ¿qué pasó?"],
        )
        agente.guia_de_unidad(0)
        quiz = agente.quiz_de_unidad(0)  # usa la guía como material, sin lección
        _, prompt_quiz = falso.llamadas[-1]
        assert "contenido de la sección 0" in prompt_quiz
        agente.calificar_quiz(quiz, [1, 1, 1, 1])  # reprueba: falla "variables"

        respuesta = agente.conversatorio(0, "")
        assert respuesta == "hola, ¿qué pasó?"
        system, prompt = falso.llamadas[-1]
        assert "CONVERSATORIO" in system
        assert "variables" in system  # conceptos fallados en el system
        assert "contenido de la sección 0" in prompt  # la guía como contexto

    def test_historial_se_mantiene(self, tmp_path, perfil):
        agente, falso = agente_nuevo(tmp_path, perfil, [guia_respuesta(), "r1", "r2"])
        agente.guia_de_unidad(0)
        agente.conversatorio(0, "primera duda")
        agente.conversatorio(0, "segunda duda")
        _, prompt = falso.llamadas[-1]
        assert "primera duda" in prompt and "r1" in prompt
