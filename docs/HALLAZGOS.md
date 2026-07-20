# HALLAZGOS — Bitácora de desarrollo

Registro cronológico de decisiones, problemas y aprendizajes. Cada entrada:
fecha, contexto, hallazgo y decisión/acción. Este archivo alimenta la sección
de "desafíos y soluciones" del reporte técnico (10 % de la nota).

---

## 2026-07-20 — Arranque del proyecto

**Contexto:** definición de stack y arquitectura (ver `docs/INVESTIGACION.md`).

**Hallazgos / decisiones:**

1. **Sin framework de agentes.** El flujo es determinista (perfil → temario →
   lección → quiz), así que LangChain/CrewAI agregan dependencia y magia sin
   beneficio. Orquestación propia de ~1 módulo. *Trade-off aceptado:* si el
   proyecto creciera a tool-calling libre, habría que reevaluar.
2. **JSON por prompt + validación propia** en vez de tool-use forzado:
   portable y explícito; el costo es escribir validadores a mano, que además
   son el material perfecto para pruebas unitarias.
3. **Lecciones bajo demanda con cache.** Cumple el requisito de navegar
   unidades no generadas y reduce costo de tokens en demos.
4. **Python 3.14 local vs. 3.12 mínimo declarado:** se desarrolla en 3.14 pero
   `requires-python = ">=3.12"` para no exigir bleeding edge al calificador.
5. **Git Flow:** `main` (estable/entregas) ← `develop` (integración) ←
   `feature/hu-XX-*` (una rama por HU), merges con `--no-ff` para conservar
   la historia de cada HU. Commits en español, sin co-autores.

---

## 2026-07-20 — Cambio de proveedor: Anthropic → OpenAI

**Contexto:** antes de implementar la HU-02 (cliente LLM) se decidió usar la
API de OpenAI en lugar de la de Anthropic (disponibilidad de crédito del
equipo).

**Hallazgo:** el costo del cambio fue casi nulo porque el diseño ya aislaba el
proveedor detrás de la interfaz `ClienteLLM` y centralizaba constantes en
`config.py`: solo se tocaron la dependencia (`openai` por `anthropic`), la
env var (`OPENAI_API_KEY`), el modelo por defecto (`gpt-5-mini`) y la
documentación. Cero cambios en `perfil.py`, `models.py` o las pruebas de
lógica.

**Decisión/acción:** validada la regla de diseño "el código de negocio nunca
conoce al proveedor"; se mantiene para la HU-02. Los errores tipados del SDK
`openai` (`APIConnectionError`, `RateLimitError`, `APIStatusError`) mapean
1:1 con la estrategia de reintentos ya especificada.

---

## 2026-07-20 — HU-02: cliente LLM

**Contexto:** implementación del cliente OpenAI con reintentos y `pedir_json`.

**Hallazgos:**

1. La cuenta nueva de OpenAI devolvía `429 insufficient_quota` aun con key
   válida: el crédito de API es independiente de ChatGPT Plus. Se resolvió
   cargando saldo en Billing. Nota: ese 429 no es transitorio, pero el SDK lo
   reporta como `RateLimitError`; se acepta el costo de 3 reintentos en ese
   caso raro a cambio de mantener simple la regla "429 ⇒ reintentar".
2. mypy estricto marca `int ** int` como `Any` (typeshed: puede dar `float`
   con exponente negativo). Solución: base flotante explícita `2.0**intento`.
3. Los tests que comparten dobles (`ClienteLLMFalso`, `SDKFalso`) necesitaron
   `tests/__init__.py` para importar desde `conftest` como paquete.
4. La prueba de humo real confirmó el contrato completo: `gpt-5-mini` respeta
   la instrucción "responde SOLO este JSON" y `pedir_json` valida y convierte
   sin reintentos en el caso feliz.

**Decisión/acción:** inyección de dependencias en `ClienteOpenAI` (SDK y
función de espera) para probar reintentos sin red ni demoras reales.

---

## 2026-07-20 — HU-03: investigación pedagógica y prompts v2

