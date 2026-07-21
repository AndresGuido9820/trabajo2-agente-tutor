# HU-25 — Panel de la clase: objetivos y progreso al lado del chat

**Como** estudiante **quiero** ver junto al chat de cada clase sus
objetivos (marcándose a medida que los cumplo), mi avance y mis quices
**para** saber siempre dónde voy y qué falta, sin interrumpir la
conversación.

## Criterios de aceptación

- Dentro de una clase aparece un **panel derecho** (colapsable; en móvil se
  oculta tras un botón) con:
  - **Objetivos de la clase**: lista con estado en vivo — pendiente (○),
    en curso (◐, el que la conversación está trabajando) y cumplido (●
    tachado). Se actualiza al cerrar cada objetivo (quiz intermedio de
    HU-24) sin recargar.
  - **Progreso**: barra "objetivo 2 de 4 · paso 3/6" + puntos ganados en
    esta clase.
  - **Quices intermedios**: resultado por objetivo (✓ 2/2, ✓ 1/2, ✗).
  - **Atajos**: 🎯 evaluación final (habilitado solo al terminar), ✨ demo,
    ↩ repasar objetivo (clic en un objetivo cumplido → lo repasa en el chat).
- El estado del panel viene del backend (fuente de verdad), no de contadores
  del front: sobrevive a recargas.
- La barra lateral izquierda (lista de clases) no cambia.

## Interfaz

```python
# API
GET /api/clase/{indice}/panel -> {
  objetivos: [{texto, estado: "pendiente|en_curso|cumplido", quiz: "2/2"|null}],
  objetivo_actual: int, paso: int, pasos_total: int,
  puntos_clase: int, evaluacion_disponible: bool
}
```

Persistencia: estado de objetivos cumplidos en `progreso` (documento JSON:
`objetivos_cumplidos: {"<clase>": [indices]}`), puntos por clase derivados
del historial de resultados.

## Tareas

- [ ] `progreso.py`: `objetivos_cumplidos` persistente + puntos por clase.
- [ ] `agente.py`: `panel_de_clase(indice)` con el estado agregado.
- [ ] `web.py`: endpoint del panel; el turno de estudio devuelve también el
      delta para actualizar el panel sin refetch completo.
- [ ] Front (`Clase.jsx`): componente `PanelClase` (Mantine: Timeline o
      lista con ThemeIcon), colapsable, actualización tras cada turno/quiz.
- [ ] Repaso por objetivo: `POST /api/estudio {unidad, objetivo}` reinicia
      la conversación en ese objetivo.
- [ ] Pruebas: panel refleja cumplidos/quices/persistencia; repaso por
      objetivo; evaluación deshabilitada hasta terminar.

## Pruebas

- `test_panel_estado_inicial_y_tras_cumplir_objetivo`
- `test_panel_sobrevive_recarga` (nueva sesión del agente)
- `test_repasar_objetivo_reinicia_en_ese_objetivo`
- `test_evaluacion_disponible_solo_al_terminar`
