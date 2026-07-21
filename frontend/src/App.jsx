import { useCallback, useEffect, useState } from 'react'
import {
  ActionIcon, AppShell, Badge, Box, Button, Card, Group, Progress, ScrollArea,
  Stack, Text, ThemeIcon, Title, Tooltip, useMantineColorScheme,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { api } from './api.js'
import MisCursos from './MisCursos.jsx'
import Clase from './Clase.jsx'
import Diseno from './Diseno.jsx'
import CreacionChat from './CreacionChat.jsx'
import Estadisticas from './Estadisticas.jsx'

export function avisar(mensaje, color = 'teal') {
  notifications.show({ message: mensaje, color, withBorder: true })
}
export function avisarError(e) {
  notifications.show({ message: String(e.message || e), color: 'red', withBorder: true })
}

export default function App({ escala, cambiarEscala }) {
  // vista: cursos | creacion | diseno | clase
  const [vista, setVista] = useState('cursos')
  const [estado, setEstado] = useState(null)
  const [convos, setConvos] = useState({})
  const [claseActiva, setClaseActiva] = useState(0)

  const refrescar = useCallback(async () => {
    try {
      const e = await api('/api/estado')
      const c = await api('/api/conversaciones')
      setEstado(e)
      setConvos(c.canales || {})
      return e
    } catch (e) {
      avisarError(e)
      return null
    }
  }, [])

  const entrarCurso = async (id) => {
    try {
      await api(`/api/cursos/${id}/activar`, {}, 'POST')
      const e = await refrescar()
      if (!e || !e.perfil) { setVista('creacion'); return }
      setClaseActiva(e.unidad_actual ?? 0)
      setVista('clase')
    } catch (e) { avisarError(e) }
  }

  const nuevoCurso = async () => {
    try {
      await api('/api/cursos', {}, 'POST')
      setEstado(null)
      setVista('creacion')
    } catch (e) { avisarError(e) }
  }

  const abrirClase = (i) => { setClaseActiva(i); setVista('clase') }

  const conCurso = vista !== 'cursos' && estado?.perfil
  const aprobadas = estado?.unidades?.filter((u) => u.estado === 'aprobada').length ?? 0
  const total = estado?.unidades?.length ?? 0

  return (
    <AppShell
      navbar={{ width: 300, breakpoint: 'sm', collapsed: { mobile: true } }}
      padding={0}
      styles={{ main: { height: '100vh', display: 'flex', flexDirection: 'column' } }}
    >
      <AppShell.Navbar p="sm" style={{ gap: 8 }}>
        <Group gap="xs" px="xs" py={6}>
          <ThemeIcon size={30} radius="md" variant="gradient" gradient={{ from: 'teal', to: 'indigo' }}>
            <Text fw={900} size="sm">Pb</Text>
          </ThemeIcon>
          <Text fw={700}>Profe Bit</Text>
        </Group>

        {conCurso && (
          <Box px="xs" pb="xs">
            <Text size="xs" c="dimmed" mb={4}>
              {aprobadas} de {total} clases · {estado.lenguaje}
            </Text>
            <Progress value={total ? (100 * aprobadas) / total : 0} size="sm" radius="xl"
              color="teal" />
          </Box>
        )}

        <ScrollArea style={{ flex: 1 }}>
          <Stack gap={4}>
            <NavItem etiqueta="← Mis cursos" sub="Todos tus cursos"
              onClick={async () => { await refrescar(); setVista('cursos') }} />
            {conCurso && (
              <>
                <Text size="xs" c="dimmed" fw={700} tt="uppercase" px="xs" mt="xs">Curso</Text>
                <NavItem icono="📄" etiqueta="Diseño del curso" sub="Documento estructurado — editable"
                  activa={vista === 'diseno'} onClick={() => setVista('diseno')} />
                <NavItem icono="📈" etiqueta="Mi progreso" sub="Actividad, notas y conceptos"
                  activa={vista === 'stats'} onClick={() => setVista('stats')} />
                <Text size="xs" c="dimmed" fw={700} tt="uppercase" px="xs" mt="xs">Clases</Text>
                {estado.unidades.map((u) => (
                  <NavClase key={u.indice} u={u} convos={convos}
                    activa={vista === 'clase' && claseActiva === u.indice}
                    onClick={() => u.estado !== 'bloqueada' && abrirClase(u.indice)} />
                ))}
              </>
            )}
          </Stack>
        </ScrollArea>

        <Group justify="space-between" px="xs" pt="xs"
          style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
          <Preferencias escala={escala} cambiarEscala={cambiarEscala} />
          {conCurso && (
            <Group gap={6}>
              <Tooltip label="Días seguidos estudiando"><Badge variant="light" color="orange">🔥 {estado.racha}</Badge></Tooltip>
              <Tooltip label="Puntos por checkpoints y clases aprobadas"><Badge variant="light" color="yellow">⭐ {estado.puntos}</Badge></Tooltip>
            </Group>
          )}
        </Group>
      </AppShell.Navbar>

      <AppShell.Main>
        {vista === 'cursos' && <MisCursos onEntrar={entrarCurso} onNuevo={nuevoCurso} />}
        {vista === 'creacion' && (
          <CreacionChat onCreado={async () => {
            const e = await refrescar()
            avisar('¡Tu curso está listo! 🎉')
            if (e?.perfil) { setClaseActiva(0); setVista('clase') }
          }} />
        )}
        {vista === 'diseno' && estado?.perfil && <Diseno onGuardado={refrescar} />}
        {vista === 'stats' && estado?.perfil && <Estadisticas irAClase={abrirClase} />}
        {vista === 'clase' && estado?.perfil && (
          <Clase key={`${estado.curso_id}-${claseActiva}`} indice={claseActiva}
            unidad={estado.unidades[claseActiva]} lenguaje={estado.lenguaje}
            refrescar={refrescar} irAClase={abrirClase}
            haySiguiente={claseActiva + 1 < total} />
        )}
      </AppShell.Main>
    </AppShell>
  )
}

function Preferencias({ escala, cambiarEscala }) {
  const { colorScheme, setColorScheme } = useMantineColorScheme()
  const siguiente = { dark: 'light', light: 'auto', auto: 'dark' }
  const icono = { dark: '🌙', light: '☀️', auto: '🌓' }[colorScheme] ?? '🌓'
  const escalas = ['chico', 'normal', 'grande']
  const subir = () => {
    const i = escalas.indexOf(escala)
    cambiarEscala(escalas[Math.min(i + 1, 2)])
  }
  const bajar = () => {
    const i = escalas.indexOf(escala)
    cambiarEscala(escalas[Math.max(i - 1, 0)])
  }
  return (
    <Group gap={2}>
      <Tooltip label={`Tema: ${colorScheme} (clic para cambiar)`}>
        <ActionIcon variant="subtle" aria-label="Cambiar tema claro/oscuro"
          onClick={() => setColorScheme(siguiente[colorScheme] ?? 'dark')}>
          {icono}
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Texto más chico">
        <ActionIcon variant="subtle" aria-label="Reducir tamaño de texto"
          onClick={bajar} disabled={escala === 'chico'}>A−</ActionIcon>
      </Tooltip>
      <Tooltip label="Texto más grande">
        <ActionIcon variant="subtle" aria-label="Aumentar tamaño de texto"
          onClick={subir} disabled={escala === 'grande'}>A+</ActionIcon>
      </Tooltip>
    </Group>
  )
}

function NavItem({ icono, etiqueta, sub, activa, onClick }) {
  return (
    <Card p="xs" radius="md" withBorder={!!activa} onClick={onClick}
      style={{ cursor: 'pointer', background: activa ? 'var(--mantine-color-default-hover)' : 'transparent' }}>
      <Group gap="sm" wrap="nowrap">
        {icono && <Text size="sm">{icono}</Text>}
        <Box style={{ minWidth: 0 }}>
          <Text size="sm" fw={600} truncate>{etiqueta}</Text>
          {sub && <Text size="xs" c="dimmed" truncate>{sub}</Text>}
        </Box>
      </Group>
    </Card>
  )
}

function NavClase({ u, convos, activa, onClick }) {
  const coronada = u.completada || u.estado === 'aprobada'
  const bloqueada = u.estado === 'bloqueada'
  const sub = u.estado === 'aprobada' ? `✓ Aprobada · ${u.mejor_nota}/100`
    : bloqueada ? '🔒 Aprueba la anterior'
    : u.completada ? 'Completada — falta evaluación'
    : convos[`u${u.indice}`] ? 'Conversación en curso' : 'Sin empezar'
  return (
    <Card p="xs" radius="md" withBorder={!!activa} onClick={onClick}
      opacity={bloqueada ? 0.45 : 1}
      style={{ cursor: bloqueada ? 'not-allowed' : 'pointer', background: activa ? 'var(--mantine-color-default-hover)' : 'transparent' }}>
      <Group gap="sm" wrap="nowrap">
        <ThemeIcon size={26} radius="xl" variant={coronada ? 'filled' : 'outline'}
          color={coronada ? 'teal' : 'gray'}>
          <Text size="xs" fw={700}>{coronada ? '✓' : u.indice + 1}</Text>
        </ThemeIcon>
        <Box style={{ minWidth: 0, flex: 1 }}>
          <Text size="sm" fw={600} truncate td={coronada ? 'line-through' : undefined}
            c={coronada ? 'dimmed' : undefined}>
            {u.titulo}
          </Text>
          <Text size="xs" c="dimmed" truncate>{sub}</Text>
        </Box>
        {!!convos[`u${u.indice}`] && !activa && (
          <Box w={7} h={7} style={{ borderRadius: '50%', background: 'var(--mantine-color-indigo-4)' }} />
        )}
      </Group>
    </Card>
  )
}
