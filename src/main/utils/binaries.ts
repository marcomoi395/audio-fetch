import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'

export function resolvePackagedYtDlpPath(resourcesPath: string): string {
  return join(
    resourcesPath,
    'app.asar.unpacked',
    'node_modules',
    'youtube-dl-exec',
    'bin',
    'yt-dlp'
  )
}

export function resolvePackagedFfmpegPath(resourcesPath: string): string {
  return join(
    resourcesPath,
    'app.asar.unpacked',
    'node_modules',
    '@ffmpeg-installer',
    `${process.platform}-${process.arch}`,
    process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg'
  )
}

export function resolveFfmpegPath(
  resourcesPath: string | undefined,
  fallbackPath: string,
  fileExists: (path: string) => boolean = existsSync
): string {
  if (!resourcesPath) return fallbackPath
  const packagedPath = resolvePackagedFfmpegPath(resourcesPath)
  return fileExists(packagedPath) ? packagedPath : fallbackPath
}

export function configurePackagedYtDlpEnvironment(
  resourcesPath: string,
  env: NodeJS.ProcessEnv,
  fileExists: (path: string) => boolean = existsSync
): boolean {
  const binaryPath = resolvePackagedYtDlpPath(resourcesPath)
  if (!fileExists(binaryPath)) return false
  env['YOUTUBE_DL_DIR'] ??= dirname(binaryPath)
  env['YOUTUBE_DL_FILENAME'] ??= 'yt-dlp'
  return true
}
