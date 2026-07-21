# HU-36 — Tema claro/oscuro y preferencias de lectura

**Como** estudiante **quiero** elegir tema claro u oscuro y el tamaño del
texto **para** estudiar cómodo en cualquier condición de luz.

## Qué hace, explícito

1. Botón 🌓 en la barra lateral (junto a racha/puntos): alterna
   claro/oscuro/auto (auto = `prefers-color-scheme`). Mantine ya soporta
   `colorScheme`; se persiste en `localStorage` y arranca sin flash
   (script inline que aplica el esquema antes del render).
2. Selector de tamaño de texto (A− / A / A+): tres pasos que ajustan la
   `fontSize` base del tema Mantine (14/15/16.5). Persistido igual.
3. TODOS los componentes se ven bien en claro: pasada de revisión sobre
   colores fijos (`#0a0d13` de bloques de código, iframes de demos, runner)
   → tokens del tema en su lugar; el iframe de artefactos conserva su tema
   oscuro interno (viene del LLM) pero con borde correcto.
4. Sin backend: preferencias 100 % locales.

## Tareas

- [x] `main.jsx`: `colorSchemeManager` de Mantine con localStorage +
      script anti-flash en `index.html`.
- [x] Componente `Preferencias` (Menu con 🌓 y A−/A/A+).
- [x] Auditoría de colores fijos → `var(--mantine-color-*)` o
      `light-dark()`; revisar Prosa/runner/quiz en ambos temas.
- [x] Captura Playwright en claro para el reporte (opcional).
- [x] Pruebas: unit front no hay harness — validación por bot Playwright:
      alternar tema y verificar screenshot claro sin colores rotos
      (revisión visual manual documentada).

## Casos borde

- localStorage bloqueado → cae a "auto" sin persistir (best-effort).
- Código resaltado en claro: fondo de `pre` pasa a gris claro con borde.

## Pruebas

Script Playwright: `capturas` toma 01 y 05 también en claro; checklist
manual de contraste en ambos temas (texto, chips, badges, feedback).
