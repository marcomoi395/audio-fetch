# Release Management Guide

This guide is for release managers who trigger and publish releases for Audio Fetch.

## Overview

The release process is fully automated through GitHub Actions workflows:
1. **Release Workflow** - Bumps version, creates tag, generates changelog, creates release draft
2. **Build Workflow** - Builds multi-platform binaries and uploads to release
3. **Manual Publish** - Manager reviews and publishes the release

## Triggering a Release

### Prerequisites
- You must have write access to the repository
- All changes should be merged to `main` branch
- CI tests should be passing on `main`

### Steps

1. **Go to GitHub Actions**
   - Navigate to: `https://github.com/<owner>/audio-fetch/actions`
   - Click on "Release" workflow in the left sidebar

2. **Run Workflow**
   - Click "Run workflow" button (top right)
   - Select branch: `main`
   - Choose version bump type:
     - **patch** (0.1.0 → 0.1.1): Bug fixes, minor improvements
     - **minor** (0.1.0 → 0.2.0): New features, backward compatible
     - **major** (0.1.0 → 1.0.0): Breaking changes, API changes
   - Click "Run workflow" green button

3. **Wait for Completion**
   - Release workflow runs (~2 minutes):
     - Bumps version in `pyproject.toml`
     - Commits and pushes version bump
     - Creates and pushes new tag (e.g., `v0.1.1`)
     - Generates changelog from commits
     - Creates release draft on GitHub
     - Triggers build workflow
   
   - Build workflow runs (~15-20 minutes):
     - Builds Linux packages (AppImage, .deb, .rpm)
     - Builds Windows installer
     - Uploads all artifacts to release draft

4. **Monitor Progress**
   - Check "Release" workflow run for completion
   - Check "Build" workflow run for build status
   - Build artifacts will appear in the release draft automatically

## Reviewing the Release Draft

1. **Find the Release Draft**
   - Go to: `https://github.com/<owner>/audio-fetch/releases`
   - The new release will be marked as "Draft"

2. **Review Content**
   - **Title**: Should be "Release vX.Y.Z"
   - **Changelog**: Auto-generated from commits since last release
   - **Artifacts**: Should include 4 files:
     - `audio-fetch-vX.Y.Z-x86_64.AppImage` (Linux - Universal)
     - `audio-fetch_X.Y.Z_amd64.deb` (Linux - Debian/Ubuntu)
     - `audio-fetch-X.Y.Z-1.x86_64.rpm` (Linux - Fedora/RHEL)
     - `audio-fetch-vX.Y.Z-setup.exe` (Windows installer)

3. **Edit if Needed**
   - Click "Edit" on the release draft
   - Update changelog for clarity (organize by categories if needed)
   - Add highlights or breaking changes section
   - Add screenshots or additional notes

4. **Verify Artifacts**
   - Check that all 4 artifacts are present
   - Check file sizes are reasonable:
     - AppImage: ~150-250 MB
     - .deb: ~150-250 MB
     - .rpm: ~150-250 MB
     - Windows setup: ~150-250 MB
   - Download and test if you have access to target platforms

## Publishing the Release

1. **Final Check**
   - All artifacts uploaded ✓
   - Changelog is accurate ✓
   - Version number is correct ✓
   - No critical issues in artifacts ✓

2. **Publish**
   - Click "Publish release" button
   - Release becomes public immediately
   - Users can download from GitHub Releases page
   - Release is tagged in git history

3. **Announcement** (Optional)
   - Share release notes in project channels
   - Update project website if applicable
   - Notify users of new version

## Troubleshooting

### Release Workflow Failed

**Symptom**: Release workflow shows red X

**Common Causes**:
- Tag already exists (trying to release same version twice)
- Permission issues (bot cannot push to main)
- Version bump script error

**Resolution**:
1. Check workflow logs for error message
2. If tag exists, delete it: `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`
3. Re-run the workflow

### Build Workflow Failed

**Symptom**: Build workflow shows red X, artifacts missing

**Common Causes**:
- Build script error (PyInstaller, fpm, Inno Setup)
- Dependency installation failure
- System dependency missing on runner

**Resolution**:
1. Check build workflow logs for errors
2. Fix the issue (update build scripts if needed)
3. Manually trigger build workflow:
   - Go to Actions → Build
   - Run workflow with the tag (e.g., `v0.1.1`)
   - Check "upload_to_release" option
4. Artifacts will be uploaded to existing release draft

### Artifacts Partially Missing

**Symptom**: Some artifacts uploaded, others missing

**Resolution**:
1. Check which job failed in build workflow
2. Re-run only failed jobs:
   - Click on failed workflow run
   - Click "Re-run failed jobs" button
3. Or manually trigger full build workflow again

### Need to Undo a Release

**Before Publishing**:
1. Delete the release draft from GitHub Releases page
2. Delete the tag: `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`
3. Revert version bump commit on main (if needed)

**After Publishing**:
- Releases cannot be "unpublished" on GitHub
- You can mark it as pre-release or delete it, but it remains in history
- Best practice: Create a new patch release to fix issues

## Version Numbering Strategy

Follow semantic versioning (https://semver.org/):

- **Major** (X.0.0): Breaking changes
  - API changes that break compatibility
  - Remove deprecated features
  - Major UI/UX overhauls

- **Minor** (0.X.0): New features
  - New download sources
  - New audio formats
  - UI improvements
  - New configuration options

- **Patch** (0.0.X): Bug fixes
  - Download failures fixed
  - UI bugs fixed
  - Performance improvements
  - Security patches

## Release Checklist

Use this checklist for every release:

- [ ] All PRs merged to main
- [ ] CI tests passing on main
- [ ] Release notes prepared (if manual additions needed)
- [ ] Triggered release workflow
- [ ] Release workflow completed successfully
- [ ] Build workflow triggered automatically
- [ ] Build workflow completed successfully
- [ ] All 4 artifacts present in release draft
- [ ] Artifacts tested on at least one platform
- [ ] Changelog reviewed and edited
- [ ] Release published
- [ ] Announcement posted (if applicable)

## Automation Details

### Release Workflow (`release.yml`)

Triggered by: Manual dispatch from GitHub Actions UI

Steps:
1. Get latest tag from repository
2. Calculate new version based on bump type
3. Update `pyproject.toml` with new version
4. Commit and push version bump to main
5. Create and push new tag
6. Generate changelog from commits
7. Create release draft with changelog
8. Trigger build workflow

### Build Workflow (`build.yml`)

Triggered by: Release workflow (or manual dispatch)

Jobs:
1. **build-linux** (ubuntu-latest):
   - Install dependencies (Python, FFmpeg, Qt libs, fpm, appimagetool)
   - Build with PyInstaller
   - Create AppImage
   - Create .deb package
   - Create .rpm package
   - Upload artifacts

2. **build-windows** (windows-latest):
   - Install dependencies (Python, Inno Setup)
   - Build with PyInstaller
   - Create Windows installer
   - Upload artifact

3. **upload-to-release**:
   - Download all artifacts
   - Upload to release draft

## Support

If you encounter issues not covered in this guide:
1. Check GitHub Actions logs for detailed error messages
2. Review build scripts in `scripts/` directory
3. Review workflow files in `.github/workflows/`
4. Open an issue with workflow run URL and error details

## Quick Reference

| Action | Command/Location |
|--------|-----------------|
| Trigger release | Actions → Release → Run workflow |
| View releases | Releases tab or `/releases` |
| View workflow runs | Actions tab |
| Delete tag | `git push --delete origin vX.Y.Z` |
| Re-run build | Actions → Build → Run workflow |
| Check artifacts | Release draft → Assets section |
