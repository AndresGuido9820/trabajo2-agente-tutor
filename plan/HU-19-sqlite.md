# HU-19 — Diseño del curso en base de datos (SQLite)

**Como** equipo **queremos** que el diseño del curso viva en una base de
datos — con el **prompt/guion de cada clase y su metadata** — **para** que
cada clase esté claramente definida y consultable, en lugar de JSONs sueltos.

Origen: retroalimentación de revisión.

## Criterios de aceptación

- Una sola BD SQLite por estudiante (`data/tutor.db`) con el esquema:
  `curso` (diseño: lenguaje, plan en Markdown, versión de prompts, fecha de
  creación), `clases` (una fila por clase: título, objetivo, subtemas, el
  **guion/prompt** con el que el tutor da la clase, la lección/guía
  generadas y fecha de actualización), `perfil`, `progreso` y `chat`
  (historial por conversación).
- Los JSON del formato anterior (`perfil.json`, `curso.json`,
  `progreso.json`, `chat.json`) se **migran automáticamente** una única vez.
- BD corrupta degrada igual que antes: perfil → rehacer cuestionario;
  progreso → vacío con advertencia; curso → regenerar temario.
- "Rehacer perfil" borra solo `curso` y `clases` (no el perfil ni los chats).
- En la conversación "Diseño del curso" se **muestra el diseño** (el plan
  desde la BD) y se puede descargar como `.md`.
- Las escrituras son transaccionales (sqlite), reemplazando el patrón
  tmp+rename.

## Tareas

- [x] `db.py`: esquema, apertura, documentos singleton, chat por canal,
      borrar curso, migración legacy best-effort.
- [x] `perfil.py`/`progreso.py`/`curso.py`: cargar/guardar sobre la BD
      (mismas firmas; `curso` ahora persiste por-clase con guion y metadata;
      `plan_md` como parte del diseño).
- [x] `agente.py`/`web.py`: una sola ruta `tutor.db`; chats vía BD;
      migración al arrancar el servidor.
- [x] Front: "Diseño del curso" muestra el plan desde la BD.
- [x] Pruebas: chat por canal, clases con prompt+metadata, borrar curso
      selectivo, migración completa e idempotente, basura tolerada.

## Pruebas

- `test_chat_por_canal` · `test_clases_guardan_prompt_y_metadata`
- `test_borrar_curso_no_toca_perfil_ni_chat`
- `test_migra_json_viejos_una_sola_vez` · `test_archivo_basura_como_db_es_tolerado`
