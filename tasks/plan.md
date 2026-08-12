# Implementation Plan: Audio Fetch Electron-Vite Migration

## Scope

Full implementation of `SPEC.md` v2.0. Planning only. No application code changes in this phase.

Current baseline: Electron-Vite scaffold in `src/`; legacy Python application in `legacy/` is the behavioral reference. Existing CI still targets Python. `package.json` lacks runtime download/test dependencies. `tasks/` did not exist before this plan.

## Planning Decisions

- Canonical package commands: Bun, matching `SPEC.md`; `bun.lock` is authoritative and no npm lockfile is generated.
- Queue behavior: one active download; second request returns busy error.
- Cookie scope: Chrome, Chromium, Brave only; Firefox and Edge remain unsupported.
- Config: new versioned schema; no legacy config migration.
- Tests use mocked yt-dlp/FFmpeg and deterministic fixtures; CI never requires live YouTube or real browser cookies.
- No implementation begins until this plan is explicitly approved.

## Dependency Graph

```text
P0 decisions and approval
    ↓
P1 Bun/tooling/test harness ─────→ P2 Node/Electron CI baseline
    ↓                                  ↓
P3 app shell + single instance       checkpoint
    ↓
P4 config + paths + logging
    ↓
P5 typed preload/IPC contract
    ├──────────────┐
    ↓              ↓
P6 video-info   P7 tier strategy
    ↓              ↓
P8 cookie extraction
    └──────┬───────┘
           ↓
P9 download service + FFmpeg
           ↓
P10 queue + download IPC + close status
           ↓
P11 HTML/CSS parity
           ↓
P12 renderer video-info/download flow
           ↓
P13 Web Audio effects
           ↓
P14 E2E and cross-process verification
           ↓
P15 packaging and assets
           ↓
P16 release CI and smoke builds
           ↓
P17 documentation and final acceptance
```

P6 and P7 can proceed in parallel after P5. P8 depends on the approved Tier 2 contract from P7. P11 can begin after the preload contract exists, but P12 waits for P6/P9/P10. P15 can begin after branding/window decisions are stable; P16 waits for P14 and P15.

## Phase 0: Contract and Tooling

### Task P0: Resolve Spec Open Questions

**Description:** Record the five approved implementation choices from `SPEC.md`: Tier 3 runtime clients, deferred progress, bundled NES.css, AppImage/deb-only Linux packaging, unsigned Windows builds. Confirm Bun lockfile authority before dependency edits.

**Acceptance criteria:**

- [x] Written decisions exist for all five `SPEC.md` open questions.
- [x] Tier 3 behavior is concrete enough to test: `android` and `mweb` clients, no cookies, one attempt per client, approved escalation signals.
- [x] Progress scope is explicit: deferred until after functional parity.
- [x] NES.css delivery strategy is explicit: bundled asset.
- [x] Linux targets and Windows signing expectation are explicit: AppImage/deb only, unsigned Windows builds.
- [x] Package-manager authority is explicit: Bun with `bun.lock`; no npm lockfile.

**Verification:**

- [x] Human review confirms the decisions.
- [x] `SPEC.md` open questions are resolved in the approved decisions section.

**Dependencies:** None.

**Files likely touched:** `SPEC.md` only if decisions are recorded there.

**Estimated scope:** Small (human decision gate; no code).

### Task P1: Establish Node Test and Build Tooling

**Description:** Add the missing runtime/test dependencies, scripts, Vitest configuration, Playwright configuration, and root test directories without implementing domain behavior.

**Acceptance criteria:**

- [x] `package.json` contains `youtube-dl-exec`, `@ffmpeg-installer/ffmpeg`, Vitest, coverage, and Playwright dependencies.
- [x] Scripts exist for `test`, `test:coverage`, `test:watch`, `test:e2e`, `build`, `build:unpack`, `build:win`, and `build:linux`; no required macOS script remains.
- [x] `vitest.config.ts` and `playwright.config.ts` load successfully.
- [x] `tests/unit/`, `tests/integration/`, and `tests/e2e/` exist with minimal executable smoke tests.
- [x] Existing TypeScript and lint configuration remain valid; formatting follows the repository's no-semicolon Prettier config unless separately approved.

