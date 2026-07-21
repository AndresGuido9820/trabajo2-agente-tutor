import { useEffect, useState } from 'react'
import {
  Badge, Box, Button, Card, Group, Loader, Progress, SimpleGrid, Stack, Text,
  Title, Tooltip,
} from '@mantine/core'
import { api } from './api.js'
import { avisarError } from './App.jsx'

/** Vista "Mi progreso" (HU-31): métricas calculadas en el backend. */
export default function Estadisticas({ irAClase }) {
  const [datos, setDatos] = useState(null)
  const [uso, setUso] = useState([])

  useEffect(() => {
    api('/api/estadisticas').then(setDatos).catch(avisarError)
    api('/api/uso').then((r) => setUso(r.uso)).catch(() => {})
  }, [])

  if (!datos) {
    return <Group justify="center" pt={80}><Loader /></Group>
  }
  const { actividad, notas, conceptos, totales } = datos
  const maxMensajes = Math.max(1, ...actividad.map((d) => d.mensajes))
  const hayNotas = Object.keys(notas).length > 0

  return (
    <Box p="lg" style={{ overflowY: 'auto', flex: 1 }}>
      <Box maw={860} mx="auto">
        <Title order={3} mb="md">📈 Mi progreso</Title>

        <SimpleGrid cols={{ base: 2, sm: 4 }} mb="md">
          <Tarjeta valor={`${totales.aprobadas}/${totales.total}`} etiqueta="clases aprobadas" />
          <Tarjeta valor={`⭐ ${totales.puntos}`} etiqueta="puntos" />
          <Tarjeta valor={`🔥 ${totales.racha}`} etiqueta={`racha (mejor: ${totales.mejor_racha})`} />
          <Tarjeta valor={`~${totales.minutos_estimados} min`} etiqueta="tiempo estudiando" />
        </SimpleGrid>

        <Card withBorder radius="md" p="md" mb="md">
          <Text fw={700} mb="xs">Actividad (mensajes por día)</Text>
          {actividad.length === 0 ? (
            <Text size="sm" c="dimmed">Aún no hay actividad: entra a una clase y conversa con el tutor.</Text>
          ) : (
            <Group align="flex-end" gap={6} h={120}>
              {actividad.map((d) => (
                <Tooltip key={d.fecha}
                  label={`${d.fecha}: ${d.mensajes} mensajes${d.puntos ? ` · +${d.puntos} ⭐` : ''}`}>
                  <Stack gap={2} align="center" style={{ flex: 1, height: '100%', justifyContent: 'flex-end' }}>
                    <Box w="100%" maw={44}
                      style={{
                        height: `${Math.max(6, (100 * d.mensajes) / maxMensajes)}%`,
                        borderRadius: 6,
                        background: d.puntos
                          ? 'var(--mantine-color-teal-5)'
                          : 'var(--mantine-color-indigo-4)',
                      }} />
                    <Text size="10px" c="dimmed">{d.fecha.slice(5)}</Text>
                  </Stack>
                </Tooltip>
              ))}
            </Group>
          )}
        </Card>

        <Card withBorder radius="md" p="md" mb="md">
          <Text fw={700} mb="xs">Notas de tus evaluaciones</Text>
          {!hayNotas ? (
            <Text size="sm" c="dimmed">Todavía no presentas evaluaciones.</Text>
          ) : (
            <Stack gap="xs">
              {Object.entries(notas).map(([clase, intentos]) => {
                const mejor = Math.max(...intentos)
                return (
                  <Group key={clase} gap="sm" wrap="nowrap">
                    <Text size="sm" w={70}>Clase {Number(clase) + 1}</Text>
                    <Progress value={mejor} size="lg" radius="xl" style={{ flex: 1 }}
                      color={mejor >= 70 ? 'teal' : 'orange'}
                      aria-label={`Mejor nota de la clase ${Number(clase) + 1}: ${mejor} de 100`} />
                    <Text size="sm" fw={700} w={60} ta="right">{mejor}/100</Text>
                    <Text size="xs" c="dimmed" w={90}>
                      {intentos.length} intento{intentos.length > 1 ? 's' : ''}
                    </Text>
                  </Group>
                )
              })}
            </Stack>
          )}
        </Card>

        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Card withBorder radius="md" p="md">
            <Text fw={700} mb="xs">💪 Conceptos dominados</Text>
            {conceptos.dominados.length === 0 ? (
              <Text size="sm" c="dimmed">Aprueba evaluaciones para ver tus fortalezas aquí.</Text>
            ) : (
              <Group gap={6}>
                {conceptos.dominados.map((f) => (
                  <Badge key={f.c} variant="light" color="teal">{f.c} · {f.ok}✓</Badge>
                ))}
              </Group>
            )}
          </Card>
          <Card withBorder radius="md" p="md">
            <Text fw={700} mb="xs">📌 Para repasar</Text>
            {conceptos.repasar.length === 0 ? (
              <Text size="sm" c="dimmed">Nada pendiente: no has fallado conceptos. 🎉</Text>
            ) : (
              <Stack gap={6}>
                {conceptos.repasar.map((f) => (
                  <Group key={f.c} justify="space-between" wrap="nowrap">
                    <Badge variant="light" color="orange">{f.c} · {f.mal}✗ {f.ok}✓</Badge>
                    {f.clase !== null && (
                      <Button size="compact-xs" variant="subtle"
                        onClick={() => irAClase(f.clase)}>
                        repasar en el chat →
                      </Button>
                    )}
                  </Group>
                ))}
              </Stack>
            )}
          </Card>
        </SimpleGrid>

        {uso.length > 0 && (
          <Card withBorder radius="md" p="md" mt="md">
            <Text fw={700} mb="xs">🤖 Uso del modelo (local)</Text>
            <Stack gap={4}>
              {uso.slice(-6).map((f, i) => (
                <Text size="sm" c="dimmed" key={i}>
                  {f.dia} · {f.carril}/{f.modelo}: {f.llamadas} llamadas
                  {f.costo_usd !== null && ` · ~$${f.costo_usd} USD`}
                </Text>
              ))}
            </Stack>
          </Card>
        )}
      </Box>
    </Box>
  )
}

function Tarjeta({ valor, etiqueta }) {
  return (
    <Card withBorder radius="md" p="md">
      <Title order={4}>{valor}</Title>
      <Text size="xs" c="dimmed">{etiqueta}</Text>
    </Card>
  )
}
