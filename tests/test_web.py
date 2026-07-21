import json

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.errores import ErrorLLM
from tutor.web import crear_app

from .conftest import ClienteLLMFalso
from .test_agente import quiz_respuesta, temario_respuesta
from .test_leccion import guion_respuesta


@pytest.fixture
def crear_cliente_web(tmp_path):
    def _crear(respuestas_llm, con_perfil=True):
        configuracion = Configuracion(
            api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path
        )
        falso = ClienteLLMFalso(respuestas_llm)
        web = TestClient(crear_app(configuracion, cliente=falso))
        if con_perfil:
            r = web.post(
                "/api/perfil",
                json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
            )
            assert r.status_code == 200
        return web, falso

    return _crear


class TestPerfilYEstado:
    def test_estado_sin_perfil(self, crear_cliente_web):
        web, _ = crear_cliente_web([], con_perfil=False)
        assert web.get("/api/estado").json() == {"perfil": False}

    def test_perfil_invalido_da_400(self, crear_cliente_web):
        web, _ = crear_cliente_web([], con_perfil=False)
        r = web.post("/api/perfil", json={"nivel": "experto", "objetivo": "datos"})
        assert r.status_code == 400

    def test_estado_con_perfil_genera_temario(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta()])
        datos = web.get("/api/estado").json()
        assert datos["perfil"] is True
        assert datos["lenguaje"] == "python"
        assert datos["puntos"] == 0
        assert datos["racha"] == 1  # la sesión de hoy cuenta al abrir
        assert len(datos["unidades"]) == 5
        assert datos["unidades"][0]["estado"] == "pendiente"
        assert all(u["estado"] == "bloqueada" for u in datos["unidades"][1:])

    def test_accion_sin_perfil_da_409(self, crear_cliente_web):
        web, _ = crear_cliente_web([], con_perfil=False)
        assert web.post("/api/leccion/0/iniciar").status_code == 409


class TestLeccionWeb:
    def test_flujo_leccion_conversacional_por_api(self, crear_cliente_web):
        from .test_leccion import avanza

        web, _ = crear_cliente_web(
            [temario_respuesta(), guion_respuesta(), "hola", avanza("paso 2")]
        )
        r = web.post("/api/leccion/0/iniciar").json()
        assert r["texto"] == "hola"
        assert r["paso"] == 1 and r["total"] == 5 and not r["terminada"]
        assert len(r["objetivos"]) == 2

        r = web.post("/api/leccion/0/turno", json={"mensaje": "imprime 4"}).json()
        assert r["texto"] == "paso 2" and r["paso"] == 2

    def test_turno_sin_iniciar_da_409(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta()])
        web.get("/api/estado")
        assert (
            web.post("/api/leccion/0/turno", json={"mensaje": "x"}).status_code == 409
        )

    def test_unidad_inexistente_da_404(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta()])
        assert web.post("/api/leccion/99/iniciar").status_code == 404

    def test_error_llm_devuelve_502(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta(), ErrorLLM("se cayó")])
        web.get("/api/estado")
        r = web.post("/api/leccion/0/iniciar")
        assert r.status_code == 502
        assert "se cayó" in r.json()["detail"]


class TestGuiaWeb:
    def test_guia_no_expone_correctas_pistas_ni_explicaciones(self, crear_cliente_web):
        from .test_guia import guia_respuesta

        web, _ = crear_cliente_web([temario_respuesta(), guia_respuesta()])
        r = web.post("/api/guia/0")
        assert r.status_code == 200
        cuerpo = r.text
        assert "correcta" not in cuerpo
        assert "pista" not in cuerpo
        assert "explicacion" not in cuerpo
        assert len(r.json()["secciones"]) == 3

    def test_checkpoint_flujo_pista_y_puntos(self, crear_cliente_web):
        from .test_guia import guia_respuesta

        web, _ = crear_cliente_web([temario_respuesta(), guia_respuesta()])
        web.post("/api/guia/0")
        # Falla el intento 1: pista, sin revelar
        r = web.post(
            "/api/guia/0/checkpoint", json={"seccion": 0, "opcion": 0, "intento": 1}
        ).json()
        assert r["correcto"] is False and r["revelada"] is False
        assert "pista" in r["texto"]
        # Acierta el intento 2: +5
        r = web.post(
            "/api/guia/0/checkpoint", json={"seccion": 0, "opcion": 1, "intento": 2}
        ).json()
        assert r["correcto"] is True and r["puntos"] == 5
        assert r["puntos_totales"] == 5

    def test_guia_de_unidad_bloqueada_da_403(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta()])
        web.get("/api/estado")
        assert web.post("/api/guia/1").status_code == 403

    def test_conversatorio_responde(self, crear_cliente_web):
        from .test_guia import guia_respuesta

        web, _ = crear_cliente_web(
            [temario_respuesta(), guia_respuesta(), "¿qué crees que hace x = 5?"]
        )
        web.post("/api/guia/0")
        r = web.post("/api/conversatorio/0", json={"mensaje": ""})
        assert r.status_code == 200
        assert "x = 5" in r.json()["texto"]


class TestQuizWeb:
    def test_quiz_no_expone_respuesta_correcta(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta(), "# lección", quiz_respuesta()])
        r = web.post("/api/quiz/0")
        assert r.status_code == 200
        texto = json.dumps(r.json())
        assert "correcta" not in texto
        assert "explicacion" not in texto

    def test_calificar_registra_progreso(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta(), "# lección", quiz_respuesta()])
        web.post("/api/quiz/0")
        r = web.post("/api/quiz/0/calificar", json={"respuestas": [0, 0, 1, 1]}).json()
        assert r["nota"] == 50
        assert len(r["detalle"]) == 4

        progreso = web.get("/api/progreso").json()
        assert progreso["filas"][0]["mejor_nota"] == 50
        assert progreso["filas"][0]["intentos"] == 1

    def test_calificar_sin_quiz_activo_da_409(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta()])
        web.get("/api/estado")
        r = web.post("/api/quiz/0/calificar", json={"respuestas": [0, 0, 0, 0]})
        assert r.status_code == 409

    def test_calificar_indica_aprobado_y_desbloquea(self, crear_cliente_web):
        web, _ = crear_cliente_web([temario_respuesta(), "# lección", quiz_respuesta()])
        web.post("/api/quiz/0")
        r = web.post("/api/quiz/0/calificar", json={"respuestas": [0, 0, 0, 0]}).json()
        assert r["aprobado"] is True and r["nota"] == 100
        assert r["puntos_totales"] > 0
        estado = web.get("/api/estado").json()
        assert estado["unidades"][0]["estado"] == "aprobada"
        assert estado["unidades"][1]["estado"] == "pendiente"

    def test_pagina_principal_sirve_html(self, crear_cliente_web):
        web, _ = crear_cliente_web([], con_perfil=False)
        r = web.get("/")
        assert r.status_code == 200
        assert "Profe Bit" in r.text
