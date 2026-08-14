import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it, vi } from 'vitest'
import { DEFAULT_CONFIG, loadConfig, saveConfig } from '../../src/main/services/config'

describe('Audio Fetch config', () => {
  it('loads defaults without cookie fields', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    await expect(loadConfig(join(directory, 'config.json'))).resolves.toEqual(DEFAULT_CONFIG)
    expect(JSON.stringify(DEFAULT_CONFIG)).not.toContain('cookie')
  })

  it('falls back safely for malformed JSON', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'config.json')
    const log = vi.fn()
    await writeFile(path, '{"token":"secret-token"', 'utf8')
    await expect(loadConfig(path, log)).resolves.toEqual(DEFAULT_CONFIG)
    expect(log).toHaveBeenCalledWith('Invalid config; using defaults')
    expect(log.mock.calls[0][0]).not.toContain('secret-token')
  })

  it('rejects legacy browser-cookie config fields', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'config.json')
    await writeFile(
      path,
      JSON.stringify({
        ...DEFAULT_CONFIG,
        tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, browser: 'chrome', cookiesEnabled: true }
      }),
      'utf8'
    )
    await expect(loadConfig(path)).resolves.toEqual(DEFAULT_CONFIG)
  })

  it('round-trips valid non-default settings', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'nested', 'config.json')
    const config = {
      ...DEFAULT_CONFIG,
      downloads: { defaultPath: '/downloads', format: 'opus', quality: '5' },
      tierStrategy: {
        ...DEFAULT_CONFIG.tierStrategy,
        tier1Attempts: 2,
        mobileFallbackEnabled: false
      },
      ui: { ...DEFAULT_CONFIG.ui, windowWidth: 1024, windowTitle: 'Custom' },
      logging: { ...DEFAULT_CONFIG.logging, backupCount: 5 }
    }
    await saveConfig(path, config)
    await expect(loadConfig(path)).resolves.toEqual(config)
  })

  it('saves parent directories asynchronously', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-config-'))
    const path = join(directory, 'nested', 'config.json')
    await saveConfig(path, {
      ...DEFAULT_CONFIG,
      ui: { ...DEFAULT_CONFIG.ui, windowTitle: 'Custom' }
    })
    await expect(readFile(path, 'utf8')).resolves.toContain('Custom')
  })
})
