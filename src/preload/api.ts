import { IPC_CHANNELS, type AudioFetchApi, type DownloadOptions } from '../shared/ipc'

type IpcRendererLike = {
  invoke(channel: string, ...args: unknown[]): Promise<unknown>
}

function invoke<T>(ipcRenderer: IpcRendererLike, channel: string, ...args: unknown[]): Promise<T> {
  return ipcRenderer.invoke(channel, ...args) as Promise<T>
}

export function createPreloadApi(ipcRenderer: IpcRendererLike): AudioFetchApi {
  return {
    videoInfo: {
      fetch: (url) => invoke(ipcRenderer, IPC_CHANNELS.videoInfoFetch, { url })
    },
    download: {
      start: (url: string, options: DownloadOptions) =>
        invoke(ipcRenderer, IPC_CHANNELS.downloadStart, { url, options })
    },
    queue: {
      getStatus: () => invoke(ipcRenderer, IPC_CHANNELS.queueStatus)
    },
    window: {
      minimize: () => invoke(ipcRenderer, IPC_CHANNELS.windowMinimize),
      close: (confirmed: boolean) => invoke(ipcRenderer, IPC_CHANNELS.windowClose, { confirmed })
    }
  }
}
