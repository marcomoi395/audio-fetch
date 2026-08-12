import type { IpcServices } from './index'
import { createVideoInfoService } from '../services/downloader'

type YtDlpModule = (url: string, options: Record<string, unknown>) => Promise<unknown>

async function executeYtDlp(url: string, options: Record<string, unknown>): Promise<unknown> {
  const module = (await import('youtube-dl-exec')) as unknown as { default: YtDlpModule }
  return module.default(url, options)
}

export function createIpcServices(log: (message: string) => void = () => undefined): IpcServices {
  const videoInfo = createVideoInfoService(executeYtDlp, log)

  return {
    fetchVideoInfo: videoInfo.fetch,
    startDownload: async () => {
      throw new Error('Download service unavailable')
    },
    getQueueStatus: async () => ({ active: false })
  }
}
