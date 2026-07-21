# HU-39 — Modelo por tarea: rápido para conversar, potente para diseñar

**Como** operador del producto **quiero** usar un modelo barato/rápido en
los turnos conversacionales y uno potente en las generaciones estructuradas
**para** bajar latencia y costo sin perder calidad donde importa.

## Qué hace, explícito

1. Dos "carriles" de modelo, configurables por env:
   - `TUTOR_MODEL` (potente; default `gpt-5-mini`): guiones, quizzes,
     artefactos, extracción de perfil, temario — todo lo estructurado.
   - `TUTOR_MODEL_CHAT` (rápido; default = `TUTOR_MODEL`, recomendado
     `gpt-5-nano` o similar): turnos de estudio, charla, conversatorio,
     reencuentro — lo conversacional.
2. `ClienteOpenAI` recibe el modelo POR LLAMADA (`generar(...,
   modelo=None)`); `Configuracion` gana `modelo_chat`. Cada sitio de
   llamada declara su carril (tabla en esta HU → revisada en el code
   review de la HU).
3. **Registro de uso local**: cada llamada anota en la BD
   (`tabla llm_uso`: fecha, carril, modelo, tokens_prompt/salida si el SDK
   los da, duración ms). "Mi progreso" (HU-31) muestra el total del día
   ("~$0.12 estimado" con precios en `config.PRECIOS_MODELO`, editables).
4. Logs: cada llamada loggea carril+modelo+duración (nivel INFO) — hoy no
   hay visibilidad ninguna de latencias.

## Carriles (fuente de verdad)

| Operación | Carril |
|---|---|
| temario, guion, guía, quiz, artefacto, extracción perfil, creación (JSON) | potente |
| turno de estudio/avance, charla, conversatorio, pista, reencuentro | chat |

## Tareas

- [x] `config.py`: `modelo_chat`, `PRECIOS_MODELO` (dict editable).
- [x] `llm.py`: parámetro `modelo` por llamada + medición de duración +
      tokens de la respuesta del SDK; hook `registrar_uso`.
- [x] `db.py`: tabla `llm_uso` (en la BD del curso activo o una global
      `data/uso.db` — decisión: GLOBAL, el costo es del operador).
- [x] `agente.py`/`web.py`: pasar el carril en cada sitio (tabla arriba).
- [x] `web.py`: `GET /api/uso` (agregado por día/carril) para HU-31.
- [x] Pruebas: carril correcto por operación (espiando el fake), registro
      de uso, estimación de costo con precios de prueba, default sin
      `TUTOR_MODEL_CHAT` = mismo modelo.

## Casos borde

- `TUTOR_MODEL_CHAT` inválido → el error 400 del SDK se reporta claro y
  se sugiere revisar la env (sin reintentos, como hoy los 400).
- SDK sin usage en la respuesta → se registra con tokens null.
- Cambiar el modelo con el server corriendo → requiere reinicio (env);
  documentado.

## Pruebas

`test_operaciones_usan_su_carril` · `test_registro_de_uso_persiste`
· `test_costo_estimado_con_precios_de_prueba` · `test_default_un_solo_modelo`
