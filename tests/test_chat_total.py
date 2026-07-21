import json

from fastapi.testclient import TestClient

from tutor.agente import Agente
from tutor.config import Configuracion
from tutor.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta
from .test_leccion import guion_respuesta


def turno_creacion(mensaje, listo=False, perfil=None):
    return json.dumps({"mensaje": mensaje, "listo": listo, "perfil": perfil})


PERFIL_OK = {
    "nivel": "basico",
    "objetivo": "datos",
    "objetivo_detalle": "",
    "experiencia": "Excel",
    "lenguaje": "python",
}


def web_con(tmp_path, respuestas):
    configuracion = Configuracion(
        api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
    )
    falso = ClienteLLMFalso(respuestas)
    return TestClient(crear_app(configuracion, cliente=falso)), falso


class TestCreacionConversacional:
    def test_conversa_pregunta_y_al_confirmar_crea_el_curso(self, tmp_path):
        web, falso = web_con(
            tmp_path,
            [
                turno_creacion("Bueno, quieres datos. ¿Cuál es tu nivel de Python?"),
                turno_creacion("Propongo estas unidades… ¿arrancamos?"),
                turno_creacion("¡Dale! Creando tu curso…", True, PERFIL_OK),
                temario_respuesta(),
            ],
        )
        r1 = web.post(
            "/api/creacion", json={"mensaje": "hazme un curso de datos"}
        ).json()
        assert r1["listo"] is False and "nivel de Python" in r1["mensaje"]

        r2 = web.post("/api/creacion", json={"mensaje": "básico, sé Excel"}).json()
        assert r2["listo"] is False
        _, prompt = falso.llamadas[-1]
        assert "hazme un curso de datos" in prompt  # historial acumulado

        r3 = web.post("/api/creacion", json={"mensaje": "ya, dale"}).json()
        assert r3["listo"] is True

        # Quedó el curso, el plan .md y el estado completo
        estado = web.get("/api/estado").json()
        assert estado["perfil"] is True
        assert estado["unidades"][0]["objetivo"] == "objetivo 0"
        assert estado["unidades"][0]["completada"] is False
        plan = web.get("/api/plan").json()["md"]
        assert "# Tu curso de python" in plan and "Unidad 0" in plan
        assert (tmp_path / "curso.md").exists()

    def test_con_curso_existente_da_409(self, tmp_path):
        web, _ = web_con(
            tmp_path,
            [turno_creacion("ok", True, PERFIL_OK), temario_respuesta()],
        )
        web.post("/api/creacion", json={"mensaje": "curso de datos ya dale"})
        r = web.post("/api/creacion", json={"mensaje": "otro curso"})
        assert r.status_code == 409


class TestEstudioEnChat:
    def _agente(self, tmp_path, perfil, respuestas):
        falso = ClienteLLMFalso([temario_respuesta(), *respuestas])
        return Agente(falso, tmp_path, perfil), falso

    def test_flujo_estudio_completa_y_permite_repasar(self, tmp_path, perfil):
        from .test_leccion import avanza

        turnos = [avanza(f"t{i}") for i in range(1, 5)]
        agente, _ = self._agente(
            tmp_path,
            perfil,
            [guion_respuesta(), "t0", *turnos, guion_respuesta(), "de nuevo"],
        )
        r = agente.turno_estudio(None)  # arranca la unidad 0
        assert r["unidad"] == 0 and r["paso"] == 1 and not r["terminada"]
        for _ in range(3):
            r = agente.turno_estudio("respondo")
            assert not r["terminada"]
        r = agente.turno_estudio("última")
        assert r["terminada"] is True
        assert 0 in agente.progreso.completadas

        # Persistencia de completadas
        agente2 = Agente(ClienteLLMFalso([]), tmp_path, perfil)
        assert 0 in agente2.progreso.completadas

        # Repasar: reinicia la lección de la unidad 0 en el chat
        r = agente.turno_estudio(None, unidad=0)
        assert r["paso"] == 1 and not r["terminada"]

    def test_mensaje_con_unidad_continua_sin_reiniciar(self, tmp_path, perfil):
        from .test_leccion import avanza

        agente, _ = self._agente(
            tmp_path, perfil, [guion_respuesta(), "t0", avanza("t1")]
        )
        agente.turno_estudio(None, unidad=0)  # entra a la clase
        r = agente.turno_estudio("respondo la predicción", unidad=0)
        assert r["paso"] == 2  # continuó, no reinició

    def test_historial_persiste_y_se_sirve(self, tmp_path):
        web, _ = web_con(
            tmp_path,
            [
                turno_creacion("¿tu nivel?"),
                turno_creacion("ok", True, PERFIL_OK),
                temario_respuesta(),
            ],
        )
        web.post("/api/creacion", json={"mensaje": "curso de datos"})
        web.post("/api/creacion", json={"mensaje": "ya dale"})
        h = web.get("/api/historial/creacion").json()["mensajes"]
        assert h[0] == {"rol": "yo", "texto": "curso de datos"}
        assert h[1] == {"rol": "tutor", "texto": "¿tu nivel?"}
        assert len(h) == 4
        assert (tmp_path / "tutor.db").exists()
        # Cada clase es una conversación aparte
        assert web.get("/api/historial/u0").json()["mensajes"] == []

    def test_estado_incluye_conceptos_para_el_temario(self, tmp_path):
        web, _ = web_con(
            tmp_path, [turno_creacion("ok", True, PERFIL_OK), temario_respuesta()]
        )
        web.post("/api/creacion", json={"mensaje": "curso de datos ya"})
        u0 = web.get("/api/estado").json()["unidades"][0]
        assert u0["conceptos"] == ["variables", "tipos"]

    def test_endpoint_estudio(self, tmp_path):
        web, _ = web_con(
            tmp_path,
            [
                turno_creacion("ok", True, PERFIL_OK),
                temario_respuesta(),
                guion_respuesta(),
                "hola, ¡arranquemos!",
            ],
        )
        web.post("/api/creacion", json={"mensaje": "curso de datos ya"})
        r = web.post("/api/estudio", json={}).json()
        assert r["texto"] == "hola, ¡arranquemos!" and r["unidad"] == 0
