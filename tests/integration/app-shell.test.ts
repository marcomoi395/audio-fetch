import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it, vi } from 'vitest'
import {
  DEFAULT_WINDOW_CONFIG,
  focusExistingWindow,
  isSafeExternalUrl,
  resolveWindowConfig
} from '../../src/main/window-policy'
import { registerSingleInstance } from '../../src/main/single-instance'

describe('Audio Fetch app shell', () => {
  it('provides branded safe window defaults', () => {
    expect(DEFAULT_WINDOW_CONFIG).toEqual({
      width: 850,
      height: 650,
      title: 'Audio Fetch'
    })
    expect(isSafeExternalUrl('https://example.com')).toBe(true)
    expect(isSafeExternalUrl('file:///tmp/secret')).toBe(false)
    expect(isSafeExternalUrl('javascript:alert(1)')).toBe(false)
    expect(resolveWindowConfig({ width: 1024, title: 'Custom' })).toEqual({
      width: 1024,
      height: 650,
      title: 'Custom'
    })
    const builderConfig = readFileSync(resolve(process.cwd(), 'electron-builder.yml'), 'utf8')
    const windowSource = readFileSync(resolve(process.cwd(), 'src/main/window.ts'), 'utf8')
    const policySource = readFileSync(resolve(process.cwd(), 'src/main/window-policy.ts'), 'utf8')
    expect(builderConfig).toContain('appId: com.audiofetch.app')
    expect(builderConfig).toContain('productName: Audio Fetch')
    expect(windowSource).toContain('frame: false')
    expect(windowSource).toContain('contextIsolation: true')
    expect(windowSource).toContain('nodeIntegration: false')
    expect(policySource).toContain("protocol === 'http:' || protocol === 'https:'")
    expect(windowSource).toContain('shell.openExternal(url).catch')
  })

  it('restores and focuses a minimized existing window', () => {
    const existingWindow = {
      isMinimized: vi.fn(() => true),
      restore: vi.fn(),
      focus: vi.fn()
    }

    focusExistingWindow(existingWindow)

    expect(existingWindow.restore).toHaveBeenCalledOnce()
    expect(existingWindow.focus).toHaveBeenCalledOnce()
  })

  it('quits when the single-instance lock is unavailable', () => {
    const app = {
      requestSingleInstanceLock: vi.fn(() => false),
      quit: vi.fn(),
      on: vi.fn()
    }

    expect(registerSingleInstance(app, vi.fn())).toBe(false)
    expect(app.quit).toHaveBeenCalledOnce()
    expect(app.on).not.toHaveBeenCalled()
  })

  it('focuses the existing window on a second launch', () => {
    const listeners: Array<
      (event: unknown, commandLine: string[], workingDirectory: string) => void
    > = []
    const app = {
      requestSingleInstanceLock: vi.fn(() => true),
      quit: vi.fn(),
      on: vi.fn(
        (
          _event: 'second-instance',
          listener: (event: unknown, commandLine: string[], workingDirectory: string) => void
        ) => {
          listeners.push(listener)
        }
      )
    }
    const focusWindow = vi.fn()
    const argv = ['audio-fetch', '--url']
    const cwd = '/tmp'

    expect(registerSingleInstance(app, focusWindow)).toBe(true)
    expect(app.on).toHaveBeenCalledWith('second-instance', expect.any(Function))

    listeners[0]({}, argv, cwd)

    expect(focusWindow).toHaveBeenCalledWith(argv, cwd)
  })
})