**Verification:**

- [x] `bun install --frozen-lockfile`
- [x] `bun test`
- [x] `bun run typecheck`
- [x] `bun run build`

**Dependencies:** P0.

**Files touched:** `package.json`, `bun.lock`, `vitest.config.ts`, `playwright.config.ts`, and `tests/`.

**Estimated scope:** Medium (2-6 hours).

### Task P2: Replace Python-Only CI with Node/Electron Checks

**Description:** Update CI to install Node dependencies, run typecheck/lint/unit/integration tests, and preserve legacy Python checks only as a temporary migration guard where useful.

**Acceptance criteria:**

- [x] Pull-request CI runs `bun install --frozen-lockfile`.
- [x] CI runs `bun run typecheck`, `bun test`, `bun run test:coverage`, and `bun run lint`.
- [x] E2E jobs run headless Electron through `xvfb-run bun run test:e2e`; local direct Playwright run discovered 1 Electron test and passed without `DISPLAY`.
- [x] Release/build workflows use Bun and Electron tooling only; AppImage/deb/Windows artifacts replace Python/RPM assumptions.
- [x] Legacy Python checks are removed from canonical CI; rationale is documented in `ci.yml`.

**Verification:**

- [x] Validate workflow YAML syntax.
- [x] Run local gates: `bun run typecheck`, `bun test`, `bun run test:coverage`, `bun run lint`, `bun run build`.
- [x] Inspect workflow diff for secrets, permissions, unsupported OS assumptions, artifact paths, and live-network test dependencies. Local `xvfb-run` is unavailable; CI remains the Xvfb verification path.

**Dependencies:** P1.

**Files touched:** `.github/workflows/ci.yml`, `.github/workflows/build.yml`, `.github/workflows/release.yml`, `.github/workflows/post-merge-release.yml`, `electron-builder.yml`, `package.json`, `bun.lock`, and workflow/E2E tests.

**Estimated scope:** Medium (2-6 hours).

### Checkpoint 0: Tooling Gate

- [x] P0 decisions approved.
- [x] P1 commands pass locally.
- [x] P2 workflow changes reviewed by workflow contract tests.
- [x] No domain implementation started before package-manager/Tier 3 decisions were resolved.

## Phase 1: Electron Infrastructure

### Task P3: Implement Branded App Shell and Single Instance

**Description:** Replace the scaffold lifecycle with branded Electron startup, a frameless BrowserWindow shell, safe external-link handling, and `app.requestSingleInstanceLock()` focus behavior.

**Acceptance criteria:**

- [x] Window uses injected config-driven dimensions/title with Audio Fetch defaults.
- [x] Context isolation remains enabled; renderer Node integration is disabled.
- [x] App ID/product branding uses `com.audiofetch.app` and `Audio Fetch`.
- [x] A second launch focuses/restores the first instance through `second-instance` handling.
- [x] No macOS-only lifecycle behavior was added; existing builder macOS config remains untouched.

**Verification:**

- [x] Focused unit/integration tests cover single-instance lock and second-instance focus behavior with mocked Electron APIs.
- [x] `bun run typecheck`
- [x] `bun run build`
- [x] Automated built-app Electron E2E from P2 substitutes for manual unpacked launch; P3 shell policy tests pass.

**Dependencies:** P1, P0.

