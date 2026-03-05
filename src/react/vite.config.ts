import { defineConfig } from 'vitest/config'
import { loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

import { webdriverio } from '@vitest/browser-webdriverio'

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, process.cwd(), '');

  const baseURL = env.VITE_BASE_URL === "/" ? "" : env.VITE_BASE_URL || "";

  return {
  plugins: [react()],
  base: baseURL,
  test: {
    browser: {
      enabled: true,
      provider: webdriverio(),
      instances: [
        {
          browser: 'firefox',
          // overriding options only for a single instance
          // this will NOT merge options with the parent one
          provider: webdriverio({
            capabilities: {
              'moz:firefoxOptions': {
                args: ['--headless'],
              },
            },
          })
        },
      ],
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
