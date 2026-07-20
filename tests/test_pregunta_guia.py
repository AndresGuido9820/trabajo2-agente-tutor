import pytest

from tutor.agente import Agente

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta
from .test_guia import guia_respuesta


def agente_con_guia(tmp_path, perfil, respuestas):
    falso = ClienteLLMFalso([temario_respuesta(), guia_respuesta(), *respuestas])
    agente = Agente(falso, tmp_path, perfil)
    agente.guia_de_unidad(0)
    return agente, falso


class TestPreguntarGuia:
    def test_incluye_seccion_y_reglas_socraticas(self, tmp_path, perfil):
        agente, falso = agente_con_guia(tmp_path, perfil, ["buena pregunta"])
        respuesta = agente.preguntar_guia(0, 1, "¿por qué se usa el =?")
        assert respuesta == "buena pregunta"
        system, prompt = falso.llamadas[-1]
        assert "MODO CHARLA" in system  # reglas socráticas de HU-09
        assert "contenido de la sección 1" in prompt  # sección actual
        assert "¿pregunta 1?" in prompt  # enunciado del checkpoint
        assert "NO reveles" in prompt
        assert "¿por qué se usa el =?" in prompt

    def test_no_filtra_explicacion_ni_pista_del_checkpoint(self, tmp_path, perfil):
        agente, falso = agente_con_guia(tmp_path, perfil, ["ok"])
        agente.preguntar_guia(0, 0, "dame la respuesta del checkpoint")
        _, prompt = falso.llamadas[-1]
        assert "explicación 0" not in prompt
        assert "pista socrática 0" not in prompt

    def test_mantiene_historial_por_unidad(self, tmp_path, perfil):
        agente, falso = agente_con_guia(tmp_path, perfil, ["r1", "r2"])
        agente.preguntar_guia(0, 0, "primera")
        agente.preguntar_guia(0, 1, "segunda")
        _, prompt = falso.llamadas[-1]
        assert "primera" in prompt and "r1" in prompt

    def test_seccion_invalida_lanza_value_error(self, tmp_path, perfil):
        agente, _ = agente_con_guia(tmp_path, perfil, [])
        with pytest.raises(ValueError, match="sección"):
            agente.preguntar_guia(0, 99, "hola")


class TestArtefacto:
    def test_genera_cachea_y_persiste(self, tmp_path, perfil):
        html = "<!doctype html><html><body>interactivo</body></html>"
        agente, falso = agente_con_guia(tmp_path, perfil, [html])
        assert agente.artefacto_de_seccion(0, 0) == html
        llamadas = len(falso.llamadas)
        assert agente.artefacto_de_seccion(0, 0) == html  # cache
        assert len(falso.llamadas) == llamadas

        # Persistido: otra sesión lo sirve sin LLM
        agente2 = Agente(ClienteLLMFalso([]), tmp_path, perfil)
        assert agente2.artefacto_de_seccion(0, 0) == html

    def test_tolera_fences_de_markdown(self, tmp_path, perfil):
        agente, _ = agente_con_guia(
            tmp_path, perfil, ["```html\n<!doctype html><p>x</p>\n```"]
        )
        assert agente.artefacto_de_seccion(0, 1).startswith("<!doctype html>")

    def test_prompt_incluye_contenido_y_reglas(self, tmp_path, perfil):
        agente, falso = agente_con_guia(tmp_path, perfil, ["<!doctype html>"])
        agente.artefacto_de_seccion(0, 2)
        _, prompt = falso.llamadas[-1]
        assert "contenido de la sección 2" in prompt
        assert "autocontenido" in prompt
        assert "sin recursos externos" in prompt


class TestPreguntaGuiaWeb:
    def test_endpoint_responde_y_valida(self, tmp_path, perfil):
        from fastapi.testclient import TestClient

        from tutor.config import Configuracion
        from tutor.web import crear_app

        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        falso = ClienteLLMFalso([temario_respuesta(), guia_respuesta(), "respuesta"])
        web = TestClient(crear_app(configuracion, cliente=falso))
        web.post(
            "/api/perfil",
            json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
        )
        web.post("/api/guia/0")

        r = web.post("/api/guia/0/pregunta", json={"seccion": 0, "mensaje": "¿y esto?"})
        assert r.status_code == 200 and r.json()["texto"] == "respuesta"
        assert (
            web.post(
                "/api/guia/0/pregunta", json={"seccion": 99, "mensaje": "x"}
            ).status_code
            == 400
        )
