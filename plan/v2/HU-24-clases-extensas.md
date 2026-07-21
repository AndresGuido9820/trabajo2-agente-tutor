# HU-24 — Clases más extensas: guion por objetivos con quices intermedios

**Como** estudiante **quiero** clases con más hilo y profundidad —
organizadas por objetivos, con un mini-quiz al cerrar cada objetivo y la
evaluación grande al final — **para** consolidar cada idea antes de pasar a
la siguiente en vez de correr por la lección.

## Contexto

Hoy el guion tiene 5-8 pasos PRIMM planos y un solo quiz al final. La
estructura nueva agrupa los pasos **por objetivo de aprendizaje** y verifica
cada objetivo en el momento (mastery learning, estilo Khan Academy).

## Criterios de aceptación

- El guion de la clase se genera **estructurado por objetivos**: 3-4
  objetivos por clase; cada objetivo trae su secuencia PRIMM propia (gancho
  → predicción → explicación → error típico → práctica), 4-7 pasos por
  objetivo → clases de 15-25 turnos en total.
- Al terminar los pasos de un objetivo, el tutor lanza un **quiz intermedio
  de 2 preguntas** (mismo contrato del quiz actual, calificación local, en
  el chat). Acertar ≥1 marca el objetivo como cumplido y sigue; fallar ambas
  → el tutor repasa ese objetivo con un ejemplo nuevo antes de reintentar
  (máx. 1 repaso; luego avanza igual y lo anota para la evaluación final).
- La **evaluación final** solo se ofrece cuando todos los objetivos de la
  clase se recorrieron; sus preguntas priorizan los conceptos fallados en
  los quices intermedios.
- Los quices intermedios dan puntos (⭐ 5 por acierto) y quedan en el
  historial del chat como tarjetas.
- Compatibilidad: los guiones v1 existentes siguen funcionando (migración
  perezosa: si el guion no tiene objetivos agrupados, se usa el flujo viejo).

## Interfaz

```python
# curso.py
@dataclass(frozen=True) class ObjetivoGuion:
    objetivo: str
    pasos: list[PasoLeccion]
    quiz: list[Pregunta]          # 2 preguntas intermedias, pre-generadas

@dataclass(frozen=True) class GuionLeccionV2:
    objetivos: list[ObjetivoGuion]

# agente.py
def turno_estudio(...)  # añade al dict: objetivo_actual, objetivos_total,
                        # objetivo_cumplido: bool, quiz_intermedio: list|None

# API
POST /api/estudio                    -> + {objetivo, objetivos_total, quiz_intermedio?}
POST /api/estudio/quiz-intermedio    -> {respuestas} -> {aciertos, cumplido, texto}
```

BD: el guion v2 se guarda en la columna `clases.guion` (mismo JSON blob,
campo `"version": 2`).

## Tareas

- [ ] `prompts.py`: `prompt_guion_v2` (objetivos con secuencia PRIMM y las 2
      preguntas del quiz intermedio por objetivo, con verificación
      independiente) + reglas de repaso en `system_leccion`.
- [ ] `curso.py`: modelos v2 + `validar_guion_v2` + carga retro-compatible.
- [ ] `agente.py`: sesión con (objetivo, paso) en vez de paso plano; lanzar
      quiz intermedio al cerrar objetivo; lógica de repaso y de anotar
      fallados para la evaluación final.
- [ ] `web.py` + front: tarjeta de quiz intermedio en el chat (reusar
      QuizCard con 2 preguntas), avance "objetivo 2/4 · paso 3/6".
- [ ] Pruebas: guion v2 válido/ inválido, flujo objetivo→quiz→cumplido,
      fallo doble→repaso→avance, retrocompatibilidad guion v1, puntos.
- [ ] Humo real: una clase completa; verificar longitud (≥15 turnos) y que
      el quiz intermedio evalúa el objetivo recién visto.

## Pruebas

- `test_guion_v2_valida_objetivos_y_quices`
- `test_cerrar_objetivo_lanza_quiz_intermedio`
- `test_fallar_quiz_intermedio_repasa_una_vez`
- `test_guion_v1_sigue_funcionando`
- `test_evaluacion_final_prioriza_fallados`
