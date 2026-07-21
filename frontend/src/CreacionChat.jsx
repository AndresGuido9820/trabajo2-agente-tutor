import { useEffect, useState } from 'react'
import {
  Box, Button, Chip, Container, Group, Stack, Text, Textarea, ThemeIcon, Title,
} from '@mantine/core'
import { api } from './api.js'
import { avisarError } from './App.jsx'
import { Escribiendo, Mensaje, ZonaChat } from './Chat.jsx'

const EJEMPLOS = [
  'Hazme un curso de Python para analizar las ventas de mi negocio; manejo bien Excel',
  'Quiero aprender a hacer páginas web desde cero, nunca he programado',
]

/** Conversación de diseño del curso: pregunta, propone y crea al confirmar. */
export default function CreacionChat({ onCreado }) {
  const [mensajes, setMensajes] = useState([])
  const [texto, setTexto] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [creando, setCreando] = useState(false)

  useEffect(() => {
    api('/api/historial/creacion')
      .then((h) => setMensajes(h.mensajes))
      .catch(() => {})
  }, [])

  const enviar = async (directo) => {
    const m = (directo ?? texto).trim()
    if (!m || ocupado) return
    setTexto('')
    setMensajes((prev) => [...prev, { rol: 'yo', texto: m }])
    setOcupado(true)
    try {
      const r = await api('/api/creacion', { mensaje: m })
      setMensajes((prev) => [...prev, { rol: 'tutor', texto: r.mensaje }])
      if (r.listo) {
        setCreando(true)
        await onCreado()
      }
    } catch (e) { avisarError(e) }
    setOcupado(false)
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
          <Mensaje key={i} rol={m.rol}>{m.texto}</Mensaje>
        ))}
        {ocupado && <Escribiendo texto={creando ? 'Diseñando tu curso y guardando el plan (~1 min)…' : undefined} />}
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
              value={texto} onChange={(e) => setTexto(e.target.value)}
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
