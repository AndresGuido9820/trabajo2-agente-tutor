# HU-10 — Lección conversacional guiada por pasos

**Como** estudiante **quiero** que la lección sea una conversación con el
tutor que sigue un plan de pasos **para** aprender haciendo (respondo
predicciones y ejercicios) en vez de leer un bloque de texto.

Origen: retroalimentación de revisión — las lecciones deben ser "habladitas"
con el chat, generando ANTES los objetivos y el paso a paso para que la
charla vaya en pro de seguir la lección.

## Criterios de aceptación

- Al entrar a una unidad se genera (una vez, con cache en `curso.json`) el
  **guion de la lección**: objetivos de aprendizaje + 5-8 pasos ordenados
  siguiendo PRIMM (gancho → predicción → explicación → error típico →
  modificación → reto → recap), cada paso con tipo e instrucción.
- La lección transcurre como chat: el tutor desarrolla UN paso por turno,
  reacciona a la respuesta del estudiante (corrige con amabilidad si erró la
  predicción) y cierra cada turno con una pregunta o instrucción.
- El estudiante puede preguntar lo que sea a mitad de lección: el tutor
  responde (reglas socráticas de HU-09) y retoma el paso donde iba.
- Los objetivos y el mapa de pasos se muestran al inicio (el estudiante sabe
  a dónde va); se indica el avance (paso i de N).
- `salir` abandona la lección sin perder el guion (cacheado); reentrar
  reinicia la conversación desde el paso 1 (decisión: charla efímera).
- Al terminar el último paso, el tutor cierra y la CLI sugiere `e <n>`.
- Errores de API en un turno no tumban la sesión.
- Las lecciones Markdown (HU-03) se conservan para exportar cursos de
  muestra (E4); la experiencia en la app es la conversacional.

## Interfaz

```python
# curso.py
@dataclass(frozen=True) class PasoLeccion:   # tipo, instruccion
@dataclass(frozen=True) class GuionLeccion:  # objetivos: list[str], pasos: list[PasoLeccion]
def generar_guion(cliente, perfil, curso, indice, progreso) -> GuionLeccion  # con cache

# agente.py
def iniciar_leccion(self, indice) -> GuionLeccion      # guion + resetea sesión
def turno_leccion(self, indice, mensaje: str | None) -> tuple[str, bool]  # (texto, terminada)

# ui.py
def bucle_leccion(agente, indice, entrada=input) -> bool  # True si se completó
```

Esquema JSON del guion: `{"objetivos": ["..."], "pasos": [{"tipo":
"gancho|prediccion|explicacion|error_tipico|modificacion|reto|recap",
"instruccion": "..."}]}`.

## Tareas

- [x] `prompts.py`: `prompt_guion` (JSON validado), `system_leccion`
      (reglas de tutor conversacional paso a paso) y `prompt_turno_leccion`
      (guion + paso actual + historial + mensaje del estudiante).
- [x] `curso.py`: modelos `PasoLeccion`/`GuionLeccion`, validador,
      `generar_guion` con cache, persistencia en `curso.json`
      (retro-compatible con archivos sin `guiones`).
- [x] `agente.py`: sesión de lección (guion, paso actual, historial acotado),
      `iniciar_leccion` y `turno_leccion` (avanza un paso por respuesta).
- [x] `ui.py` + `__main__.py`: mostrar objetivos y mapa de pasos, bucle de
      turnos con indicador de avance, salida con `salir`, sugerir quiz al
      terminar.
- [x] Pruebas (abajo) + humo real de una lección conversada completa.
- [x] Actualizar SPEC (RF-3.3b, PA) y GUION-VIDEO.

## Pruebas

- `test_validar_guion_acepta_y_rechaza` (tipos inválidos, pasos vacíos)
- `test_generar_guion_usa_cache`
- `test_turno_leccion_avanza_un_paso_por_respuesta_y_termina`
- `test_turno_leccion_incluye_paso_y_respuesta_en_prompt`
- `test_guion_persiste_en_curso_json` (roundtrip)
- `test_bucle_leccion_sale_con_salir`
