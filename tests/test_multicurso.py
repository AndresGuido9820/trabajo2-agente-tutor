from fastapi.testclient import TestClient

from tutor import db
from tutor.config import Configuracion
from tutor.models import Nivel, Objetivo, PerfilEstudiante
from tutor.perfil import guardar_perfil
from tutor.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta
from .test_chat_total import PERFIL_OK, turno_creacion


def web_con(tmp_path, respuestas):
    configuracion = Configuracion(
        api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
    )
    falso = ClienteLLMFalso(respuestas)
    return TestClient(crear_app(configuracion, cliente=falso)), falso


class TestMisCursos:
    def test_sin_cursos_lista_vacia_y_crear_activa(self, tmp_path):
        web, _ = web_con(tmp_path, [])
        assert web.get("/api/cursos").json() == {"cursos": []}
        r = web.post("/api/cursos")
        assert r.json() == {"id": 1}
        cursos = web.get("/api/cursos").json()["cursos"]
        assert cursos[0]["nombre"] == "Curso sin diseñar" and cursos[0]["activo"]

    def test_dos_cursos_independientes(self, tmp_path):
        web, _ = web_con(
            tmp_path,
            [
                turno_creacion("ok", True, PERFIL_OK),
                temario_respuesta(),
            ],
        )
        web.post("/api/cursos")
        web.post("/api/creacion", json={"mensaje": "curso de datos ya dale"})
        assert web.get("/api/estado").json()["perfil"] is True

        # Segundo curso: vacío e independiente
        assert web.post("/api/cursos").json()["id"] == 2
        assert web.get("/api/estado").json() == {"perfil": False}
        assert web.get("/api/historial/creacion").json()["mensajes"] == []

        # Volver al curso 1: todo sigue ahí
        web.post("/api/cursos/1/activar")
        e = web.get("/api/estado").json()
        assert e["perfil"] is True and e["curso_id"] == 1
        assert len(web.get("/api/historial/creacion").json()["mensajes"]) == 2

    def test_activar_inexistente_404(self, tmp_path):
        web, _ = web_con(tmp_path, [])
        assert web.post("/api/cursos/9/activar").status_code == 404

    def test_migra_curso_unico_a_cursos_1(self, tmp_path):
        # Formato anterior: tutor.db en la raíz del dir de datos
        perfil = PerfilEstudiante(Nivel.BASICO, "", Objetivo.DATOS, "", "python")
        guardar_perfil(perfil, tmp_path / "tutor.db")
        db.anotar_chat(tmp_path / "tutor.db", "u0", "yo", "hola")

        web, _ = web_con(tmp_path, [temario_respuesta()])
        assert not (tmp_path / "tutor.db").exists()
        assert (tmp_path / "cursos" / "1" / "tutor.db").exists()
        cursos = web.get("/api/cursos").json()["cursos"]
        assert len(cursos) == 1 and cursos[0]["id"] == 1
        [mensaje] = web.get("/api/historial/u0").json()["mensajes"]
        assert mensaje["rol"] == "yo" and mensaje["texto"] == "hola"


class TestDisenoEstructurado:
    def _web_con_curso(self, tmp_path):
        web, falso = web_con(
            tmp_path, [turno_creacion("ok", True, PERFIL_OK), temario_respuesta()]
        )
        web.post("/api/cursos")
        web.post("/api/creacion", json={"mensaje": "curso de datos ya dale"})
        return web, falso

    def test_diseno_estructurado_se_lee_y_edita(self, tmp_path):
        web, _ = self._web_con_curso(tmp_path)
        diseno = web.get("/api/diseno").json()
        assert diseno["lenguaje"] == "python"
        assert diseno["clases"][0]["titulo"] == "Unidad 0"
        assert diseno["clases"][0]["conceptos"] == ["variables", "tipos"]

        diseno["clases"][0]["titulo"] = "Clase renombrada a mano"
        r = web.post(
            "/api/diseno",
            json={"lenguaje": diseno["lenguaje"], "clases": diseno["clases"]},
        )
        assert r.status_code == 200
        # El estado (lo que el LLM y la UI reciben) refleja la edición
        assert (
            web.get("/api/estado").json()["unidades"][0]["titulo"]
            == "Clase renombrada a mano"
        )
        # Y el plan .md se regeneró desde la estructura
        assert "Clase renombrada a mano" in web.get("/api/plan").json()["md"]

    def test_diseno_invalido_da_400(self, tmp_path):
        web, _ = self._web_con_curso(tmp_path)
        diseno = web.get("/api/diseno").json()
        diseno["clases"][0]["titulo"] = "  "
        r = web.post(
            "/api/diseno",
            json={"lenguaje": diseno["lenguaje"], "clases": diseno["clases"]},
        )
        assert r.status_code == 400


class TestMigracionIdempotente:
    """La migración legacy no puede repetirse (hallazgo 2026-07-21)."""

    def test_json_legacy_no_aplasta_cursos_existentes(self, tmp_path):
        import json as json_mod

        from tutor import db as db_mod
        from tutor.config import Configuracion
        from tutor.web import crear_app

        from .conftest import ClienteLLMFalso

        # Un multicurso YA migrado con datos nuevos...
        ruta = tmp_path / "cursos" / "1" / "tutor.db"
        db_mod.anotar_chat(ruta, "u0", "yo", "mensaje NUEVO que no debe perderse")
        # ...y unos JSON legacy que quedaron huérfanos en la base.
        (tmp_path / "perfil.json").write_text(
            json_mod.dumps({"nivel": "basico", "objetivo": "datos"}), "utf-8"
        )
        (tmp_path / "chat.json").write_text(
            json_mod.dumps({"u0": [{"rol": "yo", "texto": "VIEJO"}]}), "utf-8"
        )
        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        crear_app(configuracion, cliente=ClienteLLMFalso([]))
        mensajes = db_mod.historial_chat(ruta, "u0")
        assert [m["texto"] for m in mensajes] == ["mensaje NUEVO que no debe perderse"]
        assert not (tmp_path / "tutor.db").exists()

    def test_migracion_aparta_los_json_tras_migrar(self, tmp_path):
        import json as json_mod

        from tutor import db as db_mod

        (tmp_path / "perfil.json").write_text(
            json_mod.dumps({"nivel": "basico"}), "utf-8"
        )
        db_mod.migrar_json_legacy(tmp_path)
        assert not (tmp_path / "perfil.json").exists()
        assert (tmp_path / "perfil.migrado").exists()
        assert (tmp_path / "tutor.db").exists()
