import { describe, expect, it, vi } from 'vitest'
import { installPreloadApi } from '../../src/preload/install'
import type { AudioFetchApi } from '../../src/shared/ipc'

describe('preload installer', () => {
  it('exposes only the audioFetch namespace', () => {
    const expose = vi.fn()
    const api: AudioFetchApi = {
      videoInfo: { fetch: vi.fn() },
      download: { start: vi.fn() },
      queue: { getStatus: vi.fn() },
      window: { minimize: vi.fn(), close: vi.fn() }
    }

    installPreloadApi(expose, api)

    expect(expose).toHaveBeenCalledWith('audioFetch', api)
    expect(expose).not.toHaveBeenCalledWith('electron', expect.anything())
    expect(expose).not.toHaveBeenCalledWith('api', expect.anything())
  })
})
