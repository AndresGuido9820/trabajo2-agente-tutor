"""Pruebas del modelo por tarea y registro de uso (plan/v2/HU-39)."""

import pytest
from fastapi.testclient import TestClient

from tutor import db
from tutor.agente import Agente
from tutor.config import Configuracion, cargar_configuracion
from tutor.llm import ClienteOpenAI
from tutor.models import Nivel, Objetivo, PerfilEstudiante
from tutor.web import crear_app

from .conftest import ClienteLLMFalso, SDKFalso
from .test_agente import temario_respuesta
from .test_leccion import avanza, guion_respuesta

PERFIL = PerfilEstudiante(
    nivel=Nivel.BASICO,
    experiencia="",
    objetivo=Objetivo.DATOS,
    objetivo_detalle="",
    lenguaje="python",
)


class TestCarriles:
    def test_configuracion_default_un_solo_modelo(self):
        configuracion = cargar_configuracion({"OPENAI_API_KEY": "sk-x"})
        assert configuracion.modelo_chat == ""  # vacío = mismo modelo

    def test_cliente_usa_modelo_chat_en_carril_chat(self, tmp_path):
        configuracion = Configuracion(
            api_key="sk-x",
            modelo="potentote",
            dir_datos=tmp_path,
            modelo_chat="rapidito",
        )
        sdk = SDKFalso(["hola", "hola"])
        registros = []
        cliente = ClienteOpenAI(
            configuracion,
            cliente=sdk,
            dormir=lambda _: None,
            registrar=lambda **campos: registros.append(campos),
        )
        cliente.generar("s", "p")
        cliente.generar("s", "p", carril="chat")
        assert sdk.modelos == ["potentote", "rapidito"]
        assert [r["carril"] for r in registros] == ["potente", "chat"]

    def test_carril_chat_cae_al_potente_sin_modelo_chat(self, tmp_path):
        configuracion = Configuracion(
            api_key="sk-x", modelo="potentote", dir_datos=tmp_path
        )
        sdk = SDKFalso(["hola"])
        cliente = ClienteOpenAI(
            configuracion,
            cliente=sdk,
            dormir=lambda _: None,
            registrar=lambda **campos: None,
        )
        cliente.generar("s", "p", carril="chat")
        assert sdk.modelos == ["potentote"]

    def test_operaciones_usan_su_carril(self, tmp_path):
        falso = ClienteLLMFalso(
            [temario_respuesta(), guion_respuesta(), "apertura", avanza("sigue")]
        )
        agente = Agente(falso, tmp_path, PERFIL)
        agente.iniciar_leccion(0)  # temario (potente) + guion (potente) + turno
        agente.turno_leccion(0, "listo")  # avance (chat)
        # temario y guion en carril potente; los turnos conversados en chat.
        assert falso.carriles[:2] == ["potente", "potente"]
        assert falso.carriles[2:] == ["chat", "chat"]


class TestRegistroDeUso:
    def test_persiste_y_agrega(self, tmp_path):
        ruta = tmp_path / "uso.db"
        db.anotar_uso(ruta, "potente", "gpt-5-mini", 1000, 200, 1500)
        db.anotar_uso(ruta, "potente", "gpt-5-mini", 2000, 300, 900)
        db.anotar_uso(ruta, "chat", "gpt-5-nano", None, None, 400)
        filas = db.resumen_uso(ruta)
        assert len(filas) == 2
        potente = next(f for f in filas if f["carril"] == "potente")
        assert potente["llamadas"] == 2
        assert potente["tokens_prompt"] == 3000
        assert potente["tokens_salida"] == 500
        chat = next(f for f in filas if f["carril"] == "chat")
        assert chat["tokens_prompt"] == 0  # tokens None → 0 en el agregado

    def test_sin_bd_devuelve_vacio(self, tmp_path):
        assert db.resumen_uso(tmp_path / "uso.db") == []

    def test_registro_por_defecto_escribe_en_dir_datos(self, tmp_path):
        configuracion = Configuracion(api_key="sk-x", modelo="m", dir_datos=tmp_path)
        cliente = ClienteOpenAI(
            configuracion, cliente=SDKFalso(["hola"]), dormir=lambda _: None
        )
        cliente.generar("s", "p")
        assert (tmp_path / "uso.db").exists()
        assert db.resumen_uso(tmp_path / "uso.db")[0]["llamadas"] == 1


class TestEndpointUso:
    def test_costo_estimado_con_precios(self, tmp_path):
        configuracion = Configuracion(
            api_key="sk-x", modelo="gpt-prueba", dir_datos=tmp_path
        )
        db.anotar_uso(
            tmp_path / "uso.db", "potente", "gpt-5-mini", 1_000_000, 1_000_000, 100
        )
        db.anotar_uso(tmp_path / "uso.db", "chat", "modelo-sin-precio", 10, 10, 50)
        web = TestClient(crear_app(configuracion, cliente=ClienteLLMFalso([])))
        filas = web.get("/api/uso").json()["uso"]
        con_precio = next(f for f in filas if f["modelo"] == "gpt-5-mini")
        assert con_precio["costo_usd"] == pytest.approx(0.25 + 2.0)
        sin_precio = next(f for f in filas if f["modelo"] == "modelo-sin-precio")
        assert sin_precio["costo_usd"] is None
