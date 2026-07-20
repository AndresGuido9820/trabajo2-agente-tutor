# Guion del video de demostración (5-7 minutos)

Requisitos del enunciado: todos los miembros hablan; el video muestra con un
rótulo en pantalla quién está hablando; se demuestran cursos para perfiles
distintos.

> Preparación previa a grabar: borrar `./data` para que el flujo arranque de
> cero, tener `.env` configurado, terminal con fuente grande y tema legible.
> Tener pre-generado el segundo curso en otra carpeta (`TUTOR_DATA_DIR`)
> para no esperar generaciones largas en cámara.

## Escena 1 — Introducción (0:00-0:45) · habla: _(nombre 1)_

- Qué es: agente tutor de programación por CLI que personaliza un curso
  completo con un LLM según el perfil del estudiante.
- Qué se ve en el video: dos perfiles opuestos → dos cursos distintos.
- Mencionar stack en una frase: Python + API de OpenAI, sin frameworks de
  agentes, todo validado y testeado (87+ pruebas).

## Escena 2 — Perfil 1 en vivo: "nunca programé → front con JavaScript" (0:45-2:30) · habla: _(nombre 2)_

- `uv run tutor` → cuestionario. Mostrar una entrada inválida a propósito
  (p. ej. opción "9") para enseñar la validación sin traceback.
- Se genera el temario: señalar que las unidades progresan hacia "ver algo
  en el navegador" temprano (personalización estructural).
- Mostrar el menú: TODAS las unidades navegables aunque no estén generadas.
- Entrar a la unidad 1: la lección es UNA CONVERSACIÓN (el momento estrella).
  Mostrar: primero aparecen los objetivos y la ruta de pasos; el tutor abre
  con el gancho y el "predice: ¿qué imprime esto?"; responder MAL a propósito
  → el tutor corrige con amabilidad y avanza al siguiente paso. Explicar en
  una frase el porqué (PRIMM conversado, `docs/INVESTIGACION-PEDAGOGIA.md`).
- Guardrail socrático: en el paso del reto pedirle "dame la solución
  completa" → da una pista, no la solución; responder "no sé" dos veces →
  muestra un paso resuelto. Explicar: guardrails tipo Khanmigo.

## Escena 3 — Evaluación y progreso (2:30-4:00) · habla: _(nombre 3)_

- `e 1`: responder el quiz en cámara fallando UNA pregunta a propósito.
- Mostrar el resultado: nota, explicación por pregunta, conceptos a repasar.
- `p`: tabla de progreso. Cerrar el tutor, volver a abrirlo → el progreso
  persiste (unidad evaluada, mejor nota).
- Decir: los conceptos fallados entran al prompt de las siguientes lecciones
  (adaptación por desempeño).

## Escena 4 — Perfil 2: "sé Excel → ciencia de datos con Python" (4:00-5:30) · habla: _(nombre 1 o 2)_

- Cambiar a la carpeta del segundo curso (pre-generado) o usar `r` para
  rehacer el perfil en vivo.
- Comparar temarios lado a lado: mismo programa, curso totalmente distinto
  (títulos con analogía Excel, pandas en la unidad 2, tabla dinámica →
  agrupación).
- Abrir una lección y mostrar una analogía Excel→Python concreta.

## Escena 5 — Bajo el capó + cierre (5:30-6:30) · hablan: todos (una frase c/u)

- _(nombre 2)_: ingeniería de prompts: banco de misconceptions para los
  distractores y verificación forzada del quiz.
- _(nombre 3)_: robustez: reintentos con backoff, JSON validado, calificación
  local determinista, progreso con escritura atómica.
- _(nombre 1)_: cierre: qué aprendimos sobre LLMs (la calidad pedagógica hay
  que especificarla, no emerge sola) y despedida.

## Checklist de edición

- [ ] Rótulo con el nombre de quien habla en cada escena.
- [ ] Duración final entre 5:00 y 7:00.
- [ ] Audio parejo y terminal legible (mín. 16 pt).
- [ ] Sin API keys visibles en pantalla (¡ojo con `.env` y el historial!).
