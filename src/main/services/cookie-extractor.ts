import { existsSync, readdirSync } from 'node:fs'

export type SupportedBrowser = 'chrome' | 'chromium' | 'brave'
export type SupportedPlatform = 'linux' | 'win32'

type FileSystem = {
  fileExists: (path: string) => boolean
  readDirectory: (path: string) => string[]
}

type CookieExtractorOptions = Partial<FileSystem> & {
  platform: string
  homeDir: string
}

export class UnsupportedBrowserError extends Error {
  constructor(browser: string) {
    super(`Unsupported browser: ${browser}`)
    this.name = 'UnsupportedBrowserError'
  }
}

export class UnsupportedPlatformError extends Error {
  constructor(platform: string) {
    super(`Unsupported platform: ${platform}`)
    this.name = 'UnsupportedPlatformError'
  }
}

const BROWSERS: SupportedBrowser[] = ['chrome', 'chromium', 'brave']
const DEFAULT_FILE_SYSTEM: FileSystem = {
  fileExists: (path) => existsSync(path),
  readDirectory: (path) => readdirSync(path, { encoding: 'utf8' })
}

export class CookieExtractor {
  private readonly platform: SupportedPlatform
  private readonly homeDir: string
  private readonly fileSystem: FileSystem

  constructor(options: CookieExtractorOptions) {
    if (options.platform !== 'linux' && options.platform !== 'win32') {
      throw new UnsupportedPlatformError(options.platform)
    }

    this.platform = options.platform
    this.homeDir = options.homeDir
    this.fileSystem = { ...DEFAULT_FILE_SYSTEM, ...options }
  }

  normalizeBrowser(browser: string): SupportedBrowser {
    const normalized = browser.trim().toLowerCase()
    if (!BROWSERS.includes(normalized as SupportedBrowser)) {
      throw new UnsupportedBrowserError(browser)
    }
    return normalized as SupportedBrowser
  }

  getCookieDbPath(browser: string, profile = 'Default'): string {
    const normalized = this.normalizeBrowser(browser)
    const root = this.getUserDataRoot(normalized)
    return this.platform === 'win32'
      ? `${root}/${profile}/Network/Cookies`
      : `${root}/${profile}/Cookies`
  }

  getAllCookiePaths(browser: string): string[] {
    const normalized = this.normalizeBrowser(browser)
    const root = this.getUserDataRoot(normalized)
    const profileNames = this.fileSystem.readDirectory(root).filter((name) => {
      return name === 'Default' || /^Profile \d+$/.test(name)
    })
    return profileNames
      .map((profile) => this.getCookieDbPath(normalized, profile))
      .filter((path) => this.fileSystem.fileExists(path))
  }

  isBrowserInstalled(browser: string): boolean {
    return this.getAllCookiePaths(browser).length > 0
  }

  findInstalledBrowsers(): SupportedBrowser[] {
    return BROWSERS.filter((browser) => this.isBrowserInstalled(browser))
  }

  getFallbackOrder(preferred: string): SupportedBrowser[] {
    const normalized = this.normalizeBrowser(preferred)
    return [normalized, ...BROWSERS.filter((browser) => browser !== normalized)]
  }

  getBestAvailableBrowser(preferred: string): SupportedBrowser | null {
    return (
      this.getFallbackOrder(preferred).find((browser) => this.isBrowserInstalled(browser)) ?? null
    )
  }

  private getUserDataRoot(browser: SupportedBrowser): string {
    if (this.platform === 'linux') {
      const roots: Record<SupportedBrowser, string> = {
        chrome: `${this.homeDir}/.config/google-chrome`,
        chromium: `${this.homeDir}/.config/chromium`,
        brave: `${this.homeDir}/.config/BraveSoftware/Brave-Browser`
      }
      return roots[browser]
    }

    const roots: Record<SupportedBrowser, string> = {
      chrome: `${this.homeDir}/AppData/Local/Google/Chrome/User Data`,
      chromium: `${this.homeDir}/AppData/Local/Chromium/User Data`,
      brave: `${this.homeDir}/AppData/Local/BraveSoftware/Brave-Browser/User Data`
    }
    return roots[browser]
  }
}
