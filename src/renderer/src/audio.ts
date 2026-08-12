export type AudioEvent = 'click' | 'fetch' | 'download' | 'success' | 'error'

export type AudioNodeLike = {
  connect(node: unknown): void
}

export type AudioContextLike = {
  currentTime: number
  destination: unknown
  createOscillator(): {
    type: string
    frequency: { value: number }
    connect(node: unknown): void
    start(): void
    stop(when?: number): void
  }
  createGain(): {
    gain: {
      value: number
      setValueAtTime(value: number, when: number): void
      exponentialRampToValueAtTime(value: number, when: number): void
    }
    connect(node: unknown): void
  }
}

const FREQUENCY: Record<AudioEvent, number> = {
  click: 440,
  fetch: 520,
  download: 660,
  success: 880,
  error: 180
}

export function createAudioEffects(getContext: () => AudioContextLike = () => new AudioContext()): {
  play(event: AudioEvent): void
} {
  return {
    play(event): void {
      try {
        const context = getContext()
        const oscillator = context.createOscillator()
        const gain = context.createGain()
        const now = context.currentTime
        oscillator.type = 'square'
        oscillator.frequency.value = FREQUENCY[event]
        gain.gain.setValueAtTime(0.0001, now)
        gain.gain.exponentialRampToValueAtTime(0.08, now + 0.01)
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.12)
        oscillator.connect(gain)
        gain.connect(context.destination)
        oscillator.start()
        oscillator.stop(now + 0.12)
      } catch {
        // Audio is optional; UI actions must continue when unavailable.
      }
    }
  }
}
