import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'node',
    coverage: {
      provider: 'v8',
      include: ['src/renderer/src/app.ts', 'src/renderer/src/audio.ts'],
      thresholds: { statements: 75, lines: 75, functions: 75, branches: 75 },
      reporter: ['text', 'json-summary']
    }
  }
})
