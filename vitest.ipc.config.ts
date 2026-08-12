import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'node',
    coverage: {
      provider: 'v8',
      include: ['src/main/ipc/index.ts'],
      thresholds: { statements: 80, lines: 80, functions: 80, branches: 70 },
      reporter: ['text', 'json-summary']
    }
  }
})
