import json
import sqlite3

from tutor.ensenanza.curso import cargar_curso, cargar_plan_md
from tutor.ensenanza.perfil import cargar_perfil
from tutor.ensenanza.progreso import cargar_progreso
from tutor.persistencia import db


class TestBaseDatos:
    def test_chat_por_canal(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        db.anotar_chat(ruta, "u0", "yo", "hola")
        db.anotar_chat(ruta, "u0", "tutor", "¡hola!")
        db.anotar_chat(ruta, "u1", "yo", "otra clase")
        assert db.historial_chat(ruta, "u0") == [
            {"rol": "yo", "texto": "hola"},
            {"rol": "tutor", "texto": "¡hola!"},
        ]
        assert db.resumen_chats(ruta) == {"u0": 2, "u1": 1}

    def test_clases_guardan_prompt_y_metadata(self, tmp_path):
        """La tabla clases contiene el guion (prompt) y metadata por clase."""
        from tutor.ensenanza.curso import Curso, guardar_curso, validar_guion

        from .test_agente import temario_respuesta
        from .test_leccion import guion_json

        ruta = tmp_path / "tutor.db"
        temario_datos = json.loads(temario_respuesta())
        from tutor.ensenanza.curso import validar_temario

        curso = Curso(temario=validar_temario(temario_datos))
        curso.guiones[0] = validar_guion(guion_json())
        curso.lecciones[0] = "# lección"
        guardar_curso(curso, ruta)

        with db.abrir(ruta) as conexion:
            fila = conexion.execute(
                "SELECT guion, leccion_md, actualizado_en FROM clases WHERE indice = 0"
            ).fetchone()
        assert "haz el paso 0" in fila[0]  # el prompt/guion de la clase
        assert fila[1] == "# lección"
        assert fila[2]  # metadata de actualización

        recargado = cargar_curso(ruta)
        assert recargado is not None and recargado.guiones[0] == curso.guiones[0]

    def test_borrar_curso_no_toca_perfil_ni_chat(self, tmp_path):
        from tutor.ensenanza.perfil import guardar_perfil
        from tutor.nucleo.models import Nivel, Objetivo, PerfilEstudiante

        ruta = tmp_path / "tutor.db"
        perfil = PerfilEstudiante(Nivel.BASICO, "", Objetivo.DATOS, "", "python")
        guardar_perfil(perfil, ruta)
        db.anotar_chat(ruta, "creacion", "yo", "hola")
        db.borrar_curso(ruta)
        assert cargar_perfil(ruta) == perfil
        assert db.resumen_chats(ruta) == {"creacion": 1}


class TestMigracionLegacy:
    def test_migra_json_viejos_una_sola_vez(self, tmp_path):
        (tmp_path / "perfil.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "nivel": "basico",
                    "experiencia": "Excel",
                    "objetivo": "datos",
                    "objetivo_detalle": "",
                    "lenguaje": "python",
                }
            ),
            "utf-8",
        )
        (tmp_path / "progreso.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "puntos": 40,
                    "vistas": {"0": "x"},
                    "resultados": [],
                    "completadas": [0],
                }
            ),
            "utf-8",
        )
        from .test_agente import temario_respuesta

        curso_viejo = json.loads(temario_respuesta())
        curso_viejo["lecciones"] = {"0": "# vieja"}
        (tmp_path / "curso.json").write_text(json.dumps(curso_viejo), "utf-8")
        (tmp_path / "curso.md").write_text("# Tu curso de python", "utf-8")
        (tmp_path / "chat.json").write_text(
            json.dumps({"u0": [{"rol": "yo", "texto": "hola"}]}), "utf-8"
        )

        db.migrar_json_legacy(tmp_path)
        ruta = tmp_path / "tutor.db"
        assert cargar_perfil(ruta) is not None
        assert cargar_progreso(ruta).puntos == 40
        curso = cargar_curso(ruta)
        assert curso is not None and curso.lecciones[0] == "# vieja"
        assert cargar_plan_md(ruta) == "# Tu curso de python"
        assert db.historial_chat(ruta, "u0") == [{"rol": "yo", "texto": "hola"}]

        # Segunda llamada: no duplica (la BD ya existe)
        db.migrar_json_legacy(tmp_path)
        assert db.resumen_chats(ruta) == {"u0": 1}

    def test_archivo_basura_como_db_es_tolerado(self, tmp_path):
        ruta = tmp_path / "tutor.db"
        ruta.write_bytes(b"{esto no es sqlite")
        try:
            db.cargar_documento(ruta, "perfil")
            raise AssertionError("debió fallar")
        except sqlite3.DatabaseError:
            pass
        assert cargar_progreso(ruta).puntos == 0  # degrada a vacío
        assert cargar_curso(ruta) is None  # degrada a regenerar
