"""Pruebas del reencuentro al volver a una clase (plan/v2/HU-30)."""

import pytest
from fastapi.testclient import TestClient

from tutor import db
from tutor.config import HORAS_PARA_REENCUENTRO, Configuracion
from tutor.prompts import prompt_reencuentro
from tutor.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


@pytest.fixture
def crear_cliente_web(tmp_path):
    def _crear(respuestas_llm):
        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        falso = ClienteLLMFalso(respuestas_llm)
        web = TestClient(crear_app(configuracion, cliente=falso))
        r = web.post(
            "/api/perfil",
            json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
        )
        assert r.status_code == 200
        return web, falso, tmp_path

    return _crear


class TestPromptReencuentro:
    def test_incluye_mensajes_y_progreso(self):
        prompt = prompt_reencuentro(
            [
                {"rol": "yo", "texto": "¿qué es una lista?"},
                {"rol": "tutor", "texto": "Una colección ordenada..."},
            ],
            "clase en curso; le costaron: bucles",
        )
        assert "¿qué es una lista?" in prompt
        assert "Estudiante:" in prompt and "Tú:" in prompt
        assert "le costaron: bucles" in prompt
        assert "NO desarrolles contenido nuevo" in prompt

    def test_omite_roles_especiales_y_trunca(self):
        prompt = prompt_reencuentro(
            [{"rol": "quiz", "texto": "x"}, {"rol": "yo", "texto": "a" * 500}],
            "clase en curso",
        )
        assert "quiz" not in prompt
        assert "a" * 400 in prompt and "a" * 401 not in prompt


class TestUltimoMensajeEn:
    def test_sin_bd_ni_mensajes(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        assert db.ultimo_mensaje_en(ruta, "u0") is None
        db.anotar_chat(ruta, "u1", "yo", "hola")
        assert db.ultimo_mensaje_en(ruta, "u0") is None

    def test_devuelve_el_mas_reciente_del_canal(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        db.anotar_chat(ruta, "u0", "yo", "primero")
        db.anotar_chat(ruta, "u0", "tutor", "segundo")
        cuando = db.ultimo_mensaje_en(ruta, "u0")
        assert cuando is not None
        with db.abrir(ruta) as conexion:
            ultimo = conexion.execute(
                "SELECT creado_en FROM chat ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
        assert cuando == ultimo


class TestEndpointReencuentro:
    def test_historial_expone_ultimo_en_y_umbral(self, crear_cliente_web):
        web, _, base = crear_cliente_web([temario_respuesta()])
        web.get("/api/estado")
        datos = web.get("/api/historial/u0").json()
        assert datos["ultimo_en"] is None
        assert datos["horas_reencuentro"] == HORAS_PARA_REENCUENTRO

        db.anotar_chat(base / "cursos" / "1" / "tutor.db", "u0", "yo", "hola")
        datos = web.get("/api/historial/u0").json()
        assert datos["ultimo_en"] is not None

    def test_reencuentro_genera_y_anota(self, crear_cliente_web):
        web, falso, base = crear_cliente_web(
            [temario_respuesta(), "¡Bienvenido de vuelta! Íbamos en listas."]
        )
        web.get("/api/estado")
        ruta = base / "cursos" / "1" / "tutor.db"
        db.anotar_chat(ruta, "u0", "yo", "¿qué es una lista?")

        r = web.post("/api/clase/0/reencuentro")
        assert r.status_code == 200
        assert "Bienvenido de vuelta" in r.json()["texto"]
        # El prompt llevó la conversación previa y el estado del progreso.
        assert "¿qué es una lista?" in falso.llamadas[-1][1]
        assert "clase en curso" in falso.llamadas[-1][1]
        # Quedó anotado en el historial de la clase.
        mensajes = db.historial_chat(ruta, "u0")
        assert mensajes[-1]["rol"] == "tutor"
        assert "Bienvenido" in mensajes[-1]["texto"]

    def test_unidad_inexistente_da_404(self, crear_cliente_web):
        web, _, _ = crear_cliente_web([temario_respuesta()])
        web.get("/api/estado")
        assert web.post("/api/clase/99/reencuentro").status_code == 404
