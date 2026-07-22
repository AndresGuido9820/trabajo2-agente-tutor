import pytest

from tutor.ensenanza.progreso import (
    Progreso,
    Resultado,
    cargar_progreso,
    crear_resultado,
    guardar_progreso,
)


def resultado(unidad=0, nota=75, fallados=None):
    return Resultado(
        unidad=unidad,
        nota=nota,
        conceptos_fallados=fallados or [],
        fecha="2026-07-20T12:00:00+00:00",
    )


class TestModelo:
    def test_nota_fuera_de_rango_lanza_error(self):
        with pytest.raises(ValueError, match="0-100"):
            resultado(nota=101)

    def test_marcar_vista_es_idempotente(self):
        progreso = Progreso()
        progreso.marcar_vista(2)
        primera_fecha = progreso.vistas[2]
        progreso.marcar_vista(2)
        assert progreso.vistas[2] == primera_fecha

    def test_mejor_nota_conserva_maxima_de_varios_intentos(self):
        progreso = Progreso()
        progreso.registrar(resultado(unidad=1, nota=50))
        progreso.registrar(resultado(unidad=1, nota=100))
        progreso.registrar(resultado(unidad=1, nota=75))
        assert progreso.mejor_nota(1) == 100
        assert progreso.intentos(1) == 3

    def test_mejor_nota_sin_intentos_es_none(self):
        assert Progreso().mejor_nota(0) is None

    def test_conceptos_fallados_recientes_dedup_y_orden(self):
        progreso = Progreso()
        progreso.registrar(resultado(unidad=0, fallados=["bucles", "variables"]))
        progreso.registrar(resultado(unidad=1, fallados=["listas", "bucles"]))
        assert progreso.conceptos_fallados_recientes() == [
            "listas",
            "bucles",
            "variables",
        ]

    def test_conceptos_fallados_respeta_maximo(self):
        progreso = Progreso()
        progreso.registrar(resultado(fallados=[f"c{i}" for i in range(10)]))
        assert len(progreso.conceptos_fallados_recientes(maximo=4)) == 4


class TestPersistencia:
    def test_roundtrip_entre_instancias(self, tmp_path):
        ruta = tmp_path / "progreso.json"
        sesion_1 = Progreso()
        sesion_1.marcar_vista(0)
        sesion_1.registrar(crear_resultado(0, 80, ["funciones"]))
        guardar_progreso(sesion_1, ruta)

        sesion_2 = cargar_progreso(ruta)
        assert sesion_2 == sesion_1
        assert sesion_2.mejor_nota(0) == 80

    def test_inexistente_arranca_vacio(self, tmp_path):
        progreso = cargar_progreso(tmp_path / "no-existe.json")
        assert progreso == Progreso()

    def test_corrupto_arranca_vacio_con_advertencia(self, tmp_path, caplog):
        ruta = tmp_path / "progreso.json"
        ruta.write_text("{roto", "utf-8")
        progreso = cargar_progreso(ruta)
        assert progreso == Progreso()
        assert "corrupto" in caplog.text.lower()

    def test_guardado_es_atomico_sin_temporal_residual(self, tmp_path):
        ruta = tmp_path / "progreso.json"
        guardar_progreso(Progreso(), ruta)
        assert ruta.exists()
        assert not ruta.with_suffix(".tmp").exists()
