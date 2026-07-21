# HU-34 — Robustez del front: desconexión, reintentos y borradores

**Como** estudiante **quiero** que la app no pierda mi mensaje si algo
falla (red caída, servidor reiniciando, generación larga) **para** confiar
en ella durante una sesión de estudio real.

## Qué hace, explícito

1. **Detección de desconexión**: si un fetch falla por red (TypeError) o
   el navegador reporta `offline`, aparece una barra fija "⚠️ Sin conexión
   con el tutor — reintentando…" que desaparece sola al volver.
2. **Reintento del último mensaje**: si un turno falla, la burbuja del
   usuario queda con estado "no enviado" y un botón **"Reintentar"** que
   repite EXACTAMENTE esa llamada (no hay que reescribir). Un solo clic;
   sin reintentos automáticos de mensajes (para no duplicar turnos LLM).
3. **Borrador persistente**: lo escrito en el composer se guarda en
   `localStorage` por canal (`borrador:u3`); recargar la página no pierde
   el texto a medio escribir. Se limpia al enviar con éxito.
4. **Timeout visible**: si una generación supera 3 min, el indicador
   cambia a "esto está tardando más de lo normal — puedes seguir esperando
   o reintentar" con botón de reintento (aborta el fetch anterior con
   AbortController).
5. **Errores del backend** (4xx/5xx) siguen mostrando su mensaje, pero los
   502 de LLM ofrecen "Reintentar" directamente en la notificación.

## Tareas

- [x] `api.js`: clasificación de errores (red vs HTTP), AbortController,
      helper `conReintento(fn)` que expone el retry al llamador.
- [x] Componente `BarraConexion` (listener online/offline + ping ligero a
      `/api/estado` cada 30 s SOLO cuando está offline).
- [x] `Clase.jsx`/`CreacionChat.jsx`: burbuja "no enviado" + Reintentar;
      borradores en localStorage; timeout de 3 min con aviso.
- [x] Pruebas backend: ninguna (es front); pruebas de humo manuales con
      el servidor apagado/encendido documentadas en la HU + prueba
      Playwright: matar el server, enviar, ver "no enviado", revivir,
      reintentar OK.

## Casos borde

- Doble clic en Reintentar → botón se deshabilita al primer clic.
- El servidor respondió pero tarde (carrera con el abort) → la respuesta
  abortada se descarta; el reintento es la fuente de verdad.
- localStorage lleno/bloqueado → se ignora en silencio (best-effort).

## Pruebas

`test_playwright_reintento_tras_caida_del_servidor` (script E2E)
· revisión manual guiada: offline → barra; borrador sobrevive recarga.
