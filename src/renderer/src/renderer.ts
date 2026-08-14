import type {
  DownloadFormat,
  DownloadQuality,
  SettingsSnapshot,
  SupportedBrowser
} from '../../shared/ipc'
import { bindAudioInteractions, createAudioEffects } from './audio'
import { confirmAndClose, createRendererController, type RendererState } from './app'

function isSafeThumbnailUrl(value: string): boolean {
  try {
    return new URL(value).protocol === 'https:'
  } catch {
    return false
  }
}

const DOWNLOAD_FORMATS: DownloadFormat[] = ['mp3', 'm4a', 'opus', 'wav', 'best']
const DOWNLOAD_QUALITIES: DownloadQuality[] = ['0', '5', '9']
const audio = createAudioEffects()
const BROWSER_LABELS: Record<SupportedBrowser, string> = {
  chrome: 'Chrome',
  chromium: 'Chromium',
  brave: 'Brave'
}
let availableBrowsers: SupportedBrowser[] = []

function updateSettingsControls(): void {
  const saveButton = document.getElementById('settings-save-btn') as HTMLButtonElement | null
  if (saveButton) saveButton.disabled = false
}
function renderSettings(settings: SettingsSnapshot): void {
  const enabled = document.getElementById('cookies-enabled') as HTMLInputElement | null
  const browserRow = document.getElementById('browser-row')
  const browserSelect = document.getElementById('browser-select') as HTMLSelectElement | null
  const availability = document.getElementById('browser-availability')
  if (!enabled || !browserRow || !browserSelect || !availability) return

  availableBrowsers = settings.availableBrowsers
  const selectedBrowser = availableBrowsers.includes(settings.browser)
    ? settings.browser
    : (availableBrowsers[0] ?? settings.browser)
  enabled.checked = settings.cookiesEnabled
  browserSelect.value = selectedBrowser
  browserRow.hidden = !settings.cookiesEnabled
  browserSelect.disabled = false
  availability.textContent = availableBrowsers.length
    ? `Available: ${availableBrowsers.map((browser) => BROWSER_LABELS[browser]).join(', ')}`
    : 'No supported browser profile detected. Tier 2 will be skipped.'
  updateSettingsControls()
}

async function loadSettings(): Promise<void> {
  const status = document.getElementById('settings-status')
  try {
    const result = await window.audioFetch.settings.get()
    if (result.ok) renderSettings(result.data)
    else if (status) status.textContent = result.error.message
  } catch {
    if (status) status.textContent = 'Unable to load settings'
  }
}
const controller = createRendererController(window.audioFetch)
let lastRenderedState = ''

function render(state: RendererState): void {
  const status = document.getElementById('videoInfoStatus')
  const input = document.getElementById('input-section')
  const loading = document.getElementById('loading-section')
  const error = document.getElementById('error-section')
  const errorMessage = document.getElementById('error-message')
  const info = document.getElementById('info-section')
  const title = document.getElementById('video-title')
  const uploader = document.getElementById('video-uploader')
  const duration = document.getElementById('video-duration')
  const thumbnail = document.getElementById('video-thumbnail') as HTMLImageElement | null

  if (
    !status ||
    !input ||
    !loading ||
    !error ||
    !errorMessage ||
    !info ||
    !title ||
    !uploader ||
    !duration ||
    !thumbnail
  ) {
    return
  }

  const stateKey = JSON.stringify(state)
  if (stateKey !== lastRenderedState) {
    if (state.status === 'error') audio.play('error')
    if (state.status === 'success' && state.downloadStatus === 'success') audio.play('success')
    lastRenderedState = stateKey
  }

  input.hidden = state.status !== 'idle'
  loading.hidden = state.status !== 'loading'
  error.hidden = state.status !== 'error'
  info.hidden = state.status !== 'success'

  if (state.status === 'idle') {
    status.textContent = 'Ready'
    return
  }
  if (state.status === 'loading') {
    status.textContent = 'Loading...'
    return
  }
  if (state.status === 'error') {
    status.textContent = state.message
    errorMessage.textContent = state.message
    return
  }

  title.textContent = state.title
  uploader.textContent = state.uploader
  duration.textContent = `${state.duration}s`
  const hasThumbnail = isSafeThumbnailUrl(state.thumbnailUrl)
  thumbnail.hidden = !hasThumbnail
  thumbnail.src = hasThumbnail ? state.thumbnailUrl : ''
  if (state.downloadStatus === 'loading') {
    status.textContent = 'Downloading...'
  } else if (state.downloadStatus === 'success') {
    status.textContent = `Downloaded: ${state.downloadPath ?? 'complete'}`
  } else {
    status.textContent = 'Video info loaded'
  }
}

