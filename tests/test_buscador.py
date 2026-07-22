"""Pruebas del buscador global (plan/v2/HU-37)."""

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.interfaces.web import crear_app
from tutor.persistencia import db

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


class TestBusquedaEnDb:
    def test_snippet_con_contexto(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        largo = "x" * 200 + " groupby agrupa filas " + "y" * 200
        db.anotar_chat(ruta, "u0", "tutor", largo)
        [r] = db.buscar_mensajes(ruta, "groupby")
        assert "groupby agrupa filas" in r["fragmento"]
        assert r["fragmento"].startswith("…") and r["fragmento"].endswith("…")
        assert len(r["fragmento"]) < 160
        assert r["canal"] == "u0" and r["rol"] == "tutor" and r["id"] > 0

    def test_like_escapado(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        db.anotar_chat(ruta, "u0", "tutor", "el operador % es módulo")
        db.anotar_chat(ruta, "u0", "tutor", "no hablo de porcentajes aquí")
        resultados = db.buscar_mensajes(ruta, "% es módulo")
        assert len(resultados) == 1  # % literal, no comodín
        db.anotar_chat(ruta, "u0", "tutor", "guion_bajo en nombres")
        assert len(db.buscar_mensajes(ruta, "guion_bajo")) == 1

    def test_busca_sin_mayusculas_y_limita(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        for i in range(12):
            db.anotar_chat(ruta, "u0", "yo", f"BUCLES prueba {i}")
        assert len(db.buscar_mensajes(ruta, "bucles")) == 8

    def test_buscar_clases_por_titulo_y_conceptos(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        with db.abrir(ruta) as conexion:
            conexion.execute(
                "INSERT INTO clases(indice, titulo, objetivo, conceptos, "
                "actualizado_en) VALUES(0, 'Variables', 'Guardar datos', "
                "'[\"tipos\", \"asignación\"]', '2026-07-21')"
            )
        assert db.buscar_clases(ruta, "variab")[0]["titulo"] == "Variables"
        [por_concepto] = db.buscar_clases(ruta, "asignación")
        assert por_concepto["indice"] == 0
        assert "asignación" in por_concepto["fragmento"]
        assert db.buscar_clases(ruta, "recursión") == []


@pytest.fixture
def web_con_curso(tmp_path):
    configuracion = Configuracion(
        api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
    )
    falso = ClienteLLMFalso([temario_respuesta()])
    web = TestClient(crear_app(configuracion, cliente=falso))
    r = web.post(
        "/api/perfil",
        json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
    )
    assert r.status_code == 200
    web.get("/api/estado")
    return web, tmp_path / "cursos" / "1" / "tutor.db"


class TestEndpointBuscar:
    def test_minimo_2_caracteres(self, web_con_curso):
        web, _ = web_con_curso
        assert web.get("/api/buscar?q=a").json() == {"clases": [], "mensajes": []}
        assert web.get("/api/buscar").json() == {"clases": [], "mensajes": []}

    def test_busca_clases_y_mensajes(self, web_con_curso):
        web, ruta = web_con_curso
        db.anotar_chat(ruta, "u0", "tutor", "una variable guarda un dato")
        datos = web.get("/api/buscar?q=variable").json()
        assert datos["mensajes"], "debe encontrar el mensaje"
        assert datos["mensajes"][0]["curso"] == 1
        assert "variable" in datos["mensajes"][0]["fragmento"]
        # El temario falso tiene 'variables' entre los conceptos de cada clase.
        assert datos["clases"], "debe encontrar clases por concepto"
        assert all("variable" in c["fragmento"] for c in datos["clases"])

    def test_multicurso_y_archivado_marcado(self, web_con_curso):
        web, ruta = web_con_curso
        db.anotar_chat(ruta, "u0", "yo", "pregunta sobre listas")
        db.escribir_meta_curso(ruta, nombre="Ventas", archivado=True)
        web.post("/api/cursos", json={})  # curso 2 vacío
        datos = web.get("/api/buscar?q=listas").json()
        assert datos["mensajes"][0]["curso_nombre"] == "Ventas (archivado)"

    def test_historial_expone_ids(self, web_con_curso):
        web, ruta = web_con_curso
        db.anotar_chat(ruta, "u0", "yo", "hola")
        mensajes = web.get("/api/historial/u0").json()["mensajes"]
        assert mensajes[0]["id"] > 0 and mensajes[0]["texto"] == "hola"
