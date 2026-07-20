# RULES — Reglas de trabajo y calidad de código

Estas reglas aplican a todo el código y documentación del repositorio.
Cualquier PR/commit que las viole no se integra.

## 1. Flujo de trabajo

1. **Nada de código sin HU.** Todo cambio de código responde a una tarea de una
   HU en `plan/`. Si surge trabajo nuevo, primero se agrega la tarea a la HU (o
   se crea una HU nueva).
2. **Documentar antes/durante, no después.** Decisiones de diseño y problemas
   encontrados van a `docs/HALLAZGOS.md` en el momento en que ocurren.
3. **Commits pequeños y descriptivos**, en español, en modo imperativo
   (`agrega validación de perfil`, `corrige parseo de respuesta del LLM`).
4. **La rama `main` siempre corre**: `uv run pytest` y `uv run ruff check .`
   deben pasar antes de cada commit.

## 2. Calidad de código (Python)

- **PEP 8, PEP 257 y PEP 484**: estilo, docstrings y type hints obligatorios en
  toda función pública.
- Funciones pequeñas (una responsabilidad); módulos con propósito único.
- Nombres claros en español para el dominio (`perfil`, `evaluacion`, `progreso`)
  y en inglés para lo técnico genérico cuando sea idiomático.
- **Sin números/textos mágicos**: constantes con nombre en `config.py`.
- **Errores explícitos**: nunca `except Exception: pass`. Toda excepción
  capturada se maneja o se relanza con contexto. Errores de API tienen tipos
  propios (`ErrorLLM`, `ErrorConfiguracion`).
- **Parseo defensivo**: toda respuesta del LLM se valida contra un esquema
  antes de usarse; si no valida, se reintenta o se falla con mensaje claro.
- **Logs útiles**: módulo `logging` (no `print`) para diagnóstico; `print`/Rich
  solo para la interfaz de usuario.

## 3. Seguridad

- **Cero secretos en el repo**: la API key vive en `.env` (gitignoreado);
  `.env.example` documenta las variables sin valores reales.
- No se registra (log) el contenido de la API key ni headers de autenticación.

## 4. Herramientas (configuradas en `pyproject.toml`)

| Herramienta | Rol | Comando |
|---|---|---|
| `ruff check` | Linter (pycodestyle, pyflakes, isort, bugbear, etc.) | `uv run ruff check .` |
| `ruff format` | Formateador (estilo único, sin discusiones) | `uv run ruff format .` |
| `mypy` | Verificación estática de tipos (modo estricto en `src`) | `uv run mypy src` |
| `pytest` | Pruebas unitarias e integración | `uv run pytest` |

## 5. Pruebas

- Toda función con lógica (validación, parseo, cálculo de progreso) tiene
  prueba unitaria. Ver estrategia completa en `docs/TESTING.md`.
- Las llamadas al LLM se prueban con **dobles (fakes/mocks)**; nunca se llama a
  la API real en la suite automatizada.
- Una HU no se marca como terminada sin sus pruebas en verde.

## 6. Definición de Hecho (DoD) por HU

- [ ] Todas las tareas de la HU marcadas.
- [ ] Criterios de aceptación de la HU verificados.
- [ ] Pruebas nuevas escritas y toda la suite en verde.
- [ ] `ruff check`, `ruff format --check` y `mypy` sin errores.
- [ ] Hallazgos/decisiones relevantes anotados en `docs/HALLAZGOS.md`.
- [ ] Docs actualizadas si cambió una interfaz (README, SPEC).
