import { useState } from 'react'
import { Badge, Box, Button, Group, Stack, Text, Textarea } from '@mantine/core'
import { IconBulb, IconCheck, IconCode } from '@tabler/icons-react'
import { api } from './api.js'
import { avisar, avisarError } from './App.jsx'
import { Mensaje } from './Chat.jsx'
import { cargarPyodide } from './Prosa.jsx'

// Guardián contra bucles infinitos (HU-28): un tracer de Python corta la
// ejecución tras N "pasos" (líneas ejecutadas), sin colgar la pestaña.
const GUARDIAN = `
import sys
_pasos = [0]
def _tracer(frame, event, arg):
    _pasos[0] += 1
    if _pasos[0] > 400000:
        raise TimeoutError("se quedó pensando demasiado (¿bucle infinito?)")
    return _tracer
sys.settrace(_tracer)
`

/** Corre el código del estudiante + los tests en Pyodide (navegador). */
async function correrTests(codigo, tests) {
  const py = await cargarPyodide()
  const resultados = []
  for (const t of tests) {
    let veredicto
    try {
      py.runPython('import sys, io\nsys.stdout = io.StringIO()\nsys.settrace(None)')
      py.runPython(GUARDIAN)
      py.runPython(codigo)
      if (t.esperado !== null && t.esperado !== undefined) {
        const obtenido = py.runPython(`repr(${t.llamada})`)
        const ok = comparar(obtenido, t.esperado)
        veredicto = ok
          ? { ok: true, texto: `${t.llamada} devuelve ${t.esperado}` }
          : { ok: false, texto: `${t.llamada} devuelve ${t.esperado} — tu código devolvió ${obtenido}` }
      } else {
        py.runPython(t.llamada)
        const salida = py.runPython('sys.stdout.getvalue()')
        veredicto = salida.includes(t.stdout_contiene)
          ? { ok: true, texto: `la salida contiene "${t.stdout_contiene}"` }
          : { ok: false, texto: `la salida debía contener "${t.stdout_contiene}" y fue: ${salida.slice(0, 120) || '(vacía)'}` }
      }
    } catch (e) {
      const mensaje = String(e.message || e).split('\n').filter((l) => !l.includes('pyodide')).slice(-3).join(' ')
      veredicto = { ok: false, texto: `${t.llamada} — error: ${mensaje}` }
    } finally {
      try { py.runPython('import sys\nsys.settrace(None)') } catch { /* ok */ }
    }
    resultados.push(veredicto)
  }
  return resultados
}

function comparar(obtenido, esperado) {
  if (obtenido === esperado) return true
  // Floats: tolerancia cuando ambos parsean como número.
  const a = Number(obtenido)
  const b = Number(esperado)
  return Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) < 1e-9
}

/** Tarjeta del reto de código (HU-28): editor + tests estilo freeCodeCamp. */
export default function RetoCard({ reto, unidad, onSuperado, onMensaje }) {
  const [codigo, setCodigo] = useState(reto.seed)
  const [resultados, setResultados] = useState(null)
  const [corriendo, setCorriendo] = useState(false)
  const [superado, setSuperado] = useState(false)
  const [pidiendo, setPidiendo] = useState(false)

  const verificar = async () => {
    setCorriendo(true)
    try {
      const r = await correrTests(codigo, reto.tests)
      setResultados(r)
      if (r.every((x) => x.ok) && !superado) {
        setSuperado(true)
        try {
          const respuesta = await api('/api/estudio/reto-superado',
            { unidad, objetivo: reto.objetivo })
          avisar('+10 puntos: ¡reto superado!')
          onSuperado?.(respuesta.texto)
        } catch { /* 409: ya estaba superado, sin doble celebración */ }
      }
    } catch (e) { avisarError(e) }
    setCorriendo(false)
  }

  const pista = async () => {
    const fallado = resultados?.find((r) => !r.ok)
    setPidiendo(true)
    try {
      const r = await api('/api/estudio/pista-reto', {
        unidad, codigo, test_fallado: fallado ? fallado.texto : '(aún no verifica)',
      })
      onMensaje?.(r.texto)
    } catch (e) { avisarError(e) }
    setPidiendo(false)
  }

  return (
    <Mensaje rol="tutor" ancho>
      <Group gap={6} mb={4}>
        <IconCode size={15} stroke={1.8} color="var(--mantine-color-dimmed)" />
        <Text size="xs" c="dimmed" fw={700} lts="0.04em">RETO DE CÓDIGO</Text>
        {superado && <Badge size="xs" color="teal">✓ superado</Badge>}
      </Group>
      <Text size="sm" mb="sm">{reto.enunciado}</Text>
      <Textarea value={codigo} onChange={(e) => setCodigo(e.target.value)}
        autosize minRows={4} maxRows={16} styles={{ input: { fontFamily: 'monospace' } }}
        aria-label="Tu código del reto" />
      {resultados && (
        <Stack gap={4} mt="sm">
          {resultados.map((r, i) => (
            <Text key={i} size="sm" c={r.ok ? 'teal' : 'red.5'} ff="monospace">
              {r.ok ? '✓' : '✗'} {r.texto}
            </Text>
          ))}
        </Stack>
      )}
      <Group gap="xs" mt="sm">
        <Button size="xs" leftSection={<IconCheck size={14} />} onClick={verificar} loading={corriendo}>Verificar</Button>
        <Button size="xs" variant="default" leftSection={<IconBulb size={14} />} onClick={pista} loading={pidiendo}>
          Pista
        </Button>
      </Group>
      <Box mt={6}>
        <Text size="xs" c="dimmed">
          Corre en TU navegador (Python vía Pyodide); los tests son visibles a propósito.
        </Text>
      </Box>
    </Mensaje>
  )
}
