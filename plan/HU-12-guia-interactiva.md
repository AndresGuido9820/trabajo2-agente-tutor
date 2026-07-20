# HU-12 — Guía interactiva por objetivos, puntos y progresión con candado

**Como** estudiante **quiero** estudiar cada unidad con una guía específica
organizada por objetivos, respondiendo checkpoints que dan puntos, y
presentar al final una evaluación que decide si paso a la siguiente unidad
(y si no paso, un conversatorio socrático de dudas) **para** aprender
haciendo con metas claras y motivación de juego.

Origen: retroalimentación de revisión (visión del producto 1.0).

## Criterios de aceptación

- **Guía por unidad** (generada una vez, cache en `curso.json`): 3-5
  secciones, UNA por objetivo de aprendizaje; cada sección = contenido
  específico (worked example con estado línea a línea, analogía del perfil)
  + un **checkpoint** de opción múltiple que evalúa ESE objetivo.
- **Checkpoints con puntos y método socrático**: acierto al 1er intento
  +10 pts; si falla recibe una **pista socrática** (no la respuesta) y
  reintenta: acierto al 2º intento +5 pts; si falla de nuevo se muestra la
  explicación completa (+0) y se avanza. Los puntos se acumulan y persisten.
- **Evaluación final por unidad** (quiz existente): nota ≥ 70 **aprueba** y
  desbloquea la siguiente unidad (+30 pts). La calificación es local.
- **Candado de progresión**: la unidad N solo se puede estudiar/evaluar si
  la N-1 está aprobada (la 1 siempre abierta). Intentarlo da error claro.
- **Conversatorio socrático**: si no aprueba, se abre un chat sobre las
  dudas de la guía (contexto: la guía + conceptos fallados del quiz), con
  guardrails socráticos (pistas, escape del "no sé"); al terminar puede
  reintentar la evaluación.
- El front web implementa toda la experiencia (guía progresiva, contador de
  puntos, candados, conversatorio). El servidor califica los checkpoints:
  las respuestas correctas NUNCA viajan al navegador.
- La CLI conserva la lección conversacional pero respeta los candados.

## Interfaz

```python
# curso.py
@dataclass Checkpoint    # pregunta, opciones[4], correcta, pista, explicacion, concepto
@dataclass SeccionGuia   # objetivo, contenido (md), checkpoint
@dataclass Guia          # secciones: list[SeccionGuia]
def generar_guia(cliente, perfil, curso, indice, progreso) -> Guia

# progreso.py
Progreso.puntos: int / sumar_puntos(n)

# agente.py
def desbloqueada(self, indice) -> bool
def guia_de_unidad(self, indice) -> Guia            # candado + cache
def responder_checkpoint(self, indice, seccion, opcion, intento) -> RespuestaCheckpoint
def conversatorio(self, indice, mensaje) -> str

# API web
POST /api/guia/{i}                     -> secciones sin correcta/explicacion
POST /api/guia/{i}/checkpoint          -> {correcto, texto, puntos, puntos_totales}
POST /api/conversatorio/{i}            -> {texto}
GET  /api/estado                       -> + puntos, estado "bloqueada"
POST /api/quiz/{i}/calificar           -> + {aprobado, puntos_totales}
```

## Tareas

- [x] `config.py`: `NOTA_APROBATORIA`, puntos por intento y por aprobar.
- [x] `progreso.py`: campo `puntos` persistente (retro-compatible).
- [x] `prompts.py`: `prompt_guia` (secciones por objetivo, checkpoints con
      distractores de misconceptions, pista socrática que NO revela,
      verificación independiente) y `system_conversatorio`.
- [x] `curso.py`: modelos + `validar_guia` + `generar_guia` con cache.
- [x] `errores.py`: `ErrorBloqueada`.
- [x] `agente.py`: candados, checkpoints con puntos, conversatorio.
- [x] `web.py`: endpoints nuevos; checkpoint calificado en servidor.
- [x] `static/index.html`: vista de guía progresiva con puntos, candados en
      el sidebar, flujo aprobado/conversatorio tras el quiz.
- [x] CLI: estado "bloqueada" visible y acciones bloqueadas con mensaje.
- [x] Pruebas + E2E real como estudiante (aprobar y reprobar).

## Pruebas

- `test_validar_guia_acepta_y_rechaza`
- `test_checkpoint_puntos_10_5_0_y_pista_luego_explicacion`
- `test_unidad_bloqueada_hasta_aprobar_anterior`
- `test_quiz_aprobado_desbloquea_y_suma_puntos`
- `test_conversatorio_incluye_guia_y_conceptos_fallados`
- `test_web_guia_no_expone_correctas`
- `test_web_flujo_reprobar_conversatorio_reintentar`
