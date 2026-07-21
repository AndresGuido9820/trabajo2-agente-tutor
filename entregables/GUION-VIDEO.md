# Guion del video de demostración (5-7 minutos)

Requisitos: todos los miembros hablan, con rótulo en pantalla de quién habla;
se demuestran cursos para perfiles distintos.

> Antes de grabar: borrar `./data` para arrancar de cero, `.env` configurado,
> fuente grande. Tener un SEGUNDO curso pre-generado en otra carpeta
> (`TUTOR_DATA_DIR=...` con perfil front/JavaScript) para comparar sin
> esperas. Internet activo (Pyodide y Python Tutor).

## Escena 1 — Qué es (0:00-0:40) · habla: _(nombre 1)_

- Un tutor de programación con LLM donde TODO pasa en una conversación:
  pides tu curso hablando, estudias charlando y el plan vive al lado.
- Stack en una frase: Python + FastAPI + API de OpenAI, sin frameworks de
  agentes, 158 pruebas automatizadas.

## Escena 2 — Creación conversacional en vivo (0:40-2:00) · habla: _(nombre 2)_

- `uv run tutor-web` → escribir: *"Hazme un curso de Python para analizar
  las ventas de mi negocio; manejo bien Excel"*.
- Mostrar que el asesor **NO crea de una**: resume lo que entendió, pregunta
  el nivel, propone un temario → responder, ajustar si se quiere, y
  confirmar con **"ya, dale"**.
- Se crea el curso: el **plan aparece en el panel derecho** y quedó guardado
  como `curso.md` → abrir la mini-ventana 📄 y el botón de descarga.
- Señalar los títulos personalizados (analogías de Excel en todo el temario).

## Escena 3 — Estudiar charlando (2:00-3:40) · habla: _(nombre 3)_

- El tutor arranca la lección en el mismo chat (método PRIMM): responde MAL
  la predicción a propósito → corrige con amabilidad y avanza de paso.
- Botón **▶ Pruébalo** en un bloque de código: se ejecuta EN el navegador
  (Pyodide); mencionar 🔍 Paso a paso (Python Tutor).
- Botón **✨ demo interactiva**: el tutor genera una mini-página interactiva
  del concepto (tenerla ya cacheada de un ensayo previo para no esperar).
- Al terminar la lección: **el objetivo se tacha en el panel** 🎉 y aparece
  "Repasar en el chat".

## Escena 4 — Evaluación, candado y conversatorio (3:40-5:10) · habla: _(nombre 1)_

- Presentar la evaluación **dentro del chat**; reprobar a propósito.
- Mostrar: la unidad 2 sigue 🔒, y el tutor abre el **conversatorio
  socrático** en el mismo hilo (pistas, no respuestas; chips "Explícame la
  pregunta N").
- Reintentar: señalar que las preguntas son **variantes nuevas** (no se
  memoriza la letra). Aprobar → +30 ⭐, objetivo aprobado, unidad 2
  desbloqueada, racha 🔥 y puntos en el header.

## Escena 5 — Otro perfil + bajo el capó (5:10-6:30) · hablan: todos (frases cortas)

- _(nombre 2)_: cambiar a la carpeta del curso front/JavaScript pre-generado:
  mismo producto, curso totalmente distinto (DOM temprano, proyectos web).
- _(nombre 3)_: ingeniería: prompts con PRIMM y banco de misconceptions,
  guardrails socráticos tipo Khanmigo, verificación independiente de
  quizzes, calificación local determinista, JSON validado con reintentos.
- _(nombre 1)_: cierre: qué aprendimos de los LLMs (la calidad pedagógica se
  especifica, no emerge; el sistema alrededor es el producto). Despedida.

## Checklist de edición

- [ ] Rótulo con el nombre de quien habla en cada escena.
- [ ] Duración 5:00-7:00; audio parejo; terminal/navegador legibles.
- [ ] Sin API keys en pantalla (¡ojo con `.env` y el historial del shell!).
