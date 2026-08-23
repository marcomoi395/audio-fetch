import { access, chmod, copyFile, mkdir } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'

export type YtDlpRuntime = {
  binaryPath: string
  updatePath?: string
}

export function resolveYtDlpFilename(platform = process.platform): string {
  return platform === 'win32' ? 'yt-dlp.exe' : 'yt-dlp'
}

export function resolvePackagedYtDlpPath(
  resourcesPath: string,
  platform = process.platform
): string {
  return join(
    resourcesPath,
    'app.asar.unpacked',
    'node_modules',
    'youtube-dl-exec',
    'bin',
    resolveYtDlpFilename(platform)
  )
}

export function resolveYtDlpSourcePath(
  resourcesPath: string | undefined,
  cwd: string,
  isPackaged: boolean,
  platform = process.platform
): string {
  return isPackaged && resourcesPath
    ? resolvePackagedYtDlpPath(resourcesPath, platform)
    : join(cwd, 'node_modules', 'youtube-dl-exec', 'bin', resolveYtDlpFilename(platform))
}

export function resolveUserYtDlpPath(userDataPath: string, platform = process.platform): string {
  return join(userDataPath, 'yt-dlp', resolveYtDlpFilename(platform))
}

export async function prepareYtDlpRuntime(
  sourcePath: string,
  userDataPath: string,
  platform = process.platform,
  fileExists: (path: string) => Promise<boolean> = async (path) => {
    try {
      await access(path)
      return true
    } catch {
      return false
    }
  }
): Promise<YtDlpRuntime> {
  const userPath = resolveUserYtDlpPath(userDataPath, platform)
  if (await fileExists(userPath)) return { binaryPath: userPath, updatePath: userPath }

  if (await fileExists(sourcePath)) {
    try {
      await mkdir(dirname(userPath), { recursive: true })
      await copyFile(sourcePath, userPath)
      if (platform !== 'win32') await chmod(userPath, 0o755)
      return { binaryPath: userPath, updatePath: userPath }
    } catch {
      return { binaryPath: sourcePath }
    }
  }

  return { binaryPath: userPath }
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
