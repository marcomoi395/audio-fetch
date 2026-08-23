import youtubeDl, { create, update } from 'youtube-dl-exec'
import type { YtDlpRuntime } from '../utils/binaries'

type YtDlpExecutor = (url: string, options: Record<string, unknown>) => Promise<unknown>
type YtDlpClient = YtDlpExecutor
type YtDlpModule = {
  create?: (binaryPath: string) => YtDlpClient
  update?: (binaryPath: string) => Promise<unknown>
  default: YtDlpClient
}

const defaultModule: YtDlpModule = { create, update, default: youtubeDl }

function loadYtDlpModule(): YtDlpModule {
  return defaultModule
}

export async function createYtDlpExecutor(
  runtime: YtDlpRuntime,
  resolveModule: () => YtDlpModule = loadYtDlpModule
): Promise<YtDlpExecutor> {
  const module = resolveModule()
  const client = module.create ? module.create(runtime.binaryPath) : module.default
  return (url, options) => client(url, options)
}

export async function updateYtDlp(
  runtime: YtDlpRuntime,
  log: (message: string) => void = () => undefined,
  resolveModule: () => YtDlpModule = loadYtDlpModule
): Promise<void> {
  if (!runtime.updatePath) return

  try {
    const module = resolveModule()
    if (!module.update) throw new Error('yt-dlp updater is unavailable')
    await module.update(runtime.updatePath)
    log('yt-dlp updated successfully')
  } catch {
    log('yt-dlp update failed; using the existing binary')
  }
}
