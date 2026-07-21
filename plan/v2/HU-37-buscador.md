# HU-37 — Buscador global (⌘K) sobre cursos, clases y conversaciones

**Como** estudiante **quiero** buscar cualquier cosa que vi ("¿dónde me
explicó groupby?") **para** volver a ese punto sin navegar a ciegas.

## Qué hace, explícito

1. `⌘K` / `Ctrl+K` (o el botón 🔎 de la barra) abre un **spotlight**
   (Mantine Spotlight) con un input único.
2. Busca, mientras escribes (debounce 250 ms), en:
   - **Clases** (título, objetivo, subtemas) de todos los cursos;
   - **Mensajes** del chat (tabla `chat`, LIKE case-insensitive, con
     fragmento resaltado);
   - **Acciones** ("Nuevo curso", "Mi progreso", "Repaso del día").
3. Resultados agrupados (Clases / Conversaciones / Acciones), máximo 8 por
   grupo, cada uno con su contexto ("Clase 3 · Curso de ventas").
4. Elegir un resultado navega: clase → abre su chat; mensaje → abre la
   clase Y hace scroll al mensaje (se localiza por id, resaltado 2 s);
   acción → la ejecuta.
5. Backend hace la búsqueda (SQL sobre todas las BDs de cursos); el front
   no descarga historiales completos.

## API

```
GET /api/buscar?q=groupby → {
  clases:   [{curso: 1, indice: 3, titulo, fragmento}],
  mensajes: [{curso: 1, canal: "u3", id: 412, rol, fragmento}],
}
```

Escapando `%`/`_` del LIKE; mínimo 2 caracteres; límite 8+8.

## Tareas

- [x] `db.py`: `buscar_mensajes(ruta, q)` (LIKE + snippet ±60 chars).
- [x] `web.py`: endpoint que consulta todos los cursos (títulos desde
      `clases`, mensajes desde `chat`).
- [x] Front: Spotlight (@mantine/spotlight), atajo, grupos, navegación con
      scroll-al-mensaje (los mensajes del historial ya tienen id de BD:
      exponerlo en /api/historial y usarlo como anchor).
- [x] Pruebas: búsqueda en clases y mensajes, escape de LIKE, mínimo de
      caracteres, límites, multi-curso.

## Casos borde

- Query con `%` o `_` literales → escapadas. — Cursos archivados → se
  incluyen marcados "(archivado)". — 0 resultados → estado vacío con tip.

## Pruebas

`test_buscar_en_clases_y_mensajes_multicurso` · `test_like_escapado`
· `test_minimo_2_caracteres_y_limites` · `test_snippet_con_contexto`
