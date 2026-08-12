import { describe, expect, it, vi } from 'vitest'
import {
  IPC_CHANNELS,
  registerIpcHandlers,
  type IpcHandler,
  type IpcMainLike,
  type IpcServices
} from '../../src/main/ipc'
import type { DownloadOptions, QueueStatus, VideoInfo } from '../../src/shared/ipc'

const services: IpcServices = {
  fetchVideoInfo: vi.fn<() => Promise<VideoInfo>>(),
  startDownload: vi.fn<(url: string, options: DownloadOptions) => Promise<{ path: string }>>(),
  getQueueStatus: vi.fn<() => Promise<QueueStatus>>().mockResolvedValue({ active: false })
}

function registerForTest(handlers: Map<string, IpcHandler>): IpcMainLike {
  return {
    handle: vi.fn((channel, handler) => handlers.set(channel, handler))
  }
}

describe('typed IPC boundary', () => {
  it('registers one explicit channel per approved operation', () => {
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )

    expect([...handlers.keys()]).toEqual(Object.values(IPC_CHANNELS))
  })

  it('rejects invalid payloads before calling services', async () => {
    const fetchVideoInfo = vi.fn<() => Promise<VideoInfo>>()
    const handlers = new Map<string, IpcHandler>()
    const testServices = { ...services, fetchVideoInfo }

    registerIpcHandlers(
      registerForTest(handlers),
      testServices,
      vi.fn(() => null)
    )
    const handler = handlers.get(IPC_CHANNELS.videoInfoFetch)
    expect(handler).toBeDefined()
    const result = await handler?.({ sender: {} }, { url: 'javascript:alert(1)' })

    expect(result).toEqual({
      ok: false,
      error: { code: 'INVALID_INPUT', message: 'Invalid video URL' }
    })
    expect(fetchVideoInfo).not.toHaveBeenCalled()
  })

  it('normalizes thrown errors into serializable safe responses', async () => {
    const handlers = new Map<string, IpcHandler>()
    const testServices: IpcServices = {
      ...services,
      fetchVideoInfo: vi.fn().mockRejectedValue(new Error('contains secret token'))
    }

    registerIpcHandlers(
      registerForTest(handlers),
      testServices,
      vi.fn(() => null)
    )
    const handler = handlers.get(IPC_CHANNELS.videoInfoFetch)
    expect(handler).toBeDefined()
    const result = await handler?.({ sender: {} }, { url: 'https://youtube.com/watch?v=1' })

    expect(result).toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to fetch video information' }
    })
  })

  it('sanitizes unavailable service errors', async () => {
    const handlers = new Map<string, IpcHandler>()
    const testServices: IpcServices = {
      fetchVideoInfo: vi.fn().mockRejectedValue(new Error('secret token leaked')),
      startDownload: vi.fn(),
      getQueueStatus: vi.fn()
    }

    registerIpcHandlers(
      registerForTest(handlers),
      testServices,
      vi.fn(() => null)
    )
    const result = await handlers.get(IPC_CHANNELS.videoInfoFetch)?.(
      { sender: {} },
      { url: 'https://youtube.com/watch?v=1' }
    )

    expect(result).toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to fetch video information' }
    })
    expect(JSON.stringify(result)).not.toContain('secret token leaked')
  })

  it('rejects window controls without an owning window', () => {
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      services,
      vi.fn(() => null)
    )

    expect(handlers.get(IPC_CHANNELS.windowMinimize)?.({ sender: {} })).toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to access application window' }
    })
  })
  it('owns window controls through the sender window', async () => {
    const handlers = new Map<string, IpcHandler>()
    const senderWindow = { minimize: vi.fn(), close: vi.fn() }
    const resolveSenderWindow = vi.fn(() => senderWindow)

    registerIpcHandlers(registerForTest(handlers), services, resolveSenderWindow)

    handlers.get(IPC_CHANNELS.windowMinimize)?.({ sender: {} })
    await handlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, { confirmed: false })

    expect(resolveSenderWindow).toHaveBeenCalledTimes(2)
    expect(senderWindow.minimize).toHaveBeenCalledOnce()
    expect(senderWindow.close).toHaveBeenCalledOnce()
  })
  it('blocks active close without confirmation', async () => {
    const handlers = new Map<string, IpcHandler>()
    const senderWindow = { minimize: vi.fn(), close: vi.fn() }
    const testServices = {
      ...services,
      getQueueStatus: vi.fn().mockResolvedValue({ active: true })
    }
    registerIpcHandlers(registerForTest(handlers), testServices, () => senderWindow)

    await expect(
      handlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, { confirmed: false })
    ).resolves.toEqual({
      ok: false,
      error: { code: 'BUSY', message: 'A download is already in progress' }
    })
    expect(senderWindow.close).not.toHaveBeenCalled()
  })

  it('closes when inactive or explicitly confirmed', async () => {
    const handlers = new Map<string, IpcHandler>()
    const senderWindow = { minimize: vi.fn(), close: vi.fn() }
    const getQueueStatus = vi
      .fn()
      .mockResolvedValueOnce({ active: false })
      .mockResolvedValueOnce({ active: true })
    const testServices = { ...services, getQueueStatus }
    registerIpcHandlers(registerForTest(handlers), testServices, () => senderWindow)

    await expect(
      handlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, { confirmed: false })
    ).resolves.toEqual({
      ok: true,
      data: null
    })
    await expect(
      handlers.get(IPC_CHANNELS.windowClose)?.({ sender: {} }, { confirmed: true })
    ).resolves.toEqual({
      ok: true,
      data: null
    })
    expect(senderWindow.close).toHaveBeenCalledTimes(2)
  })
})
