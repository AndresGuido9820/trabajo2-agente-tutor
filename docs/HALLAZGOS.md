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

## 2026-07-20 — HU-10: lección conversacional guiada por guion

**Contexto:** retroalimentación de revisión: las lecciones debían ser
"habladitas" con el chat, generando antes los objetivos y el paso a paso.

**Hallazgos:**

1. **Plan y ejecución separados**: generar primero el guion (objetivos +
   pasos PRIMM como JSON validado y cacheado en `curso.json`) y luego
   conversarlo un paso por turno resolvió los dos riesgos del chat libre:
   que la conversación divague (el guion la ancla) y el costo (el guion se
   genera una vez; cada turno es una llamada corta).
2. En el humo real, el tutor reaccionó a una predicción errada ("creo que
   imprime 10") corrigiendo con amabilidad y explicando el porqué antes de
   avanzar — el comportamiento pedido por PRIMM sin instrucciones extra.
3. Las lecciones Markdown de HU-03 se conservan para exportar los cursos de
   muestra (E4); la experiencia dentro de la app es la conversacional.

**Decisión/acción:** avance determinista (una respuesta = un paso) en vez de
dejar que el LLM decida cuándo avanzar: más predecible, testeable y barato.
El estado de la conversación es efímero (sesión); lo durable es el guion.

---

## 2026-07-20 — Hotfix web: 405 en iniciar lección/quiz

**Contexto:** al probar la web en el navegador, "Estudiar" y "Evaluarme"
fallaban con 405 Method Not Allowed.

**Hallazgo:** bug del front: el helper `api()` solo usaba POST cuando había
body, y los endpoints de iniciar lección y pedir quiz no llevan body → el
navegador enviaba GET. Las pruebas del API (TestClient) no lo detectaron
porque prueban el back, no el JS del front. Lección: el front necesita su
propia pasada E2E; se agregó un script que replica las peticiones exactas
del front contra un servidor real (15 chequeos, flujo completo de un
estudiante: perfil → temario → lección conversada → quiz → progreso →
errores 404/409).

**Decisión/acción:** `api(ruta, cuerpo, metodo)` con POST explícito;
`white-space: pre-wrap` en preguntas del quiz para no colapsar el código
multilínea de los enunciados.

---

## 2026-07-20 — HU-12: guía interactiva, puntos y progresión con candado

**Contexto:** retroalimentación de visión 1.0: guías súper específicas por
objetivos donde el estudiante responde y "va ganando", evaluación que
decide el paso a la siguiente unidad, y conversatorio socrático si reprueba.

**Hallazgos:**

1. La estructura "una sección = un objetivo + un checkpoint" hace la guía
   verificable: el validador exige 3-5 secciones con checkpoint completo
   (pista socrática + explicación), y la calificación de checkpoints es
   local (el LLM solo genera; nunca califica).
2. La pista socrática como campo SEPARADO del checkpoint (generada junto
   con la pregunta) resultó mejor que pedirla en caliente: cero latencia al
   fallar y el prompt puede exigir "prohibido revelar cuál opción es".
3. En el E2E real el flujo de reprobar funcionó completo: nota 25 → unidad
   siguiente sigue bloqueada → el conversatorio abrió preguntando por el
   concepto fallado más fundamental → reintento disponible.
4. Gamificación mínima pero efectiva: puntos por checkpoint (10/5/0 según
   intento) + 30 por aprobar, persistidos en `progreso.json` y visibles en
   el header. Sin insignias ni rachas: alcance contenido.

**Decisión/acción:** el candado vive en el `Agente` (una sola fuente de
verdad) y la web lo mapea a HTTP 403; la CLI lo muestra como error amable
sin tumbar la sesión.

---

## 2026-07-20 — HU-13: adopción de patrones de los mejores OSS

**Contexto:** encuesta de referentes open source (informe con fuentes en
`docs/INVESTIGACION-OSS.md`) y adopción de los 5 patrones de mejor ratio
impacto/esfuerzo.

**Hallazgos:**

1. **Pyodide (futurecoder)**: ejecutar Python en el navegador vía WASM
   elimina el backend de ejecución — la pieza más cara de cualquier
   plataforma de código — a cambio de ~8 MB de descarga la primera vez.
   Lazy-load al primer clic lo hace gratis para quien no lo usa.
2. **Gamificación con evidencia y sin dark patterns**: adoptamos racha
   diaria y XP (los A/B de Duolingo les atribuyen +30 % de finalización) y
   descartamos explícitamente vidas y ligas (frustración documentada).
   Nuestro 10/5/0 por intento resultó ser el mismo patrón `autoPoints` de
   PrairieLearn — validación independiente del diseño de HU-12.
3. **Variantes al reintentar (PrairieLearn)**: bastó pasar los enunciados
   previos al prompt del quiz; sin esto, aprobar el reintento medía memoria
   de la letra correcta, no dominio.
4. **Theory-of-mind (tutor-gpt/Bloom)**: el conversatorio ahora recibe el
   historial de intentos y debe inferir el malentendido antes de preguntar
   (thought → response). Cambio de ~10 líneas con impacto directo en la
   calidad de la tutoría.
5. Operativo: al relanzar el servidor tras un merge hay que verificar que
   el proceso viejo soltó el puerto; un bind fallido silenciado deja código
   viejo sirviendo (se manifestó como 404 en endpoints nuevos).

**Decisión/acción:** lo no adoptado (checkpoints de código con tests en
Pyodide, grafo de conceptos de Exercism, repaso espaciado FSRS/HLR, modelo
BKT del estudiante, Parsons adaptativos) queda como trabajo futuro citado
en el reporte.

---

## 2026-07-20 — HU-14: renovación UX e interacción total con el agente

**Contexto:** retroalimentación de visión ("el alumno interactúa con el
agente e ilustra mejor, como los Artifacts de Claude") + auditoría contra
guías abiertas de producto/UX (`docs/INVESTIGACION-UX.md`).

**Hallazgos:**

1. **Mini-artefactos**: el LLM genera páginas HTML autocontenidas e
   interactivas sorprendentemente bien (humo real: 12.8 KB, interactiva, sin
   recursos externos, con el mismo ejemplo de la sección). El
   `iframe sandbox="allow-scripts"` da el aislamiento de los Artifacts sin
   infraestructura: sin red, sin acceso al DOM de la app.
2. La mayor deuda UX era la **espera opaca**: NN/g exige progreso con
   expectativa para >10 s; ahora todas las generaciones tienen loader por
   fases + tiempo estimado + skeleton, la guía es no bloqueante y el quiz se
   prefetch-ea en la última sección.
3. **Doble ganancia inesperada**: al basar el quiz en la guía (en vez de
   regenerar la lección Markdown), se ahorra ~1 min por evaluación Y la
   evaluación queda alineada con lo que el estudiante realmente estudió.
4. Accesibilidad barata y de alto impacto: paleta AA verificada, badges con
   texto (no solo emoji/color), `:focus-visible`, `aria-live`,
   `prefers-reduced-motion` — todo CSS/HTML, cero dependencias.

**Decisión/acción:** streaming de generación queda como el siguiente salto
de percepción (requiere SSE en `ClienteLLM`); documentado como trabajo
futuro en el reporte.

---

## 2026-07-20 — HU-16: todo en un chat + timeout de generaciones largas

**Contexto:** rediseño a chat-total (creación conversacional con propuesta y
confirmación, plan en `curso.md`, estudio con objetivos que se tachan,
repaso, quiz y conversatorio inline; nunca se sale del chat).

**Hallazgos:**

1. El protocolo `{mensaje, listo, perfil}` en JSON por turno hace confiable
   la creación conversacional: el modelo conversa libremente en "mensaje" y
   la máquina solo actúa cuando `listo=true` con perfil validado. En el E2E
   real preguntó nivel, propuso temario y solo creó al "ya, dale" (3 turnos).
2. **Bug de latencia**: `TIMEOUT_API_SEGUNDOS = 60` convertía generaciones
   exitosas-pero-lentas (artefactos: 1-3 min con modelos razonadores) en
   ciclos de reintento inútiles — el SDK reporta el timeout como
   `APIConnectionError` ("no se pudo conectar"), lo que despista. Subido a
   180 s; los reintentos quedan para fallas reales.
3. La lección conversada de HU-10 (guion + turno a turno) encajó intacta
   como motor del estudio en chat: `turno_estudio` solo añade la unidad
   actual y el marcado de completadas persistente.

**Decisión/acción:** el plan `.md` es un entregable visible del producto
(mini-ventana con descarga), no solo un artefacto interno.

---

## 2026-07-20 — HU-19: el diseño del curso pasa a SQLite

**Contexto:** retroalimentación de revisión: el diseño del curso debe estar
en una BD, con el prompt de cada clase y su metadata.

**Hallazgos:**

1. El esquema natural salió del dominio: `curso` (diseño + plan_md +
   versión de prompts), `clases` (título/objetivo/subtemas + **guion** — el
   prompt paso a paso con el que el tutor da esa clase — + contenido
   generado + `actualizado_en`), `perfil`, `progreso`, `chat` por canal.
2. Mantener las MISMAS firmas de cargar/guardar hizo la migración de código
   casi indolora: solo 5 pruebas referenciaban nombres de archivo.
3. Ganancias colaterales: escrituras transaccionales (adiós tmp+rename),
   "rehacer perfil" ya no puede borrar de más (DELETE selectivo), y el chat
   por canal es un simple WHERE.
4. La migración legacy es best-effort e idempotente (si la BD existe, no
   corre): los datos de los usuarios que probaron versiones previas
   sobreviven sin pasos manuales.

**Decisión/acción:** documentos JSON dentro de columnas para perfil/progreso
(estructuras pequeñas y versionadas) y columnas de primera clase para lo que
se consulta (clases, chat). SQLite de la stdlib: cero dependencias nuevas.

---

## 2026-07-20 — HU-20: multicurso y diseño estructurado

**Contexto:** menú "Mis cursos", cada curso aislado, y el diseño como
información estructurada para el LLM (el `.md` pasa a ser solo la vista).

**Hallazgos:**

1. **Un directorio + una BD por curso** (`cursos/<id>/tutor.db`) resultó más
   simple y seguro que añadir `curso_id` a todas las tablas: el stack
   monocurso completo funciona intacto por curso, y borrar/respaldar un
   curso es mover una carpeta.
2. Las **propiedades de compatibilidad** en `_Estado` (agente/quizzes/
   creacion/ruta_db delegando al curso activo) permitieron el multicurso
   sin tocar ningún endpoint existente.
3. La **edición estructurada del diseño** reutiliza `validar_temario` como
   contrato: lo que el humano edita pasa por las mismas reglas que lo que
   genera el LLM, así los prompts siempre reciben datos limpios; el plan
   `.md` se regenera desde la estructura (una sola fuente de verdad).

**Decisión/acción:** el editor de `.md` crudo se retiró del front (quedaba
como segunda fuente de verdad divergente); el endpoint permanece para
compatibilidad.

---

<!-- Plantilla:

## 2026-07-21 — Segunda tanda v2 (HU-29…39): 11 mejoras ejecutadas

**Contexto:** ejecución completa de la segunda tanda del plan v2 en un día,
cada HU en su rama `feature/*` con merge `--no-ff` a develop y compuertas
(ruff, mypy estricto, pytest, build del front) en verde. La suite pasó de
179 a 229 pruebas.

**Hallazgos:**

- *Contraste AA no viene gratis con Mantine* (HU-38): axe-core encontró
  violaciones serias reales — los `Progress` sin nombre accesible, el
  `dimmed` y el texto de la variante `light` (badges 🔥/⭐) por debajo de
  4.5:1 incluso subiendo al tono 9. Se corrigió con variables CSS a medida
  en `global.css` y `primaryShade {light: 7}`; la auditoría quedó en 0
  violaciones serias/críticas y el script (`scripts/a11y_playwright.py`)
  queda como compuerta repetible.
- *Streamear un campo de un JSON en vivo requiere parser incremental*
  (HU-35): el turno con decisión `{avanza, mensaje}` no puede esperar el
  JSON completo. `ExtractorCampoJSON` re-escanea el buffer en cada
  fragmento (maneja `\"`, `\n` y `\uXXXX` partidos entre trozos) y el
  JSON completo se valida al final con el MISMO `_cerrar_turno` que la
  variante clásica: un solo lugar decide el avance. Validado contra la API
  real (deltas limpios extraídos del JSON en vivo).
- *La desconexión del cliente no debe abortar el turno* (HU-35/HU-34): el
  generador SSE captura `GeneratorExit` y termina/persiste el turno
  server-side; el E2E de HU-34 (matar el servidor, ver "No enviado",
  revivir, reintentar) pasó contra el servidor real.
- *El agente cachea estado en memoria* (HU-31/32): escribir la BD "por
  detrás" de un servidor vivo no se refleja hasta reiniciar; los tests que
  siembran datos crean un `crear_app` nuevo (reinicio simulado) en vez de
  parchear el caché.
- *Aciertos por concepto son una aproximación* (HU-31): el quiz no
  persiste sus preguntas, así que "acertado" = conceptos de la unidad
  menos los fallados del intento; documentado en `estadisticas()`.
- *Carriles de modelo* (HU-39): separar chat (`TUTOR_MODEL_CHAT`) de
  generación estructurada baja latencia sin tocar la calidad del diseño;
  el registro `llm_uso` es global (`data/uso.db`) porque el costo es del
  operador, no del curso.

**Decisión/acción:** el repaso espaciado usa intervalos fijos 1-3-7 (no
FSRS) y el streaming cubre solo `/api/estudio` con fallback clásico en el
front — alcance documentado en cada HU.

## AAAA-MM-DD — Título corto

**Contexto:** qué se estaba haciendo (HU-XX).

**Hallazgo:** qué se descubrió (bug, limitación del LLM, sorpresa de la API).

**Decisión/acción:** qué se hizo y por qué; alternativas descartadas.
-->
