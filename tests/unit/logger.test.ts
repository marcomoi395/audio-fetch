import { describe, expect, it, vi } from 'vitest'
import { createLogger } from '../../src/main/utils/logger'

describe('application logger', () => {
  it('does not emit cookies, tokens, or raw secrets', () => {
    const output = vi.fn()
    const logger = createLogger(output)
    const context = {
      cookie: 'session-cookie-value',
      Authorization: 'Bearer secret-token-value',
      nested: { sessionToken: 'nested-token-value', password: 'raw-password-value' }
    }

    logger.error('download failed', context)

    expect(output).toHaveBeenCalledOnce()
    const message = output.mock.calls[0][0] as string
    expect(message).not.toContain('session-cookie-value')
    expect(message).not.toContain('secret-token-value')
    expect(message).not.toContain('nested-token-value')
    expect(message).not.toContain('raw-password-value')
  })
})
