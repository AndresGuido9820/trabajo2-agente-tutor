# HU-24 — Clases más extensas: guion por objetivos con quices intermedios

**Como** estudiante **quiero** clases con más hilo y profundidad —
organizadas por objetivos, con un mini-quiz al cerrar cada objetivo y la
evaluación grande al final — **para** consolidar cada idea antes de pasar a
la siguiente en vez de correr por la lección.

## 1. Qué hace esta HU, explícito

Hoy una clase es un guion plano de 5-8 pasos PRIMM y un único quiz al
final: se siente corta y el estudiante llega a la evaluación sin haber
verificado nada por el camino. Esta HU cambia la ESTRUCTURA de la clase:

1. **El guion se genera agrupado por objetivos.** Una clase tiene 3-4
   objetivos de aprendizaje concretos (p. ej. para "Variables con tus datos
   de venta": ① representar precios/cantidades como variables, ② entender
   la asignación y los tipos, ③ calcular el ingreso con expresiones).
   Cada objetivo trae SU PROPIA secuencia PRIMM de 4-7 pasos: gancho →
   predicción → explicación → error típico → modificación/práctica.
   Resultado: la clase completa dura 15-25 turnos de conversación (hoy ~8).

2. **Al cerrar cada objetivo, el tutor lanza un quiz intermedio de 2
   preguntas** dentro del chat (misma tarjeta de quiz de hoy, pero corta).
   Las preguntas vienen PRE-GENERADAS en el guion (cero espera al llegar).
   La calificación es local:
   - **2/2 o 1/2 aciertos** → el objetivo queda CUMPLIDO. El tutor celebra
     en una línea y arranca el siguiente objetivo. (+5 ⭐ por acierto.)
   - **0/2 aciertos** → el tutor hace UN repaso del objetivo (explicación
     nueva con un ejemplo distinto, 1-2 turnos) y repite el quiz UNA vez
     con las mismas 2 preguntas. Pase lo que pase en el segundo intento,
     el flujo avanza (no hay bloqueo), pero los conceptos fallados quedan
     ANOTADOS para la evaluación final.

3. **La evaluación final solo se ofrece al terminar todos los objetivos**
   (el CTA "🎯 Presentar la evaluación" no aparece antes). Sus preguntas
   priorizan los conceptos anotados como fallados en los intermedios.

### Ejemplo de conversación (comportamiento esperado)

> **Tutor:** …y así `total = precio * cantidad` guarda 100. Con esto
> cerramos el objetivo "calcular el ingreso con expresiones". Antes de
> seguir, ¡mini-quiz! *(aparece la tarjeta con 2 preguntas)*
>
> **Estudiante:** *(responde: 1 buena, 1 mala)*
>
> **Tutor:** ✅ Objetivo cumplido (1/2 — la P2 la reforzaremos luego).
> Vamos con el objetivo 3 de 3: leer tu CSV de ventas…

## 2. Esquema del guion v2 (JSON que genera el LLM)

```json
{
  "version": 2,
  "objetivos": [
    {
      "objetivo": "Representar precios y cantidades como variables",
      "pasos": [
        {"tipo": "gancho", "instruccion": "..."},
        {"tipo": "prediccion", "instruccion": "..."},
        {"tipo": "explicacion", "instruccion": "..."},
        {"tipo": "error_tipico", "instruccion": "..."},
        {"tipo": "modificacion", "instruccion": "..."}
      ],
      "quiz": [
        {"enunciado": "...", "opciones": ["a","b","c","d"], "correcta": 1,
         "explicacion": "...", "concepto": "variables"},
        {"enunciado": "...", "opciones": ["a","b","c","d"], "correcta": 0,
         "explicacion": "...", "concepto": "asignación"}
      ]
    }
  ]
}
```

Validación (`validar_guion_v2`): 3-4 objetivos; 4-7 pasos por objetivo con
tipos del catálogo existente; exactamente 2 preguntas por quiz con el mismo
validador de preguntas del quiz actual (4 opciones, correcta en rango,
campos no vacíos). El prompt exige la verificación independiente de cada
pregunta (resolver antes de escribir opciones), igual que hoy.

## 3. API y estado

