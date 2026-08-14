import { readFile, stat } from 'node:fs/promises'
import { describe, expect, it } from 'vitest'
import {
  createManualCookieStore,
  validateNetscapeCookies
} from '../../src/main/services/cookie-store'

const VALID_COOKIES = [
  '# Netscape HTTP Cookie File',
  '#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tsecret-value',
  '.google.com\tTRUE\t/\tTRUE\t0\tHSID\tgoogle-value',
  'accounts.google.com\tFALSE\t/\tFALSE\t0\tPREF\tlang=en'
].join('\n')

describe('manual Netscape cookies', () => {
  it('accepts comments, HttpOnly domains, and YouTube/Google auth domains', () => {
    expect(validateNetscapeCookies(VALID_COOKIES)).toBe(VALID_COOKIES)
  })

  it('rejects malformed rows and unrelated domains', () => {
    expect(() => validateNetscapeCookies('youtube.com\tTRUE\t/\tTRUE\t0\tSID')).toThrow(
      'Invalid Netscape cookie format'
    )
    expect(() => validateNetscapeCookies('evil.example\tTRUE\t/\tTRUE\t0\tSID\tvalue')).toThrow(
      'Unsupported cookie domain'
    )
  })

  it('writes a 0600 temporary cookie file and removes it in finally', async () => {
    const store = createManualCookieStore()
    store.set(VALID_COOKIES)
    let filePath = ''

    await store.withCookieFile(async (path) => {
      filePath = path
      expect(await readFile(path, 'utf8')).toBe(VALID_COOKIES)
      expect((await stat(path)).mode & 0o777).toBe(0o600)
    })

    await expect(stat(filePath)).rejects.toMatchObject({ code: 'ENOENT' })
  })

  it('clears cookies without exposing them in configuration state', () => {
    const store = createManualCookieStore()
    expect(store.isConfigured()).toBe(false)
    store.set(VALID_COOKIES)
    expect(store.isConfigured()).toBe(true)
    store.clear()
    expect(store.isConfigured()).toBe(false)
  })
})
