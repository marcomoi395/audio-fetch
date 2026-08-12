import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it, vi } from 'vitest'
import { DEFAULT_CONFIG, loadConfig, saveConfig } from '../../src/main/services/config'

describe('Audio Fetch config', () => {
  it('loads the exact SPEC defaults when config is missing', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))

    await expect(loadConfig(join(directory, 'config.json'))).resolves.toEqual({
      schemaVersion: 1,
      downloads: { defaultPath: '', format: 'mp3', quality: '0' },
      tierStrategy: {
        browser: 'chrome',
        fallbackEnabled: true,
        tier1Attempts: 3,
        tier3Enabled: false
      },
      ui: { windowWidth: 850, windowHeight: 650, windowTitle: 'Audio Fetch' },
      logging: { level: 'WARNING', maxBytes: 10485760, backupCount: 3 }
    })
  })

  it('falls back safely and logs a reason for malformed JSON', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'config.json')
    const log = vi.fn()
    await writeFile(path, '{"token":"secret-token"', 'utf8')

    await expect(loadConfig(path, log)).resolves.toEqual(DEFAULT_CONFIG)
    expect(log).toHaveBeenCalledOnce()
    expect(log.mock.calls[0][0]).toContain('Invalid config')
    expect(log.mock.calls[0][0]).not.toContain('secret-token')
  })

  it('falls back safely for an invalid schema and logs a safe reason', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'config.json')
    const log = vi.fn()
    await writeFile(path, '{"schemaVersion":2}', 'utf8')

    await expect(loadConfig(path, log)).resolves.toEqual(DEFAULT_CONFIG)
    expect(log).toHaveBeenCalledOnce()
    expect(log.mock.calls[0][0]).toContain('Invalid config')
  })

  it('ignores legacy config files when the canonical file is absent', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const log = vi.fn()
    await writeFile(
      join(directory, 'legacy-config.json'),
      JSON.stringify({ downloads: { default_path: '/legacy' } }),
      'utf8'
    )

    await expect(loadConfig(join(directory, 'config.json'), log)).resolves.toEqual(DEFAULT_CONFIG)
    expect(log).not.toHaveBeenCalled()
  })

  it('round-trips valid non-default settings', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'nested', 'config.json')
    const config = {
      ...DEFAULT_CONFIG,
      downloads: { defaultPath: '/downloads', format: 'opus', quality: '5' },
      tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, browser: 'brave', tier1Attempts: 2 },
      ui: { ...DEFAULT_CONFIG.ui, windowWidth: 1024, windowTitle: 'Custom' },
      logging: { ...DEFAULT_CONFIG.logging, backupCount: 5 }
    }

    await saveConfig(path, config)

    await expect(loadConfig(path)).resolves.toEqual(config)
  })

  it('saves parent directories asynchronously and reloads', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'nested', 'config.json')
    const config = { ...DEFAULT_CONFIG, ui: { ...DEFAULT_CONFIG.ui, windowTitle: 'Custom' } }

    await saveConfig(path, config)

    await expect(readFile(path, 'utf8')).resolves.toContain('Custom')
    await expect(loadConfig(path)).resolves.toEqual(config)
  })
})
