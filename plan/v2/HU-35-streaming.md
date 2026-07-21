# HU-35 — Streaming de respuestas (SSE): el tutor escribe en vivo

**Como** estudiante **quiero** ver la respuesta del tutor aparecer palabra
a palabra **para** que la espera de 20-60 s se sienta como conversación y
no como pantalla congelada. (El mayor salto de percepción en apps LLM.)

## Qué hace, explícito

1. Los turnos CONVERSACIONALES (estudio, conversatorio, creación,
   reencuentro) se transmiten por **SSE**: el texto llega en fragmentos y
   la burbuja del tutor crece en vivo, con auto-scroll.
2. Las generaciones ESTRUCTURADAS (guion, quiz, artefacto, extracción de
   perfil) NO se streamean (necesitan el JSON completo para validarse):
   conservan el indicador por fases actual.
3. Protocolo: `POST /api/estudio/stream` (y análogos) responde
   `text/event-stream` con eventos:
   ```
   event: delta      data: {"texto": "así la asignación "}
   event: fin        data: {"unidad":0, "paso":4, "total":7, "terminada":false}
   event: error      data: {"detail": "..."}
   ```
   El evento `fin` trae el MISMO payload que hoy devuelve el endpoint no-
   stream (el front actualiza avance/panel con él). El turno decidido con
   JSON (`{avanza, mensaje}`) se streamea recortando el campo `mensaje` del
   stream crudo: se bufferiza hasta detectar `"mensaje":"` y desde ahí se
   emiten deltas hasta la comilla de cierre (parser incremental probado).
4. **Persistencia idéntica**: el mensaje completo se anota en el historial
   al terminar (si el cliente se desconecta a mitad, el turno IGUAL se
   completa y persiste server-side; al recargar aparece entero).
5. Fallback automático: si el navegador/entorno no soporta SSE o el stream
   falla al abrir, el front usa el endpoint clásico (que se conserva).

## Cambios técnicos

- `llm.py`: `ClienteLLM.generar_stream(system, prompt) -> Iterator[str]`
  (OpenAI `stream=True`); el fake de tests emite en trozos configurables.
- `agente.py`: variantes `*_stream` que producen (deltas, resultado_final)
  reutilizando la MISMA lógica de estado (un solo lugar decide avance).
- `web.py`: `StreamingResponse` con media_type `text/event-stream`.
- Front: `fetch` + `ReadableStream` (no EventSource: se necesita POST);
  render incremental en la burbuja; botón de detener opcional NO (fuera de
  alcance).

## Casos borde

- Desconexión a mitad del stream → server termina y persiste; front marca
  "conexión perdida — recarga para ver la respuesta completa".
- El modelo emite JSON malformado → el parser incremental aborta el stream
  con `event: error` y el fallback clásico rehace el turno (una vez).
- Timeout de 180 s aplica igual (el stream que no emite en 180 s se corta).

## Pruebas

`test_generar_stream_fake_emite_trozos` · `test_parser_incremental_extrae_mensaje`
· `test_turno_stream_misma_decision_que_no_stream` · `test_persistencia_si_cliente_se_va`
· `test_endpoint_sse_eventos_delta_fin` (TestClient soporta streams)


## Nota de alcance (ejecución 2026-07-21)

Se streamea el turno de **estudio** (`POST /api/estudio/stream`), que es
donde vive casi toda la conversación. Conversatorio, creación y
reencuentro conservan el endpoint clásico (respuestas cortas; el costo de
percepción es menor) y el front tiene fallback automático al clásico si
el stream falla al abrir o emite `event: error`.
