import type { AudioFetchApi, VideoInfo } from '../../shared/ipc'

export type RendererState =
  | { status: 'idle' }
  | { status: 'loading' }
  | (VideoInfo & { status: 'success' })
  | { status: 'error'; message: string }

type RendererListeners = (state: RendererState) => void

type VideoInfoApi = Pick<AudioFetchApi, 'videoInfo'>

function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' && parsed.hostname.length > 0
  } catch {
    return false
  }
}

export function createRendererController(api: VideoInfoApi) {
  let state: RendererState = { status: 'idle' }
  const listeners = new Set<RendererListeners>()

  const update = (nextState: RendererState): void => {
    state = nextState
    listeners.forEach((listener) => listener(state))
  }

  return {
    getState(): RendererState {
      return state
    },
    subscribe(listener: RendererListeners): () => void {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    async submit(url: string): Promise<void> {
      if (!isValidUrl(url)) {
        update({ status: 'error', message: 'Invalid video URL' })
        return
      }

      update({ status: 'loading' })
      try {
        const result = await api.videoInfo.fetch(url)
        if (result.ok) {
          update({ status: 'success', ...result.data })
        } else {
          update({ status: 'error', message: result.error.message })
        }
      } catch {
        update({ status: 'error', message: 'Unable to fetch video information' })
      }
    }
  }
}
