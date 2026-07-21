import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import {
  MantineProvider, createTheme, localStorageColorSchemeManager,
} from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import './global.css'
import App from './App.jsx'

// Preferencias locales (HU-36): tema y tamaño de texto persistidos.
const gestorEsquema = localStorageColorSchemeManager({ key: 'tutor-tema' })

export const ESCALAS = { chico: 0.92, normal: 1, grande: 1.1 }

function leerEscala() {
  const guardada = localStorage.getItem('tutor-escala')
  return guardada && ESCALAS[guardada] ? guardada : 'normal'
}

function Raiz() {
  const [escala, setEscala] = useState(leerEscala)
  const cambiarEscala = (nombre) => {
    localStorage.setItem('tutor-escala', nombre)
    setEscala(nombre)
  }
  const tema = createTheme({
    primaryColor: 'indigo',
    // Tono 7 en claro: el 6 con texto blanco no alcanza AA (HU-38).
    primaryShade: { light: 7, dark: 6 },
    defaultRadius: 'md',
    scale: ESCALAS[escala],
    respectReducedMotion: true,
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif',
    headings: { fontWeight: '700' },
  })
  return (
    <MantineProvider theme={tema} defaultColorScheme="auto"
      colorSchemeManager={gestorEsquema}>
      <Notifications position="bottom-center" />
      <App escala={escala} cambiarEscala={cambiarEscala} />
    </MantineProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Raiz />
  </React.StrictMode>,
)
