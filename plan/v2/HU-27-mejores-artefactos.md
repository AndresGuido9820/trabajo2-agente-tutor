# HU-27 — Mejores artefactos: plantillas por concepto, verificación y regenerar

**Como** estudiante **quiero** demos interactivas más consistentes y a la
medida de cada tipo de concepto — y nunca una demo rota — **para** que el
botón ✨ siempre valga la pena.

## 1. Qué hace esta HU, explícito

Hoy el artefacto se genera con un prompt genérico ("haz una página
interactiva sobre X"): a veces sale una joya y a veces algo plano, tarda
1-2 min y si sale roto no hay remedio. Esta HU profesionaliza el pipeline:

1. **Plantillas por tipo de concepto.** Antes de generar, una heurística
   LOCAL (`clasificar_plantilla(conceptos)`, sin LLM: por palabras clave)
   elige la plantilla, y el prompt recibe instrucciones ESPECÍFICAS de esa
   interacción:

   | Plantilla | Conceptos que la disparan | Qué debe construir el LLM |
   |---|---|---|
   | `estado` | variable, asignación, tipos, expresión | Panel de "celdas" con inputs/sliders; al cambiar un valor se recalculan las dependientes y una tabla muestra `nombre → valor (tipo)` en vivo |
   | `flujo` | if, condicional, bucle, while, for, iteración | Stepper línea-a-línea: código a la izquierda con la línea actual resaltada; botones ⏮ ▶ ⏭; a la derecha el estado de variables por iteración |
   | `datos` | csv, dataframe, filtro, groupby, tabla, columnas | Tabla con datos de ejemplo del dominio del estudiante; controles para filtrar/agrupar y ver el ANTES→DESPUÉS de la operación |
   | `funcion` | función, parámetros, retorno, def | Caja entrada→proceso→salida: argumentos editables, botón "llamar", visualización del retorno y del cuerpo ejecutado |

   Si nada matchea → plantilla `estado` (la más general).

2. **Verificación automática ANTES de mostrar.** El HTML generado pasa por
   `_verificar_artefacto(html) -> list[str]` (stdlib `html.parser`):
   - parsea sin errores y empieza por `<!doctype html>`;
   - **cero recursos externos** (nada de `http(s)://` en `src|href|url()`,
     ni `fetch`/`XMLHttpRequest`/`import(`);
   - contiene `<script>` y ≥1 control interactivo
     (`<button|input|select|textarea|[onclick]`);
   - tamaño ≤ 40 KB; sin `alert(`/`confirm(`/`prompt(`.
   Si hay errores → se regenera UNA vez con la lista de errores en el
   prompt; si vuelve a fallar → error claro al usuario ("la demo no pasó el
   control de calidad, intenta regenerar") y NO se cachea el HTML malo.

3. **Demo por OBJETIVO, no por clase.** Cache en `curso.artefactos` con
   clave `"{clase}-obj{objetivo}"`. El botón ✨ genera la demo del objetivo
   que la conversación está trabajando (contexto mucho más específico).

4. **Botón "🔄 Regenerar"** en la tarjeta de la demo: invalida esa clave y
   genera de nuevo (para cuando la demo no gustó). Máximo 1 clic
   concurrente (el botón se deshabilita mientras genera).

5. **Prefetch silencioso**: al ARRANCAR un objetivo, el backend lanza la
   generación de su demo en segundo plano (hilo daemon; si el usuario nunca
   la pide, quedó cacheada para la próxima). El botón ✨ pasa de esperar
   1-2 min a ser casi instantáneo en el caso común.

## 2. API

```
POST /api/artefacto
  body:      { unidad: 0, objetivo: 1 | null, regenerar: false }
  respuesta: { html: "<!doctype html>...", plantilla: "flujo",
               cacheado: true }
  errores:   502 con detail="La demo no pasó el control de calidad..." si
             falla dos veces la verificación.
```

Compatibilidad: `objetivo: null` (o clases v1) usa el contexto de la clase
completa, como hoy.

## 3. Cambios por archivo

| Archivo | Cambio |
|---|---|
| `prompts.py` | `clasificar_plantilla` + 4 bloques de instrucciones de plantilla en `prompt_artefacto_v2` (con ejemplo de estructura esperada por plantilla) |
| `agente.py` | `artefacto_de_objetivo(clase, objetivo, regenerar)`; `_verificar_artefacto`; regeneración única con errores; prefetch en hilo al arrancar objetivo (lock por clave para no duplicar) |
| `web.py` | Body ampliado (`objetivo`, `regenerar`); campo `plantilla`/`cacheado` en la respuesta |
| `frontend/Clase.jsx` | Botón 🔄 en la tarjeta; badge de plantilla; estado "generando" |
| `config.py` | `ARTEFACTO_MAX_KB = 40` |

## 4. Casos borde

- Prefetch en curso y el usuario pulsa ✨ → se espera al MISMO futuro (no
  se lanza otra generación; lock por clave).
- Regenerar mientras el prefetch corre → se encola tras el lock.
- HTML con fences de Markdown → ya se toleran (se despojan antes de
  verificar).
- Conceptos en otro idioma o rarísimos → heurística cae a `estado`.
- El servidor se apaga con un prefetch vivo → hilo daemon muere sin efecto
  (el cache solo se escribe al final, transaccional).

## 5. Fuera de alcance

- Editor de artefactos por el estudiante. — Artefactos con librerías
  externas (prohibidas por diseño). — Persistir métricas de calidad (v3).

## 6. Definición de Hecho

- [ ] Humo real: 4 demos (una por plantilla) generadas y revisadas a mano;
      ≥90 % de 10 generaciones pasan verificación al primer intento.
- [ ] Regenerar y prefetch verificados en el navegador.
- [ ] Pruebas de abajo + suite + ruff/mypy; HALLAZGOS actualizado.

## 7. Pruebas

- `test_clasificar_plantilla_cada_categoria_y_fallback`
- `test_verificador_rechaza_cdn_fetch_sin_script_sin_controles_y_40kb`
- `test_verificacion_fallida_regenera_una_vez_con_errores_en_prompt`
- `test_doble_fallo_no_cachea_y_devuelve_502`
- `test_cache_por_objetivo_y_regenerar_invalida`
- `test_prefetch_no_duplica_generacion` (lock)