```
POST /api/estudio            (igual que hoy) → respuesta AMPLIADA:
  { texto, unidad, terminada,
    objetivo: 2, objetivos_total: 3,      # dónde va la conversación
    paso: 3, total: 6,                    # dentro del objetivo actual
    quiz_intermedio: [ {enunciado, opciones}, ... ] | null }
      # quiz_intermedio llega SOLO en el turno que cierra un objetivo
      # (sin 'correcta' ni 'explicacion': se califica en el servidor)

POST /api/estudio/quiz-intermedio
  body:      { unidad: 0, respuestas: [1, 3] }
  respuesta: { aciertos: 1, cumplido: true, puntos_totales: 45,
               detalle: [{acierto, correcta, explicacion}],
               texto: "…celebración o arranque del repaso…" }
```

Estado del agente (`_SesionLeccion` v2): `objetivo_actual`, `paso`,
`quiz_pendiente: bool`, `repaso_usado: bool`, `fallados: list[str]`.
Persistencia: `progreso.objetivos_cumplidos: {"0": [0, 1]}` (por clase,
índices de objetivos cumplidos) y `progreso.fallados_intermedios` — ambos
retro-compatibles (claves nuevas con default).

BD: el guion v2 se guarda en la MISMA columna `clases.guion` (JSON blob con
`"version": 2`). Carga retro-compatible: si no hay `version`, es v1 y la
clase usa el flujo actual sin cambios.

## 4. Cambios por archivo

| Archivo | Cambio |
|---|---|
| `prompts.py` | `prompt_guion_v2` (objetivos+pasos+quiz por objetivo, con banco de misconceptions y verificación); `system_leccion` añade reglas del repaso |
| `curso.py` | Modelos `ObjetivoGuion`/`GuionLeccionV2`, `validar_guion_v2`, generación y persistencia retro-compatible |
| `agente.py` | Sesión (objetivo, paso); disparo del quiz al cerrar objetivo; `responder_quiz_intermedio`; anotación de fallados; candado del CTA final |
| `progreso.py` | `objetivos_cumplidos` y `fallados_intermedios` persistentes |
| `web.py` | Campos nuevos en `/api/estudio` + endpoint `quiz-intermedio` |
| `frontend/Clase.jsx` | Render del quiz intermedio (reutiliza `QuizCard` con 2 preguntas); indicador "objetivo 2/3 · paso 3/6" |
| `evaluacion.py` | `generar_quiz(..., priorizar: list[str])` para los fallados |

## 5. Casos borde

- Guion v1 ya cacheado en una clase → esa clase sigue con el flujo v1;
  "↩ Repasar desde el inicio" regenera en v2 (previa confirmación implícita
  del reinicio).
- El estudiante hace una pregunta libre justo cuando toca el quiz → el
  tutor responde (avanza=false) y el quiz queda pendiente hasta el próximo
  turno que cierre el objetivo.
- Respuestas del quiz fuera de rango o incompletas → 400 con mensaje claro.
- Salir de la clase con quiz pendiente → al volver, el quiz se re-ofrece
  (estado en la sesión del servidor; si el server se reinició, se repite el
  último paso del objetivo: aceptable y documentado).

## 6. Fuera de alcance (van en otras HUs)

- El panel visual de objetivos (HU-25). — Retos de código (HU-28).
- Cambios de tamaño/dificultad de la evaluación final (HU-26), salvo el
  parámetro `priorizar`.

## 7. Definición de Hecho

- [x] Criterios de §1 verificados manualmente con API real (una clase
      completa de ≥15 turnos con 3 quices intermedios).
- [x] Pruebas de abajo en verde + suite completa + ruff/mypy.
- [x] Retro-compatibilidad probada con un guion v1 real.
- [x] Entrada en `docs/HALLAZGOS.md` con lo aprendido.

## 8. Pruebas

- `test_guion_v2_valida_objetivos_pasos_y_quices` (+ casos inválidos)
- `test_cerrar_objetivo_entrega_quiz_intermedio_sin_correctas`
- `test_quiz_intermedio_1_de_2_cumple_y_da_puntos`
- `test_quiz_intermedio_0_de_2_repasa_una_vez_y_anota_fallados`
- `test_cta_evaluacion_solo_al_terminar_todos_los_objetivos`
- `test_evaluacion_final_recibe_priorizar_con_fallados`
- `test_guion_v1_sigue_funcionando_sin_cambios`
