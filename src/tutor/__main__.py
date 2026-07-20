"""Punto de entrada de la CLI: ``uv run tutor``."""

from __future__ import annotations

import sys

from rich.console import Console

from tutor.config import cargar_configuracion
from tutor.errores import ErrorTutor


def main() -> int:
    """Arranca el tutor y traduce errores conocidos a mensajes limpios."""
    consola = Console()
    try:
        configuracion = cargar_configuracion()
        consola.print(
            "[bold green]Tutor de programación listo.[/] "
            f"Modelo: {configuracion.modelo}. "
            "(El flujo interactivo llega en HU-06.)"
        )
        return 0
    except ErrorTutor as error:
        consola.print(f"[bold red]Error:[/] {error}")
        return 1
    except KeyboardInterrupt:
        consola.print("\nHasta la próxima.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
