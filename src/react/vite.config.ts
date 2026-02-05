import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,
    proxy: {
      '/api': {
        target: 'http://localhost:2337',
        changeOrigin: true,
      },
      '/api/v1/socket/events': {
        target: 'ws://localhost:2337',
        changeOrigin: true,
        ws: true
      }
    }
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  }
})
