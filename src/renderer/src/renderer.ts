function init(): void {
  window.addEventListener('DOMContentLoaded', () => {
    document.getElementById('ipcHandler')?.addEventListener('click', () => {
      void window.audioFetch.queue.getStatus()
    })
  })
}

init()
