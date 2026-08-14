import { describe, expect, it, vi } from 'vitest'
import {
  IPC_CHANNELS,
  registerIpcHandlers,
  type IpcHandler,
  type IpcMainLike
} from '../../src/main/ipc'
import { createVideoInfoService } from '../../src/main/services/downloader'

const registerForTest = (handlers: Map<string, IpcHandler>): IpcMainLike => ({
  handle: vi.fn((channel, handler) => handlers.set(channel, handler))
})

describe('video-info IPC flow', () => {
  it('returns normalized metadata through the main IPC boundary', async () => {
    const executor = vi.fn().mockResolvedValue({
      title: 'Integration Video',
      uploader: 'Integration Channel',
      duration: 61,
      thumbnail: 'https://example.com/integration.jpg'
    })
    const videoInfo = createVideoInfoService(executor)
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      {
        fetchVideoInfo: videoInfo.fetch,
        startDownload: vi.fn(),
        getQueueStatus: vi.fn().mockResolvedValue({ active: false })
      },
      vi.fn(() => null)
    )

    const result = await handlers.get(IPC_CHANNELS.videoInfoFetch)?.(
      { sender: {} },
      { url: 'https://youtube.com/watch?v=integration' }
    )

    expect(result).toMatchObject({
      ok: true,
      data: {
        title: 'Integration Video',
        uploader: 'Integration Channel',
        duration: 61,
        thumbnailUrl: 'https://example.com/integration.jpg',
        formats: ['mp3', 'm4a', 'opus', 'wav', 'best'],
        qualities: ['0', '5', '9']
      }
    })
    expect(executor).toHaveBeenCalledOnce()
  })

  it('rejects invalid URLs before the executor', async () => {
    const executor = vi.fn()
    const videoInfo = createVideoInfoService(executor)
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      { fetchVideoInfo: videoInfo.fetch, startDownload: vi.fn(), getQueueStatus: vi.fn() },
      vi.fn(() => null)
    )

    await expect(
      handlers.get(IPC_CHANNELS.videoInfoFetch)?.({ sender: {} }, { url: 'file:///secret' })
    ).resolves.toEqual({
      ok: false,
      error: { code: 'INVALID_INPUT', message: 'Invalid video URL' }
    })
    expect(executor).not.toHaveBeenCalled()
  })

  it('returns a safe error when yt-dlp fails', async () => {
    const executor = vi.fn().mockRejectedValue(new Error('secret token'))
    const videoInfo = createVideoInfoService(executor)
    const handlers = new Map<string, IpcHandler>()

    registerIpcHandlers(
      registerForTest(handlers),
      { fetchVideoInfo: videoInfo.fetch, startDownload: vi.fn(), getQueueStatus: vi.fn() },
      vi.fn(() => null)
    )

    const result = await handlers.get(IPC_CHANNELS.videoInfoFetch)?.(
      { sender: {} },
      { url: 'https://youtube.com/watch?v=failure' }
    )

    expect(result).toEqual({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to fetch video information' }
    })
    expect(JSON.stringify(result)).not.toContain('secret token')
  })
})
