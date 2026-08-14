import { homedir } from 'node:os'
import type {
  DownloadOptions,
  DownloadResult,
  QueueStatus,
  SettingsSnapshot,
  SettingsUpdate,
  SupportedBrowser
} from '../../shared/ipc'
import type { IpcServices } from './index'
import { createAudioDownloadService, createVideoInfoService } from '../services/downloader'
import { createDownloadQueue } from '../services/queue'
import { configurePackagedYtDlpEnvironment } from '../utils/binaries'
import { DEFAULT_CONFIG, saveConfig, type AppConfig } from '../services/config'
import { CookieExtractor } from '../services/cookie-extractor'
import { createTierStrategy, executeTierStrategy } from '../services/tier-strategy'

type YtDlpModule = (url: string, options: Record<string, unknown>) => Promise<unknown>
type AudioServiceExecutor = (url: string, options: Record<string, unknown>) => Promise<unknown>
type ConfigSaver = (path: string, config: AppConfig) => Promise<void>
export type BrowserDetector = { findInstalledBrowsers(): SupportedBrowser[] }

function isSupportedBrowser(value: unknown): value is SupportedBrowser {
  return value === 'chrome' || value === 'chromium' || value === 'brave'
}

function isSettingsUpdate(value: SettingsUpdate): boolean {
  const keys = Object.keys(value)
  if (keys.length === 0 || keys.some((key) => key !== 'cookiesEnabled' && key !== 'browser')) {
    return false
  }
  if ('cookiesEnabled' in value && typeof value.cookiesEnabled !== 'boolean') return false
  if ('browser' in value && !isSupportedBrowser(value.browser)) return false
  return true
}

async function executeYtDlp(url: string, options: Record<string, unknown>): Promise<unknown> {
  const mode = process.env['AUDIO_FETCH_E2E_FIXTURE']
  if (mode) {
    await new Promise((resolve) => setTimeout(resolve, mode === 'slow' ? 1000 : 100))
    if (mode === 'error' || (mode === 'failure' && !options.dumpSingleJson)) {
      throw new Error('fixture failure')
    }
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

function createDefaultBrowserDetector(): BrowserDetector {
  try {
    return new CookieExtractor({ platform: process.platform, homeDir: homedir() })
  } catch {
    return { findInstalledBrowsers: () => [] }
  }
}

export function createIpcServices(
  log: (message: string) => void = () => undefined,
  outputDir = process.cwd(),
  executor: AudioServiceExecutor = executeYtDlp,
  config: AppConfig = DEFAULT_CONFIG,
  configPath = '',
  browserDetector: BrowserDetector = createDefaultBrowserDetector(),
  configSaver: ConfigSaver = saveConfig
): IpcServices {
  let currentConfig = config
  const videoInfo = createVideoInfoService(executor, log)
  const audioDownload = createAudioDownloadService(executor, log)
  const queue = createDownloadQueue()

  const getAvailableBrowsers = (): SupportedBrowser[] => {
    try {
      return browserDetector.findInstalledBrowsers()
    } catch {
      return []
    }
  }

  const getSettings = (): SettingsSnapshot => ({
    cookiesEnabled: currentConfig.tierStrategy.cookiesEnabled,
    browser: currentConfig.tierStrategy.browser,
    availableBrowsers: getAvailableBrowsers()
  })

  return {
    fetchVideoInfo: videoInfo.fetch,
    startDownload: (url: string, options: DownloadOptions): Promise<DownloadResult> =>
      queue.run(async () => {
        let downloadResult: DownloadResult | undefined
        const availableBrowsers = getAvailableBrowsers()
        const tierStrategy = createTierStrategy({
          browser: currentConfig.tierStrategy.browser,
          cookiesEnabled:
            currentConfig.tierStrategy.cookiesEnabled &&
            availableBrowsers.includes(currentConfig.tierStrategy.browser),
          fallbackEnabled: currentConfig.tierStrategy.fallbackEnabled,
          tier1Attempts: currentConfig.tierStrategy.tier1Attempts,
          tier3Enabled: currentConfig.tierStrategy.tier3Enabled
        })
        const result = await executeTierStrategy(tierStrategy, async (flags) => {
          downloadResult = await audioDownload.download(url, options, outputDir, flags)
          return downloadResult
        })
        if (!result.success)
          throw new Error('Unable to download audio', { cause: result.lastError })
        if (!downloadResult) throw new Error('Unable to download audio')
        return downloadResult
      }),
    getQueueStatus: async (): Promise<QueueStatus> => queue.getStatus(),
    getSettings: async (): Promise<SettingsSnapshot> => getSettings(),
    updateSettings: async (update: SettingsUpdate): Promise<SettingsSnapshot> => {
      if (!isSettingsUpdate(update)) throw new Error('Invalid settings update')
      const nextConfig: AppConfig = {
        ...currentConfig,
        tierStrategy: {
          ...currentConfig.tierStrategy,
          ...(update.cookiesEnabled === undefined ? {} : { cookiesEnabled: update.cookiesEnabled }),
          ...(update.browser === undefined ? {} : { browser: update.browser })
        }
      }
      if (configPath) await configSaver(configPath, nextConfig)
      currentConfig = nextConfig
      return getSettings()
    }
  }
}