**Contexto:** antes de fijar los prompts definitivos se investigó en fuentes
de computing education y tutores LLM (informe completo en
`docs/INVESTIGACION-PEDAGOGIA.md`).

**Hallazgos:**

1. Los prompts v1 ("explica y pon un ejemplo") ignoraban evidencia clave:
   PRIMM (predecir antes de explicar), worked examples con subgoal labeling,
   y la "máquina nocional" de Sorva. Los prompts v2 codifican esa estructura
   como secciones obligatorias de la lección.
2. Los LLM no generan distractores realistas espontáneamente (literatura de
   2025-2026): hay que inyectarles un banco de misconceptions documentadas.
   Se agregó `MISCONCEPTIONS` en `prompts.py`, compartido por lección (para
   desmontarlas) y quiz (para encarnarlas en distractores).
3. El CoT aumenta la confianza del modelo incluso cuando se equivoca, así
   que el prompt del quiz exige verificación independiente: trazar el código
   y derivar la salida ANTES de escribir opciones, y re-resolver desde cero.
4. Humo real con perfil "Excel → datos": el temario insertó pandas/CSV en
   unidades tempranas con títulos tipo "Variables y tipos: tus celdas de
   Excel, pero programables", y la lección 1 salió con 824 palabras,
   predicción inicial y subgoal labels. Prompts v2 validados.

**Decisión/acción:** `PROMPTS_VERSION = 2`; los cursos de muestra citarán la
versión. La especificación pedagógica vive en el doc de investigación y los
prompts son su implementación.

---

## 2026-07-20 — HU-07: respuestas vacías de gpt-5 y exportación de cursos

**Contexto:** al exportar el primer curso de muestra, el quiz de la unidad 1
falló con "La API devolvió una respuesta vacía".

**Hallazgo:** los modelos de la familia gpt-5 gastan tokens de razonamiento
DENTRO de `max_completion_tokens`; con el límite en 4096 y un prompt largo
(quiz con verificación), el razonamiento podía consumir todo el presupuesto y
el contenido llegaba vacío. Además ocurre de forma intermitente, así que no
basta con subir el límite.

**Decisión/acción:** doble mitigación en HU-02/config: `MAX_TOKENS_RESPUESTA`
sube a 16384 y la respuesta vacía se trata como error transitorio
reintentable (`_RespuestaVacia` interno en `llm.py`). También se observaron
errores de conexión intermitentes durante la exportación larga que los
reintentos con backoff absorbieron sin intervención — la estrategia de HU-02
pagó su costo.

---

## 2026-07-20 — HU-09: charla socrática con el tutor

**Contexto:** retroalimentación de revisión: el agente debía sentirse como un
asistente interactivo de aprendizaje, no solo un generador de cursos. Se
agregó el modo charla tras cada lección.

**Hallazgos:**

1. Los guardrails de Khanmigo (investigados en HU-03) funcionaron a la
   primera con `gpt-5-mini` en la prueba real: ante "dame la solución
   completa del mini-reto" respondió con pistas y una pregunta de vuelta;
   ante el segundo "no sé" mostró UN paso resuelto (con tabla de máquina
   nocional incluida, heredada del system compartido) y pidió continuar.
2. El historial multi-turno se resolvió sin cambiar la interfaz `ClienteLLM`
   (un solo método `generar`): la transcripción va dentro del prompt, acotada
   a `MAX_TURNOS_CHARLA` turnos. Suficiente para charlas de estudio; un chat
   largo requeriría mensajes nativos del API.

**Decisión/acción:** historial por unidad solo en memoria (no se persiste):
la charla es efímera por diseño; lo durable es el progreso.

---

<!-- Plantilla:

## AAAA-MM-DD — Título corto

**Contexto:** qué se estaba haciendo (HU-XX).

**Hallazgo:** qué se descubrió (bug, limitación del LLM, sorpresa de la API).

**Decisión/acción:** qué se hizo y por qué; alternativas descartadas.
-->
