import { stat } from 'node:fs/promises'
import { describe, expect, it, vi } from 'vitest'
import {
  IPC_CHANNELS,
  registerIpcHandlers,
  type IpcHandler,
  type IpcMainLike
} from '../../src/main/ipc'
import { createIpcServices } from '../../src/main/ipc/services'
import { DEFAULT_CONFIG } from '../../src/main/services/config'
import { createManualCookieStore } from '../../src/main/services/cookie-store'

const COOKIE_TEXT = '.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tsecret-value'
const registerForTest = (handlers: Map<string, IpcHandler>): IpcMainLike => ({
  handle: vi.fn((channel, handler) => handlers.set(channel, handler))
})

describe('download IPC flow', () => {
  it('downloads successfully and exposes safe queue status', async () => {
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
        {
          url: 'https://youtube.com/watch?v=test',
          options: { format: 'mp3', quality: '0' }
        }
      )
    ).resolves.toEqual({ ok: true, data: { path: '/downloads/song.mp3' } })
    await expect(handlers.get(IPC_CHANNELS.queueStatus)?.({ sender: {} })).resolves.toEqual({
      ok: true,
      data: { active: false }
    })
  })

  it('runs mobile clients before manual cookies and logs safe labels', async () => {
    const executor = vi
      .fn()
      .mockRejectedValueOnce({ stderr: 'HTTP Error 403: Forbidden', exitCode: 1 })
      .mockRejectedValueOnce({ stderr: 'HTTP Error 403: Forbidden', exitCode: 1 })
      .mockRejectedValueOnce({ stderr: 'HTTP Error 403: Forbidden', exitCode: 1 })
      .mockResolvedValueOnce('/downloads/cookie.mp3\n')
    const log = vi.fn()
    const cookieStore = createManualCookieStore()
    cookieStore.set(COOKIE_TEXT)
    const services = createIpcServices(
      log,
      '/downloads',
      executor,
      { ...DEFAULT_CONFIG, tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, tier1Attempts: 1 } },
      cookieStore
    )

    await expect(
      services.startDownload('https://youtube.com/watch?v=test', { format: 'mp3', quality: '0' })
    ).resolves.toEqual({
      path: '/downloads/cookie.mp3'
    })
    expect(log).toHaveBeenCalledWith('[download] tier=1 attempt=1')
    expect(log).toHaveBeenCalledWith('[download] tier=2 client=android')
    expect(log).toHaveBeenCalledWith('[download] tier=2 client=mweb')
    expect(log).toHaveBeenCalledWith('[download] tier=3 manual-cookie')
    expect(log.mock.calls.flat().join('\n')).not.toContain('cookies.txt')
    expect(log.mock.calls.flat().join('\n')).not.toContain('secret-value')
    const cookiePath = executor.mock.calls[3][1].cookies as string
    await expect(stat(cookiePath)).rejects.toMatchObject({ code: 'ENOENT' })
  })

  it('uses the same tier order for private metadata lookup', async () => {
    const executor = vi
      .fn()
      .mockRejectedValueOnce({ stderr: 'This video is private', exitCode: 1 })
      .mockRejectedValueOnce({ stderr: 'This video is private', exitCode: 1 })
      .mockRejectedValueOnce({ stderr: 'This video is private', exitCode: 1 })
      .mockResolvedValueOnce({ title: 'Private', uploader: 'Channel', duration: 1 })
    const cookieStore = createManualCookieStore()
    cookieStore.set(COOKIE_TEXT)
    const services = createIpcServices(
      () => undefined,
      '/downloads',
      executor,
      { ...DEFAULT_CONFIG, tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, tier1Attempts: 1 } },
      cookieStore
    )

    await expect(
      services.fetchVideoInfo('https://youtube.com/watch?v=private')
    ).resolves.toMatchObject({
      title: 'Private'
    })
    expect(executor.mock.calls[1][1]).toMatchObject({
      extractorArgs: 'youtube:player_client=android'
    })
    expect(executor.mock.calls[2][1]).toMatchObject({ extractorArgs: 'youtube:player_client=mweb' })
    const cookiePath = executor.mock.calls[3][1].cookies as string
    expect(cookiePath).toContain('cookies.txt')
    await expect(stat(cookiePath)).rejects.toMatchObject({ code: 'ENOENT' })
  })
  it('maps terminal auth failure to COOKIES_REQUIRED', async () => {
    const executor = vi.fn().mockRejectedValue({ stderr: 'This video is private', exitCode: 1 })
    const services = createIpcServices(() => undefined, '/downloads', executor, {
      ...DEFAULT_CONFIG,
      tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, tier1Attempts: 1 }
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
        {
          url: 'https://youtube.com/watch?v=test',
          options: { format: 'mp3', quality: '0' }
        }
      )
    ).resolves.toMatchObject({
      ok: false,
      error: { code: 'COOKIES_REQUIRED', hint: expect.stringContaining('Add Netscape cookies') }
    })
  })

  it('does not classify network errors as cookie failures', async () => {
    const executor = vi.fn().mockRejectedValue({ stderr: 'network timeout', exitCode: 1 })
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
        {
          url: 'https://youtube.com/watch?v=test',
          options: { format: 'mp3', quality: '0' }
        }
      )
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to start download' }
    })
  })
  it('adds a cookie hint for terminal HTTP 403 without changing error code', async () => {
    const executor = vi
      .fn()
      .mockRejectedValue({ statusCode: 403, stderr: 'Forbidden', exitCode: 1 })
    const services = createIpcServices(() => undefined, '/downloads', executor, {
      ...DEFAULT_CONFIG,
      tierStrategy: { ...DEFAULT_CONFIG.tierStrategy, tier1Attempts: 1 }
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
        {
          url: 'https://youtube.com/watch?v=test',
          options: { format: 'mp3', quality: '0' }
        }
      )
    ).resolves.toEqual({
      ok: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Unable to start download',
        hint: 'Nội dung có thể yêu cầu cookie; hãy thêm Netscape cookies và thử lại'
      }
    })
  })
})
