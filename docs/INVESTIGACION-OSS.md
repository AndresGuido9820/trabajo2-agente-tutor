# Investigación: qué copiamos de los mejores proyectos open source

Fecha: 2026-07-20. Encuesta de los referentes OSS de enseñanza interactiva
de programación, con decisión explícita de qué adoptamos ya (HU-13) y qué
queda como trabajo futuro (sección del reporte).

## Referentes revisados (con fuente)

- **freeCodeCamp** ([repo](https://github.com/freeCodeCamp/freeCodeCamp)):
  retos declarativos test-driven; regla de granularidad (1 concepto,
  resoluble en ~2 min); **feedback pedagógico por aserción/opción**, no
  genérico; MCQ con feedback específico por distractor.
- **Exercism** ([docs](https://exercism.org/docs/building/tracks/concept-exercises)):
  concept vs practice exercises; **syllabus tree** (`teaches`/`prerequisites`
  por ejercicio → desbloqueo por concepto); pistas escalonadas (`hints.md`);
  `design.md` con learning goals y out-of-scope explícito.
- **Runestone / PrairieLearn**
  ([directivas](https://runestone.academy/ns/books/published/authorguide/directives.html),
  [PrairieLearn](https://github.com/PrairieLearn/PrairieLearn)): catálogo de
  tipos de ítem embebible (Parsons drag&drop, fill-in-the-blank por regex,
  clickable-code, CodeLens); evidencia de Parsons (igual aprendizaje, menos
  tiempo — [ITiCSE WG](https://dl.acm.org/doi/10.1145/3623762.3633498),
  [ICER'22 adaptativos](https://web.eecs.umich.edu/~xwanghci/papers/ICER22.pdf));
  `autoPoints` decrecientes por intento (≙ nuestro 10/5/0, validado a
  escala); **variantes nuevas del ítem en cada reintento**.
- **futurecoder** ([repo](https://github.com/alexmojaki/futurecoder), MIT) +
  **Pyodide** ([docs](https://pyodide.org)): Python 100 % en el navegador
  (WASM, sin backend de ejecución); pasos verificados ejecutando el código;
  revelar la solución por partes; tracebacks amigables.
- **Duolingo** ([half-life regression](https://github.com/duolingo/halflife-regression),
  casos A/B publicados): lo que funciona — **streaks + meta diaria** (+30 %
  finalización con badges), XP visible, repaso espaciado con modelo. Lo que
  NO copiamos (dark patterns documentados): vidas/corazones y ligas.
- **Tutores LLM OSS**: [tutor-gpt/Bloom](https://github.com/plastic-labs/tutor-gpt)
  (patrón **thought chain → response chain**: inferir primero qué entendió
  mal el alumno y responder condicionado a eso; memoria persistente del
  estudiante), [DeepTutor](https://github.com/HKUDS/DeepTutor),
  [OpenTutor](https://github.com/zijinz456/OpenTutor) (FSRS + BKT),
  [SocraticLM](https://github.com/Ljyustc/SocraticLM) (rúbrica pedagógica).
- **Python Tutor** ([pythontutor.com](https://pythontutor.com), Guo
  SIGCSE'13): visualizador de la máquina nocional, embebible por URL/iframe;
  Runestone lo empaqueta como `codelens`.

## Adoptado en HU-13 (horas)

| # | Mejora | Copiado de |
|---|---|---|
| 1 | "▶ Pruébalo aquí": ejecutar los ejemplos Python de la guía en el navegador con Pyodide (client-side, cero backend) | futurecoder, Runestone `activecode` |
| 2 | Racha diaria 🔥 + XP visibles y persistentes (sin vidas ni ligas) | Duolingo (evidencia A/B; anti-patrones excluidos) |
| 3 | "🔍 Ver paso a paso": enlace del ejemplo a Python Tutor (máquina nocional) | Python Tutor / Runestone `codelens` |
| 4 | Variantes al reintentar la evaluación (no repetir preguntas literales) | PrairieLearn, khan-exercises |
| 5 | Theory-of-mind en el conversatorio: el prompt recibe el historial de desempeño y primero infiere el malentendido | tutor-gpt/Bloom (thought → response) |

## Trabajo futuro (para el reporte)

1. Checkpoints de código auto-verificados con tests en Pyodide (fCC/futurecoder) — convierte el producto de quiz-driven a code-driven.
2. Grafo de conceptos con prerequisitos como estructura del curso (Exercism syllabus trees).
3. Repaso espaciado por concepto (half-life regression de Duolingo o FSRS de OpenTutor).
4. Modelo persistente del estudiante (BKT / Honcho-like) que gobierne dificultad y repaso.
5. Tipos de checkpoint adicionales: Parsons adaptativos ([js-parsons](https://github.com/js-parsons/js-parsons)), fill-in-the-blank por regex, clickable-code (Runestone).
6. Visualizador de ejecución propio (traza `sys.settrace` + render de estado) y evaluación de calidad docente con rúbrica estilo SocraticLM.
