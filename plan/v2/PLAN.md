# Plan v2 — Profundidad, evaluación y experiencia de clase

Roadmap de la siguiente ola de mejoras sobre el producto entregado (v1).
Cada mejora es una HU en esta carpeta, con criterios verificables y sus
pruebas. Orden de implementación sugerido (dependencias primero).
**Estado: las 16 HUs del plan v2 fueron ejecutadas el 2026-07-21.**

| # | HU | Qué mejora | Depende de |
|---|----|------------|------------|
| 1 | ✅ [HU-24](HU-24-clases-extensas.md) | Clases más largas y con más hilo: guion por objetivos con quices intermedios | — |
| 2 | ✅ [HU-25](HU-25-panel-clase.md) | Panel lateral por clase: objetivos que se marcan en vivo + progreso | HU-24 |
| 3 | ✅ [HU-26](HU-26-evaluaciones-robustas.md) | Evaluaciones con más preguntas, dificultad mixta y banco por clase | HU-24 |
| 4 | ✅ [HU-27](HU-27-mejores-artefactos.md) | Mejores artefactos: plantillas por concepto, verificación y regenerar | — |
| 5 | ✅ [HU-28](HU-28-practica-con-codigo.md) | Práctica con código real: retos verificados con Pyodide | HU-24, HU-27 |

## Segunda tanda (calidad de producto ×1000) — EJECUTADA 2026-07-21

| # | HU | Qué mejora | Depende de |
|---|----|------------|------------|
| 6 | ✅ [HU-29](HU-29-gestion-cursos.md) | Renombrar, archivar y borrar cursos (con papelera) | — |
| 7 | ✅ [HU-36](HU-36-tema-y-preferencias.md) | Tema claro/oscuro y tamaño de texto | — |
| 8 | ✅ [HU-30](HU-30-bienvenida-inteligente.md) | "¿Dónde iba?": reencuentro al volver a una clase | — |
| 9 | ✅ [HU-31](HU-31-estadisticas.md) | Mi progreso: actividad, notas y conceptos débiles | — |
| 10 | ✅ [HU-33](HU-33-exportar-curso.md) | Exportar el curso completo (.zip de Markdown) | HU-29 |
| 11 | ✅ [HU-39](HU-39-modelos-por-tarea.md) | Modelo por tarea (rápido en chat, potente en diseño) + registro de uso | — |
| 12 | ✅ [HU-34](HU-34-robustez-front.md) | Robustez: desconexión, reintentos, borradores | — |
| 13 | ✅ [HU-37](HU-37-buscador.md) | Buscador global ⌘K (clases y conversaciones) | — |
| 14 | ✅ [HU-38](HU-38-accesibilidad.md) | Accesibilidad y teclado (axe sin violaciones) | HU-36 |
| 15 | ✅ [HU-32](HU-32-repaso-espaciado.md) | Repaso del día (repetición espaciada 1-3-7) | HU-26 |
| 16 | ✅ [HU-35](HU-35-streaming.md) | Streaming SSE: el tutor escribe en vivo | — |

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
