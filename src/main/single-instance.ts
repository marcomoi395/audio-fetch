type SingleInstanceApp = {
  requestSingleInstanceLock(): boolean
  quit(): void
  on(
    event: 'second-instance',
    listener: (event: unknown, commandLine: string[], workingDirectory: string) => void
  ): void
}

export function registerSingleInstance(
  app: SingleInstanceApp,
  focusWindow: (commandLine: string[], workingDirectory: string) => void
): boolean {
  if (!app.requestSingleInstanceLock()) {
    app.quit()
    return false
  }

  app.on('second-instance', (_event, commandLine, workingDirectory) => {
    focusWindow(commandLine, workingDirectory)
  })
  return true
}
