import { useEffect, useState } from 'react'
import {
  Box, Button, Chip, Container, Group, Stack, Text, Textarea, ThemeIcon, Title,
} from '@mantine/core'
import { api, guardarBorrador, leerBorrador } from './api.js'
import { avisarError } from './App.jsx'
import { Escribiendo, Mensaje, ZonaChat } from './Chat.jsx'
import { QuizCard } from './Clase.jsx'

const EJEMPLOS = [
  'Hazme un curso de Python para analizar las ventas de mi negocio; manejo bien Excel',
  'Quiero aprender a hacer páginas web desde cero, nunca he programado',
]

/** Conversación de diseño del curso: pregunta, propone y crea al confirmar. */
export default function CreacionChat({ onCreado }) {
  const [mensajes, setMensajes] = useState([])
  const [texto, setTexto] = useState(() => leerBorrador('creacion'))
  const [ocupado, setOcupado] = useState(false)
  const [creando, setCreando] = useState(false)
  const [fallo, setFallo] = useState(null)  // {m} del último envío fallido (HU-34)

  useEffect(() => {
    api('/api/historial/creacion')
      .then((h) => setMensajes(h.mensajes))
      .catch(() => {})
  }, [])

  const enviar = async (directo, esReintento = false) => {
    const m = (directo ?? texto).trim()
    if (!m || ocupado) return
    if (!esReintento) {
      setTexto('')
      setMensajes((prev) => [...prev, { rol: 'yo', texto: m }])
    }
    setFallo(null)
    setOcupado(true)
    try {
      const r = await api('/api/creacion', { mensaje: m })
      setMensajes((prev) => [...prev, { rol: 'tutor', texto: r.mensaje }])
      guardarBorrador('creacion', '')
      if (r.listo && r.diagnostico) {
        // Examen diagnóstico (HU-41): mide el punto de partida real y
        // recién con su resultado se diseña el temario.
        setMensajes((prev) => [...prev, { rol: 'diagnostico', preguntas: r.diagnostico }])
      } else if (r.listo) {
        setCreando(true)
        await onCreado()
      }
    } catch (e) {
      avisarError(e)
      setFallo({ m })
    }
    setOcupado(false)
  }

  const calificarDiagnostico = async (respuestas) => {
    try {
      setCreando(true)
      setOcupado(true)
      const r = await api('/api/diagnostico/calificar', { respuestas })
      setMensajes((prev) => [...prev, { rol: 'tutor', texto: r.resumen + ' Con eso calibro tu curso: creándolo…' }])
      await onCreado()
      setOcupado(false)
      return true
    } catch (e) { avisarError(e); setCreando(false); setOcupado(false); return false }
  }

  return (
    <Box style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <ZonaChat dep={mensajes.length + (ocupado ? 1 : 0)}>
        {mensajes.length === 0 && (
          <Container size="xs" ta="center" py={60}>
            <ThemeIcon size={56} radius="lg" variant="gradient"
              gradient={{ from: 'teal', to: 'indigo' }} mx="auto" mb="md">
              <Text fw={900} size="lg">Pb</Text>
            </ThemeIcon>
            <Title order={2} mb={6}>¿Qué quieres aprender?</Title>
            <Text c="dimmed" size="sm">
              Cuéntamelo con tus palabras. Te haré un par de preguntas, te propondré
              un plan y cuando digas “ya, dale” creo tu curso.
            </Text>
          </Container>
        )}
        {mensajes.map((m, i) => (
          m.rol === 'diagnostico'
            ? <QuizCard key={i} preguntas={m.preguntas} titulo="EXAMEN DIAGNÓSTICO — ¿DESDE DÓNDE ARRANCAMOS?"
                onCalificar={calificarDiagnostico} />
            : <Mensaje key={i} rol={m.rol}>{m.texto}</Mensaje>
        ))}
        {ocupado && <Escribiendo texto={creando ? 'Diseñando tu curso y guardando el plan (~1 min)…' : undefined} />}
        {fallo && (
          <Group justify="flex-end" gap="xs">
            <Text size="xs" c="red.5">⚠️ No enviado</Text>
            <Button size="compact-xs" variant="default" disabled={ocupado}
              onClick={() => enviar(fallo.m, true)}>
              Reintentar
            </Button>
          </Group>
        )}
      </ZonaChat>

      <Box p="md" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
        <Box maw={760} mx="auto">
          {mensajes.length === 0 && (
            <Group gap="xs" mb="xs">
              {EJEMPLOS.map((e) => (
                <Button key={e} variant="default" size="compact-xs" radius="xl"
                  onClick={() => enviar(e)}>
                  {e.slice(0, 52)}…
                </Button>
              ))}
            </Group>
          )}
          <Group align="flex-end" gap="xs">
            <Textarea
              style={{ flex: 1 }} radius="lg" autosize minRows={1} maxRows={5}
              placeholder="Hazme un curso de…"
              value={texto}
              onChange={(e) => {
                setTexto(e.target.value)
                guardarBorrador('creacion', e.target.value)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar() }
              }}
              autoFocus
            />
            <Button radius="lg" onClick={() => enviar()} loading={ocupado}>Enviar</Button>
          </Group>
        </Box>
      </Box>
    </Box>
  )
}
