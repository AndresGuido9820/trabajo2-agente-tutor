"""Pruebas del examen diagnóstico inicial (HU-41)."""

from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.errores import ErrorLLM
from tutor.perfil import cargar_perfil
from tutor.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import quiz_respuesta, temario_respuesta
from .test_chat_total import PERFIL_OK, turno_creacion


def web_con(tmp_path, respuestas):
    configuracion = Configuracion(
        api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
    )
    falso = ClienteLLMFalso(respuestas)
    return TestClient(crear_app(configuracion, cliente=falso)), falso


class TestDiagnostico:
    def test_resultado_entra_al_perfil_y_al_temario(self, tmp_path):
        web, falso = web_con(
            tmp_path,
            [
                turno_creacion("dale", True, PERFIL_OK),
                quiz_respuesta(4),
                temario_respuesta(),
            ],
        )
        r = web.post("/api/creacion", json={"mensaje": "curso de datos, ya"}).json()
        assert r["listo"] and len(r["diagnostico"]) == 4
        # Falla las dos últimas → brechas anotadas.
        web.post("/api/diagnostico/calificar", json={"respuestas": [0, 0, 1, 1]})
        perfil = cargar_perfil(tmp_path / "cursos" / "1" / "tutor.db")
        assert "Diagnóstico inicial 2/4" in perfil.experiencia
        # El system del temario recibió el diagnóstico (personalización real).
        assert "Diagnóstico inicial 2/4" in falso.llamadas[-1][0]

    def test_calificar_sin_pendiente_da_409_y_respuestas_malas_400(self, tmp_path):
        web, _ = web_con(
            tmp_path,
            [
                turno_creacion("dale", True, PERFIL_OK),
                quiz_respuesta(4),
                temario_respuesta(),
            ],
        )
        assert (
            web.post("/api/diagnostico/calificar", json={"respuestas": [0]}).status_code
            == 409
        )
        web.post("/api/creacion", json={"mensaje": "curso ya"})
        assert (
            web.post("/api/diagnostico/calificar", json={"respuestas": [0]}).status_code
            == 400
        )

    def test_fallo_del_diagnostico_degrada_a_curso_directo(self, tmp_path):
        web, _ = web_con(
            tmp_path,
            [
                turno_creacion("dale", True, PERFIL_OK),
                ErrorLLM("sin diagnóstico"),  # generar el examen falla
                temario_respuesta(),
            ],
        )
        r = web.post("/api/creacion", json={"mensaje": "curso ya"}).json()
        assert r["listo"] is True and r["diagnostico"] is None
        assert web.get("/api/estado").json()["perfil"] is True
