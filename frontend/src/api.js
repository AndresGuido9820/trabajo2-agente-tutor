// Cliente del API del tutor con clasificación de errores y timeout (HU-34).

// El peor caso legítimo es la creación del curso con listo=true: hasta 3
// llamadas LLM seguidas (perfil + temario + plan) ≈ 4-5 min. El timeout
// local debe superar eso o aborta operaciones que iban bien (visto en la
// grabación del demo: el server terminaba y el navegador ya había cortado).
export const TIMEOUT_FETCH_MS = 6 * 60 * 1000

export class ErrorRed extends Error {
  constructor() {
    super('Sin conexión con el tutor')
    this.esRed = true
  }
}

export async function api(ruta, cuerpo, metodo) {
  const m = metodo || (cuerpo !== undefined ? 'POST' : 'GET')
  const control = new AbortController()
  const temporizador = setTimeout(() => control.abort(), TIMEOUT_FETCH_MS)
  const opciones = {
    signal: control.signal,
    ...(m === 'GET'
      ? {}
      : {
          method: m,
          headers: { 'Content-Type': 'application/json' },
          body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
        }),
  }
  let r
  try {
    r = await fetch(ruta, opciones)
  } catch (e) {
    // TypeError = red caída; AbortError = timeout local. Ambos reintentables.
    window.dispatchEvent(new Event('tutor:red'))
    throw new ErrorRed()
  } finally {
    clearTimeout(temporizador)
  }
  if (!r.ok) {
    const datos = await r.json().catch(() => ({}))
    const error = new Error(datos.detail || `Error ${r.status}`)
    error.status = r.status
    throw error
  }
  return r.json()
}

/**
 * POST con respuesta SSE (HU-35): invoca callbacks.delta/fin/error por evento.
 * Lanza si el stream no se puede abrir (el llamador hace fallback al clásico).
 */
export async function apiStream(ruta, cuerpo, callbacks) {
  const r = await fetch(ruta, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  })
  if (!r.ok || !r.body) throw new Error(`Stream no disponible (${r.status})`)
  const lector = r.body.getReader()
  const decodificador = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await lector.read()
    if (done) break
    buffer += decodificador.decode(value, { stream: true })
    let corte
    while ((corte = buffer.indexOf('\n\n')) >= 0) {
      const marco = buffer.slice(0, corte)
      buffer = buffer.slice(corte + 2)
      const evento = /^event: (.+)$/m.exec(marco)?.[1]
      const datos = JSON.parse(/^data: (.+)$/m.exec(marco)?.[1] ?? '{}')
      callbacks[evento]?.(datos)
    }
  }
}

// Borradores del composer por canal (best-effort: localStorage puede fallar).
export function leerBorrador(canal) {
  try {
    return localStorage.getItem(`borrador:${canal}`) || ''
  } catch {
    return ''
  }
}

export function guardarBorrador(canal, texto) {
  try {
    if (texto) localStorage.setItem(`borrador:${canal}`, texto)
    else localStorage.removeItem(`borrador:${canal}`)
  } catch {
    // lleno o bloqueado: se ignora, es solo una comodidad
  }
}
