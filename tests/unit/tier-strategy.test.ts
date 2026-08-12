import { describe, expect, it, vi } from 'vitest'
import {
  DownloadTier,
  createTierStrategy,
  executeTierStrategy,
  getNextTier,
  shouldEscalateOnError
} from '../../src/main/services/tier-strategy'

describe('three-tier download strategy', () => {
  it('defines Tier 1 attempts in order', () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: true })

    expect(strategy.getAttempts(DownloadTier.Tier1)).toEqual([
      {},
      { userAgent: expect.any(String) },
      { userAgent: expect.any(String), sleepRequests: 1 }
    ])
  })

  it('succeeds on the first Tier 1 attempt', async () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: true })
    const attempt = vi.fn().mockResolvedValue(undefined)

    await expect(executeTierStrategy(strategy, attempt)).resolves.toEqual({
      success: true,
      tier: DownloadTier.Tier1,
      attempts: 1
    })
  })

  it('defines Tier 2 browser-cookie attempts', () => {
    const strategy = createTierStrategy({ browser: 'brave', tier3Enabled: true })

    expect(strategy.getAttempts(DownloadTier.Tier2)).toEqual([
      { cookiesFromBrowser: 'brave' },
      { cookiesFromBrowser: 'brave', userAgent: expect.any(String) }
    ])
  })

  it('succeeds on the first Tier 2 attempt', async () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: true })
    const attempt = vi
      .fn()
      .mockRejectedValueOnce({ statusCode: 403 })
      .mockRejectedValueOnce({ statusCode: 403 })
      .mockRejectedValueOnce({ statusCode: 403 })
      .mockResolvedValueOnce(undefined)

    await expect(executeTierStrategy(strategy, attempt)).resolves.toEqual({
      success: true,
      tier: DownloadTier.Tier2,
      attempts: 4
    })
  })
  it('defines Tier 3 android and mweb attempts without cookies', () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: true })

    expect(strategy.getAttempts(DownloadTier.Tier3)).toEqual([
      { playerClient: ['android'] },
      { playerClient: ['mweb'] }
    ])
    expect(
      createTierStrategy({ browser: 'chrome', tier3Enabled: false }).getAttempts(DownloadTier.Tier3)
    ).toEqual([])
  })

  it('escalates on approved status codes and bot/auth keywords only', () => {
    expect(shouldEscalateOnError({ statusCode: 401 })).toBe(true)
    expect(shouldEscalateOnError({ statusCode: 403 })).toBe(true)
    expect(shouldEscalateOnError({ statusCode: 429 })).toBe(true)
    expect(shouldEscalateOnError({ message: 'Sign in to confirm you are not a bot' })).toBe(true)
    expect(shouldEscalateOnError({ statusCode: 404, message: 'not found' })).toBe(false)
    expect(shouldEscalateOnError({ statusCode: 500, message: 'temporary error' })).toBe(false)
  })

  it('succeeds on the first Tier 3 attempt', async () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: true })
    const attempt = vi.fn().mockResolvedValue(undefined)

    await expect(executeTierStrategy(strategy, attempt, DownloadTier.Tier3)).resolves.toEqual({
      success: true,
      tier: DownloadTier.Tier3,
      attempts: 1
    })
  })

  it('executes Tier 3 once per client and returns terminal exhaustion', async () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: true })
    const attempt = vi.fn().mockRejectedValue({ statusCode: 403, message: 'forbidden' })

    await expect(executeTierStrategy(strategy, attempt, DownloadTier.Tier3)).resolves.toEqual({
      success: false,
      tier: DownloadTier.Tier3,
      attempts: 2
    })
    expect(attempt).toHaveBeenNthCalledWith(1, { playerClient: ['android'] })
    expect(attempt).toHaveBeenNthCalledWith(2, { playerClient: ['mweb'] })
  })

  it('consumes all attempts across tiers after approved escalation errors', async () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: true })
    const attempt = vi.fn().mockRejectedValue({ statusCode: 403 })

    await expect(executeTierStrategy(strategy, attempt)).resolves.toEqual({
      success: false,
      tier: DownloadTier.Tier3,
      attempts: 7
    })
  })

  it('returns tier order and terminal exhaustion', () => {
    expect(getNextTier(DownloadTier.Tier1)).toBe(DownloadTier.Tier2)
    expect(getNextTier(DownloadTier.Tier2)).toBe(DownloadTier.Tier3)
    expect(getNextTier(DownloadTier.Tier3)).toBeNull()
  })

  it('stops at Tier 2 when Tier 3 is disabled', async () => {
    const strategy = createTierStrategy({ browser: 'chrome', tier3Enabled: false })
    const attempt = vi.fn().mockRejectedValue({ statusCode: 403 })

    await expect(executeTierStrategy(strategy, attempt)).resolves.toEqual({
      success: false,
      tier: DownloadTier.Tier2,
      attempts: 5
    })
  })
})
