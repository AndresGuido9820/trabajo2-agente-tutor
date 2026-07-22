"""E2E de robustez (HU-34): caída del servidor, "No enviado" y Reintentar.

Flujo: levanta el servidor sobre los datos reales de ``./data``, entra al
primer curso, MATA el servidor, envía un mensaje (debe quedar "No enviado"),
revive el servidor y reintenta (debe llegar la respuesta del tutor).

CUESTA 1 llamada LLM y tarda ~1-2 min: uso manual.
Uso: ``uv run python scripts/e2e_reintento.py``
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

from playwright.sync_api import Page, sync_playwright

PUERTO = 8036
BASE = f"http://127.0.0.1:{PUERTO}"
ESPERA_LLM = 240_000  # ms


def arrancar_servidor() -> subprocess.Popen[bytes]:
    """Levanta el servidor del tutor sobre los datos reales."""
    proceso = subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-c",
            "from dotenv import load_dotenv; load_dotenv();"
            "import uvicorn; from tutor.config import cargar_configuracion;"
            "from tutor.interfaces.web import crear_app;"
            f"uvicorn.run(crear_app(cargar_configuracion()), host='127.0.0.1', "
            f"port={PUERTO}, log_level='warning')",
        ],
        env={**os.environ},
    )
    time.sleep(4)
    return proceso


def recorrer(page: Page) -> None:
    """Caída → No enviado → revivir → Reintentar → respuesta del tutor."""
    page.goto(BASE)
    page.wait_for_selector("text=Mis cursos", timeout=30_000)
    page.click("text=Entrar →")
    page.wait_for_selector("text=Clase", timeout=ESPERA_LLM)
    time.sleep(1)

    print("💥 Matando el servidor…")
    global servidor
    servidor.terminate()
    servidor.wait()

    caja = page.get_by_role("textbox").last
    caja.fill("hola, ¿seguimos donde íbamos?")
    page.keyboard.press("Enter")
    page.wait_for_selector("text=No enviado", timeout=30_000)
    print("✅ Apareció 'No enviado' con el servidor caído")

    print("🔌 Reviviendo el servidor…")
    servidor = arrancar_servidor()

    antes = page.locator(".prosa").count()
    page.click("text=Reintentar")
    page.wait_for_function(
        f"document.querySelectorAll('.prosa').length > {antes}",
        timeout=ESPERA_LLM,
    )
    print("✅ El reintento obtuvo respuesta del tutor")


servidor: subprocess.Popen[bytes]


def main() -> int:
    """Corre el escenario completo."""
    global servidor
    servidor = arrancar_servidor()
    try:
        with sync_playwright() as pw:
            navegador = pw.chromium.launch()
            page = navegador.new_page(viewport={"width": 1440, "height": 900})
            recorrer(page)
            navegador.close()
        print("E2E de reintento: OK ✅")
        return 0
    finally:
        servidor.terminate()


if __name__ == "__main__":
    sys.exit(main())
