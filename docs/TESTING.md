# TESTING — Estrategia de pruebas

Cómo se irá testeando todo, en qué orden y con qué herramientas. Regla madre
(RULES.md §5): **ninguna HU se cierra sin sus pruebas en verde** y las llamadas
al LLM **nunca** golpean la API real en la suite automatizada.

## 1. Pirámide del proyecto

| Nivel | Qué cubre | Herramienta | Cuándo corre |
|---|---|---|---|
| Unitarias | validación de entradas, parseo de JSON del LLM, cálculo de progreso, persistencia | pytest | en cada cambio (`uv run pytest`) |
| Integración (con LLM falso) | flujo perfil→temario→lección→quiz con un `ClienteLLMFalso` que devuelve respuestas fijas/mal formadas | pytest | en cada cambio |
| Humo con API real | 1 script manual que genera un temario real y valida el esquema | script `scripts/humo_llm.py` | manual, antes de grabar demo/entrega |
| Aceptación | checklist PA-01…PA-14 de `SPEC.md` | manual | al cerrar cada HU relacionada y antes de entregar |
| Estática | estilo, bugs comunes, tipos | ruff + mypy | en cada cambio |

## 2. Diseño para testeabilidad

- El cliente LLM es una **interfaz** (`ClienteLLM` con método `generar`).
  El código de negocio recibe la interfaz, nunca crea el cliente real → en
  tests se inyecta `ClienteLLMFalso` (respuestas programables, contador de
  llamadas, modo "falla N veces").
- La persistencia recibe una ruta de directorio → en tests se usa `tmp_path`
  de pytest, nunca el `data/` real.
- La CLI separa **lectura de entrada** de **lógica de validación**: la
  validación es función pura y se testea directo; la lectura interactiva se
  testea con `monkeypatch` de `input`.

## 3. Plan de pruebas por HU (se detalla en cada HU)

- **HU-01 Perfil**: validación de cada campo (opción fuera de rango, vacío,
  texto→número), serialización/carga de `perfil.json`, archivo corrupto.
- **HU-02 Cliente LLM**: reintentos ante 429/5xx/conexión (cliente falso que
  falla N veces), sin reintento ante 401, timeout, error tras agotar intentos.
- **HU-03 Temario/lecciones**: parseo de JSON válido, inválido (reintento),
  esquema incompleto (falta campo → error claro), cache de lecciones.
- **HU-04 Evaluaciones**: parseo del quiz, calificación (todas correctas,
  todas malas, mixto), retroalimentación presente.
- **HU-05 Progreso**: persistencia entre "sesiones" (dos instancias sobre el
  mismo dir), unidad marcada como vista, mejor nota conservada.
- **HU-06 CLI/navegación**: mapeo de opción de menú → acción, opciones
  inválidas, navegación a unidad sin contenido dispara generación (con fake).

## 4. Convenciones

- Un archivo de test por módulo: `tests/test_<modulo>.py`.
- Nombres descriptivos en español: `test_perfil_rechaza_opcion_fuera_de_rango`.
- Arrange-Act-Assert; un comportamiento por test.
- Fixtures compartidas en `tests/conftest.py` (perfil de ejemplo,
  `ClienteLLMFalso`, dir temporal de datos).

## 5. Puertas de calidad (antes de cada merge a develop)

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

Las cuatro deben pasar. Antes de la entrega final se corre además el script de
humo con API real y el checklist PA completo de `SPEC.md`.
