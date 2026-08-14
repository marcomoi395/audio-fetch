export enum DownloadTier {
  Tier1 = 'tier1',
  Tier2 = 'tier2',
  Tier3 = 'tier3'
}

export type TierAttempt = Record<string, unknown>
export type TierStrategyOptions = {
  cookiesConfigured?: boolean
  fallbackEnabled?: boolean
  tier1Attempts?: number
  mobileFallbackEnabled?: boolean
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

const AUTH_KEYWORDS = [
  'sign in',
  'log in',
  'login',
  'private video',
  'video is private',
  'members-only',
  'members only',
  'confirm your age',
  'age-restricted',
  'age restricted',
  'authentication required',
  'unusual traffic',
  'bot',
  'captcha',
  'verify'
]

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object'
}

function toTierError(error: unknown): TierError {
  const outer = isRecord(error) ? error : {}
  const cause = isRecord(outer.cause) ? outer.cause : {}
  const nestedCause = isRecord(cause.cause) ? cause.cause : {}
  const outerMessage = error instanceof Error ? error.message : outer.message
  const causeMessage = cause instanceof Error ? cause.message : cause.message
  const stage = cause.stage ?? outer.stage
  return {
    statusCode:
      typeof cause.statusCode === 'number'
        ? cause.statusCode
        : typeof nestedCause.statusCode === 'number'
          ? nestedCause.statusCode
          : typeof outer.statusCode === 'number'
            ? outer.statusCode
            : undefined,
    message:
      typeof causeMessage === 'string'
        ? causeMessage
        : typeof nestedCause.message === 'string'
          ? nestedCause.message
          : typeof outerMessage === 'string'
            ? outerMessage
            : undefined,
    stderr:
      typeof cause.stderr === 'string'
        ? cause.stderr
        : typeof nestedCause.stderr === 'string'
          ? nestedCause.stderr
          : typeof outer.stderr === 'string'
            ? outer.stderr
            : undefined,
    stdout:
      typeof cause.stdout === 'string'
        ? cause.stdout
        : typeof nestedCause.stdout === 'string'
          ? nestedCause.stdout
          : typeof outer.stdout === 'string'
            ? outer.stdout
            : undefined,
    exitCode:
      typeof cause.exitCode === 'number'
        ? cause.exitCode
        : typeof nestedCause.exitCode === 'number'
          ? nestedCause.exitCode
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
  const fallbackEnabled = options.fallbackEnabled !== false
  const tier1Attempts = options.tier1Attempts ?? 3
  const attempts: Record<DownloadTier, TierAttempt[]> = {
    [DownloadTier.Tier1]: [
      {},
      { userAgent: USER_AGENT },
      { userAgent: USER_AGENT, sleepRequests: 1 }
    ].slice(0, tier1Attempts),
    [DownloadTier.Tier2]:
      fallbackEnabled && options.mobileFallbackEnabled !== false
        ? [
            { extractorArgs: 'youtube:player_client=android' },
            { extractorArgs: 'youtube:player_client=mweb' }
          ]
        : [],
    [DownloadTier.Tier3]:
      fallbackEnabled && options.cookiesConfigured ? [{ useManualCookies: true }] : []
  }

  return {
    getAttempts(tier: DownloadTier): TierAttempt[] {
      return attempts[tier].map((attempt) => ({ ...attempt }))
    }
  }
}

function errorText(error: unknown): string {
  const source = toTierError(error)
  return [source.message, source.stderr, source.stdout].filter(Boolean).join('\n').toLowerCase()
}

export function shouldEscalateOnError(error: unknown): boolean {
  const source = toTierError(error)
  const text = [source.message, source.stderr, source.stdout].filter(Boolean).join('\n')
  const match = text.match(/HTTP Error (401|403|429)\b/i)
  const statusCode = source.statusCode ?? (match ? Number(match[1]) : undefined)
  return (
    Boolean(statusCode && [401, 403, 429].includes(statusCode)) ||
    AUTH_KEYWORDS.some((keyword) => text.toLowerCase().includes(keyword))
  )
}

export function isAuthenticationRequired(error: unknown): boolean {
  return AUTH_KEYWORDS.some((keyword) => errorText(error).includes(keyword))
}

export function getNextTier(tier: DownloadTier): DownloadTier | null {
  if (tier === DownloadTier.Tier1) return DownloadTier.Tier2
  if (tier === DownloadTier.Tier2) return DownloadTier.Tier3
  return null
}

function nextNonEmptyTier(strategy: TierStrategy, tier: DownloadTier): DownloadTier | null {
  let nextTier = getNextTier(tier)
  while (nextTier && strategy.getAttempts(nextTier).length === 0) nextTier = getNextTier(nextTier)
  return nextTier
}

function attemptLabel(tier: DownloadTier, flags: TierAttempt, attempt: number): string {
  if (tier === DownloadTier.Tier1) return `tier=1 attempt=${attempt}`
  if (tier === DownloadTier.Tier2) {
    const client = flags.extractorArgs === 'youtube:player_client=mweb' ? 'mweb' : 'android'
    return `tier=2 client=${client}`
  }
  return 'tier=3 manual-cookie'
}

export async function executeTierStrategy(
  strategy: TierStrategy,
  attempt: (flags: TierAttempt) => Promise<unknown>,
  startTier: DownloadTier = DownloadTier.Tier1,
  logAttempt: (message: string) => void = () => undefined
): Promise<TierExecutionResult> {
  let tier: DownloadTier | null = startTier
  let lastTier = startTier
  let attempts = 0
  let lastError: TierError | undefined

  while (tier) {
    lastTier = tier
    const tierAttempts = strategy.getAttempts(tier)
    if (tierAttempts.length === 0) {
      const nextTier = nextNonEmptyTier(strategy, tier)
      if (!nextTier) return { success: false, tier: lastTier, attempts, lastError }
      tier = nextTier
      continue
    }
    for (const [index, flags] of tierAttempts.entries()) {
      attempts += 1
      logAttempt(attemptLabel(tier, flags, index + 1))
      try {
        await attempt(flags)
        return { success: true, tier, attempts }
      } catch (error) {
        lastError = toTierError(error)
        if (!shouldEscalateOnError(lastError)) return { success: false, tier, attempts, lastError }
      }
    }
    const nextTier = nextNonEmptyTier(strategy, tier)
    if (!nextTier) return { success: false, tier: lastTier, attempts, lastError }
    tier = nextTier
  }
  return { success: false, tier: lastTier, attempts, lastError }
}
