import type { DownloadOptions, DownloadResult, QueueStatus } from '../../shared/ipc'
import type { IpcServices } from './index'
import { createAudioDownloadService, createVideoInfoService } from '../services/downloader'
import { createDownloadQueue } from '../services/queue'
import { configurePackagedYtDlpEnvironment } from '../utils/binaries'
import { DEFAULT_CONFIG, type AppConfig } from '../services/config'
import { createTierStrategy, executeTierStrategy } from '../services/tier-strategy'

type YtDlpModule = (url: string, options: Record<string, unknown>) => Promise<unknown>
type AudioServiceExecutor = (url: string, options: Record<string, unknown>) => Promise<unknown>

async function executeYtDlp(url: string, options: Record<string, unknown>): Promise<unknown> {
  const mode = process.env['AUDIO_FETCH_E2E_FIXTURE']
  if (mode) {
    // Test-only deterministic executor; normal launches always use youtube-dl-exec.
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

export function createIpcServices(
  log: (message: string) => void = () => undefined,
  outputDir = process.cwd(),
  executor: AudioServiceExecutor = executeYtDlp,
  config: AppConfig = DEFAULT_CONFIG
): IpcServices {
  const videoInfo = createVideoInfoService(executor, log)
  const audioDownload = createAudioDownloadService(executor, log)
  const tierStrategy = createTierStrategy({
    browser: config.tierStrategy.browser,
    cookiesEnabled: false,
    fallbackEnabled: config.tierStrategy.fallbackEnabled,
    tier1Attempts: config.tierStrategy.tier1Attempts,
    tier3Enabled: config.tierStrategy.tier3Enabled
  })
  const queue = createDownloadQueue()

  return {
    fetchVideoInfo: videoInfo.fetch,
    startDownload: (url: string, options: DownloadOptions): Promise<DownloadResult> =>
      queue.run(async () => {
        let downloadResult: DownloadResult | undefined
        const result = await executeTierStrategy(tierStrategy, async (flags) => {
          downloadResult = await audioDownload.download(url, options, outputDir, flags)
          return downloadResult
        })
        if (!result.success)
          throw new Error('Unable to download audio', { cause: result.lastError })
        if (!downloadResult) throw new Error('Unable to download audio')
        return downloadResult
      }),
    getQueueStatus: async (): Promise<QueueStatus> => queue.getStatus()
  }
}
