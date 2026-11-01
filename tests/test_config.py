from pathlib import Path

import pytest

from tutor.config import (
    API_KEY_LOCAL,
    DIR_DATOS_POR_DEFECTO,
    MODELO_POR_DEFECTO,
    cargar_configuracion,
)
from tutor.nucleo.errores import ErrorConfiguracion


def test_config_sin_api_key_lanza_error_configuracion():
    with pytest.raises(ErrorConfiguracion, match="OPENAI_API_KEY"):
        cargar_configuracion(entorno={})


def test_config_api_key_en_blanco_lanza_error_configuracion():
    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(entorno={"OPENAI_API_KEY": "   "})


def test_config_lee_valores_por_defecto():
    config = cargar_configuracion(entorno={"OPENAI_API_KEY": "sk-prueba"})
    assert config.api_key == "sk-prueba"
    assert config.modelo == MODELO_POR_DEFECTO
    assert config.dir_datos == Path(DIR_DATOS_POR_DEFECTO)


def test_config_respeta_overrides_de_entorno(tmp_path):
    config = cargar_configuracion(
        entorno={
            "OPENAI_API_KEY": "sk-prueba",
            "TUTOR_MODEL": "gpt-5",
            "TUTOR_DATA_DIR": str(tmp_path),
        }
    )
    assert config.modelo == "gpt-5"
    assert config.dir_datos == tmp_path


def test_config_endpoint_local_no_exige_api_key():
    config = cargar_configuracion(
        entorno={
            "TUTOR_BASE_URL": "http://localhost:11434/v1",
            "TUTOR_MODEL": "gemma3:4b",
        }
    )
    assert config.base_url == "http://localhost:11434/v1"
    assert config.api_key == API_KEY_LOCAL
    assert config.modelo == "gemma3:4b"


def test_config_acepta_openai_base_url_y_prefiere_tutor_base_url():
    solo_openai = cargar_configuracion(entorno={"OPENAI_BASE_URL": "http://a/v1"})
    ambas = cargar_configuracion(
        entorno={"OPENAI_BASE_URL": "http://a/v1", "TUTOR_BASE_URL": "http://b/v1"}
    )
    assert solo_openai.base_url == "http://a/v1"
    assert ambas.base_url == "http://b/v1"


def test_config_endpoint_local_conserva_api_key_explicita():
    config = cargar_configuracion(
        entorno={"TUTOR_BASE_URL": "http://a/v1", "OPENAI_API_KEY": "sk-proxy"}
    )
    assert config.api_key == "sk-proxy"


def test_config_sin_key_sugiere_modelo_local():
    with pytest.raises(ErrorConfiguracion, match="TUTOR_BASE_URL"):
        cargar_configuracion(entorno={})


def test_config_sin_endpoint_usa_openai():
    assert cargar_configuracion(entorno={"OPENAI_API_KEY": "sk-x"}).base_url == ""
