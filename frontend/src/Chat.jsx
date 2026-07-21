import { useEffect, useRef } from 'react'
import { Box, Group, Loader, Paper, Text } from '@mantine/core'
import Prosa from './Prosa.jsx'

/** Burbuja de mensaje del chat. */
export function Mensaje({ rol, children, lenguaje, ancho }) {
  if (rol === 'sistema') {
    return (
      <Text size="xs" c="dimmed" ta="center" my={6}>{children}</Text>
    )
  }
  const esTutor = rol === 'tutor'
  return (
    <Paper
      p="md" radius="lg" withBorder={esTutor} mb="sm"
      maw={ancho ? '100%' : '86%'} w={ancho ? '100%' : undefined}
      ml={esTutor ? 0 : 'auto'}
      bg={esTutor ? 'var(--mantine-color-default-hover)' : 'var(--mantine-color-indigo-light)'}
      style={{
        borderBottomLeftRadius: esTutor ? 6 : undefined,
        borderBottomRightRadius: esTutor ? undefined : 6,
      }}
    >
      {esTutor && (
        <Text size="10px" fw={700} tt="uppercase" c="dimmed" mb={6} lts="0.06em">
          Profe Bit
        </Text>
      )}
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
