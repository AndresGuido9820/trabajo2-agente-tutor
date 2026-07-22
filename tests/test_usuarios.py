"""Pruebas del multiusuario por perfiles (HU-42)."""

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.interfaces.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import quiz_respuesta, temario_respuesta
from .test_chat_total import PERFIL_OK, turno_creacion


@pytest.fixture
def web(tmp_path):
    configuracion = Configuracion(
        api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
    )
    falso = ClienteLLMFalso(
        [
            turno_creacion("ok", True, PERFIL_OK),
            quiz_respuesta(4),
            temario_respuesta(),
        ]
    )
    return TestClient(crear_app(configuracion, cliente=falso)), tmp_path


class TestUsuarios:
    def test_arranca_con_el_perfil_principal(self, web):
        cliente, _ = web
        datos = cliente.get("/api/usuarios").json()
        assert datos["activo"] == "principal"
        assert datos["usuarios"][0]["id"] == "principal"

    def test_crear_activa_y_persiste(self, web):
        cliente, base = web
        r = cliente.post("/api/usuarios", json={"nombre": "María José"}).json()
        assert (
            r == {"id": "mar-a-jos", "nombre": "María José"}
            or r["nombre"] == "María José"
        )
        datos = cliente.get("/api/usuarios").json()
        assert datos["activo"] == r["id"]
        assert (base / "usuarios.json").exists()
        assert cliente.post("/api/usuarios", json={"nombre": "  "}).status_code == 400
        assert cliente.post("/api/usuarios/nadie/activar").status_code == 404

    def test_datos_totalmente_aislados_por_usuario(self, web):
        cliente, base = web
        # El principal crea su curso (creación + diagnóstico + temario).
        cliente.post("/api/creacion", json={"mensaje": "curso de datos ya"})
        cliente.post("/api/diagnostico/calificar", json={"respuestas": [0, 0, 0, 0]})
        assert len(cliente.get("/api/cursos").json()["cursos"]) == 1

        # Un usuario nuevo NO ve los cursos del principal.
        r = cliente.post("/api/usuarios", json={"nombre": "Ana"}).json()
        assert cliente.get("/api/cursos").json()["cursos"] == []
        assert (base / "usuarios" / r["id"]).exists()

        # Y al volver, el principal conserva lo suyo.
        cliente.post("/api/usuarios/principal/activar")
        assert len(cliente.get("/api/cursos").json()["cursos"]) == 1

    def test_nombres_repetidos_no_colisionan(self, web):
        cliente, _ = web
        a = cliente.post("/api/usuarios", json={"nombre": "Ana"}).json()
        b = cliente.post("/api/usuarios", json={"nombre": "Ana"}).json()
        assert a["id"] != b["id"]
