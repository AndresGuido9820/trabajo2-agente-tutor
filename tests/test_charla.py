from tutor.config import MAX_TURNOS_CHARLA
from tutor.ensenanza.agente import Agente
from tutor.interfaces.ui import bucle_charla
from tutor.nucleo.errores import ErrorLLM

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


def agente_con_leccion(tmp_path, perfil, respuestas_extra):
    falso = ClienteLLMFalso([temario_respuesta(), "# Lección", *respuestas_extra])
    agente = Agente(cliente=falso, dir_datos=tmp_path, perfil=perfil)
    agente.abrir_unidad(0)
    return agente, falso


class TestCharlar:
    def test_incluye_leccion_historial_y_pregunta_en_prompt(self, tmp_path, perfil):
        agente, falso = agente_con_leccion(
            tmp_path, perfil, ["respuesta 1", "respuesta 2"]
        )
        agente.charlar(0, "¿qué es una variable?")
        agente.charlar(0, "sigo sin entender")

        system, prompt = falso.llamadas[-1]
        assert "MODO CHARLA" in system
        assert "# Lección" in prompt
        assert "¿qué es una variable?" in prompt  # historial del turno previo
        assert "respuesta 1" in prompt
        assert "sigo sin entender" in prompt  # pregunta nueva

    def test_acota_historial_a_max_turnos(self, tmp_path, perfil):
        n = MAX_TURNOS_CHARLA + 3
        agente, _ = agente_con_leccion(tmp_path, perfil, [f"r{i}" for i in range(n)])
        for i in range(n):
            agente.charlar(0, f"p{i}")
        historial = agente._charlas[0]
        assert len(historial) == MAX_TURNOS_CHARLA
        assert historial[0] == (f"p{3}", "r3")  # se descartaron los más viejos

    def test_charla_usa_leccion_cacheada_sin_regenerarla(self, tmp_path, perfil):
        agente, falso = agente_con_leccion(tmp_path, perfil, ["hola"])
        llamadas_antes = len(falso.llamadas)
        agente.charlar(0, "hola tutor")
        assert len(falso.llamadas) == llamadas_antes + 1  # solo la charla


class TestBucleCharla:
    def test_sale_con_entrada_vacia_sin_llamar_al_llm(self, tmp_path, perfil):
        agente, falso = agente_con_leccion(tmp_path, perfil, [])
        llamadas_antes = len(falso.llamadas)
        bucle_charla(agente, 0, entrada=lambda _: "")
        assert len(falso.llamadas) == llamadas_antes

    def test_error_llm_no_rompe_el_bucle(self, tmp_path, perfil, capsys):
        agente, _ = agente_con_leccion(tmp_path, perfil, [ErrorLLM("se cayó la API")])
        entradas = iter(["¿por qué?", "volver"])
        bucle_charla(agente, 0, entrada=lambda _: next(entradas))
        assert "se cayó la API" in capsys.readouterr().out
