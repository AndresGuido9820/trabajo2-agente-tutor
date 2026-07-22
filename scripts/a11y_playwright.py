"""Auditoría de accesibilidad con axe-core sobre las vistas principales (HU-38).

Levanta el servidor sobre los datos reales de ``./data``, inyecta axe-core
(vendorizado del paquete npm ``axe-core``) y falla si hay violaciones
serias o críticas en: Mis cursos, Clase y Mi progreso.

No cuesta tokens (solo navega, no conversa). Uso:
``uv run python scripts/a11y_playwright.py``
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

PUERTO = 8037
BASE = f"http://127.0.0.1:{PUERTO}"
AXE_JS = Path("frontend/node_modules/axe-core/axe.min.js")
SEVERAS = {"serious", "critical"}


def auditar(page: Page, nombre: str) -> list[dict]:
    """Corre axe en la página actual y devuelve las violaciones severas."""
    page.add_script_tag(path=str(AXE_JS))
    resultado = page.evaluate("async () => await axe.run()")
    severas = [v for v in resultado["violations"] if v["impact"] in SEVERAS]
    estado = "❌" if severas else "✅"
    print(f"{estado} {nombre}: {len(severas)} violaciones serias/críticas")
    for v in severas:
        objetivos = [n["target"] for n in v["nodes"][:3]]
        print(f"   - [{v['impact']}] {v['id']}: {v['help']} → {objetivos}")
    return severas


def recorrer(page: Page) -> list[dict]:
    """Audita Mis cursos, Clase y Mi progreso."""
    fallas: list[dict] = []
    page.goto(BASE)
    # Selector de perfiles (HU-42): auditarlo y entrar con el primero.
    page.wait_for_selector("text=¿Quién estudia hoy?", timeout=30_000)
    fallas += auditar(page, "Selector de perfiles")
    page.locator(".mantine-Card-root").first.click()
    page.wait_for_selector("text=Nuevo curso", timeout=30_000)
    fallas += auditar(page, "Mis cursos")

    page.click("text=Entrar →")
    page.wait_for_selector("text=Clase", timeout=60_000)
    time.sleep(1.5)
    fallas += auditar(page, "Clase (chat)")

    page.click("text=Mi progreso")
    page.wait_for_selector("text=clases aprobadas", timeout=30_000)
    fallas += auditar(page, "Mi progreso")
    return fallas


def main() -> int:
    """Levanta el servidor, audita y devuelve 1 si hay violaciones severas."""
    if not AXE_JS.exists():
        print("Falta axe-core: corre `npm install -D axe-core` en frontend/")
        return 2
    servidor = subprocess.Popen(
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
    try:
        with sync_playwright() as pw:
            navegador = pw.chromium.launch()
            page = navegador.new_page(viewport={"width": 1440, "height": 900})
            fallas = recorrer(page)
            navegador.close()
        if fallas:
            print(f"\nAuditoría a11y: {len(fallas)} violaciones severas ❌")
            return 1
        print("\nAuditoría a11y: 0 violaciones serias/críticas ✅")
        return 0
    finally:
        servidor.terminate()


if __name__ == "__main__":
    sys.exit(main())
