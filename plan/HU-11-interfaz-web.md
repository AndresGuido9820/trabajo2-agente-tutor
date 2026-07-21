# HU-11 — Interfaz web simple

**Como** estudiante **quiero** usar el tutor desde el navegador **para**
probarlo sin instalar nada más que el servidor local. *(RF-3.1: el enunciado
permite CLI o interfaz web simple; ofrecemos ambas.)*

## Criterios de aceptación

- `uv run tutor-web` levanta un servidor local (FastAPI + uvicorn) y la app
  se usa en `http://127.0.0.1:8017`.
- Misma lógica que la CLI: el back reusa `Agente` (cero duplicación de
  lógica de negocio); la web es otra "UI" más.
- Flujo completo en el navegador: formulario de perfil (si no existe) →
  temario con estados → lección conversacional por pasos (chat) → quiz →
  resultado con retroalimentación → progreso.
- El API nunca envía al navegador la respuesta correcta del quiz antes de
  calificar (se guarda en el servidor).
- Errores del LLM → HTTP 502 con mensaje claro; entradas inválidas → 400.
  El front los muestra sin romper la página.
- Front autocontenido: un `index.html` con JS vanilla (sin build ni CDN).
- Single-user local (igual que la CLI): sin auth ni sesiones múltiples;
  documentado como limitación.

## Interfaz (API REST)

| Método y ruta | Body | Respuesta |
|---|---|---|
| `GET /api/estado` | — | `{perfil: bool, lenguaje?, unidades?: [{indice,titulo,estado,mejor_nota}]}` (genera el temario si falta) |
| `POST /api/perfil` | `{nivel, experiencia, objetivo, objetivo_detalle, lenguaje}` | `{ok: true}` |
| `POST /api/leccion/{i}/iniciar` | — | `{objetivos, ruta, texto, paso, total, terminada}` |
| `POST /api/leccion/{i}/turno` | `{mensaje}` | `{texto, paso, total, terminada}` |
| `POST /api/quiz/{i}` | — | `{preguntas: [{enunciado, opciones}]}` (sin `correcta`) |
| `POST /api/quiz/{i}/calificar` | `{respuestas: [int]}` | `{nota, conceptos_fallados, detalle: [...]}` |
| `GET /api/progreso` | — | `{filas: [{indice,titulo,vista,intentos,mejor_nota}]}` |

## Tareas

- [x] Dependencias `fastapi` + `uvicorn`; script `tutor-web`.
- [x] `web.py`: app factory `crear_app` (cliente LLM inyectable para tests),
      endpoints de la tabla, manejo de errores 400/404/409/502.
- [x] `static/index.html`: perfil, temario, chat de lección, quiz, progreso.
- [x] Pruebas con `TestClient` y `ClienteLLMFalso`: flujo completo, quiz sin
      fuga de respuestas, errores mapeados.
- [x] Humo real en el navegador (bots Playwright: capturas, E2E de
      reintento y auditoría axe recorren la app real).
- [x] Actualizar README (cómo correr la web) y SPEC.

## Pruebas

- `test_estado_sin_perfil_y_alta_de_perfil`
- `test_flujo_leccion_conversacional_por_api`
- `test_quiz_no_expone_respuesta_correcta`
- `test_calificar_registra_progreso`
- `test_error_llm_devuelve_502`
