import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import { Box, Button, Group, Textarea, Code } from '@mantine/core'

// ---- Pyodide: Python en el navegador (estilo futurecoder) ----
let pyodidePromesa = null
function cargarPyodide() {
  if (!pyodidePromesa) {
    pyodidePromesa = new Promise((res, rej) => {
      const s = document.createElement('script')
      s.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js'
      s.onload = () => window.loadPyodide().then(res, rej)
      s.onerror = () => rej(new Error('No se pudo descargar Python (¿sin internet?).'))
      document.head.appendChild(s)
    })
  }
  return pyodidePromesa
}

function Runner({ codigo }) {
  const [texto, setTexto] = useState(codigo)
  const [salida, setSalida] = useState('Edítalo y ejecútalo: corre en TU navegador.')
  const [corriendo, setCorriendo] = useState(false)
  const [esError, setEsError] = useState(false)

  const ejecutar = async () => {
    setCorriendo(true)
    setEsError(false)
    setSalida(pyodidePromesa ? '▶ Ejecutando…' : '⏳ Preparando Python (solo la primera vez, ~10 s)…')
    try {
      const py = await cargarPyodide()
      py.runPython('import sys, io\nsys.stdout = sys.stderr = io.StringIO()')
      let error = null
      try {
        py.runPython(texto)
      } catch (e) {
        error = String(e.message || e)
          .split('\n')
          .filter((l) => !l.includes('pyodide'))
          .slice(-8)
          .join('\n')
      }
      const out = py.runPython('sys.stdout.getvalue()')
      if (error) {
        setEsError(true)
        setSalida((out ? out + '\n' : '') + error)
      } else {
        setSalida(out || '(corrió sin imprimir nada — agrega un print())')
      }
    } catch (e) {
      setEsError(true)
      setSalida(e.message)
    }
    setCorriendo(false)
  }

  return (
    <Box my="xs" p="sm" style={{ background: '#0a0d13', borderRadius: 8, border: '1px solid #2a3444' }}>
      <Textarea
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        autosize
        minRows={4}
        styles={{ input: { fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 13, background: 'transparent', border: 'none' } }}
      />
      <Group gap="xs" mt="xs">
        <Button size="compact-sm" onClick={ejecutar} loading={corriendo}>▶ Ejecutar</Button>
      </Group>
      <Code block mt="xs" c={esError ? 'red.4' : 'cyan.3'} style={{ whiteSpace: 'pre-wrap', background: 'transparent' }}>
        {salida}
      </Code>
    </Box>
  )
}

function BloqueCodigo({ codigo, esPython }) {
  const [abierto, setAbierto] = useState(false)
  const multilinea = codigo.trim().split('\n').length >= 2
  return (
    <Box>
      <Code block style={{ fontSize: 13 }}>{codigo}</Code>
      {esPython && multilinea && (
        <Group gap="xs" mt={4} mb="xs">
          <Button variant="subtle" size="compact-xs" onClick={() => setAbierto(!abierto)}>
            {abierto ? 'Ocultar' : '▶ Pruébalo aquí'}
          </Button>
          <Button
            variant="subtle"
            size="compact-xs"
            onClick={() =>
              window.open(
                'https://pythontutor.com/render.html#code=' +
                  encodeURIComponent(codigo) +
                  '&cumulative=false&py=311&curInstr=0',
                '_blank',
              )
            }
          >
            🔍 Paso a paso
          </Button>
        </Group>
      )}
      {abierto && <Runner codigo={codigo.trimEnd()} />}
    </Box>
  )
}

/** Markdown del tutor con bloques de código ejecutables. */
export default function Prosa({ children, lenguaje }) {
  return (
    <Box className="prosa" style={{ lineHeight: 1.65 }}>
      <Markdown
        components={{
          pre: ({ children: hijos }) => hijos,
          code: ({ inline, className, children: contenido, ...props }) => {
            const texto = String(contenido ?? '')
            if (texto.includes('\n')) {
              return <BloqueCodigo codigo={texto} esPython={lenguaje === 'python'} />
            }
            return <Code {...props}>{texto}</Code>
          },
        }}
      >
        {String(children ?? '')}
      </Markdown>
    </Box>
  )
}
