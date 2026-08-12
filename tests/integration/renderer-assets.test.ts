import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const rendererRoot = resolve(process.cwd(), 'src/renderer')
const indexHtml = readFileSync(resolve(rendererRoot, 'index.html'), 'utf8')
const mainCss = readFileSync(resolve(rendererRoot, 'assets/main.css'), 'utf8')

describe('legacy renderer assets', () => {
  it('keeps the four state sections and title-bar controls', () => {
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
      'videoInfoStatus'
    ]) {
      expect(indexHtml).toContain(`id="${id}"`)
    }
  })

  it('uses bundled local styles and favicon without remote CSS/font dependencies', () => {
    expect(indexHtml).toContain('./assets/nes.css')
    expect(indexHtml).toContain('./assets/images/favicon.png')
    expect(indexHtml).not.toContain('https://unpkg.com/nes.css')
    expect(indexHtml).not.toContain('fonts.googleapis.com')
    expect(mainCss).toContain('./css/custom.css')
    expect(existsSync(resolve(rendererRoot, 'assets/nes.css'))).toBe(true)
    expect(existsSync(resolve(rendererRoot, 'assets/css/custom.css'))).toBe(true)
    expect(existsSync(resolve(rendererRoot, 'assets/images/favicon.png'))).toBe(true)
  })

  it('keeps thumbnail CSP restricted to HTTPS and local resources', () => {
    expect(indexHtml).toContain("default-src 'self'")
    expect(indexHtml).toContain("img-src 'self' data: https:")
    expect(indexHtml).not.toContain('connect-src *')
  })
})
