import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['tests/unit/tier-strategy.test.ts', 'tests/unit/queue.test.ts'],
    environment: 'node',
    coverage: {
      provider: 'v8',
      include: ['src/main/services/tier-strategy.ts', 'src/main/services/queue.ts'],
      thresholds: { statements: 100, lines: 100, functions: 100, branches: 85 },
      reporter: ['text']
    }
  }
})
