from pathlib import Path

import pytest

from tutor.config import DIR_DATOS_POR_DEFECTO, MODELO_POR_DEFECTO, cargar_configuracion
from tutor.errores import ErrorConfiguracion


def test_config_sin_api_key_lanza_error_configuracion():
    with pytest.raises(ErrorConfiguracion, match="ANTHROPIC_API_KEY"):
        cargar_configuracion(entorno={})


def test_config_api_key_en_blanco_lanza_error_configuracion():
    with pytest.raises(ErrorConfiguracion):
        cargar_configuracion(entorno={"ANTHROPIC_API_KEY": "   "})


def test_config_lee_valores_por_defecto():
    config = cargar_configuracion(entorno={"ANTHROPIC_API_KEY": "sk-prueba"})
    assert config.api_key == "sk-prueba"
    assert config.modelo == MODELO_POR_DEFECTO
    assert config.dir_datos == Path(DIR_DATOS_POR_DEFECTO)


def test_config_respeta_overrides_de_entorno(tmp_path):
    config = cargar_configuracion(
        entorno={
            "ANTHROPIC_API_KEY": "sk-prueba",
            "TUTOR_MODEL": "claude-haiku-4-5-20251001",
            "TUTOR_DATA_DIR": str(tmp_path),
        }
    )
    assert config.modelo == "claude-haiku-4-5-20251001"
    assert config.dir_datos == tmp_path
