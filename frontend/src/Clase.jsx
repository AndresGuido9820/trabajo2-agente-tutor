import { useEffect, useRef, useState } from 'react'
import {
  ActionIcon, Badge, Box, Button, Card, Group, Paper, Progress, Radio, Stack,
  Text, Textarea, Title, Tooltip,
} from '@mantine/core'
import { api, apiStream, guardarBorrador, leerBorrador } from './api.js'
import { avisar, avisarError } from './App.jsx'
import { Escribiendo, Mensaje, ZonaChat } from './Chat.jsx'
import Prosa from './Prosa.jsx'
import RetoCard from './RetoCard.jsx'

/** ¿El último mensaje es de hace más de `horas`? (HU-30, reencuentro). */
function pausaLarga(ultimoEn, horas) {
  if (!ultimoEn || !horas) return false
  const ms = Date.now() - new Date(ultimoEn).getTime()
  return Number.isFinite(ms) && ms > horas * 3600 * 1000
}

/** El chat de UNA clase: estudio, evaluación y conversatorio inline. */
export default function Clase({ indice, unidad, lenguaje, refrescar, irAClase, haySiguiente, destacar }) {
  const [mensajes, setMensajes] = useState([])       // {rol, texto} o {rol:'quiz'|'resultado'|'demo', ...}
  const [texto, setTexto] = useState(() => leerBorrador(`u${indice}`))
  const [ocupado, setOcupado] = useState(false)
  const [fallo, setFallo] = useState(null)           // {m} del último turno fallido (HU-34)
  const [espera, setEspera] = useState(null)         // texto del indicador
  const [modo, setModo] = useState('estudio')        // estudio | conversatorio
  const [avance, setAvance] = useState(null)         // {paso, total, objetivo?, objetivos_total?}
  const [finPendiente, setFinPendiente] = useState(false)  // fin-clase espera al mini-quiz (HU-24)
  const [panel, setPanel] = useState(null)           // {objetivos, progreso_pct, evaluacion_lista} (HU-25)
  const [panelAbierto, setPanelAbierto] = useState(() => window.innerWidth >= 900)
  const inicio = useRef(false)

  const cargarPanel = async () => {
    try { setPanel(await api(`/api/clase/${indice}/panel`)) } catch { /* sin panel */ }
  }

  const agregar = (m) => setMensajes((prev) => [...prev, m])

  useEffect(() => {
    if (inicio.current) return
    inicio.current = true
    ;(async () => {
      try {
        const h = await api(`/api/historial/u${indice}`)
        setMensajes(h.mensajes)
        if (h.mensajes.length === 0) {
          setEspera('Preparando tu clase (primera vez: ~1 min)…')
          const r = await api('/api/estudio', { unidad: indice })
          setEspera(null)
          agregar({ rol: 'tutor', texto: r.texto })
          setAvance({ paso: r.paso, total: r.total })
        } else if (pausaLarga(h.ultimo_en, h.horas_reencuentro)) {
          // HU-30: si pasaron horas desde el último mensaje, el tutor
          // resume dónde iban antes de retomar.
          setEspera('Recordando dónde íbamos…')
          const r = await api(`/api/clase/${indice}/reencuentro`, undefined, 'POST')
          setEspera(null)
          agregar({ rol: 'tutor', texto: r.texto })
        }
      } catch (e) { setEspera(null); avisarError(e) }
      cargarPanel()
      if (destacar) {
        // Llegamos desde el buscador (HU-37): scroll y resaltado 2 s.
        setTimeout(() => {
          const el = document.getElementById(`msg-${destacar}`)
          if (!el) return
          el.scrollIntoView({ block: 'center' })
          el.style.transition = 'background 0.4s'
          el.style.background = 'var(--mantine-color-yellow-light)'
          el.style.borderRadius = '12px'
          setTimeout(() => { el.style.background = 'transparent' }, 2000)
        }, 350)
      }
    })()
  }, [indice])

  const enviar = async (directo, esReintento = false) => {
    const m = (directo ?? texto).trim()
    if (!m || ocupado) return
    if (!esReintento) {
      setTexto('')
      agregar({ rol: 'yo', texto: m })
    }
    setFallo(null)
    setOcupado(true)
    setEspera('')
    // A los 2.5 min avisamos que va lento (el fetch aborta solo a los 3).
    const tardando = setTimeout(() => {
      setEspera('Esto está tardando más de lo normal — puedes seguir esperando o reintentar…')
    }, 150000)
    try {
      if (modo === 'conversatorio') {
        const r = await api(`/api/conversatorio/${indice}`, { mensaje: m })
        agregar({ rol: 'tutor', texto: r.texto })
      } else {
        const r = await turnoEstudio(m)
        setAvance({ paso: r.paso, total: r.total, objetivo: r.objetivo, objetivos_total: r.objetivos_total })
        // HU-24: al cerrar un objetivo llega su mini-quiz; el cierre de
        // clase espera a que se responda.
        if (r.reto) agregar({ rol: 'reto', reto: r.reto })  // HU-28
        if (r.quiz_intermedio) {
          agregar({ rol: 'quiz-mini', preguntas: r.quiz_intermedio })
          if (r.terminada) { await refrescar(); setFinPendiente(true) }
        } else if (r.terminada) {
          await refrescar()
          agregar({ rol: 'fin-clase' })
        }
        cargarPanel()
      }
      guardarBorrador(`u${indice}`, '')  // envío exitoso: borrador fuera
    } catch (e) {
      avisarError(e)
      setFallo({ m })  // reintenta EXACTAMENTE esta llamada, sin reescribir
    }
    clearTimeout(tardando)
    setEspera(null)
    setOcupado(false)
  }

  // Turno de estudio en vivo por SSE, con fallback al endpoint clásico (HU-35).
  const turnoEstudio = async (m) => {
    let fin = null
    let huboDelta = false
    try {
      await apiStream('/api/estudio/stream', { mensaje: m, unidad: indice }, {
        delta: (d) => {
          setEspera(null)
          if (!huboDelta) {
            huboDelta = true
            agregar({ rol: 'tutor', texto: d.texto })
          } else {
            setMensajes((prev) => {
              const copia = prev.slice()
              const ultimo = copia[copia.length - 1]
              copia[copia.length - 1] = { ...ultimo, texto: ultimo.texto + d.texto }
              return copia
            })
          }
        },
        fin: (d) => { fin = d },
        error: (d) => { throw new Error(d.detail) },
      })
    } catch (e) {
      // Fallback: se descarta la burbuja parcial y se rehace el turno clásico.
      if (huboDelta) setMensajes((prev) => prev.slice(0, -1))
      fin = null
    }
    if (!fin) {
      setEspera('')
      const r = await api('/api/estudio', { mensaje: m, unidad: indice })
      agregar({ rol: 'tutor', texto: r.texto })
      return r
    }
    // El texto final es la fuente de verdad (el stream pudo perder deltas).
    if (!huboDelta) {
      agregar({ rol: 'tutor', texto: fin.texto })
    } else {
      setMensajes((prev) => {
        const copia = prev.slice()
        copia[copia.length - 1] = { rol: 'tutor', texto: fin.texto }
        return copia
      })
    }
    return fin
  }

  const repasar = async () => {
    agregar({ rol: 'yo', texto: 'Quiero repasar esta clase desde el inicio' })
    setEspera('')
    try {
      const r = await api('/api/estudio', { unidad: indice })
      agregar({ rol: 'tutor', texto: r.texto })
      setAvance({ paso: r.paso, total: r.total, objetivo: r.objetivo, objetivos_total: r.objetivos_total })
      cargarPanel()  // el repaso puede regenerar el guion (v2 → panel)
    } catch (e) { avisarError(e) }
    setEspera(null)
  }

  const evaluar = async () => {
    agregar({ rol: 'yo', texto: 'Quiero presentar la evaluación' })
    setEspera('Escribiendo tus preguntas y verificándolas (~40 s)…')
    try {
      const quiz = await api(`/api/quiz/${indice}`, undefined, 'POST')
      agregar({ rol: 'quiz', preguntas: quiz.preguntas })
    } catch (e) { avisarError(e) }
    setEspera(null)
  }

  const calificar = async (respuestas) => {
    try {
      const r = await api(`/api/quiz/${indice}/calificar`, { respuestas })
      await refrescar()
      agregar({ rol: 'resultado', r })
      if (r.aprobado) {
        avisar(`+30 ⭐ · Clase ${indice + 1} aprobada`)
        setModo('estudio')
      } else {
        setModo('conversatorio')
        setEspera('')
        const c = await api(`/api/conversatorio/${indice}`, { mensaje: '' })
        agregar({ rol: 'tutor', texto: c.texto })
        setEspera(null)
      }
      return true
    } catch (e) { avisarError(e); return false }
  }

  // Mini-quiz de cierre de objetivo (HU-24): calificación en el servidor.
  const calificarMini = (preguntas) => async (respuestas) => {
    try {
      const r = await api('/api/estudio/quiz-intermedio', { unidad: indice, respuestas })
      agregar({ rol: 'tutor', texto: r.texto })
      if (r.repite) {
        agregar({ rol: 'quiz-mini', preguntas })  // mismo quiz, tras el repaso
        return true
      }
      if (r.aciertos > 0) avisar(`+${5 * r.aciertos} ⭐ por tu mini-quiz`)
      if (finPendiente) {
        setFinPendiente(false)
        agregar({ rol: 'fin-clase' })
      }
      cargarPanel()  // el panel marca el objetivo en vivo (HU-25)
      return true
    } catch (e) { avisarError(e); return false }
  }

  const demo = async (regenerar = false) => {
    if (!regenerar) agregar({ rol: 'yo', texto: '✨ Muéstrame una demo interactiva de esto' })
    setEspera('Creando tu demo interactiva (vale la pena: ~1-2 min)…')
    try {
      // La demo ilustra el objetivo que la conversación está trabajando (HU-27).
      const objetivo = avance?.objetivos_total ? avance.objetivo - 1 : null
      const r = await api('/api/artefacto', { unidad: indice, objetivo, regenerar })
      if (regenerar) {
        setMensajes((prev) => {
          const copia = prev.slice()
          for (let i = copia.length - 1; i >= 0; i--) {
            if (copia[i].rol === 'demo') { copia[i] = { ...copia[i], html: r.html }; break }
          }
          return copia
        })
      } else {
        agregar({ rol: 'demo', html: r.html, plantilla: r.plantilla })
      }
    } catch (e) { avisarError(e) }
    setEspera(null)
  }

  const coronada = unidad.completada || unidad.estado === 'aprobada'

  const hayPanel = panel && panel.objetivos.length > 0

  return (
    <Box style={{ display: 'flex', flexDirection: 'row', height: '100vh' }}>
    <Box style={{ display: 'flex', flexDirection: 'column', height: '100vh', flex: 1, minWidth: 0 }}>
      <Group px="lg" py="sm" style={{ borderBottom: '1px solid var(--mantine-color-default-border)' }}>
        <Title order={5}>Clase {indice + 1}: {unidad.titulo}</Title>
        <Text size="xs" c="dimmed" truncate style={{ flex: 1 }}>
          {(unidad.conceptos || []).join(' · ')}
        </Text>
        {avance?.objetivos_total && (
          <Badge variant="light" color="teal">objetivo {avance.objetivo}/{avance.objetivos_total}</Badge>
        )}
        {avance && <Badge variant="light">paso {avance.paso}/{avance.total}</Badge>}
        {hayPanel && (
          <Tooltip label={panelAbierto ? 'Ocultar panel' : 'Ver objetivos de la clase'}>
            <ActionIcon variant="subtle" color="gray" aria-label="Mostrar u ocultar el panel de objetivos"
              onClick={() => setPanelAbierto(!panelAbierto)}>≡</ActionIcon>
          </Tooltip>
        )}
      </Group>

      <ZonaChat dep={mensajes.length + (espera !== null ? 1 : 0)}>
        {mensajes.map((m, i) => {
          if (m.rol === 'quiz') return <QuizCard key={i} preguntas={m.preguntas} onCalificar={calificar} indice={indice} />
          if (m.rol === 'reto') return (
            <RetoCard key={i} reto={m.reto} unidad={indice}
              onSuperado={async (texto) => { agregar({ rol: 'tutor', texto }); await refrescar() }}
              onMensaje={(texto) => agregar({ rol: 'tutor', texto })} />
          )
          if (m.rol === 'quiz-mini') return (
            <QuizCard key={i} preguntas={m.preguntas} indice={indice}
              titulo="⚡ MINI-QUIZ · CIERRE DE OBJETIVO"
              onCalificar={calificarMini(m.preguntas)} />
          )
          if (m.rol === 'resultado') return <ResultadoCard key={i} r={m.r} onSiguiente={haySiguiente ? () => irAClase(indice + 1) : null} onReintentar={evaluar} />
          if (m.rol === 'demo') return (
            <Mensaje key={i} rol="tutor" ancho>
              <Group justify="space-between" mb="xs">
                <Group gap={6}>
                  <Text size="xs" c="dimmed" fw={700}>✨ DEMO INTERACTIVA — JUEGA CON ELLA</Text>
                  {m.plantilla && <Badge size="xs" variant="light">{m.plantilla}</Badge>}
                </Group>
                <Button size="compact-xs" variant="subtle" disabled={espera !== null}
                  onClick={() => demo(true)}>🔄 Regenerar</Button>
              </Group>
              <iframe sandbox="allow-scripts" srcDoc={m.html}
                title="Demo interactiva generada por el tutor"
                style={{ width: '100%', height: 460, border: '1px solid var(--mantine-color-default-border)', borderRadius: 12, background: '#0a0d13' }} />
            </Mensaje>
          )
          if (m.rol === 'fin-clase') return (
            <Mensaje key={i} rol="tutor" ancho>
              <Text fw={700} mb="xs">🎉 ¡Clase completada! Quedó tachada en tu lista.</Text>
              <Group gap="xs">
                <Button size="xs" onClick={evaluar}>🎯 Presentar la evaluación</Button>
              </Group>
            </Mensaje>
          )
          return (
            <Box key={i} id={m.id ? `msg-${m.id}` : undefined}>
              <Mensaje rol={m.rol} lenguaje={lenguaje}>{m.texto}</Mensaje>
            </Box>
          )
        })}
        {espera !== null && <Escribiendo texto={espera || undefined} />}
        {fallo && (
          <Group justify="flex-end" gap="xs">
            <Text size="xs" c="red.5">⚠️ No enviado</Text>
            <Button size="compact-xs" variant="default" disabled={ocupado}
              onClick={() => enviar(fallo.m, true)}>
              Reintentar
            </Button>
          </Group>
        )}
      </ZonaChat>

      <Box p="md" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
        <Box maw={760} mx="auto">
          <Group gap="xs" mb="xs">
            {modo === 'conversatorio' && (
              <Button variant="default" size="compact-xs" radius="xl" onClick={evaluar}>
                Ya estoy listo: reintentar 🎯
              </Button>
            )}
            {coronada && modo === 'estudio' && (
              <>
                <Button variant="default" size="compact-xs" radius="xl" onClick={evaluar}>🎯 Evaluarme</Button>
                <Button variant="default" size="compact-xs" radius="xl" onClick={repasar}>↩ Repasar desde el inicio</Button>
              </>
            )}
          </Group>
          <Group align="flex-end" gap="xs">
            <Textarea
              style={{ flex: 1 }} radius="lg" autosize minRows={1} maxRows={5}
              placeholder={modo === 'conversatorio' ? 'Tu respuesta o tu duda…' : 'Responde al tutor o pregunta lo que quieras…'}
              value={texto}
              onChange={(e) => {
                setTexto(e.target.value)
                guardarBorrador(`u${indice}`, e.target.value)
              }}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar() } }}
              autoFocus
            />
            <Button variant="default" radius="lg" onClick={() => demo()}
              title="Pídele una demo interactiva"
              aria-label="Pedir una demo interactiva de esta clase">✨</Button>
            <Button radius="lg" onClick={() => enviar()} loading={ocupado}>Enviar</Button>
          </Group>
        </Box>
      </Box>
    </Box>
    {hayPanel && panelAbierto && (
      <PanelClase panel={panel} indiceClase={indice} onEvaluar={evaluar} onDemo={() => demo()}
        onRepasar={(texto) => enviar(`Quiero repasar este objetivo: ${texto}`)} />
    )}
    </Box>
  )
}

