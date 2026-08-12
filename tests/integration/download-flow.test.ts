import { describe, expect, it, vi } from 'vitest'
import {
  IPC_CHANNELS,
  registerIpcHandlers,
  type IpcHandler,
  type IpcMainLike
} from '../../src/main/ipc'
import { createIpcServices } from '../../src/main/ipc/services'

const registerForTest = (handlers: Map<string, IpcHandler>): IpcMainLike => ({
  handle: vi.fn((channel, handler) => handlers.set(channel, handler))
})

describe('download IPC flow', () => {
  it('starts one download and exposes safe queue status', async () => {
    const executor = vi.fn().mockResolvedValue({ filename: '/downloads/song.mp3' })
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
