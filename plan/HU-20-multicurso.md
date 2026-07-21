# HU-20 — Mis cursos + diseño estructurado editable

**Como** estudiante **quiero** un menú con todos mis cursos (entrar a uno
muestra sus clases y su diseño; "Nuevo curso" abre el chat del prompt) y que
el diseño sea **información estructurada** editable **para** manejar varios
cursos y que el LLM siempre reciba el diseño limpio.

Origen: retroalimentación de revisión.

## Criterios de aceptación

- **Mis cursos** (vista inicial): tarjetas con nombre (el pedido original),
  lenguaje, progreso (aprobadas/total) y "Entrar"; tarjeta "＋ Nuevo curso"
  que crea un curso vacío y abre su chat de diseño.
- Cada curso vive aislado en `data/cursos/<id>/` (su `tutor.db` + su
  `curso.md`); el formato anterior de un solo curso migra a `cursos/1/`
  automáticamente. `← Mis cursos` en la barra lateral para volver.
- **Diseño estructurado**: `GET /api/diseno` expone {lenguaje, descripcion,
  clases[{indice, titulo, objetivo, conceptos}]} — exactamente lo que
  consumen los prompts. La edición manual es un formulario por clase
  (título/objetivo/subtemas) validado con las reglas del temario; al guardar
  se persiste en la tabla `clases` y se regenera el plan `.md` (que queda
  como vista/descarga, no como fuente).
- Los endpoints existentes operan sobre el **curso activo**
  (`POST /api/cursos/{id}/activar`); crear perfil/diseñar auto-crea el curso
  1 si no existe ninguno.

## Tareas

- [x] `web.py`: `_SesionCurso` por curso + `_Estado` multicurso con
      propiedades de compatibilidad; migración single→multi; endpoints
      `/api/cursos` (GET/POST), `/activar`, `/api/diseno` (GET/POST).
- [x] Front: vista "Mis cursos" con tarjetas y nuevo curso; `← Mis cursos`
      en la barra; editor estructurado del diseño (reemplaza el editor de
      texto crudo).
- [x] Pruebas: cursos independientes (estado/historial), activar 404,
      migración a `cursos/1`, diseño leer/editar/validar.

## Pruebas

- `test_dos_cursos_independientes` · `test_migra_curso_unico_a_cursos_1`
- `test_diseno_estructurado_se_lee_y_edita` · `test_diseno_invalido_da_400`
