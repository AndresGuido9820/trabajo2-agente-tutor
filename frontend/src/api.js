// Cliente mínimo del API del tutor (mismos endpoints de siempre).
export async function api(ruta, cuerpo, metodo) {
  const usarPost = metodo === 'POST' || cuerpo !== undefined
  const opciones = usarPost
    ? {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo ?? {}),
      }
    : {}
  const r = await fetch(ruta, opciones)
  if (!r.ok) {
    const datos = await r.json().catch(() => ({}))
    throw new Error(datos.detail || `Error ${r.status}`)
  }
  return r.json()
}
