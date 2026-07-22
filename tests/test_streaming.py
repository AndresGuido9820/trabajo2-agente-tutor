"""Pruebas del streaming SSE de turnos conversacionales (plan/v2/HU-35)."""

import json

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.ensenanza.agente import Agente
from tutor.interfaces.web import crear_app
from tutor.nucleo.models import Nivel, Objetivo, PerfilEstudiante
from tutor.persistencia import db
from tutor.proveedor.llm import ExtractorCampoJSON

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta
from .test_leccion import avanza, guion_respuesta

PERFIL = PerfilEstudiante(
    nivel=Nivel.BASICO,
    experiencia="",
    objetivo=Objetivo.DATOS,
    objetivo_detalle="",
    lenguaje="python",
)


class TestFakeStream:
    def test_emite_trozos(self):
        falso = ClienteLLMFalso(["hola mundo estudioso"])
        falso.tamano_trozo = 4
        trozos = list(falso.generar_stream("s", "p", carril="chat"))
        assert "".join(trozos) == "hola mundo estudioso"
        assert len(trozos) == 5
        assert falso.carriles == ["chat"]


class TestExtractorIncremental:
    def test_extrae_mensaje_con_escapes_y_bordes(self):
        crudo = json.dumps(
            {"avanza": True, "mensaje": 'línea 1\ncon "comillas" y ñ'},
            ensure_ascii=False,
        )
        for n in (1, 3, 5, 100):  # cualquier partición de trozos
            extractor = ExtractorCampoJSON("mensaje")
            emitido = ""
            for i in range(0, len(crudo), n):
                emitido += extractor.alimentar(crudo[i : i + n])
            assert emitido == 'línea 1\ncon "comillas" y ñ', f"trozo={n}"
            assert extractor.crudo == crudo

    def test_unicode_escapado_partido(self):
        crudo = '{"mensaje": "a\\u00f1o"}'
        extractor = ExtractorCampoJSON("mensaje")
        emitido = "".join(extractor.alimentar(c) for c in crudo)  # de a 1 char
        assert emitido == "año"

    def test_sin_campo_no_emite(self):
        extractor = ExtractorCampoJSON("mensaje")
        assert extractor.alimentar('{"otro": "x"}') == ""


class TestTurnoStream:
    def test_misma_decision_que_no_stream(self, tmp_path):
        falso = ClienteLLMFalso(
            [temario_respuesta(), guion_respuesta(), "apertura", avanza("¡eso es!")]
        )
        falso.tamano_trozo = 3
        agente = Agente(falso, tmp_path, PERFIL)
        eventos = list(agente.turno_estudio_stream(None, unidad=0))
        assert eventos[-1]["fin"]["paso"] == 1

        eventos = list(agente.turno_estudio_stream("imprimo con print(4)"))
        deltas = "".join(e["delta"] for e in eventos if "delta" in e)
        fin = eventos[-1]["fin"]
        assert deltas == "¡eso es!" == fin["texto"]
        assert fin["paso"] == 2  # avanzó, igual que la variante clásica
        assert not fin["terminada"]

    def test_json_invalido_lanza_error(self, tmp_path):
        falso = ClienteLLMFalso(
            [temario_respuesta(), guion_respuesta(), "apertura", "esto no es json"]
        )
        agente = Agente(falso, tmp_path, PERFIL)
        list(agente.turno_estudio_stream(None, unidad=0))
        from tutor.nucleo.errores import ErrorLLM

        with pytest.raises(ErrorLLM):
            list(agente.turno_estudio_stream("sigamos"))


@pytest.fixture
def web_con(tmp_path):
    def _crear(respuestas):
        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        falso = ClienteLLMFalso(respuestas)
        web = TestClient(crear_app(configuracion, cliente=falso))
        r = web.post(
            "/api/perfil",
            json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
        )
        assert r.status_code == 200
        return web, tmp_path / "cursos" / "1" / "tutor.db"

    return _crear


class TestEndpointSSE:
    def test_eventos_delta_fin_y_persistencia(self, web_con):
        web, ruta = web_con(
            [temario_respuesta(), guion_respuesta(), "hola, ¡arranquemos!"]
        )
        r = web.post("/api/estudio/stream", json={"unidad": 0})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        cuerpo = r.text
        assert "event: delta" in cuerpo
        assert "event: fin" in cuerpo
        # El fin trae el mismo payload que /api/estudio.
        linea_fin = cuerpo.split("event: fin\n")[1].splitlines()[0]
        fin = json.loads(linea_fin.removeprefix("data: "))
        assert fin["texto"] == "hola, ¡arranquemos!"
        assert fin["unidad"] == 0 and fin["paso"] == 1
        # Persistencia idéntica a la variante clásica.
        mensajes = db.historial_chat(ruta, "u0")
        assert mensajes[-1]["rol"] == "tutor"
        assert mensajes[-1]["texto"] == "hola, ¡arranquemos!"

    def test_error_llega_como_evento(self, web_con):
        from tutor.nucleo.errores import ErrorLLM

        web, _ = web_con(
            [temario_respuesta(), guion_respuesta(), "apertura", ErrorLLM("se cayó")]
        )
        web.post("/api/estudio/stream", json={"unidad": 0})
        r = web.post("/api/estudio/stream", json={"mensaje": "sigamos"})
        assert r.status_code == 200  # el error viaja dentro del stream
        assert "event: error" in r.text
        assert "se cayó" in r.text
