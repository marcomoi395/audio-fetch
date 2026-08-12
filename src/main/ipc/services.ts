import type { IpcServices } from './index'

export function createUnavailableIpcServices(): IpcServices {
  return {
    fetchVideoInfo: async () => {
      throw new Error('Video info service unavailable')
    },
    startDownload: async () => {
      throw new Error('Download service unavailable')
    },
    getQueueStatus: async () => ({ active: false })
  }
}