**Files touched:** `src/main/index.ts`, `src/main/window.ts`, `src/main/window-policy.ts`, `src/main/single-instance.ts`, `electron-builder.yml`, and `tests/integration/app-shell.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P4: Implement Config, Paths, and Logging Services

**Description:** Add the new versioned config schema, Electron path resolution, async persistence, safe fallback behavior, and structured logging without legacy-schema migration.
**Acceptance criteria:**

- [x] Config path uses `app.getPath('userData')` through `getElectronConfigPath`; no hardcoded home-directory logic appears in production code.
- [x] Missing config loads exact SPEC defaults.
- [x] Invalid JSON/schema logs a safe generic reason and falls back to defaults.
- [x] Save creates parent directories asynchronously.
- [x] Logger redacts case-insensitive cookie/token/password/secret/authorization fields, including nested metadata.
- [x] Config tests prove legacy keys/files are not migrated.

**Verification:**

- [x] `bun test -- tests/unit/config.test.ts tests/unit/paths.test.ts tests/unit/logger.test.ts`
- [x] `bun run typecheck:node`
- [x] Temporary-directory tests cover load, invalid file/schema, save, custom reload, and legacy-file ignore.

**Dependencies:** P1, P3.

**Files touched:** `src/main/services/config.ts`, `src/main/utils/paths.ts`, `src/main/utils/logger.ts`, `src/main/index.ts`, `src/main/window-policy.ts`, `tests/unit/config.test.ts`, `tests/unit/paths.test.ts`, and `tests/unit/logger.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P5: Define and Register the Typed IPC Boundary

**Description:** Replace the scaffold preload bridge with a narrow typed API and register explicit IPC channels for video info, download, queue status, and window controls.

**Acceptance criteria:**

- [x] Preload exposes only typed `audioFetch` namespace methods from `SPEC.md`.
- [x] Raw `ipcRenderer`, Node.js modules, arbitrary channel names, and remote eval remain unavailable to the renderer.
- [x] Main registration uses one shared channel map for `videoInfo`, `download`, `queueStatus`, `windowMinimize`, and `windowClose`, with sender-owned window handler boundary.
- [x] Invalid payloads are rejected before service calls.
- [x] IPC error responses are serializable and user-safe.
- [x] P5 service seam returns safe unavailable errors; P6 replaces stubs with video-info/download services.

**Verification:**

- [x] `bun test -- tests/integration/ipc-handlers.test.ts tests/integration/preload.test.ts tests/integration/preload-install.test.ts`
- [x] `bun run test`
- [x] `bun test`
- [x] `bun run typecheck`
- [x] `bun run test:e2e` verifies built Electron URL, body, `audioFetch` bridge, and absence of `electron`/`api` globals.

**Dependencies:** P3, P4.

**Files touched:** `src/shared/ipc.ts`, `src/preload/index.ts`, `src/preload/index.d.ts`, `src/preload/api.ts`, `src/preload/install.ts`, `src/main/ipc/index.ts`, `src/main/ipc/services.ts`, `src/main/index.ts`, `src/renderer/src/renderer.ts`, `tests/integration/ipc-handlers.test.ts`, `tests/integration/preload.test.ts`, `tests/integration/preload-install.test.ts`, and `tests/e2e/app.e2e.ts`.

**Estimated scope:** Medium (2-6 hours).

### Checkpoint 1: Infrastructure Gate

- [x] App launches through the new main process.
- [x] Config writes to the Electron user-data directory.
- [x] Preload exposes only the approved API.
- [x] Typecheck, focused tests, and build pass.

## Phase 2: Backend Vertical Slices

### Task P6: Deliver the Video-Info Flow

**Description:** Implement YouTube metadata extraction plus the complete main → preload → renderer video-info path, using mocked yt-dlp in tests.

**Acceptance criteria:**

- [x] URL validation rejects malformed/untrusted input before yt-dlp execution.
- [x] Returned data includes title, uploader, duration, thumbnail URL, formats, and qualities.
- [x] Format values are `mp3`, `m4a`, `opus`, `wav`, `best`.
- [x] Quality values are `0`, `5`, and `9` with legacy meanings.
- [x] yt-dlp failures become logged, serializable, user-facing errors.

**Verification:**

