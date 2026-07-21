"""Bot Playwright: recorre la app como un estudiante y toma capturas.

Levanta un servidor con datos limpios, crea un curso conversando, estudia,
evalúa y captura cada pantalla en ``entregables/capturas/`` (las usa el
reporte). CUESTA TOKENS y tarda varios minutos: uso manual.

Uso: ``uv run python scripts/capturas_playwright.py``
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

PUERTO = 8019
BASE = f"http://127.0.0.1:{PUERTO}"
DESTINO = Path("entregables/capturas")
ESPERA_LLM = 240_000  # ms: generaciones largas (guías, quizzes)

PROMPT_CURSO = (
    "Hazme un curso de Python para analizar las ventas de mi negocio; manejo bien Excel"
)


def foto(page: Page, nombre: str) -> None:
    """Captura la pantalla completa con un nombre estable."""
    ruta = DESTINO / f"{nombre}.png"
    page.screenshot(path=ruta, full_page=False)
    print(f"📸 {ruta}")


def esperar_tutor(page: Page, n_esperados: int) -> None:
    """Espera a que haya al menos ``n_esperados`` mensajes del tutor."""
    page.wait_for_function(
        f"document.querySelectorAll('.prosa').length >= {n_esperados}",
        timeout=ESPERA_LLM,
    )
    time.sleep(0.6)  # deja asentar el render


def enviar(page: Page, texto: str) -> None:
    """Escribe en el composer y envía."""
    page.get_by_role("textbox").last.fill(texto)
    page.keyboard.press("Enter")


def recorrer(page: Page) -> None:
    """El recorrido completo del estudiante, con captura por pantalla."""
    page.goto(BASE)
    page.wait_for_selector("text=Mis cursos", timeout=30_000)
    foto(page, "01-mis-cursos")

    # Crear curso conversando
    page.click("text=Nuevo curso")
    page.wait_for_selector("text=¿Qué quieres aprender?", timeout=15_000)
    foto(page, "02-nuevo-curso")
    enviar(page, PROMPT_CURSO)
    esperar_tutor(page, 1)
    foto(page, "03-asesor-pregunta")
    enviar(page, "Mi nivel es básico; sé fórmulas y tablas dinámicas de Excel")
    esperar_tutor(page, 2)
    foto(page, "04-asesor-propone")
    enviar(page, "Me gusta la propuesta: ya, dale, arranca")
    # Al confirmar: genera temario y entra a la clase 1 (lección ~1 min)
    page.wait_for_selector("text=Clase 1", timeout=ESPERA_LLM)
    esperar_tutor(page, 1)
    foto(page, "05-clase-1-arranca")

    # Responder la predicción (mal a propósito: el tutor corrige)
    enviar(page, "creo que imprime 12")
    esperar_tutor(page, 2)
    foto(page, "06-tutor-corrige-y-avanza")

    # Completar la lección respondiendo como un estudiante real (el tutor
    # NO avanza ante respuestas vacías: hay que atender cada paso).
    respuestas = [
        "mi predicción: creo que imprime el total de la venta, algo como 300",
        "ya lo probé en mi compu y funcionó, me dio el resultado",
        "mi intento: total = precio * cantidad y luego print(total)",
        "listo, lo modifiqué como pediste y corre bien",
        "sí, entendido; sigamos con lo que viene",
    ]
    boton_evaluar = page.locator("text=Presentar la evaluación")
    for intento in range(14):
        if boton_evaluar.count():
            break
        n = page.locator(".prosa").count()
        enviar(page, respuestas[intento % len(respuestas)])
        page.wait_for_function(
            f"document.querySelectorAll('.prosa').length >= {n + 1}",
            timeout=ESPERA_LLM,
        )
        time.sleep(0.5)
    foto(page, "07-clase-completada")

    # Evaluación dentro del chat (tolerante: si algo falla, seguimos con el
    # resto de capturas)
    try:
        boton_evaluar.first.click(timeout=10_000)
        page.wait_for_selector("text=EVALUACIÓN", timeout=ESPERA_LLM)
        foto(page, "08-evaluacion")
        for grupo in page.locator("[role=radiogroup]").all():
            grupo.locator("input[type=radio]").first.check(force=True)
        page.click("text=Calificar")
        page.wait_for_selector("text=/Aprobada|cerremos esas brechas/", timeout=90_000)
        foto(page, "09-resultado")
    except Exception as error:
        print(f"⚠️ Se omitió la evaluación: {error}")

    # Diseño del curso (documento estructurado)
    page.click("text=Diseño del curso")
    page.wait_for_selector("text=Editar estructura", timeout=15_000)
    time.sleep(0.8)
    foto(page, "10-diseno-documento")
    page.click("text=Editar estructura")
    page.wait_for_selector("text=CLASE 1", timeout=15_000)
    foto(page, "11-diseno-editor-estructurado")

    # Mis cursos con el curso creado y su progreso
    page.click("text=← Mis cursos")
    page.wait_for_selector("text=Entrar", timeout=15_000)
    foto(page, "12-mis-cursos-con-progreso")


def main() -> int:
    """Levanta servidor limpio, recorre y captura."""
    DESTINO.mkdir(parents=True, exist_ok=True)
    datos = tempfile.mkdtemp(prefix="tutor-capturas-")
    entorno = {**os.environ, "TUTOR_DATA_DIR": datos}
    servidor = subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-c",
            "from dotenv import load_dotenv; load_dotenv();"
            "import uvicorn; from tutor.config import cargar_configuracion;"
            "from tutor.web import crear_app;"
            f"uvicorn.run(crear_app(cargar_configuracion()), host='127.0.0.1', "
            f"port={PUERTO}, log_level='warning')",
        ],
        env=entorno,
    )
    time.sleep(4)
    try:
        with sync_playwright() as pw:
            navegador = pw.chromium.launch()
            page = navegador.new_page(viewport={"width": 1440, "height": 900})
            recorrer(page)
            navegador.close()
        print("Capturas completas ✅")
        return 0
    finally:
        servidor.terminate()


if __name__ == "__main__":
    sys.exit(main())
