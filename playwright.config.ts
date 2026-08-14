import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  projects: [{ name: 'electron', testMatch: /.*\.e2e\.ts/ }]
})
