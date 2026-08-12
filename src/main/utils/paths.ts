import { join } from 'node:path'

type ElectronApp = { getPath(name: 'userData'): string }

export function getConfigPath(userDataPath: string): string {
  return join(userDataPath, 'config.json')
}

export function getLogPath(userDataPath: string): string {
  return join(userDataPath, 'logs', 'app.log')
}

export function getElectronConfigPath(app: ElectronApp): string {
  return getConfigPath(app.getPath('userData'))
}
