"""Pruebas de las ilustraciones con IA (plan/HU-08, bonus)."""

from fastapi.testclient import TestClient

from tutor.config import Configuracion, cargar_configuracion
from tutor.interfaces.web import crear_app
from tutor.proveedor.imagenes import ilustrar_unidad, prompt_visual, ruta_imagen

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta

PNG_FALSO = b"\x89PNG\r\n\x1a\nimagen-de-mentiras"


class GeneradorFalso:
    """Doble del generador de imágenes: cuenta llamadas y puede fallar."""

    def __init__(self, error=None):
        self.llamadas = []
        self.error = error

    def generar_imagen(self, prompt):
        self.llamadas.append(prompt)
        if self.error:
            raise self.error
        return PNG_FALSO


class TestIlustrarUnidad:
    def test_genera_y_cachea(self, tmp_path):
        generador = GeneradorFalso()
        ruta = ilustrar_unidad(
            generador, tmp_path, 0, "Variables", ["variables", "tipos"], "python"
        )
        assert ruta == ruta_imagen(tmp_path, 0)
        assert ruta.read_bytes() == PNG_FALSO
        assert len(generador.llamadas) == 1
        assert "Variables" in generador.llamadas[0]
        assert "SIN texto" in generador.llamadas[0]
        # Cache: la segunda llamada no toca la API.
        ilustrar_unidad(generador, tmp_path, 0, "Variables", ["v"], "python")
        assert len(generador.llamadas) == 1

    def test_fallo_degrada_a_none_sin_romper(self, tmp_path):
        generador = GeneradorFalso(error=RuntimeError("API caída"))
        ruta = ilustrar_unidad(generador, tmp_path, 0, "X", ["y"], "python")
        assert ruta is None
        assert not ruta_imagen(tmp_path, 0).exists()

    def test_cliente_sin_soporte_devuelve_none(self, tmp_path):
        # Los dobles del LLM no tienen generar_imagen: cero llamadas, cero error.
        assert ilustrar_unidad(object(), tmp_path, 0, "X", ["y"], "python") is None

    def test_prompt_visual_evita_texto(self):
        p = prompt_visual("Bucles", ["for", "while", "range", "extra"], "python")
        assert "SIN texto" in p and "extra" not in p  # máximo 3 conceptos


class TestFlag:
    def test_flag_apagado_por_defecto_y_encendido_por_env(self):
        assert cargar_configuracion({"OPENAI_API_KEY": "sk-x"}).imagenes is False
        activa = cargar_configuracion({"OPENAI_API_KEY": "sk-x", "TUTOR_IMAGENES": "1"})
        assert activa.imagenes is True


class TestEndpointImagen:
    def _web(self, tmp_path, imagenes):
        configuracion = Configuracion(
            api_key="sk-prueba",
            modelo="gpt-prueba",
            dir_datos=tmp_path,
            imagenes=imagenes,
        )
        falso = ClienteLLMFalso([temario_respuesta()])
        falso.generar_imagen = lambda prompt: PNG_FALSO  # doble con soporte
        web = TestClient(crear_app(configuracion, cliente=falso))
        web.post(
            "/api/perfil",
            json={"nivel": "basico", "objetivo": "datos", "lenguaje": "python"},
        )
        return web

    def test_flag_apagado_da_404_sin_llamar(self, tmp_path):
        web = self._web(tmp_path, imagenes=False)
        assert web.get("/api/clase/0/imagen").status_code == 404
        assert not (tmp_path / "cursos" / "1" / "imagenes").exists()

    def test_flag_encendido_sirve_png_y_cachea(self, tmp_path):
        web = self._web(tmp_path, imagenes=True)
        r = web.get("/api/clase/0/imagen")
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"
        assert r.content == PNG_FALSO
        assert (tmp_path / "cursos" / "1" / "imagenes" / "unidad-0.png").exists()
        assert web.get("/api/clase/99/imagen").status_code == 404
