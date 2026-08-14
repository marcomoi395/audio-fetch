import { describe, expect, it, vi } from 'vitest'
import {
  IPC_CHANNELS,
  registerIpcHandlers,
  type IpcHandler,
  type IpcMainLike,
  type IpcServices
} from '../../src/main/ipc'
import type {
  DownloadOptions,
  QueueStatus,
  SettingsSnapshot,
  VideoInfo
} from '../../src/shared/ipc'

const settings: SettingsSnapshot = { cookiesConfigured: false }
const services: IpcServices = {
  fetchVideoInfo: vi.fn<() => Promise<VideoInfo>>(),
  startDownload: vi.fn<(url: string, options: DownloadOptions) => Promise<{ path: string }>>(),
  getQueueStatus: vi.fn<() => Promise<QueueStatus>>().mockResolvedValue({ active: false }),
  getSettings: vi.fn<() => Promise<SettingsSnapshot>>().mockResolvedValue(settings),
  updateSettings: vi.fn().mockResolvedValue(settings)
}
function registerForTest(handlers: Map<string, IpcHandler>): IpcMainLike {
  return { handle: vi.fn((channel, handler) => handlers.set(channel, handler)) }
}

const downloadWindow = { minimize: vi.fn(), close: vi.fn() }

describe('typed IPC boundary', () => {
  it('registers one explicit handler per channel', () => {
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )
    expect([...handlers.keys()]).toEqual(Object.values(IPC_CHANNELS))
  })
  it('moves a successful download to the user-selected path', async () => {
    const handlers = new Map<string, IpcHandler>()
    const showSaveDialog = vi
      .fn()
      .mockResolvedValue({ canceled: false, filePath: '/home/user/song.mp3' })
    const moveFile = vi.fn().mockResolvedValue(undefined)
    services.startDownload = vi.fn().mockResolvedValue({ path: '/tmp/song.mp3' })
    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => downloadWindow),
      console.error,
      showSaveDialog,
      moveFile
    )

    const result = await handlers.get(IPC_CHANNELS.downloadStart)?.(
      { sender: {} },
      { url: 'https://youtube.com/watch?v=test', options: { format: 'mp3', quality: '0' } }
    )

    expect(showSaveDialog).toHaveBeenCalledWith(
      downloadWindow,
      expect.objectContaining({ defaultPath: '/tmp/song.mp3' })
    )
    expect(moveFile).toHaveBeenCalledWith('/tmp/song.mp3', '/home/user/song.mp3')
    expect(result).toEqual({ ok: true, data: { path: '/home/user/song.mp3' } })
  })

  it('rejects invalid URLs before service calls', async () => {
    const fetchVideoInfo = vi.fn<() => Promise<VideoInfo>>()
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      { ...services, fetchVideoInfo },
      vi.fn(() => null)
    )
    await expect(
      handlers.get(IPC_CHANNELS.videoInfoFetch)?.({ sender: {} }, { url: 'javascript:alert(1)' })
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INVALID_INPUT', message: 'Invalid video URL' }
    })
    expect(fetchVideoInfo).not.toHaveBeenCalled()
  })

  it('accepts cookie settings without returning raw cookie text', async () => {
    const handlers = new Map<string, IpcHandler>()
    const updateSettings = vi.fn().mockResolvedValue({ cookiesConfigured: true })
    registerIpcHandlers(
      registerForTest(handlers),
      { ...services, updateSettings },
      vi.fn(() => null)
    )
    const cookieText = '.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tsecret-value'
    await expect(
      handlers.get(IPC_CHANNELS.settingsUpdate)?.({ sender: {} }, { cookies: cookieText })
    ).resolves.toEqual({
      ok: true,
      data: { cookiesConfigured: true }
    })
    expect(
      JSON.stringify(await handlers.get(IPC_CHANNELS.settingsGet)?.({ sender: {} }))
    ).not.toContain('secret-value')
    expect(updateSettings).toHaveBeenCalledWith({ cookies: cookieText })
  })

  it('rejects unknown settings fields', async () => {
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )
    await expect(
      handlers.get(IPC_CHANNELS.settingsUpdate)?.({ sender: {} }, { browser: 'chrome' })
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INVALID_INPUT', message: 'Invalid settings update' }
    })
  })

  it('maps auth failures for metadata and download', async () => {
    const handlers = new Map<string, IpcHandler>()
    const authError = Object.assign(new Error('Authentication required'), {
      code: 'COOKIES_REQUIRED',
      hint: 'Add Netscape cookies and retry.'
    })
    const testServices: IpcServices = {
      ...services,
      fetchVideoInfo: vi.fn().mockRejectedValue(authError),
      startDownload: vi.fn().mockRejectedValue(authError)
    }
    registerIpcHandlers(
      registerForTest(handlers),
      testServices,
      vi.fn(() => null)
    )
    await expect(
      handlers.get(IPC_CHANNELS.videoInfoFetch)?.(
        { sender: {} },
        { url: 'https://youtube.com/watch?v=1' }
      )
    ).resolves.toEqual({
      ok: false,
      error: {
        code: 'COOKIES_REQUIRED',
        message: 'Authentication required',
        hint: 'Add Netscape cookies and retry.'
      }
    })
    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.(
        { sender: {} },
        {
          url: 'https://youtube.com/watch?v=1',
          options: { format: 'mp3', quality: '0' }
        }
      )
    ).resolves.toEqual({
      ok: false,
      error: {
        code: 'COOKIES_REQUIRED',
        message: 'Authentication required',
        hint: 'Add Netscape cookies and retry.'
      }
    })
  })

  it('keeps generic failures generic', async () => {
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      {
        ...services,
        fetchVideoInfo: vi.fn().mockRejectedValue(new Error('network timeout'))
      },
      vi.fn(() => null)
    )
    await expect(
      handlers.get(IPC_CHANNELS.videoInfoFetch)?.(
        { sender: {} },
        { url: 'https://youtube.com/watch?v=1' }
      )
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to fetch video information' }
    })
  })
  it('preserves a cookie hint for uncertain HTTP auth failures only', async () => {
    const handlers = new Map<string, IpcHandler>()
    const uncertainError = Object.assign(new Error('Unable to download audio'), {
      cause: { statusCode: 403 },
      hint: 'Nội dung có thể yêu cầu cookie; hãy thêm Netscape cookies và thử lại'
    })
    registerIpcHandlers(
      registerForTest(handlers),
      {
        ...services,
        startDownload: vi.fn().mockRejectedValue(uncertainError)
      },
      vi.fn(() => null)
    )
    await expect(
      handlers.get(IPC_CHANNELS.downloadStart)?.(
        { sender: {} },
        {
          url: 'https://youtube.com/watch?v=1',
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
  it('maps settings service failures to internal errors', async () => {
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      {
        ...services,
        getSettings: vi.fn().mockRejectedValue(new Error('read failed')),
        updateSettings: vi.fn().mockRejectedValue(new Error('write failed'))
      },
      vi.fn(() => null)
    )

    await expect(handlers.get(IPC_CHANNELS.settingsGet)?.({ sender: {} })).resolves.toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to read settings' }
    })
    await expect(
      handlers.get(IPC_CHANNELS.settingsUpdate)?.({ sender: {} }, { clearCookies: true })
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to save settings' }
    })
  })

  it('handles minimize requests with and without a window', async () => {
    const missingWindowHandlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(missingWindowHandlers),
      services,
      vi.fn(() => null)
    )
    await expect(missingWindowHandlers.get(IPC_CHANNELS.windowMinimize)?.({ sender: {} })).toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to access application window' }
    })

    const window = { minimize: vi.fn(), close: vi.fn() }
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => window)
    )
    await expect(handlers.get(IPC_CHANNELS.windowMinimize)?.({ sender: {} })).toEqual({
      ok: true,
      data: null
    })
    expect(window.minimize).toHaveBeenCalledOnce()
  })

  it('validates close requests and protects active downloads', async () => {
    const handlers = new Map<string, IpcHandler>()
    const window = { minimize: vi.fn(), close: vi.fn() }
    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => window)
    )

    await expect(handlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, {})).resolves.toEqual({
      ok: false,
      error: { code: 'INVALID_INPUT', message: 'Invalid close request' }
    })

    const busyHandlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(busyHandlers),
      { ...services, getQueueStatus: vi.fn().mockResolvedValue({ active: true }) },
      vi.fn(() => window)
    )
    await expect(
      busyHandlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, { confirmed: false })
    ).resolves.toEqual({
      ok: false,
      error: { code: 'BUSY', message: 'A download is already in progress' }
    })

    await expect(
      busyHandlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, { confirmed: true })
    ).resolves.toEqual({ ok: true, data: null })
    expect(window.close).toHaveBeenCalledOnce()
  })

  it('returns internal errors when closing cannot read queue status', async () => {
    const handlers = new Map<string, IpcHandler>()
    registerIpcHandlers(
      registerForTest(handlers),
      { ...services, getQueueStatus: vi.fn().mockRejectedValue(new Error('queue failed')) },
      vi.fn(() => downloadWindow)
    )

    await expect(
      handlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, { confirmed: false })
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to close application window' }
    })
  })
})