- [x] `bun test -- tests/unit/downloader.test.ts tests/integration/video-info-flow.test.ts`
- [x] `bun run typecheck`
- [x] Automated renderer controller/UI tests cover loading, metadata, invalid input, and error states; built Electron E2E remains offline.

**Dependencies:** P5, P1.

**Files touched:** `src/main/services/downloader.ts`, `src/main/ipc/services.ts`, `src/main/index.ts`, `src/renderer/src/app.ts`, `src/renderer/src/renderer.ts`, `src/renderer/index.html`, `tests/unit/downloader.test.ts`, `tests/unit/renderer-app.test.ts`, and `tests/integration/video-info-flow.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P7: Port and Lock the Three-Tier Strategy

**Description:** Port the legacy tier order, attempt counts, escalation signals, and approved Tier 3 implementation into a deterministic TypeScript service.

**Acceptance criteria:**

- [x] Tier 1 has the three approved attempts in order.
- [x] Tier 2 has the approved Chrome-family cookie attempts in order.
- [x] Tier 3 matches the P0 decision exactly: `android`, then `mweb`, no cookies, disabled by default.
- [x] Status codes `401`, `403`, `429` and legacy bot/auth keywords trigger the approved escalation behavior.
- [x] Attempt counts, tier order, disabled Tier 3 behavior, and terminal failure state are unit-tested.

**Verification:**

- [x] `bun test -- tests/unit/tier-strategy.test.ts`
- [x] `bun run typecheck:node`
- [x] Fixture tests cover success path shape, all approved escalation attempts, disabled Tier 3, and complete exhaustion.

**Dependencies:** P0, P1.

**Files touched:** `src/main/services/tier-strategy.ts` and `tests/unit/tier-strategy.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P8: Implement Chrome-Family Cookie Extraction

**Description:** Implement browser selection/profile discovery for Chrome, Chromium, and Brave on Windows/Linux, with explicit rejection of Firefox and Edge.

**Acceptance criteria:**

- [x] Supported browser names normalize consistently.
- [x] Chrome, Chromium, Brave profile discovery covers default and additional profiles required by the approved library.
- [x] Firefox and Edge return a clear unsupported error.
- [x] Cookie values are never returned to renderer or logs.
- [x] Tests use fake filesystem/profile fixtures; no real browser database is required.

**Verification:**

- [x] `bun test -- tests/unit/cookie-extractor.test.ts`
- [x] `bun run typecheck:node`
- [x] Linux and Windows path fixtures pass in the same test suite.

**Dependencies:** P1, P7.

**Files touched:** `src/main/services/cookie-extractor.ts`, `tests/unit/cookie-extractor.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P9: Deliver the Audio Download Service

**Description:** Implement yt-dlp/FFmpeg audio conversion, filename sanitization, thumbnail embedding, metadata embedding, and tier execution using mocked external processes.

**Acceptance criteria:**

- [x] `mp3`, `m4a`, `opus`, `wav`, and `best` map to the legacy output behavior.
- [x] Quality `0`, `5`, and `9` map to 320, 192, and 128 kbps for MP3.
- [x] Thumbnail conversion/embed and metadata postprocessors are configured in the required order.
- [x] Output filenames are safe on Windows/Linux.
- [x] External binary failures are logged and normalized without leaking command secrets.

**Verification:**

- [x] `bun test -- tests/unit/downloader.test.ts`
- [x] Assert yt-dlp/FFmpeg invocation options with mocks.
- [x] `bun run typecheck:node`

**Dependencies:** P6, P7, P8, P1.

**Files touched:** `src/main/services/downloader.ts`, `tests/unit/downloader.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P10: Deliver Single-Active Download and Queue Status

**Description:** Add the one-active-download guard, download IPC handler, queue status IPC, and close-confirmation data path.

**Acceptance criteria:**

- [x] First download starts normally.
- [x] Second request while active returns a busy error and does not invoke yt-dlp.
- [x] Queue status exposes only safe state needed by renderer.
- [x] Completion and failure release the guard.
- [x] Close flow can determine whether an active download exists.

