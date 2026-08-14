import { chmod, mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const MAX_COOKIE_BYTES = 1024 * 1024
const COOKIE_DOMAIN = /^(?:[^.]+\.)*(?:youtube|google|googlevideo)\.com$/i

type CookieFileCallback<T> = (path: string) => Promise<T>

export interface ManualCookieStore {
  set(value: string): void
  clear(): void
  isConfigured(): boolean
  withCookieFile<T>(callback: CookieFileCallback<T>): Promise<T>
}

export function validateNetscapeCookies(value: string): string {
  if (!value || Buffer.byteLength(value, 'utf8') > MAX_COOKIE_BYTES) {
    throw new Error('Invalid Netscape cookie format')
  }

  for (const line of value.split(/\r?\n/)) {
    if (!line.trim() || (line.startsWith('#') && !line.startsWith('#HttpOnly_'))) continue
    const columns = line.split('\t')
    if (columns.length !== 7) throw new Error('Invalid Netscape cookie format')

    const [rawDomain, includeSubdomains, path, secure, expires, name] = columns
    const domain = rawDomain
      .replace(/^#HttpOnly_/i, '')
      .trim()
      .replace(/^\./, '')
    if (!domain || !COOKIE_DOMAIN.test(domain)) throw new Error('Unsupported cookie domain')
    if (!['TRUE', 'FALSE'].includes(includeSubdomains.toUpperCase())) {
      throw new Error('Invalid Netscape cookie format')
    }
    if (!path.startsWith('/') || !['TRUE', 'FALSE'].includes(secure.toUpperCase())) {
      throw new Error('Invalid Netscape cookie format')
    }
    if (!/^\d+$/.test(expires) || !name) throw new Error('Invalid Netscape cookie format')
  }

  return value
}

export function createManualCookieStore(): ManualCookieStore {
  let cookies = ''

  return {
    set(value: string): void {
      cookies = validateNetscapeCookies(value)
    },
    clear(): void {
      cookies = ''
    },
    isConfigured(): boolean {
      return cookies.length > 0
    },
    async withCookieFile<T>(callback: CookieFileCallback<T>): Promise<T> {
      if (!cookies) throw new Error('Manual cookies are not configured')
      const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-cookies-'))
      try {
        await chmod(directory, 0o700)
        const filePath = join(directory, 'cookies.txt')
        await writeFile(filePath, cookies, { encoding: 'utf8', mode: 0o600 })
        return await callback(filePath)
      } finally {
        await rm(directory, { recursive: true, force: true })
      }
    }
  }
}
