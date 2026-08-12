import { app, BrowserWindow } from 'electron'
import { electronApp, optimizer } from '@electron-toolkit/utils'
import { createWindow, focusExistingWindow } from './window'
import { registerSingleInstance } from './single-instance'

const hasSingleInstance = registerSingleInstance(app, () => {
  const [mainWindow] = BrowserWindow.getAllWindows()
  if (mainWindow) focusExistingWindow(mainWindow)
})

if (hasSingleInstance) {
  void app.whenReady().then(() => {
    electronApp.setAppUserModelId('com.audiofetch.app')
    app.on('browser-window-created', (_, window) => optimizer.watchWindowShortcuts(window))
    createWindow()
  })

  app.on('window-all-closed', () => app.quit())
}
