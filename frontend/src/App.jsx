import { useCallback, useEffect, useState } from 'react'
import {
  ActionIcon, AppShell, Avatar, Badge, Box, Button, Card, Group, Progress,
  ScrollArea, Stack, Text, ThemeIcon, Title, Tooltip, useMantineColorScheme,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { Spotlight, spotlight } from '@mantine/spotlight'
import {
  IconArrowLeft, IconChartLine, IconDeviceDesktop, IconFileDescription,
  IconFlame, IconMoon, IconPlus, IconRepeat, IconSearch, IconStar, IconSun,
} from '@tabler/icons-react'
import '@mantine/spotlight/styles.css'
import { api } from './api.js'
import MisCursos from './MisCursos.jsx'
import Clase from './Clase.jsx'
import Diseno from './Diseno.jsx'
import CreacionChat from './CreacionChat.jsx'
import Estadisticas from './Estadisticas.jsx'
import Repaso from './Repaso.jsx'
import Usuarios from './Usuarios.jsx'

export function avisar(mensaje, color = 'teal') {
  notifications.show({ message: mensaje, color, withBorder: true })
}
export function avisarError(e) {
  notifications.show({ message: String(e.message || e), color: 'red', withBorder: true })
}

export default function App({ escala, cambiarEscala }) {
  // vista: usuarios | cursos | creacion | diseno | clase | stats | repaso
  const [vista, setVista] = useState('usuarios')
  const [usuario, setUsuario] = useState(null)
  const [estado, setEstado] = useState(null)
  const [convos, setConvos] = useState({})
  const [claseActiva, setClaseActiva] = useState(0)
  const [destacar, setDestacar] = useState(null)  // id de mensaje a resaltar (HU-37)
  const [repaso, setRepaso] = useState(null)      // {pendientes, proximo} (HU-32)

  const refrescar = useCallback(async () => {
    try {
      const e = await api('/api/estado')
      const c = await api('/api/conversaciones')
      setEstado(e)
      setConvos(c.canales || {})
      if (e?.perfil) api('/api/repaso').then(setRepaso).catch(() => {})
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

  const abrirClase = (i) => { setDestacar(null); setClaseActiva(i); setVista('clase') }

  const entrarComoUsuario = async () => {
    try {
      const u = await api('/api/usuarios')
      setUsuario(u.usuarios.find((x) => x.id === u.activo) || null)
    } catch { /* opcional */ }
    setEstado(null)
    await refrescar()
    setVista('cursos')
  }

  // Navegación desde el buscador: activa el curso y abre la conversación.
  const irADesdeBusqueda = async (curso, canal, msgId) => {
    try {
      await api(`/api/cursos/${curso}/activar`, {}, 'POST')
      const e = await refrescar()
      if (!e?.perfil || canal === 'creacion') { setVista('creacion'); return }
      setDestacar(msgId ?? null)
      setClaseActiva(Number(canal.slice(1)) || 0)
      setVista('clase')
    } catch (e) { avisarError(e) }
  }

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
          <ThemeIcon size={30} radius="md" variant="filled" color="indigo">
            <Text fw={800} size="sm" ff="monospace">P</Text>
          </ThemeIcon>
          <Text fw={650} style={{ flex: 1 }} lts="-0.01em">Profe Bit</Text>
          {usuario && (
            <Tooltip label={`Estudiando como ${usuario.nombre} — clic para cambiar de perfil`}>
              <ActionIcon variant="subtle" color="gray" aria-label="Cambiar de perfil"
                onClick={() => setVista('usuarios')}>
                <Avatar size={22} radius="xl" color="indigo" variant="filled">
                  <Text size="10px" fw={700}>{usuario.nombre.trim()[0]?.toUpperCase()}</Text>
                </Avatar>
              </ActionIcon>
            </Tooltip>
          )}
          <Tooltip label="Buscar en todo (⌘K)">
            <ActionIcon variant="subtle" color="gray" aria-label="Buscar"
              onClick={() => spotlight.open()}><IconSearch size={17} stroke={1.8} /></ActionIcon>
          </Tooltip>
        </Group>

        {conCurso && (
          <Box px="xs" pb="xs">
            <Text size="xs" c="dimmed" mb={4}>
              {aprobadas} de {total} clases · {estado.lenguaje}
            </Text>
            <Progress value={total ? (100 * aprobadas) / total : 0} size="sm" radius="xl"
              color="teal" aria-label={`Progreso del curso: ${aprobadas} de ${total} clases aprobadas`} />
          </Box>
        )}

        <ScrollArea style={{ flex: 1 }}>
          <Stack gap={4}>
            <NavItem icono={<IconArrowLeft size={16} stroke={1.8} />} etiqueta="Mis cursos" sub="Todos tus cursos"
              onClick={async () => { await refrescar(); setVista('cursos') }} />
            {conCurso && (
              <>
                <Text size="xs" c="dimmed" fw={700} tt="uppercase" px="xs" mt="xs">Curso</Text>
                <NavItem icono={<IconFileDescription size={16} stroke={1.8} />} etiqueta="Diseño del curso" sub="Documento estructurado — editable"
                  activa={vista === 'diseno'} onClick={() => setVista('diseno')} />
                <NavItem icono={<IconChartLine size={16} stroke={1.8} />} etiqueta="Mi progreso" sub="Actividad, notas y conceptos"
                  activa={vista === 'stats'} onClick={() => setVista('stats')} />
                <NavItem icono={<IconRepeat size={16} stroke={1.8} />} etiqueta="Repaso del día"
                  sub={repaso?.pendientes ? `${repaso.pendientes} para repasar` : 'Al día'}
                  activa={vista === 'repaso'} onClick={() => setVista('repaso')} />
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
              <Tooltip label="Días seguidos estudiando">
                <Badge variant="light" color="orange" leftSection={<IconFlame size={12} />}>{estado.racha}</Badge>
              </Tooltip>
              <Tooltip label="Puntos por checkpoints y clases aprobadas">
                <Badge variant="light" color="yellow" leftSection={<IconStar size={12} />}>{estado.puntos}</Badge>
              </Tooltip>
            </Group>
          )}
        </Group>
      </AppShell.Navbar>

      <AppShell.Main>
        <BarraConexion />
        {vista === 'usuarios' && <Usuarios onElegir={entrarComoUsuario} />}
        {vista === 'cursos' && <MisCursos onEntrar={entrarCurso} onNuevo={nuevoCurso} />}
        {vista === 'creacion' && (
          <CreacionChat onCreado={async () => {
            const e = await refrescar()
            avisar('¡Tu curso está listo!')
            if (e?.perfil) { setClaseActiva(0); setVista('clase') }
          }} />
        )}
        {vista === 'diseno' && estado?.perfil && <Diseno onGuardado={refrescar} />}
        {vista === 'stats' && estado?.perfil && <Estadisticas irAClase={abrirClase} />}
        {vista === 'repaso' && estado?.perfil && <Repaso refrescar={refrescar} />}
        {vista === 'clase' && estado?.perfil && (
          <Clase key={`${estado.curso_id}-${claseActiva}`} indice={claseActiva}
            unidad={estado.unidades[claseActiva]} lenguaje={estado.lenguaje}
            refrescar={refrescar} irAClase={abrirClase}
            haySiguiente={claseActiva + 1 < total} destacar={destacar} />
        )}
      </AppShell.Main>
      <Buscador irA={irADesdeBusqueda} nuevoCurso={nuevoCurso}
        verProgreso={estado?.perfil ? () => setVista('stats') : null}
        verCursos={async () => { await refrescar(); setVista('cursos') }} />
    </AppShell>
  )
}

/** Spotlight global ⌘K (HU-37): clases, mensajes y acciones. */
function Buscador({ irA, nuevoCurso, verProgreso, verCursos }) {
  const [q, setQ] = useState('')
  const [res, setRes] = useState({ clases: [], mensajes: [] })

  useEffect(() => {
    if (q.trim().length < 2) { setRes({ clases: [], mensajes: [] }); return undefined }
    const t = setTimeout(() => {
      api(`/api/buscar?q=${encodeURIComponent(q.trim())}`).then(setRes).catch(() => {})
    }, 250)
    return () => clearTimeout(t)
  }, [q])

  const acciones = [
    {
      group: 'Clases',
      actions: res.clases.map((c) => ({
        id: `c-${c.curso}-${c.indice}`,
        label: `Clase ${c.indice + 1}: ${c.titulo}`,
        description: `${c.curso_nombre} · ${c.fragmento}`,
        onClick: () => irA(c.curso, `u${c.indice}`, null),
      })),
    },
    {
      group: 'Conversaciones',
      actions: res.mensajes.map((m) => ({
        id: `m-${m.curso}-${m.id}`,
        label: m.fragmento,
        description: `${m.curso_nombre} · ${m.canal === 'creacion' ? 'diseño del curso' : `clase ${Number(m.canal.slice(1)) + 1}`} · ${m.rol === 'yo' ? 'tú' : 'el tutor'}`,
        onClick: () => irA(m.curso, m.canal, m.id),
      })),
    },
    {
      group: 'Acciones',
      actions: [
        { id: 'a-cursos', label: 'Mis cursos', onClick: verCursos },
        { id: 'a-nuevo', label: 'Nuevo curso', onClick: nuevoCurso },
        ...(verProgreso
          ? [{ id: 'a-stats', label: 'Mi progreso', onClick: verProgreso }]
          : []),
      ],
    },
  ]

  return (
    <Spotlight
      actions={acciones.filter((g) => g.actions.length > 0)}
      query={q}
      onQueryChange={setQ}
      shortcut={['mod + K']}
      filter={(_query, todas) => todas}  // el backend ya filtró
      nothingFound="Nada por aquí — prueba con otras palabras"
      highlightQuery
      searchProps={{ placeholder: 'Buscar clases, mensajes, acciones…' }}
    />
  )
}

/** Barra fija de desconexión (HU-34): aparece ante errores de red y se va sola. */
function BarraConexion() {
  const [caida, setCaida] = useState(false)
  useEffect(() => {
    const marcar = () => setCaida(true)
    const listo = () => setCaida(false)
    window.addEventListener('tutor:red', marcar)
    window.addEventListener('offline', marcar)
    window.addEventListener('online', listo)
    return () => {
      window.removeEventListener('tutor:red', marcar)
      window.removeEventListener('offline', marcar)
      window.removeEventListener('online', listo)
    }
  }, [])
  useEffect(() => {
    if (!caida) return undefined
    // Ping ligero SOLO mientras está caída; al responder, la barra se va.
    const timer = setInterval(() => {
      fetch('/api/estado').then((r) => r.ok && setCaida(false)).catch(() => {})
    }, 30000)
    return () => clearInterval(timer)
  }, [caida])
  if (!caida) return null
  return (
    <Box py={6} ta="center" style={{ background: 'var(--mantine-color-yellow-light)' }}>
      <Text size="sm" fw={600}>⚠️ Sin conexión con el tutor — reintentando…</Text>
    </Box>
  )
}

function Preferencias({ escala, cambiarEscala }) {
  const { colorScheme, setColorScheme } = useMantineColorScheme()
  const siguiente = { dark: 'light', light: 'auto', auto: 'dark' }
  const icono = {
    dark: <IconMoon size={16} stroke={1.8} />,
    light: <IconSun size={16} stroke={1.8} />,
    auto: <IconDeviceDesktop size={16} stroke={1.8} />,
  }[colorScheme] ?? <IconDeviceDesktop size={16} stroke={1.8} />
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
  // component="button": navegable con Tab y activable con Enter/Espacio (HU-38)
  return (
    <Card component="button" type="button" p="xs" radius="md" withBorder={!!activa}
      onClick={onClick} aria-current={activa ? 'page' : undefined}
      style={{ cursor: 'pointer', width: '100%', textAlign: 'left', border: activa ? undefined : 'none', background: activa ? 'var(--mantine-color-default-hover)' : 'transparent' }}>
      <Group gap="sm" wrap="nowrap">
        {icono && <Box c="dimmed" style={{ display: 'flex' }}>{icono}</Box>}
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
    <Card component="button" type="button" p="xs" radius="md" withBorder={!!activa}
      onClick={onClick} disabled={bloqueada}
      aria-current={activa ? 'page' : undefined}
      aria-label={`Clase ${u.indice + 1}: ${u.titulo}. ${sub}`}
      opacity={bloqueada ? 0.45 : 1}
      style={{ cursor: bloqueada ? 'not-allowed' : 'pointer', width: '100%', textAlign: 'left', border: activa ? undefined : 'none', background: activa ? 'var(--mantine-color-default-hover)' : 'transparent' }}>
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
