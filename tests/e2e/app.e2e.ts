import { _electron as electron } from 'playwright'
import { expect, test } from '@playwright/test'
import { resolve } from 'node:path'

test('launches the built Electron application', async () => {
  const app = await electron.launch({ args: [resolve(process.cwd(), 'out/main/index.js')] })

  try {
    const window = await app.firstWindow()
    await expect(window).toHaveURL(/file:.*out[\\/]renderer[\\/]index\.html/)
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
