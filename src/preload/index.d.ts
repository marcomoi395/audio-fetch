import type { AudioFetchApi } from '../shared/ipc'

declare global {
  interface Window {
    audioFetch: AudioFetchApi
  }
}
