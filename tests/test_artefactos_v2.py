"""Pruebas del pipeline de artefactos v2 (plan/v2/HU-27)."""

import pytest

from tutor.ensenanza.agente import Agente, verificar_artefacto
from tutor.ensenanza.prompts import clasificar_plantilla
from tutor.nucleo.errores import ErrorLLM
from tutor.nucleo.models import Nivel, Objetivo, PerfilEstudiante

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta
from .test_guion_v2 import guion_v2_respuesta

PERFIL = PerfilEstudiante(
    nivel=Nivel.BASICO,
    experiencia="",
    objetivo=Objetivo.DATOS,
    objetivo_detalle="",
    lenguaje="python",
)

HTML_OK = (
    "<!doctype html><html><body><button onclick='f()'>x</button>"
    "<script>function f(){}</script></body></html>"
)


class TestClasificarPlantilla:
    @pytest.mark.parametrize(
        ("conceptos", "esperada"),
        [
            (["bucles for", "iteración"], "flujo"),
            (["filtrar un CSV", "columnas"], "datos"),
            (["funciones", "parámetros"], "funcion"),
            (["variables", "tipos"], "estado"),
            (["algo rarísimo"], "estado"),  # fallback
        ],
    )
    def test_cada_categoria_y_fallback(self, conceptos, esperada):
        assert clasificar_plantilla(conceptos) == esperada


class TestVerificador:
    def test_acepta_html_valido(self):
        assert verificar_artefacto(HTML_OK) == []

    @pytest.mark.parametrize(
        ("html", "problema"),
        [
            ("<html><script></script><button></button></html>", "doctype"),
            (
                HTML_OK.replace("<script>", "<script src='https://cdn.x/a.js'>"),
                "externos",
            ),
            (HTML_OK.replace("function f(){}", "fetch('/x')"), "fetch"),
            (
                HTML_OK.replace("<button onclick='f()'>x</button>", "<p>x</p>"),
                "control",
            ),
            (HTML_OK.replace("function f(){}", "alert(1)"), "alert"),
            ("<!doctype html><body><button>x</button></body>", "script"),
        ],
    )
    def test_rechaza_problemas(self, html, problema):
        assert any(problema in e for e in verificar_artefacto(html))

    def test_rechaza_mas_de_40kb(self):
        gordo = HTML_OK + "<!--" + "x" * 41 * 1024 + "-->"
        assert any("40 KB" in e for e in verificar_artefacto(gordo))


def agente_con_guion(tmp_path, respuestas):
    falso = ClienteLLMFalso(
        [temario_respuesta(), guion_v2_respuesta(), "apertura", *respuestas]
    )
    agente = Agente(falso, tmp_path, PERFIL)
    agente.turno_estudio(None, unidad=0)
    return agente, falso


class TestArtefacto:
    def test_cache_por_objetivo_y_regenerar_invalida(self, tmp_path):
        v2 = HTML_OK.replace("x</button>", "y</button>")
        agente, falso = agente_con_guion(tmp_path, [HTML_OK, v2])
        r1 = agente.artefacto(0, objetivo=1)
        assert r1 == {"html": HTML_OK, "plantilla": "estado", "cacheado": False}
        assert "objetivo 1" in falso.llamadas[-1][1]  # contexto del objetivo
        # Cache: segunda llamada no gasta LLM.
        r2 = agente.artefacto(0, objetivo=1)
        assert r2["cacheado"] is True and r2["html"] == HTML_OK
        # Regenerar invalida esa clave.
        r3 = agente.artefacto(0, objetivo=1, regenerar=True)
        assert r3["html"] == v2 and r3["cacheado"] is False

    def test_objetivos_distintos_no_comparten_cache(self, tmp_path):
        agente, _ = agente_con_guion(tmp_path, [HTML_OK, HTML_OK])
        agente.artefacto(0, objetivo=0)
        agente.artefacto(0, objetivo=1)
        assert "0-obj0" in agente.curso.artefactos
        assert "0-obj1" in agente.curso.artefactos

    def test_verificacion_fallida_regenera_con_errores(self, tmp_path):
        roto = "<p>sin nada</p>"
        agente, falso = agente_con_guion(tmp_path, [roto, HTML_OK])
        r = agente.artefacto(0, objetivo=0)
        assert r["html"] == HTML_OK
        # El segundo prompt llevó los errores del primer intento.
        assert "NO pasó el control de calidad" in falso.llamadas[-1][1]
        assert "doctype" in falso.llamadas[-1][1]

    def test_doble_fallo_no_cachea_y_lanza(self, tmp_path):
        agente, _ = agente_con_guion(tmp_path, ["<p>roto</p>", "<p>roto2</p>"])
        with pytest.raises(ErrorLLM, match="control de calidad"):
            agente.artefacto(0, objetivo=0)
        assert "0-obj0" not in agente.curso.artefactos

    def test_clase_v1_usa_contexto_de_clase(self, tmp_path):
        falso = ClienteLLMFalso([temario_respuesta(), HTML_OK])
        agente = Agente(falso, tmp_path, PERFIL)
        r = agente.artefacto(0, objetivo=2)  # sin guion v2 → cae a clase
        assert r["html"] == HTML_OK
        assert "u0" in agente.curso.artefactos
        assert "Conceptos a ilustrar" in falso.llamadas[-1][1]
