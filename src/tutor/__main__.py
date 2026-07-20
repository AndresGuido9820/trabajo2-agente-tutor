"""Punto de entrada de la CLI: ``uv run tutor`` (HU-06)."""

from __future__ import annotations

import logging
import sys

from tutor import ui
from tutor.agente import ARCHIVO_PERFIL, Agente, perfil_o_none
from tutor.config import cargar_configuracion
from tutor.errores import ErrorTutor
from tutor.llm import ClienteOpenAI
from tutor.perfil import guardar_perfil, preguntar_perfil


def _preparar_agente() -> Agente:
    """Carga configuración y perfil (preguntándolo si falta) y arma la sesión."""
    configuracion = cargar_configuracion()
    perfil = perfil_o_none(configuracion.dir_datos)
    if perfil is None:
        perfil = preguntar_perfil()
        guardar_perfil(perfil, configuracion.dir_datos / ARCHIVO_PERFIL)
    return Agente(
        cliente=ClienteOpenAI(configuracion),
        dir_datos=configuracion.dir_datos,
        perfil=perfil,
    )


def _bucle_principal(agente: Agente) -> None:
    """Menú principal: navegar unidades, evaluar, ver progreso (RF-3)."""
    if not agente.curso_ya_generado():
        ui.consola.print("Voy a diseñar tu curso a la medida, dame un momento...")
    temario = ui.con_spinner("Preparando el curso...", lambda: agente.curso)
    while True:
        ui.consola.print()
        ui.mostrar_menu(agente)
        try:
            accion = ui.parsear_accion(input("> "), len(temario.temario.unidades))
        except ValueError as error:
            ui.consola.print(f"[red]{error}[/]")
            continue
        if accion.tipo == "salir":
            ui.consola.print("¡Hasta la próxima! Tu progreso quedó guardado.")
            return
        try:
            if accion.tipo == "progreso":
                ui.mostrar_progreso(agente)
            elif accion.tipo == "unidad":
                assert accion.indice is not None
                ui.bucle_leccion(agente, accion.indice)
            elif accion.tipo == "evaluar":
                assert accion.indice is not None
                calificacion = ui.preguntar_respuestas(agente, accion.indice)
                if calificacion is not None:
                    ui.mostrar_resultado(*calificacion)
            elif accion.tipo == "rehacer" and ui.confirmar(
                "Esto rehace tu perfil y regenera el curso "
                "(el progreso se conserva). ¿Seguro?"
            ):
                agente.rehacer_perfil(preguntar_perfil())
        except ErrorTutor as error:
            # Candados y fallas del LLM no tumban la sesión: se informa y
            # se vuelve al menú (el progreso ya está persistido).
            ui.consola.print(f"[red]{error}[/]")


def main() -> int:
    """Arranca el tutor y traduce errores conocidos a mensajes limpios."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    try:
        agente = _preparar_agente()
        _bucle_principal(agente)
        return 0
    except ErrorTutor as error:
        ui.consola.print(f"[bold red]Error:[/] {error}")
        return 1
    except (KeyboardInterrupt, EOFError):
        ui.consola.print("\nHasta la próxima. Tu progreso quedó guardado.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
