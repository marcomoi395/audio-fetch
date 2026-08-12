import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('integration test harness', () => {
  it('configures Vitest roots and Playwright for Electron', () => {
    const vitestConfig = readFileSync(resolve(process.cwd(), 'vitest.config.ts'), 'utf8')
    const playwrightConfig = readFileSync(resolve(process.cwd(), 'playwright.config.ts'), 'utf8')

    expect(vitestConfig).toContain("include: ['tests/**/*.test.ts']")
    expect(vitestConfig).toContain("environment: 'node'")
    expect(playwrightConfig).toContain("testDir: './tests/e2e'")
    expect(playwrightConfig).toContain("name: 'electron'")
  })
})
