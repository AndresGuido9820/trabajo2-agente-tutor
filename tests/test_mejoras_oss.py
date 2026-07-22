from datetime import date, timedelta

from tutor.ensenanza.agente import Agente
from tutor.ensenanza.progreso import Progreso, cargar_progreso, guardar_progreso

from .conftest import ClienteLLMFalso
from .test_agente import quiz_respuesta, temario_respuesta

HOY = date.today().isoformat()
AYER = (date.today() - timedelta(days=1)).isoformat()
ANTIER = (date.today() - timedelta(days=2)).isoformat()


class TestRacha:
    def test_primera_sesion_arranca_en_1(self):
        p = Progreso()
        p.registrar_sesion(HOY)
        assert p.racha == 1 and p.ultima_sesion == HOY

    def test_mismo_dia_no_suma(self):
        p = Progreso()
        p.registrar_sesion(HOY)
        p.registrar_sesion(HOY)
        assert p.racha == 1

    def test_dia_consecutivo_suma(self):
        p = Progreso(racha=3, ultima_sesion=AYER)
        p.registrar_sesion(HOY)
        assert p.racha == 4

    def test_salto_de_dias_reinicia(self):
        p = Progreso(racha=9, ultima_sesion=ANTIER)
        p.registrar_sesion(HOY)
        assert p.racha == 1

    def test_racha_persiste(self, tmp_path):
        ruta = tmp_path / "progreso.json"
        p = Progreso(racha=5, ultima_sesion=HOY)
        guardar_progreso(p, ruta)
        assert cargar_progreso(ruta).racha == 5

    def test_agente_registra_sesion_al_abrir(self, tmp_path, perfil):
        agente = Agente(ClienteLLMFalso([temario_respuesta()]), tmp_path, perfil)
        assert agente.progreso.racha == 1
        assert agente.progreso.ultima_sesion == HOY
        # y quedó persistida
        assert cargar_progreso(tmp_path / "tutor.db").racha == 1


class TestVariantesDeQuiz:
    def test_reintento_pide_variantes_de_preguntas_previas(self, tmp_path, perfil):
        falso = ClienteLLMFalso(
            [temario_respuesta(), "# lección", quiz_respuesta(), quiz_respuesta()]
        )
        agente = Agente(falso, tmp_path, perfil)
        primer_quiz = agente.quiz_de_unidad(0)
        _, primer_prompt = falso.llamadas[-1]
        assert "REINTENTO" not in primer_prompt

        agente.quiz_de_unidad(0)  # reintento
        _, prompt = falso.llamadas[-1]
        assert "REINTENTO" in prompt and "VARIANTES" in prompt
        assert primer_quiz.preguntas[0].enunciado in prompt


class TestTheoryOfMind:
    def test_conversatorio_incluye_desempeno_e_inferencia(self, tmp_path, perfil):
        falso = ClienteLLMFalso(
            [temario_respuesta(), "# lección", quiz_respuesta(), "abro yo"]
        )
        agente = Agente(falso, tmp_path, perfil)
        quiz = agente.quiz_de_unidad(0)
        agente.calificar_quiz(quiz, [1, 1, 1, 1, 1, 1])  # reprueba con 0

        agente.conversatorio(0, "")
        system, _ = falso.llamadas[-1]
        assert "Intento 1: nota 0/100" in system  # historial de desempeño
        assert "PASO PREVIO" in system  # inferencia del malentendido
        assert "variables" in system  # concepto fallado presente
