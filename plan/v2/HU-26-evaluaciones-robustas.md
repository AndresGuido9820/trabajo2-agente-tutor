# HU-26 — Evaluaciones robustas: más preguntas, dificultad mixta y banco

**Como** estudiante **quiero** evaluaciones finales más completas — más
preguntas, de dificultad variada, sin repetirse entre intentos y con nota
que pese lo difícil — **para** que aprobar signifique dominio real.

## 1. Qué hace esta HU, explícito

Hoy la evaluación final son 4 preguntas iguales en peso, y aunque los
reintentos piden "variantes", no hay memoria real entre intentos. Esta HU
la convierte en un instrumento serio:

1. **Más preguntas**: la evaluación pasa a `2 × nº de objetivos` preguntas
   (6-8 típicamente; mínimo 6). El tamaño sale del guion v2 (HU-24).

2. **Dificultad etiquetada (Bloom) y con cuotas.** Cada pregunta trae
   `nivel`: `recordar` (definición), `comprender` (predecir salida,
   explicar qué hace) o `aplicar` (elegir el código que resuelve algo,
   encontrar y corregir el bug). El prompt EXIGE: máximo 1 de `recordar`,
   ≥50 % entre `comprender` y `aplicar`, y al menos 2 de `aplicar`.
   El front muestra un badge del nivel en cada pregunta.

3. **Nota ponderada, siempre local**:
   `nota = 100 × Σ(peso_i × acierto_i) / Σ(peso_i)` con pesos
   recordar=0.5, comprender=1.0, aplicar=1.5, redondeada al entero.
   El umbral de aprobación sigue siendo `NOTA_APROBATORIA` (70).
   *Ejemplo*: 6 preguntas (1R+3C+2A). Aciertas 1R+3C, fallas las 2A →
   nota = 100×(0.5+3.0)/(0.5+3.0+3.0) = **54** → no apruebas: saber
   definiciones no basta si no aplicas.

4. **Banco de preguntas por clase, sin repetición.** Toda pregunta generada
   se guarda en `clases.banco_preguntas` con metadata
   (`nivel`, `concepto`, `intentos_en_que_salio: [1,3]`). Al armar un
   intento: (a) se EXCLUYE todo enunciado usado en los últimos 2 intentos;
   (b) se completa el cupo generando variantes nuevas (el prompt recibe la
   lista de enunciados vetados); (c) las nuevas se suman al banco.
   Resultado: dos intentos consecutivos jamás comparten una pregunta.

5. **Preguntas dirigidas**: los conceptos anotados como fallados en los
   quices intermedios (HU-24) reciben al menos una pregunta específica.

6. **Resultado más útil**: además del desglose actual, un
   **resumen por concepto** ("variables 2/2 · bucles 1/3 · CSV 2/2") y por
   nivel ("aplicar 1/2"), para que el conversatorio ataque lo correcto.

## 2. Esquema y API

Pregunta (modelo y JSON del LLM) — campo nuevo:

```json
{"enunciado": "...", "opciones": ["a","b","c","d"], "correcta": 2,
 "explicacion": "...", "concepto": "bucles", "nivel": "aplicar"}
```

Banco (columna `clases.banco_preguntas`, JSON):

```json
[{"pregunta": { ...como arriba... }, "intentos": [1, 3]}]
```

API (misma forma, campos nuevos):

```
POST /api/quiz/{i}           → {preguntas: [{enunciado, opciones, nivel}]}
POST /api/quiz/{i}/calificar → { nota, aprobado, ...,
    resumen_conceptos: {"bucles": [1, 3], "variables": [2, 2]},
    resumen_niveles:   {"aplicar": [1, 2], "comprender": [3, 3]} }
```

`calificar()` en `evaluacion.py` implementa la ponderación (función pura,
fácil de probar). `Resultado` conserva `nota` 0-100 (nada cambia aguas
abajo: candados, puntos y estados usan la nota ponderada).

## 3. Cambios por archivo

| Archivo | Cambio |
|---|---|
| `evaluacion.py` | `nivel` en `Pregunta` (+validación de valores), pesos y nota ponderada, resúmenes por concepto/nivel |
| `prompts.py` | Cuotas de Bloom con definiciones de cada nivel y ejemplos; lista de enunciados vetados; refuerzo de `priorizar` |
| `curso.py`/`db.py` | Columna `banco_preguntas` (migración: `ALTER TABLE` tolerante) + guardar/leer banco |
| `agente.py` | Armado del intento: banco filtrado + generación del faltante + dirigidas; registro de uso por intento |
| `config.py` | `PESOS_NIVEL`, `MIN_PREGUNTAS_EVALUACION = 6`, `INTENTOS_SIN_REPETIR = 2` |
| `frontend/Clase.jsx` | Badge de nivel por pregunta; resúmenes en la tarjeta de resultado |

## 4. Casos borde

- El LLM devuelve un `nivel` fuera del catálogo → la validación lo rechaza
  y `pedir_json` reintenta con el error (mecanismo existente).
- Banco pequeño y todo vetado → se genera un set completo nuevo (y el
  banco crece); jamás se bloquea el reintento.
- Clases v1 (sin objetivos): evaluación de 6 preguntas con las mismas
  cuotas (el tamaño no depende del guion).
- Preguntas del banco cuyo concepto ya no existe tras editar el diseño
  (HU-20) → se descartan del armado (filtro por conceptos vigentes).
- Empate exacto en 70 tras ponderar → aprueba (≥, no >).

## 5. Fuera de alcance

- Preguntas de respuesta abierta calificadas por LLM (la calificación se
  mantiene 100 % local). — Retos de código (HU-28). — Ajuste dinámico de
  dificultad entre intentos (posible v3 con BKT).

## 6. Definición de Hecho

- [ ] Humo real: dos intentos seguidos de la misma clase sin ningún
      enunciado repetido y con cuotas de nivel cumplidas.
- [ ] La nota ponderada aparece igual en tarjeta, panel, barra lateral y BD.
- [ ] Pruebas de abajo + suite + ruff/mypy en verde; HALLAZGOS actualizado.

## 7. Pruebas

- `test_nota_ponderada_ejemplos_tabla` (incluye el ejemplo del §1.3)
- `test_validacion_rechaza_nivel_desconocido`
- `test_cuotas_de_bloom_en_prompt_y_validacion`
- `test_reintento_no_repite_enunciados_de_ultimos_2_intentos`
- `test_banco_crece_y_registra_intentos`
- `test_fallados_intermedios_reciben_pregunta_dirigida`
- `test_resumen_por_concepto_y_nivel`
- `test_migracion_alter_table_banco`
