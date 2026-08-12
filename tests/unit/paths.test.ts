import { describe, expect, it } from 'vitest'
import { getConfigPath, getElectronConfigPath, getLogPath } from '../../src/main/utils/paths'

describe('Electron paths', () => {
  it('resolves config and log paths from Electron user data paths', () => {
    expect(getConfigPath('/tmp/audio-fetch-user-data')).toBe(
      '/tmp/audio-fetch-user-data/config.json'
    )
    expect(getLogPath('/tmp/audio-fetch-user-data')).toBe('/tmp/audio-fetch-user-data/logs/app.log')
  })

  it('uses Electron app.getPath for production config resolution', () => {
    const electronApp = { getPath: () => '/tmp/electron-user-data' }

    expect(getElectronConfigPath(electronApp)).toBe('/tmp/electron-user-data/config.json')
  })
})
