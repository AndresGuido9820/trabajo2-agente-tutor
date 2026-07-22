"""Interfaz de línea de comandos con Rich (HU-06).

La UI solo presenta y lee: la lógica vive en ``Agente`` y las validaciones
en sus módulos. Toda entrada inválida reintenta con mensaje claro.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from tutor.ensenanza.agente import Agente, EstadoUnidad
from tutor.ensenanza.evaluacion import Retroalimentacion, validar_respuesta
from tutor.ensenanza.perfil import FuncionEntrada
from tutor.ensenanza.progreso import Resultado
from tutor.nucleo.errores import ErrorLLM

consola = Console()

_ETIQUETA_ESTADO = {
    EstadoUnidad.BLOQUEADA: "[dim]🔒 bloqueada[/]",
    EstadoUnidad.PENDIENTE: "[dim]pendiente[/]",
    EstadoUnidad.VISTA: "[yellow]vista[/]",
    EstadoUnidad.EVALUADA: "[yellow]evaluada[/]",
    EstadoUnidad.APROBADA: "[green]aprobada ✔[/]",
}


@dataclass(frozen=True)
class Accion:
    """Acción parseada del menú principal.

    ``tipo`` es 'unidad' | 'evaluar' | 'progreso' | 'rehacer' | 'salir';
    ``indice`` acompaña a 'unidad' y 'evaluar'.
    """

    tipo: str
    indice: int | None = None


def parsear_accion(texto: str, num_unidades: int) -> Accion:
    """Parsea la entrada del menú principal.

    Formatos: ``3`` (unidad 3), ``e 3`` (evaluar unidad 3), ``p`` (progreso),
    ``r`` (rehacer perfil), ``q`` (salir).

    Raises:
        ValueError: Si la entrada no corresponde a ninguna acción.
    """
    texto = texto.strip().lower()
    if texto in {"q", "salir"}:
        return Accion("salir")
    if texto in {"p", "progreso"}:
        return Accion("progreso")
    if texto in {"r", "rehacer"}:
        return Accion("rehacer")
    partes = texto.split()
    if len(partes) == 2 and partes[0] == "e" and partes[1].isdigit():
        indice = int(partes[1]) - 1
        if 0 <= indice < num_unidades:
            return Accion("evaluar", indice)
        raise ValueError(f"No existe la unidad {partes[1]}.")
    if texto.isdigit():
        indice = int(texto) - 1
        if 0 <= indice < num_unidades:
            return Accion("unidad", indice)
        raise ValueError(f"No existe la unidad {texto}.")
    raise ValueError(
        "Opciones: número de unidad, 'e <n>' (evaluar), 'p' (progreso), "
        "'r' (rehacer perfil), 'q' (salir)."
    )


def mostrar_menu(agente: Agente) -> None:
    """Imprime el temario con el estado de cada unidad."""
    tabla = Table(title=f"Tu curso de {agente.curso.temario.lenguaje}")
    tabla.add_column("#", justify="right")
    tabla.add_column("Unidad")
    tabla.add_column("Estado")
    tabla.add_column("Mejor nota", justify="right")
    for fila in agente.filas_unidades():
        tabla.add_row(
            str(fila.indice + 1),
            fila.titulo,
            _ETIQUETA_ESTADO[fila.estado],
            "" if fila.mejor_nota is None else f"{fila.mejor_nota}/100",
        )
    consola.print(tabla)
    consola.print(
        "[bold]Opciones:[/] número → entrar a la unidad · e <n> → evaluar · "
        "p → progreso · r → rehacer perfil · q → salir"
    )


def mostrar_leccion(markdown: str) -> None:
    """Renderiza la lección como Markdown."""
    consola.print(Panel(Markdown(markdown), border_style="cyan"))


def mostrar_progreso(agente: Agente) -> None:
    """Tabla de avance: unidad, vista, intentos y mejor nota (HU-05)."""
    tabla = Table(title="Tu progreso")
    tabla.add_column("#", justify="right")
    tabla.add_column("Unidad")
    tabla.add_column("Vista")
    tabla.add_column("Intentos", justify="right")
    tabla.add_column("Mejor nota", justify="right")
    for fila in agente.filas_unidades():
        tabla.add_row(
            str(fila.indice + 1),
            fila.titulo,
            "sí" if fila.indice in agente.progreso.vistas else "no",
            str(agente.progreso.intentos(fila.indice)),
            "" if fila.mejor_nota is None else f"{fila.mejor_nota}/100",
        )
    consola.print(tabla)


def preguntar_respuestas(
    agente: Agente, indice: int, entrada: FuncionEntrada = input
) -> tuple[Resultado, list[Retroalimentacion]] | None:
    """Flujo completo de evaluación de una unidad.

    Genera el quiz, pregunta cada pregunta (reintentando entradas inválidas),
    califica y devuelve el resultado; ``None`` si el quiz no pudo generarse.
    """
    with consola.status("Preparando tu evaluación..."):
        quiz = agente.quiz_de_unidad(indice)
    respuestas = []
    for numero, pregunta in enumerate(quiz.preguntas, start=1):
        consola.print(f"\n[bold]Pregunta {numero}.[/] {pregunta.enunciado}\n")
        for letra, opcion in zip("abcd", pregunta.opciones, strict=True):
            consola.print(f"  {letra}) {opcion}")
        while True:
            try:
                respuestas.append(
                    validar_respuesta(entrada("> "), len(pregunta.opciones))
                )
                break
            except ValueError as error:
                consola.print(f"[red]{error}[/]")
    return agente.calificar_quiz(quiz, respuestas)


def mostrar_resultado(resultado: Resultado, detalle: list[Retroalimentacion]) -> None:
    """Nota final + retroalimentación por pregunta (RF-3.2)."""
    color = (
        "green" if resultado.nota >= 70 else "yellow" if resultado.nota >= 40 else "red"
    )
    consola.print(
        Panel(f"[bold {color}]Nota: {resultado.nota}/100[/]", title="Resultado")
    )
    for numero, r in enumerate(detalle, start=1):
        icono = "✅" if r.acierto else "❌"
        elegida = r.pregunta.opciones[r.respuesta]
        consola.print(f"{icono} [bold]P{numero}[/] — elegiste: {elegida}")
        if not r.acierto:
            correcta = r.pregunta.opciones[r.pregunta.correcta]
            consola.print(f"   Correcta: [green]{correcta}[/]")
        consola.print(f"   [dim]{r.pregunta.explicacion}[/]")
    if resultado.conceptos_fallados:
        consola.print(
            "\n[yellow]Para repasar:[/] "
            + ", ".join(resultado.conceptos_fallados)
            + " — las próximas lecciones los reforzarán."
        )
    else:
        consola.print("\n[green]¡Impecable! Sigue así.[/]")


_NOMBRE_PASO = {
    "gancho": "para qué te sirve",
    "prediccion": "predice",
    "explicacion": "explicación",
    "error_tipico": "error típico",
    "modificacion": "modifícalo",
    "reto": "mini-reto",
    "recap": "en resumen",
}


def bucle_leccion(agente: Agente, indice: int, entrada: FuncionEntrada = input) -> bool:
    """Lección conversada: objetivos + pasos charlados con el tutor (HU-10).

    Returns:
        ``True`` si el estudiante llegó al final de la lección.
    """
    with consola.status("Preparando tu lección..."):
        guion = agente.iniciar_leccion(indice)

    objetivos = "\n".join(f"• {o}" for o in guion.objetivos)
    mapa = " → ".join(_NOMBRE_PASO.get(p.tipo, p.tipo) for p in guion.pasos)
    consola.print(
        Panel(
            f"[bold]Al terminar sabrás:[/]\n{objetivos}\n\n[dim]Ruta: {mapa}[/]",
            title="Objetivos de la lección",
            border_style="cyan",
        )
    )
    consola.print(
        "[dim]Responde para avanzar (Enter = seguir · 'salir' = volver al menú).[/]"
    )

    with consola.status("El tutor está escribiendo..."):
        texto, terminada = agente.turno_leccion(indice, None)
    consola.print(Panel(Markdown(texto), border_style="magenta"))

    while not terminada:
        paso, total = agente.avance_leccion(indice)
        mensaje = entrada(f"(paso {paso}/{total}) > ").strip()
        if mensaje.lower() in {"salir", "menu", "menú"}:
            consola.print("[dim]Lección pausada; puedes retomarla desde el menú.[/]")
            return False
        try:
            with consola.status("El tutor está escribiendo..."):
                texto, terminada = agente.turno_leccion(
                    indice, mensaje or "ok, sigamos"
                )
            consola.print(Panel(Markdown(texto), border_style="magenta"))
        except ErrorLLM as error:
            consola.print(f"[red]{error}[/] Intenta de nuevo o escribe 'salir'.")
    consola.print(
        f"[green]¡Lección completada![/] Cuando quieras, evalúate con "
        f"[bold]e {indice + 1}[/]."
    )
    return True


def bucle_charla(agente: Agente, indice: int, entrada: FuncionEntrada = input) -> None:
    """Charla con el tutor sobre la unidad recién leída (HU-09).

    Enter vacío o 'volver' regresa al menú; un error del LLM no rompe la
    sesión (se informa y se puede seguir preguntando o salir).
    """
    consola.print(
        "\n[bold cyan]💬 ¿Dudas?[/] Pregúntale al tutor sobre esta lección "
        "(Enter o 'volver' para regresar al menú)."
    )
    while True:
        pregunta = entrada("💬 > ").strip()
        if not pregunta or pregunta.lower() == "volver":
            return
        try:
            with consola.status("Pensando..."):
                respuesta = agente.charlar(indice, pregunta)
            consola.print(Panel(Markdown(respuesta), border_style="magenta"))
        except ErrorLLM as error:
            consola.print(f"[red]{error}[/]")


def confirmar(mensaje: str, entrada: FuncionEntrada = input) -> bool:
    """Pregunta sí/no; solo 's' confirma."""
    return entrada(f"{mensaje} [s/N] > ").strip().lower() == "s"


def con_spinner[T](mensaje: str, funcion: Callable[[], T]) -> T:
    """Ejecuta ``funcion`` mostrando un spinner (llamadas al LLM)."""
    with consola.status(mensaje):
        return funcion()
