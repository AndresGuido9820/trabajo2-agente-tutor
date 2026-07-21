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
- RF-2.1 Interfaz con una API de LLM (OpenAI GPT).
- RF-2.2 Generar el contenido educativo (temario del curso + lecciones).
- RF-2.3 Generar evaluaciones (quizzes por unidad) y calificarlas.
- RF-2.4 Llevar el progreso del estudiante (persistente entre sesiones).
- RF-2.5 Manejo de errores de API: timeouts, rate limits, respuestas mal
  formadas → reintentos con backoff y mensajes claros al usuario.

### RF-3. Interfaz de usuario
- RF-3.1 Interfaz de línea de comandos (CLI) **y** interfaz web local
  (`uv run tutor-web`, FastAPI single-user sobre el mismo `Agente`). La web
  es **chat-total**: toda la experiencia ocurre en una sola conversación
  (header + chat + panel del plan), sin cambios de pantalla.
- RF-3.1b **Creación conversacional del curso**: el estudiante escribe qué
  quiere aprender; el asesor resume lo entendido, pregunta lo que falta
  (nivel, experiencia, lenguaje), propone un temario y solo crea el curso
  cuando el estudiante confirma. Al confirmar se guarda el plan en
  `curso.md`, visible y descargable desde una mini-ventana.
- RF-3.1c **Panel de objetivos vivo**: cada unidad muestra su objetivo; al
  completar la lección en el chat, el objetivo se tacha y aparece "Repasar
  en el chat" (reinicia esa lección en la misma conversación).
- RF-3.2 Mostrar resultados de evaluaciones y progreso.
- RF-3.3 Navegar por las unidades del curso **aunque su contenido aún no se
  haya generado** (se genera bajo demanda al entrar).
- RF-3.3b La lección es **conversacional**: al entrar a la unidad se genera
  primero su guion (objetivos + paso a paso PRIMM, cacheado) y el tutor la
  imparte charlando: un paso por turno, reaccionando a las respuestas del
  estudiante (predicciones, ejercicios) antes de avanzar.
- RF-3.3c **Guía interactiva por objetivos** (experiencia principal en la
  web): cada unidad genera una guía de 3-5 secciones (una por objetivo) con
  contenido específico y un checkpoint; responder da puntos (10/5/0 según
  intento), fallar da primero una pista socrática. La evaluación final con
  nota ≥ 70 aprueba la unidad (+30 pts) y **desbloquea la siguiente**; si no,
  se abre un **conversatorio socrático** de dudas antes de reintentar.
- RF-3.4 Charla con el tutor: tras leer una lección, el estudiante puede
  hacerle preguntas libres; el tutor responde en contexto con guía socrática
  (pistas, no soluciones completas; escape ante el "no sé" repetido).
- RF-3.5 *(Bonus)* Complementar el contenido con imágenes generadas por IA.

## 3. Interfaces explícitas

### 3.1 CLI y web
```
uv run tutor                # CLI: perfil → curso → navegación
uv run tutor-web            # web en http://127.0.0.1:8017 (API en plan/HU-11)
```
Menú principal: `[n] entrar a unidad n · [e] evaluación de la unidad ·
[p] ver progreso · [q] salir`.

### 3.2 Variables de entorno (`.env`)
| Variable | Requerida | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | sí | API key de OpenAI |
| `TUTOR_MODEL` | no (default `gpt-5-mini`) | modelo a usar |
| `TUTOR_DATA_DIR` | no (default `./data`) | carpeta de perfiles/progreso |

### 3.3 Persistencia (SQLite en `TUTOR_DATA_DIR/tutor.db`)
- Tabla `curso` — el diseño (lenguaje, plan en Markdown, versión de prompts,
  metadata de creación). `curso.md` es la copia legible/descargable.
- Tabla `clases` — una fila por clase: definición (título, objetivo,
  subtemas), el **prompt/guion** con el que el tutor la imparte, el
  contenido generado y su metadata de actualización.
- Tablas `perfil`, `progreso` (documentos versionados) y `chat`
  (historial por conversación). Migración automática desde los JSON del
  formato anterior.

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
- [ ] **PA-07** Sin `OPENAI_API_KEY` el programa termina con un mensaje de
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
- [ ] **PA-14** Durante una lección, pedir "dame la solución completa del
  reto" produce una pista/pregunta guía, NO la solución; tras insistir
  con "no sé" dos veces, el tutor muestra un paso resuelto concreto.
- [ ] **PA-16** Al entrar a una unidad se muestran los objetivos y la ruta de
  pasos; la lección avanza un paso por respuesta del estudiante, reacciona a
  respuestas erradas con corrección amable, y `salir` pausa sin perder el
  guion (reentrar no vuelve a llamar al LLM para generarlo).
- [ ] **PA-17** En la web: la guía muestra objetivos y secciones; fallar un
  checkpoint da una pista que NO revela la respuesta y permite reintentar;
  los puntos suben (10 primer intento, 5 segundo) y persisten al recargar.
- [ ] **PA-18** Las unidades posteriores aparecen bloqueadas 🔒 hasta aprobar
  la anterior (≥ 70); reprobar la evaluación ofrece el conversatorio de
  dudas y el reintento; aprobar desbloquea la siguiente y suma 30 pts. Las
  respuestas correctas de checkpoints y quiz nunca llegan al navegador antes
  de calificar (verificar en la pestaña Red).
- [ ] **PA-19** La creación es una conversación: ante "hazme un curso de X"
  el asesor pregunta (p. ej. nivel) y propone ANTES de crear; solo el "ya,
  dale" crea el curso, guarda `curso.md` y muestra el plan en el panel.
- [ ] **PA-20** Al terminar una lección en el chat, su objetivo queda tachado
  en el panel; "↩ Repasar en el chat" la reinicia en la misma conversación;
  el quiz y el conversatorio ocurren dentro del chat, sin cambiar de vista.
- [ ] **PA-15** *(Bonus)* Las lecciones incluyen imágenes generadas por IA
  referenciadas en el contenido.

## 7. Fuera de alcance

- Interfaz web, autenticación multiusuario, base de datos relacional,
  despliegue en la nube. (Simplicidad primero: CLI + JSON local.)