**Verification:**

- [x] `bun test -- tests/unit/queue.test.ts tests/integration/download-flow.test.ts tests/integration/ipc-handlers.test.ts`
- [x] Test success, failure, and second-request race cases.
- [x] `bun run typecheck`

**Dependencies:** P5, P9.

**Files touched:** `src/main/services/queue.ts`, `src/main/ipc/services.ts`, `src/main/ipc/index.ts`, `src/shared/ipc.ts`, `tests/unit/queue.test.ts`, `tests/integration/download-flow.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Checkpoint 2: Backend Gate

- [x] Video-info flow works with mocked yt-dlp.
- [x] Tier strategy matches approved legacy contract.
- [x] Cookie scope is enforced.
- [x] Download conversion/metadata options are asserted.
- [x] Queue rejects concurrent execution.
- [x] Main-process coverage targets are measurable through scoped reports.

## Phase 3: Renderer Parity

### Task P11: Port Legacy HTML, CSS, and Static Assets

**Description:** Replace the electron-vite demo page with the legacy Audio Fetch layout, CSP, favicon, and approved NES.css delivery strategy.

**Acceptance criteria:**

- [x] Four legacy UI states exist: input, loading, error, and info.
- [x] Custom title bar DOM includes drag area, minimize, and close controls.
- [x] Legacy dimensions, text, responsive breakpoints, and custom CSS are preserved.
- [x] CSP permits only approved local/CDN resources.
- [x] No nonexistent MP3/WAV asset requirement is introduced; sound behavior remains Web Audio based.

**Verification:**

- [x] `bun run typecheck:web`
- [x] `bun run build`
- [x] `bun run test:e2e`
- [ ] Manual screenshot comparison against `legacy/templates/index.html` and `legacy/static/css/custom.css`.

**Dependencies:** P0 (NES.css decision), P3, P5.

**Files likely touched:** `src/renderer/index.html`, `src/renderer/assets/css/custom.css`, `src/renderer/assets/images/favicon.png`, `resources/icon.png` only if branding requires it.

**Estimated scope:** Medium (2-6 hours).

### Task P12: Wire Renderer Video-Info and Download State Flow

**Description:** Port the legacy state machine and event handlers to typed preload calls for fetch, retry, new URL, download, and user-facing error handling.

**Acceptance criteria:**

- [x] Fetch button validates URL, shows loading, invokes `videoInfo.fetch`, and renders returned info.
- [x] Retry and new-URL actions restore the correct legacy state.
- [x] Download button invokes `download.start` with selected format/quality.
- [x] Busy, validation, tier exhaustion, and external errors render safe messages.
- [x] Renderer never calls HTTP endpoints, raw IPC, Node.js, or filesystem APIs.

**Verification:**

- [x] `bun test -- tests/unit/renderer-app.test.ts`
- [x] `bun run typecheck:web`
- [x] E2E fixture verifies input → loading → info → download-success transitions.

**Dependencies:** P6, P10, P11.

**Files likely touched:** `src/renderer/src/app.ts`, `src/renderer/src/renderer.ts`, `src/renderer/src/types.ts`, `tests/unit/renderer-app.test.ts`, `tests/e2e/app.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P13: Port Web Audio 8-Bit Effects and Window Controls

**Description:** Port generated 8-bit sound behavior and connect click/fetch/download/success/error sounds plus minimize, close, and drag controls.

**Acceptance criteria:**

- [x] Five required UI sound events invoke the audio module.
- [x] Audio failures do not break UI actions.
- [x] Minimize invokes the preload window API.
- [x] Close prompts when queue status is active and closes after confirmation.
- [x] Title-bar drag uses the native frameless drag region on supported Windows/Linux display environments.

**Verification:**

