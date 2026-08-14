import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'node',
    coverage: {
      provider: 'v8',
      include: ['src/main/services/**/*.ts'],
      thresholds: { statements: 85, lines: 85, functions: 80, branches: 75 },
      reporter: ['text', 'json-summary']
    }
  }
})
