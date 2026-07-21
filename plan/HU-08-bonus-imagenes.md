# HU-08 — (Bonus) Imágenes generadas por IA

**Como** estudiante **quiero** ilustraciones en las lecciones **para** que el
material sea más memorable. *(RF-3.4; PA-14)* — Solo si HU-01…HU-07 están
cerradas antes de la entrega.

## Criterios de aceptación

- Al generar una lección se genera (o reutiliza de cache) 1 imagen ilustrativa
  del concepto central, guardada en `data/imagenes/unidad-<n>.png`.
- La lección referencia la imagen; en la CLI se muestra la ruta (y en los
  cursos de muestra exportados se incrusta en el Markdown).
- Si la API de imágenes falla, la lección funciona igual (la imagen es
  opcional; error → warning en log, nunca bloquea).
- Feature detrás de un flag `TUTOR_IMAGENES=1` (por costo).

## Tareas

- [x] Investigar API disponible (OpenAI Images u otra con crédito del equipo)
      y anotar decisión en HALLAZGOS.
- [x] `imagenes.py`: generación del prompt visual a partir de la lección,
      llamada a la API, cache por unidad, degradación silenciosa→log.
- [x] Integrar a `generar_leccion` detrás del flag.
- [x] Incluir imágenes en `exportar_curso.py`.
- [x] Pruebas: flag apagado no llama a la API (fake); fallo de imagen no rompe
      la lección; cache evita segunda llamada.


## Nota de ejecución (2026-07-21)

Implementada sobre la app web actual (la spec era de la era CLI): la
ilustración se genera bajo demanda vía `GET /api/clase/{i}/imagen` (cache
en `data/cursos/<id>/imagenes/unidad-<n>.png`), se muestra en el panel de
la clase y se incrusta en el .zip exportado (HU-33). API elegida: OpenAI
Images `gpt-image-1` (calidad low, misma API key: cero fricción). Humo
real: 1 imagen generada y revisada (estilo flat, sin texto, fiel al tema).
