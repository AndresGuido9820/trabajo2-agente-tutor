import json

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.models import Nivel, Objetivo
from tutor.perfil import validar_perfil_extraido
from tutor.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


def extraccion(**cambios):
    base = {
        "nivel": "basico",
        "objetivo": "datos",
        "objetivo_detalle": "",
        "experiencia": "Excel",
        "lenguaje": "python",
    }
    base.update(cambios)
    return base


class TestValidarPerfilExtraido:
    def test_extrae_perfil_completo(self):
        perfil = validar_perfil_extraido(extraccion(), "hazme un curso de python")
        assert perfil.nivel is Nivel.BASICO
        assert perfil.objetivo is Objetivo.DATOS
        assert perfil.lenguaje == "python"
        assert perfil.descripcion == "hazme un curso de python"

    def test_objetivo_otro_sin_detalle_usa_la_peticion(self):
        perfil = validar_perfil_extraido(
            extraccion(objetivo="otro", objetivo_detalle=""),
            "quiero programar robots",
        )
        assert perfil.objetivo_detalle == "quiero programar robots"

    def test_nivel_invalido_lanza_error(self):
        with pytest.raises(ValueError):
            validar_perfil_extraido(extraccion(nivel="experto"), "x")


class TestCursoPorPrompt:
    def _web(self, tmp_path, respuestas):
        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        falso = ClienteLLMFalso(respuestas)
        return TestClient(crear_app(configuracion, cliente=falso)), falso

    def test_crea_curso_desde_prompt_libre(self, tmp_path):
        web, falso = self._web(
            tmp_path, [json.dumps(extraccion()), temario_respuesta()]
        )
        r = web.post(
            "/api/curso",
            json={"prompt": "hazme un curso de python para analizar mis ventas"},
        )
        assert r.status_code == 200
        _, prompt_llm = falso.llamadas[0]
        assert "analizar mis ventas" in prompt_llm  # la petición va al extractor

        estado = web.get("/api/estado").json()
        assert estado["perfil"] is True and estado["lenguaje"] == "python"
        # La petición original queda en el system de generaciones posteriores
        _, _ = falso.llamadas[-1]
        system_temario, _ = falso.llamadas[-1]
        assert "analizar mis ventas" in system_temario

    def test_prompt_demasiado_corto_da_400(self, tmp_path):
        web, _ = self._web(tmp_path, [])
        assert web.post("/api/curso", json={"prompt": "hola"}).status_code == 400
