import type { DownloadOptions, DownloadResult, QueueStatus } from '../../shared/ipc'
import type { IpcServices } from './index'
import { createAudioDownloadService, createVideoInfoService } from '../services/downloader'
import { createDownloadQueue } from '../services/queue'

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
      : { filename: '/downloads/fixture.mp3' }
  }

  const module = (await import('youtube-dl-exec')) as unknown as { default: YtDlpModule }
  return module.default(url, options)
}

export function createIpcServices(
  log: (message: string) => void = () => undefined,
  outputDir = process.cwd(),
  executor: AudioServiceExecutor = executeYtDlp
): IpcServices {
  const videoInfo = createVideoInfoService(executor, log)
  const audioDownload = createAudioDownloadService(executor, log)
  const queue = createDownloadQueue()

  return {
    fetchVideoInfo: videoInfo.fetch,
    startDownload: (url: string, options: DownloadOptions): Promise<DownloadResult> =>
      queue.run(() => audioDownload.download(url, options, outputDir)),
    getQueueStatus: async (): Promise<QueueStatus> => queue.getStatus()
  }
}
