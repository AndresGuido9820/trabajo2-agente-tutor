# HU-41 — Examen diagnóstico inicial

**Como** estudiante **quiero** que el tutor mida mi conocimiento REAL con
un examen corto antes de diseñar mi curso **para** que el temario arranque
exactamente desde donde estoy (requisito del enunciado: "Evaluar las
capacidades y conocimientos actuales del estudiante" como examen).

## Qué hace

1. Al confirmar el diseño conversacional ("ya, dale"), el asesor NO crea
   el temario todavía: genera un **examen diagnóstico de 4 preguntas** de
   opción múltiple calibrado al nivel declarado (nivel "nunca" →
   razonamiento computacional sin sintaxis; "basico"/"scripts" → código
   corto sobre fundamentos), con dificultad ascendente y distractores del
   banco de misconceptions.
2. El estudiante lo responde dentro del mismo chat (tarjeta de quiz;
   calificación local en el servidor, las correctas nunca viajan).
3. El resultado ("Diagnóstico inicial 2/4: domina X; brechas en Y") se
   incorpora al `perfil.experiencia` y RECIÉN entonces se genera el
   temario: todo el curso queda calibrado al conocimiento real.
4. Degradación: si la generación del examen falla, el curso se crea igual
   sin examen (el diagnóstico es un plus, jamás un bloqueo).

## API

```
POST /api/creacion (listo=true) → {mensaje, listo: true,
    diagnostico: [{enunciado, opciones}] | null}
POST /api/diagnostico/calificar {respuestas} →
    {aciertos, total, resumen, detalle}   (409 sin pendiente; 400 inválidas)
```

## Tareas

- [x] `prompt_diagnostico` calibrado por nivel (prompts.py).
- [x] Flujo en dos pasos en `web.py` (+ `_disenar_curso` compartido).
- [x] Front: tarjeta "EXAMEN DIAGNÓSTICO" en el chat de creación.
- [x] Pruebas: resultado entra al perfil y al prompt del temario; 409/400;
      degradación ante ErrorLLM; flujo completo actualizado.
