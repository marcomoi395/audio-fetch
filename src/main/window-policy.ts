export const DEFAULT_WINDOW_CONFIG = {
  width: 850,
  height: 650,
  title: 'Audio Fetch'
} as const

export type WindowConfig = Partial<typeof DEFAULT_WINDOW_CONFIG>

type FocusableWindow = {
  isMinimized(): boolean
  restore(): void
  focus(): void
}

export function resolveWindowConfig(config: WindowConfig = {}): typeof DEFAULT_WINDOW_CONFIG {
  return { ...DEFAULT_WINDOW_CONFIG, ...config }
}

export function focusExistingWindow(window: FocusableWindow): void {
  if (window.isMinimized()) window.restore()
  window.focus()
}

export function isSafeExternalUrl(url: string): boolean {
  try {
    const protocol = new URL(url).protocol
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}
