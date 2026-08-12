import type { DownloadFormat, DownloadQuality, VideoInfo } from '../../shared/ipc'

export const SUPPORTED_FORMATS: DownloadFormat[] = ['mp3', 'm4a', 'opus', 'wav', 'best']
export const SUPPORTED_QUALITIES: DownloadQuality[] = ['0', '5', '9']

type YtDlpExecutor = (url: string, options: Record<string, unknown>) => Promise<unknown>
type VideoInfoLogger = (message: string) => void

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object'
}

function isHttpsUrl(value: string): boolean {
  try {
    return new URL(value).protocol === 'https:'
  } catch {
    return false
  }
}

function mapVideoInfo(value: unknown): VideoInfo {
  if (!isRecord(value)) throw new Error('Invalid yt-dlp metadata')

  const duration =
    typeof value.duration === 'number' && Number.isFinite(value.duration)
      ? Math.floor(value.duration)
      : 0
  const title =
    typeof value.title === 'string' && value.title.length > 0 ? value.title : 'Unknown Title'
  const uploader =
    typeof value.uploader === 'string' && value.uploader.length > 0
      ? value.uploader
      : 'Unknown Artist'
  const thumbnailUrl =
    typeof value.thumbnail === 'string' && isHttpsUrl(value.thumbnail) ? value.thumbnail : ''

  return {
    title,
    uploader,
    duration,
    thumbnailUrl,
    formats: SUPPORTED_FORMATS,
    qualities: SUPPORTED_QUALITIES
  }
}

function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' && parsed.hostname.length > 0
  } catch {
    return false
  }
}

export function createVideoInfoService(
  executor: YtDlpExecutor,
  log: VideoInfoLogger = () => undefined
): { fetch(url: string): Promise<VideoInfo> } {
  return {
    async fetch(url: string): Promise<VideoInfo> {
      if (!isValidUrl(url)) throw new Error('Invalid video URL')

      try {
        const metadata = await executor(url, {
          dumpSingleJson: true,
          skipDownload: true,
          extractorArgs: { youtube: { playerClient: ['android'] } }
        })
        return mapVideoInfo(metadata)
      } catch {
        log('Video info fetch failed')
        throw new Error('Unable to fetch video information')
      }
    }
  }
}
