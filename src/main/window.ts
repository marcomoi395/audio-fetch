import { BrowserWindow, shell } from 'electron'
import { join } from 'node:path'
import { is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import {
  DEFAULT_WINDOW_CONFIG,
  focusExistingWindow,
  isSafeExternalUrl,
  resolveWindowConfig,
  type WindowConfig
} from './window-policy'

export { DEFAULT_WINDOW_CONFIG, focusExistingWindow, isSafeExternalUrl, resolveWindowConfig }
export type { WindowConfig }

export function createWindow(config: WindowConfig = {}): BrowserWindow {
  const windowConfig = resolveWindowConfig(config)
  const mainWindow = new BrowserWindow({
    width: windowConfig.width,
    height: windowConfig.height,
    title: windowConfig.title,
    frame: false,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => mainWindow.show())
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (isSafeExternalUrl(url)) void shell.openExternal(url).catch(() => undefined)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    void mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    void mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  return mainWindow
}
