import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const workflow = (name: string) =>
  readFileSync(resolve(process.cwd(), '.github/workflows', name), 'utf8')

describe('GitHub Actions workflow contract', () => {
  it('uses pinned actionlint and Bun quality gates on main and develop', () => {
    const ci = workflow('ci.yml')

    expect(ci).toContain('uses: docker://rhysd/actionlint:1.7.11')
    expect(ci).toContain('with:\n          args: -color')
    expect(ci).toContain('oven-sh/setup-bun@v2')
    expect(ci).toContain('bun install --frozen-lockfile')
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

  it('updates package.json and refreshes bun.lock during release preparation', () => {
    const release = workflow('release.yml')

    expect(release).toContain('package.json')
    expect(release).toContain('bun install --lockfile-only --ignore-scripts')
    expect(release).toContain('git add package.json bun.lock')
    expect(release).not.toContain('pyproject.toml')
    expect(release).toContain('bun install --frozen-lockfile')
  })

  it('publishes only Electron artifacts from the post-merge release flow', () => {
    const packageJson = readFileSync(resolve(process.cwd(), 'package.json'), 'utf8')
    const builder = readFileSync(resolve(process.cwd(), 'electron-builder.yml'), 'utf8')
    const postMerge = workflow('post-merge-release.yml')
    const autoApprove = workflow('auto-approve-release.yml')

    expect(packageJson).toContain('"desktopName": "audio-fetch"')
    expect(builder).toContain('- AppImage')
    expect(builder).toContain('- deb')
    expect(builder).toContain('artifactName: ${name}-${version}.${ext}')
    expect(builder).toContain('deb:')
    expect(builder).not.toContain('- snap')
    expect(builder).not.toContain('- rpm')
    expect(postMerge).toContain('prepare-release:')
    expect(postMerge).toContain(
      'ref: ${{ github.event.pull_request.merge_commit_sha || github.sha }}'
    )
    expect(postMerge).toContain('Verify release commit')
    expect(postMerge).toContain('Upload release changelog')
    expect(postMerge).toContain('build:')
    expect(postMerge).toContain('uses: ./.github/workflows/build.yml')
    expect(postMerge).toContain('tag: ${{ needs.prepare-release.outputs.new_tag }}')
    expect(postMerge).toContain('publish:')
    expect(postMerge).toContain('needs: [prepare-release, build]')
    expect(postMerge).toContain('name: production')
    expect(postMerge).toContain('actions/download-artifact@v4')
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
    expect(autoApprove).toContain('contents: read')
    expect(autoApprove).not.toContain('contents: write')
    expect(autoApprove).not.toContain('|| echo "Auto-merge not available')
    expect(autoApprove.match(/gh pr merge/g)).toHaveLength(1)
  })
})
