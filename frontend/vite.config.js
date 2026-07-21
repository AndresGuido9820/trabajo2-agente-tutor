import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El build se sirve desde FastAPI (src/tutor/static/dist); en dev, el
// proxy apunta al backend local.
export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: '../src/tutor/static/dist',
    emptyOutDir: true,
  },
  server: {
    proxy: { '/api': 'http://127.0.0.1:8017' },
  },
})
