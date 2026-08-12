import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname } from 'node:path'

export type AppConfig = {
  schemaVersion: 1
  downloads: { defaultPath: string; format: string; quality: string }
  tierStrategy: {
    browser: string
    fallbackEnabled: boolean
    tier1Attempts: number
    tier3Enabled: boolean
  }
  ui: { windowWidth: number; windowHeight: number; windowTitle: string }
  logging: { level: string; maxBytes: number; backupCount: number }
}

export const DEFAULT_CONFIG: AppConfig = {
  schemaVersion: 1,
  downloads: { defaultPath: '', format: 'mp3', quality: '0' },
  tierStrategy: {
    browser: 'chrome',
    fallbackEnabled: true,
    tier1Attempts: 3,
    tier3Enabled: false
  },
  ui: { windowWidth: 850, windowHeight: 650, windowTitle: 'Audio Fetch' },
  logging: { level: 'WARNING', maxBytes: 10485760, backupCount: 3 }
}

type ConfigLogger = (message: string) => void

function isConfig(value: unknown): value is AppConfig {
  if (!value || typeof value !== 'object') return false
  const config = value as Record<string, unknown>
  const downloads = config.downloads as Record<string, unknown> | undefined
  const tierStrategy = config.tierStrategy as Record<string, unknown> | undefined
  const ui = config.ui as Record<string, unknown> | undefined
  const logging = config.logging as Record<string, unknown> | undefined

  return Boolean(
    config.schemaVersion === 1 &&
    downloads &&
    typeof downloads.defaultPath === 'string' &&
    typeof downloads.format === 'string' &&
    ['mp3', 'm4a', 'opus', 'wav', 'best'].includes(downloads.format) &&
    typeof downloads.quality === 'string' &&
    ['0', '5', '9'].includes(downloads.quality) &&
    tierStrategy &&
    typeof tierStrategy.browser === 'string' &&
    ['chrome', 'chromium', 'brave'].includes(tierStrategy.browser) &&
    typeof tierStrategy.fallbackEnabled === 'boolean' &&
    typeof tierStrategy.tier1Attempts === 'number' &&
    Number.isInteger(tierStrategy.tier1Attempts) &&
    tierStrategy.tier1Attempts >= 1 &&
    tierStrategy.tier1Attempts <= 3 &&
    typeof tierStrategy.tier3Enabled === 'boolean' &&
    ui &&
    typeof ui.windowWidth === 'number' &&
    Number.isFinite(ui.windowWidth) &&
    ui.windowWidth > 0 &&
    typeof ui.windowHeight === 'number' &&
    Number.isFinite(ui.windowHeight) &&
    ui.windowHeight > 0 &&
    typeof ui.windowTitle === 'string' &&
    ui.windowTitle.length > 0 &&
    logging &&
    typeof logging.level === 'string' &&
    typeof logging.maxBytes === 'number' &&
    Number.isInteger(logging.maxBytes) &&
    logging.maxBytes > 0 &&
    typeof logging.backupCount === 'number' &&
    Number.isInteger(logging.backupCount) &&
    logging.backupCount >= 0
  )
}

export async function loadConfig(
  path: string,
  log: ConfigLogger = () => undefined
): Promise<AppConfig> {
  try {
    const raw = await readFile(path, 'utf8')
    const parsed: unknown = JSON.parse(raw)
    if (!isConfig(parsed)) throw new Error('schema')
    return parsed
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return DEFAULT_CONFIG
    log('Invalid config; using defaults')
    return DEFAULT_CONFIG
  }
}

export async function saveConfig(path: string, config: AppConfig): Promise<void> {
  await mkdir(dirname(path), { recursive: true })
  await writeFile(path, `${JSON.stringify(config, null, 2)}\n`, 'utf8')
}
