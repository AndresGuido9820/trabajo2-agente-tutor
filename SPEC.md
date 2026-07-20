# SPEC — Agente Tutor de Programación con LLMs

Trabajo 02 · Fecha de entrega: 2026-07-21 23:59 · 100 puntos.

## 1. Objetivo

Construir un agente interactivo que guíe a un estudiante en el aprendizaje de
fundamentos de programación, personalizando el curso según sus conocimientos
previos y objetivos (ciencia de datos, front, back, etc.), generando contenido
y evaluaciones con un LLM y llevando su progreso.

## 2. Alcance funcional (requisitos técnicos del enunciado)

### RF-1. Módulo de procesamiento de entradas
- RF-1.1 Evaluar capacidades y conocimientos actuales del estudiante.
- RF-1.2 Evaluar objetivos de aprendizaje (ciencia de datos, front, back, …).
- RF-1.3 Validar toda entrada del usuario (opciones fuera de rango, vacíos,
  tipos incorrectos) sin crashear.

### RF-2. Motor de generación de contenidos
- RF-2.1 Interfaz con una API de LLM (Anthropic Claude).
- RF-2.2 Generar el contenido educativo (temario del curso + lecciones).
- RF-2.3 Generar evaluaciones (quizzes por unidad) y calificarlas.
- RF-2.4 Llevar el progreso del estudiante (persistente entre sesiones).
- RF-2.5 Manejo de errores de API: timeouts, rate limits, respuestas mal
  formadas → reintentos con backoff y mensajes claros al usuario.

### RF-3. Interfaz de usuario
- RF-3.1 Interfaz de línea de comandos (CLI).
- RF-3.2 Mostrar resultados de evaluaciones y progreso.
- RF-3.3 Navegar por las unidades del curso **aunque su contenido aún no se
  haya generado** (se genera bajo demanda al entrar).
- RF-3.4 *(Bonus)* Complementar el contenido con imágenes generadas por IA.

## 3. Interfaces explícitas

### 3.1 CLI
```
uv run tutor                # flujo completo: perfil → curso → navegación
```
Menú principal: `[n] entrar a unidad n · [e] evaluación de la unidad ·
[p] ver progreso · [q] salir`.

### 3.2 Variables de entorno (`.env`)
| Variable | Requerida | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | sí | API key de Anthropic |
| `TUTOR_MODEL` | no (default `claude-sonnet-5`) | modelo a usar |
| `TUTOR_DATA_DIR` | no (default `./data`) | carpeta de perfiles/progreso |

### 3.3 Persistencia (JSON en `TUTOR_DATA_DIR`)
- `perfil.json` — perfil del estudiante (nivel, lenguaje, objetivo).
- `curso.json` — temario y lecciones generadas (cache).
- `progreso.json` — unidades vistas, resultados de evaluaciones.

Los esquemas exactos se definen en cada HU y se validan al cargar
(archivos corruptos → error claro, nunca crash silencioso).

### 3.4 Contrato con el LLM
Toda generación estructurada (temario, quiz, calificación) pide **JSON** con
esquema explícito en el prompt y se valida al recibir; a lo sumo
`MAX_REINTENTOS_PARSEO` reintentos antes de fallar con `ErrorLLM`.

## 4. Criterios de evaluación del entregable (rúbrica del curso)

### 4.1 Implementación técnica (40 %)
- Calidad del código, organización y documentación (RULES.md aplicado).
- Manejo adecuado de errores y validación de entradas del usuario.
- Integración efectiva de API y procesamiento de respuestas.
- Diseño de interfaz de usuario y usabilidad.

### 4.2 Ingeniería de prompts (30 %)
- Calidad y efectividad de los prompts (versionados en `src/tutor/prompts.py`).
- Personalización según conocimientos previos e intereses del estudiante.
- Uso creativo de técnicas: rol/persona, few-shot, salida estructurada,
  encadenamiento (perfil → temario → lección → quiz).

### 4.3 Calidad del curso (20 %)
- Coherencia, desarrollo y consistencia entre unidades.
- Lenguaje motivador y valor de entretenimiento.

### 4.4 Documentación y reflexión (10 %)
- Decisiones de diseño documentadas (`docs/HALLAZGOS.md` + reporte).
- Reflexión sobre capacidades y limitaciones de LLMs.
- Desafíos y soluciones.

## 5. Entregables

| # | Entregable | Dónde vive |
|---|---|---|
| E1 | Código fuente documentado + instrucciones de configuración | este repo (`README.md`) |
| E2 | Video demo 5–7 min, todos los miembros hablan con rótulo de quién habla, mostrando cursos para **distintos perfiles** | `entregables/video/` (guion en `entregables/GUION-VIDEO.md`) |
| E3 | Reporte técnico 1000–1500 palabras: enfoque, desafíos, perspectivas, contribución individual | `entregables/REPORTE.md` |
| E4 | ≥ 2 cursos de muestra, perfiles distintos y **lenguajes distintos** | `entregables/cursos-muestra/` |

## 6. Pruebas de aceptación (checklist final antes de entregar)

Cada prueba se ejecuta manualmente y se marca; las automatizables tienen
además prueba en `tests/` (ver `docs/TESTING.md`).

- [ ] **PA-01** Al iniciar sin perfil, el tutor hace el cuestionario de perfil
  (nivel, experiencia, objetivo, lenguaje) y lo guarda en `perfil.json`.
- [ ] **PA-02** Entradas inválidas en el cuestionario (opción inexistente,
  vacío, texto donde va número) reintentan con mensaje claro, sin traceback.
- [ ] **PA-03** Con el perfil, el tutor genera un temario de 5–8 unidades
  coherente con el objetivo declarado (p. ej. datos → Python/pandas al final).
- [ ] **PA-04** Se puede navegar por todas las unidades desde el menú aunque
  ninguna lección haya sido generada aún; al entrar, se genera bajo demanda.
- [ ] **PA-05** Cada unidad ofrece una evaluación; al responderla se muestra
  calificación con retroalimentación por pregunta.
- [ ] **PA-06** El progreso (unidades vistas, notas) persiste: cerrar y reabrir
  el tutor conserva el estado y lo muestra en `[p]`.
- [ ] **PA-07** Sin `ANTHROPIC_API_KEY` el programa termina con un mensaje de
  configuración claro (no traceback).
- [ ] **PA-08** Con la red caída o error 429/5xx de la API, el tutor reintenta
  con backoff y, si agota reintentos, informa el error sin perder el progreso.
- [ ] **PA-09** Respuesta del LLM mal formada (JSON inválido) → reintento
  automático; si persiste, mensaje de error claro.
- [ ] **PA-10** Dos perfiles distintos (p. ej. "cero programación → front con
  JS" y "sabe Excel → ciencia de datos con Python") producen cursos claramente
  distintos en temario, lenguaje y tono. (Base de E4.)
- [ ] **PA-11** `uv sync && uv run tutor` funciona en una máquina limpia
  siguiendo solo el README.
- [ ] **PA-12** `uv run pytest`, `uv run ruff check .` y `uv run mypy src`
  pasan sin errores.
- [ ] **PA-13** No hay secretos en el repo (`git log -p | grep -i api_key`
  limpio; `.env` ignorado).
- [ ] **PA-14** *(Bonus)* Las lecciones incluyen imágenes generadas por IA
  referenciadas en el contenido.

## 7. Fuera de alcance

- Interfaz web, autenticación multiusuario, base de datos relacional,
  despliegue en la nube. (Simplicidad primero: CLI + JSON local.)
