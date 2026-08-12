# Audio Fetch Migration Task Checklist

## Phase 0: Contract and Tooling

- [x] P0 Resolve SPEC open questions: Tier 3, progress, NES.css delivery, Linux targets, Windows signing, package-manager authority.
- [ ] P1 Add Node runtime/test dependencies, scripts, Vitest/Playwright configs, root test directories.
- [ ] P2 Replace Python-only CI/release assumptions with Node/Electron checks; retain legacy guard only if approved.
- [ ] Checkpoint 0: Tooling commands pass; unresolved blockers explicitly recorded.

## Phase 1: Electron Infrastructure

- [ ] P3 Implement branded Electron shell, frameless window, safe links, single-instance focus.
- [ ] P4 Implement new config schema, Electron paths, async persistence, safe logging.
- [ ] P5 Define/register typed preload and IPC boundary; reject invalid payloads.
- [ ] Checkpoint 1: App shell, config, preload, typecheck, focused tests, build pass.

## Phase 2: Backend Vertical Slices

- [ ] P6 Deliver video-info flow: validation, yt-dlp metadata, typed IPC, renderer response/error states.
- [ ] P7 Port approved three-tier strategy and escalation contract.
- [ ] P8 Implement Chrome/Chromium/Brave cookie extraction; reject Firefox/Edge.
- [ ] P9 Deliver audio download service: formats, quality, FFmpeg, metadata, thumbnail, filename safety.
- [ ] P10 Deliver single-active-download guard, download IPC, queue status, close-confirmation data.
- [ ] Checkpoint 2: Backend flow, tier tests, cookie tests, download mocks, queue exclusivity pass.

## Phase 3: Renderer Parity

- [ ] P11 Port legacy HTML/CSS/favicon and approved NES.css delivery.
- [ ] P12 Wire renderer video-info/download state machine through typed preload IPC.
- [ ] P13 Port Web Audio effects and window controls/drag/close confirmation.
- [ ] Checkpoint 3: UI parity, renderer IPC-only access, controls, focused E2E pass.

## Phase 4: Verification, Packaging, Release

- [ ] P14 Complete unit/integration/Electron E2E regression coverage; meet SPEC thresholds.
- [ ] P15 Finalize Windows/Linux packaging, branding, binary resources, AppImage/deb targets.
- [ ] P16 Update release workflows for Electron artifacts, versioning, signing, uploads.
- [ ] P17 Complete README, IPC/architecture/troubleshooting docs, release acceptance measurements.
- [ ] Checkpoint 4: Full tests, lint, builds, cross-platform smoke tests, performance checks, human release approval.

## Global Verification

- [ ] `bun run typecheck`
- [ ] `bun test`
- [ ] `bun run test:coverage`
- [ ] `bun run test:e2e`
- [ ] `bun run lint`
- [ ] `bun run build`
- [ ] `bun run build:unpack`
- [ ] Windows installer smoke test
- [ ] Linux AppImage/deb smoke test
