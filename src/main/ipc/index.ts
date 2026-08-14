import { copyFile, rename, unlink } from 'node:fs/promises'
import { BusyDownloadError } from '../services/queue'
import {
  IPC_CHANNELS,
  type AudioFetchApi,
  type DownloadOptions,
  type DownloadResult,
  type IpcResult,
  type QueueStatus,
  type SettingsSnapshot,
  type SettingsUpdate,
  type VideoInfo
} from '../../shared/ipc'

export type IpcEvent = { sender: unknown }
export type IpcHandler = (event: IpcEvent, payload?: unknown) => Promise<unknown> | unknown
export type IpcMainLike = { handle(channel: string, handler: IpcHandler): void }
type WindowLike = { minimize(): void; close(): void }
type SaveDialogWindow = WindowLike | null
type SaveDialogResult = { canceled: boolean; filePath: string }
type SaveDialogOptions = {
  defaultPath: string
  title: string
  properties: ['showOverwriteConfirmation']
}
type ShowSaveDialog = (
  window: SaveDialogWindow,
  options: SaveDialogOptions
) => Promise<SaveDialogResult>
type MoveFile = (source: string, destination: string) => Promise<void>

const moveFileAcrossDevices: MoveFile = async (source, destination) => {
  try {
    await rename(source, destination)
  } catch (error) {
    if (!(error instanceof Error && 'code' in error && error.code === 'EXDEV')) throw error
    await copyFile(source, destination)
    await unlink(source)
  }
}

export type IpcServices = {
  fetchVideoInfo(url: string): Promise<VideoInfo>
  startDownload(url: string, options: DownloadOptions): Promise<DownloadResult>
  getQueueStatus(): Promise<QueueStatus>
  getSettings(): Promise<SettingsSnapshot>
  updateSettings(update: SettingsUpdate): Promise<SettingsSnapshot>
}

function canceled<T>(message: string): IpcResult<T> {
  return { ok: false, error: { code: 'CANCELED', message } }
}

const defaultShowSaveDialog: ShowSaveDialog = async (_window, options) => ({
  canceled: false,
  filePath: options.defaultPath
})

async function removeStagedFile(path: string): Promise<void> {
  await unlink(path).catch(() => undefined)
}

type ServiceError = Error & { code?: string; hint?: string }

function invalid<T>(message: string): IpcResult<T> {
  return { ok: false, error: { code: 'INVALID_INPUT', message } }
}
function internal<T>(message: string, hint?: string): IpcResult<T> {
  return { ok: false, error: { code: 'INTERNAL_ERROR', message, ...(hint ? { hint } : {}) } }
}
function busy<T>(message: string): IpcResult<T> {
  return { ok: false, error: { code: 'BUSY', message } }
}
function authRequired<T>(error: ServiceError): IpcResult<T> {
  return {
    ok: false,
    error: { code: 'COOKIES_REQUIRED', message: error.message, hint: error.hint }
  }
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
function isValidSettingsUpdate(value: unknown): value is SettingsUpdate {
  if (!isRecord(value)) return false
  const keys = Object.keys(value)
  if (keys.length === 0 || keys.some((key) => key !== 'cookies' && key !== 'clearCookies'))
    return false
  if ('cookies' in value && typeof value.cookies !== 'string') return false
  if ('clearCookies' in value && typeof value.clearCookies !== 'boolean') return false
  return true
}
function describeError(value: unknown): string {
  const message = value instanceof Error ? value.message : String(value)
  return message.replace(
    /(cookie|token|password|secret|authorization)[=:][^\s]+/gi,
    '$1=[REDACTED]'
  )
}

export function registerIpcHandlers(
  ipcMain: IpcMainLike,
  services: IpcServices,
  resolveSenderWindow: (sender: unknown) => WindowLike | null,
  log: (message: string) => void = console.error,
  showSaveDialog: ShowSaveDialog = defaultShowSaveDialog,
  moveFile: MoveFile = moveFileAcrossDevices
): void {
  ipcMain.handle(IPC_CHANNELS.videoInfoFetch, async (_event, payload) => {
    const url = property(payload, 'url')
    if (!isValidUrl(url)) return invalid('Invalid video URL')
    try {
      return { ok: true, data: await services.fetchVideoInfo(url) }
    } catch (error) {
      const serviceError = error as ServiceError
      if (serviceError.code === 'COOKIES_REQUIRED') return authRequired(serviceError)
      return internal('Unable to fetch video information', serviceError.hint)
    }
  })

  ipcMain.handle(IPC_CHANNELS.downloadStart, async (event, payload) => {
    const url = property(payload, 'url')
    const options = property(payload, 'options')
    if (!isValidUrl(url) || !isValidOptions(options)) return invalid('Invalid download request')
    let stagedPath = ''
    try {
      const window = resolveSenderWindow(event.sender)
      const result = await services.startDownload(url, options)
      stagedPath = result.path
      const saveResult = await showSaveDialog(window, {
        defaultPath: result.path,
        title: 'Save downloaded audio',
        properties: ['showOverwriteConfirmation']
      })
      if (saveResult.canceled || !saveResult.filePath) {
        await removeStagedFile(stagedPath)
        return canceled<DownloadResult>('Download canceled')
      }
      if (saveResult.filePath !== stagedPath) await moveFile(stagedPath, saveResult.filePath)
      return { ok: true, data: { path: saveResult.filePath } }
    } catch (error) {
      if (stagedPath) await removeStagedFile(stagedPath)
      const serviceError = error as ServiceError
      if (!(error instanceof Error && error.message === 'Unable to download audio')) {
        log(`[download] IPC failure ${describeError(error).slice(0, 1000)}`)
      }
      if (error instanceof BusyDownloadError) return busy(error.message)
      if (serviceError.code === 'COOKIES_REQUIRED') return authRequired(serviceError)
      return internal('Unable to start download', serviceError.hint)
    }
  })

  ipcMain.handle(IPC_CHANNELS.queueStatus, async () => {
    try {
      return { ok: true, data: await services.getQueueStatus() }
    } catch {
      return internal('Unable to read queue status')
    }
  })
  ipcMain.handle(IPC_CHANNELS.settingsGet, async () => {
    try {
      return { ok: true, data: await services.getSettings() }
    } catch {
      return internal<SettingsSnapshot>('Unable to read settings')
    }
  })
  ipcMain.handle(IPC_CHANNELS.settingsUpdate, async (_event, payload) => {
    if (!isValidSettingsUpdate(payload)) return invalid<SettingsSnapshot>('Invalid settings update')
    try {
      return { ok: true, data: await services.updateSettings(payload) }
    } catch {
      return internal<SettingsSnapshot>('Unable to save settings')
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
