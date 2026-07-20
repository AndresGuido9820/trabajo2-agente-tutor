# HALLAZGOS — Bitácora de desarrollo

Registro cronológico de decisiones, problemas y aprendizajes. Cada entrada:
fecha, contexto, hallazgo y decisión/acción. Este archivo alimenta la sección
de "desafíos y soluciones" del reporte técnico (10 % de la nota).

---

## 2026-07-20 — Arranque del proyecto

**Contexto:** definición de stack y arquitectura (ver `docs/INVESTIGACION.md`).

**Hallazgos / decisiones:**

1. **Sin framework de agentes.** El flujo es determinista (perfil → temario →
   lección → quiz), así que LangChain/CrewAI agregan dependencia y magia sin
   beneficio. Orquestación propia de ~1 módulo. *Trade-off aceptado:* si el
   proyecto creciera a tool-calling libre, habría que reevaluar.
2. **JSON por prompt + validación propia** en vez de tool-use forzado:
   portable y explícito; el costo es escribir validadores a mano, que además
   son el material perfecto para pruebas unitarias.
3. **Lecciones bajo demanda con cache.** Cumple el requisito de navegar
   unidades no generadas y reduce costo de tokens en demos.
4. **Python 3.14 local vs. 3.12 mínimo declarado:** se desarrolla en 3.14 pero
   `requires-python = ">=3.12"` para no exigir bleeding edge al calificador.
5. **Git Flow:** `main` (estable/entregas) ← `develop` (integración) ←
   `feature/hu-XX-*` (una rama por HU), merges con `--no-ff` para conservar
   la historia de cada HU. Commits en español, sin co-autores.

---

<!-- Plantilla:

## AAAA-MM-DD — Título corto

**Contexto:** qué se estaba haciendo (HU-XX).

**Hallazgo:** qué se descubrió (bug, limitación del LLM, sorpresa de la API).

**Decisión/acción:** qué se hizo y por qué; alternativas descartadas.
-->
