# Guion del video de demostración (5-7 minutos)

**Concepto:** el video empieza **desde cero**: se crea el curso conversando
(el asesor pregunta, propone el temario y solo crea al confirmar) y luego
se vive **la clase 1 completa** — panel de objetivos de 0 % a 100 %, retos
de código, mini-quices, demo — hasta la evaluación final. Una sola toma.

**Mapa de marcas** (`marcas-desde-cero.txt`): C1 creación (0:00-2:07) ·
C2 la clase abre (2:07) · C3 conversación con retos/quices (4:48-19:59) ·
C4 demo (7:17) · C5 clase completada (19:59) · C6 evaluación (20:03) ·
C7 Mi progreso (22:29).

**Material** (local en `entregables/video/`, los videos no van al repo):

| Archivo | Duración | Contenido |
|---|---|---|
| **`demo-desde-cero.mp4`** (.webm) | 22:41 | **LA TOMA PRINCIPAL**: crear el curso conversando + la clase 1 completa + evaluación + Mi progreso, con la UI profesional |
| `marcas-desde-cero.txt` | — | Timestamp de cada hito para cortar |
| `demo-una-clase*.mp4`, `demo-playwright*.mp4` | — | Tomas anteriores (B-roll opcional; UI vieja) |

> **Edición:** el metraje se grabó con `TUTOR_MODEL_CHAT=gpt-5-nano`
> (turnos de ~3-8 s) así que hay poca espera muerta; recorta los tramos de
> "escribiendo…" y los quices repetidos que sobren para aterrizar en
> 5:30-6:30. Rótulo con el nombre de quien habla en cada bloque.

---

## Bloque 0 — Intro (sin app, ~25 s) · habla: _(nombre 1)_

> "Este es Profe Bit, un tutor de programación construido sobre la API de
> OpenAI. Vamos a ver UNA clase completa, de cero a evaluación, tal como la
> vive un estudiante. Detrás: Python + FastAPI, sin frameworks de agentes,
> 300 pruebas automatizadas, y una regla de oro: el LLM genera el
> contenido, pero la nota siempre la calcula el servidor."

## Bloque 0.5 — Crear el curso conversando (C1, 0:00-2:07) · habla: _(nombre 1)_

- Se ve: "Hazme un curso de Python para analizar las ventas de mi negocio;
  manejo bien Excel" → el asesor resume, pregunta nivel y tiempo, propone
  un temario de 8 unidades y SOLO crea al confirmar con "ya, dale".
> "Todo empieza con una frase. El asesor no crea de una: resume lo que
> entendió, pregunta lo que falta y propone un temario a la medida — miren
> las analogías con Excel en cada unidad. Solo cuando confirmo, crea el
> curso."

## Bloque 1 — La clase arranca (C2-C3, 2:07-6:00) · habla: _(nombre 1)_

- Se ve: entrar al curso "Ventas con Python 📊"; la clase 1 abre al
  instante; a la derecha, el **panel con 4 objetivos pendientes y 0 %**.
> "Este curso se creó conversando — el estudiante dijo \'sé Excel, quiero
> analizar mis ventas\' y todo el temario usa esa analogía. Cada clase tiene
> un guion por objetivos: el panel muestra los 4 de hoy, todos pendientes.
> El tutor abre con método PRIMM: me pide PREDECIR antes de explicarme."

## Bloque 2 — Aprender conversando (C3.r-C3.q1, 6:12-7:10) · habla: _(nombre 2)_

- Se ve: turnos con **streaming**; el **reto de código** (Verificar corre
  tests en el navegador, la pista es socrática); el **mini-quiz** del
  objetivo 1; el panel tacha el objetivo.
> "El tutor decide si mi respuesta atiende el paso o si es una duda — un
> \'hola\' no avanza la clase. Al final de cada objetivo hay un reto de
> código real: los tests corren en MI navegador con Pyodide, y si fallo,
> la pista me orienta pero JAMÁS me da la solución. Luego un mini-quiz de
> dos preguntas cierra el objetivo: mírenlo tacharse en el panel."

## Bloque 3 — Repaso sin castigo + demo (C3.q2-C4, 7:12-9:45) · habla: _(nombre 2)_

- Se ve: quiz fallado 0/2 → el tutor **re-explica con otro ejemplo** y
  repite el quiz; la **demo interactiva ✨** del objetivo.
> "Fallar no castiga: el tutor re-explica con un ejemplo distinto y me deja
> reintentar; lo fallado queda anotado para la evaluación y para el repaso
> espaciado. Y el botón ✨ genera una demo interactiva del objetivo — una
> mini-app que el LLM escribe, pasa control de calidad automático y corre
> en un sandbox sin red."

## Bloque 4 — El arco se completa (C3 restante, 9:49-19:59; acelerar) · habla: _(nombre 3)_

- Se ve (acelerado/cortes): objetivos 2, 3 y 4 con sus retos y quices; el
  panel llenándose; a las 12:06, **"¡Clase completada!" y el botón
  Evaluación final se enciende**.
> "Así avanza la clase entera: cuatro objetivos, cada uno con su secuencia,
> su reto y su verificación. La evaluación final está bloqueada hasta
> cumplirlos todos — cuando el panel llega al 100 %, se enciende."

## Bloque 5 — Evaluación final (C6, 20:03-22:29) · habla: _(nombre 3)_

- Se ve: 6 preguntas con **badges de nivel** (recordar/comprender/aplicar),
  calificación, **nota ponderada** y resumen por concepto.
> "La evaluación pondera por nivel de Bloom: aplicar pesa el triple que
> recordar — saber definiciones no aprueba. Las preguntas salen de un banco
> por clase que garantiza cero repetición entre intentos, y la nota es una
> comparación de índices en el servidor: el modelo nunca califica. Si
> repruebo, se abre un conversatorio socrático sobre MIS errores."

## Bloque 6 — Cierre (C7, 22:29-fin) · habla: _(nombre 1)_

- Se ve: **Mi progreso** con la actividad, notas y conceptos de la clase.
> "Todo queda registrado: actividad, notas, qué domino y qué repasar — y lo
> fallado vuelve a los 1, 3 y 7 días, que es lo que la evidencia dice que
> funciona. El proyecto completo está en GitHub con CI, 300 pruebas y el
> reporte en GitHub Pages. Gracias."

---

## Checklist de edición

- [ ] Rótulos con nombre por bloque (requisito de la rúbrica).
- [ ] Acelerar/cortar el bloque 4 (7 min de metraje → ~1 min).
- [ ] Duración final entre 5 y 7 minutos.
- [ ] (Opcional) intercalar 10-15 s del B-roll `demo-playwright.mp4` para
      mostrar la creación conversacional y el buscador ⌘K.
