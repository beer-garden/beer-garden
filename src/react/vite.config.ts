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
      '/config': {
        target: 'http://localhost:2337',
        changeOrigin: true,
      },
      '/version': {
        target: 'http://localhost:2337',
        changeOrigin: true,
      },
    }
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  }
})