window.addEventListener('DOMContentLoaded', () => {
  controller.subscribe(render)
  render(controller.getState())

  function bindSettingsToggle(): void {
    const toggle = document.getElementById('settings-toggle-btn') as HTMLButtonElement | null
    const content = document.getElementById('settings-content')
    const icon = toggle?.querySelector('.settings-toggle-icon')
    if (!toggle || !content || !icon) return
    toggle.addEventListener('click', () => {
      const expanded = toggle.getAttribute('aria-expanded') === 'true'
      toggle.setAttribute('aria-expanded', String(!expanded))
      content.hidden = expanded
      icon.textContent = expanded ? '▸' : '▾'
    })
  }
  bindSettingsToggle()
  bindAudioInteractions(document.querySelectorAll('button, input, select'), audio.play, false)

  document.getElementById('videoInfoForm')?.addEventListener('submit', (event) => {
    event.preventDefault()
    audio.play('fetch')
    const input = document.getElementById('youtube-url') as HTMLInputElement | null
    if (input) void controller.submit(input.value)
  })
  document.getElementById('retry-btn')?.addEventListener('click', () => {
    audio.play('click')
    void controller.retry()
  })

  document.getElementById('new-url-btn')?.addEventListener('click', () => {
    audio.play('click')
    controller.newUrl()
    const input = document.getElementById('youtube-url') as HTMLInputElement | null
    if (input) input.value = ''
  })

  document.getElementById('download-btn')?.addEventListener('click', () => {
    audio.play('download')
    const format = document.getElementById('format-select') as HTMLSelectElement | null
    const quality = document.getElementById('quality-select') as HTMLSelectElement | null
    if (!format || !quality) return
    if (
      !DOWNLOAD_FORMATS.includes(format.value as DownloadFormat) ||
      !DOWNLOAD_QUALITIES.includes(quality.value as DownloadQuality)
    ) {
      return
    }
    void controller.download(format.value as DownloadFormat, quality.value as DownloadQuality)
  })

  document.getElementById('settings-save-btn')?.addEventListener('click', () => {
    audio.play('click')
    const enabled = document.getElementById('cookies-enabled') as HTMLInputElement | null
    const browser = document.getElementById('browser-select') as HTMLSelectElement | null
    const status = document.getElementById('settings-status')
    if (!enabled || !browser || !status) return
    status.textContent = 'Saving...'
    void window.audioFetch.settings
      .update({ cookiesEnabled: enabled.checked, browser: browser.value as SupportedBrowser })
      .then((result) => {
        if (result.ok) {
          renderSettings(result.data)
          status.textContent = 'Settings saved'
        } else {
          status.textContent = result.error.message
        }
      })
      .catch(() => {
        status.textContent = 'Unable to save settings'
      })
  })

  document.getElementById('cookies-enabled')?.addEventListener('change', () => {
    const browserRow = document.getElementById('browser-row')
    const enabled = document.getElementById('cookies-enabled') as HTMLInputElement | null
    if (browserRow && enabled) browserRow.hidden = !enabled.checked
    updateSettingsControls()
  })
  document.getElementById('browser-select')?.addEventListener('change', updateSettingsControls)

  void loadSettings()

  document.getElementById('minimize-btn')?.addEventListener('click', () => {
    audio.play('click')
    void window.audioFetch.window.minimize()
  })

  document.getElementById('close-btn')?.addEventListener('click', () => {
    audio.play('click')
    void confirmAndClose(window.audioFetch, (message) => window.confirm(message))
  })
})
