# Profe Bit — Tutor de Programación con LLMs (Trabajo 02)

[![CI](https://github.com/AndresGuido9820/trabajo2-agente-tutor/actions/workflows/ci.yml/badge.svg)](https://github.com/AndresGuido9820/trabajo2-agente-tutor/actions/workflows/ci.yml)

Agente tutor interactivo que enseña fundamentos de programación. El
estudiante **pide su curso conversando** ("hazme un curso de Python para
analizar mis ventas; sé Excel"): el asesor pregunta lo que falta, propone un
temario y lo crea al confirmar. Cada **clase es una conversación** con el
tutor (método socrático), con evaluación que desbloquea la siguiente,
conversatorio de dudas al reprobar, código ejecutable en el navegador
(Pyodide), demos interactivas generadas por el LLM y puntos/racha.

Curso: *Normalización: aplicaciones de LLMs y Agentes para la enseñanza de
la programación básica* — Prof. Juan David Ospina Arango.

## Cómo correrlo

Requisitos: Python ≥ 3.12 y [uv](https://docs.astral.sh/uv/). (No necesitas
Node: el frontend ya viene compilado.)

```bash
git clone https://github.com/AndresGuido9820/trabajo2-agente-tutor
cd trabajo2-agente-tutor
uv sync

cp .env.example .env          # y pon tu OPENAI_API_KEY=sk-...

uv run tutor-web              # abre http://127.0.0.1:8017 (UI web, React)
uv run tutor                  # alternativa: CLI en la terminal
```

## Qué hace (recorrido)

1. **Mis cursos**: menú con todos tus cursos y su progreso; "＋ Nuevo curso".
2. **Diseño conversacional**: describes qué quieres aprender; el asesor
   resume, pregunta tu nivel/experiencia, propone un temario y crea el curso
   cuando confirmas. El diseño queda **estructurado en la base de datos**
   (clase → título, objetivo, subtemas, prompt/guion) y como documento
   `curso.md` visible, descargable y **editable** (editor estructurado).
3. **Clases como conversaciones extensas**: cada clase se estructura en
   3-4 **objetivos de aprendizaje**, cada uno con su secuencia PRIMM
   (predices antes de que te explique) y un **mini-quiz de 2 preguntas**
   al cerrarlo (+5 ⭐ por acierto; si fallas ambas, el tutor repasa con
   otro ejemplo y reintentas). El tutor **escribe en vivo** (SSE) y decide
   con criterio si tu mensaje avanza el paso o es una duda. Un **panel
   lateral** muestra los objetivos marcándose en tiempo real. Los bloques
   de código traen **▶ Pruébalo** (Python en tu navegador vía Pyodide) y
   al cerrar cada objetivo llega un **⌨️ reto de código real** con tests
   automáticos estilo freeCodeCamp (+10 ⭐, pista socrática si te trabas).
   El botón **✨** genera una demo interactiva del objetivo (plantilla
   según el concepto, verificada antes de mostrarse, regenerable).
4. **Evaluación y progresión**: evaluación final de 6+ preguntas con
   **niveles Bloom** (recordar/comprender/aplicar) y **nota ponderada** —
   saber definiciones no basta si no aplicas. Las preguntas salen de un
   **banco por clase sin repetición entre intentos** y priorizan lo que
   fallaste en los mini-quices. Con 70+ apruebas (+30 ⭐) y desbloqueas la
   siguiente clase; si no, **conversatorio socrático** y reintento con
   preguntas nuevas. Lo fallado entra al **🔁 Repaso del día** (repetición
   espaciada 1-3-7). Puntos, racha y estadísticas (📈 Mi progreso)
   persistentes; buscador global ⌘K; exportar el curso a .zip.

## Arquitectura

```
frontend/  (React + Mantine, Vite)  →  build en src/tutor/static/dist
src/tutor/
  web.py       API FastAPI (multi-curso; sirve el front)
  agente.py    Orquestador: lecciones, quizzes, candados, chats, artefactos
  curso.py     Temario/guiones/guías + persistencia del diseño
  evaluacion.py  Quiz: generación LLM + calificación local determinista
  prompts.py   TODOS los prompts, versionados (PRIMM, misconceptions, socrático)
  llm.py       Cliente OpenAI: reintentos con backoff, JSON validado
  db.py        SQLite por curso: curso, clases (con su prompt), perfil,
               progreso, chat; migraciones automáticas
  ui.py, __main__.py   CLI equivalente
```

- **Datos**: `data/cursos/<id>/tutor.db` (una BD por curso) + `curso.md`.
- **Seguridad**: la API key solo vive en `.env` (gitignoreado); las
  respuestas correctas de quizzes/checkpoints nunca viajan al navegador;
  las demos corren en `iframe sandbox` sin red. Excepción consciente: los
  tests de los retos de código sí viajan (se ejecutan en tu navegador con
  Pyodide); el objetivo es aprender, no vigilar.
- **Decisiones y fuentes**: `docs/INVESTIGACION*.md` (pedagogía, OSS, UX) y
  `docs/HALLAZGOS.md` (bitácora). Plan por HU en `plan/`.

## Desarrollo

```bash
uv run pytest              # 289 pruebas (LLM siempre con dobles)
uv run ruff format --check . && uv run ruff check .
uv run mypy src            # estricto

# Frontend (solo si vas a tocar la UI)
cd frontend && npm install && npm run dev    # proxy a :8017
npm run build                                 # regenera static/dist

# Manuales (cuestan tokens):
uv run python scripts/humo_llm.py             # humo del cliente LLM
uv run python scripts/exportar_curso.py datos-excel   # cursos de muestra
uv run python scripts/capturas_playwright.py  # bot que captura la app
uv run python scripts/e2e_reintento.py        # caída del server + reintento
uv run python scripts/a11y_playwright.py      # axe-core (no cuesta tokens)
```

CI en GitHub Actions: lint + tipos + pruebas + build del frontend en cada
push (`.github/workflows/ci.yml`).

### Accesibilidad

La app se opera completa con teclado (Tab/Enter/Espacio; `⌘K` abre el
buscador, `Esc` cierra modales). El chat es una región `aria-live` que
anuncia los mensajes del tutor; los botones-ícono llevan `aria-label`; los
temas claro y oscuro pasan contraste AA (los colores de la variante
"light" y el `dimmed` se ajustaron en `frontend/src/global.css`). La
auditoría automática con axe-core (`scripts/a11y_playwright.py`) corre
sobre Mis cursos, Clase y Mi progreso: 0 violaciones serias/críticas.

## Entregables del curso

- `entregables/REPORTE.md` — reporte técnico (con capturas del recorrido).
- `entregables/GUION-VIDEO.md` — guion del video de demostración.
- `entregables/cursos-muestra/` — 2 cursos generados (perfiles y lenguajes
  distintos).
- `SPEC.md` — requisitos, criterios de la rúbrica y pruebas de aceptación.
