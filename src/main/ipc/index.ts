import { BusyDownloadError } from '../services/queue'

import {
  IPC_CHANNELS,
  type AudioFetchApi,
  type DownloadOptions,
  type DownloadResult,
  type IpcResult,
  type QueueStatus,
  type VideoInfo
} from '../../shared/ipc'

export type IpcEvent = { sender: unknown }
export type IpcHandler = (event: IpcEvent, payload?: unknown) => Promise<unknown> | unknown

export type IpcMainLike = {
  handle(channel: string, handler: IpcHandler): void
}

type WindowLike = { minimize(): void; close(): void }

export type IpcServices = {
  fetchVideoInfo(url: string): Promise<VideoInfo>
  startDownload(url: string, options: DownloadOptions): Promise<DownloadResult>
  getQueueStatus(): Promise<QueueStatus>
}

function invalid<T>(message: string): IpcResult<T> {
  return { ok: false, error: { code: 'INVALID_INPUT', message } }
}

function internal<T>(message: string): IpcResult<T> {
  return { ok: false, error: { code: 'INTERNAL_ERROR', message } }
}
function busy<T>(message: string): IpcResult<T> {
  return { ok: false, error: { code: 'BUSY', message } }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object'
}

function property(value: unknown, key: string): unknown {
  return isRecord(value) && key in value ? value[key] : undefined
}

function isValidUrl(value: unknown): value is string {
  if (typeof value !== 'string') return false
  try {
    const url = new URL(value)
    return url.protocol === 'https:' && url.hostname.length > 0
  } catch {
    return false
  }
}

function isValidOptions(value: unknown): value is DownloadOptions {
  return (
    isRecord(value) &&
    typeof value.format === 'string' &&
    ['mp3', 'm4a', 'opus', 'wav', 'best'].includes(value.format) &&
    typeof value.quality === 'string' &&
    ['0', '5', '9'].includes(value.quality)
  )
}

export function registerIpcHandlers(
  ipcMain: IpcMainLike,
  services: IpcServices,
  resolveSenderWindow: (sender: unknown) => WindowLike | null
): void {
  ipcMain.handle(IPC_CHANNELS.videoInfoFetch, async (_event, payload) => {
    const url = property(payload, 'url')
    if (!isValidUrl(url)) return invalid('Invalid video URL')

    try {
      return { ok: true, data: await services.fetchVideoInfo(url) }
    } catch {
      return internal('Unable to fetch video information')
    }
  })

  ipcMain.handle(IPC_CHANNELS.downloadStart, async (_event, payload) => {
    const url = property(payload, 'url')
    const options = property(payload, 'options')
    if (!isValidUrl(url) || !isValidOptions(options)) return invalid('Invalid download request')

    try {
      return { ok: true, data: await services.startDownload(url, options) }
    } catch (error) {
      if (error instanceof BusyDownloadError) return busy(error.message)
      return internal('Unable to start download')
    }
  })

  ipcMain.handle(IPC_CHANNELS.queueStatus, async () => {
    try {
      return { ok: true, data: await services.getQueueStatus() }
    } catch {
      return internal('Unable to read queue status')
    }
  })

  ipcMain.handle(IPC_CHANNELS.windowMinimize, (event) => {
    const window = resolveSenderWindow(event.sender)
    if (!window) return internal<null>('Unable to access application window')
    window.minimize()
    return { ok: true, data: null }
  })

  ipcMain.handle(IPC_CHANNELS.windowClose, async (event, payload) => {
    const window = resolveSenderWindow(event.sender)
    if (!window) return internal<null>('Unable to access application window')
    if (!isRecord(payload) || typeof payload.confirmed !== 'boolean') {
      return invalid<null>('Invalid close request')
    }

    try {
      const status = await services.getQueueStatus()
      if (status.active && !payload.confirmed)
        return busy<null>('A download is already in progress')
      window.close()
      return { ok: true, data: null }
    } catch {
      return internal<null>('Unable to close application window')
    }
  })
}

export { IPC_CHANNELS }
export type { AudioFetchApi }
