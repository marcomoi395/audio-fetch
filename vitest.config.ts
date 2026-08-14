import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'node',
    coverage: {
      provider: 'v8',
      include: [
        'src/main/services/**/*.ts',
        'src/main/ipc/index.ts',
        'src/renderer/src/app.ts',
        'src/renderer/src/audio.ts',
        'src/shared/ipc.ts',
        'src/preload/api.ts'
      ],
      exclude: ['**/*.d.ts'],
      thresholds: {
        statements: 85,
        branches: 75,
        functions: 80,
        lines: 85
      },
      reporter: ['text', 'json-summary']
    }
  }
})
