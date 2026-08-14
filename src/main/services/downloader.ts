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
export class DownloadExecutionError extends Error {
  readonly stage = 'yt-dlp' as const
  readonly statusCode?: number
  readonly stderr?: string
  readonly stdout?: string
  readonly exitCode?: number

  constructor(error: unknown) {
    const source = isRecord(error) ? error : {}
    const originalMessage = error instanceof Error ? error.message : String(error)
    super('Unable to download audio')
    this.name = 'DownloadExecutionError'
    this.cause = error
    this.statusCode =
      typeof source.statusCode === 'number'
        ? source.statusCode
        : readHttpStatus(originalMessage, source.stderr)
    this.stderr = typeof source.stderr === 'string' ? source.stderr : undefined
    this.stdout = typeof source.stdout === 'string' ? source.stdout : undefined
    this.exitCode = typeof source.exitCode === 'number' ? source.exitCode : undefined
  }
}

function readHttpStatus(...values: unknown[]): number | undefined {
  const text = values.filter((value): value is string => typeof value === 'string').join('\n')
  const match = text.match(/HTTP Error (401|403|429)\b/i)
  return match ? Number(match[1]) : undefined
}
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
          extractorArgs: 'youtube:player_client=android'
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
function describeFailure(value: unknown): string {
  const redact = (text: string): string =>
    text
      .slice(0, 1000)
      .replace(
        /(cookie|token|password|secret|authorization)(?:[=:_\-\s]+)[^&\s]+/gi,
        '$1=[REDACTED]'
      )
  if (value instanceof Error) {
    const cause = value.cause
    const causeDetails = isRecord(cause) ? cause : {}
    const details: Record<string, string> = {
      name: value.name,
      message: redact(value.message)
    }
    for (const key of ['stderr', 'stdout', 'exitCode', 'statusCode']) {
      if (key in causeDetails) details[key] = redact(String(causeDetails[key]))
    }
    if (cause instanceof Error && cause.message !== value.message) {
      details.cause = redact(cause.message)
    }
    return JSON.stringify(details)
  }
  if (!isRecord(value)) return redact(String(value))
  const details = Object.fromEntries(
    ['name', 'message', 'stderr', 'stdout', 'exitCode', 'statusCode'].flatMap((key) =>
      key in value ? [[key, redact(String(value[key]))]] : []
    )
  )
  return JSON.stringify(details)
}

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

function getAudioOptions(options: DownloadOptions): Record<string, unknown> {
  const audioOptions: Record<string, unknown> = {
    format: 'bestaudio/best',
    writeThumbnail: true,
    convertThumbnails: 'jpg',
    embedThumbnail: true,
    embedMetadata: true
  }
  if (options.format !== 'best') {
    audioOptions.extractAudio = true
    audioOptions.audioFormat = options.format
    if (options.format === 'mp3') audioOptions.audioQuality = MP3_QUALITY[options.quality]
  }
  return audioOptions
}

export function createAudioDownloadService(
  executor: AudioExecutor,
  log: VideoInfoLogger = () => undefined
): {
  download(
    url: string,
    options: DownloadOptions,
    outputDir: string,
    attemptFlags?: Record<string, unknown>
  ): Promise<DownloadResult>
} {
  return {
    async download(url, options, outputDir, attemptFlags = {}): Promise<DownloadResult> {
      if (!isValidUrl(url)) throw new Error('Invalid video URL')
      if (!outputDir) throw new Error('Invalid output directory')

      console.log('[download] yt-dlp start', {
        format: options.format,
        quality: options.quality,
        outputDir,
        attemptFlags,
        ffmpegLocation: ffmpeg.path
      })
      try {
        const result = await executor(url, {
          ...attemptFlags,
          ...getAudioOptions(options),
          output: `${outputDir.replace(/[\\/]+$/, '')}/%(title)s.%(ext)s`,
          print: 'after_move:filepath',
          ffmpegLocation: ffmpeg.path
        })
        console.log('[download] yt-dlp result', {
          type: typeof result,
          preview: typeof result === 'string' ? result.slice(-500) : result
        })
        const filename =
          typeof result === 'string'
            ? (result
                .split(/\r?\n/)
                .map((line) => line.trim())
                .filter(Boolean)
                .at(-1) ?? '')
            : isRecord(result) && typeof result.filename === 'string'
              ? result.filename
              : ''
        if (!filename) throw new Error('Missing download path')
        return { path: safeOutputPath(filename) }
      } catch (error) {
        const executionError = new DownloadExecutionError(error)
        const message = `[download] yt-dlp failure ${describeFailure(executionError)}`
        log(message)
        throw new Error('Unable to download audio', { cause: executionError })
      }
    }
  }
}
