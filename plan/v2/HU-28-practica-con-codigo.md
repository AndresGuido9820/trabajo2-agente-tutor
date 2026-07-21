# HU-28 — Práctica con código real: retos verificados con Pyodide

**Como** estudiante **quiero** que el reto de cada objetivo sea escribir
código de verdad que se verifique automáticamente en mi navegador **para**
pasar de responder opciones a programar (el salto de quiz-driven a
code-driven, patrón freeCodeCamp/futurecoder).

## Criterios de aceptación

- En el paso *reto* de cada objetivo (guion v2), el tutor entrega un
  **reto de código**: enunciado + código inicial (`seed`) + **tests
  ocultos** generados junto con el guion (JSON validado: cada test es
  `{entrada, salida_esperada}` o una aserción sobre stdout).
- El front muestra el editor (el runner Pyodide existente) con el seed; el
  botón **"Verificar"** ejecuta el código del estudiante + los tests EN el
  navegador y muestra por test: ✓/✗ con mensaje pedagógico (qué se esperaba
  vs qué dio), estilo freeCodeCamp.
- Pasar todos los tests marca el paso como superado (+10 ⭐) y el chat
  continúa; fallar permite pedir **una pista al tutor** (socrática, recibe
  el código del estudiante y el test fallado — nunca da la solución).
- Los tests nunca viajan con la respuesta esperada visible en la UI (van en
  el payload pero ofuscados no: son ejecutables client-side — se acepta que
  un estudiante avanzado los inspeccione; documentar el trade-off).
- Cursos no-Python: el paso reto cae al comportamiento actual (texto).

## Interfaz

```python
# curso.py (guion v2)
@dataclass(frozen=True) class RetoCodigo:
    enunciado: str
    seed: str
    tests: list[dict]   # {"llamada": "ingreso(25, 4)", "esperado": "100"} |
                        # {"stdout_contiene": "Total: 100"}

# API
POST /api/estudio/reto-superado {unidad, objetivo}   # marca y da puntos
POST /api/estudio/pista-reto {unidad, codigo, test_fallado} -> {texto}
```

Front: `RetoCard` (editor + Verificar + resultados por test + pista).

## Tareas

- [ ] `prompts.py`: el guion v2 genera el reto con seed y 2-4 tests
      (verificación independiente: el prompt debe resolver el reto y
      comprobar los tests antes de emitirlos).
- [ ] Validador del reto (tests bien formados, seed compila con `ast`).
- [ ] Front: `RetoCard` con ejecución de tests sobre Pyodide (armar un
      harness JS que llama la función/captura stdout y compara).
- [ ] Backend: endpoints de superado y de pista (la pista usa system
      socrático + código del estudiante).
- [ ] Pruebas: validación del reto, endpoint superado suma puntos una vez,
      pista incluye código y test en el prompt sin filtrar solución.
- [ ] Humo real: 2 retos generados, resolverlos y romperlos a propósito.

## Pruebas

- `test_guion_v2_incluye_reto_con_tests_validos`
- `test_reto_superado_marca_y_suma_puntos_una_vez`
- `test_pista_recibe_codigo_y_test_sin_dar_solucion`
- `test_curso_no_python_usa_reto_textual`
