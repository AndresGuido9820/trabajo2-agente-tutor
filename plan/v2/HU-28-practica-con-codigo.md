# HU-28 — Práctica con código real: retos verificados con Pyodide

**Como** estudiante **quiero** que el reto de cada objetivo sea escribir
código de verdad, verificado automáticamente en mi navegador, **para**
pasar de elegir opciones a PROGRAMAR (el salto de quiz-driven a
code-driven; patrón freeCodeCamp/futurecoder).

## 1. Qué hace esta HU, explícito

Hoy el paso "reto"/"modificación" es textual: el tutor pide un ejercicio y
confía en que el estudiante diga "ya lo hice". Esta HU lo vuelve real:

1. **El guion v2 genera, para el último paso de cada objetivo, un RETO DE
   CÓDIGO** con tres piezas: enunciado ligado a la meta del estudiante,
   código inicial (`seed`) con huecos por completar, y **2-4 tests**
   ejecutables. El prompt DEBE resolver el reto y comprobar sus propios
   tests antes de emitirlos (verificación independiente, como los quizzes).

2. **En el chat aparece una `RetoCard`**: el editor (el runner Pyodide ya
   existente) precargado con el seed + botón **"✓ Verificar"**. Al pulsar:
   - se ejecuta el código del estudiante en Pyodide (en SU navegador, sin
     backend de ejecución);
   - se corre cada test y se pinta el resultado por test, con mensaje
     pedagógico estilo freeCodeCamp:

     ```
     ✓ ingreso(25, 4) devuelve 100
     ✗ ingreso(10, 3) devuelve 30 — tu código devolvió 13
       (pista: ¿estás sumando en vez de multiplicar?)
     ```

3. **Pasar todos los tests** → el front avisa al backend, que marca el paso
   como superado (+10 ⭐, una sola vez) y el tutor continúa la conversación
   celebrando en concreto ("tu función ya calcula ingresos: eso mismo harás
   con tu CSV").

4. **Fallar** → el estudiante puede reintentar libremente o pedir
   **"💡 Pista"**: el backend llama al tutor con el CÓDIGO del estudiante y
   el test fallado; responde socrático (señala dónde mirar, nunca pega la
   solución). Sin límite de intentos ni castigo.

5. **Cursos no-Python**: el paso reto conserva el comportamiento textual
   actual (el runner solo existe para Python).

### Ejemplo completo de reto (lo que genera el LLM)

```json
{
  "enunciado": "Completa la función para calcular el ingreso de una venta.",
  "seed": "def ingreso(precio, cantidad):\n    # tu código aquí\n    return 0\n",
  "tests": [
    {"llamada": "ingreso(25, 4)",  "esperado": "100"},
    {"llamada": "ingreso(10, 3)",  "esperado": "30"},
    {"stdout_contiene": null, "llamada": "ingreso(0, 99)", "esperado": "0"}
  ]
}
```

Dos tipos de test: `llamada+esperado` (se evalúa `repr(eval(llamada))` y se
compara con `esperado`) y `stdout_contiene` (se ejecuta el script completo
y se busca la subcadena en la salida). El harness JS los ejecuta sobre el
MISMO intérprete Pyodide del runner.

## 2. Transparencia del trade-off (documentado)

Los tests viajan al navegador (deben ejecutarse client-side): un estudiante
avanzado puede inspeccionarlos en las DevTools. Se acepta a conciencia — el
objetivo es aprender, no vigilar — y se documenta en el reporte. Las
respuestas de QUIZZES siguen sin viajar nunca.

## 3. API y validación

```
# El reto llega dentro del turno de estudio cuando toca ese paso:
POST /api/estudio → { ..., reto: {enunciado, seed, tests} | null }

POST /api/estudio/reto-superado
  body: { unidad: 0, objetivo: 1 }
  → { puntos_totales, texto }        # texto = celebración del tutor (LLM)
    409 si ya estaba superado (no repaga puntos)

POST /api/estudio/pista-reto
  body: { unidad: 0, codigo: "...", test_fallado: "ingreso(10,3) → 13, esperaba 30" }
  → { texto }                        # pista socrática
```

Validación del reto en el guion (`validar_reto`): seed parsea con
`ast.parse`; 2-4 tests; cada test tiene `llamada` no vacía y `esperado` o
`stdout_contiene`; el enunciado no está vacío. Persistencia: dentro del
guion v2 (columna `clases.guion`); superados en
`progreso.retos_superados: {"<clase>": [objetivos]}`.

## 4. Cambios por archivo

| Archivo | Cambio |
|---|---|
| `prompts.py` | El paso final de cada objetivo en `prompt_guion_v2` genera el reto (con la regla "resuélvelo y verifica tus tests antes de emitir"); `prompt_pista_reto` (socrático + código + test fallado) |
| `curso.py` | Modelo `RetoCodigo` + `validar_reto` (usa `ast`) dentro del guion v2 |
| `agente.py` | Adjuntar `reto` al turno cuando toca; `reto_superado` (idempotente, puntos una vez); `pista_reto` |
| `progreso.py` | `retos_superados` persistente |
| `web.py` | Endpoints `reto-superado` y `pista-reto`; `reto` en la respuesta de estudio |
| `frontend/` | `RetoCard.jsx`: editor Pyodide + harness de tests (evalúa `llamada`/captura stdout, compara, pinta ✓/✗ con mensaje) + botones Verificar/Pista |

## 5. Casos borde

- Código del estudiante con bucle infinito → el harness corre cada test con
  un guardián de tiempo (interrupción de Pyodide / timeout de 5 s) y lo
  reporta como ✗ "se quedó pensando demasiado".
- Errores de sintaxis → se muestran como salida del test con el traceback
  amigable ya existente en el runner.
- `esperado` con floats → comparación con tolerancia (`abs(a-b) < 1e-9`)
  cuando ambos parsean como número.
- Reto ya superado y el estudiante vuelve a verificar → ✓ visual, el
  endpoint responde 409 y el front no repite la celebración.
- El LLM genera un test incoherente → `validar_reto` lo rechaza y
  `pedir_json` reintenta con el error (mecanismo existente).

## 6. Fuera de alcance

- Ejecución server-side o sandboxing adicional (todo corre en el navegador
  del estudiante). — Retos multi-archivo. — Otros lenguajes (JS podría ser
  v3 con el propio motor del navegador).

## 7. Definición de Hecho

- [ ] Humo real: 2 retos generados; uno resuelto bien (✓✓✓, puntos, el
      tutor celebra) y uno saboteado (✗ con mensaje claro + pista socrática
      útil que NO da la solución).
- [ ] Bucle infinito probado a mano sin colgar la pestaña.
- [ ] Pruebas de abajo + suite + ruff/mypy; HALLAZGOS + reporte
      actualizados (incluida la nota del trade-off §2).

## 8. Pruebas

- `test_validar_reto_acepta_y_rechaza` (seed inválido, tests malformados)
- `test_turno_adjunta_reto_en_el_paso_final_del_objetivo`
- `test_reto_superado_suma_puntos_una_sola_vez` (segundo intento → 409)
- `test_pista_incluye_codigo_y_test_en_el_prompt`
- `test_pista_no_contiene_la_solucion_del_seed` (el seed resuelto no viaja)
- `test_curso_no_python_mantiene_reto_textual`
