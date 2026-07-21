import json

import pytest

from tutor.agente import Agente
from tutor.curso import cargar_curso, validar_guion
from tutor.ui import bucle_leccion

from .conftest import ClienteLLMFalso
from .test_agente import temario_respuesta


def guion_json(n_pasos=5):
    tipos = ["gancho", "prediccion", "explicacion", "modificacion", "recap"]
    return {
        "objetivos": ["crear variables", "leer errores"],
        "pasos": [
            {"tipo": tipos[i % len(tipos)], "instruccion": f"haz el paso {i}"}
            for i in range(n_pasos)
        ],
    }


def guion_respuesta():
    return json.dumps(guion_json())


def avanza(mensaje, si=True):
    """Respuesta del tutor en el contrato JSON de avance."""
    return json.dumps({"avanza": si, "mensaje": mensaje})


class TestValidarGuion:
    def test_acepta_guion_valido(self):
        guion = validar_guion(guion_json())
        assert len(guion.pasos) == 5
        assert guion.objetivos[0] == "crear variables"

    @pytest.mark.parametrize("n", [4, 9])
    def test_rechaza_numero_de_pasos_fuera_de_rango(self, n):
        with pytest.raises(ValueError, match="pasos"):
            validar_guion(guion_json(n))

    def test_rechaza_tipo_desconocido(self):
        datos = guion_json()
        datos["pasos"][2]["tipo"] = "magia"
        with pytest.raises(ValueError, match="desconocido"):
            validar_guion(datos)

    def test_rechaza_objetivos_vacios(self):
        datos = guion_json()
        datos["objetivos"] = []
        with pytest.raises(ValueError, match="objetivos"):
            validar_guion(datos)


class TestLeccionConversada:
    def _agente(self, tmp_path, perfil, respuestas):
        falso = ClienteLLMFalso([temario_respuesta(), *respuestas])
        return Agente(cliente=falso, dir_datos=tmp_path, perfil=perfil), falso

    def test_flujo_avanza_un_paso_por_respuesta_y_termina(self, tmp_path, perfil):
        turnos = [avanza(f"tutor dice {i}") for i in range(1, 5)]
        agente, _ = self._agente(
            tmp_path, perfil, [guion_respuesta(), "tutor dice 0", *turnos]
        )
        agente.iniciar_leccion(0)

        texto, terminada = agente.turno_leccion(0, None)
        assert texto == "tutor dice 0" and not terminada
        assert agente.avance_leccion(0) == (1, 5)

        for i in range(1, 4):
            texto, terminada = agente.turno_leccion(0, f"respuesta {i}")
            assert texto == f"tutor dice {i}" and not terminada
        texto, terminada = agente.turno_leccion(0, "última respuesta")
        assert texto == "tutor dice 4" and terminada

    def test_saludo_o_duda_no_avanza_el_paso(self, tmp_path, perfil):
        agente, _ = self._agente(
            tmp_path,
            perfil,
            [guion_respuesta(), "paso 1", avanza("¡hola! seguimos…", False)],
        )
        agente.iniciar_leccion(0)
        agente.turno_leccion(0, None)
        texto, terminada = agente.turno_leccion(0, "hola jaja")
        assert texto == "¡hola! seguimos…" and not terminada
        assert agente.avance_leccion(0) == (1, 5)  # NO avanzó

    def test_turno_incluye_paso_historial_y_respuesta_en_prompt(self, tmp_path, perfil):
        agente, falso = self._agente(
            tmp_path, perfil, [guion_respuesta(), "hola", avanza("sigo")]
        )
        agente.iniciar_leccion(0)
        agente.turno_leccion(0, None)
        agente.turno_leccion(0, "creo que imprime 4")

        system, prompt = falso.llamadas[-1]
        assert "CONVERSACIÓN" in system
        assert "paso 1 de 5" in prompt
        assert "haz el paso 0" in prompt  # paso actual
        assert "haz el paso 1" in prompt  # paso siguiente
        assert "creo que imprime 4" in prompt  # respuesta del estudiante
        assert "hola" in prompt  # historial del turno anterior
        assert '"avanza"' in prompt  # contrato JSON

    def test_guion_se_cachea_y_persiste(self, tmp_path, perfil):
        agente, falso = self._agente(tmp_path, perfil, [guion_respuesta()])
        guion = agente.iniciar_leccion(0)
        llamadas = len(falso.llamadas)

        # Reiniciar la lección no regenera el guion (cache en memoria)
        assert agente.iniciar_leccion(0) == guion
        assert len(falso.llamadas) == llamadas

        # Y sobrevive en curso.json para una nueva sesión
        curso = cargar_curso(tmp_path / "curso.json")
        assert curso is not None and curso.guiones[0] == guion

    def test_bucle_leccion_sale_con_salir(self, tmp_path, perfil, capsys):
        agente, _ = self._agente(tmp_path, perfil, [guion_respuesta(), "turno 1"])
        completada = bucle_leccion(agente, 0, entrada=lambda _: "salir")
        assert completada is False
        assert "pausada" in capsys.readouterr().out

    def test_bucle_leccion_completa(self, tmp_path, perfil, capsys):
        turnos = [avanza(f"t{i}") for i in range(1, 5)]
        agente, _ = self._agente(tmp_path, perfil, [guion_respuesta(), "t0", *turnos])
        completada = bucle_leccion(agente, 0, entrada=lambda _: "ok")
        assert completada is True
        assert "completada" in capsys.readouterr().out
