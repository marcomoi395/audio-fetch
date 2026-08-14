export type AudioEvent = 'click' | 'fetch' | 'download' | 'success' | 'error' | 'hover' | 'focus'

export type AudioNodeLike = {
  connect(node: unknown): void
}

export type AudioContextLike = {
  currentTime: number
  destination: unknown
  state?: string
  resume?: () => Promise<void>
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

export type AudioInteractiveElement = {
  addEventListener(type: string, listener: () => void): void
}

const FREQUENCY: Record<AudioEvent, number> = {
  click: 440,
  fetch: 520,
  download: 660,
  success: 880,
  error: 180,
  hover: 300,
  focus: 360
}

export function createAudioEffects(getContext: () => AudioContextLike = () => new AudioContext()): {
  play(event: AudioEvent): void
} {
  let context: AudioContextLike | undefined
  let resumeRequested = false

  return {
    play(event): void {
      try {
        context ??= getContext()
        if (context.state === 'suspended' && !resumeRequested) {
          resumeRequested = true
          const resume = context.resume?.()
          if (resume)
            void resume.catch(() => {
              resumeRequested = false
            })
        }

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

export function bindAudioInteractions(
  controls: Iterable<AudioInteractiveElement>,
  play: (event: AudioEvent) => void,
  includeClick = true
): void {
  for (const control of controls) {
    control.addEventListener('pointerenter', () => play('hover'))
    control.addEventListener('focusin', () => play('focus'))
    if (includeClick) control.addEventListener('click', () => play('click'))
  }
}
