import { useEffect, useState } from 'react'
import {
  Badge, Box, Button, Card, Group, Loader, Stack, Text, Title,
} from '@mantine/core'
import { api } from './api.js'
import { avisar, avisarError } from './App.jsx'
import { QuizCard } from './Clase.jsx'

/** Repaso del día (HU-32): quiz corto sobre los conceptos vencidos. */
export default function Repaso({ refrescar }) {
  const [info, setInfo] = useState(null)          // {pendientes, proximo}
  const [preguntas, setPreguntas] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    api('/api/repaso').then(setInfo).catch(avisarError)
  }, [])

  const iniciar = async () => {
    setCargando(true)
    try {
      const r = await api('/api/repaso/iniciar', {}, 'POST')
      setPreguntas(r.preguntas)
    } catch (e) { avisarError(e) }
    setCargando(false)
  }

  const calificar = async (respuestas) => {
    try {
      const r = await api('/api/repaso/calificar', { respuestas })
      setResultado(r)
      avisar(`+${3 * r.aciertos} puntos por tu repaso`)
      await refrescar?.()
      return true
    } catch (e) { avisarError(e); return false }
  }

  if (!info) return <Group justify="center" pt={80}><Loader /></Group>

  return (
    <Box p="lg" style={{ overflowY: 'auto', flex: 1 }}>
      <Box maw={760} mx="auto">
        <Title order={3} mb="xs">Repaso del día</Title>
        <Text c="dimmed" size="sm" mb="md">
          Preguntas cortas sobre lo que te costó antes: repasar espaciado
          (1, 3 y 7 días) es la forma más eficaz de no olvidar.
        </Text>

        {info.pendientes === 0 && !preguntas && (
          <Card withBorder radius="md" p="lg">
            <Text fw={650}>Estás al día.</Text>
            <Text size="sm" c="dimmed">
              {info.proximo
                ? `Tu próximo repaso vence el ${info.proximo}.`
                : 'Nada en la cola: los conceptos que falles en evaluaciones aparecerán aquí.'}
            </Text>
          </Card>
        )}

        {info.pendientes > 0 && !preguntas && (
          <Card withBorder radius="md" p="lg">
            <Group justify="space-between">
              <Text fw={700}>{info.pendientes} concepto{info.pendientes > 1 ? 's' : ''} para repasar hoy</Text>
              <Button onClick={iniciar} loading={cargando}>Empezar el repaso</Button>
            </Group>
          </Card>
        )}

        {preguntas && !resultado && (
          <QuizCard preguntas={preguntas} onCalificar={calificar}
            titulo="REPASO DEL DÍA" />
        )}

        {resultado && (
          <Card withBorder radius="md" p="lg" mt="md">
            <Title order={4} mb="xs">
              {resultado.aciertos}/{resultado.total} — {resultado.aciertos === resultado.total ? 'impecable' : 'sin castigo: vuelven pronto'}
            </Title>
            <Stack gap={6}>
              {resultado.cola.map((i, k) => (
                <Group key={k} gap="xs">
                  <Badge variant="light" color="orange">{i.concepto}</Badge>
                  <Text size="sm" c="dimmed">vuelve el {i.vence}</Text>
                </Group>
              ))}
              {resultado.cola.length === 0 && (
                <Text size="sm" c="dimmed">La cola quedó vacía: todo dominado.</Text>
              )}
            </Stack>
          </Card>
        )}
      </Box>
    </Box>
  )
}
