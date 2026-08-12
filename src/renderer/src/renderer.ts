import { createRendererController, type RendererState } from './app'

function isSafeThumbnailUrl(value: string): boolean {
  try {
    return new URL(value).protocol === 'https:'
  } catch {
    return false
  }
}

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

  status.textContent = 'Video info loaded'
  title.textContent = state.title
  uploader.textContent = state.uploader
  duration.textContent = `${state.duration}s`
  const hasThumbnail = isSafeThumbnailUrl(state.thumbnailUrl)
  thumbnail.hidden = !hasThumbnail
  thumbnail.src = hasThumbnail ? state.thumbnailUrl : ''
}

window.addEventListener('DOMContentLoaded', () => {
  controller.subscribe(render)
  render(controller.getState())

  document.getElementById('videoInfoForm')?.addEventListener('submit', (event) => {
    event.preventDefault()
    const input = document.getElementById('youtube-url') as HTMLInputElement | null
    if (input) void controller.submit(input.value)
  })
})
