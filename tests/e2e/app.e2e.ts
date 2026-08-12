import { _electron as electron } from 'playwright'
import { expect, test } from '@playwright/test'
import { resolve } from 'node:path'

test('launches the built Electron application', async () => {
  const app = await electron.launch({ args: [resolve(process.cwd(), 'out/main/index.js')] })

  try {
    const window = await app.firstWindow()
    await expect(window).toHaveURL(/file:.*out[\\/]renderer[\\/]index\.html/)
    await expect(window).toHaveTitle(/Audio Fetch|Electron/i)
  } finally {
    await app.close()
  }
})
