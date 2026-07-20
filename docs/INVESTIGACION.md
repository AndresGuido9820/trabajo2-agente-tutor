# Investigación previa (antes de la primera línea de código)

Fecha: 2026-07-20. Objetivo: decidir stack, arquitectura y técnicas de
prompting ANTES de implementar, para no improvisar sobre la marcha.

## 1. ¿Qué es un "agente" aquí?

Un agente basado en LLM = bucle de interacción donde el programa decide qué
pedirle al modelo según el **estado** (perfil del estudiante, progreso) y
**valida** lo que el modelo devuelve antes de actuar. No necesitamos
tool-calling complejo ni frameworks de agentes: el flujo es determinista
(perfil → temario → lección → quiz → calificación) y el LLM es el motor de
contenido. Conclusión: **orquestación propia y simple**, sin LangChain — menos
dependencias, más control y más claro para explicar en el reporte.

## 2. Elección de API y SDK

Opciones evaluadas:

| Opción | Pros | Contras |
|---|---|---|
| **Anthropic Claude (elegida)** | SDK Python simple, buen seguimiento de instrucciones de formato JSON, system prompts potentes | requiere API key de pago |
| OpenAI GPT | muy documentado | mismo costo; el equipo ya tiene crédito Anthropic |
| Modelos locales (Ollama) | gratis | calidad/latencia insuficiente para contenido educativo largo |

Modelo por defecto: `claude-sonnet-5` (balance costo/calidad); configurable
por env var para poder bajar a Haiku en pruebas manuales.

## 3. Salida estructurada del LLM

El riesgo #1 del proyecto: el LLM devuelve texto libre y el programa necesita
estructura (temario, quiz con respuestas correctas). Técnicas investigadas:

1. **Pedir JSON con esquema en el prompt + validar al recibir** (elegida):
   simple, portable entre proveedores, y el manejo del error de parseo es
   explícito (reintento con el error incluido en el prompt).
2. Tool-use/function-calling forzado: más robusto pero acopla al proveedor.
3. Regex sobre texto libre: frágil, descartada.

Decisión: respuestas JSON validadas con funciones de parseo defensivo propias
(dataclasses + validación manual) para mantener dependencias mínimas.

## 4. Técnicas de prompting a usar (rúbrica: 30 %)

- **Persona/rol**: el system prompt define un tutor motivador, paciente, con
  humor ligero, que adapta ejemplos al interés del estudiante.
- **Contexto de personalización**: cada prompt incluye el perfil (nivel,
  objetivo, lenguaje) y el historial de progreso (qué ya vio, en qué falló).
- **Encadenamiento**: perfil → temario (una llamada) → lección por unidad
  (bajo demanda) → quiz → calificación con retroalimentación. Cada eslabón
  recibe la salida validada del anterior.
- **Few-shot** en el quiz: un ejemplo del formato de pregunta esperado.
- **Salida estructurada**: esquema JSON explícito + instrucción "responde solo
  JSON".
- **Adaptación por desempeño**: si el estudiante falla el quiz, la siguiente
  lección refuerza esos conceptos (el resultado del quiz entra al prompt).

## 5. Persistencia y navegación

Requisito clave del enunciado: navegar unidades **sin contenido generado**.
Diseño: el temario (títulos + objetivos por unidad) se genera una sola vez y
se guarda; las lecciones se generan bajo demanda al entrar a la unidad y se
cachean en `curso.json`. Progreso separado en `progreso.json` para que borrar
el cache de contenido no borre el avance.

JSON plano en disco (no SQLite): un solo usuario por instalación, estructuras
pequeñas, legible para depurar y para mostrar en el video.

## 6. Manejo de errores de API (investigado en docs del SDK)

- Errores tipados del SDK: `APIConnectionError`, `RateLimitError`,
  `APIStatusError`. Estrategia: reintentos con backoff exponencial
  (máx. 3) para conexión/429/5xx; sin reintento para 401 (key mala → mensaje
  de configuración).
- Timeout explícito por request (60 s) para que la CLI nunca quede colgada.

## 7. CLI

Opciones: `input()` puro, `rich`, `textual`. Elegida: **`rich`** para paneles,
markdown y colores (las lecciones vienen en Markdown y `rich` las renderiza
nativo) + `input()` para lectura. `textual` (TUI completa) es
sobre-ingeniería para el alcance.

## 8. Riesgos identificados

| Riesgo | Mitigación |
|---|---|
| JSON inválido del LLM | validación + reintento con el error en el prompt (máx. 2) |
| Costo de tokens en demos | cache de lecciones; modelo configurable |
| Alucinación de contenido técnico | temperatura baja para contenido; revisión humana de cursos de muestra |
| Quiz con respuesta correcta errónea | el prompt exige explicación de la respuesta; revisión en cursos de muestra |
| Key en el repo | `.env` + gitignore + revisión pre-commit (PA-13) |

## 9. Conclusión

Stack final: **Python 3.12+, uv, SDK `anthropic`, `rich`, `python-dotenv`;
pytest + ruff + mypy**. Arquitectura en capas: `ui` (CLI) → `agente`
(orquestación/estado) → `llm` (cliente API) + `almacen` (persistencia), con
`prompts.py` centralizando todos los prompts versionados.
