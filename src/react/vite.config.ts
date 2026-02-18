import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { playwright } from '@vitest/browser-playwright'
import { webdriverio } from '@vitest/browser-webdriverio'

export default defineConfig({
  plugins: [react()],
  test: {
    browser: {
      enabled: true,
       provider: playwright(),
      instances: [{ browser: 'chromium', headless: true}],
    },
  },
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
  },
  
})
