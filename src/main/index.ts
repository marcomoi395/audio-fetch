import { app, BrowserWindow, ipcMain, type WebContents } from 'electron'
import { electronApp, optimizer } from '@electron-toolkit/utils'
import { registerIpcHandlers } from './ipc'
import { createIpcServices } from './ipc/services'
import { loadConfig, saveConfig } from './services/config'
import { createLogger } from './utils/logger'
import { getElectronConfigPath } from './utils/paths'
import { createWindow, DEFAULT_WINDOW_CONFIG, focusExistingWindow } from './window'
import { registerSingleInstance } from './single-instance'

const hasSingleInstance = registerSingleInstance(app, () => {
  const [mainWindow] = BrowserWindow.getAllWindows()
  if (mainWindow) focusExistingWindow(mainWindow)
})

if (hasSingleInstance) {
  void app.whenReady().then(async () => {
    electronApp.setAppUserModelId('com.audiofetch.app')
    app.on('browser-window-created', (_, window) => optimizer.watchWindowShortcuts(window))
    const logger = createLogger()

    try {
      const configPath = getElectronConfigPath(app)
      const config = await loadConfig(configPath, (message) => logger.warn(message))
      await saveConfig(configPath, config)
      createWindow({
        width: config.ui.windowWidth,
        height: config.ui.windowHeight,
        title: config.ui.windowTitle
      })
    } catch {
      logger.warn('Config startup failed; using defaults')
      createWindow(DEFAULT_WINDOW_CONFIG)
    }

    registerIpcHandlers(
      ipcMain,
      createIpcServices((message) => logger.warn(message)),
      (sender) => {
        if (!sender || typeof sender !== 'object') return null
        try {
          return BrowserWindow.fromWebContents(sender as WebContents)
        } catch {
          return null
        }
      }
    )
  })

  app.on('window-all-closed', () => app.quit())
}
