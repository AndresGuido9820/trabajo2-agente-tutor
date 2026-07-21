// Cliente mínimo del API del tutor (mismos endpoints de siempre).
export async function api(ruta, cuerpo, metodo) {
  const m = metodo || (cuerpo !== undefined ? 'POST' : 'GET')
  const opciones =
    m === 'GET'
      ? {}
      : {
          method: m,
          headers: { 'Content-Type': 'application/json' },
          body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
        }
  const r = await fetch(ruta, opciones)
  if (!r.ok) {
    const datos = await r.json().catch(() => ({}))
    throw new Error(datos.detail || `Error ${r.status}`)
  }
  return r.json()
}
