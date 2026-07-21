# Guion del video de demostración (5-7 minutos)

**Formato:** el video base es una grabación real de la app hecha con
Playwright (generada por `scripts/video_demo.py`), en dos archivos que se
concatenan al editar: `entregables/video/demo-playwright.webm` (escenas
E1-E8b, ~10:39) y `demo-playwright-parte2.webm` (E9-E10, ~1:29). Se narra
encima y se recortan las esperas de generación. Los tiempos exactos de
cada escena están en `entregables/video/marcas.txt` y
`marcas-parte2.txt` — usa esas marcas para cortar. (Los .webm no van al
repo: quedan locales en `entregables/video/`.)

Requisitos de la rúbrica: todos los miembros hablan con **rótulo en
pantalla de quién habla**; se muestran cursos para **perfiles distintos**
(aquí: "ventas con Excel → Python" y "nunca programé → web/JS").

> Edición sugerida: recorta las esperas de generación (los tramos donde
> solo se ve el indicador "escribiendo…") a 1-2 s con un corte o un
> acelerado x8; el resto va a velocidad real. Apunta a 5:30-6:30 finales.

---

## Escena 0 — Intro (sin video de la app, ~25 s) · habla: _(nombre 1)_

> "Este es Profe Bit, un tutor de programación construido sobre la API de
> OpenAI. La idea central: **todo pasa conversando** — pides tu curso
> hablando, estudias charlando, y el sistema decide con criterio cuándo
> avanzas. Python y FastAPI, sin frameworks de agentes, 296 pruebas
> automatizadas y calificación siempre local: el LLM genera contenido,
> nunca pone la nota."

## Escena 1 — Mis cursos, tema y gestión (marca E1-E2) · habla: _(nombre 1)_

- Se ve: la biblioteca de cursos, el toggle claro/oscuro, la sección de
  archivados, y el renombrado de un curso desde el menú ⋯.
> "Esta es la biblioteca: cada curso con su progreso. Hay tema claro y
> oscuro con contraste AA verificado con axe-core, cursos archivables, y
> gestión completa: renombrar, exportar, borrar con papelera."

## Escena 2 — Crear un curso conversando (marca E3) · habla: _(nombre 2)_

- Se ve: "Quiero aprender a hacer páginas web desde cero, nunca he
  programado" → el asesor **pregunta** antes de crear → "ya, dale" → el
  curso se crea y arranca la clase 1.
> "Fíjense que el asesor NO crea el curso de una: resume lo que entendió,
> pregunta el nivel y el tiempo disponible, propone un temario y solo lo
> crea cuando confirmo. Este perfil es 'nunca he programado, quiero web' —
> compárenlo con el curso de ventas de la otra escena: temario, lenguaje y
> analogías completamente distintos."

## Escena 3 — La clase por objetivos (marcas E3b-E4) · habla: _(nombre 2)_

- Se ve: la clase nueva con su **panel de objetivos** a la derecha; luego
  el curso de ventas con su **historial persistente** y el repaso.
> "Cada clase es una conversación con historial persistente. El panel
> derecho muestra los 3-4 objetivos de la clase y se van marcando en vivo;
> la evaluación final está bloqueada hasta cumplirlos todos. El tutor
> escribe en tiempo real, por streaming."

## Escena 4 — Mini-quiz y reto de código (marcas E5-E5c) · habla: _(nombre 3)_

- Se ve: el tutor avanza paso a paso (PRIMM); al cerrar un objetivo salta
  el **mini-quiz** (se responde y suma ⭐); luego el **reto de código**:
  Verificar corre los tests EN el navegador y la **pista** es socrática.
> "El método es PRIMM: predigo antes de que me expliquen. El tutor decide
> si mi respuesta atiende el paso o si es una duda — un 'hola' no avanza
> la lección. Al cerrar cada objetivo hay un mini-quiz pre-generado, y un
> reto de código real: los tests corren en MI navegador con Pyodide, y si
> me trabo, la pista me guía pero jamás me da la solución."

## Escena 5 — Demo interactiva ✨ (marca E6) · habla: _(nombre 3)_

- Se ve: la demo HTML generada por el LLM dentro del chat (iframe aislado).
> "El botón ✨ genera una demo interactiva del objetivo — el LLM escribe
> una mini-página que pasa un control de calidad automático antes de
> mostrarse, y corre en un sandbox sin red. Si no me gusta, la regenero."

## Escena 6 — Buscador, progreso y repaso (marcas E7-E8b) · habla: _(nombre 1)_

- Se ve: ⌘K con resultados de clases y mensajes; la vista Mi progreso
  (actividad, notas, conceptos); el Repaso del día.
> "Todo lo que vi es buscable con comando-K. Mi progreso muestra la
> actividad, las notas y qué conceptos domino o debo repasar — y lo que
> fallo entra a un repaso espaciado a 1, 3 y 7 días, que es lo que la
> evidencia dice que funciona para no olvidar."

## Escena 7 — Evaluación final (marca E9) · habla: _(nombre 2)_

- Se ve: evaluación de 6+ preguntas con badges de nivel
  (recordar/comprender/aplicar), calificación, nota y resumen por concepto.
> "La evaluación pondera por nivel de Bloom: las preguntas de 'aplicar'
> pesan el triple que las de memoria — saber definiciones no aprueba. Las
> preguntas salen de un banco por clase que garantiza que dos intentos
> nunca repiten enunciado, y si repruebo, se abre un conversatorio
> socrático sobre MIS errores. La nota la calcula el servidor comparando
> índices: el LLM nunca califica."

## Escena 8 — Exportar y cierre (marca E10) · habla: _(nombre 3)_

- Se ve: exportar el curso a .zip desde el menú ⋯; vuelta a Mis cursos.
> "El curso completo — diseño, conversaciones y resultados — se exporta a
> un zip de Markdown para estudiar offline. Todo el proyecto está en
> GitHub con CI, 296 pruebas, y el reporte publicado en GitHub Pages.
> Gracias."

---

## Checklist de edición

- [ ] Rótulo con el nombre de quien habla en cada escena.
- [ ] Recortar las esperas de generación (ver marcas.txt).
- [ ] Duración final entre 5 y 7 minutos.
- [ ] Exportar y subir; enlazar en el README si el curso lo pide.
