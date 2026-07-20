# HU-14 — Renovación de UX e interacción total con el agente

**Como** estudiante **quiero** una experiencia pulida (esperas explicadas,
retroalimentación inmediata, accesible) donde pueda **interactuar con el
agente en todo momento** — preguntarle en cualquier sección y pedirle demos
interactivas — **para** aprender sin fricción y con el tutor siempre a mano.

Origen: retroalimentación de revisión + auditoría contra guías abiertas de
producto/UX (`docs/INVESTIGACION-UX.md`, con fuentes).

## Criterios de aceptación

- **Chat en la guía**: cada sección tiene "💬 Preguntar al tutor" (socrático,
  con la sección como contexto y SIN revelar el checkpoint) con historial de
  sesión, sugerencias de arranque, Enter para enviar y typing indicator.
- **Mini-artefactos (patrón Artifacts)**: "✨ Ver demo interactiva" genera
  una página HTML autocontenida (sin recursos externos) que ilustra el
  concepto de la sección; se muestra en `iframe sandbox="allow-scripts"` y
  queda cacheada en `curso.json`.
- **Esperas**: loader por fases con expectativa de tiempo para curso/guía/
  quiz; skeletons; generación de guía **no bloqueante** (volver al curso,
  badge "Generando…", toast al terminar); **prefetch del quiz** en la última
  sección; el quiz se basa en la guía (sin regenerar lección).
- **Sistema base**: paleta dark AA, focus-visible, `prefers-reduced-motion`,
  badges con texto (no solo emoji/color), `aria-live` en feedback dinámico,
  70ch de ancho de lectura.
- **Sidebar**: un CTA por unidad según estado, siguiente unidad resaltada,
  progreso "N de M" con barra en el header.
- **Resultado**: aprobado = celebración ≤500 ms + toast; reprobado = tono de
  crecimiento + sugerencias "Explícame la pregunta X" en el conversatorio.
- **Formulario**: labels + hints, chips de sugerencia, autofocus, mensaje de
  valor antes de pedir datos, errores inline (nunca en toast).

## Tareas

- [x] Backend: `preguntar_guia` + `artefacto_de_seccion` (cache persistente)
      + endpoints `/api/guia/{i}/pregunta` y `/api/guia/{i}/artefacto`;
      quiz basado en la guía cuando existe.
- [x] `prompts.py`: `prompt_artefacto` (HTML autocontenido, tema oscuro,
      interactivo, mismo ejemplo de la sección).
- [x] Front: rediseño completo con el sistema base y los patrones del
      informe (fases, skeletons, prefetch, CTA único, Peak-End, a11y).
- [x] Pruebas backend (pregunta con contexto sin filtrar respuestas,
      artefacto cache/persistencia/fences, endpoints) + humo real.
- [x] `docs/INVESTIGACION-UX.md` + HALLAZGOS.

## Pruebas

- `test_incluye_seccion_y_reglas_socraticas` / `test_no_filtra_explicacion`
- `test_artefacto_genera_cachea_y_persiste` / `test_tolera_fences`
- `test_endpoint_pregunta_responde_y_valida`
- Humo real: pregunta socrática + artefacto autocontenido (verificado).
