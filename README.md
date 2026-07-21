# Tutor de Programación con LLMs — Trabajo 02

Agente interactivo (CLI) que enseña fundamentos de programación adaptándose al
perfil del estudiante: evalúa sus conocimientos previos y objetivos, genera un
curso personalizado con un LLM (OpenAI GPT), crea evaluaciones y lleva el
progreso.

Curso: *Normalización: aplicaciones de LLMs y Agentes para la enseñanza de la
programación básica* — Prof. Juan David Ospina Arango.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `SPEC.md` | Especificación: requisitos, criterios de evaluación del entregable y pruebas de aceptación |
| `RULES.md` | Reglas de trabajo, calidad de código, linters y convenciones |
| `docs/INVESTIGACION.md` | Investigación previa (antes de la primera línea de código) |
| `docs/HALLAZGOS.md` | Bitácora de hallazgos durante el desarrollo |
| `docs/TESTING.md` | Estrategia de pruebas: qué se testea, cómo y cuándo |
| `plan/HU-*.md` | Historias de usuario, cada una con sus tareas y criterios |
| `src/tutor/` | Código fuente del agente |
| `tests/` | Pruebas automatizadas (pytest) |

## Configuración

Requisitos: Python ≥ 3.12 y [uv](https://docs.astral.sh/uv/).

```bash
# 1. Clonar e instalar dependencias
git clone <repo>
cd trabajo2-agente-tutor
uv sync

# 2. Configurar la API key (nunca se versiona)
cp .env.example .env
# editar .env y poner OPENAI_API_KEY=sk-...

# 3a. Ejecutar el tutor en la terminal
uv run tutor

# 3b. …o en el navegador (interfaz web simple)
uv run tutor-web        # abre http://127.0.0.1:8017 (UI React ya compilada)
```

## Comandos de desarrollo

```bash
uv run pytest            # pruebas
uv run ruff check .      # linter
uv run ruff format .     # formateo
uv run mypy src          # tipos
```

## Estado del proyecto

El avance se rastrea por HU en `plan/` (checkboxes por tarea). Los hallazgos y
decisiones se registran en `docs/HALLAZGOS.md`.

## Frontend (React + Mantine)

El build compilado está versionado en `src/tutor/static/dist` (no necesitas
npm para usar la app). Para desarrollarlo:

```bash
cd frontend
npm install
npm run dev      # dev server con proxy a :8017
npm run build    # regenera src/tutor/static/dist
```
