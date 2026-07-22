"""Pruebas de evaluaciones robustas: niveles, ponderación y banco (HU-26)."""

import json

import pytest

from tutor import db
from tutor.agente import Agente
from tutor.evaluacion import Pregunta, Quiz, calificar, resumenes, validar_quiz
from tutor.models import Nivel, Objetivo, PerfilEstudiante

from .conftest import ClienteLLMFalso
from .test_agente import quiz_respuesta, temario_respuesta

PERFIL = PerfilEstudiante(
    nivel=Nivel.BASICO,
    experiencia="",
    objetivo=Objetivo.DATOS,
    objetivo_detalle="",
    lenguaje="python",
)


def pregunta(concepto="variables", nivel="comprender", enunciado="p"):
    return Pregunta(
        enunciado=enunciado,
        opciones=["a", "b", "c", "d"],
        correcta=0,
        explicacion="porque sí",
        concepto=concepto,
        nivel=nivel,
    )


class TestNotaPonderada:
    def test_ejemplo_de_la_spec(self):
        # 6 preguntas: 1 recordar + 3 comprender + 2 aplicar.
        preguntas = (
            [pregunta(nivel="recordar")]
            + [pregunta(nivel="comprender") for _ in range(3)]
            + [pregunta(nivel="aplicar") for _ in range(2)]
        )
        quiz = Quiz(unidad=0, preguntas=preguntas)
        # Acierta recordar + comprender, falla las 2 de aplicar.
        resultado, _ = calificar(quiz, [0, 0, 0, 0, 1, 1])
        assert resultado.nota == 54  # 3.5 / 6.5: saber definiciones no basta

    def test_todo_correcto_es_100_y_empate_en_70_aprueba(self):
        preguntas = [pregunta(nivel="aplicar"), pregunta(nivel="recordar")]
        quiz = Quiz(unidad=0, preguntas=preguntas)
        resultado, _ = calificar(quiz, [0, 0])
        assert resultado.nota == 100
        # Falla recordar: 1.5/2.0 = 75; falla aplicar: 0.5/2.0 = 25.
        assert calificar(quiz, [0, 1])[0].nota == 75
        assert calificar(quiz, [1, 0])[0].nota == 25


class TestValidacionNivel:
    def test_rechaza_nivel_desconocido(self):
        crudo = json.loads(quiz_respuesta(6))
        crudo["preguntas"][0]["nivel"] = "inventar"
        with pytest.raises(ValueError, match="nivel desconocido"):
            validar_quiz(crudo, 0, 6)

    def test_sin_nivel_carga_como_comprender(self):
        crudo = json.loads(quiz_respuesta(6))
        del crudo["preguntas"][0]["nivel"]
        quiz = validar_quiz(crudo, 0, 6)
        assert quiz.preguntas[0].nivel == "comprender"


class TestResumenes:
    def test_por_concepto_y_nivel(self):
        quiz = Quiz(
            unidad=0,
            preguntas=[
                pregunta("bucles", "aplicar"),
                pregunta("bucles", "comprender"),
                pregunta("csv", "comprender"),
            ],
        )
        _, detalle = calificar(quiz, [0, 1, 0])
        r = resumenes(detalle)
        assert r["conceptos"] == {"bucles": [1, 2], "csv": [1, 1]}
        assert r["niveles"] == {"aplicar": [1, 1], "comprender": [1, 2]}


class TestBanco:
    def _agente(self, tmp_path, respuestas):
        falso = ClienteLLMFalso([temario_respuesta(), *respuestas])
        return Agente(falso, tmp_path, PERFIL), falso

    def test_banco_crece_y_registra_intentos(self, tmp_path):
        agente, _ = self._agente(tmp_path, ["# lección", quiz_respuesta(6)])
        agente.quiz_de_unidad(0)
        banco = db.leer_banco(tmp_path / "tutor.db", 0)
        assert len(banco) == 6
        assert all(b["intentos"] == [1] for b in banco)
        assert all(b["pregunta"]["nivel"] for b in banco)

    def test_reintento_no_repite_enunciados(self, tmp_path):
        segundo = quiz_respuesta(6).replace("pregunta ", "variante ")
        agente, falso = self._agente(
            tmp_path, ["# lección", quiz_respuesta(6), segundo]
        )
        quiz1 = agente.quiz_de_unidad(0)
        agente.calificar_quiz(quiz1, [1, 1, 1, 1, 1, 1])  # intento 1 (0)
        quiz2 = agente.quiz_de_unidad(0)
        enunciados1 = {p.enunciado for p in quiz1.preguntas}
        enunciados2 = {p.enunciado for p in quiz2.preguntas}
        assert not enunciados1 & enunciados2  # cero repetidas
        # El prompt del intento 2 vetó los enunciados del intento 1.
        assert "pregunta 0" in falso.llamadas[-1][1]
        banco = db.leer_banco(tmp_path / "tutor.db", 0)
        assert len(banco) == 12

    def test_banco_reutiliza_preguntas_viejas_sin_llm(self, tmp_path):
        agente, falso = self._agente(
            tmp_path,
            [
                "# lección",
                quiz_respuesta(6),
                quiz_respuesta(6).replace("pregunta ", "v2 "),
            ],
        )
        q1 = agente.quiz_de_unidad(0)
        agente.calificar_quiz(q1, [1] * 6)  # intento 1
        q2 = agente.quiz_de_unidad(0)
        agente.calificar_quiz(q2, [1] * 6)  # intento 2
        llamadas_antes = len(falso.llamadas)
        # Intento 3: las del intento 1 ya salieron de la ventana de veto
        # (INTENTOS_SIN_REPETIR=2) → se reutilizan sin llamar al LLM.
        q3 = agente.quiz_de_unidad(0)
        assert len(falso.llamadas) == llamadas_antes
        assert {p.enunciado for p in q3.preguntas} == {
            p.enunciado for p in q1.preguntas
        }

    def test_migracion_alter_table_banco(self, tmp_path):
        import sqlite3

        ruta = tmp_path / "tutor.db"
        # BD con el esquema viejo (sin banco_preguntas).
        conexion = sqlite3.connect(ruta)
        conexion.executescript(
            "CREATE TABLE clases(indice INTEGER PRIMARY KEY, titulo TEXT NOT NULL,"
            "objetivo TEXT NOT NULL, conceptos TEXT NOT NULL, guion TEXT,"
            "leccion_md TEXT, guia TEXT, actualizado_en TEXT NOT NULL);"
            "INSERT INTO clases VALUES(0, 't', 'o', '[]', NULL, NULL, NULL, 'x');"
        )
        conexion.commit()
        conexion.close()
        assert db.leer_banco(ruta, 0) == []  # abre y migra sin romper
        db.guardar_banco(ruta, 0, [{"pregunta": {}, "intentos": [1]}])
        assert db.leer_banco(ruta, 0) == [{"pregunta": {}, "intentos": [1]}]
