# HU-31 — Mi progreso: estadísticas de aprendizaje

**Como** estudiante **quiero** una vista "Mi progreso" con mis métricas —
puntos por día, conceptos fuertes/débiles, notas y actividad — **para**
ver mi evolución y saber qué repasar.

## Qué hace, explícito

1. Nueva entrada "📈 Mi progreso" en la barra lateral (nivel curso). Abre
   una vista (no chat) con:
   - **Actividad**: barras de mensajes/puntos por día (últimos 14 días),
     racha actual y mejor racha.
   - **Notas**: nota de cada intento de evaluación por clase (línea o
     lista), mejor nota destacada.
   - **Conceptos**: dos columnas "dominados" (acertados ≥2 veces sin
     fallos recientes) y "para repasar" (fallados en quizzes/checkpoints),
     cada uno con el conteo aciertos/fallos.
   - **Totales**: clases aprobadas, puntos ⭐, tiempo estimado (nº de
     mensajes × 40 s, aproximación documentada).
2. Todo se calcula EN el backend a partir de datos que ya existen
   (progreso.resultados, chat con `creado_en`, puntos): esta HU no agrega
   escritura nueva, solo agregación.
3. Los "para repasar" enlazan a su clase ("repasar en el chat").

## API

```
GET /api/estadisticas → {
  actividad: [{fecha: "2026-07-21", mensajes: 34, puntos: 25}, ...],
  notas: {"0": [40, 85], "1": [90]},
  conceptos: {dominados: [{c: "variables", ok: 4, mal: 0}],
              repasar:   [{c: "bucles", ok: 1, mal: 3, clase: 2}]},
  totales: {aprobadas: 2, total: 7, puntos: 145, racha: 3, mejor_racha: 5,
            minutos_estimados: 210}
}
```

`mejor_racha` se persiste en `progreso` (se actualiza en
`registrar_sesion`).

## Tareas

- [ ] `progreso.py`: `mejor_racha` persistente.
- [ ] `agente.py`/`web.py`: `estadisticas()` agregando resultados + chat
      (GROUP BY fecha) + conceptos (conteo por concepto de Resultados).
- [ ] Front: vista `Estadisticas.jsx` (Mantine: Cards, Progress, barras
      simples con divs — sin librería de charts).
- [ ] Pruebas: agregación por día, clasificación dominado/repasar, mejor
      racha persiste, totales coherentes.

## Casos borde

- Sin datos → estados vacíos amigables ("aún no hay actividad").
- Conceptos con nombres casi iguales ("bucles"/"bucle") → se agrupan por
  minúsculas exactas (no se intenta fuzzy; documentado).

## Pruebas

`test_actividad_agrupa_por_dia` · `test_conceptos_dominados_vs_repasar`
· `test_mejor_racha_persiste` · `test_estadisticas_sin_datos`
