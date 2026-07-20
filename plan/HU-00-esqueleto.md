# HU-00 — Esqueleto del proyecto y calidad

**Como** equipo de desarrollo **quiero** un proyecto configurado con
dependencias, linters, tipos y pruebas **para** que toda HU posterior se
construya sobre una base con puertas de calidad automáticas.

## Criterios de aceptación

- `uv sync` instala todo en una máquina limpia.
- `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y
  `uv run mypy src` corren en verde.
- `.env.example` documenta las variables; `.env` y `data/` están gitignoreados.
- Existe el paquete `tutor` con un punto de entrada `uv run tutor` que arranca.

## Tareas

- [x] `pyproject.toml`: metadatos, deps (`anthropic`, `rich`, `python-dotenv`),
      dev-deps (`pytest`, `ruff`, `mypy`), script `tutor`, config de ruff/mypy.
- [x] `.gitignore` (venv, `.env`, `data/`, `__pycache__`, cachés de tools).
- [x] `.env.example` con `ANTHROPIC_API_KEY`, `TUTOR_MODEL`, `TUTOR_DATA_DIR`.
- [x] Paquete `src/tutor/` con `__init__.py`, `config.py` (carga de env,
      constantes, `ErrorConfiguracion`) y `__main__.py` mínimo.
- [x] Test trivial de `config.py` (falta de API key → `ErrorConfiguracion`).
- [x] Verificar las 4 puertas de calidad.

## Pruebas

- `test_config_sin_api_key_lanza_error_configuracion`
- `test_config_lee_valores_por_defecto`
