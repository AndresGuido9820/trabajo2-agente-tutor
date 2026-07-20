"""Exporta un curso de muestra completo a Markdown (entregable E4).

Corre el flujo real (temario → todas las lecciones → quiz de las primeras
unidades) para un perfil predefinido y lo escribe en
``entregables/cursos-muestra/<nombre>/``. CUESTA TOKENS: uso manual.

Uso: ``uv run python scripts/exportar_curso.py <perfil>``
Perfiles disponibles: front-principiante, datos-excel.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tutor.config import cargar_configuracion
from tutor.curso import Curso, generar_leccion, generar_temario
from tutor.errores import ErrorTutor
from tutor.evaluacion import generar_quiz
from tutor.llm import ClienteOpenAI
from tutor.models import Nivel, Objetivo, PerfilEstudiante
from tutor.progreso import Progreso
from tutor.prompts import PROMPTS_VERSION, system_tutor

QUIZZES_A_EXPORTAR = 2  # quiz de las 2 primeras unidades como muestra

PERFILES = {
    "front-principiante": PerfilEstudiante(
        nivel=Nivel.NUNCA,
        experiencia="uso redes sociales y hago presentaciones; nunca he programado",
        objetivo=Objetivo.FRONT,
        objetivo_detalle="",
        lenguaje="javascript",
    ),
    "datos-excel": PerfilEstudiante(
        nivel=Nivel.BASICO,
        experiencia="manejo Excel avanzado en mi trabajo (fórmulas, tablas dinámicas)",
        objetivo=Objetivo.DATOS,
        objetivo_detalle="",
        lenguaje="python",
    ),
}


def _describir_perfil_md(nombre: str, perfil: PerfilEstudiante) -> str:
    """Encabezado del curso exportado con el perfil que lo generó."""
    return f"""# Curso de muestra: {nombre}

Generado con prompts v{PROMPTS_VERSION}.

**Perfil del estudiante:**

- Nivel: {perfil.nivel.descripcion}
- Experiencia: {perfil.experiencia}
- Objetivo: {perfil.objetivo.descripcion}
- Lenguaje: {perfil.lenguaje}

---
"""


def exportar(nombre: str) -> int:
    """Genera y exporta el curso completo del perfil ``nombre``."""
    perfil = PERFILES[nombre]
    cliente = ClienteOpenAI(cargar_configuracion())
    destino = Path("entregables/cursos-muestra") / nombre
    destino.mkdir(parents=True, exist_ok=True)

    print(f"Generando temario para '{nombre}'...")
    curso = Curso(temario=generar_temario(cliente, perfil))
    indice_md = [_describir_perfil_md(nombre, perfil), "## Temario\n"]
    for i, unidad in enumerate(curso.temario.unidades):
        indice_md.append(
            f"{i + 1}. **{unidad.titulo}** — {unidad.objetivo} "
            f"(_conceptos: {', '.join(unidad.conceptos)}_)"
        )
    (destino / "00-temario.md").write_text("\n".join(indice_md), "utf-8")

    progreso = Progreso()
    for i, unidad in enumerate(curso.temario.unidades):
        print(f"  Lección {i + 1}/{len(curso.temario.unidades)}: {unidad.titulo}")
        leccion = generar_leccion(cliente, perfil, curso, i, progreso)
        (destino / f"{i + 1:02d}-leccion.md").write_text(leccion, "utf-8")

        if i < QUIZZES_A_EXPORTAR:
            print(f"  Quiz de la unidad {i + 1}")
            quiz = generar_quiz(
                cliente,
                titulo_unidad=unidad.titulo,
                conceptos=unidad.conceptos,
                leccion_md=leccion,
                unidad=i,
                system=system_tutor(perfil),
            )
            lineas = [f"# Quiz — {unidad.titulo}\n"]
            for n, p in enumerate(quiz.preguntas, start=1):
                lineas.append(f"## Pregunta {n}\n\n{p.enunciado}\n")
                for letra, opcion in zip("abcd", p.opciones, strict=True):
                    marca = " ✅" if letra == "abcd"[p.correcta] else ""
                    lineas.append(f"- {letra}) {opcion}{marca}")
                lineas.append(f"\n> **Explicación:** {p.explicacion}")
                lineas.append(f"> **Concepto:** {p.concepto}\n")
            (destino / f"{i + 1:02d}-quiz.md").write_text("\n".join(lineas), "utf-8")

    print(f"Curso exportado en {destino}")
    return 0


def main() -> int:
    """Punto de entrada del exportador."""
    if len(sys.argv) != 2 or sys.argv[1] not in PERFILES:
        print(f"Uso: exportar_curso.py <{'|'.join(PERFILES)}>")
        return 2
    try:
        return exportar(sys.argv[1])
    except ErrorTutor as error:
        print(f"FALLO — {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
