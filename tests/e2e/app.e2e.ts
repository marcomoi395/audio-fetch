import { spawn, type ChildProcess } from 'node:child_process'
import { _electron as electron } from 'playwright'
import { expect, test } from '@playwright/test'
import { resolve } from 'node:path'

const appEntry = resolve(process.cwd(), 'out/main/index.js')
function launchSecondInstance(): ChildProcess {
  return spawn(process.execPath, [appEntry], { env: process.env, stdio: 'ignore' })
}

test('launches the built Electron application', async () => {
  const app = await electron.launch({ args: [appEntry] })

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
test('opens download settings and allows browser selection', async () => {
  const app = await electron.launch({
    args: [`--user-data-dir=/tmp/audio-fetch-settings-e2e-${process.pid}`, appEntry]
  })

  try {
    const window = await app.firstWindow()
    const toggle = window.locator('#settings-toggle-btn')
    await expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await toggle.click()
    await expect(toggle).toHaveAttribute('aria-expanded', 'true')
    await expect(window.locator('#settings-content')).toBeVisible()
    await expect(window.locator('#cookies-enabled')).toBeEnabled()
    await expect(window.locator('#browser-select')).toBeEnabled()
    await window.locator('#cookies-enabled').check()
    await window.locator('#browser-select').selectOption('brave')
    await expect(window.locator('#browser-select')).toHaveValue('brave')
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

    await window.locator('#download-btn').click()
    await expect(window.locator('#videoInfoStatus')).toHaveText(
      /Downloaded: \/downloads\/fixture[.]mp3/
    )
  } finally {
    await app.close()
  }
})

test('renders safe fixture error state', async () => {
  const app = await electron.launch({
    args: [appEntry],
    env: { ...process.env, AUDIO_FETCH_E2E_FIXTURE: 'error' }
  })

  try {
    const window = await app.firstWindow()
    await window.locator('#youtube-url').fill('https://youtube.com/watch?v=fixture')
    await window.locator('#fetch-btn').click()
    await expect(window.locator('#error-section')).toBeVisible()
    await expect(window.locator('#error-message')).toHaveText('Unable to fetch video information')
  } finally {
    await app.close()
  }
})

test('renders download failure safely', async () => {
  const app = await electron.launch({
    args: [appEntry],
    env: { ...process.env, AUDIO_FETCH_E2E_FIXTURE: 'failure' }
  })

  try {
    const window = await app.firstWindow()
    await window.locator('#youtube-url').fill('https://youtube.com/watch?v=fixture')
    await window.locator('#fetch-btn').click()
    await expect(window.locator('#info-section')).toBeVisible()
    await window.locator('#download-btn').click()
    await expect(window.locator('#error-message')).toHaveText('Unable to start download')
  } finally {
    await app.close()
  }
})

test('renders busy error for concurrent fixture downloads', async () => {
  const app = await electron.launch({
    args: [appEntry],
    env: { ...process.env, AUDIO_FETCH_E2E_FIXTURE: 'slow' }
  })

  try {
    const window = await app.firstWindow()
    await window.locator('#youtube-url').fill('https://youtube.com/watch?v=fixture')
    await window.locator('#fetch-btn').click()
    await expect(window.locator('#info-section')).toBeVisible()
    const results = await window.evaluate(async () => {
      const payload = { format: 'mp3' as const, quality: '0' as const }
      const first = window.audioFetch.download.start('https://youtube.com/watch?v=fixture', payload)
      const second = await window.audioFetch.download.start(
        'https://youtube.com/watch?v=fixture',
        payload
      )
      const completed = await first
      return { second, completed }
    })
    expect(results.second).toEqual({
      ok: false,
      error: { code: 'BUSY', message: 'A download is already in progress' }
    })
    expect(results.completed).toEqual({ ok: true, data: { path: '/downloads/fixture.mp3' } })
  } finally {
    await app.close()
  }
})

test('closes through the title-bar close control when inactive', async () => {
  const app = await electron.launch({ args: [appEntry] })

  try {
    const window = await app.firstWindow()
    await window.locator('#close-btn').click()
    await expect.poll(() => app.windows().length).toBe(0)
  } finally {
    await app.close()
  }
})

test('minimizes the window and exposes a draggable title-bar region', async () => {
  const app = await electron.launch({ args: [appEntry] })

  try {
    const window = await app.firstWindow()
    await expect(
      window.locator('#drag-area').evaluate((element) => getComputedStyle(element).webkitAppRegion)
    ).resolves.toBe('drag')
    await window.locator('#minimize-btn').click()
    await expect
      .poll(() =>
        app.evaluate(
          ({ BrowserWindow }) => BrowserWindow.getAllWindows()[0]?.isMinimized() ?? false
        )
      )
      .toBe(true)
  } finally {
    await app.close()
  }
})

test('restores and focuses the first window on a second launch', async () => {
  const first = await electron.launch({ args: [appEntry] })
  await first.firstWindow()
  await first.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0]?.minimize())

  const second = launchSecondInstance()
  try {
    await expect
      .poll(() =>
        first.evaluate(({ BrowserWindow }) => {
          const window = BrowserWindow.getAllWindows()[0]
          return {
            focused: window?.isFocused() ?? false,
            minimized: window?.isMinimized() ?? false
          }
        })
      )
      .toEqual({ focused: true, minimized: false })
  } finally {
    second.kill()
    await first.close()
  }
})
