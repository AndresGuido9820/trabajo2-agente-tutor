# HU-25 — Panel de la clase: objetivos y progreso al lado del chat

**Como** estudiante **quiero** ver junto al chat de cada clase sus
objetivos (marcándose a medida que los cumplo), mi avance y mis quices
**para** saber siempre dónde voy y qué falta, sin interrumpir la
conversación.

## 1. Qué hace esta HU, explícito

Hoy, dentro de una clase, la única señal de avance es el badge "paso 3/8"
de la cabecera. Esta HU añade un **panel derecho fijo** (330 px, colapsable
con un botón `≡`; en pantallas <900 px arranca colapsado) que muestra en
todo momento el estado de ESTA clase:

```
┌───────────────────────────────┐
│ OBJETIVOS DE LA CLASE         │
│ ● R̶e̶p̶r̶e̶s̶e̶n̶t̶a̶r̶ ̶v̶a̶r̶i̶a̶b̶l̶e̶s̶   ✓ 2/2 │   ← cumplido: tachado + su quiz
│ ◐ Asignación y tipos          │   ← en curso (donde va el chat)
│ ○ Calcular el ingreso         │   ← pendiente
│                               │
│ PROGRESO                      │
│ objetivo 2 de 3 · paso 3/6    │
│ ▓▓▓▓▓▓░░░░  55 %              │
│ ⭐ 15 puntos en esta clase     │
│                               │
│ [🎯 Evaluación final]  (gris  │   ← se habilita al cumplir todo
│ [✨ Demo del objetivo]        │
└───────────────────────────────┘
```

Comportamiento explícito:

1. **Los objetivos se marcan EN VIVO**: cuando el quiz intermedio (HU-24)
   cumple un objetivo, la fila pasa de ◐ a ● tachada con su resultado
   ("✓ 2/2" o "✓ 1/2"; si hubo repaso, "↻ 1/2") — sin recargar la página
   (el turno de estudio devuelve el delta y el front actualiza).
2. **Clic en un objetivo cumplido** → confirmación ligera y el chat lo
   REPASA: la conversación reinicia en ese objetivo ("Quiero repasar:
   {objetivo}"), sin tocar los demás.
3. **El botón "🎯 Evaluación final" vive en el panel**, deshabilitado con
   tooltip "Cumple los 3 objetivos para presentar" hasta que todos estén
   cumplidos; entonces se vuelve primario.
4. **La barra de progreso** combina objetivos y pasos:
   `pct = (objetivos_cumplidos + paso/pasos_del_objetivo) / objetivos_total`.
5. **Fuente de verdad = backend**: el panel se hidrata con un GET al entrar
   a la clase y sobrevive recargas y reinicios del servidor (estado en
   `progreso`, no en contadores del front).

## 2. API

```
GET /api/clase/{indice}/panel →
{
  "objetivos": [
    {"texto": "Representar variables", "estado": "cumplido", "quiz": "2/2",
     "repaso": false},
    {"texto": "Asignación y tipos",   "estado": "en_curso", "quiz": null,
     "repaso": false},
    {"texto": "Calcular el ingreso",  "estado": "pendiente", "quiz": null,
     "repaso": false}
  ],
  "objetivo_actual": 1, "paso": 3, "pasos_total": 6,
  "puntos_clase": 15,
  "evaluacion_disponible": false
}

POST /api/estudio {unidad, objetivo}   # repasar: reinicia EN ese objetivo
```

Además, la respuesta de `POST /api/estudio` y de
`POST /api/estudio/quiz-intermedio` incluye `panel` (el mismo objeto) para
actualizar sin refetch.

Persistencia: `progreso.objetivos_cumplidos: {"<clase>": [{"i": 0,
"quiz": "2/2", "repaso": false}]}`; `puntos_clase` se deriva de los
resultados/checkpoints de esa clase (consulta, no contador duplicado).

## 3. Cambios por archivo

| Archivo | Cambio |
|---|---|
| `progreso.py` | `objetivos_cumplidos` enriquecido (quiz, repaso) |
| `agente.py` | `panel_de_clase(indice)`; `turno_estudio(..., objetivo=)` para repaso puntual; adjuntar `panel` a las respuestas |
| `web.py` | `GET /api/clase/{i}/panel`; `objetivo` en `CuerpoEstudio` |
| `frontend/Clase.jsx` | Componente `PanelClase` (Mantine `Timeline`/lista con `ThemeIcon`), colapsable, actualización por delta; mover el CTA de evaluación al panel |

## 4. Casos borde

- Clase con guion v1 (sin objetivos): el panel muestra solo "paso X/Y" +
  puntos + CTA (sin lista de objetivos) — degradación explícita.
- Repasar un objetivo NO des-cumple lo ya cumplido ni resta puntos.
- Dos pestañas abiertas: la segunda se hidrata al entrar; los deltas de una
  no empujan a la otra (sin websockets; documentado como limitación).
- Clase aprobada: todos ● + botón "Evaluación" pasa a "Reintentar".

## 5. Fuera de alcance

- Websockets/tiempo real multi-pestaña. — Panel a nivel de curso (ya existe
  en la barra izquierda). — Edición de objetivos (eso es el diseño, HU-20).

## 6. Definición de Hecho

- [ ] Recorrido manual: entrar, cumplir un objetivo, ver el tachado en
      vivo, recargar la página y verificar que persiste, repasar desde el
      panel, terminar y presentar la evaluación desde el panel.
- [ ] Pruebas de abajo + suite + ruff/mypy en verde.
- [ ] Captura nueva del panel para el reporte (bot Playwright).

## 7. Pruebas

- `test_panel_estado_inicial_pendientes`
- `test_cumplir_objetivo_actualiza_panel_y_persiste` (nueva sesión)
- `test_panel_incluido_en_respuesta_de_estudio`
- `test_repasar_objetivo_reinicia_solo_ese_objetivo`
- `test_evaluacion_disponible_solo_con_todo_cumplido`
- `test_guion_v1_panel_degradado_sin_objetivos`
