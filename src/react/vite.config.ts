import { defineConfig } from 'vitest/config'
import { loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { playwright } from '@vitest/browser-playwright'

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, process.cwd(), '');

  const baseURL = env.VITE_BASE_URL === "/" ? "" : env.VITE_BASE_URL || "";

  return {
  plugins: [react()],
  base: baseURL,
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
      [`${baseURL}/api`]: {
        target: 'http://localhost:2337',
        changeOrigin: true,
        rewrite: (path) => path.replace(new RegExp(`^${baseURL}`), '')
      },
      [`${baseURL}/api/v1/socket/events`]: {
        target: 'ws://localhost:2337',
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(new RegExp(`^${baseURL}`), '')
      },
      [`${baseURL}/config`]: {
        target: 'http://localhost:2337',
        changeOrigin: true,
        rewrite: (path) => path.replace(new RegExp(`^${baseURL}`), '')
      },
      [`${baseURL}/version`]: {
        target: 'http://localhost:2337',
        changeOrigin: true,
        rewrite: (path) => path.replace(new RegExp(`^${baseURL}`), '')
      },
    }
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  
}})
