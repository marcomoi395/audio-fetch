import ffmpeg from '@ffmpeg-installer/ffmpeg'
import type {
  DownloadFormat,
  DownloadOptions,
  DownloadQuality,
  DownloadResult,
  VideoInfo
} from '../../shared/ipc'

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
type AudioExecutor = (url: string, options: Record<string, unknown>) => Promise<unknown>

const MP3_QUALITY: Record<DownloadQuality, string> = { '0': '320', '5': '192', '9': '128' }

function sanitizeFilename(value: string): string {
  const sanitized = [...value]
    .map((character) => (character.charCodeAt(0) < 32 ? '-' : character))
    .join('')
    .replace(/[<>:"/\\|?*]/g, '-')
    .replace(/[. ]+$/, '')
  return sanitized || 'audio'
}

function safeOutputPath(value: string): string {
  const separator = Math.max(value.lastIndexOf('/'), value.lastIndexOf('\\'))
  if (separator < 0) return sanitizeFilename(value)
  return `${value.slice(0, separator + 1)}${sanitizeFilename(value.slice(separator + 1))}`
}

function getAudioPostprocessors(options: DownloadOptions): Record<string, unknown>[] {
  const postprocessors: Record<string, unknown>[] = []
  if (options.format !== 'best') {
    const processor: Record<string, unknown> = {
      key: 'FFmpegExtractAudio',
      preferredcodec: options.format
    }
    if (options.format === 'mp3') processor.preferredquality = MP3_QUALITY[options.quality]
    postprocessors.push(processor)
  }
  postprocessors.push(
    { key: 'FFmpegThumbnailsConvertor', format: 'jpg' },
    { key: 'EmbedThumbnail' },
    { key: 'FFmpegMetadata', add_metadata: true }
  )
  return postprocessors
}

export function createAudioDownloadService(
  executor: AudioExecutor,
  log: VideoInfoLogger = () => undefined
): { download(url: string, options: DownloadOptions, outputDir: string): Promise<DownloadResult> } {
  return {
    async download(url, options, outputDir): Promise<DownloadResult> {
      if (!isValidUrl(url)) throw new Error('Invalid video URL')
      if (!outputDir) throw new Error('Invalid output directory')

      try {
        const result = await executor(url, {
          format: 'bestaudio/best',
          outtmpl: `${outputDir.replace(/[\\/]+$/, '')}/%(title)s.%(ext)s`,
          ffmpegLocation: ffmpeg.path,
          writethumbnail: true,
          postprocessors: getAudioPostprocessors(options)
        })
        const filename =
          isRecord(result) && typeof result.filename === 'string' ? result.filename : ''
        if (!filename) throw new Error('Missing download path')
        return { path: safeOutputPath(filename) }
      } catch {
        log('Audio download failed')
        throw new Error('Unable to download audio')
      }
    }
  }
}
