"""Pruebas de la exportación del curso a .zip (plan/v2/HU-33)."""

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from tutor import db
from tutor.config import Configuracion
from tutor.exportar import paquete_zip, slug
from tutor.progreso import Resultado, cargar_progreso, guardar_progreso
from tutor.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


class TestSlug:
    def test_nombres_raros(self):
        assert (
            slug("¡Bucles y condiciones! (parte 2)") == "bucles-y-condiciones-parte-2"
        )
        assert slug("Análisis de código") == "analisis-de-codigo"
        assert slug("???") == "clase"
        assert slug("", "mi-curso") == "mi-curso"


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
    web.get("/api/estado")  # genera el temario
    return web, tmp_path / "cursos" / "1"


class TestPaqueteZip:
    def test_contiene_diseno_clases_y_resultados(self, web_con_curso):
        _web, dir_curso = web_con_curso
        ruta = dir_curso / "tutor.db"
        db.anotar_chat(ruta, "u0", "yo", "hola tutor")
        db.anotar_chat(ruta, "u0", "tutor", "¡Empecemos con variables!")

        contenido = zipfile.ZipFile(io.BytesIO(paquete_zip(dir_curso)))
        nombres = contenido.namelist()
        raiz = nombres[0].split("/")[0]
        assert f"{raiz}/00-diseno.md" in nombres
        assert f"{raiz}/resultados.md" in nombres
        clases = [n for n in nombres if "/clase-" in n]
        assert len(clases) == 5  # una por unidad del temario falso
        assert any("clase-01-" in n for n in clases)

    def test_transcripcion_roles_e_hitos(self, web_con_curso):
        _web, dir_curso = web_con_curso
        ruta = dir_curso / "tutor.db"
        db.anotar_chat(ruta, "u0", "yo", "hola tutor")
        db.anotar_chat(ruta, "u0", "tutor", "¡Empecemos!")
        progreso = cargar_progreso(ruta)
        progreso.registrar(Resultado(0, 85, [], "2026-07-21T10:00:00+00:00"))
        progreso.completar(0)
        guardar_progreso(progreso, ruta)

        contenido = zipfile.ZipFile(io.BytesIO(paquete_zip(dir_curso)))
        clase = next(n for n in contenido.namelist() if "clase-01" in n)
        texto = contenido.read(clase).decode()
        assert "**Tú:**" in texto and "hola tutor" in texto
        assert "**Profe Bit:**" in texto
        assert "> 🎯 Evaluación: 85/100 — aprobada" in texto
        assert "> 🎉 Clase completada" in texto
        # Clase sin conversación → marcador amable.
        clase2 = next(n for n in contenido.namelist() if "clase-02" in n)
        assert "(sin conversación todavía)" in contenido.read(clase2).decode()
        # Resultados con la nota y los puntos.
        resultados = contenido.read(
            next(n for n in contenido.namelist() if "resultados" in n)
        ).decode()
        assert "mejor: 85/100" in resultados

    def test_endpoint_descarga_zip(self, web_con_curso):
        web, _ = web_con_curso
        r = web.get("/api/cursos/1/exportar")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/zip"
        assert "attachment" in r.headers["content-disposition"]
        assert zipfile.ZipFile(io.BytesIO(r.content)).namelist()

    def test_curso_inexistente_404_y_sin_diseno_409(self, web_con_curso):
        web, _ = web_con_curso
        assert web.get("/api/cursos/99/exportar").status_code == 404
        web.post("/api/cursos", json={})  # curso 2, vacío (sin diseño)
        assert web.get("/api/cursos/2/exportar").status_code == 409
