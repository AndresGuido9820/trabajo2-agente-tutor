# Investigación: guías de producto y UX aplicadas (HU-14)

Fecha: 2026-07-20. Auditoría de nuestra app contra guías abiertas de producto
y UX, y decisiones aplicadas. Fuentes principales:
[10 heurísticas de Nielsen](https://www.nngroup.com/articles/ten-usability-heuristics/) ·
[NN/g Progress Indicators](https://www.nngroup.com/articles/progress-indicators/) ·
[Laws of UX](https://lawsofux.com/) ·
[GOV.UK Design System](https://design-system.service.gov.uk/) ·
[Shopify Polaris — Loading](https://polaris-react.shopify.com/patterns/loading) ·
[Material 3 — motion/states](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs) ·
[PAIR de Google](https://pair.withgoogle.com/) · [Shape of AI](https://www.shapeof.ai/) ·
[growth.design — Duolingo](https://growth.design/case-studies/duolingo-user-retention) ·
[The A11Y Project](https://www.a11yproject.com/checklist/).

## Sistema base adoptado

- **Paleta dark AA** (familia GitHub Dark, contrastes verificados): fondo
  `#0d1117`, superficie `#161b22`, texto `#e6edf3` (~15:1), secundario
  `#8b949e` (~5.6:1), acento `#58a6ff` (~7:1), éxito `#3fb950`, error
  `#f85149`, advertencia `#d29922`. Regla A11Y: nunca color solo — badges
  con texto, no solo emoji.
- **Tipografía** escala 1.25 base 16 px; cuerpo de lectura a `max-width:70ch`.
- **Espaciado** escala de 4 px; radios 6/10/999.
- **Foco**: `:focus-visible` con anillo de 2 px en todo lo interactivo.
- **Motion** (tokens M3): 180 ms interacciones, 280 ms paneles, ≤500 ms
  celebraciones; `prefers-reduced-motion` respetado globalmente.

## Cambios aplicados (con su fuente)

1. **Esperas largas de IA**: loader por fases con barra asintótica y tiempo
   esperado ("~60 s") para curso/guía/quiz (NN/g: >10 s exige progreso, no
   spinner) + **generación de guía no bloqueante** (puedes volver al curso;
   badge "Generando…" y toast al terminar — Polaris).
2. **Skeleton screens** de guía y quiz replicando el layout (Polaris:
   skeleton por defecto, spinner último recurso).
3. **Prefetch del quiz** al llegar a la última sección de la guía → la
   espera de la evaluación desaparece (Doherty Threshold). Además el quiz
   ahora se basa en la guía ya generada (antes regeneraba una lección: ~60 s
   desperdiciados).
4. **Formulario GOV.UK-style**: labels visibles + hints + "(opcional)",
   chips de sugerencia (Shape of AI: Suggestions), autofocus, preview del
   valor antes de pedir datos (growth.design: valor primero).
5. **Un CTA por unidad según estado** y la siguiente unidad resaltada como
   único elemento primario (Hick's Law, Von Restorff).
6. **Progreso de curso visible**: "N de M unidades" + barra en el header
   (Goal-Gradient, Zeigarnik).
7. **Resultado con Peak-End**: aprobado = celebración única ≤500 ms + toast;
   reprobado = encuadre de crecimiento ("2 de 4 — cerremos esas brechas"),
   desglose por pregunta y CTA directo al conversatorio (heurística 9).
8. **Chat**: typing indicator inmediato, autofocus, Enter para enviar,
   sugerencias de arranque ("Explícame la pregunta 3" desde las falladas),
   botón persistente de reintento, disclosure "una IA que puede equivocarse"
   (Shape of AI: Disclosure/Caveat).
9. **Checkpoints**: `aria-live` en el feedback, opciones operables por
   teclado, reintento sin castigo con encuadre de aprendizaje (PAIR).
10. **Interacción con el agente en toda la guía** (esencia del producto):
    "💬 Preguntar al tutor" por sección (socrático, sin revelar el
    checkpoint) y "✨ Ver demo interactiva" — **mini-artefactos**: el LLM
    genera una página HTML autocontenida e interactiva que ilustra el
    concepto, montada en `iframe sandbox="allow-scripts"` (sin red ni acceso
    a la app), cacheada en `curso.json`. Inspirado en los Artifacts de
    Claude.

## No adoptado (documentado)

- **Streaming** de la generación (el mayor salto de percepción en AI UX):
  requiere SSE + cambios en `ClienteLLM`; trabajo futuro.
- Ligas/vidas de Duolingo: dark patterns documentados, excluidos a propósito.
