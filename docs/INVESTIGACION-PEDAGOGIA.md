# Investigación: pedagogía y prompting para la calidad del curso

Fecha: 2026-07-20. Investigación en fuentes de computing education, diseño de
evaluaciones y tutores LLM, hecha ANTES de escribir la versión final de los
prompts (`src/tutor/prompts.py`). Las "Recomendaciones directas" del final
son la especificación de los prompts v2.

---

## 1. Pedagogía de programación para novatos

- **PRIMM (Predict–Run–Investigate–Modify–Make)**: método con validación
  empírica; el alumno *lee y predice* antes de escribir. → La lección debe
  incluir, en orden: código de ejemplo + pregunta "¿qué imprime esto?"
  (predict), explicación línea a línea (investigate), ejercicio de
  modificación pequeña (modify) y solo al final creación (make).
  Fuentes: [PRIMM – Sentance et al., ACM](https://dl.acm.org/doi/10.1145/3287324.3287477),
  [PRIMM Portal](https://primmportal.com/).
- **Use–Modify–Create**: usar código ajeno → modificarlo → crear propio.
  Nunca "crea X desde cero" en las primeras lecciones de un tema.
  Fuente: [Raspberry Pi Foundation – pedagogy review](https://www.raspberrypi.org/app/uploads/2021/11/Teaching-programming-in-schools-pedagogy-review-Raspberry-Pi-Foundation.pdf)
  (la mejor síntesis única de evidencia: PRIMM, worked examples, subgoal
  labelling, tracing, Parsons).
- **Worked examples + subgoal labeling** (Margulieux & Catrambone 2016):
  ejemplos resueltos con comentarios que nombran el *propósito* de cada
  bloque ("1. leer entrada, 2. inicializar acumulador…"), no la sintaxis.
- **Parsons/completion problems**: "¿cuál es el orden correcto de estas
  líneas?" y "¿qué línea falta?" reducen carga cognitiva y son tan efectivos
  como escribir desde cero ([CHI 2021 – Ericson et al.](https://dl.acm.org/doi/10.1145/3411764.3445292)).
- **Carga cognitiva**: lecciones cortas, UN concepto nuevo por lección,
  ejemplos mínimos sin features aún no explicadas.
- **Jerarquía trace → explain → write**: trazar código y explicarlo precede a
  escribirlo. → Quizzes tempranos pesados hacia predict-the-output.
- **Bloom en programación**: evaluar Remember→Understand→Apply; los niveles
  bajos son necesarios pero no suficientes
  ([Ullah et al. 2020](https://onlinelibrary.wiley.com/doi/abs/10.1002/cae.22339),
  [taxonomía de Fuller et al.](https://kar.kent.ac.uk/23997/1/TaxonomyFuller.pdf)).
- **Misconceptions documentadas** (Sorva catalogó >160;
  [Notional Machines](https://dl.acm.org/doi/pdf/10.1145/2483710.2483713),
  [revisión](https://www.researchgate.net/publication/320679287_Students'_Misconceptions_and_Other_Difficulties_in_Introductory_Programming_A_Literature_Review)):
  - `a = a + 1` leído como ecuación imposible; asignación como "vínculo"
    permanente entre variables.
  - Creer que una variable guarda varios valores o su "historial".
  - Asignar la expresión sin evaluar; confundir nombre con valor.
  - `while` entendido como "se detiene apenas la condición se cumple";
    creer que la condición se re-evalúa dentro del cuerpo. Bucles y arrays
    son lo más difícil.
  - Raíz común: falta de **máquina nocional** (modelo mental de la
    ejecución). → Mostrar el estado de las variables paso a paso.
- **Secuenciación de referencia** ([CS50x](https://cs50.harvard.edu/x/syllabus/),
  [CS50P](https://cs50.harvard.edu/python/), freeCodeCamp): conceptos antes
  que sintaxis; orden consenso: variables/tipos → E/S → condicionales →
  bucles → colecciones → funciones → integración → dominio objetivo; repaso
  espaciado (cada lección reutiliza las 2-3 anteriores); proyectos visibles
  desde temprano (freeCodeCamp).

## 2. Diseño de quizzes de opción múltiple

- **Distractores = misconceptions reales**, escritos junto con la correcta;
  distractores absurdos invalidan el ítem
  ([NC State](https://teaching-resources.delta.ncsu.edu/multiplechoice/),
  [UWSOM](https://clime.washington.edu/wp-content/uploads/2020/07/WritingMultipleChoiceQuestions.pdf)).
- **Formato**: 4 opciones homogéneas en longitud/forma, stem autocontenido,
  sin negaciones, prohibido "todas/ninguna de las anteriores", posición de
  la correcta aleatorizada.
- **Feedback por opción**: explicar por qué el distractor tentador es
  incorrecto convierte el quiz en instrumento de enseñanza.
- **Comprensión, no memoria**: ≥50 % predict-the-output / find-the-bug;
  máximo una pregunta de definición por quiz.
- **Limitación de los LLM**: no generan distractores basados en errores
  reales de estudiantes espontáneamente; mejoran mucho si el prompt inyecta
  un banco de misconceptions explícito
  ([arXiv 2603.15547](https://arxiv.org/abs/2603.15547),
  [overgenerate-and-rank](https://arxiv.org/pdf/2405.05144)).

## 3. Prompting de LLMs para contenido educativo

- **Khanmigo, 7 pasos** ([blog Khan Academy](https://blog.khanacademy.org/khan-academys-7-step-approach-to-prompt-engineering-for-khanmigo/)):
  anclar en ciencia del aprendizaje; especificar tono/personalidad;
  "economía de lenguaje" (frases cortas, sin relleno); **los guardrails son
  el producto** (no dar la respuesta directa; y prever el "no sé": dar pista
  concreta, no repetir la pregunta).
- **Nivel como variable del prompt**: reglas distintas por nivel declarado
  (vocabulario permitido, cuánta pista dar); en principiante ningún término
  se usa sin definirse antes ([arXiv 2604.17460](https://arxiv.org/pdf/2604.17460)).
- **Analogías del dominio del estudiante** en todo el contenido (práctica
  estándar de tutores efectivos).
- **CoT y verificación**: el razonamiento aumenta la *confianza* del LLM
  incluso cuando se equivoca ([arXiv 2501.09775](https://arxiv.org/html/2501.09775v1));
  la verificación debe ser independiente: trazar el código y derivar la
  salida SIN mirar las opciones, re-resolver desde cero, confirmar que cada
  distractor es inequívocamente incorrecto y descartar ítems con dos
  opciones defendibles ([chain-of-verification](https://moazharu.medium.com/chain-of-verification-the-prompting-pattern-that-makes-llm-answers-check-themselves-f9563ea9e960)).

## 4. Personalización por perfil

- **"Nunca programó → front con JS"**: resultado visible temprano (DOM
  básico pronto: cambiar texto/color con un botón); analogías cotidianas;
  posponer temas sin payoff visual (closures, prototipos); proyecto visual
  pequeño por módulo.
- **"Sabe Excel → datos con Python"**: no es principiante absoluto; mapa de
  analogías canónico de la doc de pandas
  ([Comparison with spreadsheets](https://pandas.pydata.org/docs/getting_started/comparison/comparison_with_spreadsheets.html)):
  hoja=DataFrame, columna=Series, BUSCARV=merge, tabla dinámica=groupby.
  Enseñar explícitamente dónde se rompe la analogía (operaciones por
  columna, índice, reproducibilidad). Llegar a "cargar un CSV" en la lección
  2-3, no tras 10 lecciones de Python puro.
- **Motivación de adultos autodidactas** (investigación MOOC:
  [SDL en MOOCs](https://files.eric.ed.gov/fulltext/EJ1340532.pdf)):
  unidades pequeñas, metas explícitas, relevancia directa al objetivo
  declarado, feedback inmediato, autoevaluación frecuente. → Cada lección
  abre con "para qué te sirve respecto a TU meta" y cierra con un quick win.

---

## Recomendaciones directas para los prompts (spec de prompts v2)

System prompt: (1) persona adulto-a-adulto, sin condescendencia, economía de
lenguaje; (2) pistas graduales, con escape ante el "no sé"; (3) nivel,
objetivo e intereses como variables usadas en TODO el contenido; (4) en
principiante, ningún término sin definir antes ni features no vistas en
ejemplos; (5) máquina nocional: estado de variables paso a paso.

Temario: (6) secuencia variables→E/S→condicionales→bucles→colecciones→
funciones→proyecto→dominio, un concepto nuevo por unidad, repaso espaciado;
(7) personalización estructural (pandas en lección 2-3 para Excel; DOM en el
primer tercio para front); (8) cada módulo termina en resultado visible
ligado a la meta.

Lección: (9) estructura PRIMM (gancho → predicción → explicación con
analogía → ejemplo con subgoal labels → modificar → crear → recap en 3
bullets); (10) corta, un concepto, ejemplos mínimos; (11) sección "Error
típico" que desmonta la misconception documentada del tema.

Quiz: (12) 4 opciones homogéneas, sin todas/ninguna, correcta en posición
aleatoria; (13) ≥50 % predict-the-output/find-the-bug, ≤1 definición, cubrir
Remember→Understand→Apply; (14) inyectar banco de misconceptions y mapear
cada distractor a una; (15) verificación independiente antes de emitir
(trazar sin ver opciones, re-resolver, descartar ítems ambiguos).
