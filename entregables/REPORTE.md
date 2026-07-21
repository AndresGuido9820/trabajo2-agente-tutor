# Reporte técnico — Agente Tutor de Programación con LLMs

Trabajo 02 · Curso: Normalización: aplicaciones de LLMs y Agentes para la
enseñanza de la programación básica.

## 1. Enfoque y arquitectura

Construimos un agente que enseña fundamentos de programación adaptándose al
estudiante, con una experiencia **chat-total** en la web: pedir el curso es
una conversación (el asesor resume lo que entendió, pregunta el nivel y la
experiencia, propone un temario y solo crea el curso cuando el estudiante
confirma), el plan queda guardado como `curso.md` visible en una
mini-ventana, y el estudio ocurre en el mismo hilo — el tutor da la lección
por pasos, los objetivos se van tachando en un panel lateral, cada unidad
puede repasarse, y la evaluación y el conversatorio de dudas suceden dentro
del chat. El agente genera temarios de 5 a 8 unidades, quizzes de opción
múltiple con desbloqueo por nota, y lleva progreso, puntos y racha entre
sesiones. También existe una CLI equivalente sobre el mismo núcleo.

Tomamos tres decisiones de arquitectura tempranas que definieron el proyecto.
Primero, **no usar frameworks de agentes** (LangChain o similares): nuestro
flujo es determinista (perfil → temario → lección → quiz → calificación) y el
LLM actúa como motor de contenido, no como planificador; una orquestación
propia de un módulo (`agente.py`) resultó más simple, depurable y explicable.
Segundo, **aislar el proveedor del LLM** detrás de una interfaz (`ClienteLLM`)
que el resto del código conoce, con el SDK concreto confinado a `llm.py`.
Esta decisión se validó sola: a mitad del proyecto cambiamos de Anthropic a
OpenAI y el cambio no tocó una sola línea de lógica de negocio. Tercero,
**salida estructurada por contrato**: toda generación que el programa consume
(temario, quiz) se pide como JSON con esquema explícito en el prompt y se
valida con funciones propias antes de usarse; si no valida, se reintenta
incluyendo el error de parseo en el prompt.

La calificación de quizzes es deliberadamente **local y determinista**
(comparación de índices): el LLM propone las preguntas, pero la nota nunca
depende de una segunda llamada que pueda alucinar. El progreso se guarda con
escritura atómica y los archivos corruptos degradan con gracia (advertir y
regenerar) en lugar de bloquear al estudiante.

## 2. Ingeniería de prompts

Antes de escribir los prompts definitivos investigamos literatura de
enseñanza de la programación y tutores LLM (informe completo con fuentes en
`docs/INVESTIGACION-PEDAGOGIA.md`). Tres hallazgos cambiaron el diseño:

1. **La estructura de la lección importa más que el tono.** Los prompts v1
   pedían "explica con ejemplos y sé motivador". Los v2 codifican el método
   PRIMM: la lección debe abrir con un código y la pregunta "¿qué crees que
   imprime?" *antes* de explicar, seguir con worked examples cuyos comentarios
   nombran el propósito de cada bloque (subgoal labeling), incluir una sección
   que desmonta un error conceptual documentado, y cerrar con un ejercicio de
   modificación antes del de creación.

2. **Los LLM no conocen los errores reales de los principiantes.** La
   literatura reciente muestra que generan distractores plausibles pero no
   basados en misconceptions reales. Por eso inyectamos en los prompts un
   banco de misconceptions documentadas (leer `x = x + 1` como ecuación,
   `while` como interrupción instantánea, índices desde 1...) y exigimos que
   cada distractor del quiz encarne una.

3. **El razonamiento del modelo no garantiza respuestas correctas** — de
   hecho aumenta su confianza incluso al equivocarse. El prompt del quiz exige
   verificación independiente: trazar el código y derivar la salida antes de
   escribir opciones, re-resolver desde cero, y reescribir la pregunta si dos
   opciones son defendibles.

La lección misma es **una conversación en dos fases**: primero el agente
genera el *guion* de la unidad (objetivos + 5-8 pasos PRIMM, validado como
JSON y cacheado) y luego el tutor la imparte charlando — desarrolla un paso
por turno, espera la respuesta del estudiante (su predicción, su intento de
ejercicio) y reacciona a ella antes de avanzar. Separar plan y ejecución fue
clave: la conversación no divaga porque el guion la ancla, y el guion no se
paga dos veces porque se cachea. El modo aplica además los guardrails
documentados por Khan Academy para Khanmigo: guía socrática (ante "dame la
solución" responde con pistas), escape del "no sé" (al segundo bloqueo
muestra un paso resuelto en lugar de repetir la pregunta) y redirección de
desvíos de tema. En las pruebas reales ambos comportamientos se sostuvieron:
ante una predicción errada el tutor corrigió con amabilidad y explicó el
porqué antes de continuar.

