import { describe, expect, it, vi } from 'vitest'
import { confirmAndClose } from '../../src/renderer/src/app'
import {
  bindAudioInteractions,
  createAudioEffects,
  type AudioContextLike,
  type AudioEvent
} from '../../src/renderer/src/audio'

function createContext(
  frequencies: number[] = [],
  state: 'running' | 'suspended' = 'running'
): AudioContextLike {
  return {
    currentTime: 0,
    destination: {},
    state,
    resume: vi.fn().mockResolvedValue(undefined),
    createOscillator: vi.fn(() => {
      let value = 0
      return {
        type: 'square',
        frequency: {
          get value() {
            return value
          },
          set value(next: number) {
            value = next
            frequencies.push(next)
          }
        },
        connect: vi.fn(),
        start: vi.fn(),
        stop: vi.fn()
      }
    }),
    createGain: vi.fn(() => ({
      gain: { value: 0, setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() },
      connect: vi.fn()
    }))
  }
}

describe('renderer audio effects', () => {
  it('plays seven distinct UI sound frequencies through one context', () => {
    const frequencies: number[] = []
    const context = createContext(frequencies)
    const effects = createAudioEffects(() => context)

    for (const event of [
      'click',
      'fetch',
      'download',
      'success',
      'error',
      'hover',
      'focus'
    ] as const) {
      effects.play(event)
    }

    expect(context.createOscillator).toHaveBeenCalledTimes(7)
    expect(context.createGain).toHaveBeenCalledTimes(7)
    expect(frequencies).toEqual([440, 520, 660, 880, 180, 300, 360])
  })

  it('creates one context and resumes it when suspended', () => {
    const context = createContext([], 'suspended')
    const getContext = vi.fn(() => context)
    const effects = createAudioEffects(getContext)

    effects.play('hover')
    effects.play('focus')

    expect(getContext).toHaveBeenCalledOnce()
    expect(context.resume).toHaveBeenCalledOnce()
  })
  it('retries resume after the first resume rejection', async () => {
    const context = createContext([], 'suspended')
    context.resume = vi
      .fn()
      .mockRejectedValueOnce(new Error('Autoplay blocked'))
      .mockResolvedValue(undefined)
    const effects = createAudioEffects(() => context)

    effects.play('hover')
    await Promise.resolve()
    effects.play('focus')

    expect(context.resume).toHaveBeenCalledTimes(2)
  })

  it('binds hover and focus without click when click is disabled', () => {
    const listeners = new Map<string, () => void>()
    const controls = [
      {
        addEventListener: vi.fn((event: string, listener: () => void) => {
          listeners.set(event, listener)
        })
      }
    ]
    const play = vi.fn<(event: AudioEvent) => void>()

    bindAudioInteractions(controls, play, false)
    listeners.get('pointerenter')?.()
    listeners.get('focusin')?.()
    listeners.get('click')?.()

    expect(play.mock.calls).toEqual([['hover'], ['focus']])
  })

  it('binds one hover, focus, and click sound per control', () => {
    const listeners = new Map<string, () => void>()
    const controls = [
      {
        addEventListener: vi.fn((event: string, listener: () => void) => {
          listeners.set(event, listener)
        })
      }
    ]
    const play = vi.fn<(event: AudioEvent) => void>()

    bindAudioInteractions(controls, play)
    listeners.get('pointerenter')?.()
    listeners.get('focusin')?.()
    listeners.get('click')?.()

    expect(play.mock.calls).toEqual([['hover'], ['focus'], ['click']])
  })

  it('swallows audio failures without breaking actions', () => {
    const effects = createAudioEffects(() => {
      throw new Error('Audio unavailable')
    })

    expect(() => effects.play('click')).not.toThrow()
  })
})

describe('renderer close confirmation', () => {
  it('does not close when an active download is declined', async () => {
    const close = vi.fn()
    const queue = { getStatus: vi.fn().mockResolvedValue({ ok: true, data: { active: true } }) }

    await confirmAndClose({ queue, window: { close } }, () => false)

    expect(close).not.toHaveBeenCalled()
  })

  it('passes true after active confirmation', async () => {
    const close = vi.fn().mockResolvedValue({ ok: true, data: null })
    const queue = { getStatus: vi.fn().mockResolvedValue({ ok: true, data: { active: true } }) }

    await confirmAndClose({ queue, window: { close } }, () => true)

    expect(close).toHaveBeenCalledWith(true)
  })

  it('passes false when no download is active', async () => {
    const close = vi.fn().mockResolvedValue({ ok: true, data: null })
    const queue = { getStatus: vi.fn().mockResolvedValue({ ok: true, data: { active: false } }) }

    await confirmAndClose({ queue, window: { close } }, () => false)

    expect(close).toHaveBeenCalledWith(false)
  })
})