/** Panel lateral de la clase: objetivos en vivo + progreso + CTAs (HU-25). */
/** Ilustración de la clase (HU-08, bonus): solo aparece si el flag está activo. */
function IlustracionClase({ indice }) {
  const [visible, setVisible] = useState(true)
  if (!visible) return null
  return (
    <img src={`/api/clase/${indice}/imagen`}
      alt={`Ilustración de la clase ${indice + 1}`}
      onError={() => setVisible(false)}
      style={{ width: '100%', borderRadius: 12, marginBottom: 12 }} />
  )
}

function PanelClase({ panel, onEvaluar, onDemo, onRepasar, indiceClase }) {
  const iconos = { cumplido: '●', en_curso: '◐', pendiente: '○' }
  return (
    <Box w={330} p="md" style={{
      borderLeft: '1px solid var(--mantine-color-default-border)',
      height: '100vh', overflowY: 'auto', flexShrink: 0,
    }}>
      <IlustracionClase indice={indiceClase} />
      <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">Objetivos de la clase</Text>
      <Stack gap={8} mb="lg">
        {panel.objetivos.map((o, k) => (
          <Group key={k} gap={8} wrap="nowrap" align="flex-start">
            <Text c={o.estado === 'cumplido' ? 'teal' : o.estado === 'en_curso' ? 'indigo' : 'dimmed'}>
              {iconos[o.estado]}
            </Text>
            <Box style={{ minWidth: 0, flex: 1 }}>
              <Text size="sm" td={o.estado === 'cumplido' ? 'line-through' : undefined}
                c={o.estado === 'cumplido' ? 'dimmed' : undefined}>
                {o.texto}
              </Text>
              {o.quiz && (
                <Group gap={6}>
                  <Badge size="xs" variant="light" color={o.repaso ? 'orange' : 'teal'}>
                    {o.repaso ? '↻' : '✓'} {o.quiz}
                  </Badge>
                  <Button size="compact-xs" variant="subtle"
                    onClick={() => onRepasar(o.texto)}>repasar</Button>
                </Group>
              )}
            </Box>
          </Group>
        ))}
      </Stack>

      <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb="xs">Progreso</Text>
      <Progress value={panel.progreso_pct} size="lg" radius="xl" color="teal" mb={4}
        aria-label={`Progreso de la clase: ${panel.progreso_pct} por ciento`} />
      <Text size="xs" c="dimmed" mb="lg">{panel.progreso_pct} % de la clase</Text>

      <Stack gap="xs">
        <Tooltip disabled={panel.evaluacion_lista}
          label={`Cumple los ${panel.objetivos.length} objetivos para presentar`}>
          <Button fullWidth disabled={!panel.evaluacion_lista} onClick={onEvaluar}>
            🎯 Evaluación final
          </Button>
        </Tooltip>
        <Button fullWidth variant="default" onClick={onDemo}>✨ Demo interactiva</Button>
      </Stack>
    </Box>
  )
}

