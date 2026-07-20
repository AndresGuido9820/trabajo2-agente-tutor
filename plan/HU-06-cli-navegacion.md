# HU-06 — CLI y navegación de unidades

**Como** estudiante **quiero** un menú claro para moverme por el curso
**para** estudiar, evaluarme y ver mi progreso sin fricción.
*(RF-3.1–RF-3.3; PA-01…PA-06, PA-11)*

## Criterios de aceptación

- `uv run tutor`: si no hay perfil → cuestionario (HU-01); si no hay temario →
  generarlo (HU-03); luego menú principal.
- El menú lista **todas** las unidades con estado: `pendiente` (sin contenido
  generado), `vista`, `evaluada (nota)`. Se puede entrar a cualquiera aunque
  no esté generada (se genera en ese momento con indicador de "generando…").
- Acciones: `[n]` entrar a unidad, `[e n]` evaluación de la unidad n,
  `[p]` progreso, `[r]` rehacer perfil (regenera curso previa confirmación),
  `[q]` salir.
- Lecciones renderizadas como Markdown con `rich`; entrada inválida en
  cualquier punto → mensaje claro y reintento.
- `Ctrl+C` sale limpio guardando progreso.

## Tareas

- [x] `ui.py`: menú, render de temario con estados, render de lección/quiz/
      progreso, spinner durante llamadas al LLM.
- [x] `agente.py`: orquestador que conecta perfil, curso, evaluación y
      progreso (la UI no llama al LLM directo).
- [x] `__main__.py` + script `tutor` en `pyproject.toml`.
- [x] Manejo global de `KeyboardInterrupt` y `ErrorLLM`/`ErrorConfiguracion`
      (mensajes finales sin traceback).
- [x] Pruebas (abajo) + pasada manual del checklist PA-01…PA-06.

## Pruebas

- `test_parsear_opcion_menu_valida_e_invalida`
- `test_entrar_a_unidad_no_generada_dispara_generacion` (fake)
- `test_estado_de_unidades_refleja_progreso`
- `test_flujo_completo_con_llm_falso` (integración: perfil→temario→lección→quiz)
