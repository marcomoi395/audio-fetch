import { describe, expect, it, vi } from 'vitest'
import {
  IPC_CHANNELS,
  registerIpcHandlers,
  type IpcHandler,
  type IpcMainLike
} from '../../src/main/ipc'
import { createIpcServices } from '../../src/main/ipc/services'
import { DEFAULT_CONFIG } from '../../src/main/services/config'

const registerForTest = (handlers: Map<string, IpcHandler>): IpcMainLike => ({
  handle: vi.fn((channel, handler) => handlers.set(channel, handler))
})

describe('download IPC flow', () => {
  it('starts one download and exposes safe queue status', async () => {
    const executor = vi.fn().mockResolvedValue('/downloads/song.mp3\n')
    const services = createIpcServices(() => undefined, '/downloads', executor)
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )

    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.(
        { sender: {} },
        { url: 'https://youtube.com/watch?v=test', options: { format: 'mp3', quality: '0' } }
      )
    ).resolves.toEqual({ ok: true, data: { path: '/downloads/song.mp3' } })
    await expect(handlers.get(IPC_CHANNELS.queueStatus)?.({ sender: {} })).resolves.toEqual({
      ok: true,
      data: { active: false }
    })
  })

  it('falls back to Tier 3 and preserves fixed yt-dlp options', async () => {
    const executor = vi
      .fn()
      .mockRejectedValueOnce({ stderr: 'HTTP Error 403: Forbidden', exitCode: 1 })
      .mockResolvedValueOnce('/downloads/fallback.mp3\n')
    const services = createIpcServices(() => undefined, '/downloads', executor, {
      ...DEFAULT_CONFIG,
      tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, tier1Attempts: 1, tier3Enabled: true }
    })
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )

    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.(
        { sender: {} },
        { url: 'https://youtube.com/watch?v=test', options: { format: 'mp3', quality: '5' } }
      )
    ).resolves.toEqual({ ok: true, data: { path: '/downloads/fallback.mp3' } })
    expect(executor).toHaveBeenCalledTimes(2)
    expect(executor.mock.calls[0][1]).toMatchObject({
      output: '/downloads/%(title)s.%(ext)s',
      print: 'after_move:filepath',
      format: 'bestaudio/best',
      audioFormat: 'mp3',
      audioQuality: '192'
    })
    expect(executor.mock.calls[1][1]).toMatchObject({
      output: '/downloads/%(title)s.%(ext)s',
      print: 'after_move:filepath',
      format: 'bestaudio/best',
      audioFormat: 'mp3',
      audioQuality: '192',
      extractorArgs: 'youtube:player_client=android'
    })
    expect(executor.mock.calls[1][1]).not.toHaveProperty('cookiesFromBrowser')
  })
  it('uses Tier 2 cookies only after explicit opt-in and browser detection', async () => {
    const executor = vi
      .fn()
      .mockRejectedValueOnce({ stderr: 'HTTP Error 403: Forbidden', exitCode: 1 })
      .mockResolvedValueOnce('/downloads/cookie.mp3\n')
    const services = createIpcServices(
      () => undefined,
      '/downloads',
      executor,
      {
        ...DEFAULT_CONFIG,
        tierStrategy: {
          ...DEFAULT_CONFIG.tierStrategy,
          cookiesEnabled: true,
          tier1Attempts: 1,
          tier3Enabled: true
        }
      },
      '',
      { findInstalledBrowsers: () => ['chrome'] }
    )
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )

    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.(
        { sender: {} },
        { url: 'https://youtube.com/watch?v=test', options: { format: 'mp3', quality: '0' } }
      )
    ).resolves.toEqual({ ok: true, data: { path: '/downloads/cookie.mp3' } })
    expect(executor.mock.calls[1][1]).toMatchObject({ cookiesFromBrowser: 'chrome' })
  })

  it('skips unavailable Tier 2 cookies and continues to Tier 3', async () => {
    const executor = vi
      .fn()
      .mockRejectedValueOnce({ stderr: 'HTTP Error 403: Forbidden', exitCode: 1 })
      .mockResolvedValueOnce('/downloads/no-cookie.mp3\n')
    const services = createIpcServices(
      () => undefined,
      '/downloads',
      executor,
      {
        ...DEFAULT_CONFIG,
        tierStrategy: {
          ...DEFAULT_CONFIG.tierStrategy,
          cookiesEnabled: true,
          tier1Attempts: 1,
          tier3Enabled: true
        }
      },
      '',
      { findInstalledBrowsers: () => [] }
    )

    await expect(
      services.startDownload('https://youtube.com/watch?v=test', { format: 'mp3', quality: '0' })
    ).resolves.toEqual({ path: '/downloads/no-cookie.mp3' })
    expect(executor.mock.calls[1][1]).toMatchObject({
      extractorArgs: 'youtube:player_client=android'
    })
    expect(executor.mock.calls[1][1]).not.toHaveProperty('cookiesFromBrowser')
  })

  it('rejects invalid direct settings updates and rolls back failed saves', async () => {
    const configSaver = vi.fn().mockRejectedValue(new Error('disk full'))
    const services = createIpcServices(
      () => undefined,
      '/downloads',
      vi.fn(),
      DEFAULT_CONFIG,
      '/config.json',
      { findInstalledBrowsers: () => [] },
      configSaver
    )

    await expect(services.updateSettings({ browser: 'firefox' as never })).rejects.toThrow(
      'Invalid settings update'
    )
    await expect(services.updateSettings({ cookiesEnabled: true })).rejects.toThrow('disk full')
    await expect(services.getSettings()).resolves.toMatchObject({
      cookiesEnabled: false,
      browser: 'chrome'
    })
  })
  it('persists selected browser and cookie opt-in before updating runtime state', async () => {
    const configSaver = vi.fn().mockResolvedValue(undefined)
    const services = createIpcServices(
      () => undefined,
      '/downloads',
      vi.fn(),
      DEFAULT_CONFIG,
      '/config.json',
      { findInstalledBrowsers: () => ['brave'] },
      configSaver
    )

    await expect(
      services.updateSettings({ cookiesEnabled: true, browser: 'brave' })
    ).resolves.toMatchObject({
      cookiesEnabled: true,
      browser: 'brave'
    })
    expect(configSaver).toHaveBeenCalledWith(
      '/config.json',
      expect.objectContaining({
        tierStrategy: expect.objectContaining({ cookiesEnabled: true, browser: 'brave' })
      })
    )
  })

  it('returns failure after terminal fallback exhaustion and releases queue', async () => {
    const executor = vi.fn().mockRejectedValue({ stderr: 'HTTP Error 403: Forbidden', exitCode: 1 })
    const services = createIpcServices(() => undefined, '/downloads', executor, {
      ...DEFAULT_CONFIG,
      tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, tier3Enabled: true }
    })
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )

    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.(
        { sender: {} },
        { url: 'https://youtube.com/watch?v=test', options: { format: 'mp3', quality: '0' } }
      )
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to start download' }
    })
    expect(executor).toHaveBeenCalledTimes(5)
    await expect(handlers.get(IPC_CHANNELS.queueStatus)?.({ sender: {} })).resolves.toEqual({
      ok: true,
      data: { active: false }
    })
  })

  it('does not retry non-escalation failures', async () => {
    const executor = vi.fn().mockRejectedValue({ stderr: 'ERROR: ffmpeg not found', exitCode: 1 })
    const services = createIpcServices(() => undefined, '/downloads', executor, {
      ...DEFAULT_CONFIG,
      tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, tier3Enabled: true }
    })
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )

    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.(
        { sender: {} },
        { url: 'https://youtube.com/watch?v=test', options: { format: 'mp3', quality: '0' } }
      )
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to start download' }
    })
    expect(executor).toHaveBeenCalledOnce()
  })

  it('returns a busy error for a concurrent second request', async () => {
    const { promise: result, resolve: release } = Promise.withResolvers<{ filename: string }>()
    const executor = vi.fn(() => result)
    const services = createIpcServices(() => undefined, '/downloads', executor)
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )
    const payload = {
      url: 'https://youtube.com/watch?v=test',
      options: { format: 'mp3', quality: '0' }
    }

    const first = handlers.get(IPC_CHANNELS.downloadStart)?.({ sender: {} }, payload)
    await expect(handlers.get(IPC_CHANNELS.queueStatus)?.({ sender: {} })).resolves.toEqual({
      ok: true,
      data: { active: true }
    })
    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.({ sender: {} }, payload)
    ).resolves.toEqual({
      ok: false,
      error: { code: 'BUSY', message: 'A download is already in progress' }
    })
    expect(executor).toHaveBeenCalledOnce()

    release({ filename: '/downloads/song.mp3' })
    await first
  })
})
