import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

import { webdriverio } from '@vitest/browser-webdriverio'

export default defineConfig({
  plugins: [react()],
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
    // setupFiles: [
    //   './src/setupTests.tsx', // Adjust the path to your setup file
    // ],
  },
  server: {
    port: 3002,
    proxy: {
      '/api': {
        target: 'http://localhost:2337',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  
})
