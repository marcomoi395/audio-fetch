import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const workflow = (name: string) =>
  readFileSync(resolve(process.cwd(), '.github/workflows', name), 'utf8')

describe('GitHub Actions workflow contract', () => {
  it('uses Bun quality gates and headless Electron E2E', () => {
    const ci = workflow('ci.yml')

    expect(ci).toContain('oven-sh/setup-bun@v2')
    expect(ci).toContain('bun install --frozen-lockfile')
    expect(ci).toContain('bun run typecheck')
    expect(ci).toContain('bun test')
    expect(ci).toContain('bun run lint')
    expect(ci).toContain('bun run test:coverage')
    expect(ci).toContain('bun run build')
    expect(ci).toContain('xvfb-run bun run test:e2e')
    expect(ci.indexOf('bun run build')).toBeLessThan(ci.indexOf('xvfb-run bun run test:e2e'))
  })

  it('builds Electron AppImage, deb, and Windows artifacts without Python or RPM', () => {
    const build = workflow('build.yml')

    expect(build).toContain('oven-sh/setup-bun@v2')
    expect(build).toContain('bun install --frozen-lockfile')
    expect(build).toContain('bun run build:linux')
    expect(build).toContain('bun run build:win')
    expect(build).toContain('path: dist/*.AppImage')
    expect(build).toContain('path: dist/*.deb')
    expect(build).toContain('path: dist/*.exe')
    expect(build).not.toMatch(/Python|PyInstaller|Qt|rpm/i)
  })

  it('updates package.json and refreshes bun.lock during release preparation', () => {
    const release = workflow('release.yml')

    expect(release).toContain('package.json')
    expect(release).toContain('bun install --lockfile-only --ignore-scripts')
    expect(release).toContain('git add package.json bun.lock')
    expect(release).not.toContain('pyproject.toml')
  })

  it('publishes only Electron artifacts from the post-merge release flow', () => {
    const builder = readFileSync(resolve(process.cwd(), 'electron-builder.yml'), 'utf8')
    const postMerge = workflow('post-merge-release.yml')

    expect(builder).toContain('- AppImage')
    expect(builder).toContain('- deb')
    expect(builder).not.toContain('- snap')
    expect(builder).not.toContain('- rpm')
    expect(postMerge).toContain('artifacts/linux-appimage/*.AppImage')
    expect(postMerge).toContain('artifacts/linux-deb/*.deb')
    expect(postMerge).toContain('artifacts/windows-installer/*.exe')
    expect(postMerge).not.toMatch(/pyproject|\.rpm|Firefox|Edge|ffmpeg is required/i)
  })
})
