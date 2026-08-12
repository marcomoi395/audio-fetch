import { describe, expect, it, vi } from 'vitest'
import { createRendererController } from '../../src/renderer/src/app'

describe('renderer video-info flow', () => {
  it('moves from idle to loading to metadata', async () => {
    const fetch = vi.fn().mockResolvedValue({
      ok: true,
      data: {
        title: 'Test Video',
        uploader: 'Test Channel',
        duration: 120,
        thumbnailUrl: 'https://example.com/thumb.jpg',
        formats: ['mp3', 'm4a', 'opus', 'wav', 'best'],
        qualities: ['0', '5', '9']
      }
    })
    const controller = createRendererController({ videoInfo: { fetch } })

    expect(controller.getState().status).toBe('idle')
    const pending = controller.submit('https://youtube.com/watch?v=test')
    expect(controller.getState().status).toBe('loading')
    await pending

    expect(controller.getState()).toMatchObject({ status: 'success', title: 'Test Video' })
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
})
