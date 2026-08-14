import type {
  DownloadOptions,
  DownloadResult,
  QueueStatus,
  SettingsSnapshot,
  SettingsUpdate,
  VideoInfo
} from '../../shared/ipc'
import type { IpcServices } from './index'
import { createAudioDownloadService, createVideoInfoService } from '../services/downloader'
import { createDownloadQueue } from '../services/queue'
import { configurePackagedYtDlpEnvironment } from '../utils/binaries'
import { DEFAULT_CONFIG, type AppConfig } from '../services/config'
import { createManualCookieStore, type ManualCookieStore } from '../services/cookie-store'
import {
  createTierStrategy,
  executeTierStrategy,
  isAuthenticationRequired,
  type TierAttempt
} from '../services/tier-strategy'

type YtDlpModule = (url: string, options: Record<string, unknown>) => Promise<unknown>
type AudioServiceExecutor = (url: string, options: Record<string, unknown>) => Promise<unknown>
type ServiceError = Error & { code?: 'COOKIES_REQUIRED'; hint?: string }

const COOKIE_HINT = 'Nội dung có thể yêu cầu cookie; hãy thêm Netscape cookies và thử lại'

function createUncertainError(
  message: string,
  lastError: { statusCode?: number } | undefined
): ServiceError {
  const error = new Error(message) as ServiceError
  if (lastError?.statusCode && [401, 403, 429].includes(lastError.statusCode))
    error.hint = COOKIE_HINT
  error.cause = lastError
  return error
}

async function executeYtDlp(url: string, options: Record<string, unknown>): Promise<unknown> {
  const mode = process.env['AUDIO_FETCH_E2E_FIXTURE']
  if (mode) {
    await new Promise((resolve) => setTimeout(resolve, mode === 'slow' ? 1000 : 100))
    if (mode === 'error' || (mode === 'failure' && !options.dumpSingleJson))
      throw new Error('fixture failure')
    return options.dumpSingleJson
      ? { title: 'Fixture Video', uploader: 'Fixture Channel', duration: 42, thumbnail: '' }
      : '/downloads/fixture.mp3\n'
  }
  if (process.resourcesPath && process.resourcesPath !== process.cwd()) {
    configurePackagedYtDlpEnvironment(process.resourcesPath, process.env)
  }
  const module = (await import('youtube-dl-exec')) as unknown as { default: YtDlpModule }
  return module.default(url, options)
}

function isSettingsUpdate(value: SettingsUpdate): boolean {
  const keys = Object.keys(value)
  if (keys.length === 0 || keys.some((key) => key !== 'cookies' && key !== 'clearCookies'))
    return false
  if ('cookies' in value && typeof value.cookies !== 'string') return false
  if ('clearCookies' in value && typeof value.clearCookies !== 'boolean') return false
  return true
}

function createAuthError(lastError: unknown): ServiceError {
  const error = new Error('Authentication required to download this content') as ServiceError
  error.code = 'COOKIES_REQUIRED'
  error.hint =
    'This content may be private, age-restricted, or require login. Add Netscape cookies and retry.'
  error.cause = lastError
  return error
}

export function createIpcServices(
  log: (message: string) => void = () => undefined,
  outputDir = process.cwd(),
  executor: AudioServiceExecutor = executeYtDlp,
  config: AppConfig = DEFAULT_CONFIG,
  cookieStore: ManualCookieStore = createManualCookieStore()
): IpcServices {
  const videoInfo = createVideoInfoService(executor, log)
  const audioDownload = createAudioDownloadService(executor, log)
  const queue = createDownloadQueue()
  const getSettings = (): SettingsSnapshot => ({ cookiesConfigured: cookieStore.isConfigured() })
  const withCookieFlags = async <T>(
    flags: TierAttempt,
    callback: (next: TierAttempt) => Promise<T>
  ) => {
    if (!flags.useManualCookies) return callback(flags)
    return cookieStore.withCookieFile((path) => callback({ ...flags, cookies: path }))
  }
  const createStrategy = () =>
    createTierStrategy({
      fallbackEnabled: config.tierStrategy.fallbackEnabled,
      tier1Attempts: config.tierStrategy.tier1Attempts,
      mobileFallbackEnabled: config.tierStrategy.mobileFallbackEnabled,
      cookiesConfigured: cookieStore.isConfigured()
    })

  return {
    fetchVideoInfo: async (url: string): Promise<VideoInfo> => {
      let metadata: VideoInfo | undefined
      const result = await executeTierStrategy(
        createStrategy(),
        (flags) =>
          withCookieFlags(flags, async (attemptFlags) => {
            metadata = await videoInfo.fetch(url, attemptFlags)
            return metadata
          }),
        undefined,
        (message) => log(`[video-info] ${message}`)
      )
      if (!result.success) {
        if (isAuthenticationRequired(result.lastError)) throw createAuthError(result.lastError)
        throw createUncertainError('Unable to fetch video information', result.lastError)
      }
      if (!metadata) throw new Error('Unable to fetch video information')
      return metadata
    },
    startDownload: (url: string, options: DownloadOptions): Promise<DownloadResult> =>
      queue.run(async () => {
        let downloadResult: DownloadResult | undefined
        const result = await executeTierStrategy(
          createStrategy(),
          (flags) =>
            withCookieFlags(flags, async (attemptFlags) => {
              downloadResult = await audioDownload.download(url, options, outputDir, attemptFlags)
              return downloadResult
            }),
          undefined,
          (message) => log(`[download] ${message}`)
        )
        if (!result.success) {
          if (isAuthenticationRequired(result.lastError)) throw createAuthError(result.lastError)
          throw createUncertainError('Unable to download audio', result.lastError)
        }
        if (!downloadResult) throw new Error('Unable to download audio')
        return downloadResult
      }),
    getQueueStatus: async (): Promise<QueueStatus> => queue.getStatus(),
    getSettings: async (): Promise<SettingsSnapshot> => getSettings(),
    updateSettings: async (update: SettingsUpdate): Promise<SettingsSnapshot> => {
      if (!isSettingsUpdate(update)) throw new Error('Invalid settings update')
      if (update.clearCookies) cookieStore.clear()
      if (update.cookies !== undefined) cookieStore.set(update.cookies)
      return getSettings()
    }
  }
}
