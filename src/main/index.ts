import { app, BrowserWindow } from 'electron'
import { electronApp, optimizer } from '@electron-toolkit/utils'
import { loadConfig } from './services/config'
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
      const config = await loadConfig(getElectronConfigPath(app), (message) => logger.warn(message))
      createWindow({
        width: config.ui.windowWidth,
        height: config.ui.windowHeight,
        title: config.ui.windowTitle
      })
    } catch {
      logger.warn('Config startup failed; using defaults')
      createWindow(DEFAULT_WINDOW_CONFIG)
    }
  })

  app.on('window-all-closed', () => app.quit())
}
