export enum DownloadTier {
  Tier1 = 'tier1',
  Tier2 = 'tier2',
  Tier3 = 'tier3'
}

export type TierAttempt = Record<string, unknown>
export type TierStrategyOptions = {
  browser: 'chrome' | 'chromium' | 'brave'
  tier3Enabled: boolean
}
export type TierStrategy = { getAttempts(tier: DownloadTier): TierAttempt[] }
export type TierError = { statusCode?: number; message?: string }
export type TierExecutionResult = { success: boolean; tier: DownloadTier | null; attempts: number }

const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

export function createTierStrategy(options: TierStrategyOptions): TierStrategy {
  const attempts: Record<DownloadTier, TierAttempt[]> = {
    [DownloadTier.Tier1]: [
      {},
      { userAgent: USER_AGENT },
      { userAgent: USER_AGENT, sleepRequests: 1 }
    ],
    [DownloadTier.Tier2]: [
      { cookiesFromBrowser: options.browser },
      { cookiesFromBrowser: options.browser, userAgent: USER_AGENT }
    ],
    [DownloadTier.Tier3]: options.tier3Enabled
      ? [{ playerClient: ['android'] }, { playerClient: ['mweb'] }]
      : []
  }

  return {
    getAttempts(tier: DownloadTier): TierAttempt[] {
      return attempts[tier].map((attempt) => ({ ...attempt }))
    }
  }
}

export function shouldEscalateOnError(error: TierError): boolean {
  if (error.statusCode && [401, 403, 429].includes(error.statusCode)) return true
  const message = error.message?.toLowerCase() ?? ''
  return ['sign in', 'unusual traffic', 'bot', 'captcha', 'verify', 'confirm your age'].some(
    (keyword) => message.includes(keyword)
  )
}

export function getNextTier(tier: DownloadTier): DownloadTier | null {
  if (tier === DownloadTier.Tier1) return DownloadTier.Tier2
  if (tier === DownloadTier.Tier2) return DownloadTier.Tier3
  return null
}

export async function executeTierStrategy(
  strategy: TierStrategy,
  attempt: (flags: TierAttempt) => Promise<unknown>,
  startTier: DownloadTier = DownloadTier.Tier1
): Promise<TierExecutionResult> {
  let tier: DownloadTier | null = startTier
  let lastTier = startTier
  let attempts = 0

  while (tier) {
    lastTier = tier
    const tierAttempts = strategy.getAttempts(tier)
    if (tierAttempts.length === 0) return { success: false, tier: lastTier, attempts }

    for (const flags of tierAttempts) {
      attempts += 1
      try {
        await attempt(flags)
        return { success: true, tier, attempts }
      } catch (error) {
        if (!shouldEscalateOnError(error as TierError)) return { success: false, tier, attempts }
      }
    }

    const nextTier = getNextTier(tier)
    if (nextTier === DownloadTier.Tier3 && strategy.getAttempts(nextTier).length === 0) {
      return { success: false, tier, attempts }
    }
    tier = nextTier
  }

  return { success: false, tier: lastTier, attempts }
}
