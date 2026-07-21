# Reporte técnico — Profe Bit: Tutor de Programación con LLMs

Trabajo 02 · Curso: Normalización: aplicaciones de LLMs y Agentes para la
enseñanza de la programación básica.

## 1. Enfoque y arquitectura

Construimos un agente tutor donde **todo es una conversación**. El
estudiante pide su curso con sus palabras ("hazme un curso de Python para
analizar las ventas de mi negocio; manejo bien Excel"); un asesor
conversacional resume lo que entendió, pregunta lo que falta (nivel,
experiencia, lenguaje), propone un temario y solo crea el curso cuando el
estudiante confirma. Desde ahí, la app funciona como un ChatGPT educativo:
un menú de **Mis cursos**, y dentro de cada curso una barra lateral con el
**diseño del curso** (documento estructurado) y **una conversación por
clase**, cada una con su historial persistente. El tutor imparte la clase
paso a paso, la evaluación ocurre dentro del mismo chat, aprobar con 70+
desbloquea la siguiente clase, y reprobar abre un conversatorio socrático de
dudas antes de reintentar con preguntas nuevas.

Las decisiones de arquitectura que definieron el proyecto:

**Sin frameworks de agentes.** El flujo es determinista (diseño → clase →
evaluación → progresión) y el LLM es el motor de contenido, no un
planificador: la orquestación propia (`agente.py`) resultó más simple,
depurable y explicable que LangChain. **Proveedor aislado**: el código de
negocio solo conoce la interfaz `ClienteLLM`; cuando cambiamos de Anthropic
a OpenAI a mitad del proyecto, no se tocó una línea de lógica. **Salida
estructurada por contrato**: todo lo que el programa consume (perfil
extraído de la conversación, temario, guiones, quizzes, la decisión de
avanzar un paso) se pide como JSON con esquema explícito y se valida antes
de usarse; si no valida, se reintenta incluyendo el error en el prompt.
**Calificación local y determinista**: el LLM genera preguntas, pero la
nota es una comparación de índices — nunca depende de una segunda llamada
que pueda alucinar.

**El diseño del curso vive en una base de datos.** Cada curso tiene su
SQLite (`data/cursos/<id>/tutor.db`) con tablas `curso` (diseño, plan en
Markdown, versión de prompts), `clases` (título, objetivo, subtemas y el
**guion/prompt** con el que el tutor imparte esa clase, con metadata),
`perfil`, `progreso` y `chat` por conversación. El documento `curso.md` es
una vista generada; la edición manual es un **editor estructurado** que pasa
por las mismas validaciones que el contenido generado — así el LLM siempre
recibe el diseño limpio. Los formatos anteriores migran automáticamente.

**Frontend en React + Mantine** (Vite), servido compilado por el mismo
FastAPI: burbujas de chat, quiz con radios dentro de la conversación,
notificaciones, progreso y candados. Dos capacidades diferenciales: los
bloques de código se pueden **ejecutar en el navegador** (Pyodide/WASM, sin
backend de ejecución) y visualizar línea a línea (Python Tutor); y el botón
✨ genera **demos interactivas** — el LLM escribe una mini-página HTML
autocontenida que corre en un `iframe sandbox` sin red, al estilo de los
Artifacts de Claude.

## 2. Ingeniería de prompts

Antes de fijar los prompts investigamos literatura de enseñanza de la
programación y tutores LLM (`docs/INVESTIGACION-PEDAGOGIA.md`, con fuentes).
Tres hallazgos definieron el diseño:

1. **La estructura pedagógica hay que especificarla.** Las clases siguen un
   guion PRIMM generado primero (predicción antes de explicación, worked
   examples con subgoal labels, estado de variables línea a línea, error
   típico, reto). Separar el plan (guion JSON validado y cacheado) de la
   ejecución (un paso por turno) evita que la conversación divague y que el
   plan se pague dos veces.
2. **Los LLM no conocen los errores reales de los principiantes**: inyectamos
   un banco de misconceptions documentadas (Sorva: leer `x = x + 1` como
   ecuación, `while` como interrupción instantánea…) y exigimos que los
   distractores de cada quiz encarnen una.
3. **El razonamiento del modelo aumenta su confianza incluso al errar**: el
   prompt del quiz exige verificación independiente (trazar el código y
   derivar la salida antes de escribir opciones, re-resolver desde cero,
   reescribir ítems ambiguos).

El avance de la lección también es una decisión del modelo con contrato
JSON `{avanza, mensaje}`: si el mensaje del estudiante atiende el paso,
reacciona y desarrolla el siguiente; si es un saludo o una duda, responde
natural y **no avanza** — un "hola" ya no dispara media lección. El
conversatorio post-reprobación aplica los guardrails documentados de
Khanmigo (pistas, no soluciones; escape ante el "no sé" repetido) más un
paso theory-of-mind al estilo tutor-gpt: recibe el historial de intentos e
infiere el malentendido antes de preguntar. Al reintentar, el prompt recibe
los enunciados previos y exige **variantes** (patrón PrairieLearn): aprobar
mide dominio, no memoria. Las mecánicas restantes también vienen de
referentes con evidencia (`docs/INVESTIGACION-OSS.md`): racha y puntos sin
los dark patterns de Duolingo, Pyodide de futurecoder, Python Tutor.

## 3. Desafíos y soluciones

**Timeouts que se disfrazan de errores de red.** Con `gpt-5-mini`, las
generaciones largas (demos, guías) superaban el timeout de 60 s del SDK,
que reporta el corte como error de conexión: el sistema reintentaba en vano
llamadas que iban bien. Diagnóstico con logs de reintentos; solución:
timeout de 180 s y respuesta-vacía tratada como transitoria (los gpt-5
gastan razonamiento dentro de `max_completion_tokens`).

**El front también necesita pruebas.** Un bug de método HTTP (405) pasó
inadvertido porque los tests del API no ejercitan el JS. Añadimos un bot
E2E que replica las peticiones exactas del navegador contra un servidor
real, y luego un **bot Playwright** que recorre la app completa y captura
las pantallas del anexo.

**Probar sin gastar.** Las 174 pruebas corren contra dobles del LLM
inyectados (respuestas en cola, fallas simuladas del SDK); la API real solo
se toca en scripts de humo y E2E manuales. CI en GitHub Actions corre
formato, linter, mypy estricto, pytest y el build del frontend en cada push.

## 4. Capacidades y limitaciones de los LLMs (reflexión)

Lo que más nos sorprendió fue la **transferencia de dominio**: con solo
"manejo bien Excel", el modelo produjo el mapa hoja→DataFrame,
filtro→selección, tabla dinámica→agrupación en títulos, analogías y
ejemplos. También su capacidad de **generar software pequeño**: las demos
interactivas salen funcionales y fieles al tema. Pero la calidad pedagógica
**no emerge sola**: la diferencia entre un tutor mediocre y uno bueno
estuvo en cuánta ciencia del aprendizaje codificamos en los prompts. Y la
fiabilidad tampoco: JSON que a veces no valida, quizzes cuya corrección no
puede darse por sentada, latencias de minutos que exigen UX de espera
honesta. La conclusión del equipo: el LLM es un generador excepcional de
contenido personalizado; el **producto** es el sistema alrededor —
validación, reintentos, calificación determinista, persistencia, candados
y una interfaz que administra la espera.

## 5. Contribución individual

| Integrante | Contribución |
|---|---|
| _(nombre 1)_ | _(p. ej. cliente LLM, BD y pruebas)_ |
| _(nombre 2)_ | _(p. ej. investigación pedagógica y prompts)_ |
| _(nombre 3)_ | _(p. ej. frontend, E2E y video)_ |

## Anexo — Recorrido de la aplicación (capturas del bot Playwright)

Capturas generadas automáticamente por `scripts/capturas_playwright.py`
interactuando con la app real (servidor limpio + API de OpenAI).

**1. Mis cursos** — menú inicial con la tarjeta de nuevo curso.

![Mis cursos](capturas/01-mis-cursos.png)

**2. Nuevo curso** — la creación es un chat: "¿Qué quieres aprender?".

![Nuevo curso](capturas/02-nuevo-curso.png)

**3. El asesor NO crea de una** — resume lo entendido y pregunta el nivel.

![El asesor pregunta](capturas/03-asesor-pregunta.png)

**4. Propuesta de temario** — lista de clases para ajustar o confirmar.

![El asesor propone](capturas/04-asesor-propone.png)

**5. Clase 1 en el chat** — confirmado el "ya, dale", arranca la lección
(guion PRIMM: pide predecir antes de explicar).

![Arranca la clase 1](capturas/05-clase-1-arranca.png)

**6. Predicción errada a propósito** — el tutor corrige con amabilidad,
explica el porqué y avanza de paso.

![El tutor corrige](capturas/06-tutor-corrige-y-avanza.png)

**7. Duda libre a mitad de clase** — el estudiante interrumpe con una
pregunta ("¿esto para qué me sirve en mi negocio?"); el tutor la responde y
retoma el paso **sin avanzar** la lección (decisión de avance con criterio).

![Duda al tutor](capturas/07-duda-al-tutor.png)

**8. Clase completada** — tras responder todos los pasos, la clase queda
tachada en la barra lateral, el tutor cierra con el recap y aparece el CTA
de evaluación; las clases 2-7 siguen con candado.

![Clase completada](capturas/08-clase-completada.png)

**9. Evaluación dentro del chat** — 4 preguntas de comprensión (predicción /
encuentra-el-bug) con distractores basados en misconceptions documentadas.

![Evaluación](capturas/09-evaluacion.png)

**10. Resultado (ruta de reprobar)** — el bot respondió al azar y sacó 1 de
4: desglose por pregunta con la correcta y la explicación del error de
razonamiento, botón de reintento (con preguntas nuevas) y el conversatorio
socrático abriéndose automáticamente al final.

![Resultado](capturas/10-resultado.png)

**11. Diseño del curso** — el documento generado (persistido en la BD, con
copia `curso.md` descargable).

![Diseño del curso](capturas/11-diseno-documento.png)

**12. Edición estructurada** — título/objetivo/subtemas por clase, validados
con las mismas reglas que usa el LLM.

![Editor estructurado](capturas/12-diseno-editor-estructurado.png)

**13. Mis cursos con progreso** — el curso creado con su barra de avance.

![Mis cursos con progreso](capturas/13-mis-cursos-con-progreso.png)
