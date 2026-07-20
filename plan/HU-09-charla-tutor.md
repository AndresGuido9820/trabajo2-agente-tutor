# HU-09 — Charla con el tutor (modo socrático)

**Como** estudiante **quiero** hacerle preguntas al tutor sobre la lección
que estoy estudiando **para** resolver mis dudas sin salir del curso, con un
tutor que me guía en vez de darme todo resuelto.

Origen: retroalimentación de revisión — el agente debe ser un asistente
interactivo de aprendizaje, no solo un generador de contenido. Aplica las
reglas socráticas investigadas (Khanmigo, `docs/INVESTIGACION-PEDAGOGIA.md` §3).

## Criterios de aceptación

- Tras leer una lección, el estudiante entra en modo charla: escribe
  preguntas libres y el tutor responde en contexto (la lección + el perfil +
  el historial de la conversación).
- Guardrail socrático: ante ejercicios o el mini-reto, el tutor guía con
  preguntas y pistas graduales, no da la solución completa de entrada.
- Escape del "no sé": si el estudiante expresa que no sabe/no entiende por
  segunda vez, el tutor da un paso resuelto concreto y sigue desde ahí
  (evita el colapso socrático documentado).
- Redirección: preguntas fuera del curso se redirigen amablemente al tema.
- Enter vacío (o `volver`) regresa al menú; `Ctrl+C` no pierde progreso.
- El historial de la charla vive en la sesión (no se persiste) y se acota a
  los últimos `MAX_TURNOS_CHARLA` turnos para controlar tokens.
- Errores de API en la charla no tumban la sesión: mensaje claro y sigue el
  menú.

## Interfaz

```python
# prompts.py
def system_charla(perfil) -> str          # persona + reglas socráticas
def prompt_charla(leccion_md, historial: list[tuple[str, str]], pregunta) -> str

# agente.py
def charlar(self, indice: int, pregunta: str) -> str   # mantiene historial por unidad

# ui.py
def bucle_charla(agente, indice, entrada=input) -> None
```

## Tareas

- [x] `prompts.py`: `system_charla` (socrático + escape "no sé" + redirección
      + economía de lenguaje) y `prompt_charla` con lección e historial.
- [x] `agente.py`: `charlar()` con historial por unidad acotado.
- [x] `ui.py`: bucle de charla tras mostrar la lección, con salida clara.
- [x] `config.py`: `MAX_TURNOS_CHARLA`.
- [x] Pruebas: historial se acumula y acota, la lección y la pregunta van en
      el prompt, salida con vacío/'volver', error de API no rompe el bucle.
- [x] Humo real: 2-3 preguntas de estudiante (una pidiendo la solución del
      mini-reto → debe dar pista, no solución).

## Pruebas

- `test_charlar_incluye_leccion_historial_y_pregunta_en_prompt`
- `test_charlar_acota_historial_a_max_turnos`
- `test_bucle_charla_sale_con_entrada_vacia`
- `test_bucle_charla_error_llm_no_rompe` (fake que lanza ErrorLLM)
