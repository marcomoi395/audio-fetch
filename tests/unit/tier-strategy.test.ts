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
  it('disables fallback tiers when configured off', () => {
    const strategy = createTierStrategy({
      fallbackEnabled: false,
      mobileFallbackEnabled: false,
      cookiesConfigured: true
    })
    expect(strategy.getAttempts(DownloadTier.Tier2)).toEqual([])
    expect(strategy.getAttempts(DownloadTier.Tier3)).toEqual([])
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
  it('preserves outer exit codes in terminal errors', async () => {
    const attempt = vi.fn().mockRejectedValue({ exitCode: 1, message: 'network timeout' })
    await expect(
      executeTierStrategy(createTierStrategy({ tier1Attempts: 1 }), attempt)
    ).resolves.toMatchObject({
      success: false,
      tier: DownloadTier.Tier1,
      attempts: 1,
      lastError: { exitCode: 1, message: 'network timeout' }
    })
  })
  it('unwraps nested downloader error fields', async () => {
    const attempt = vi.fn().mockRejectedValue({
      cause: {
        cause: {
          message: 'network timeout',
          stderr: 'stderr output',
          stdout: 'stdout output',
          exitCode: 1
        }
      }
    })
    await expect(
      executeTierStrategy(createTierStrategy({ tier1Attempts: 1 }), attempt)
    ).resolves.toMatchObject({
      success: false,
      lastError: {
        message: 'network timeout',
        stderr: 'stderr output',
        stdout: 'stdout output',
        exitCode: 1
      }
    })
  })
  it('preserves outer tier error fields', async () => {
    const attempt = vi.fn().mockRejectedValue({
      statusCode: 403,
      stderr: 'stderr output',
      stdout: 'stdout output',
      message: 'network timeout'
    })
    await expect(
      executeTierStrategy(createTierStrategy({ tier1Attempts: 1 }), attempt)
    ).resolves.toMatchObject({
      success: false,
      lastError: {
        statusCode: 403,
        stderr: 'stderr output',
        stdout: 'stdout output',
        message: 'network timeout'
      }
    })
  })

  it('preserves direct cause fields before outer fallbacks', async () => {
    const attempt = vi.fn().mockRejectedValue({
      cause: {
        stdout: 'cause stdout output',
        exitCode: 2,
        cause: { statusCode: 403 }
      }
    })
    const strategy = {
      getAttempts: (tier: DownloadTier) => (tier === DownloadTier.Tier1 ? [{}] : [])
    }
    await expect(executeTierStrategy(strategy, attempt)).resolves.toMatchObject({
      success: false,
      lastError: { statusCode: 403, stdout: 'cause stdout output', exitCode: 2 }
    })
  })

  it('preserves nested status codes after direct causes', async () => {
    const attempt = vi.fn().mockRejectedValue({
      cause: { cause: { statusCode: 403 } }
    })
    const strategy = {
      getAttempts: (tier: DownloadTier) => (tier === DownloadTier.Tier1 ? [{}] : [])
    }
    await expect(executeTierStrategy(strategy, attempt)).resolves.toMatchObject({
      success: false,
      lastError: { statusCode: 403 }
    })
  })

  it('preserves tier ordering helpers', () => {
    expect(getNextTier(DownloadTier.Tier1)).toBe(DownloadTier.Tier2)
    expect(getNextTier(DownloadTier.Tier2)).toBe(DownloadTier.Tier3)
    expect(getNextTier(DownloadTier.Tier3)).toBeNull()
  })
  it('skips empty tiers before executing the next available tier', async () => {
    const strategy = {
      getAttempts: (tier: DownloadTier) => (tier === DownloadTier.Tier2 ? [{}] : [])
    }

    await expect(
      executeTierStrategy(strategy, vi.fn().mockResolvedValue(undefined))
    ).resolves.toEqual({
      success: true,
      tier: DownloadTier.Tier2,
      attempts: 1
    })
  })

  it('returns success immediately when an attempt completes', async () => {
    const strategy = createTierStrategy({ tier1Attempts: 1 })
    await expect(
      executeTierStrategy(strategy, vi.fn().mockResolvedValue(undefined))
    ).resolves.toEqual({
      success: true,
      tier: DownloadTier.Tier1,
      attempts: 1
    })
  })
})
