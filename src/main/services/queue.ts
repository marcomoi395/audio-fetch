export class BusyDownloadError extends Error {
  readonly code = 'BUSY'

  constructor() {
    super('A download is already in progress')
    this.name = 'BusyDownloadError'
  }
}

export function createDownloadQueue() {
  let active = false

  return {
    getStatus(): { active: boolean } {
      return { active }
    },
    async run<T>(task: () => Promise<T>): Promise<T> {
      if (active) throw new BusyDownloadError()
      active = true
      try {
        return await task()
      } finally {
        active = false
      }
    }
  }
}
