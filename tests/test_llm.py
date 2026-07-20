import json

import httpx
import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

from tutor.config import MAX_REINTENTOS_API, MAX_REINTENTOS_PARSEO
from tutor.errores import ErrorLLM
from tutor.llm import ClienteOpenAI, espera_backoff, extraer_json, pedir_json

from .conftest import ClienteLLMFalso, SDKFalso


def _error_http(codigo):
    peticion = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    respuesta = httpx.Response(codigo, request=peticion)
    if codigo == 429:
        return RateLimitError("límite", response=respuesta, body=None)
    if codigo == 401:
        return AuthenticationError("no autorizado", response=respuesta, body=None)
    return APIStatusError(f"error {codigo}", response=respuesta, body=None)


def _error_conexion():
    peticion = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return APIConnectionError(request=peticion)


def _cliente(configuracion, resultados):
    sdk = SDKFalso(resultados)
    cliente = ClienteOpenAI(configuracion, cliente=sdk, dormir=lambda _: None)
    return cliente, sdk


class TestClienteOpenAI:
    def test_generar_devuelve_contenido(self, configuracion):
        cliente, sdk = _cliente(configuracion, ["hola"])
        assert cliente.generar("sys", "pregunta") == "hola"
        assert sdk.llamadas[0]["model"] == "gpt-prueba"

    def test_generar_reintenta_ante_429_y_luego_funciona(self, configuracion):
        cliente, sdk = _cliente(configuracion, [_error_http(429), "ok"])
        assert cliente.generar("sys", "p") == "ok"
        assert len(sdk.llamadas) == 2

    def test_generar_reintenta_ante_500_y_conexion(self, configuracion):
        cliente, sdk = _cliente(
            configuracion, [_error_http(500), _error_conexion(), "ok"]
        )
        assert cliente.generar("sys", "p") == "ok"
        assert len(sdk.llamadas) == 3

    def test_generar_no_reintenta_ante_401(self, configuracion):
        cliente, sdk = _cliente(configuracion, [_error_http(401)])
        with pytest.raises(ErrorLLM, match="sin reintento"):
            cliente.generar("sys", "p")
        assert len(sdk.llamadas) == 1

    def test_generar_agota_reintentos_y_lanza_error_llm(self, configuracion):
        cliente, sdk = _cliente(configuracion, [_error_http(429)] * MAX_REINTENTOS_API)
        with pytest.raises(ErrorLLM, match="siguió fallando"):
            cliente.generar("sys", "p")
        assert len(sdk.llamadas) == MAX_REINTENTOS_API

    def test_generar_respuesta_vacia_lanza_error_llm(self, configuracion):
        cliente, _ = _cliente(configuracion, [""])
        with pytest.raises(ErrorLLM, match="vacía"):
            cliente.generar("sys", "p")


class TestEsperaBackoff:
    def test_es_exponencial_con_jitter_acotado(self):
        assert 0.5 <= espera_backoff(0, azar=lambda: 0.0) <= 1.5
        assert espera_backoff(2, azar=lambda: 0.5) == 4.0
        assert espera_backoff(1, azar=lambda: 0.999) < 3.0


class TestExtraerJson:
    def test_parsea_json_plano(self):
        assert extraer_json('{"a": 1}') == {"a": 1}

    def test_extrae_json_entre_fences(self):
        assert extraer_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_json_invalido_lanza_error(self):
        with pytest.raises(json.JSONDecodeError):
            extraer_json("no es json")


class TestPedirJson:
    @staticmethod
    def _validar(datos):
        if "unidades" not in datos:
            raise ValueError("falta el campo 'unidades'")
        return datos["unidades"]

    def test_parsea_respuesta_valida(self):
        falso = ClienteLLMFalso(['{"unidades": [1, 2]}'])
        assert pedir_json(falso, "sys", "p", self._validar) == [1, 2]

    def test_reintenta_ante_json_invalido_e_incluye_error_en_prompt(self):
        falso = ClienteLLMFalso(["no es json", '{"unidades": []}'])
        assert pedir_json(falso, "sys", "p", self._validar) == []
        assert len(falso.llamadas) == 2
        assert "no cumplió el esquema" in falso.llamadas[1][1]

    def test_reintenta_ante_esquema_incompleto(self):
        falso = ClienteLLMFalso(['{"otra_cosa": 1}', '{"unidades": [3]}'])
        assert pedir_json(falso, "sys", "p", self._validar) == [3]
        assert "unidades" in falso.llamadas[1][1]

    def test_falla_claro_tras_agotar_reintentos(self):
        falso = ClienteLLMFalso(["basura"] * (MAX_REINTENTOS_PARSEO + 1))
        with pytest.raises(ErrorLLM, match="formato esperado"):
            pedir_json(falso, "sys", "p", self._validar)
        assert len(falso.llamadas) == MAX_REINTENTOS_PARSEO + 1
