export enum DownloadTier {
  Tier1 = 'tier1',
  Tier2 = 'tier2',
  Tier3 = 'tier3'
}

export type TierAttempt = Record<string, unknown>
export type TierStrategyOptions = {
  browser: 'chrome' | 'chromium' | 'brave'
  cookiesEnabled?: boolean
  tier3Enabled: boolean
}
export type TierStrategy = { getAttempts(tier: DownloadTier): TierAttempt[] }
export type TierError = {
  statusCode?: number
  message?: string
  stderr?: string
  stdout?: string
  exitCode?: number
  stage?: 'yt-dlp'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object'
}

function toTierError(error: unknown): TierError {
  const outer = isRecord(error) ? error : {}
  const cause = isRecord(outer.cause) ? outer.cause : {}
  const outerMessage = error instanceof Error ? error.message : outer.message
  const causeMessage = cause instanceof Error ? cause.message : cause.message
  const stage = cause.stage ?? outer.stage
  return {
    statusCode:
      typeof cause.statusCode === 'number'
        ? cause.statusCode
        : typeof outer.statusCode === 'number'
          ? outer.statusCode
          : undefined,
    message:
      typeof causeMessage === 'string'
        ? causeMessage
        : typeof outerMessage === 'string'
          ? outerMessage
          : undefined,
    stderr:
      typeof cause.stderr === 'string'
        ? cause.stderr
        : typeof outer.stderr === 'string'
          ? outer.stderr
          : undefined,
    stdout:
      typeof cause.stdout === 'string'
        ? cause.stdout
        : typeof outer.stdout === 'string'
          ? outer.stdout
          : undefined,
    exitCode:
      typeof cause.exitCode === 'number'
        ? cause.exitCode
        : typeof outer.exitCode === 'number'
          ? outer.exitCode
          : undefined,
    stage: stage === 'yt-dlp' ? stage : undefined
  }
}
export type TierExecutionResult = {
  success: boolean
  tier: DownloadTier | null
  attempts: number
  lastError?: TierError
}

const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

export function createTierStrategy(options: TierStrategyOptions): TierStrategy {
  const attempts: Record<DownloadTier, TierAttempt[]> = {
    [DownloadTier.Tier1]: [
      {},
      { userAgent: USER_AGENT },
      { userAgent: USER_AGENT, sleepRequests: 1 }
    ],
    [DownloadTier.Tier2]: options.cookiesEnabled
      ? [
          { cookiesFromBrowser: options.browser },
          { cookiesFromBrowser: options.browser, userAgent: USER_AGENT }
        ]
      : [],
    [DownloadTier.Tier3]: options.tier3Enabled
      ? [
          { extractorArgs: 'youtube:player_client=android' },
          { extractorArgs: 'youtube:player_client=mweb' }
        ]
      : []
  }

  return {
    getAttempts(tier: DownloadTier): TierAttempt[] {
      return attempts[tier].map((attempt) => ({ ...attempt }))
    }
  }
}

export function shouldEscalateOnError(error: unknown): boolean {
  const source = toTierError(error)
  const text = [source.message, source.stderr, source.stdout].filter(Boolean).join('\n')
  const match = text.match(/HTTP Error (401|403|429)\b/i)
  const statusCode = source.statusCode ?? (match ? Number(match[1]) : undefined)
  if (statusCode && [401, 403, 429].includes(statusCode)) return true
  const message = text.toLowerCase()
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
  let lastError: TierError | undefined

  while (tier) {
    lastTier = tier
    const tierAttempts = strategy.getAttempts(tier)
    if (tierAttempts.length === 0) {
      tier = getNextTier(tier)
      continue
    }

    for (const flags of tierAttempts) {
      attempts += 1
      try {
        await attempt(flags)
        return { success: true, tier, attempts }
      } catch (error) {
        lastError = toTierError(error)
        if (!shouldEscalateOnError(lastError)) return { success: false, tier, attempts, lastError }
      }
    }

    const nextTier = getNextTier(tier)
    if (nextTier === DownloadTier.Tier3 && strategy.getAttempts(nextTier).length === 0) {
      return { success: false, tier, attempts, lastError }
    }
    tier = nextTier
  }

  return { success: false, tier: lastTier, attempts, lastError }
}