export function QuizCard({ preguntas, onCalificar, indice, titulo }) {
  const [respuestas, setRespuestas] = useState(Array(preguntas.length).fill(null))
  const [error, setError] = useState('')
  const [listo, setListo] = useState(false)
  const [enviando, setEnviando] = useState(false)

  const calificar = async () => {
    const faltan = respuestas.map((r, i) => (r === null ? i + 1 : null)).filter(Boolean)
    if (faltan.length) { setError(`Te falta responder: ${faltan.join(', ')}.`); return }
    setEnviando(true)
    if (await onCalificar(respuestas.map(Number))) setListo(true)
    setEnviando(false)
  }

  return (
    <Mensaje rol="tutor" ancho>
      <Text size="xs" c="dimmed" fw={700} mb={4}>{titulo || `🎯 EVALUACIÓN · CLASE ${indice + 1}`}</Text>
      <Text size="sm" c="dimmed" mb="md">Apruebas con 70+. Puedes reintentar con preguntas nuevas.</Text>
      <Stack gap="md">
        {preguntas.map((p, i) => (
          <Card key={i} withBorder radius="md" p="md">
            <Group gap={6} mb={6}>
              <Text size="xs" c="dimmed" fw={700}>PREGUNTA {i + 1} DE {preguntas.length}</Text>
              {p.nivel && (
                <Badge size="xs" variant="light"
                  color={{ recordar: 'gray', comprender: 'indigo', aplicar: 'grape' }[p.nivel]}>
                  {p.nivel}
                </Badge>
              )}
            </Group>
            <Prosa>{p.enunciado}</Prosa>
            <Radio.Group value={respuestas[i] ?? undefined}
              onChange={(v) => { const r = respuestas.slice(); r[i] = v; setRespuestas(r) }}>
              <Stack gap="xs" mt="sm">
                {p.opciones.map((op, j) => (
                  <Radio key={j} value={String(j)} disabled={listo}
                    label={<Prosa>{op}</Prosa>} />
                ))}
              </Stack>
            </Radio.Group>
          </Card>
        ))}
      </Stack>
      {error && <Text c="red.4" size="sm" mt="sm">{error}</Text>}
      {!listo && <Button mt="md" onClick={calificar} loading={enviando}>Calificar</Button>}
    </Mensaje>
  )
}

