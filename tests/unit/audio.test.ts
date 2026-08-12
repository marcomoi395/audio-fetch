import { describe, expect, it, vi } from 'vitest'
import { confirmAndClose } from '../../src/renderer/src/app'
import { createAudioEffects, type AudioContextLike } from '../../src/renderer/src/audio'

function createContext(frequencies: number[] = []): AudioContextLike {
  return {
    currentTime: 0,
    destination: {},
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
  it('plays five distinct UI sound frequencies', () => {
    const frequencies: number[] = []
    const context = createContext(frequencies)
    const effects = createAudioEffects(() => context)

    for (const event of ['click', 'fetch', 'download', 'success', 'error'] as const) {
      effects.play(event)
    }

    expect(context.createOscillator).toHaveBeenCalledTimes(5)
    expect(context.createGain).toHaveBeenCalledTimes(5)
    expect(frequencies).toEqual([440, 520, 660, 880, 180])
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
