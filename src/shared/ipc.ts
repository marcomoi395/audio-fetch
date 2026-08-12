export const IPC_CHANNELS = {
  videoInfoFetch: 'video-info:fetch',
  downloadStart: 'download:start',
  queueStatus: 'queue:status',
  windowMinimize: 'window:minimize',
  windowClose: 'window:close'
} as const

export type DownloadFormat = 'mp3' | 'm4a' | 'opus' | 'wav' | 'best'
export type DownloadQuality = '0' | '5' | '9'

export type DownloadOptions = {
  format: DownloadFormat
  quality: DownloadQuality
}

export type VideoInfo = {
  title: string
  uploader: string
  duration: number
  thumbnailUrl: string
  formats: DownloadFormat[]
  qualities: DownloadQuality[]
}

export type DownloadResult = { path: string }
export type QueueStatus = { active: boolean }

export type IpcError = {
  code: 'INVALID_INPUT' | 'BUSY' | 'INTERNAL_ERROR'
  message: string
}

export type IpcResult<T> = { ok: true; data: T } | { ok: false; error: IpcError }

export type AudioFetchApi = {
  videoInfo: { fetch(url: string): Promise<IpcResult<VideoInfo>> }
  download: { start(url: string, options: DownloadOptions): Promise<IpcResult<DownloadResult>> }
  queue: { getStatus(): Promise<IpcResult<QueueStatus>> }
  window: {
    minimize(): Promise<IpcResult<null>>
    close(confirmed: boolean): Promise<IpcResult<null>>
  }
}
