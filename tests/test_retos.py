"""Pruebas de los retos de código verificados (plan/v2/HU-28)."""

import json

import pytest

from tutor.ensenanza.agente import Agente
from tutor.ensenanza.curso import validar_guion, validar_reto
from tutor.nucleo.errores import ErrorDatos
from tutor.nucleo.models import Nivel, Objetivo, PerfilEstudiante

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta
from .test_guion_v2 import guion_v2_json
from .test_leccion import avanza

PERFIL = PerfilEstudiante(
    nivel=Nivel.BASICO,
    experiencia="",
    objetivo=Objetivo.DATOS,
    objetivo_detalle="",
    lenguaje="python",
)

RETO = {
    "enunciado": "Completa la función para calcular el ingreso.",
    "seed": "def ingreso(precio, cantidad):\n    # tu código aquí\n    return 0\n",
    "tests": [
        {"llamada": "ingreso(25, 4)", "esperado": "100"},
        {"llamada": "ingreso(10, 3)", "esperado": "30"},
    ],
}


def guion_con_retos():
    crudo = guion_v2_json()
    for grupo in crudo["objetivos"]:
        grupo["reto"] = dict(RETO)
    return json.dumps(crudo)


class TestValidarReto:
    def test_acepta_reto_valido(self):
        reto = validar_reto(RETO)
        assert reto.enunciado.startswith("Completa")
        assert len(reto.tests) == 2
        assert reto.tests[0] == {
            "llamada": "ingreso(25, 4)",
            "esperado": "100",
            "stdout_contiene": None,
        }

    def test_rechaza_seed_invalido(self):
        malo = {**RETO, "seed": "def ingreso(:\n"}
        with pytest.raises(ValueError, match="Python válido"):
            validar_reto(malo)

    @pytest.mark.parametrize(
        "tests",
        [
            [{"llamada": "f()", "esperado": "1"}] * 5,  # más de 4
            [{"llamada": "f()", "esperado": "1"}],  # menos de 2
            [{"llamada": "", "esperado": "1"}] * 2,  # llamada vacía
            [{"llamada": "f()"}] * 2,  # sin esperado ni stdout
        ],
    )
    def test_rechaza_tests_malformados(self, tests):
        with pytest.raises(ValueError):
            validar_reto({**RETO, "tests": tests})

    def test_guion_con_retos_y_sin_retos(self):
        guion = validar_guion(json.loads(guion_con_retos()))
        assert all(r is not None for r in guion.retos)
        sin = validar_guion(guion_v2_json())
        assert sin.retos == [None, None, None]
        # v1: sin campo retos.
        from .test_leccion import guion_json

        assert validar_guion(guion_json()).retos == []

    def test_serializa_ida_y_vuelta(self):
        from tutor.ensenanza.curso import _guion_a_json

        guion = validar_guion(json.loads(guion_con_retos()))
        assert validar_guion(_guion_a_json(guion)) == guion


def agente_con_retos(tmp_path, extra):
    falso = ClienteLLMFalso(
        [temario_respuesta(), guion_con_retos(), "apertura", *extra]
    )
    agente = Agente(falso, tmp_path, PERFIL)
    agente.turno_estudio(None, unidad=0)
    return agente, falso


class TestRetoEnElTurno:
    def test_turno_adjunta_reto_en_el_paso_final(self, tmp_path):
        agente, _ = agente_con_retos(tmp_path, [avanza("casi", si=True)] * 3)
        # Avanza hasta el último paso del objetivo 0 (fin_paso=3).
        r = None
        for _ in range(3):
            r = agente.turno_estudio("sigo")
        assert r["reto"] is not None
        assert r["reto"]["objetivo"] == 0
        assert r["reto"]["seed"].startswith("def ingreso")
        assert len(r["reto"]["tests"]) == 2

    def test_reto_superado_no_se_reoferta(self, tmp_path):
        agente, _ = agente_con_retos(
            tmp_path, [avanza("x")] * 3 + ["¡celebro tu función!"]
        )
        for _ in range(3):
            r = agente.turno_estudio("sigo")
        assert r["reto"] is not None
        agente.reto_superado(0, 0)
        # El mismo paso ya no adjunta el reto (payload recalculado).
        assert agente._payload_estudio("x", False, 3)["reto"] is None


class TestRetoSuperado:
    def test_suma_puntos_una_sola_vez(self, tmp_path):
        agente, falso = agente_con_retos(tmp_path, ["¡ya calculas ingresos!"])
        r = agente.reto_superado(0, 1)
        assert r["texto"] == "¡ya calculas ingresos!"
        assert agente.progreso.puntos == 10
        assert falso.carriles[-1] == "chat"
        with pytest.raises(ErrorDatos, match="ya estaba superado"):
            agente.reto_superado(0, 1)
        assert agente.progreso.puntos == 10  # no repaga

    def test_objetivo_sin_reto_falla(self, tmp_path):
        falso = ClienteLLMFalso(
            [temario_respuesta(), json.dumps(guion_v2_json()), "apertura"]
        )
        agente = Agente(falso, tmp_path, PERFIL)
        agente.turno_estudio(None, unidad=0)
        with pytest.raises(ErrorDatos, match="no tiene un reto"):
            agente.reto_superado(0, 0)


class TestPistaReto:
    def test_incluye_codigo_y_test_sin_solucion(self, tmp_path):
        agente, falso = agente_con_retos(tmp_path, ["mira la operación…"])
        texto = agente.pista_reto(0, "return precio + cantidad", "ingreso(10,3) → 13")
        assert texto == "mira la operación…"
        prompt = falso.llamadas[-1][1]
        assert "return precio + cantidad" in prompt
        assert "ingreso(10,3) → 13" in prompt
        assert "PROHIBIDO escribir" in prompt
        # El seed resuelto jamás viaja en el prompt de pista.
        assert "# tu código aquí" not in prompt

    def test_sin_conversacion_activa_falla(self, tmp_path):
        falso = ClienteLLMFalso([temario_respuesta()])
        agente = Agente(falso, tmp_path, PERFIL)
        assert agente.curso is not None  # genera el temario
        with pytest.raises(ErrorDatos):
            agente.pista_reto(0, "x", "y")
