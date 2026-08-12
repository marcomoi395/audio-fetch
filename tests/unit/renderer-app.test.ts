import { describe, expect, it, vi } from 'vitest'
import { createRendererController } from '../../src/renderer/src/app'

const videoInfo = {
  title: 'Test Video',
  uploader: 'Test Channel',
  duration: 120,
  thumbnailUrl: 'https://example.com/thumb.jpg',
  formats: ['mp3', 'm4a', 'opus', 'wav', 'best'] as const,
  qualities: ['0', '5', '9'] as const
}

describe('renderer video-info flow', () => {
  it('moves from idle to loading to metadata', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, data: videoInfo })
    const controller = createRendererController({ videoInfo: { fetch } })

    expect(controller.getState().status).toBe('idle')
    const pending = controller.submit('https://youtube.com/watch?v=test')
    expect(controller.getState().status).toBe('loading')
    await pending

    expect(controller.getState()).toMatchObject({ status: 'success', title: 'Test Video' })
  })

  it('rejects invalid URLs before calling preload', async () => {
    const fetch = vi.fn()
    const controller = createRendererController({ videoInfo: { fetch } })

    await controller.submit('javascript:alert(1)')

    expect(controller.getState()).toEqual({ status: 'error', message: 'Invalid video URL' })
    expect(fetch).not.toHaveBeenCalled()
  })

  it('ignores a stale fetch result after new URL reset', async () => {
    const { promise, resolve } = Promise.withResolvers<typeof videoInfo>()
    const fetch = vi.fn().mockReturnValue(promise.then((data) => ({ ok: true as const, data })))
    const controller = createRendererController({ videoInfo: { fetch } })

    const pending = controller.submit('https://youtube.com/watch?v=test')
    controller.newUrl()
    resolve(videoInfo)
    await pending

    expect(controller.getState()).toEqual({ status: 'idle' })
  })

  it('moves to an error state without exposing internal errors', async () => {
    const fetch = vi.fn().mockResolvedValue({
      ok: false,
      error: { code: 'INTERNAL_ERROR', message: 'Unable to fetch video information' }
    })
    const controller = createRendererController({ videoInfo: { fetch } })

    await controller.submit('https://youtube.com/watch?v=test')

    expect(controller.getState()).toEqual({
      status: 'error',
      message: 'Unable to fetch video information'
    })
  })

  it('moves to a generic error state when IPC rejects', async () => {
    const fetch = vi.fn().mockRejectedValue(new Error('internal secret'))
    const controller = createRendererController({ videoInfo: { fetch } })

    await controller.submit('https://youtube.com/watch?v=test')

    expect(controller.getState()).toEqual({
      status: 'error',
      message: 'Unable to fetch video information'
    })
  })

  it('retries the last URL and resets to idle for a new URL', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, data: videoInfo })
    const controller = createRendererController({ videoInfo: { fetch } })

    await controller.submit('https://youtube.com/watch?v=test')
    await controller.retry()
    expect(fetch).toHaveBeenCalledTimes(2)

    controller.newUrl()
    expect(controller.getState()).toEqual({ status: 'idle' })
  })

  it('downloads with selected options and reports busy errors safely', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, data: videoInfo })
    const start = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, data: { path: '/downloads/song.mp3' } })
      .mockResolvedValueOnce({
        ok: false,
        error: { code: 'BUSY', message: 'A download is already in progress' }
      })
    const controller = createRendererController({ videoInfo: { fetch }, download: { start } })

    await controller.submit('https://youtube.com/watch?v=test')
    await expect(controller.download('opus', '5')).resolves.toBeUndefined()
    expect(controller.getState()).toMatchObject({ status: 'success', downloadStatus: 'success' })
    expect(start).toHaveBeenCalledWith('https://youtube.com/watch?v=test', {
      format: 'opus',
      quality: '5'
    })

    await controller.download('mp3', '0')
    expect(controller.getState()).toEqual({
      status: 'error',
      message: 'A download is already in progress'
    })
  })
})
