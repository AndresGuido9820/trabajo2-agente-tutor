# HU-26 — Evaluaciones robustas: más preguntas, dificultad mixta y banco

**Como** estudiante **quiero** evaluaciones finales más completas — más
preguntas, de dificultad variada y sin repetirse entre intentos — **para**
que aprobar signifique dominio real de la clase.

## Criterios de aceptación

- La evaluación final pasa de 4 a **6-8 preguntas** (`PREGUNTAS_POR_QUIZ`
  configurable por clase según nº de objetivos: 2 por objetivo).
- **Dificultad mixta y etiquetada**: cada pregunta trae `nivel`
  ("recordar" | "comprender" | "aplicar", taxonomía de Bloom); el prompt
  exige ≥50 % comprender/aplicar y máximo 1 de recordar. La nota pondera:
  aplicar ×1.5, comprender ×1.0, recordar ×0.5 (redondeada a 0-100; la
  calificación sigue siendo local).
- **Banco por clase**: las preguntas generadas se acumulan en la BD
  (`clases.banco_preguntas`); cada intento toma un subconjunto que **no
  repite enunciados** de los últimos 2 intentos y se completa generando
  variantes nuevas si el banco no alcanza.
- Los conceptos fallados en quices intermedios (HU-24) reciben al menos 1
  pregunta dirigida en la evaluación final.
- El desglose del resultado muestra el nivel de cada pregunta y un resumen
  por concepto ("bucles: 2/3").

## Interfaz

```python
# evaluacion.py
@dataclass(frozen=True) class Pregunta:  # + nivel: str
def calificar(...)  # nota ponderada por nivel

# db.py / curso.py
clases.banco_preguntas TEXT  # JSON: lista de preguntas con metadata de uso

# API (sin cambios de forma): /api/quiz/{i} devuelve además "nivel" por
# pregunta (nunca la correcta) y /calificar devuelve resumen_por_concepto.
```

## Tareas

- [ ] `prompts.py`: prompt de quiz con niveles Bloom etiquetados y cuota
      mínima de comprender/aplicar; variantes que esquivan el banco.
- [ ] `evaluacion.py`: `nivel` en el modelo + validación + nota ponderada +
      resumen por concepto.
- [ ] `db.py`/`curso.py`: columna `banco_preguntas` con metadata de uso
      (intento en que salió); selección sin repetición.
- [ ] `agente.py`: armar el quiz mezclando banco + variantes nuevas +
      preguntas dirigidas a fallados.
- [ ] Front: badge de nivel por pregunta y resumen por concepto en el
      resultado.
- [ ] Pruebas: ponderación, cuotas de nivel, no-repetición entre intentos,
      pregunta dirigida a fallados, banco persiste.

## Pruebas

- `test_nota_ponderada_por_nivel`
- `test_quiz_respeta_cuotas_de_bloom`
- `test_reintento_no_repite_enunciados_de_ultimos_2_intentos`
- `test_fallados_intermedios_reciben_pregunta_dirigida`
- `test_banco_persiste_en_bd`
