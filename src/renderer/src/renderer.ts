import type { DownloadFormat, DownloadQuality } from '../../shared/ipc'
import { createRendererController, type RendererState } from './app'

function isSafeThumbnailUrl(value: string): boolean {
  try {
    return new URL(value).protocol === 'https:'
  } catch {
    return false
  }
}
const DOWNLOAD_FORMATS: DownloadFormat[] = ['mp3', 'm4a', 'opus', 'wav', 'best']
const DOWNLOAD_QUALITIES: DownloadQuality[] = ['0', '5', '9']

const controller = createRendererController(window.audioFetch)

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

  document.getElementById('videoInfoForm')?.addEventListener('submit', (event) => {
    event.preventDefault()
    const input = document.getElementById('youtube-url') as HTMLInputElement | null
    if (input) void controller.submit(input.value)
  })

  document.getElementById('retry-btn')?.addEventListener('click', () => {
    void controller.retry()
  })

  document.getElementById('new-url-btn')?.addEventListener('click', () => {
    controller.newUrl()
    const input = document.getElementById('youtube-url') as HTMLInputElement | null
    if (input) input.value = ''
  })

  document.getElementById('download-btn')?.addEventListener('click', () => {
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
})
