import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('unit test harness', () => {
  it('defines the Bun-backed test and build scripts', () => {
    const packageJson = JSON.parse(
      readFileSync(resolve(process.cwd(), 'package.json'), 'utf8')
    ) as {
      scripts?: Record<string, string>
      dependencies?: Record<string, string>
      devDependencies?: Record<string, string>
    }

    expect(packageJson.scripts).toMatchObject({
      test: 'bunx vitest run',
      'test:coverage': 'bunx vitest run --coverage',
      'test:watch': 'bunx vitest',
      'test:e2e': 'bunx playwright test',
      build: 'bun run typecheck && bunx electron-vite build',
      'build:unpack': 'bun run build && bunx electron-builder --dir',
      'build:win': 'bun run build && bunx electron-builder --win',
      'build:linux': 'bun run build && bunx electron-builder --linux'
    })
    expect(packageJson.scripts).not.toHaveProperty('build:mac')
    expect(packageJson.dependencies).toMatchObject({
      'youtube-dl-exec': expect.any(String),
      '@ffmpeg-installer/ffmpeg': expect.any(String)
    })
    expect(packageJson.devDependencies).toMatchObject({
      vitest: expect.any(String),
      '@vitest/coverage-v8': expect.any(String),
      '@playwright/test': expect.any(String)
    })
  })
})
