# HU-07 — Entregables: cursos de muestra, reporte y video

**Como** equipo **queremos** producir los entregables E2–E4 del SPEC **para**
cumplir la rúbrica completa. *(PA-10; rúbrica de documentación 10 % y curso 20 %)*

## Criterios de aceptación

- **Cursos de muestra (E4):** ≥ 2 cursos completos generados con API real, en
  `entregables/cursos-muestra/<perfil>/`, con perfiles y **lenguajes
  distintos** (p. ej. "cero experiencia → front con JavaScript" y "usa Excel →
  ciencia de datos con Python"). Cada uno incluye perfil usado, temario,
  lecciones y un quiz con resultado.
- **Reporte técnico (E3):** 1000–1500 palabras en `entregables/REPORTE.md`:
  enfoque, arquitectura, ingeniería de prompts (con ejemplos antes/después),
  desafíos y soluciones (desde HALLAZGOS.md), reflexión sobre capacidades y
  limitaciones de LLMs, y tabla de contribución individual.
- **Video (E2):** guion en `entregables/GUION-VIDEO.md` de 5–7 min: demo con
  los dos perfiles, todos los miembros hablan y el video rotula quién habla.
- Revisión de calidad del contenido generado: sin errores técnicos en el
  código de las lecciones, tono motivador consistente.

## Tareas

- [ ] Script `scripts/exportar_curso.py`: corre el flujo con un perfil dado y
      exporta temario+lecciones+quiz a Markdown.
- [ ] Generar curso muestra 1 (front/JavaScript, principiante absoluto).
- [ ] Generar curso muestra 2 (datos/Python, nivel básico).
- [ ] Revisar manualmente ambos cursos (código corre, quizzes correctos).
- [ ] Redactar `entregables/REPORTE.md` (1000–1500 palabras, contar palabras).
- [ ] Redactar `entregables/GUION-VIDEO.md` con reparto de quién dice qué.
- [ ] Grabar y editar el video con rótulos de nombre.
- [ ] Checklist final PA-01…PA-14 de SPEC.md marcado.

## Pruebas

- Verificación manual: word count del reporte en rango; video 5–7 min;
  cursos de muestra cumplen PA-10.
