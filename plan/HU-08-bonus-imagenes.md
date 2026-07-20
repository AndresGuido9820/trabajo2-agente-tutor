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

- [ ] Investigar API disponible (OpenAI Images u otra con crédito del equipo)
      y anotar decisión en HALLAZGOS.
- [ ] `imagenes.py`: generación del prompt visual a partir de la lección,
      llamada a la API, cache por unidad, degradación silenciosa→log.
- [ ] Integrar a `generar_leccion` detrás del flag.
- [ ] Incluir imágenes en `exportar_curso.py`.
- [ ] Pruebas: flag apagado no llama a la API (fake); fallo de imagen no rompe
      la lección; cache evita segunda llamada.
