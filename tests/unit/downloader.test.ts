import { describe, expect, it, vi } from 'vitest'
import {
  createVideoInfoService,
  SUPPORTED_FORMATS,
  SUPPORTED_QUALITIES
} from '../../src/main/services/downloader'

describe('video info service', () => {
  it('validates URLs before invoking yt-dlp', async () => {
    const executor = vi.fn()
    const service = createVideoInfoService(executor)

    await expect(service.fetch('javascript:alert(1)')).rejects.toThrow('Invalid video URL')
    expect(executor).not.toHaveBeenCalled()
  })

  it('maps yt-dlp metadata to the typed video-info contract', async () => {
    const executor = vi.fn().mockResolvedValue({
      title: 'Test Video',
      uploader: 'Test Channel',
      duration: 120.7,
      thumbnail: 'https://example.com/thumb.jpg'
    })
    const service = createVideoInfoService(executor)

    await expect(service.fetch('https://youtube.com/watch?v=test')).resolves.toEqual({
      title: 'Test Video',
      uploader: 'Test Channel',
      duration: 120,
      thumbnailUrl: 'https://example.com/thumb.jpg',
      formats: SUPPORTED_FORMATS,
      qualities: SUPPORTED_QUALITIES
    })
    expect(executor).toHaveBeenCalledWith(
      'https://youtube.com/watch?v=test',
      expect.objectContaining({
        dumpSingleJson: true,
        skipDownload: true,
        extractorArgs: expect.any(Object)
      })
    )
  })

  it('uses safe fallbacks for incomplete metadata', async () => {
    const executor = vi.fn().mockResolvedValue({
      title: '',
      uploader: null,
      duration: null,
      thumbnail: 'file:///secret'
    })
    const service = createVideoInfoService(executor)

    await expect(service.fetch('https://youtube.com/watch?v=test')).resolves.toMatchObject({
      title: 'Unknown Title',
      uploader: 'Unknown Artist',
      duration: 0,
      thumbnailUrl: ''
    })
  })

  it('logs a safe reason and exposes a user-safe error', async () => {
    const log = vi.fn()
    const executor = vi.fn().mockRejectedValue(new Error('secret token from yt-dlp'))
    const service = createVideoInfoService(executor, log)

    await expect(service.fetch('https://youtube.com/watch?v=test')).rejects.toThrow(
      'Unable to fetch video information'
    )
    expect(log).toHaveBeenCalledWith('Video info fetch failed')
    expect(log.mock.calls[0][0]).not.toContain('secret token')
  })
})
