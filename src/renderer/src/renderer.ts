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
  const info = document.getElementById('videoInfo')
  const title = document.getElementById('videoTitle')
  const uploader = document.getElementById('videoUploader')
  const duration = document.getElementById('videoDuration')
  const thumbnail = document.getElementById('videoThumbnail') as HTMLImageElement | null

  if (!status || !info || !title || !uploader || !duration || !thumbnail) return

  if (state.status === 'idle') {
    status.textContent = 'Ready'
    info.hidden = true
    return
  }

  if (state.status === 'loading') {
    status.textContent = 'Loading…'
    info.hidden = true
    return
  }

  if (state.status === 'error') {
    status.textContent = state.message
    info.hidden = true
    return
  }

  status.textContent = 'Video info loaded'
  title.textContent = state.title
  uploader.textContent = state.uploader
  duration.textContent = `${state.duration}s`
  const hasThumbnail = isSafeThumbnailUrl(state.thumbnailUrl)
  thumbnail.hidden = !hasThumbnail
  thumbnail.src = hasThumbnail ? state.thumbnailUrl : ''
  info.hidden = false
}

window.addEventListener('DOMContentLoaded', () => {
  controller.subscribe(render)
  render(controller.getState())

  document.getElementById('videoInfoForm')?.addEventListener('submit', (event) => {
    event.preventDefault()
    const input = document.getElementById('videoUrl') as HTMLInputElement | null
    if (input) void controller.submit(input.value)
  })
})
