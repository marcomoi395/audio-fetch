type LogOutput = (message: string) => void

function isSensitiveKey(key: string): boolean {
  const normalized = key.toLowerCase()
  return ['cookie', 'token', 'password', 'secret', 'authorization', 'apikey'].some((part) =>
    normalized.includes(part)
  )
}

function sanitize(value: unknown, seen = new WeakSet<object>()): unknown {
  if (value instanceof Error) return { name: value.name, message: '[REDACTED]' }
  if (Array.isArray(value)) return value.map((entry) => sanitize(entry, seen))
  if (!value || typeof value !== 'object') return value
  if (seen.has(value)) return '[Circular]'
  seen.add(value)

  return Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [
      key,
      isSensitiveKey(key) ? '[REDACTED]' : sanitize(entry, seen)
    ])
  )
}

function serialize(value: unknown): string {
  try {
    return JSON.stringify(sanitize(value))
  } catch {
    return '[Unserializable context]'
  }
}

export function createLogger(output: LogOutput = console.error) {
  return {
    error(message: string, context: Record<string, unknown> = {}): void {
      output(`${message} ${serialize(context)}`)
    },
    warn(message: string, context: Record<string, unknown> = {}): void {
      output(`${message} ${serialize(context)}`)
    }
  }
}
