# HU-33 — Exportar el curso completo (paquete de estudio)

**Como** estudiante **quiero** descargar mi curso completo — diseño,
conversaciones de cada clase y mis resultados — **para** estudiar offline,
archivarlo o compartirlo.

## Qué hace, explícito

1. En "Mis cursos", el menú `⋯` (HU-29) añade **"Exportar (.zip)"**.
2. El zip contiene Markdown legible, generado del contenido real:
   ```
   mi-curso/
     00-diseno.md              # el plan (curso.md) + metadata (fecha, lenguaje)
     clase-01-variables.md     # transcripción limpia del chat de la clase
     clase-02-csv.md           #  (Tú: / Profe Bit:), quices con resultado
     resultados.md             # notas por intento, puntos, objetivos cumplidos
   ```
3. Las transcripciones marcan los hitos: `> 🎯 Evaluación: 85/100 —
   aprobada`, `> 🎉 Clase completada`.
4. La descarga es un endpoint que arma el zip EN MEMORIA (zipfile de
   stdlib) desde la BD — nada de tocar el filesystem del curso.
5. No incluye artefactos HTML ni datos sensibles (no hay); tamaño típico
   < 1 MB.

## API

```
GET /api/cursos/{id}/exportar → application/zip
    (404 si no existe; 409 si el curso no tiene diseño aún)
```

## Tareas

- [x] `exportar.py` (módulo nuevo): `paquete_zip(dir_curso) -> bytes` —
      lee BD (plan, chats por canal, progreso) y arma los .md.
- [x] `web.py`: endpoint con `Response(content=..., media_type=zip,
      headers Content-Disposition)`.
- [x] Front: opción en el menú ⋯ (usa `window.location` al endpoint).
- [x] Pruebas: estructura del zip, transcripción con roles e hitos,
      resultados correctos, 404/409.

## Casos borde

- Clase sin conversación → su .md dice "(sin conversación todavía)".
- Nombres de clase con caracteres raros → slug seguro para el filename.
- Curso enorme → transcripciones completas igual (es local, sin límite
  duro; documentado).

## Pruebas

`test_zip_contiene_diseno_clases_y_resultados` · `test_transcripcion_roles_e_hitos`
· `test_slug_de_nombres_raros` · `test_exportar_sin_diseno_409`
