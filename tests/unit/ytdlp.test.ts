import { describe, expect, it, vi } from 'vitest'
import { createYtDlpExecutor, updateYtDlp } from '../../src/main/services/ytdlp'

const runtime = { binaryPath: '/user-data/yt-dlp/yt-dlp', updatePath: '/user-data/yt-dlp/yt-dlp' }

describe('yt-dlp runtime service', () => {
  it('creates an executor bound to the writable runtime binary', async () => {
    const executor = vi.fn().mockResolvedValue('ok')
    const create = vi.fn(() => executor)
    const delegate = await createYtDlpExecutor(runtime, () => ({
      create,
      default: vi.fn()
    }))

    await expect(
      delegate('https://youtube.com/watch?v=test', { dumpSingleJson: true })
    ).resolves.toBe('ok')
    expect(create).toHaveBeenCalledWith(runtime.binaryPath)
    expect(executor).toHaveBeenCalledWith('https://youtube.com/watch?v=test', {
      dumpSingleJson: true
    })
  })

  it('logs update success when yt-dlp updates successfully', async () => {
    const update = vi.fn().mockResolvedValue(undefined)
    const log = vi.fn()

    await updateYtDlp(runtime, log, () => ({ default: vi.fn(), update }))

    expect(update).toHaveBeenCalledWith(runtime.updatePath)
    expect(log).toHaveBeenCalledWith('yt-dlp updated successfully')
  })

  it('keeps the existing binary when update fails', async () => {
    const update = vi.fn().mockRejectedValue(new Error('offline'))
    const log = vi.fn()

    await expect(
      updateYtDlp(runtime, log, () => ({ default: vi.fn(), update }))
    ).resolves.toBeUndefined()
    expect(log).toHaveBeenCalledWith('yt-dlp update failed; using the existing binary')
  })
})
