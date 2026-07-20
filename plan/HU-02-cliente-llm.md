# HU-02 — Cliente LLM con manejo de errores

**Como** desarrollador del agente **quiero** un cliente de la API de Claude
con reintentos, timeout y errores tipados **para** que ninguna falla de red o
de la API tumbe la sesión del estudiante. *(RF-2.1, RF-2.5; PA-07, PA-08, PA-09)*

## Criterios de aceptación

- Interfaz `ClienteLLM` (protocolo) con `generar(system, prompt) -> str`;
  implementación real `ClienteAnthropic` e implementación falsa para tests.
- Reintentos con backoff exponencial (máx. `MAX_REINTENTOS_API = 3`) ante
  error de conexión, 429 y 5xx; **sin** reintento ante 401/400.
- Timeout por request de 60 s.
- Al agotar reintentos se lanza `ErrorLLM` con mensaje entendible (sin volcar
  el stack del SDK al usuario).
- `pedir_json(...)` envía un esquema, parsea la respuesta y ante JSON inválido
  reintenta incluyendo el error de parseo en el prompt (máx.
  `MAX_REINTENTOS_PARSEO = 2`).
- La API key jamás aparece en logs ni mensajes de error.

## Interfaz

```python
class ClienteLLM(Protocol):
    def generar(self, system: str, prompt: str) -> str: ...

class ClienteAnthropic:  # usa config: modelo, timeout, max_tokens
    def generar(self, system: str, prompt: str) -> str: ...

def pedir_json(cliente: ClienteLLM, system: str, prompt: str,
               validar: Callable[[Any], T]) -> T
```

## Tareas

- [ ] `llm.py`: protocolo, cliente real, mapeo de errores del SDK a `ErrorLLM`.
- [ ] Backoff exponencial con jitter (función pura calculable en tests).
- [ ] `pedir_json` con extracción tolerante (JSON dentro de fences ```...```)
      y bucle de reintento de parseo.
- [ ] `tests/conftest.py`: `ClienteLLMFalso` (respuestas en cola, modo fallar
      N veces, contador de llamadas).
- [ ] `scripts/humo_llm.py`: prueba de humo manual contra la API real.
- [ ] Pruebas unitarias (abajo).

## Pruebas

- `test_generar_reintenta_ante_429_y_luego_funciona`
- `test_generar_no_reintenta_ante_401`
- `test_generar_agota_reintentos_y_lanza_error_llm`
- `test_pedir_json_parsea_respuesta_valida`
- `test_pedir_json_extrae_json_entre_fences`
- `test_pedir_json_reintenta_ante_json_invalido`
- `test_pedir_json_falla_claro_tras_agotar_reintentos`