- [x] `bun test -- tests/unit/audio.test.ts tests/integration/ipc-handlers.test.ts tests/integration/preload.test.ts`
- [x] `bun run typecheck:web`
- [x] Renderer build/E2E smoke passes; manual cross-OS control check remains at Checkpoint 3.

**Dependencies:** P10, P11, P12.

**Files touched:** `src/renderer/src/audio.ts`, `src/renderer/src/app.ts`, `src/renderer/src/renderer.ts`, `src/renderer/assets/css/custom.css`, `src/shared/ipc.ts`, `src/preload/api.ts`, `src/main/ipc/index.ts`, `tests/unit/audio.test.ts`, `tests/integration/ipc-handlers.test.ts`, `tests/integration/preload.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Checkpoint 3: User Flow Gate

- [ ] UI visually matches the legacy page at the approved viewport sizes.
- [ ] Video-info and download actions use only preload IPC.
- [ ] Window controls and close confirmation work.
- [ ] All renderer tests and focused E2E tests pass.

## Phase 4: Verification, Packaging, and Release

### Task P14: Complete Cross-Process E2E and Regression Coverage

**Description:** Add deterministic Electron E2E coverage for startup, single instance, UI states, mocked video-info/download, queue busy behavior, and close confirmation.

**Acceptance criteria:**

- [x] E2E launches the built Electron app.
- [x] Tests cover video-info success/error, download success/busy/failure, and inactive title-bar close.
- [x] Tests do not contact YouTube or read real browser cookies.
- [x] Coverage reports include scoped main services 98.93%, IPC 88.63%, renderer 92.5%, and critical paths 100% statements/lines.
- [x] Legacy Python tests remain available as temporary reference/guard.
- [ ] Electron E2E single-instance focus, minimize, and drag coverage.

**Verification:**

- [x] `bun test`
- [x] `bun run test:coverage`
- [x] Scoped coverage scripts pass: main, IPC, renderer, critical.
- [x] `bun run test:e2e` — 6 passed.
- [x] Coverage report reviewed against scoped SPEC thresholds.

**Dependencies:** P2, P10, P13.

**Files likely touched:** `tests/unit/`, `tests/integration/`, `tests/e2e/app.test.ts`, `playwright.config.ts`, `vitest.config.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P15: Finalize Electron Packaging and Bundled Resources

**Acceptance criteria:**

- [x] `electron-builder.yml` contains only approved Windows/Linux targets.
- [x] App ID, product name, executable name, and Linux artifact names are Audio Fetch branded.
- [x] yt-dlp and FFmpeg binaries are present in verified Linux unpacked runtime paths.
- [x] AppImage and deb targets are configured.
- [x] No secrets, personal paths, or fake publish endpoints are required for local builds.
- [ ] Windows icon/installer build and runtime smoke on a Windows runner.

**Verification:**

- [x] `bun run build:unpack`
- [x] `bun run verify:resources:unpacked`
- [x] `bun run build:linux` — AppImage and deb produced.
- [ ] `bun run build:win` on Windows or approved Windows CI runner.
- [x] Linux unpacked startup/resource smoke passed through existing Electron E2E and verifier.

**Dependencies:** P3, P9, P11, P0.

**Files touched:** `electron-builder.yml`, `package.json`, `scripts/verify-resources.mjs`, `src/main/ipc/services.ts`, `src/main/utils/binaries.ts`, `tests/unit/binaries.test.ts`.

**Estimated scope:** Medium (2-6 hours).

### Task P16: Make Release Workflows Build and Publish Electron Artifacts

**Description:** Update release automation for versioning, Node dependency installation, Windows installer, Linux AppImage/deb artifacts, and optional signing/publishing decisions.
**Acceptance criteria:**

- [x] Release workflow versions `package.json` and refreshes `bun.lock`.
- [x] Build workflow produces approved Linux AppImage/deb and Windows installer artifact paths.
- [x] Signing is not required for local builds; no signing secret is hardcoded.
- [x] Artifact upload paths match electron-builder output.
- [x] CI fails on test, coverage, build, or resource verification errors.

