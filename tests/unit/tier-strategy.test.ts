import { describe, expect, it, vi } from 'vitest'
import {
  DownloadTier,
  createTierStrategy,
  executeTierStrategy,
  getNextTier,
  isAuthenticationRequired,
  shouldEscalateOnError
} from '../../src/main/services/tier-strategy'
import { DownloadExecutionError } from '../../src/main/services/downloader'

describe('three-tier download strategy', () => {
  it('orders Tier 1, mobile Tier 2, manual-cookie Tier 3', () => {
    const strategy = createTierStrategy({ cookiesConfigured: true })
    expect(strategy.getAttempts(DownloadTier.Tier1)).toEqual([
      {},
      { userAgent: expect.any(String) },
      { userAgent: expect.any(String), sleepRequests: 1 }
    ])
    expect(strategy.getAttempts(DownloadTier.Tier2)).toEqual([
      { extractorArgs: 'youtube:player_client=android' },
      { extractorArgs: 'youtube:player_client=mweb' }
    ])
    expect(strategy.getAttempts(DownloadTier.Tier3)).toEqual([{ useManualCookies: true }])
  })

  it('keeps manual cookies optional', () => {
    expect(createTierStrategy({}).getAttempts(DownloadTier.Tier3)).toEqual([])
  })

  it('executes all enabled tiers after escalation errors', async () => {
    const strategy = createTierStrategy({ cookiesConfigured: true, tier1Attempts: 1 })
    const attempt = vi.fn().mockRejectedValue({ statusCode: 403 })

    await expect(executeTierStrategy(strategy, attempt)).resolves.toMatchObject({
      success: false,
      tier: DownloadTier.Tier3,
      attempts: 4,
      lastError: { statusCode: 403 }
    })
    expect(attempt).toHaveBeenNthCalledWith(2, { extractorArgs: 'youtube:player_client=android' })
    expect(attempt).toHaveBeenNthCalledWith(3, { extractorArgs: 'youtube:player_client=mweb' })
    expect(attempt).toHaveBeenNthCalledWith(4, { useManualCookies: true })
  })

  it('recognizes auth failures without classifying unrelated failures', () => {
    expect(isAuthenticationRequired({ stderr: 'This video is private' })).toBe(true)
    expect(isAuthenticationRequired({ stderr: 'network timeout' })).toBe(false)
    expect(shouldEscalateOnError({ statusCode: 403 })).toBe(true)
    expect(shouldEscalateOnError({ statusCode: 404 })).toBe(false)
    expect(shouldEscalateOnError(new Error('network timeout'))).toBe(false)
  })

  it('unwraps downloader causes', () => {
    const cause = new DownloadExecutionError({ stderr: 'HTTP Error 403: Forbidden' })
    expect(shouldEscalateOnError(new Error('Unable to download audio', { cause }))).toBe(true)
  })

  it('preserves tier ordering helpers', () => {
    expect(getNextTier(DownloadTier.Tier1)).toBe(DownloadTier.Tier2)
    expect(getNextTier(DownloadTier.Tier2)).toBe(DownloadTier.Tier3)
    expect(getNextTier(DownloadTier.Tier3)).toBeNull()
  })
})
