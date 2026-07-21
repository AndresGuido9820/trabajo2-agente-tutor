# HU-32 — Repaso del día (repetición espaciada entre clases)

**Como** estudiante **quiero** un "Repaso del día" que mezcle preguntas de
lo que fallé y de lo que vi hace días **para** no olvidar lo aprendido
mientras avanzo (evidencia: spaced repetition).

## Qué hace, explícito

1. Entrada "🔁 Repaso del día" en la barra lateral. Muestra cuántos ítems
   hay pendientes hoy ("5 para repasar").
2. **Cola de repaso** con intervalos fijos 1-3-7 días (versión simple, no
   FSRS): cada concepto FALLADO (quiz/checkpoint) entra a la cola con
   vencimiento mañana; al repasarlo bien pasa al siguiente intervalo
   (3, luego 7, luego sale); al fallarlo vuelve a 1 día.
3. El repaso es una tarjeta de quiz de hasta 5 preguntas: se toman del
   **banco** (HU-26) de las clases correspondientes, priorizando las que
   evalúan el concepto vencido; si no hay en banco, se generan (y se
   suman al banco). Calificación local; +3 ⭐ por acierto.
4. Al terminar: resumen ("4/5 — 'bucles' vuelve mañana") y la cola se
   reprograma. Sin castigo por fallar.
5. Si no hay nada vencido: mensaje "al día ✅" con la fecha del próximo.

## API

```
GET  /api/repaso           → {pendientes: 5, proximo: "2026-07-22"}
POST /api/repaso/iniciar   → {preguntas: [{enunciado, opciones, clase}]}
POST /api/repaso/calificar → {respuestas} → {aciertos, detalle, cola: [...]}
```

Persistencia: `progreso.cola_repaso: [{concepto, clase, vence: "fecha",
nivel_intervalo: 0|1|2}]`.

## Tareas

- [ ] `progreso.py`: cola con (re)programación 1-3-7.
- [ ] `agente.py`: alimentar la cola desde fallos (quiz/checkpoint/
      intermedios); armar el repaso desde el banco; calificar y reprogramar.
- [ ] `web.py` + front: entrada lateral con contador, vista de repaso
      (reusa QuizCard), resumen final.
- [ ] Pruebas: programación de intervalos, fallo→reinicio a 1 día,
      selección desde banco, sin vencidos.

## Casos borde

- Concepto fallado en dos clases → un ítem por (concepto, clase).
- Cola > 5 vencidos → se toman los 5 más antiguos; el resto sigue vencido.
- Clase borrada (HU-29) → sus ítems se purgan de la cola.

## Pruebas

`test_fallo_entra_a_cola_1_dia` · `test_acierto_avanza_1_3_7_y_sale`
· `test_fallo_en_repaso_reinicia_intervalo` · `test_purga_de_clases_borradas`
