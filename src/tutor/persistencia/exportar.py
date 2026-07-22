"""Exportación del curso a un paquete .zip de Markdown (plan/v2/HU-33).

El zip se arma EN MEMORIA desde la base de datos del curso: diseño,
transcripción de cada clase (con hitos de evaluación) y resultados. No se
limita el tamaño: es una descarga local y las transcripciones van completas.
"""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from pathlib import Path

from tutor.config import NOTA_APROBATORIA
from tutor.ensenanza.agente import ARCHIVO_DB
from tutor.ensenanza.curso import cargar_curso, cargar_plan_md
from tutor.ensenanza.progreso import Progreso, cargar_progreso
from tutor.persistencia import db

_ROLES = {"yo": "Tú", "tutor": "Profe Bit"}


def slug(texto: str, defecto: str = "clase") -> str:
    """Nombre seguro para archivo: minúsculas, sin tildes, guiones."""
    plano = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    limpio = re.sub(r"[^a-z0-9]+", "-", plano.lower()).strip("-")
    return limpio or defecto


def _transcripcion(mensajes: list[dict[str, str]]) -> str:
    """Chat de una clase como Markdown legible (Tú: / Profe Bit:)."""
    if not mensajes:
        return "_(sin conversación todavía)_\n"
    partes = []
    for m in mensajes:
        rol = _ROLES.get(m["rol"], m["rol"])
        partes.append(f"**{rol}:**\n\n{m['texto']}\n")
    return "\n---\n\n".join(partes)


def _hitos(progreso: Progreso, indice: int) -> str:
    """Hitos de la clase: intentos de evaluación y si quedó completada."""
    lineas = []
    for r in progreso.resultados:
        if r.unidad == indice:
            veredicto = "aprobada" if r.nota >= NOTA_APROBATORIA else "reprobada"
            lineas.append(
                f"> 🎯 Evaluación: {r.nota}/100 — {veredicto} ({r.fecha[:10]})"
            )
    if indice in progreso.completadas:
        lineas.append("> 🎉 Clase completada")
    return ("\n".join(lineas) + "\n\n") if lineas else ""


def _resultados_md(progreso: Progreso, titulos: list[str]) -> str:
    """Resumen de notas, puntos y racha del estudiante."""
    lineas = ["# Mis resultados", ""]
    lineas.append(f"- Puntos: ⭐ {progreso.puntos}")
    lineas.append(f"- Racha: 🔥 {progreso.racha} días (mejor: {progreso.mejor_racha})")
    lineas.append("")
    if not progreso.resultados:
        lineas.append("_(todavía no hay evaluaciones presentadas)_")
    for indice, titulo in enumerate(titulos):
        notas = [r.nota for r in progreso.resultados if r.unidad == indice]
        if notas:
            lineas.append(
                f"- **Clase {indice + 1}: {titulo}** — intentos: "
                f"{', '.join(str(n) for n in notas)} · mejor: {max(notas)}/100"
            )
    return "\n".join(lineas) + "\n"


def paquete_zip(dir_curso: Path) -> bytes:
    """Arma el paquete de estudio del curso como zip en memoria.

    Raises:
        ValueError: Si el curso aún no tiene diseño (temario).
    """
    ruta = dir_curso / ARCHIVO_DB
    curso = cargar_curso(ruta)
    if curso is None:
        raise ValueError("El curso no tiene diseño todavía.")

    plan = cargar_plan_md(ruta)
    progreso = cargar_progreso(ruta)
    meta = db.leer_meta_curso(ruta)
    nombre = str(meta["nombre"]) or f"curso-de-{curso.temario.lenguaje}"
    raiz = slug(nombre, "mi-curso")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_:
        diseno = plan or f"# Curso de {curso.temario.lenguaje}\n"
        zip_.writestr(
            f"{raiz}/00-diseno.md",
            f"{diseno}\n\n---\n\n_Lenguaje: {curso.temario.lenguaje}_\n",
        )
        titulos = [u.titulo for u in curso.temario.unidades]
        for indice, titulo in enumerate(titulos):
            mensajes = db.historial_chat(ruta, f"u{indice}")
            encabezado = f"# Clase {indice + 1}: {titulo}\n\n"
            # Ilustración de la clase (HU-08): se incrusta si existe.
            imagen = dir_curso / "imagenes" / f"unidad-{indice}.png"
            if imagen.exists():
                nombre_png = f"imagenes/unidad-{indice}.png"
                zip_.write(imagen, f"{raiz}/{nombre_png}")
                encabezado += f"![Ilustración de la clase]({nombre_png})\n\n"
            contenido = encabezado + _hitos(progreso, indice) + _transcripcion(mensajes)
            zip_.writestr(f"{raiz}/clase-{indice + 1:02d}-{slug(titulo)}.md", contenido)
        zip_.writestr(f"{raiz}/resultados.md", _resultados_md(progreso, titulos))
    return buffer.getvalue()
