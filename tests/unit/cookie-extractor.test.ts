import { describe, expect, it } from 'vitest'
import {
  CookieExtractor,
  UnsupportedBrowserError,
  UnsupportedPlatformError
} from '../../src/main/services/cookie-extractor'

function fakeFileSystem(files: string[], directories: Record<string, string[]> = {}) {
  const fileSet = new Set(files)
  return {
    fileExists: (path: string) => fileSet.has(path),
    readDirectory: (path: string) => directories[path] ?? []
  }
}

describe('Chrome-family cookie extractor', () => {
  it('normalizes supported browser names and rejects Firefox and Edge', () => {
    const extractor = new CookieExtractor({ platform: 'linux', homeDir: '/home/test' })

    expect(extractor.normalizeBrowser(' Chrome ')).toBe('chrome')
    expect(extractor.normalizeBrowser('CHROMIUM')).toBe('chromium')
    expect(extractor.normalizeBrowser('brave')).toBe('brave')
    expect(() => extractor.normalizeBrowser('firefox')).toThrow(UnsupportedBrowserError)
    expect(() => extractor.normalizeBrowser('edge')).toThrow(UnsupportedBrowserError)
  })

  it('discovers Linux default and additional Chrome profiles', () => {
    const root = '/home/test/.config/google-chrome'
    const files = [
      `${root}/Default/Cookies`,
      `${root}/Profile 1/Cookies`,
      `${root}/Profile 2/Cookies`
    ]
    const extractor = new CookieExtractor({
      platform: 'linux',
      homeDir: '/home/test',
      ...fakeFileSystem(files, { [root]: ['Default', 'Profile 1', 'Profile 2', 'Guest'] })
    })

    expect(extractor.getCookieDbPath('chrome')).toBe(`${root}/Default/Cookies`)
    expect(extractor.getAllCookiePaths('chrome')).toEqual(files)
  })

  it('discovers Windows Chromium and Brave profile paths', () => {
    const chromiumRoot = 'C:/Users/test/AppData/Local/Chromium/User Data'
    const braveRoot = 'C:/Users/test/AppData/Local/BraveSoftware/Brave-Browser/User Data'
    const files = [
      `${chromiumRoot}/Default/Network/Cookies`,
      `${braveRoot}/Profile 1/Network/Cookies`
    ]
    const extractor = new CookieExtractor({
      platform: 'win32',
      homeDir: 'C:/Users/test',
      ...fakeFileSystem(files, {
        [chromiumRoot]: ['Default'],
        [braveRoot]: ['Default', 'Profile 1']
      })
    })

    expect(extractor.getAllCookiePaths('chromium')).toEqual([files[0]])
    expect(extractor.getAllCookiePaths('brave')).toEqual([files[1]])
  })

  it('returns installed browsers in stable fallback order', () => {
    const chromeRoot = '/home/test/.config/google-chrome'
    const braveRoot = '/home/test/.config/BraveSoftware/Brave-Browser'
    const extractor = new CookieExtractor({
      platform: 'linux',
      homeDir: '/home/test',
      ...fakeFileSystem([`${braveRoot}/Default/Cookies`], {
        [chromeRoot]: [],
        [braveRoot]: ['Default']
      })
    })

    expect(extractor.findInstalledBrowsers()).toEqual(['brave'])
    expect(extractor.getFallbackOrder('chromium')).toEqual(['chromium', 'chrome', 'brave'])
    expect(extractor.getBestAvailableBrowser('chrome')).toBe('brave')
  })

  it('rejects unsupported operating systems', () => {
    expect(() => new CookieExtractor({ platform: 'darwin', homeDir: '/home/test' })).toThrow(
      UnsupportedPlatformError
    )
  })
})
