import json

import pytest

from tutor.curso import (
    Curso,
    Temario,
    cargar_curso,
    generar_leccion,
    generar_temario,
    guardar_curso,
    validar_temario,
)
from tutor.errores import ErrorLLM
from tutor.progreso import Progreso, Resultado

from .conftest import ClienteLLMFalso


def temario_json(n_unidades=5):
    return {
        "lenguaje": "python",
        "unidades": [
            {
                "titulo": f"Unidad {i}",
                "objetivo": f"objetivo {i}",
                "conceptos": ["a", "b", "c"],
            }
            for i in range(n_unidades)
        ],
    }


def temario_ejemplo(n_unidades=5):
    return validar_temario(temario_json(n_unidades))


class TestValidarTemario:
    def test_acepta_temario_valido(self):
        temario = validar_temario(temario_json())
        assert temario.lenguaje == "python"
        assert len(temario.unidades) == 5
        assert temario.unidades[0].conceptos == ["a", "b", "c"]

    @pytest.mark.parametrize("n", [4, 9])
    def test_rechaza_numero_de_unidades_fuera_de_rango(self, n):
        with pytest.raises(ValueError, match="unidades"):
            validar_temario(temario_json(n))

    def test_rechaza_unidad_con_campos_vacios(self):
        datos = temario_json()
        datos["unidades"][2]["titulo"] = "  "
        with pytest.raises(ValueError, match="unidad 2"):
            validar_temario(datos)

    def test_rechaza_esquema_incompleto(self):
        with pytest.raises(KeyError):
            validar_temario({"lenguaje": "python"})


class TestGenerarTemario:
    def test_parsea_y_valida(self, perfil):
        falso = ClienteLLMFalso([json.dumps(temario_json())])
        temario = generar_temario(falso, perfil)
        assert isinstance(temario, Temario)
        system, prompt = falso.llamadas[0]
        assert "ciencia de datos" in system  # perfil inyectado en la persona
        assert "python" in system  # lenguaje elegido presente
        assert "JSON" in prompt

    def test_json_incompleto_reintenta_y_luego_falla_claro(self, perfil):
        falso = ClienteLLMFalso(['{"lenguaje": "python"}'] * 3)
        with pytest.raises(ErrorLLM, match="formato esperado"):
            generar_temario(falso, perfil)


class TestGenerarLeccion:
    def test_genera_y_cachea(self, perfil):
        curso = Curso(temario=temario_ejemplo())
        falso = ClienteLLMFalso(["# Lección 1"])
        primera = generar_leccion(falso, perfil, curso, 0, Progreso())
        segunda = generar_leccion(falso, perfil, curso, 0, Progreso())
        assert primera == segunda == "# Lección 1"
        assert len(falso.llamadas) == 1  # la segunda salió del cache

    def test_incluye_unidades_vistas_y_conceptos_fallados_en_prompt(self, perfil):
        curso = Curso(temario=temario_ejemplo(), lecciones={0: "ya vista"})
        progreso = Progreso()
        progreso.registrar(
            Resultado(
                unidad=0,
                nota=50,
                conceptos_fallados=["bucles"],
                fecha="2026-07-20T12:00:00+00:00",
            )
        )
        falso = ClienteLLMFalso(["# Lección 2"])
        generar_leccion(falso, perfil, curso, 1, progreso)
        _, prompt = falso.llamadas[0]
        assert "Unidad 0" in prompt  # contexto de lo ya estudiado
        assert "bucles" in prompt  # refuerzo de lo fallado

    def test_indice_invalido_lanza_index_error(self, perfil):
        curso = Curso(temario=temario_ejemplo())
        with pytest.raises(IndexError):
            generar_leccion(ClienteLLMFalso([]), perfil, curso, 99, Progreso())


class TestPersistenciaCurso:
    def test_roundtrip(self, tmp_path):
        ruta = tmp_path / "curso.json"
        curso = Curso(temario=temario_ejemplo(), lecciones={0: "# md"})
        guardar_curso(curso, ruta)
        assert cargar_curso(ruta) == curso

    def test_inexistente_devuelve_none(self, tmp_path):
        assert cargar_curso(tmp_path / "no.json") is None

    def test_corrupto_devuelve_none_con_advertencia(self, tmp_path, caplog):
        ruta = tmp_path / "curso.json"
        ruta.write_text("{roto", "utf-8")
        assert cargar_curso(ruta) is None
        assert "regenerará" in caplog.text
