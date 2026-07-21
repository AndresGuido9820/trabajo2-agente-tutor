"""Graba el video demo de la app con Playwright (entregable E2, base visual).

Recorre la app como un estudiante real y lo graba a .webm (1600x900) con un
cursor visible inyectado y tipeo natural. Imprime MARCAS de tiempo por
escena (y las guarda en entregables/video/marcas.txt) para editar encima.

CUESTA TOKENS y tarda 10-25 min (espera generaciones reales): uso manual.
Uso: ``uv run python scripts/video_demo.py``
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

# Cursor visible: Playwright no dibuja el mouse; lo inyectamos nosotros.
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
    """Anota el tiempo de inicio de una escena (para editar el video)."""
    t = time.monotonic() - inicio_global
    linea = f"{int(t // 60):02d}:{int(t % 60):02d}  {nombre}"
    marcas.append(linea)
    print(f"🎬 {linea}", flush=True)


def escribir(page: Page, texto: str) -> None:
    """Tipea en el composer con ritmo humano y envía."""
    caja = page.get_by_role("textbox").last
    caja.click()
    caja.fill("")  # nunca heredar texto a medias
    caja.press_sequentially(texto, delay=22)
    time.sleep(0.4)
    page.keyboard.press("Enter")


def esperar(page: Page, n_minimo: int) -> None:
    """Espera ``n_minimo`` burbujas Y que nada esté cargando.

    El propio mensaje del estudiante también es una burbuja `.prosa`, y con
    streaming la respuesta crece en vivo: contar burbujas no basta — hay
    que esperar además a que ningún botón siga en estado loading.
    """
    page.wait_for_function(
        f"() => document.querySelectorAll('.prosa').length >= {n_minimo}"
        " && !document.querySelector('button[data-loading]')",
        timeout=ESPERA_LLM,
    )
    time.sleep(1.2)


def turno(page: Page, texto: str) -> None:
    """Envía un mensaje y espera la respuesta COMPLETA del tutor."""
    n = page.locator(".prosa").count()
    escribir(page, texto)
    esperar(page, n + 2)  # +1 mi burbuja, +1 la del tutor


def pausa(segundos: float = 2.0) -> None:
    """Respiro entre acciones (queda grabado: da ritmo al video)."""
    time.sleep(segundos)


def recorrer(page: Page) -> None:
    """El recorrido completo del demo, escena por escena."""
    # ---- Escena 1: Mis cursos, tema y archivados -------------------------
    marca("E1 · Mis cursos + tema claro/oscuro + archivados")
    page.goto(BASE)
    page.wait_for_selector("text=Mis cursos", timeout=30_000)
    pausa(3)
    page.get_by_label("Cambiar tema claro/oscuro").click()
    pausa(2.5)
    page.get_by_label("Cambiar tema claro/oscuro").click()
    pausa(1)
    page.get_by_label("Cambiar tema claro/oscuro").click()  # vuelve a oscuro
    pausa(1.5)
    if page.locator("text=Archivados").count():
        page.locator("text=Archivados").first.click()
        pausa(2.5)
        page.locator("text=Archivados").first.click()

    # ---- Escena 2: renombrar el curso -----------------------------------
    marca("E2 · Renombrar curso (menú ⋯)")
    page.get_by_label("Opciones del curso").first.click()
    pausa(1)
    page.locator("text=✏️ Renombrar").click()
    caja = page.get_by_role("textbox").last
    caja.click()
    page.keyboard.press("Meta+a")
    caja.press_sequentially("Ventas con Python 📊", delay=35)
    pausa(0.8)
    page.locator("text=Guardar").click()
    pausa(2.5)

    # ---- Escena 3: crear un curso NUEVO conversando (perfil distinto) ----
    marca("E3 · Nuevo curso: diseño conversacional (perfil web/JS)")
    page.click("text=Nuevo curso")
    page.wait_for_selector("text=¿Qué quieres aprender?", timeout=15_000)
    pausa(2)
    # Diálogo de creación: responder y confirmar turno a turno hasta que la
    # vista cambie a la clase — la ÚNICA señal fiable de que el asesor creó
    # el curso (sus mensajes usan listas tanto para preguntar como para
    # proponer: el texto no sirve como detector).
    mensajes_creacion = [
        "Quiero aprender a hacer páginas web desde cero, nunca he programado",
        "Nunca he programado; tengo 4 horas a la semana; mi meta es mi "
        "página personal; elige tú las tecnologías",
        "Sí, es correcto: proponme el plan",
        "Me encanta la propuesta: ya, dale, arranca",
        "Sí, confirmo: crea el curso ya, tal como está",
        "ya, dale",
    ]
    en_clase = "document.body.innerText.includes('Clase 1:')"
    for mensaje in mensajes_creacion:
        if page.evaluate(f"() => {en_clase}"):
            break
        n = page.locator(".prosa").count()
        escribir(page, mensaje)
        # Espera la respuesta O el salto a la clase (crear tarda ~1-2 min).
        page.wait_for_function(
            f"() => (document.querySelectorAll('.prosa').length >= {n + 2}"
            f" && !document.querySelector('button[data-loading]')) || {en_clase}",
            timeout=ESPERA_LLM,
        )
        pausa(2)
    page.wait_for_selector("text=Clase 1:", timeout=ESPERA_LLM)
    esperar(page, 1)  # la apertura del tutor
    marca("E3b · Clase 1 del curso nuevo: panel de objetivos + apertura")
    pausa(4)
    turno(page, "creo que esa línea muestra un texto en la página, ¿no?")
    pausa(3)

    # ---- Escena 4: curso de ventas — historial + repaso regenera v2 ------
    marca("E4 · Curso de ventas: historial persistente + repasar")
    page.click("text=← Mis cursos")
    page.wait_for_selector("text=Ventas con Python", timeout=15_000)
    pausa(1.5)
    tarjeta = page.locator(".mantine-Card-root", has_text="Ventas con Python")
    tarjeta.locator("text=Entrar →").click()
    page.wait_for_selector("text=Clase 1", timeout=30_000)
    pausa(3)
    page.mouse.wheel(0, -1200)  # mostrar que el historial persiste
    pausa(2)
    page.mouse.wheel(0, 2400)
    pausa(1.5)
    n = page.locator(".prosa").count()
    page.locator("text=↩ Repasar desde el inicio").click()
    esperar(page, n + 2)
    pausa(3)

    # ---- Escena 5: conversar hasta el mini-quiz (y el reto si sale) ------
    marca("E5 · Lección por objetivos: streaming + mini-quiz")
    respuestas = [
        "mi predicción: creo que imprime el total de la venta, algo como 300",
        "listo, lo probé y me dio justo eso; tiene sentido",
        "mi intento: total = precio * cantidad y luego print(total)",
        "lo modifiqué como pediste y corre bien",
        "entendido, la asignación reemplaza el valor; sigamos",
        "creo que la respuesta es que guarda 25 en la variable",
    ]
    for intento in range(10):
        if page.locator("text=MINI-QUIZ").count():
            break
        turno(page, respuestas[intento % len(respuestas)])
        pausa(1)
    if page.locator("text=MINI-QUIZ").count():
        marca("E5b · Mini-quiz de cierre de objetivo")
        page.locator("text=MINI-QUIZ").last.scroll_into_view_if_needed()
        pausa(2)
        for grupo in page.locator("[role=radiogroup]").all():
            grupo.locator("input[type=radio]").first.check(force=True)
            pausa(0.8)
        page.locator("text=Calificar").last.click()
        page.wait_for_selector(
            "text=/Objetivo cumplido|Objetivo visto|reintentar/", timeout=ESPERA_LLM
        )
        pausa(3)
    if page.locator("text=RETO DE CÓDIGO").count():
        marca("E5c · Reto de código: verificar + pista socrática")
        page.locator("text=RETO DE CÓDIGO").last.scroll_into_view_if_needed()
        pausa(2)
        page.locator("text=✓ Verificar").last.click()
        pausa(14)  # Pyodide carga la primera vez
        n = page.locator(".prosa").count()
        page.locator("text=💡 Pista").last.click()
        esperar(page, n + 1)
        pausa(3)

    # ---- Escena 6: demo interactiva ✨ ------------------------------------
    marca("E6 · Demo interactiva ✨ (artefacto verificado)")
    n = page.locator(".prosa").count()
    page.get_by_label("Pedir una demo interactiva de esta clase").click()
    page.wait_for_selector("iframe[title*='Demo']", timeout=ESPERA_LLM)
    page.locator("iframe[title*='Demo']").last.scroll_into_view_if_needed()
    pausa(6)

    # ---- Escena 7: buscador global ⌘K -------------------------------------
    marca("E7 · Buscador global ⌘K")
    page.keyboard.press("Meta+k")
    pausa(1.2)
    page.keyboard.type("ventas", delay=60)
    pausa(2.5)
    resultados = page.locator("[data-spotlight-action]")
    if resultados.count():
        resultados.first.click()
        pausa(4)
    else:
        page.keyboard.press("Escape")

    # ---- Escena 8: Mi progreso + Repaso del día ---------------------------
    marca("E8 · Mi progreso (estadísticas)")
    page.click("text=Mi progreso")
    page.wait_for_selector("text=clases aprobadas", timeout=15_000)
    pausa(4)
    page.mouse.wheel(0, 600)
    pausa(3)
    marca("E8b · Repaso del día (repetición espaciada)")
    page.click("text=Repaso del día")
    page.wait_for_selector("text=Repaso del día", timeout=15_000)
    pausa(4)

    # ---- Escena 9: evaluación final ---------------------------------------
    marca("E9 · Evaluación final (niveles Bloom + nota ponderada)")
    page.locator("text=Clase 1:").first.click()
    page.wait_for_selector("text=🎯 Evaluarme", timeout=15_000)
    pausa(1.5)
    page.locator("text=🎯 Evaluarme").click()
    page.wait_for_selector("text=PREGUNTA 1 DE", timeout=ESPERA_LLM)
    page.locator("text=PREGUNTA 1 DE").first.scroll_into_view_if_needed()
    pausa(3)
    for grupo in page.locator("[role=radiogroup]").all():
        grupo.locator("input[type=radio]").first.check(force=True)
        pausa(0.6)
    page.locator("text=Calificar").last.click()
    page.wait_for_selector("text=/Aprobada|cerremos esas brechas/", timeout=ESPERA_LLM)
    page.locator(
        "text=/Aprobada|cerremos esas brechas/"
    ).first.scroll_into_view_if_needed()
    pausa(4)
    page.mouse.wheel(0, 500)
    pausa(3)

    # ---- Escena 10: exportar el curso -------------------------------------
    marca("E10 · Exportar el curso (.zip) y cierre")
    page.click("text=← Mis cursos")
    page.wait_for_selector("text=Ventas con Python", timeout=15_000)
    pausa(1.5)
    page.get_by_label("Opciones del curso").first.click()
    pausa(1.5)
    with page.expect_download() as descarga:
        page.locator("text=⬇️ Exportar (.zip)").click()
    print(f"   zip descargado: {descarga.value.suggested_filename}", flush=True)
    pausa(3)
    marca("FIN")


def main() -> int:
    """Graba el recorrido y guarda video + marcas de tiempo."""
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
                destino = DESTINO / "demo-playwright.webm"
                origen.replace(destino)
                print(
                    f"\n🎥 Video: {destino} ({destino.stat().st_size // 1_000_000} MB)"
                )
            (DESTINO / "marcas.txt").write_text("\n".join(marcas) + "\n")
            print(f"⏱️ Marcas: {DESTINO / 'marcas.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
