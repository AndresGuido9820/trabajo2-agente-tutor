# HU-38 — Accesibilidad y teclado de punta a punta

**Como** estudiante (incluido quien usa lector de pantalla o solo teclado)
**quiero** operar toda la app sin mouse y con anuncios correctos **para**
que el tutor sea usable por cualquiera.

## Qué hace, explícito

1. **Teclado completo**: orden de tabulación lógico en cada vista; `Enter`
   envía (ya), `Esc` cierra modales/spotlight; los items de la barra
   lateral son botones reales (no divs clicables) navegables con Tab y
   activables con Enter/Espacio; el quiz se responde con flechas dentro
   del RadioGroup.
2. **Anuncios de lector de pantalla**: la zona del chat es
   `aria-live="polite"` (los mensajes nuevos del tutor se anuncian); las
   notificaciones ya usan role apropiado (Mantine); los indicadores de
   "escribiendo…" son `aria-hidden` (ruido).
3. **Etiquetas**: todos los botones-ícono (✨, 🌓, ⋯, 🔎) llevan
   `aria-label` descriptivo; los iframes de demos llevan `title`.
4. **Focus management**: al entrar a una clase, el foco va al composer; al
   abrir un modal, al primer control; al cerrarlo, vuelve al disparador.
5. **Contraste AA verificado** en ambos temas (HU-36): revisar dim/tx3
   sobre fondos de tarjeta; documentar los pares corregidos.
6. **prefers-reduced-motion**: ya global por CSS; verificar que las
   animaciones de Mantine lo respetan (`respectReducedMotion` del tema).

## Tareas

- [x] Auditoría con teclado de las 6 vistas (checklist en esta HU).
- [x] Cambios en componentes: botones reales, aria-labels, aria-live en
      `ZonaChat`, focus management (useRef + focus()).
- [x] `respectReducedMotion: true` en el tema.
- [x] Validación: axe-core vía Playwright (`npx playwright` +
      `@axe-core/playwright`) en las vistas principales → 0 violaciones
      serias/críticas; el script queda en `scripts/a11y_playwright.py`.
- [x] Documentar en README (sección accesibilidad).

## Casos borde

- Spotlight abierto + Esc → cierra sin robar el foco del composer previo.
- Lector + streaming (HU-35): anunciar el mensaje COMPLETO al terminar,
  no cada delta (aria-live en el contenedor final, no en el parcial).

## Pruebas

`scripts/a11y_playwright.py` (axe: 0 críticas en Mis cursos, Creación,
Clase, Diseño) · checklist manual de teclado por vista (en esta HU).
