import { useEffect, useState } from 'react'
import {
  Box, Button, Card, Container, Group, Loader, Paper, Text, TextInput,
  Textarea, Title,
} from '@mantine/core'
import Markdown from 'react-markdown'
import { api } from './api.js'
import { avisar, avisarError } from './App.jsx'

/** El diseño del curso: documento .md (vista) + edición ESTRUCTURADA. */
export default function Diseno({ onGuardado }) {
  const [plan, setPlan] = useState(null)
  const [editando, setEditando] = useState(false)
  const [diseno, setDiseno] = useState(null)

  const cargar = () => {
    api('/api/plan').then((r) => setPlan(r.md)).catch(avisarError)
  }
  useEffect(cargar, [])

  const abrirEditor = async () => {
    try {
      setDiseno(await api('/api/diseno'))
      setEditando(true)
    } catch (e) { avisarError(e) }
  }

  const guardar = async () => {
    try {
      await api('/api/diseno', {
        lenguaje: diseno.lenguaje,
        clases: diseno.clases.map((c) => ({
          titulo: c.titulo.trim(),
          objetivo: c.objetivo.trim(),
          conceptos: (Array.isArray(c.conceptos) ? c.conceptos.join(',') : c.conceptos)
            .split(',').map((s) => s.trim()).filter(Boolean),
        })),
      })
      avisar('Diseño guardado 💾 — el tutor ya usa la nueva estructura')
      setEditando(false)
      setPlan(null)
      cargar()
      onGuardado?.()
    } catch (e) { avisarError(e) }
  }

  const descargar = () => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([plan ?? ''], { type: 'text/markdown' }))
    a.download = 'mi-curso.md'
    a.click()
  }

  if (editando && diseno) {
    return (
      <Container size="md" py="lg" style={{ width: '100%', overflowY: 'auto' }}>
        <Group mb="md">
          <Button onClick={guardar}>💾 Guardar estructura</Button>
          <Button variant="default" onClick={() => setEditando(false)}>Cancelar</Button>
          <Text size="xs" c="dimmed">Esto es lo que el tutor (LLM) recibe: mantenlo claro.</Text>
        </Group>
        <TextInput label="Lenguaje" value={diseno.lenguaje} maw={240} mb="md"
          onChange={(e) => setDiseno({ ...diseno, lenguaje: e.target.value })} />
        {diseno.clases.map((c, i) => (
          <Card key={i} withBorder radius="lg" mb="sm" p="md">
            <Text size="xs" c="dimmed" fw={700} mb={6}>CLASE {i + 1}</Text>
            <TextInput placeholder="Título" value={c.titulo} mb="xs"
              onChange={(e) => actualizar(i, 'titulo', e.target.value)} />
            <Textarea placeholder="Objetivo: qué sabrá HACER el estudiante" autosize minRows={2}
              value={c.objetivo} mb="xs"
              onChange={(e) => actualizar(i, 'objetivo', e.target.value)} />
            <TextInput placeholder="Subtemas separados por coma"
              value={Array.isArray(c.conceptos) ? c.conceptos.join(', ') : c.conceptos}
              onChange={(e) => actualizar(i, 'conceptos', e.target.value)} />
          </Card>
        ))}
      </Container>
    )

    function actualizar(i, campo, valor) {
      const clases = diseno.clases.slice()
      clases[i] = { ...clases[i], [campo]: valor }
      setDiseno({ ...diseno, clases })
    }
  }

  return (
    <Container size="md" py="lg" style={{ width: '100%', overflowY: 'auto' }}>
      <Group justify="space-between" mb="md">
        <Title order={3}>📄 Diseño del curso</Title>
        <Group gap="xs">
          <Button variant="light" onClick={abrirEditor}>✏️ Editar estructura</Button>
          <Button variant="default" onClick={descargar}>⬇️ .md</Button>
        </Group>
      </Group>
      <Paper withBorder radius="lg" p="xl">
        {plan === null ? <Loader /> : (
          <Box className="prosa" style={{ lineHeight: 1.7 }}>
            <Markdown>{plan}</Markdown>
          </Box>
        )}
      </Paper>
    </Container>
  )
}
