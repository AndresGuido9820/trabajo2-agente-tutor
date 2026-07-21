import { useEffect, useState } from 'react'
import {
  Badge, Box, Button, Card, Container, Group, Progress, SimpleGrid, Text,
  ThemeIcon, Title,
} from '@mantine/core'
import { api } from './api.js'
import { avisarError } from './App.jsx'

/** Menú inicial: todos los cursos del estudiante + crear uno nuevo. */
export default function MisCursos({ onEntrar, onNuevo }) {
  const [cursos, setCursos] = useState(null)

  useEffect(() => {
    api('/api/cursos')
      .then((r) => setCursos(r.cursos))
      .catch((e) => { avisarError(e); setCursos([]) })
  }, [])

  return (
    <Container size="md" py="xl" style={{ width: '100%' }}>
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
        {(cursos ?? []).map((c) => (
          <Card key={c.id} withBorder radius="lg" p="lg" style={{ cursor: 'pointer' }}
            onClick={() => onEntrar(c.id)}>
            <Group justify="space-between" mb="xs">
              <Badge variant="light" color={c.total && c.aprobadas === c.total ? 'teal' : 'indigo'}>
                {c.total ? c.lenguaje : 'sin diseñar'}
              </Badge>
              {c.total > 0 && <Text size="xs" c="dimmed">{c.aprobadas}/{c.total} aprobadas</Text>}
            </Group>
            <Text fw={700} lineClamp={2} mb="sm">{c.nombre}</Text>
            {c.total > 0 && (
              <Progress value={(100 * c.aprobadas) / c.total} size="sm" radius="xl" color="teal" mb="sm" />
            )}
            <Button fullWidth variant="light">Entrar →</Button>
          </Card>
        ))}
      </SimpleGrid>
    </Container>
  )
}
