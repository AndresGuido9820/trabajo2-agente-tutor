import { useEffect, useState } from 'react'
import {
  Avatar, Box, Button, Card, Group, Loader, Modal, SimpleGrid, Text,
  TextInput, ThemeIcon, Title,
} from '@mantine/core'
import { IconPlus } from '@tabler/icons-react'
import { api } from './api.js'
import { avisarError } from './App.jsx'

const COLORES = ['indigo', 'teal', 'grape', 'orange', 'cyan', 'pink']

/** Selector de perfiles de estudiante (HU-42): datos aislados por persona. */
export default function Usuarios({ onElegir }) {
  const [datos, setDatos] = useState(null)
  const [modal, setModal] = useState(false)
  const [nombre, setNombre] = useState('')
  const [creando, setCreando] = useState(false)

  useEffect(() => {
    api('/api/usuarios').then(setDatos).catch(avisarError)
  }, [])

  const elegir = async (id) => {
    try {
      await api(`/api/usuarios/${id}/activar`, {}, 'POST')
      onElegir()
    } catch (e) { avisarError(e) }
  }

  const crear = async () => {
    if (!nombre.trim()) return
    setCreando(true)
    try {
      await api('/api/usuarios', { nombre })
      setModal(false)
      onElegir()
    } catch (e) { avisarError(e) }
    setCreando(false)
  }

  if (!datos) return <Group justify="center" pt={120}><Loader /></Group>

  return (
    <Box p="xl" style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
      <Box maw={720} mx="auto" w="100%" ta="center">
        <Title order={2} mb={6}>¿Quién estudia hoy?</Title>
        <Text c="dimmed" size="sm" mb="xl">
          Cada perfil tiene sus propios cursos, progreso y conversaciones.
        </Text>
        <SimpleGrid cols={{ base: 2, sm: 3 }} spacing="lg">
          {datos.usuarios.map((u, i) => (
            <Card key={u.id} component="button" type="button" withBorder radius="lg"
              p="lg" onClick={() => elegir(u.id)}
              style={{ cursor: 'pointer', width: '100%' }}
              aria-label={`Estudiar como ${u.nombre}`}>
              <Avatar size={64} radius="xl" mx="auto" mb="sm"
                color={COLORES[i % COLORES.length]} variant="filled">
                <Text size="xl" fw={700}>{u.nombre.trim()[0]?.toUpperCase()}</Text>
              </Avatar>
              <Text fw={600} truncate>{u.nombre}</Text>
              {u.id === datos.activo && <Text size="xs" c="dimmed">sesión actual</Text>}
            </Card>
          ))}
          <Card component="button" type="button" withBorder radius="lg" p="lg"
            onClick={() => setModal(true)}
            style={{ cursor: 'pointer', borderStyle: 'dashed', width: '100%' }}
            aria-label="Crear un perfil nuevo">
            <ThemeIcon size={64} radius="xl" mx="auto" mb="sm" variant="light" color="gray">
              <IconPlus size={28} stroke={1.6} />
            </ThemeIcon>
            <Text fw={600} c="dimmed">Nuevo perfil</Text>
          </Card>
        </SimpleGrid>
      </Box>

      <Modal opened={modal} onClose={() => setModal(false)} title="Nuevo perfil" centered>
        <TextInput label="¿Cómo te llamas?" placeholder="Tu nombre" value={nombre}
          onChange={(e) => setNombre(e.target.value)} data-autofocus
          onKeyDown={(e) => { if (e.key === 'Enter') crear() }} />
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={() => setModal(false)}>Cancelar</Button>
          <Button onClick={crear} loading={creando} disabled={!nombre.trim()}>Empezar</Button>
        </Group>
      </Modal>
    </Box>
  )
}
