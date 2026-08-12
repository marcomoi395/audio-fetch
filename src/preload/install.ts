import type { AudioFetchApi } from '../shared/ipc'

type ExposeInMainWorld = (key: string, api: AudioFetchApi) => void

export function installPreloadApi(exposeInMainWorld: ExposeInMainWorld, api: AudioFetchApi): void {
  exposeInMainWorld('audioFetch', api)
}
