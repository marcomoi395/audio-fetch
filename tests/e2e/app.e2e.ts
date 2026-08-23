import { test, expect, _electron as electron } from '@playwright/test'
import { resolve } from 'node:path'

const appEntry = resolve(process.cwd(), 'out/main/index.js')

test('launches the built Electron application', async () => {
  const app = await electron.launch({ args: [appEntry] })
  try {
    const window = await app.firstWindow()
    await expect(window.locator('body')).toBeVisible()
    expect(
      await window.evaluate(() => ({
        hasAudioFetch: 'audioFetch' in window,
        hasElectron: 'electron' in window,
        hasLegacyApi: 'api' in window
      }))
    ).toEqual({ hasAudioFetch: true, hasElectron: false, hasLegacyApi: false })
  } finally {
    await app.close()
  }
})

test('opens settings and saves manual Netscape cookies', async () => {
  const app = await electron.launch({
    args: [`--user-data-dir=/tmp/audio-fetch-settings-e2e-${process.pid}`, appEntry]
  })
  try {
    const window = await app.firstWindow()
    await window.locator('#settings-toggle-btn').click()
    await expect(window.locator('#settings-content')).toBeVisible()
    await window.locator('#cookies-input').fill('.youtube.com\tTRUE\t/\tTRUE\t0\tSID\ttest-value')
    await window.locator('#settings-save-btn').click()
    await expect(window.locator('#cookies-configured')).toHaveText('Cookies configured')
  } finally {
    await app.close()
  }
})

test('runs offline input to loading to info to download transitions', async () => {
  const app = await electron.launch({
    args: [appEntry],
    env: { ...process.env, AUDIO_FETCH_E2E_FIXTURE: 'success' }
  })
  try {
    const window = await app.firstWindow()
    await window.locator('#youtube-url').fill('https://youtube.com/watch?v=fixture')
    await window.locator('#fetch-btn').click()
    await expect(window.locator('#videoInfoStatus')).toHaveText('Loading...')
    await expect(window.locator('#info-section')).toBeVisible()
    await expect(window.locator('#video-title')).toHaveText('Fixture Video')
  } finally {
    await app.close()
  }
})