function ResultadoCard({ r, onSiguiente, onReintentar }) {
  return (
    <Mensaje rol="tutor" ancho>
      {r.aprobado ? (
        <>
          <Title order={4} c="teal.4">🎉 Aprobada · {r.nota}/100</Title>
          <Text size="sm" c="dimmed" mb="md">Desbloqueaste la siguiente clase (+30 ⭐).</Text>
        </>
      ) : (
        <>
          <Title order={4}>{r.detalle.filter((d) => d.acierto).length} de {r.detalle.length} — cerremos esas brechas</Title>
          <Text size="sm" c="dimmed" mb="md">Conversemos tus dudas aquí mismo y reintentas con preguntas nuevas.</Text>
        </>
      )}
      <Stack gap="xs">
        {r.detalle.map((d, i) => (
          <Card key={i} withBorder radius="md" p="sm">
            <Text size="sm">{d.acierto ? '✅' : '❌'} <b>P{i + 1}</b> — elegiste: {d.elegida}</Text>
            {!d.acierto && <Text size="sm">Correcta: <Text span c="teal.4">{d.correcta}</Text></Text>}
            <Text size="xs" c="dimmed" mt={4}>{d.explicacion}</Text>
          </Card>
        ))}
      </Stack>
      {r.resumen_conceptos && (
        <Group gap={6} mt="md">
          {Object.entries(r.resumen_conceptos).map(([c, [ok, total]]) => (
            <Badge key={c} variant="light" color={ok === total ? 'teal' : 'orange'}>
              {c} {ok}/{total}
            </Badge>
          ))}
          {Object.entries(r.resumen_niveles || {}).map(([n, [ok, total]]) => (
            <Badge key={n} variant="outline" color={ok === total ? 'teal' : 'orange'}>
              {n} {ok}/{total}
            </Badge>
          ))}
        </Group>
      )}
      <Group gap="xs" mt="md">
        {r.aprobado && onSiguiente && <Button onClick={onSiguiente}>Ir a la siguiente clase →</Button>}
        {r.aprobado && !onSiguiente && <Text fw={700} c="teal.4">🏆 ¡Terminaste el curso completo!</Text>}
        {!r.aprobado && <Button variant="default" onClick={onReintentar}>Reintentar (preguntas nuevas)</Button>}
      </Group>
    </Mensaje>
  )
}
