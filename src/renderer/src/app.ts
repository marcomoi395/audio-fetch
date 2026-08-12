import type { AudioFetchApi, DownloadFormat, DownloadQuality, VideoInfo } from '../../shared/ipc'

export type RendererState =
  | { status: 'idle' }
  | { status: 'loading' }
  | (VideoInfo & {
      status: 'success'
      downloadStatus?: 'loading' | 'success'
      downloadPath?: string
    })
  | { status: 'error'; message: string }

type RendererApi = Partial<AudioFetchApi> & Pick<AudioFetchApi, 'videoInfo'>
type RendererListeners = (state: RendererState) => void

function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' && parsed.hostname.length > 0
  } catch {
    return false
  }
}

export async function confirmAndClose(
  api: Pick<AudioFetchApi, 'queue' | 'window'>,
  confirmClose: (message: string) => boolean
): Promise<void> {
  const result = await api.queue.getStatus()
  if (!result.ok) return
  const confirmed = result.data.active
    ? confirmClose('A download is still in progress. Close Audio Fetch?')
    : false
  if (result.data.active && !confirmed) return
  await api.window.close(confirmed)
}

export function createRendererController(api: RendererApi) {
  let state: RendererState = { status: 'idle' }
  let currentUrl = ''
  let requestVersion = 0
  const listeners = new Set<RendererListeners>()

  const update = (nextState: RendererState): void => {
    state = nextState
    listeners.forEach((listener) => listener(state))
  }

  const submit = async (url: string): Promise<void> => {
    requestVersion += 1
    const version = requestVersion
    currentUrl = url
    if (!isValidUrl(url)) {
      update({ status: 'error', message: 'Invalid video URL' })
      return
    }

    update({ status: 'loading' })
    try {
      const result = await api.videoInfo.fetch(url)
      if (version !== requestVersion) return
      if (result.ok) {
        update({ status: 'success', ...result.data })
      } else {
        update({ status: 'error', message: result.error.message })
      }
    } catch {
      if (version === requestVersion) {
        update({ status: 'error', message: 'Unable to fetch video information' })
      }
    }
  }

  return {
    getState(): RendererState {
      return state
    },
    subscribe(listener: RendererListeners): () => void {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    submit,
    retry(): Promise<void> {
      return currentUrl ? submit(currentUrl) : Promise.resolve()
    },
    newUrl(): void {
      requestVersion += 1
      currentUrl = ''
      update({ status: 'idle' })
    },
    async download(format: DownloadFormat, quality: DownloadQuality): Promise<void> {
      if (state.status !== 'success' || !currentUrl || !api.download) return
      const current = state
      const version = requestVersion
      update({ ...current, downloadStatus: 'loading' })
      try {
        const result = await api.download.start(currentUrl, { format, quality })
        if (version !== requestVersion) return
        if (result.ok) {
          update({ ...current, downloadStatus: 'success', downloadPath: result.data.path })
        } else {
          update({ status: 'error', message: result.error.message })
        }
      } catch {
        if (version === requestVersion) {
          update({ status: 'error', message: 'Unable to download audio' })
        }
      }
    }
  }
}
