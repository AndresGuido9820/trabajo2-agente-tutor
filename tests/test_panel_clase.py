"""Pruebas del panel lateral de la clase (plan/v2/HU-25)."""

from tutor.ensenanza.progreso import cargar_progreso, guardar_progreso

from .test_guion_v2 import PERFIL, agente_en_fin_de_objetivo
from .test_leccion import avanza


class TestPanelDeClase:
    def test_sin_guion_devuelve_vacio(self, tmp_path):
        from tutor.ensenanza.agente import Agente

        from .conftest import ClienteLLMFalso
        from .test_agente import temario_respuesta

        agente = Agente(ClienteLLMFalso([temario_respuesta()]), tmp_path, PERFIL)
        assert agente.panel_de_clase(0) == {
            "objetivos": [],
            "progreso_pct": 0,
            "evaluacion_lista": False,
        }

    def test_estados_en_vivo_y_progreso(self, tmp_path):
        agente, _ = agente_en_fin_de_objetivo(tmp_path, [avanza("¡bien!")])
        panel = agente.panel_de_clase(0)
        estados = [o["estado"] for o in panel["objetivos"]]
        assert estados == ["en_curso", "pendiente", "pendiente"]
        assert panel["evaluacion_lista"] is False
        assert 0 < panel["progreso_pct"] < 100  # paso 3 de 4 del objetivo 1

        agente.turno_estudio("listo")  # cierra el objetivo 0 → quiz
        agente.responder_quiz_intermedio(0, [0, 0])  # 1/2, cumplido
        panel = agente.panel_de_clase(0)
        assert panel["objetivos"][0]["estado"] == "cumplido"
        assert panel["objetivos"][0]["quiz"] == "1/2"
        assert panel["objetivos"][0]["repaso"] is False
        assert panel["objetivos"][1]["estado"] == "en_curso"

    def test_evaluacion_lista_con_todos_cumplidos(self, tmp_path):
        agente, _ = agente_en_fin_de_objetivo(tmp_path, [])
        for k in range(3):
            agente.progreso.cumplir_objetivo(0, k, aciertos=2, total=2)
        panel = agente.panel_de_clase(0)
        assert panel["evaluacion_lista"] is True
        assert panel["progreso_pct"] == 100
        assert all(o["estado"] == "cumplido" for o in panel["objetivos"])

    def test_sobrevive_reinicio_del_servidor(self, tmp_path):
        from tutor.ensenanza.agente import Agente

        from .conftest import ClienteLLMFalso

        agente, _ = agente_en_fin_de_objetivo(tmp_path, [avanza("¡bien!")])
        agente.turno_estudio("listo")
        agente.responder_quiz_intermedio(0, [0, 1])  # 2/2
        # "Reinicio": agente nuevo sobre el mismo directorio, sin sesión.
        nuevo = Agente(ClienteLLMFalso([]), tmp_path, PERFIL)
        panel = nuevo.panel_de_clase(0)
        assert panel["objetivos"][0]["estado"] == "cumplido"
        assert panel["objetivos"][0]["quiz"] == "2/2"
        assert panel["objetivos"][1]["estado"] == "en_curso"

    def test_resultados_intermedios_persisten(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        from tutor.ensenanza.progreso import Progreso

        p = Progreso()
        p.cumplir_objetivo(0, 1, aciertos=1, total=2, repaso=True)
        guardar_progreso(p, ruta)
        cargado = cargar_progreso(ruta)
        assert cargado.resultados_intermedios["0"]["1"] == {
            "aciertos": 1,
            "total": 2,
            "repaso": True,
        }
