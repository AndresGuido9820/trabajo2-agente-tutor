import { useEffect, useState } from 'react'
import {
  ActionIcon, Badge, Box, Button, Card, Collapse, Container, Group, Menu,
  Modal, Progress, SimpleGrid, Text, TextInput, ThemeIcon, Title,
} from '@mantine/core'
import { api } from './api.js'
import { avisar, avisarError } from './App.jsx'

/** Menú inicial: todos los cursos + crear, renombrar, archivar y borrar. */
export default function MisCursos({ onEntrar, onNuevo }) {
  const [cursos, setCursos] = useState(null)
  const [verArchivados, setVerArchivados] = useState(false)
  const [renombrando, setRenombrando] = useState(null)   // {id, nombre}
  const [borrando, setBorrando] = useState(null)         // {id, nombre}

  const cargar = () =>
    api('/api/cursos')
      .then((r) => setCursos(r.cursos))
      .catch((e) => { avisarError(e); setCursos([]) })
  useEffect(() => { cargar() }, [])

  const activos = (cursos ?? []).filter((c) => !c.archivado)
  const archivados = (cursos ?? []).filter((c) => c.archivado)

  const archivar = async (c, valor) => {
    try {
      await api(`/api/cursos/${c.id}`, { archivado: valor }, 'PATCH')
      avisar(valor ? 'Curso archivado 📦' : 'Curso restaurado')
      cargar()
    } catch (e) { avisarError(e) }
  }

  return (
    <Container size="md" py="xl" style={{ width: '100%', overflowY: 'auto' }}>
      <Title order={2} mb={4}>Mis cursos</Title>
      <Text c="dimmed" size="sm" mb="xl">
        Cada curso se diseña conversando con tu tutor y se estudia clase por clase.
      </Text>
      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
        <Card withBorder radius="lg" p="lg" style={{ borderStyle: 'dashed', cursor: 'pointer' }}
          onClick={onNuevo}>
          <Group>
            <ThemeIcon size={38} radius="xl" variant="light" color="indigo">＋</ThemeIcon>
            <Box>
              <Text fw={700}>Nuevo curso</Text>
              <Text size="sm" c="dimmed">Dale un prompt al tutor y diseñen el curso juntos</Text>
            </Box>
          </Group>
        </Card>
        {activos.map((c) => (
          <TarjetaCurso key={c.id} c={c} onEntrar={onEntrar}
            onRenombrar={() => setRenombrando({ id: c.id, nombre: c.nombre })}
            onArchivar={() => archivar(c, true)}
            onBorrar={() => setBorrando({ id: c.id, nombre: c.nombre })} />
        ))}
      </SimpleGrid>

      {archivados.length > 0 && (
        <Box mt="xl">
          <Button variant="subtle" size="compact-sm"
            onClick={() => setVerArchivados(!verArchivados)}>
            📦 Archivados ({archivados.length}) {verArchivados ? '▴' : '▾'}
          </Button>
          <Collapse in={verArchivados}>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md" mt="sm">
              {archivados.map((c) => (
                <TarjetaCurso key={c.id} c={c} onEntrar={onEntrar}
                  onRenombrar={() => setRenombrando({ id: c.id, nombre: c.nombre })}
                  onArchivar={() => archivar(c, false)}
                  onBorrar={() => setBorrando({ id: c.id, nombre: c.nombre })} />
              ))}
            </SimpleGrid>
          </Collapse>
        </Box>
      )}

      <ModalRenombrar datos={renombrando} onCerrar={() => setRenombrando(null)}
        onListo={() => { setRenombrando(null); cargar() }} />
      <ModalBorrar datos={borrando} onCerrar={() => setBorrando(null)}
        onListo={() => { setBorrando(null); cargar() }} />
    </Container>
  )
}

function TarjetaCurso({ c, onEntrar, onRenombrar, onArchivar, onBorrar }) {
  return (
    <Card withBorder radius="lg" p="lg" opacity={c.archivado ? 0.7 : 1}>
      <Group justify="space-between" mb="xs">
        <Badge variant="light" color={c.total && c.aprobadas === c.total ? 'teal' : 'indigo'}>
          {c.total ? c.lenguaje : 'sin diseñar'}
        </Badge>
        <Group gap={4}>
          {c.total > 0 && <Text size="xs" c="dimmed">{c.aprobadas}/{c.total} aprobadas</Text>}
          <Menu position="bottom-end" withinPortal>
            <Menu.Target>
              <ActionIcon variant="subtle" color="gray" aria-label="Opciones del curso">⋯</ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item onClick={onRenombrar}>✏️ Renombrar</Menu.Item>
              <Menu.Item onClick={onArchivar}>
                {c.archivado ? '📤 Restaurar' : '📦 Archivar'}
              </Menu.Item>
              <Menu.Item component="a" href={`/api/cursos/${c.id}/exportar`}
                style={{ display: 'none' }}>⬇️ Exportar</Menu.Item>
              <Menu.Divider />
              <Menu.Item color="red" onClick={onBorrar}>🗑 Borrar curso…</Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>
      <Text fw={700} lineClamp={2} mb="sm">{c.nombre}</Text>
      {c.total > 0 && (
        <Progress value={(100 * c.aprobadas) / c.total} size="sm" radius="xl" color="teal" mb="sm" />
      )}
      <Button fullWidth variant="light" onClick={() => onEntrar(c.id)}>Entrar →</Button>
    </Card>
  )
}

function ModalRenombrar({ datos, onCerrar, onListo }) {
  const [nombre, setNombre] = useState('')
  useEffect(() => { if (datos) setNombre(datos.nombre) }, [datos])
  const guardar = async () => {
    if (!nombre.trim()) return
    try {
      await api(`/api/cursos/${datos.id}`, { nombre: nombre.trim() }, 'PATCH')
      avisar('Nombre guardado ✏️')
      onListo()
    } catch (e) { avisarError(e) }
  }
  return (
    <Modal opened={!!datos} onClose={onCerrar} title="Renombrar curso" centered>
      <TextInput value={nombre} onChange={(e) => setNombre(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && guardar()} autoFocus
        placeholder="Nombre del curso" mb="md" />
      <Group justify="flex-end">
        <Button variant="default" onClick={onCerrar}>Cancelar</Button>
        <Button onClick={guardar} disabled={!nombre.trim()}>Guardar</Button>
      </Group>
    </Modal>
  )
}

function ModalBorrar({ datos, onCerrar, onListo }) {
  const [confirmacion, setConfirmacion] = useState('')
  useEffect(() => { setConfirmacion('') }, [datos])
  const coincide = datos && confirmacion.trim() === datos.nombre.trim()
  const borrar = async () => {
    try {
      await api(`/api/cursos/${datos.id}`, undefined, 'DELETE')
      avisar('Curso movido a la papelera 🗑')
      onListo()
    } catch (e) { avisarError(e) }
  }
  return (
    <Modal opened={!!datos} onClose={onCerrar} title="Borrar curso" centered>
      <Text size="sm" mb="xs">
        Se moverá a la papelera (recuperable a mano). Para confirmar, escribe
        el nombre del curso:
      </Text>
      <Text size="sm" fw={700} mb="xs" c="red.4">{datos?.nombre}</Text>
      <TextInput value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)}
        placeholder="Escribe el nombre exacto" autoFocus mb="md" />
      <Group justify="flex-end">
        <Button variant="default" onClick={onCerrar}>Cancelar</Button>
        <Button color="red" onClick={borrar} disabled={!coincide}>Borrar</Button>
      </Group>
    </Modal>
  )
}
