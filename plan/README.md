# Plan — Historias de Usuario

Cada HU es un archivo con su historia, criterios de aceptación, tareas
(checkboxes = estado real) y pruebas. Se implementan en orden, una rama
`feature/hu-XX-*` por HU (Git Flow, ver RULES.md).

| HU | Título | Rúbrica que ataca | Depende de |
|---|---|---|---|
| [HU-00](HU-00-esqueleto.md) | Esqueleto del proyecto y calidad | Técnica | — |
| [HU-01](HU-01-perfil-estudiante.md) | Perfil del estudiante (entradas) | Técnica | HU-00 |
| [HU-02](HU-02-cliente-llm.md) | Cliente LLM con manejo de errores | Técnica | HU-00 |
| [HU-03](HU-03-generacion-curso.md) | Generación de temario y lecciones | Prompts + Curso | HU-01, HU-02 |
| [HU-04](HU-04-evaluaciones.md) | Evaluaciones y calificación | Prompts + Curso | HU-03 |
| [HU-05](HU-05-progreso.md) | Progreso persistente | Técnica | HU-01 |
| [HU-06](HU-06-cli-navegacion.md) | CLI y navegación de unidades | Técnica (UI) | HU-01…HU-05 |
| [HU-07](HU-07-entregables.md) | Cursos de muestra, reporte y video | Docs + Curso | HU-06 |
| [HU-08](HU-08-bonus-imagenes.md) | *(Bonus)* Imágenes generadas por IA | Bonus | HU-06 |