**Verification:**

- [x] Workflow contract tests pass.
- [x] Local equivalents `bun run build` and `bun run build:unpack` pass.
- [ ] Workflow-dispatch build on Windows and Linux release runners.

**Dependencies:** P2, P14, P15, P0.

**Files touched:** `.github/workflows/ci.yml`, `.github/workflows/build.yml`, `.github/workflows/release.yml`.

**Estimated scope:** Medium (2-6 hours).

### Task P17: Complete Documentation and Release Acceptance

**Description:** Replace scaffold README content with installation, supported scope, IPC/process architecture, troubleshooting, test, build, and release instructions.
**Acceptance criteria:**

- [x] README documents Windows/Linux support and Chrome/Chromium/Brave-only cookie scope.
- [x] README documents no concurrent downloads and no legacy config migration.
- [x] IPC API and main/preload/renderer boundaries are documented.
- [x] Troubleshooting covers yt-dlp, FFmpeg, cookie permissions, output paths, and packaging.
- [ ] Release performance measurements recorded on named Windows/Linux test machines.

**Verification:**

- [x] README commands reviewed against `package.json`.
- [x] `bun run typecheck`
- [x] `bun test`
- [x] `bun run lint`

**Dependencies:** P14, P15, P16.

**Files touched:** `README.md`.

**Estimated scope:** Small (1-2 hours).

### Checkpoint 4: Release Gate

- [ ] All functional criteria in `SPEC.md` are checked.
- [ ] All automated checks pass.
- [ ] Windows installer and Linux AppImage/deb are smoke-tested.
- [ ] Manual real yt-dlp/FFmpeg smoke tests pass on Windows and Linux.
- [ ] Performance targets are measured and recorded.
- [ ] Human approves release scope, signing, and artifact publication.

## Parallelization

Safe parallel work after each contract is approved:

- P6 and P7 can run in parallel after P5; P8 follows P7's approved cookie contract.
- P11 can run in parallel with P6/P7 after P5, provided the NES.css decision is resolved.
- Unit tests for P4/P7/P8 can be written alongside their implementation, but integration/E2E tasks wait for stable IPC contracts.

Must remain sequential:

- P0 → P1 → P5 → user-facing vertical slices.
- P7 decision → P8/P9.
- P9 → P10 → P12/P13.
- P14/P15 → P16.

## Risks and Mitigations

| Risk                                            | Impact | Mitigation                                                                                        |
| ----------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------- |
| yt-dlp changes upstream                         | High   | Mock options, keep binary checks, run manual smoke downloads before release.                      |
| Tier 3 ambiguity                                | High   | Block P7/P9 until exact clients/cookies/attempts are approved.                                    |
| Chrome cookie encryption/profile differences    | High   | Test fake profiles per OS; document supported browser versions and permission failures.           |
| Frameless drag behavior on Wayland              | Medium | Keep drag region minimal; test X11 and Wayland where available; retain native fallback if needed. |
| NES.css unavailable offline                     | Medium | Bundle NES.css for offline operation.                                                             |
| Python CI still owns release flow               | High   | Land P2 before feature work reaches release packaging.                                            |
| Bun lockfile conflict                           | Medium | Keep `bun.lock` authoritative; avoid npm lockfile generation.                                     |
| Cross-platform binary packaging                 | High   | Validate unpacked runtime paths in P15 before artifact builds.                                    |
| Scope creep into unsupported platforms/features | Medium | Enforce SPEC boundaries: no macOS, Firefox/Edge, concurrency, or config migration.                |

## Definition of Done

- Every task's focused verification passes.
- Full `bun run typecheck`, `bun test`, `bun run test:coverage`, `bun run test:e2e`, and `bun run lint` pass.
- `bun run build` passes; Windows/Linux artifacts are smoke-tested.
- No raw IPC/Node access reaches the renderer.
- No live-network dependency exists in automated tests.
- Human approves checkpoints and final release gate.
