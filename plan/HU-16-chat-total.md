# HU-16 — Todo en un chat: creación conversacional, plan .md y estudio continuo

**Como** estudiante **quiero** que TODO pase en una sola conversación — el
tutor me pregunta y propone antes de crear el curso, guarda el plan como
`.md` visible en una mini-ventana, me enseña charlando mientras los
objetivos se van tachando, y puedo repasar cualquiera — **para** aprender
sin salirme nunca del chat.

Origen: retroalimentación de visión del producto.

## Criterios de aceptación

- **Creación conversacional**: el primer mensaje abre un diálogo — el asesor
  resume lo que entendió ("bueno, tal y tal cosa"), pregunta lo que falta
  (nivel, experiencia, lenguaje), propone un temario y solo crea el curso
  cuando el estudiante confirma ("ya", "dale"). Protocolo JSON
  {mensaje, listo, perfil} validado.
- **Plan en .md**: al confirmar se guarda `curso.md` (unidades + objetivos +
  conceptos) y se puede ver/descargar en una mini-ventana (modal) sin salir
  del chat.
- **Estudio en el chat**: el tutor da la lección por pasos en la misma
  conversación (`/api/estudio`); al terminar la lección, el **objetivo se
  tacha en el panel** lateral y aparece el CTA de evaluación.
- **Repasar**: cada unidad completada tiene "↩ Repasar en el chat", que
  reinicia su lección en la conversación.
- **Evaluación y conversatorio inline**: el quiz se responde dentro del chat
  (tarjeta ancha) y el conversatorio al reprobar continúa en el mismo hilo.
- **Demo interactiva** desde el chat (botón ✨): artefacto de la unidad
  actual, sin necesitar guía generada.
- Nunca hay cambio de pantalla: header + chat + panel es toda la app.

## Tareas

- [x] `prompts.py`: `system_creacion`/`prompt_creacion` (JSON con listo/perfil).
- [x] `web.py`: `/api/creacion` (historial server-side, crea perfil+temario+
      curso.md al confirmar), `/api/plan`, `/api/estudio`, `/api/artefacto`
      (unidad); estado con `objetivo`, `completada`, `unidad_actual`.
- [x] `agente.py`: `turno_estudio` (lección continua + completadas),
      `artefacto_de_unidad`; `progreso.completadas` persistente.
- [x] `curso.py`: `plan_markdown`.
- [x] Front chat-total: layout header+chat+panel, modos (creación/estudio/
      quiz/conversatorio), panel con objetivos tachables y repasar, modal
      del plan con descarga .md, quiz y demos inline.
- [x] Config: subir `TIMEOUT_API_SEGUNDOS` a 180 s (generaciones largas).
- [x] Pruebas + E2E real (creación en 3+ turnos, estudio, repaso, artefacto).

## Pruebas

- `test_conversa_pregunta_y_al_confirmar_crea_el_curso`
- `test_con_curso_existente_da_409`
- `test_flujo_estudio_completa_y_permite_repasar`
- `test_endpoint_estudio`
- E2E real: 10/10 (incluye artefacto con timeout de 180 s).
