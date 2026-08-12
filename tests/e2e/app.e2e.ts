import { _electron as electron } from 'playwright'
import { expect, test } from '@playwright/test'
import { resolve } from 'node:path'

test('launches the built Electron application', async () => {
  const app = await electron.launch({ args: [resolve(process.cwd(), 'out/main/index.js')] })

  try {
    const window = await app.firstWindow()
    await expect(window).toHaveURL(/file:.*out.*renderer.*index[.]html/)
    await expect(window).toHaveTitle(/Audio Fetch|Electron/i)
    await expect(window.locator('body')).toBeVisible()
    expect(
      await window.evaluate(() => ({
        hasAudioFetch: typeof window.audioFetch?.queue?.getStatus === 'function',
        hasElectron: 'electron' in window,
        hasLegacyApi: 'api' in window
      }))
    ).toEqual({ hasAudioFetch: true, hasElectron: false, hasLegacyApi: false })
  } finally {
    await app.close()
  }
})

test('runs offline input to loading to info to download transitions', async () => {
  const app = await electron.launch({
    args: [resolve(process.cwd(), 'out/main/index.js')],
    env: { ...process.env, AUDIO_FETCH_E2E_FIXTURE: '1' }
  })

  try {
    const window = await app.firstWindow()
    await window.locator('#youtube-url').fill('https://youtube.com/watch?v=fixture')
    await window.locator('#fetch-btn').click()
    await expect(window.locator('#videoInfoStatus')).toHaveText('Loading...')
    await expect(window.locator('#info-section')).toBeVisible()
    await expect(window.locator('#video-title')).toHaveText('Fixture Video')

    await window.locator('#download-btn').click()
    await expect(window.locator('#videoInfoStatus')).toHaveText(
      /Downloaded: \/downloads\/fixture[.]mp3/
    )
  } finally {
    await app.close()
  }
})
