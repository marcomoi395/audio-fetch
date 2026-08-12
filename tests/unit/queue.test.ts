import { describe, expect, it, vi } from 'vitest'
import { BusyDownloadError, createDownloadQueue } from '../../src/main/services/queue'

describe('single-active download queue', () => {
  it('allows one download and reports active status while running', async () => {
    const queue = createDownloadQueue()
    const { promise: task, resolve: release } = Promise.withResolvers<void>()

    const running = queue.run(() => task)
    expect(queue.getStatus()).toEqual({ active: true })

    release()
    await running
    expect(queue.getStatus()).toEqual({ active: false })
  })

  it('rejects a second download without invoking it', async () => {
    const queue = createDownloadQueue()
    const { promise: task, resolve: release } = Promise.withResolvers<void>()
    const first = vi.fn(() => task)
    const second = vi.fn()

    const running = queue.run(first)
    await expect(queue.run(second)).rejects.toBeInstanceOf(BusyDownloadError)
    expect(second).not.toHaveBeenCalled()

    release()
    await running
  })

  it('releases the guard after success and failure', async () => {
    const queue = createDownloadQueue()

    await queue.run(async () => undefined)
    expect(queue.getStatus()).toEqual({ active: false })

    await expect(queue.run(async () => Promise.reject(new Error('failed')))).rejects.toThrow(
      'failed'
    )
    expect(queue.getStatus()).toEqual({ active: false })
  })
})
