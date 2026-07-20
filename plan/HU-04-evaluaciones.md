# HU-04 — Evaluaciones y calificación

**Como** estudiante **quiero** quizzes por unidad con retroalimentación
**para** saber si de verdad entendí antes de avanzar. *(RF-2.3; PA-05)*

## Criterios de aceptación

- Cada unidad ofrece un quiz de `PREGUNTAS_POR_QUIZ = 4` preguntas de opción
  múltiple generado por el LLM a partir de la lección (few-shot con un ejemplo
  de formato).
- El JSON del quiz incluye por pregunta: enunciado, opciones, índice de la
  correcta y **explicación** (mitiga respuestas correctas erróneas).
- La calificación es local (comparar índices, sin LLM): nota 0–100 y
  retroalimentación por pregunta (correcta/incorrecta + explicación).
- Respuestas del estudiante validadas (solo letras de opciones existentes).
- El resultado se registra en el progreso (HU-05) y alimenta la adaptación de
  lecciones siguientes (HU-03).

## Interfaz

```python
@dataclass(frozen=True)
class Pregunta:    # enunciado, opciones: list[str], correcta: int, explicacion
@dataclass(frozen=True)
class Quiz:        # unidad: int, preguntas: list[Pregunta]
@dataclass(frozen=True)
class Resultado:   # unidad, nota: int (0-100), fallos: list[int], fecha

def generar_quiz(cliente: ClienteLLM, leccion_md: str, unidad: int) -> Quiz
def calificar(quiz: Quiz, respuestas: list[int]) -> Resultado
```

## Tareas

- [x] Prompt de quiz en `prompts.py` con ejemplo few-shot y esquema JSON.
- [x] `evaluacion.py`: modelos, validador de esquema, `generar_quiz`,
      `calificar`, validación de respuestas del usuario.
- [x] (completada en HU-06) Presentación del resultado (nota + detalle por pregunta) en la CLI.
- [x] Pruebas (abajo).

## Pruebas

- `test_generar_quiz_valida_esquema_y_numero_de_preguntas`
- `test_quiz_rechaza_indice_correcta_fuera_de_opciones`
- `test_calificar_todo_correcto_da_100`
- `test_calificar_todo_incorrecto_da_0_y_lista_fallos`
- `test_calificar_mixto_calcula_nota_proporcional`
- `test_respuesta_usuario_invalida_reintenta`
