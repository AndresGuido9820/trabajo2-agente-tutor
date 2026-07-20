import pytest

from tutor.errores import ErrorDatos
from tutor.models import Nivel, Objetivo, PerfilEstudiante
from tutor.perfil import (
    cargar_perfil,
    guardar_perfil,
    preguntar_perfil,
    validar_lenguaje,
    validar_opcion,
)


def perfil_ejemplo(**cambios):
    base = dict(
        nivel=Nivel.BASICO,
        experiencia="hice macros en Excel",
        objetivo=Objetivo.DATOS,
        objetivo_detalle="",
        lenguaje="python",
    )
    base.update(cambios)
    return PerfilEstudiante(**base)


class TestValidaciones:
    def test_valida_opcion_acepta_rango(self):
        assert validar_opcion("2", 3) == 1

    def test_valida_opcion_rechaza_fuera_de_rango(self):
        with pytest.raises(ValueError, match="entre 1 y 3"):
            validar_opcion("4", 3)

    @pytest.mark.parametrize("entrada", ["", "  ", "abc", "-1", "1.5"])
    def test_valida_opcion_rechaza_no_numericas(self, entrada):
        with pytest.raises(ValueError):
            validar_opcion(entrada, 3)

    def test_valida_lenguaje_normaliza(self):
        assert validar_lenguaje("  Python ") == "python"
        assert validar_lenguaje("C++") == "c++"

    def test_valida_lenguaje_vacio_significa_decide_el_tutor(self):
        assert validar_lenguaje("") == ""

    def test_valida_lenguaje_rechaza_basura(self):
        with pytest.raises(ValueError):
            validar_lenguaje("¿?¡!")

    def test_valida_objetivo_otro_exige_detalle(self):
        with pytest.raises(ValueError, match="objetivo_detalle"):
            perfil_ejemplo(objetivo=Objetivo.OTRO, objetivo_detalle="  ")


class TestCuestionario:
    def test_preguntar_perfil_flujo_feliz(self):
        respuestas = iter(["2", "macros de Excel", "1", "python"])
        perfil = preguntar_perfil(entrada=lambda _: next(respuestas))
        assert perfil == perfil_ejemplo(experiencia="macros de Excel")

    def test_preguntar_perfil_reintenta_ante_entrada_invalida(self, capsys):
        respuestas = iter(["", "9", "2", "", "abc", "1", ""])
        perfil = preguntar_perfil(entrada=lambda _: next(respuestas))
        assert perfil.nivel is Nivel.BASICO
        assert perfil.objetivo is Objetivo.DATOS
        assert perfil.lenguaje == ""
        assert "Entrada inválida" in capsys.readouterr().out

    def test_preguntar_perfil_objetivo_otro_pide_detalle(self):
        respuestas = iter(["1", "", "5", "   ", "videojuegos", ""])
        perfil = preguntar_perfil(entrada=lambda _: next(respuestas))
        assert perfil.objetivo is Objetivo.OTRO
        assert perfil.objetivo_detalle == "videojuegos"


class TestPersistencia:
    def test_guardar_y_cargar_perfil_roundtrip(self, tmp_path):
        ruta = tmp_path / "perfil.json"
        original = perfil_ejemplo()
        guardar_perfil(original, ruta)
        assert cargar_perfil(ruta) == original

    def test_cargar_perfil_inexistente_devuelve_none(self, tmp_path):
        assert cargar_perfil(tmp_path / "no-existe.json") is None

    def test_cargar_perfil_json_corrupto_lanza_error_claro(self, tmp_path):
        ruta = tmp_path / "perfil.json"
        ruta.write_text("{esto no es json", "utf-8")
        with pytest.raises(ErrorDatos, match="corrupto"):
            cargar_perfil(ruta)

    def test_cargar_perfil_con_campos_faltantes_lanza_error(self, tmp_path):
        ruta = tmp_path / "perfil.json"
        ruta.write_text('{"version": 1, "nivel": "basico"}', "utf-8")
        with pytest.raises(ErrorDatos, match="faltan campos"):
            cargar_perfil(ruta)

    def test_cargar_perfil_con_enum_invalido_lanza_error(self, tmp_path):
        ruta = tmp_path / "perfil.json"
        guardar_perfil(perfil_ejemplo(), ruta)
        contenido = ruta.read_text("utf-8").replace('"basico"', '"experto"')
        ruta.write_text(contenido, "utf-8")
        with pytest.raises(ErrorDatos):
            cargar_perfil(ruta)
