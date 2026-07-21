# Plan v2 — Profundidad, evaluación y experiencia de clase

Roadmap de la siguiente ola de mejoras sobre el producto entregado (v1).
Cada mejora es una HU en esta carpeta, con criterios verificables y sus
pruebas. Orden de implementación sugerido (dependencias primero):

| # | HU | Qué mejora | Depende de |
|---|----|------------|------------|
| 1 | [HU-24](HU-24-clases-extensas.md) | Clases más largas y con más hilo: guion por objetivos con quices intermedios | — |
| 2 | [HU-25](HU-25-panel-clase.md) | Panel lateral por clase: objetivos que se marcan en vivo + progreso | HU-24 |
| 3 | [HU-26](HU-26-evaluaciones-robustas.md) | Evaluaciones con más preguntas, dificultad mixta y banco por clase | HU-24 |
| 4 | [HU-27](HU-27-mejores-artefactos.md) | Mejores artefactos: plantillas por concepto, verificación y regenerar | — |
| 5 | [HU-28](HU-28-practica-con-codigo.md) | Práctica con código real: retos verificados con Pyodide | HU-24, HU-27 |

## Principios (heredados de v1)

- Toda salida del LLM que el sistema consume se pide como JSON con esquema y
  se valida (`pedir_json`); la calificación siempre es local y determinista.
- La estructura pedagógica se especifica en los prompts (PRIMM,
  misconceptions, verificación independiente): no se asume que emerge.
- Cada HU cierra con pruebas con dobles del LLM + humo real, ruff/mypy en
  verde, y su entrada en `docs/HALLAZGOS.md`.
- Nada de dark patterns: la gamificación suma (puntos/racha), nunca castiga.

## Métricas de éxito de la ola

- Una clase típica pasa de ~8 turnos a 15-25 turnos con 2-3 quices
  intermedios (más hilo, misma claridad).
- La evaluación final pasa de 4 a 6-8 preguntas con al menos 2 niveles de
  dificultad, sin repetir enunciados entre intentos.
- El estudiante ve en todo momento qué objetivos lleva cumplidos de la clase
  sin salir del chat.
- ≥90 % de los artefactos generados pasan la verificación automática al
  primer intento.
