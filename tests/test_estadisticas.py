"""Pruebas de la vista Mi progreso (plan/v2/HU-31)."""

import pytest
from fastapi.testclient import TestClient

from tutor.config import Configuracion
from tutor.ensenanza.progreso import (
    Progreso,
    Resultado,
    cargar_progreso,
    guardar_progreso,
)
from tutor.interfaces.web import crear_app
from tutor.persistencia import db

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


class TestMejorRacha:
    def test_se_actualiza_y_no_baja(self):
        p = Progreso()
        p.registrar_sesion("2026-07-01")
        p.registrar_sesion("2026-07-02")
        p.registrar_sesion("2026-07-03")
        assert p.racha == 3 and p.mejor_racha == 3
        p.registrar_sesion("2026-07-10")  # se rompe la racha
        assert p.racha == 1 and p.mejor_racha == 3

    def test_persiste(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        p = Progreso()
        p.registrar_sesion("2026-07-01")
        p.registrar_sesion("2026-07-02")
        guardar_progreso(p, ruta)
        assert cargar_progreso(ruta).mejor_racha == 2

    def test_retrocompatible_sin_campo(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        db.guardar_documento(
            ruta,
            "progreso",
            {"version": 1, "racha": 4, "vistas": {}, "resultados": []},
        )
        cargado = cargar_progreso(ruta)
        assert cargado.mejor_racha == 4  # hereda la racha vigente


class TestActividadChat:
    def test_agrupa_por_dia(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        assert db.actividad_chat(ruta) == {}
        for _ in range(3):
            db.anotar_chat(ruta, "u0", "yo", "hola")
        db.anotar_chat(ruta, "creacion", "tutor", "hola")
        actividad = db.actividad_chat(ruta)
        assert len(actividad) == 1
        assert next(iter(actividad.values())) == 4


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

    def reiniciar():
        """Nuevo servidor sobre los mismos datos (recarga desde disco)."""
        return TestClient(crear_app(configuracion, cliente=ClienteLLMFalso([])))

    return web, tmp_path / "cursos" / "1" / "tutor.db", reiniciar


class TestEndpointEstadisticas:
    def test_sin_datos(self, web_con_curso):
        web, _, _ = web_con_curso
        datos = web.get("/api/estadisticas").json()
        assert datos["actividad"] == []
        assert datos["notas"] == {}
        assert datos["conceptos"] == {"dominados": [], "repasar": []}
        assert datos["totales"]["aprobadas"] == 0
        assert datos["totales"]["total"] == 5
        assert datos["totales"]["racha"] == 1

    def test_agrega_notas_conceptos_y_actividad(self, web_con_curso):
        _web, ruta, reiniciar = web_con_curso
        progreso = cargar_progreso(ruta)
        progreso.registrar(
            Resultado(0, 40, ["bucles", "Bucles"], "2026-07-20T10:00:00+00:00")
        )
        progreso.registrar(Resultado(0, 85, [], "2026-07-21T10:00:00+00:00"))
        progreso.sumar_puntos(30)
        guardar_progreso(progreso, ruta)
        db.anotar_chat(ruta, "u0", "yo", "hola")
        db.anotar_chat(ruta, "u0", "tutor", "¡hola!")

        datos = reiniciar().get("/api/estadisticas").json()
        assert datos["notas"] == {"0": [40, 85]}
        # "bucles"/"Bucles" se agrupan por minúsculas y quedan para repasar.
        repasar = {f["c"]: f for f in datos["conceptos"]["repasar"]}
        assert "bucles" in repasar and repasar["bucles"]["clase"] == 0
        # Los conceptos de la unidad no fallados en el 2º intento suman ok.
        assert (
            any(f["ok"] >= 1 for f in datos["conceptos"]["repasar"])
            or datos["conceptos"]["dominados"]
        )
        # Actividad: un día con 2 mensajes; puntos el día de la aprobación.
        assert len(datos["actividad"]) == 1
        assert datos["actividad"][0]["mensajes"] == 2
        assert datos["totales"]["aprobadas"] == 1
        assert datos["totales"]["puntos"] == 30
        assert datos["totales"]["minutos_estimados"] == 2 * 40 // 60

    def test_dominados_requieren_dos_aciertos_sin_fallos(self, web_con_curso):
        _web, ruta, reiniciar = web_con_curso
        progreso = cargar_progreso(ruta)
        progreso.registrar(Resultado(0, 85, [], "2026-07-20T10:00:00+00:00"))
        progreso.registrar(Resultado(0, 90, [], "2026-07-21T10:00:00+00:00"))
        guardar_progreso(progreso, ruta)

        datos = reiniciar().get("/api/estadisticas").json()
        dominados = {f["c"] for f in datos["conceptos"]["dominados"]}
        assert dominados  # los conceptos de la unidad 0, acertados 2 veces
        assert all(
            f["mal"] == 0 and f["ok"] >= 2 for f in datos["conceptos"]["dominados"]
        )
        assert datos["conceptos"]["repasar"] == []
        # Aprobar dos veces la misma unidad solo cuenta puntos-día una vez.
        assert sum(d["puntos"] for d in datos["actividad"]) == 0  # sin chat ese día
