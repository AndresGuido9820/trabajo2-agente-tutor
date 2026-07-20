# HU-13 — Mejoras copiadas de los mejores OSS

**Como** estudiante **quiero** ejecutar los ejemplos en el navegador, ver mi
racha y mis puntos, visualizar el código paso a paso, no repetir preguntas
idénticas al reintentar, y que las pistas entiendan QUÉ malentendí **para**
aprender con las mecánicas que los mejores productos ya validaron.

Origen y fuentes: `docs/INVESTIGACION-OSS.md` (freeCodeCamp, Exercism,
Runestone/PrairieLearn, futurecoder/Pyodide, Duolingo, tutor-gpt).

## Criterios de aceptación

- **Pyodide (futurecoder)**: en cursos de Python, cada bloque de código de
  la guía tiene "▶ Pruébalo": editor editable + salida, ejecutado 100 % en
  el navegador (lazy-load de Pyodide al primer uso; errores mostrados sin
  romper la página). Cero cambios de backend.
- **Racha y XP (Duolingo, sin dark patterns)**: racha diaria persistente
  (hoy cuenta una vez; día seguido +1; día saltado reinicia a 1) visible en
  el header junto a los puntos. Sin vidas ni ligas (decisión documentada).
- **Python Tutor**: cada bloque de código Python tiene "🔍 Paso a paso" que
  abre pythontutor.com con el código precargado (URL-encoded).
- **Variantes al reintentar (PrairieLearn)**: el prompt del quiz recibe los
  enunciados del intento anterior y exige variantes equivalentes (mismos
  conceptos, distinta superficie). Sesión-local.
- **Theory-of-mind (tutor-gpt)**: el system del conversatorio incluye el
  historial de desempeño (intentos, notas, conceptos fallados) y ordena
  inferir primero el malentendido antes de preguntar.

## Tareas

- [x] `progreso.py`: `racha` + `ultima_sesion` persistentes con
      `registrar_sesion(hoy)`; se registra al crear el `Agente`.
- [x] `evaluacion.py`/`prompts.py`: `generar_quiz(..., preguntas_previas)` y
      prompt con regla de variantes; `agente.py` recuerda enunciados por
      unidad (sesión).
- [x] `prompts.py`: `system_conversatorio` con resumen de desempeño y paso
      de inferencia del malentendido.
- [x] `web.py`: `racha` en `/api/estado`.
- [x] `static/index.html`: header 🔥/⭐, botones ▶ y 🔍 en los bloques de
      código de la guía, runner Pyodide con lazy-load.
- [x] Pruebas: racha (mismo día/consecutivo/salto), variantes en el prompt,
      desempeño en el system del conversatorio, estado con racha.
- [x] `docs/INVESTIGACION-OSS.md` + HALLAZGOS + reporte (adoptado/futuro).

## Pruebas

- `test_racha_mismo_dia_no_suma` / `_dia_consecutivo_suma` / `_salto_reinicia`
- `test_quiz_reintento_pide_variantes_de_preguntas_previas`
- `test_conversatorio_incluye_desempeno_e_inferencia`
- `test_estado_web_expone_racha`
