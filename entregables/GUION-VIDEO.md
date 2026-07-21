# Guion del video de demostración (5-7 minutos)

**Concepto:** el video sigue **UNA clase completa** de principio a fin — el
panel de objetivos arranca en 0 %, la conversación avanza, los objetivos se
van tachando en verde, y al llegar al 100 % se desbloquea y presenta la
evaluación final. Es el arco de aprendizaje real de la app, sin saltos.

**Material** (local en `entregables/video/`, los videos no van al repo):

| Archivo | Duración | Contenido |
|---|---|---|
| `demo-una-clase.mp4` (.webm) | 12:41 | El arco de la clase: V1→V5 |
| `demo-una-clase-parte2.mp4` | 1:36 | Evaluación final calificada + Mi progreso |
| `marcas-una-clase.txt` / `-p2.txt` | — | Timestamp de cada hito para cortar |
| `demo-playwright*.mp4` | 10:39 + 1:29 | (B-roll opcional: tour completo — creación conversacional, buscador ⌘K, tema, exportar) |

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

## Bloque 1 — La clase arranca (marca V1-V2, 0:00-2:00) · habla: _(nombre 1)_

- Se ve: entrar al curso "Ventas con Python 📊"; la clase 1 abre al
  instante; a la derecha, el **panel con 4 objetivos pendientes y 0 %**.
> "Este curso se creó conversando — el estudiante dijo \'sé Excel, quiero
> analizar mis ventas\' y todo el temario usa esa analogía. Cada clase tiene
> un guion por objetivos: el panel muestra los 4 de hoy, todos pendientes.
> El tutor abre con método PRIMM: me pide PREDECIR antes de explicarme."

## Bloque 2 — Aprender conversando (V2-V2.1, 2:00-3:30) · habla: _(nombre 2)_

- Se ve: turnos con **streaming**; el **reto de código** (Verificar corre
  tests en el navegador, la pista es socrática); el **mini-quiz** del
  objetivo 1; el panel tacha el objetivo.
> "El tutor decide si mi respuesta atiende el paso o si es una duda — un
> \'hola\' no avanza la clase. Al final de cada objetivo hay un reto de
> código real: los tests corren en MI navegador con Pyodide, y si fallo,
> la pista me orienta pero JAMÁS me da la solución. Luego un mini-quiz de
> dos preguntas cierra el objetivo: mírenlo tacharse en el panel."

## Bloque 3 — Repaso sin castigo + demo (V2.2-V3, ~3:10-4:45) · habla: _(nombre 2)_

- Se ve: quiz fallado 0/2 → el tutor **re-explica con otro ejemplo** y
  repite el quiz; la **demo interactiva ✨** del objetivo.
> "Fallar no castiga: el tutor re-explica con un ejemplo distinto y me deja
> reintentar; lo fallado queda anotado para la evaluación y para el repaso
> espaciado. Y el botón ✨ genera una demo interactiva del objetivo — una
> mini-app que el LLM escribe, pasa control de calidad automático y corre
> en un sandbox sin red."

## Bloque 4 — El arco se completa (V2.3-V4, 4:45-12:08) · habla: _(nombre 3)_

- Se ve (acelerado/cortes): objetivos 2, 3 y 4 con sus retos y quices; el
  panel llenándose; a las 12:06, **"¡Clase completada!" y el botón
  Evaluación final se enciende**.
> "Así avanza la clase entera: cuatro objetivos, cada uno con su secuencia,
> su reto y su verificación. La evaluación final está bloqueada hasta
> cumplirlos todos — cuando el panel llega al 100 %, se enciende."

## Bloque 5 — Evaluación final (parte 2, 0:00-1:29) · habla: _(nombre 3)_

- Se ve: 6 preguntas con **badges de nivel** (recordar/comprender/aplicar),
  calificación, **nota ponderada** y resumen por concepto.
> "La evaluación pondera por nivel de Bloom: aplicar pesa el triple que
> recordar — saber definiciones no aprueba. Las preguntas salen de un banco
> por clase que garantiza cero repetición entre intentos, y la nota es una
> comparación de índices en el servidor: el modelo nunca califica. Si
> repruebo, se abre un conversatorio socrático sobre MIS errores."

## Bloque 6 — Cierre (parte 2, 1:29-fin) · habla: _(nombre 1)_

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
