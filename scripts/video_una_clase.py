"""Video demo: el arco COMPLETO de una clase, de 0 % a evaluación aprobada.

Graba una sola clase de principio a fin: panel con los objetivos en cero,
la conversación avanzando (streaming), mini-quiz al cerrar cada objetivo
(el panel se marca en vivo), reto de código, demo interactiva, y al cumplir
todo, la evaluación final que se desbloquea y se presenta.

Correr el servidor con ``TUTOR_MODEL_CHAT=gpt-5-nano`` para turnos rápidos.
Uso: ``uv run python scripts/video_una_clase.py``
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = "http://127.0.0.1:8017"
DESTINO = Path("entregables/video")
ESPERA_LLM = 300_000  # ms
TAMANO = {"width": 1600, "height": 900}
MAX_TURNOS = 45

CURSOR_JS = """
window.addEventListener('DOMContentLoaded', () => {
  const c = document.createElement('div');
  c.style.cssText = 'position:fixed;z-index:99999;width:22px;height:22px;' +
    'border-radius:50%;background:rgba(80,100,255,.45);border:2px solid ' +
    'rgba(80,100,255,.9);pointer-events:none;transform:translate(-50%,-50%);' +
    'transition:width .12s,height .12s;top:0;left:0';
  document.body.appendChild(c);
  document.addEventListener('mousemove', (e) => {
    c.style.top = e.clientY + 'px'; c.style.left = e.clientX + 'px';
  }, true);
  document.addEventListener('mousedown', () => {
    c.style.width = '34px'; c.style.height = '34px';
  }, true);
  document.addEventListener('mouseup', () => {
    c.style.width = '22px'; c.style.height = '22px';
  }, true);
});
"""

inicio_global = time.monotonic()
marcas: list[str] = []


def marca(nombre: str) -> None:
    """Anota el tiempo de inicio de un hito (para editar el video)."""
    t = time.monotonic() - inicio_global
    linea = f"{int(t // 60):02d}:{int(t % 60):02d}  {nombre}"
    marcas.append(linea)
    print(f"🎬 {linea}", flush=True)


def escribir(page: Page, texto: str) -> None:
    """Tipea en el composer con ritmo humano y envía."""
    caja = page.get_by_role("textbox").last
    caja.click()
    caja.fill("")
    caja.press_sequentially(texto, delay=18)
    time.sleep(0.3)
    page.keyboard.press("Enter")


def esperar(page: Page, n_minimo: int) -> None:
    """Espera ``n_minimo`` burbujas Y que nada esté cargando."""
    page.wait_for_function(
        f"() => document.querySelectorAll('.prosa').length >= {n_minimo}"
        " && !document.querySelector('button[data-loading]')",
        timeout=ESPERA_LLM,
    )
    time.sleep(0.8)


def turno(page: Page, texto: str) -> None:
    """Envía un mensaje y espera la respuesta COMPLETA del tutor."""
    n = page.locator(".prosa").count()
    escribir(page, texto)
    esperar(page, n + 2)


RESPUESTAS = [
    "mi predicción: creo que imprime el total de la venta, algo como 300",
    "listo, lo probé y me dio justo eso; tiene sentido",
    "mi intento: total = precio * cantidad y luego print(total)",
    "lo modifiqué como pediste y ya corre bien",
    "entendido: la asignación reemplaza el valor anterior; sigamos",
    "creo que la variable queda con el valor nuevo, 25",
    "sería un str, porque va entre comillas",
    "para mi negocio usaría precio por cantidad, como en Excel",
]


def quiz_sin_responder(page: Page):
    """La tarjeta de mini-quiz que aún tiene botón Calificar, o None."""
    tarjetas = page.locator(".mantine-Paper-root", has_text="MINI-QUIZ").filter(
        has=page.locator("button", has_text="Calificar")
    )
    return tarjetas.last if tarjetas.count() else None


def responder_mini_quiz(page: Page, tarjeta) -> None:
    """Responde un mini-quiz pendiente (primera opción de cada pregunta)."""
    tarjeta.scroll_into_view_if_needed()
    time.sleep(1.5)
    for grupo in tarjeta.locator("[role=radiogroup]").all():
        grupo.locator("input[type=radio]").first.check(force=True)
        time.sleep(0.6)
    n = page.locator(".prosa").count()
    tarjeta.locator("button", has_text="Calificar").click()
    page.wait_for_function(
        f"() => document.querySelectorAll('.prosa').length >= {n + 1}"
        " && !document.querySelector('button[data-loading]')",
        timeout=ESPERA_LLM,
    )
    time.sleep(1.5)


def manejar_reto(page: Page) -> None:
    """Verifica el reto con el seed (falla a propósito) y pide la pista."""
    tarjeta = page.locator(".mantine-Paper-root", has_text="RETO DE CÓDIGO").last
    tarjeta.scroll_into_view_if_needed()
    time.sleep(1.5)
    tarjeta.locator("text=✓ Verificar").click()
    time.sleep(12)  # Pyodide carga la primera vez
    n = page.locator(".prosa").count()
    tarjeta.locator("text=💡 Pista").click()
    esperar(page, n + 1)
    time.sleep(1.5)


def recorrer(page: Page) -> None:
    """Una clase completa: 0 % → objetivos → evaluación aprobable."""
    marca("V1 · Entrar al curso y a la clase 1 (panel en cero)")
    page.goto(BASE)
    page.wait_for_selector("text=Ventas con Python", timeout=30_000)
    time.sleep(2)
    tarjeta = page.locator(".mantine-Card-root", has_text="Ventas con Python")
    tarjeta.locator("text=Entrar →").click()
    page.wait_for_selector("text=Clase 1:", timeout=30_000)
    esperar(page, 1)  # apertura del tutor (guion ya cacheado: rápido)
    time.sleep(3)

    marca("V2 · La clase conversada: objetivos marcándose en vivo")
    quizzes, retos, demo_hecha = 0, 0, False
    for intento in range(MAX_TURNOS):
        if page.locator("text=¡Clase completada!").count():
            break
        pendiente = quiz_sin_responder(page)
        if pendiente is not None:
            quizzes += 1
            marca(f"V2.{quizzes} · Mini-quiz (intento/objetivo {quizzes})")
            responder_mini_quiz(page, pendiente)
            if page.locator("text=¡Clase completada!").count():
                break
            # Tras el primer quiz, mostrar la demo interactiva una vez.
            if not demo_hecha and quiz_sin_responder(page) is None:
                marca("V3 · Demo interactiva ✨ del objetivo")
                page.get_by_label(
                    "Pedir una demo interactiva de esta clase"
                ).click()
                page.wait_for_selector("iframe[title*='Demo']", timeout=ESPERA_LLM)
                page.locator("iframe[title*='Demo']").last.scroll_into_view_if_needed()
                time.sleep(6)
                demo_hecha = True
            continue
        n_retos = page.locator(
            ".mantine-Paper-root", has_text="RETO DE CÓDIGO"
        ).count()
        if n_retos > retos:
            marca("V2r · Reto de código (verificar + pista)")
            manejar_reto(page)
            retos = n_retos
            # seguir la conversación después del reto
        turno(page, RESPUESTAS[intento % len(RESPUESTAS)])
        time.sleep(0.5)

    marca("V4 · Clase completada: el panel al 100 % desbloquea la evaluación")
    page.locator("text=¡Clase completada!").last.scroll_into_view_if_needed()
    time.sleep(3)

    marca("V5 · Evaluación final (niveles Bloom, nota ponderada)")
    page.locator("text=🎯 Evaluación final").click()
    page.wait_for_selector("text=PREGUNTA 1 DE", timeout=ESPERA_LLM)
    page.locator("text=PREGUNTA 1 DE").first.scroll_into_view_if_needed()
    time.sleep(2.5)
    for grupo in page.locator(
        ".mantine-Paper-root", has_text="EVALUACIÓN"
    ).last.locator("[role=radiogroup]").all():
        grupo.locator("input[type=radio]").first.check(force=True)
        time.sleep(0.5)
    page.locator("text=Calificar").last.click()
    page.wait_for_selector("text=/Aprobada|cerremos esas brechas/", timeout=ESPERA_LLM)
    page.locator(
        "text=/Aprobada|cerremos esas brechas/"
    ).first.scroll_into_view_if_needed()
    time.sleep(4)
    page.mouse.wheel(0, 500)
    time.sleep(3)

    marca("V6 · Mi progreso: lo que dejó la clase")
    page.click("text=Mi progreso")
    page.wait_for_selector("text=clases aprobadas", timeout=15_000)
    time.sleep(4)
    page.mouse.wheel(0, 600)
    time.sleep(3)
    marca("FIN")


def main() -> int:
    """Graba el arco completo de una clase y guarda video + marcas."""
    DESTINO.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        contexto = navegador.new_context(
            viewport=TAMANO, record_video_dir=str(DESTINO), record_video_size=TAMANO
        )
        page = contexto.new_page()
        page.add_init_script(CURSOR_JS)
        try:
            recorrer(page)
        finally:
            video = page.video
            contexto.close()
            navegador.close()
            if video:
                origen = Path(video.path())
                destino = DESTINO / "demo-una-clase.webm"
                origen.replace(destino)
                print(f"\n🎥 Video: {destino} ({destino.stat().st_size // 1_000_000} MB)")
            (DESTINO / "marcas-una-clase.txt").write_text("\n".join(marcas) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
