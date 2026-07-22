"""Pruebas del repaso espaciado 1-3-7 (plan/v2/HU-32)."""

import json

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.ensenanza.progreso import Progreso, cargar_progreso, guardar_progreso
from tutor.interfaces.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


class TestColaRepaso:
    def test_fallo_entra_a_cola_1_dia(self):
        p = Progreso()
        p.programar_repaso("Bucles", 2, "2026-07-21")
        [item] = p.cola_repaso
        assert item == {
            "concepto": "bucles",  # normalizado a minúsculas
            "clase": 2,
            "vence": "2026-07-22",
            "nivel": 0,
        }
        # Mismo (concepto, clase) no duplica; distinta clase sí.
        p.programar_repaso("bucles", 2, "2026-07-21")
        assert len(p.cola_repaso) == 1
        p.programar_repaso("bucles", 3, "2026-07-21")
        assert len(p.cola_repaso) == 2

    def test_acierto_avanza_1_3_7_y_sale(self):
        p = Progreso()
        p.programar_repaso("bucles", 0, "2026-07-20")
        p.resolver_repaso("bucles", 0, acierto=True, hoy="2026-07-21")
        assert p.cola_repaso[0]["nivel"] == 1
        assert p.cola_repaso[0]["vence"] == "2026-07-24"  # +3 días
        p.resolver_repaso("bucles", 0, acierto=True, hoy="2026-07-24")
        assert p.cola_repaso[0]["nivel"] == 2
        assert p.cola_repaso[0]["vence"] == "2026-07-31"  # +7 días
        p.resolver_repaso("bucles", 0, acierto=True, hoy="2026-07-31")
        assert p.cola_repaso == []  # dominado

    def test_fallo_en_repaso_reinicia_intervalo(self):
        p = Progreso()
        p.programar_repaso("bucles", 0, "2026-07-18")
        p.resolver_repaso("bucles", 0, acierto=True, hoy="2026-07-19")
        p.resolver_repaso("bucles", 0, acierto=False, hoy="2026-07-22")
        assert p.cola_repaso[0]["nivel"] == 0
        assert p.cola_repaso[0]["vence"] == "2026-07-23"

    def test_vencidos_ordenados_y_purga(self):
        p = Progreso()
        p.programar_repaso("b", 1, "2026-07-15")
        p.programar_repaso("a", 0, "2026-07-10")
        p.programar_repaso("c", 9, "2026-07-15")
        vencidos = p.repasos_vencidos("2026-07-21")
        assert [i["concepto"] for i in vencidos] == ["a", "b", "c"]
        assert p.repasos_vencidos("2026-07-10") == []
        p.purgar_repasos(total_clases=5)  # la clase 9 ya no existe
        assert {i["concepto"] for i in p.cola_repaso} == {"a", "b"}
        assert p.proximo_repaso() == "2026-07-11"

    def test_persiste(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        p = Progreso()
        p.programar_repaso("bucles", 0, "2026-07-21")
        guardar_progreso(p, ruta)
        assert cargar_progreso(ruta).cola_repaso == p.cola_repaso


def quiz_repaso_respuesta():
    """Quiz falso de repaso: 2 preguntas sobre 'bucles' y 1 sobre 'listas'."""
    preguntas = [
        {
            "enunciado": f"pregunta {i}",
            "opciones": ["a", "b", "c", "d"],
            "correcta": 0,
            "explicacion": "porque sí",
            "concepto": concepto,
        }
        for i, concepto in enumerate(["bucles", "bucles", "listas", "listas"])
    ]
    return json.dumps({"preguntas": preguntas})


@pytest.fixture
def web_con_cola(tmp_path):
    configuracion = Configuracion(
        api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
    )
    falso = ClienteLLMFalso([temario_respuesta(), quiz_repaso_respuesta()])
    web = TestClient(crear_app(configuracion, cliente=falso))
    r = web.post(
        "/api/perfil",
        json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
    )
    assert r.status_code == 200
    web.get("/api/estado")
    ruta = tmp_path / "cursos" / "1" / "tutor.db"
    progreso = cargar_progreso(ruta)
    progreso.programar_repaso("bucles", 0, "2020-01-01")  # vencidos hace rato
    progreso.programar_repaso("listas", 1, "2020-01-01")
    guardar_progreso(progreso, ruta)
    web.post("/api/cursos/1/activar")  # el agente cachea: no recarga solo
    return web, ruta, configuracion


class TestEndpointsRepaso:
    def test_estado_y_flujo_completo(self, web_con_cola):
        web, ruta, configuracion = web_con_cola
        # El agente en memoria no vio la cola escrita a disco: reiniciamos.
        web = TestClient(
            crear_app(
                configuracion,
                cliente=ClienteLLMFalso([quiz_repaso_respuesta()]),
            )
        )
        assert web.get("/api/repaso").json()["pendientes"] == 2

        quiz = web.post("/api/repaso/iniciar").json()
        assert len(quiz["preguntas"]) == 4
        assert "correcta" not in quiz["preguntas"][0]  # nunca al navegador

        # bucles: 2/2 bien (avanza); listas: 1 mal (reinicia a mañana).
        r = web.post("/api/repaso/calificar", json={"respuestas": [0, 0, 0, 1]}).json()
        assert r["aciertos"] == 3
        cola = {i["concepto"]: i for i in r["cola"]}
        assert cola["bucles"]["nivel"] == 1
        assert cola["listas"]["nivel"] == 0
        # Puntos: +3 por acierto.
        progreso = cargar_progreso(ruta)
        assert progreso.puntos == 9

    def test_iniciar_sin_vencidos_da_409(self, tmp_path):
        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        web = TestClient(
            crear_app(configuracion, cliente=ClienteLLMFalso([temario_respuesta()]))
        )
        web.post(
            "/api/perfil",
            json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
        )
        web.get("/api/estado")
        assert web.get("/api/repaso").json() == {"pendientes": 0, "proximo": None}
        assert web.post("/api/repaso/iniciar").status_code == 409
        assert (
            web.post("/api/repaso/calificar", json={"respuestas": []}).status_code
            == 409
        )
