"""Pruebas del guion v2 por objetivos con mini-quices (plan/v2/HU-24)."""

import json

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.ensenanza.agente import Agente
from tutor.ensenanza.curso import validar_guion
from tutor.interfaces.web import crear_app
from tutor.nucleo.models import Nivel, Objetivo, PerfilEstudiante

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta
from .test_leccion import avanza

PERFIL = PerfilEstudiante(
    nivel=Nivel.BASICO,
    experiencia="",
    objetivo=Objetivo.DATOS,
    objetivo_detalle="",
    lenguaje="python",
)


def pregunta(concepto="variables", correcta=0):
    return {
        "enunciado": f"¿qué imprime este código sobre {concepto}?",
        "opciones": ["a", "b", "c", "d"],
        "correcta": correcta,
        "explicacion": "porque sí",
        "concepto": concepto,
    }


def guion_v2_json(objetivos=3, pasos=4):
    return {
        "version": 2,
        "objetivos": [
            {
                "objetivo": f"objetivo {k}",
                "pasos": [
                    {"tipo": "explicacion", "instruccion": f"paso {k}.{j}"}
                    for j in range(pasos)
                ],
                "quiz": [pregunta("variables"), pregunta("tipos", 1)],
            }
            for k in range(objetivos)
        ],
    }


def guion_v2_respuesta(**kwargs):
    return json.dumps(guion_v2_json(**kwargs))


class TestValidarGuionV2:
    def test_aplana_pasos_y_marca_fronteras(self):
        guion = validar_guion(guion_v2_json(objetivos=3, pasos=4))
        assert len(guion.objetivos) == 3
        assert len(guion.pasos) == 12
        assert [i.fin_paso for i in guion.intermedios] == [3, 7, 11]
        assert len(guion.intermedios[0].preguntas) == 2

    @pytest.mark.parametrize("n", [2, 5])
    def test_rechaza_numero_de_objetivos(self, n):
        with pytest.raises(ValueError, match="objetivos"):
            validar_guion(guion_v2_json(objetivos=n))

    @pytest.mark.parametrize("n", [3, 8])
    def test_rechaza_pasos_por_objetivo_fuera_de_rango(self, n):
        with pytest.raises(ValueError, match="pasos"):
            validar_guion(guion_v2_json(pasos=n))

    def test_rechaza_quiz_sin_2_preguntas(self):
        crudo = guion_v2_json()
        crudo["objetivos"][0]["quiz"] = [pregunta()]
        with pytest.raises(ValueError, match="preguntas intermedias"):
            validar_guion(crudo)

    def test_guion_v1_sigue_funcionando(self):
        from .test_leccion import guion_json

        guion = validar_guion(guion_json())
        assert guion.intermedios == []

    def test_serializa_y_recarga_identico(self, tmp_path):
        from tutor.ensenanza.curso import _guion_a_json

        guion = validar_guion(guion_v2_json())
        assert validar_guion(_guion_a_json(guion)) == guion


def agente_en_fin_de_objetivo(tmp_path, respuestas_extra):
    """Agente con guion v2 (3 objetivos x 4 pasos) parado en el paso 3."""
    falso = ClienteLLMFalso(
        [temario_respuesta(), guion_v2_respuesta(), "apertura", *respuestas_extra]
    )
    agente = Agente(falso, tmp_path, PERFIL)
    agente.turno_estudio(None, unidad=0)  # inicia (paso 0)
    sesion = agente._lecciones_activas[0]
    sesion.paso = 3  # último paso del objetivo 0
    return agente, falso


class TestQuizIntermedio:
    def test_cerrar_objetivo_entrega_quiz_sin_correctas(self, tmp_path):
        agente, _ = agente_en_fin_de_objetivo(tmp_path, [avanza("¡bien!")])
        r = agente.turno_estudio("listo, entendí")
        assert r["objetivo"] == 2 and r["objetivos_total"] == 3
        assert r["quiz_intermedio"] is not None
        assert len(r["quiz_intermedio"]) == 2
        assert "correcta" not in r["quiz_intermedio"][0]
        assert "explicacion" not in r["quiz_intermedio"][0]

    def test_1_de_2_cumple_y_da_puntos(self, tmp_path):
        agente, _ = agente_en_fin_de_objetivo(tmp_path, [avanza("¡bien!")])
        agente.turno_estudio("listo")
        r = agente.responder_quiz_intermedio(0, [0, 0])  # correctas: 0 y 1
        assert r["cumplido"] is True and r["aciertos"] == 1
        assert agente.progreso.puntos == 5
        assert agente.progreso.objetivos_cumplidos["0"] == [0]
        # El concepto fallado queda anotado y entra a la cola de repaso.
        assert agente.progreso.fallados_intermedios["0"] == ["tipos"]
        assert any(i["concepto"] == "tipos" for i in agente.progreso.cola_repaso)

    def test_0_de_2_repasa_una_vez_y_luego_avanza(self, tmp_path):
        agente, falso = agente_en_fin_de_objetivo(
            tmp_path, [avanza("¡bien!"), "repaso con otro ejemplo"]
        )
        agente.turno_estudio("listo")
        r = agente.responder_quiz_intermedio(0, [3, 3])  # 0 aciertos
        assert r["repite"] is True and r["cumplido"] is False
        assert r["texto"] == "repaso con otro ejemplo"
        assert falso.carriles[-1] == "chat"
        # Segundo intento: aunque falle, avanza y anota los 2 conceptos.
        r = agente.responder_quiz_intermedio(0, [3, 3])
        assert r["cumplido"] is True and r["repite"] is False
        assert sorted(agente.progreso.fallados_intermedios["0"]) == [
            "tipos",
            "variables",
        ]

    def test_sin_quiz_pendiente_falla(self, tmp_path):
        from tutor.nucleo.errores import ErrorDatos

        agente, _ = agente_en_fin_de_objetivo(tmp_path, [])
        with pytest.raises(ErrorDatos):
            agente.responder_quiz_intermedio(0, [0, 0])

    def test_evaluacion_final_prioriza_fallados(self, tmp_path):
        from .test_agente import quiz_respuesta

        agente, falso = agente_en_fin_de_objetivo(
            tmp_path, [avanza("¡bien!"), "una lección", quiz_respuesta()]
        )
        agente.turno_estudio("listo")
        agente.responder_quiz_intermedio(0, [0, 0])  # falla "tipos"
        agente.quiz_de_unidad(0)
        assert "tipos" in falso.llamadas[-1][1]
        assert "PRIORIZA" in falso.llamadas[-1][1]


class TestEndpointQuizIntermedio:
    def test_flujo_por_api(self, tmp_path):
        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        falso = ClienteLLMFalso(
            [temario_respuesta(), guion_v2_respuesta(), "apertura", avanza("ok")]
        )
        web = TestClient(crear_app(configuracion, cliente=falso))
        web.post(
            "/api/perfil",
            json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
        )
        web.post("/api/estudio", json={"unidad": 0})
        # Sin pendiente → 409; respuestas inválidas tras forzar → 400.
        r = web.post(
            "/api/estudio/quiz-intermedio", json={"unidad": 0, "respuestas": [0, 0]}
        )
        assert r.status_code == 409
