import { useEffect, useRef } from 'react'
import { Avatar, Box, Group, Loader, Paper, Text } from '@mantine/core'
import Prosa from './Prosa.jsx'

/** Burbuja de mensaje del chat (estilo sobrio: el tutor sin burbuja). */
export function Mensaje({ rol, children, lenguaje, ancho }) {
  if (rol === 'sistema') {
    return (
      <Text size="xs" c="dimmed" ta="center" my={6}>{children}</Text>
    )
  }
  const esTutor = rol === 'tutor'
  if (esTutor) {
    return (
      <Group align="flex-start" gap="sm" mb="md" wrap="nowrap"
        w={ancho ? '100%' : undefined}>
        <Avatar size={28} radius="md" color="indigo" variant="filled">
          <Text size="xs" fw={800} ff="monospace">P</Text>
        </Avatar>
        <Box style={{ minWidth: 0, flex: 1 }} pt={2}>
          {typeof children === 'string'
            ? <Prosa lenguaje={lenguaje}>{children}</Prosa>
            : (
              <Paper withBorder radius="md" p="md">
                {children}
              </Paper>
            )}
        </Box>
      </Group>
    )
  }
  return (
    <Paper
      p="sm" px="md" radius="lg" mb="md"
      maw={ancho ? '100%' : '78%'} w={ancho ? '100%' : undefined}
      ml="auto" bg="var(--mantine-color-default-hover)"
      style={{ borderBottomRightRadius: 6 }}
    >
      {typeof children === 'string'
        ? <Prosa lenguaje={lenguaje}>{children}</Prosa>
        : children}
    </Paper>
  )
}

export function Escribiendo({ texto = 'El tutor escribe…' }) {
  // aria-hidden: el indicador es ruido para lectores; se anuncia el
  // mensaje completo al llegar (aria-live de ZonaChat), no el "escribiendo".
  return (
    <Group gap="xs" mb="sm" aria-hidden>
      <Loader size="xs" type="dots" />
      <Text size="sm" c="dimmed">{texto}</Text>
    </Group>
  )
}

/** Contenedor scrolleable que baja solo al llegar mensajes. */
export function ZonaChat({ children, dep }) {
  const ref = useRef(null)
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' })
  }, [dep])
  return (
    <Box ref={ref} style={{ flex: 1, overflowY: 'auto' }} p="lg"
      aria-live="polite" role="log" aria-label="Conversación con el tutor">
      <Box maw={760} mx="auto">{children}</Box>
    </Box>
  )
}
