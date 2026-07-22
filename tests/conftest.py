"""Fixtures compartidas: dobles de prueba del LLM y datos de ejemplo."""

from types import SimpleNamespace

import pytest

from tutor.config import Configuracion
from tutor.models import Nivel, Objetivo, PerfilEstudiante


class ClienteLLMFalso:
    """Doble de ``ClienteLLM``: respuestas en cola y registro de llamadas.

    - ``respuestas``: se devuelven en orden; si un elemento es una excepción,
      se lanza en vez de devolverse.
    - ``llamadas``: lista de tuplas (system, prompt) recibidas.
    """

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.carriles = []  # carril de cada llamada, en orden (HU-39)

    def generar(self, system: str, prompt: str, carril: str = "potente") -> str:
        self.llamadas.append((system, prompt))
        self.carriles.append(carril)
        return self._siguiente()

    def generar_stream(self, system: str, prompt: str, carril: str = "potente"):
        """Emite la siguiente respuesta en trozos de ``tamano_trozo`` (HU-35)."""
        respuesta = self.generar(system, prompt, carril)
        n = getattr(self, "tamano_trozo", 7)
        for i in range(0, len(respuesta), n):
            yield respuesta[i : i + n]

    def _siguiente(self) -> str:
        if not self.respuestas:
            raise AssertionError("ClienteLLMFalso se quedó sin respuestas.")
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


class SDKFalso:
    """Doble del cliente del SDK de OpenAI (``chat.completions.create``).

    ``resultados`` mezcla strings (respuesta exitosa) y excepciones del SDK.
    """

    def __init__(self, resultados):
        self._resultados = list(resultados)
        self.llamadas = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    @property
    def modelos(self):
        """Modelo pedido en cada llamada, en orden (HU-39)."""
        return [k["model"] for k in self.llamadas]

    def _create(self, **kwargs):
        self.llamadas.append(kwargs)
        siguiente = self._resultados.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=siguiente))]
        )


@pytest.fixture
def configuracion(tmp_path):
    return Configuracion(api_key="sk-prueba", modelo="gpt-prueba", dir_datos=tmp_path)


@pytest.fixture
def perfil():
    return PerfilEstudiante(
        nivel=Nivel.BASICO,
        experiencia="macros de Excel",
        objetivo=Objetivo.DATOS,
        objetivo_detalle="",
        lenguaje="python",
    )
