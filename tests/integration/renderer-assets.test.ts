import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const rendererRoot = resolve(process.cwd(), 'src/renderer')
const indexHtml = readFileSync(resolve(rendererRoot, 'index.html'), 'utf8')
const mainCss = readFileSync(resolve(rendererRoot, 'assets/main.css'), 'utf8')

describe('renderer assets', () => {
  it('keeps the four state sections, title-bar controls, and manual cookie settings', () => {
    for (const id of [
      'title-bar',
      'drag-area',
      'minimize-btn',
      'close-btn',
      'input-section',
      'loading-section',
      'error-section',
      'info-section',
      'videoInfoForm',
      'videoInfoStatus',
      'settings-section',
      'settings-toggle-btn',
      'settings-content',
      'cookies-input',
      'cookies-configured',
      'settings-save-btn',
      'settings-clear-btn'
    ]) {
      expect(indexHtml).toContain(`id="${id}"`)
    }
    expect(indexHtml).toContain('Paste Netscape HTTP Cookie File content.')
    expect(indexHtml).toContain('Cookie values stay in the main process memory')
    expect(indexHtml).not.toContain('cookies-enabled')
    expect(indexHtml).not.toContain('browser-select')
  })

  it('uses bundled local styles and pixel font without remote dependencies', () => {
    const customCss = readFileSync(resolve(rendererRoot, 'assets/css/custom.css'), 'utf8')
    const fontPath = resolve(rendererRoot, 'assets/fonts/press-start-2p.woff2')
    expect(indexHtml).toContain('./assets/nes.css')
    expect(indexHtml).toContain('./assets/images/favicon.png')
    expect(indexHtml).not.toContain('https://unpkg.com/nes.css')
    expect(indexHtml).not.toContain('fonts.googleapis.com')
    expect(mainCss).toContain('./css/custom.css')
    expect(customCss).toContain("url('../fonts/press-start-2p.woff2')")
    expect(customCss).toContain("font-family: 'Press Start 2P', monospace")
    expect(existsSync(resolve(rendererRoot, 'assets/nes.css'))).toBe(true)
    expect(existsSync(resolve(rendererRoot, 'assets/css/custom.css'))).toBe(true)
    expect(existsSync(fontPath)).toBe(true)
    expect(readFileSync(fontPath).byteLength).toBeGreaterThan(0)
    expect(existsSync(resolve(rendererRoot, 'assets/images/favicon.png'))).toBe(true)
  })

  it('keeps thumbnail CSP restricted to HTTPS and local resources', () => {
    expect(indexHtml).toContain("default-src 'self'")
    expect(indexHtml).toContain("img-src 'self' data: https:")
    expect(indexHtml).not.toContain('connect-src *')
  })
})
