# Audio Fetch

Electron desktop app for downloading YouTube audio on Windows and Linux.

## Scope

- Formats: MP3, M4A, OPUS, WAV, BEST.
- MP3 quality: 320, 192, 128 kbps.
- Browser cookies: Chrome, Chromium, Brave only.
- Queue: one active download; concurrent requests return `BUSY`.
- Config: new Electron JSON config; no legacy config migration.
- Supported OS: Windows and Linux. macOS packaging is out of scope.

## Install

Requirements: Bun 1.x, Node.js 20+ LTS.

```bash
bun install
```

`youtube-dl-exec` installs the yt-dlp binary during dependency setup. FFmpeg comes from `@ffmpeg-installer/ffmpeg`.

## Development

```bash
bun run dev
bun start
```

## Quality checks

```bash
bun run typecheck
bun test
bun run test:coverage
bun run test:coverage:main
bun run test:coverage:ipc
bun run test:coverage:renderer
bun run test:coverage:critical
bun run test:e2e
bun run lint
```

Automated tests use mocked yt-dlp/FFmpeg behavior. No live YouTube request or real browser cookie database is required.

## Build

```bash
bun run build
bun run build:unpack
bun run verify:resources
bun run verify:resources:unpacked
bun run build:linux
bun run build:win
```

`verify:resources:unpacked` targets the Linux `dist/linux-unpacked` layout. Windows artifact verification runs on the Windows CI runner.

Linux targets: AppImage and deb. Windows output: unsigned NSIS installer. Windows packaging requires a Windows runner.

## Architecture

```text
Renderer → contextBridge preload → typed IPC → main services
```

- Renderer: DOM, state, Web Audio, user interactions.
- Preload: narrow `audioFetch` API only.
- Main: yt-dlp, FFmpeg, cookies, config, queue, logging, window lifecycle.
- Renderer has no Node.js, filesystem, raw IPC, or direct HTTP access.

Main IPC operations:

- `video-info:fetch`
- `download:start`
- `queue:status`
- `window:minimize`
- `window:close` with required confirmation flag.

## Runtime data

- Config: Electron `userData/config.json`.
- Logs: Electron log path.
- Download output: configured output directory; filenames are sanitized for Windows/Linux.

## Troubleshooting

### yt-dlp unavailable

Run `bun install`, then verify:

```bash
bun run verify:resources
```

Packaged Linux resources are verified with:

```bash
bun run build:unpack
bun run verify:resources:unpacked
```

### FFmpeg unavailable

Confirm the platform package exists under `node_modules/@ffmpeg-installer/` and rerun the resource check.

### Cookies unavailable

Use Chrome, Chromium, or Brave. Sign in to YouTube. Firefox and Edge are intentionally unsupported. Browser cookie values never enter renderer state or logs.

### Permission/output errors

Choose a writable output directory. Check filesystem permissions and available disk space. Internal command details are not shown to users or logged.

### Packaging

Build AppImage/deb on Linux and the NSIS installer on Windows. Cross-platform artifact smoke tests require the corresponding OS runner.

## Release acceptance

Release approval requires:

- Full typecheck, tests, coverage, E2E, lint, and build gates.
- Linux AppImage/deb smoke tests.
- Windows installer smoke test on Windows.
- Manual yt-dlp/FFmpeg smoke tests on Windows and Linux.
- Startup under 3 seconds, idle memory under 200 MB, download memory under 500 MB.
- UI responsiveness and manual renderer control/screenshot review.

Current automated gaps remain explicitly tracked in `tasks/plan.md`: Windows artifact smoke, Electron single-instance/minimize/drag E2E, and manual visual/cross-OS control checks.
