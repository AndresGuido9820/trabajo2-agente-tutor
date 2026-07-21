# HU-27 — Mejores artefactos: plantillas por concepto, verificación y regenerar

**Como** estudiante **quiero** demos interactivas más consistentes y
efectivas — con el tipo de interacción adecuado para cada concepto y sin
demos rotas — **para** ilustrarme de verdad con cada tema.

## Criterios de aceptación

- **Plantillas por tipo de concepto**: el prompt del artefacto elige (y
  recibe instrucciones específicas) según el concepto a ilustrar:
  - *estado/variables*: panel de "celdas" con sliders/inputs y la tabla de
    estado actualizándose en vivo;
  - *control de flujo (if/bucles)*: stepper línea-a-línea con resaltado de
    la línea actual y el estado por iteración (estilo Python Tutor);
  - *datos/tablas*: tabla interactiva con filtros/agrupación simulando la
    operación (p. ej. groupby) paso a paso;
  - *funciones*: caja entrada→proceso→salida con argumentos editables.
- **Verificación automática antes de mostrar**: el HTML generado se valida
  (parsea sin errores, sin recursos externos, tamaño < 40 KB, contiene
  `<script>` y al menos un control interactivo); si falla, se regenera una
  vez con el error en el prompt; si vuelve a fallar, mensaje claro.
- **Botón "🔄 Regenerar demo"** en la tarjeta (invalida el cache de ese
  artefacto) y **una demo por objetivo** (cache por `clase-objetivo`, ya no
  solo por clase).
- Latencia comunicada: la tarjeta muestra fase + tiempo esperado, y la demo
  del objetivo actual se **pre-genera en segundo plano** mientras el
  estudiante conversa (prefetch, mismo patrón del quiz).

## Interfaz

```python
# prompts.py
def prompt_artefacto_v2(concepto, tipo_plantilla, contexto, lenguaje) -> str
def clasificar_plantilla(conceptos: list[str]) -> str   # heurística local

# agente.py
def artefacto_de_objetivo(self, clase, objetivo, regenerar=False) -> str
def _verificar_artefacto(html) -> list[str]  # errores; [] si pasa

# API
POST /api/artefacto {unidad, objetivo?, regenerar?}
```

## Tareas

- [ ] Heurística `clasificar_plantilla` (por palabras de los conceptos) +
      4 bloques de instrucciones de plantilla en `prompts.py`.
- [ ] Verificador de HTML (html.parser de stdlib + reglas) con regeneración
      única ante fallo.
- [ ] Cache por `clase-objetivo` + `regenerar` + prefetch en `turno_estudio`.
- [ ] Front: botón 🔄 en la tarjeta de demo; indicador de fase.
- [ ] Pruebas: clasificación de plantillas, verificador (casos rotos:
      recurso externo, sin script, gigante), regeneración única, cache por
      objetivo, prefetch no duplica.
- [ ] Humo real: 4 demos (una por plantilla) verificadas a mano.

## Pruebas

- `test_clasificar_plantilla_por_conceptos`
- `test_verificador_rechaza_html_con_cdn_o_sin_interaccion`
- `test_fallo_de_verificacion_regenera_una_vez`
- `test_cache_por_objetivo_y_regenerar`
