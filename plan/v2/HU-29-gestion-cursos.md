# HU-29 — Gestión de cursos: renombrar, archivar y borrar

**Como** estudiante **quiero** renombrar, archivar y borrar mis cursos
**para** mantener ordenado "Mis cursos" sin tocar archivos a mano.

## Qué hace, explícito

1. **Renombrar**: cada tarjeta de "Mis cursos" tiene un menú `⋯` con
   "Renombrar" → input inline → el nombre se guarda en la BD del curso
   (columna `curso.nombre`; si está vacía se sigue derivando del pedido).
2. **Borrar**: opción "Borrar curso" con confirmación explícita escribiendo
   el nombre ("escribe *ventas* para confirmar") → mueve el directorio
   `cursos/<id>/` a `cursos/.papelera/<id>-<timestamp>/` (no destruye nada;
   la papelera se puede vaciar a mano). El curso desaparece del menú.
3. **Archivar**: alterna `curso.archivado` (0/1); los archivados se agrupan
   colapsados al final de "Mis cursos" y no cuentan en métricas del header.
4. Si se borra/archiva el curso ACTIVO, el activo pasa al primer curso
   visible (o a "sin cursos" → pantalla de nuevo curso).

## API

```
PATCH  /api/cursos/{id}        body {nombre?} | {archivado?} → {ok}
DELETE /api/cursos/{id}        → {ok}    (409 si el nombre confirmado no coincide: la
                                          confirmación es del front; el back solo borra)
GET    /api/cursos             → cada curso incluye {nombre, archivado}
```

## Tareas

- [x] `db.py`: columnas `nombre`, `archivado` (ALTER TABLE tolerante).
- [x] `web.py`: PATCH/DELETE + papelera (shutil.move) + reasignar activo.
- [x] Front `MisCursos.jsx`: menú ⋯ (Mantine Menu), modal de confirmación
      de borrado con input del nombre, sección "Archivados" colapsada.
- [x] Pruebas: renombrar persiste; borrar mueve a papelera y reasigna
      activo; archivado sale del listado principal; 404 en id inexistente.

## Casos borde

- Borrar el único curso → estado "sin cursos" y pantalla de creación.
- Nombre vacío al renombrar → 400. — Id inexistente → 404.
- Papelera ya contiene un id igual → sufijo timestamp evita colisión.

## Pruebas

`test_renombrar_persiste_y_lista` · `test_borrar_mueve_a_papelera_y_reasigna_activo`
· `test_archivar_saca_del_listado` · `test_borrar_unico_curso_deja_sin_cursos`