La personalización opera en dos niveles: el system prompt describe al
estudiante (nivel, meta, experiencia como fuente de analogías) y reglas
pedagógicas fijas; y el prompt del temario añade ajustes estructurales por
objetivo (para datos, pandas debe aparecer en las unidades 2-4 con analogías
Excel→DataFrame; para front, resultado visible en el navegador en el primer
tercio). Además el agente es adaptativo: los conceptos fallados en quizzes
entran al prompt de las lecciones siguientes para reforzarlos con ejemplos
nuevos. El efecto es medible en los cursos de muestra: el mismo programa
produjo "Variables y expresiones aplicadas a datos (repaso activo con
analogía Excel)" para un perfil y un curso de JavaScript con DOM temprano
para el otro.

## 3. Desafíos y soluciones

**Respuestas vacías de la API.** Con `gpt-5-mini`, las peticiones largas
devolvían a veces contenido vacío: los modelos de la familia gpt-5 gastan
tokens de razonamiento dentro de `max_completion_tokens`, y con un límite de
4096 el razonamiento podía consumirlo todo. Solución doble: subir el límite a
16384 y tratar la respuesta vacía como error transitorio reintentable.

**JSON envuelto o mal formado.** El modelo a veces envuelve el JSON en fences
de Markdown o responde con esquemas incompletos. `pedir_json` tolera fences,
valida contra el esquema y reintenta con el error de parseo dentro del prompt;
tras dos reintentos falla con un mensaje claro. En las pruebas con la API
real el caso feliz no necesitó reintentos.

**Crédito de API ≠ suscripción de chat.** Una cuenta con ChatGPT Plus
devolvía `429 insufficient_quota`: el crédito de API se compra aparte. Ese
429 no es transitorio, pero decidimos mantener la regla simple "429 ⇒
reintentar" aceptando el costo de tres reintentos en ese caso raro.

**Probar sin gastar.** Toda la suite (87+ pruebas) corre contra dobles del
LLM inyectados por constructor: un `ClienteLLMFalso` con respuestas en cola y
un `SDKFalso` que simula errores HTTP del SDK. La API real solo se toca en
scripts de humo manuales y en la exportación de los cursos de muestra.

Las mecánicas del producto no son inventadas: encuestamos los mejores
proyectos open source del área (`docs/INVESTIGACION-OSS.md`) y adoptamos con
fuente lo que tiene evidencia — ejecución de los ejemplos en el navegador
con Pyodide (futurecoder), racha diaria y XP sin vidas ni ligas (los A/B
publicados de Duolingo, excluyendo sus dark patterns), variantes de las
preguntas al reintentar (PrairieLearn), visualización de la máquina nocional
con Python Tutor, y el patrón thought→response de tutor-gpt para que las
pistas infieran primero el malentendido. Nuestro esquema de puntos por
intento resultó coincidir con el `autoPoints` de PrairieLearn, una
validación independiente del diseño.

## 4. Capacidades y limitaciones de los LLMs (reflexión)

El LLM demostró una capacidad notable para la **transferencia de dominio**:
con solo declarar "manejo Excel avanzado", produjo espontáneamente el mapa
hoja→DataFrame, filtro→selección y tabla dinámica→agrupación, que coincide
con la tabla de equivalencias oficial de pandas. La calidad pedagógica, sin
embargo, **no emerge sola: hay que especificarla**. Sin estructura PRIMM en
el prompt, las lecciones eran explicaciones genéricas correctas pero planas;
la diferencia entre un buen curso y uno mediocre estuvo en cuánta ciencia del
aprendizaje codificamos nosotros en el prompt, no en el modelo.

Las limitaciones que observamos: la fiabilidad del formato estructurado no es
absoluta (por eso todo se valida y reintenta); la corrección de los quizzes
no puede darse por sentada (por eso la verificación forzada y la calificación
local); y el no determinismo hace que dos ejecuciones del mismo perfil den
cursos distintos, lo que es aceptable aquí pero exigiría evaluación
sistemática en producción. En síntesis: el LLM es un excelente generador de
contenido personalizado, pero el sistema alrededor —validación, reintentos,
persistencia, calificación determinista— es lo que lo convierte en un
producto confiable.

## 5. Contribución individual

| Integrante | Contribución |
|---|---|
| _(nombre 1)_ | _(módulos/HUs, p. ej. HU-01/02, cliente LLM y pruebas)_ |
| _(nombre 2)_ | _(p. ej. HU-03/04, investigación pedagógica y prompts)_ |
| _(nombre 3)_ | _(p. ej. HU-05/06, CLI, cursos de muestra y video)_ |

<!-- Completar con los nombres reales y ajustar el reparto antes de entregar.
Conteo de palabras objetivo: 1000-1500 (verificar con `wc -w`). -->
