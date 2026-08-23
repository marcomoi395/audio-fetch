import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const workflow = (name: string) =>
  readFileSync(resolve(process.cwd(), '.github/workflows', name), 'utf8')

describe('GitHub Actions workflow contract', () => {
  it('uses pinned actionlint and Bun quality gates on main and develop', () => {
    const ci = workflow('ci.yml')

    expect(ci).toContain(
      'uses: docker://rhysd/actionlint@sha256:6f03470d0152251d7f07f7c4dc019dbe7024c72cd952f839544c7798843efa8f'
    )
    expect(ci).toContain('with:\n          args: -color')
    expect(ci).toContain('oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6')
    expect(ci).toContain('actions/checkout@11d5960a326750d5838078e36cf38b85af677262')
    expect(ci).toContain('bun run typecheck')
    expect(ci).toContain('bun test')
    expect(ci).toContain('bun run lint')
    expect(ci).toContain('bun run test:coverage')
    expect(ci).toContain('bun run build:unpack')
    expect(ci).toContain('xvfb-run bun run test:e2e')
    expect(ci).toMatch(/branches:\n\s+- main\n\s+- develop/)
  })

  it('builds Electron AppImage, deb, and Windows artifacts without Python or RPM', () => {
    const build = workflow('build.yml')

    expect(build).toContain('workflow_call:')
    expect(build).toContain('run: bun run build:linux')
    expect(build).toContain('run: bun run build:win')
    expect(build).toContain('path: dist/*.AppImage')
    expect(build).toContain('path: dist/*.deb')
    expect(build).toContain('path: dist/*.exe')
    expect(build).toContain('^v[0-9]+\\.[0-9]+\\.[0-9]+$')
    expect(build).not.toContain('upload_to_release')
    expect(build).not.toMatch(/Python|PyInstaller|Qt|rpm/i)
  })

  it('updates package.json, refreshes bun.lock, and serializes release preparation', () => {
    const release = workflow('release.yml')

    expect(release).toContain('package.json')
    expect(release).toContain('bun install --lockfile-only --ignore-scripts')
    expect(release).toContain('git add package.json bun.lock')
    expect(release).not.toContain('pyproject.toml')
    expect(release).toContain('bun install --frozen-lockfile')
    expect(release).toContain('group: release-preparation')
    expect(release).toContain('cancel-in-progress: false')
    expect(release).toContain('name: Get current package version')
    expect(release).toContain(
      'CURRENT_VERSION: ${{ steps.get_current_version.outputs.current_version }}'
    )
    expect(release).not.toContain('get_latest_tag')
  })

  it('publishes only Electron artifacts from the post-merge release flow', () => {
    const packageJson = readFileSync(resolve(process.cwd(), 'package.json'), 'utf8')
    const builder = readFileSync(resolve(process.cwd(), 'electron-builder.yml'), 'utf8')
    const postMerge = workflow('post-merge-release.yml')
    const autoApprovePath = resolve(process.cwd(), '.github/workflows/auto-approve-release.yml')

    expect(packageJson).toContain('"desktopName": "audio-fetch"')
    expect(builder).toContain('- AppImage')
    expect(builder).toContain('- deb')
    expect(builder).toContain('artifactName: ${name}-${version}.${ext}')
    expect(builder).toContain('deb:')
    expect(builder).not.toContain('- snap')
    expect(builder).not.toContain('- rpm')
    expect(postMerge).toContain('publish:')
    expect(postMerge).toContain('group: release-publish')
    expect(postMerge).toContain(
      'ref: ${{ github.event.pull_request.merge_commit_sha || github.sha }}'
    )
    expect(postMerge).toContain('Verify release commit')
    expect(postMerge).toContain('Upload release changelog')
    expect(postMerge).toContain('build:')
    expect(postMerge).toContain('uses: ./.github/workflows/build.yml')
    expect(postMerge).toContain('tag: ${{ needs.prepare-release.outputs.new_tag }}')
    expect(postMerge).toContain('smoke-simulated:')
    expect(postMerge).toContain('name: Simulated artifact and Electron smoke')
    expect(postMerge).toContain(
      "find artifacts/linux-appimage -type f -name '*.AppImage' -size +0c"
    )
    expect(postMerge).toContain("find artifacts/linux-deb -type f -name '*.deb' -size +0c")
    expect(postMerge).toContain("find artifacts/windows-installer -type f -name '*.exe' -size +0c")
    expect(postMerge).toContain('name: Run unpacked Electron E2E with offline fixture')
    expect(postMerge).toContain(
      'run: bun install --frozen-lockfile\n      - name: Download release artifacts'
    )
    expect(postMerge).not.toContain(
      'run: bun install --frozen-lockfile --ignore-scripts\n      - name: Download release artifacts'
    )
    expect(postMerge).toContain('needs: [prepare-release, build, smoke-simulated]')
    expect(postMerge).toContain('name: production')
    expect(postMerge).toContain(
      'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093'
    )
    expect(postMerge).not.toContain('gh workflow run')
    expect(postMerge).not.toContain('gh run list')
    expect(postMerge).not.toContain('request_id')
    expect(postMerge).toContain('DISPATCH_VERSION: ${{ inputs.version }}')
    expect(postMerge).toContain('HEAD_REF: ${{ github.event.pull_request.head.ref }}')
    expect(postMerge).toContain('^v[0-9]+\\.[0-9]+\\.[0-9]+$')
    expect(postMerge).not.toContain('NEW_TAG="${{ inputs.version }}"')
    expect(postMerge).not.toContain('NEW_TAG="${{ github.event.pull_request.head.ref }}"')
    expect(postMerge).toContain('artifacts/linux-appimage/*.AppImage')
    expect(postMerge).toContain('artifacts/linux-deb/*.deb')
    expect(postMerge).toContain('artifacts/windows-installer/*.exe')
    expect(postMerge).not.toMatch(/pyproject|\.rpm|Firefox|Edge|ffmpeg is required/i)
    expect(existsSync(autoApprovePath)).toBe(false)
  })
})
