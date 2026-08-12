import { describe, expect, it, vi } from 'vitest'
import { IPC_CHANNELS } from '../../src/shared/ipc'
import { createPreloadApi } from '../../src/preload/api'

describe('preload IPC bridge', () => {
  it('exposes only typed methods on fixed channels', async () => {
    const invoke = vi.fn().mockResolvedValue({ ok: true, data: { active: false } })
    const api = createPreloadApi({ invoke })

    expect(Object.keys(api)).toEqual(['videoInfo', 'download', 'queue', 'window'])
    expect(api).not.toHaveProperty('ipcRenderer')
    expect(api).not.toHaveProperty('send')
    expect(api).not.toHaveProperty('invoke')

    await api.videoInfo.fetch('https://youtube.com/watch?v=1')
    await api.download.start('https://youtube.com/watch?v=1', { format: 'mp3', quality: '0' })
    await api.queue.getStatus()
    await api.window.minimize()
    await api.window.close(true)

    expect(invoke).toHaveBeenNthCalledWith(1, IPC_CHANNELS.videoInfoFetch, {
      url: 'https://youtube.com/watch?v=1'
    })
    expect(invoke).toHaveBeenNthCalledWith(2, IPC_CHANNELS.downloadStart, {
      url: 'https://youtube.com/watch?v=1',
      options: { format: 'mp3', quality: '0' }
    })
    expect(invoke).toHaveBeenNthCalledWith(3, IPC_CHANNELS.queueStatus)
    expect(invoke).toHaveBeenNthCalledWith(4, IPC_CHANNELS.windowMinimize)
    expect(invoke).toHaveBeenNthCalledWith(5, IPC_CHANNELS.windowClose, { confirmed: true })
  })
})
