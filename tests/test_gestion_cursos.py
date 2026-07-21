from .test_agente import temario_respuesta
from .test_chat_total import PERFIL_OK, turno_creacion, web_con


def crear_curso(web, mensaje="curso de datos ya"):
    web.post("/api/creacion", json={"mensaje": mensaje})


class TestGestionCursos:
    def test_renombrar_persiste_y_lista(self, tmp_path):
        web, _ = web_con(
            tmp_path, [turno_creacion("ok", True, PERFIL_OK), temario_respuesta()]
        )
        crear_curso(web)
        r = web.patch("/api/cursos/1", json={"nombre": "Ventas con Python"})
        assert r.status_code == 200
        cursos = web.get("/api/cursos").json()["cursos"]
        assert cursos[0]["nombre"] == "Ventas con Python"

    def test_renombrar_vacio_da_400_e_inexistente_404(self, tmp_path):
        web, _ = web_con(tmp_path, [])
        web.post("/api/cursos")
        assert web.patch("/api/cursos/1", json={"nombre": "  "}).status_code == 400
        assert web.patch("/api/cursos/9", json={"nombre": "x"}).status_code == 404
        assert web.request("DELETE", "/api/cursos/9").status_code == 404

    def test_archivar_marca_y_lista(self, tmp_path):
        web, _ = web_con(
            tmp_path, [turno_creacion("ok", True, PERFIL_OK), temario_respuesta()]
        )
        crear_curso(web)
        web.patch("/api/cursos/1", json={"archivado": True})
        assert web.get("/api/cursos").json()["cursos"][0]["archivado"] is True
        web.patch("/api/cursos/1", json={"archivado": False})
        assert web.get("/api/cursos").json()["cursos"][0]["archivado"] is False

    def test_borrar_mueve_a_papelera_y_reasigna_activo(self, tmp_path):
        web, _ = web_con(
            tmp_path, [turno_creacion("ok", True, PERFIL_OK), temario_respuesta()]
        )
        crear_curso(web)  # curso 1 (activo)
        web.post("/api/cursos")  # curso 2 (queda activo)
        r = web.request("DELETE", "/api/cursos/2")
        assert r.status_code == 200
        # La papelera contiene el curso movido
        papelera = list((tmp_path / "cursos" / ".papelera").glob("2-*"))
        assert len(papelera) == 1 and (papelera[0] / "tutor.db").exists()
        # El activo volvió al curso 1 y el listado ya no muestra el 2
        cursos = web.get("/api/cursos").json()["cursos"]
        assert [c["id"] for c in cursos] == [1]
        assert web.get("/api/estado").json()["perfil"] is True

    def test_borrar_unico_curso_deja_sin_cursos(self, tmp_path):
        web, _ = web_con(tmp_path, [])
        web.post("/api/cursos")
        web.request("DELETE", "/api/cursos/1")
        assert web.get("/api/cursos").json() == {"cursos": []}
        assert web.get("/api/estado").json() == {"perfil": False}
