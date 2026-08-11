# Release Management Guide

This guide is for release managers who trigger and publish releases for Audio Fetch.

## Overview
The release process is fully automated through GitHub Actions workflows in two stages:

**Stage 1: Release Preparation** (Manual trigger)
1. **Release Workflow** - Creates release branch, bumps version, creates Pull Request
2. **CI Tests** - Automatically run on the PR
3. **Manual Review** - Manager reviews and merges the PR

**Stage 2: Release Publishing** (Automatic after PR merge)
4. **Post-Merge Release Workflow** - Creates tag, generates changelog, creates release draft
5. **Build Workflow** - Builds multi-platform binaries and uploads to release
6. **Manual Publish** - Manager reviews and publishes the release

## Triggering a Release

### Prerequisites
- You must have write access to the repository
- All changes should be merged to `main` branch
- CI tests should be passing on `main`
- Branch protection rules are configured on `main` branch

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
3. **Monitor Release PR Creation**
   - Release workflow runs (~1 minute):
     - Calculates new version number
     - Creates release branch (e.g., `release/v0.1.1`)
     - Updates version in `pyproject.toml`
     - Commits and pushes to release branch
     - Creates Pull Request to `main`
   
   - Wait for workflow to complete
   - Check workflow summary for PR link

4. **Review the Pull Request**
   - Click on the PR link from workflow summary
   - Review the version bump in `pyproject.toml`
   - Wait for CI tests to pass (status checks)
   - Verify all checks are green ✓

5. **Merge the Pull Request**
   - Once tests pass, click "Merge pull request"
   - Confirm the merge
   - **Important**: Do NOT delete the release branch yet (workflow handles this)

6. **Automatic Release Publishing**
   - Post-merge workflow runs automatically (~2 minutes):
     - Creates and pushes git tag (e.g., `v0.1.1`)
     - Generates changelog from commits
     - Creates release draft on GitHub
     - Triggers build workflow
     - Deletes the release branch
   
   - Build workflow runs (~15-20 minutes):
     - Builds Linux packages (AppImage, .deb, .rpm)
     - Builds Windows installer
     - Uploads all artifacts to release draft

7. **Monitor Progress**
   - Check "Post-Merge Release" workflow run for completion
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

### Release Workflow Failed to Create PR

**Symptom**: Release workflow shows red X, no PR created

**Common Causes**:
- Tag already exists (trying to release same version twice)
- Branch already exists (previous release attempt)
- Permission issues (bot cannot create branches)
- Version bump script error

**Resolution**:
1. Check workflow logs for error message
2. If tag exists, delete it: `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`
3. If branch exists, delete it: `git push --delete origin release/vX.Y.Z`
4. Re-run the workflow

### CI Tests Failed on Release PR

**Symptom**: PR has red X, cannot merge

**Resolution**:
1. Check which test failed in PR checks
2. Fix the issue on the release branch or main branch
3. If fixing on main:
   - Merge fix to main first
   - Update release branch: `git checkout release/vX.Y.Z && git merge main && git push`
4. If fixing on release branch:
   - Push fix to release branch
   - Tests will re-run automatically
5. Wait for tests to pass, then merge PR

### Post-Merge Workflow Failed

**Symptom**: PR merged but no tag/release created

**Common Causes**:
- Workflow didn't trigger (wrong branch name format)
- Tag already exists
- Permission issues

**Resolution**:
1. Check "Post-Merge Release" workflow runs in Actions tab
2. If workflow didn't run, manually trigger it or create tag manually
3. If tag exists, delete and re-trigger: `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`
4. Manually re-run the workflow from Actions tab

### Artifacts Partially Missing

**Symptom**: Some artifacts uploaded, others missing

**Resolution**:
1. Check which job failed in build workflow
2. Re-run only failed jobs:
   - Click on failed workflow run
   - Click "Re-run failed jobs" button
3. Or manually trigger full build workflow again

### Need to Undo a Release

### Need to Cancel a Release

**Before Merging PR**:
1. Close the release PR without merging
2. Delete the release branch: `git push --delete origin release/vX.Y.Z`
3. Delete the tag if created: `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`

**After Merging PR (Before Publishing)**:
1. Delete the release draft from GitHub Releases page
2. Delete the tag: `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`
3. Revert the version bump commit on main if needed

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

- [ ] All PRs merged to main
- [ ] CI tests passing on main
- [ ] Release notes prepared (if manual additions needed)
- [ ] Triggered release workflow
- [ ] Release workflow completed successfully
- [ ] Release PR created
- [ ] CI tests passing on release PR
- [ ] Release PR reviewed
- [ ] Release PR merged
- [ ] Post-merge workflow completed successfully
- [ ] Git tag created
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
3. Check if tag already exists
4. Update `pyproject.toml` with new version
5. Create release branch (e.g., `release/v0.1.1`)
6. Commit version bump to release branch
7. Push release branch
8. Create Pull Request to main branch

### Post-Merge Release Workflow (`post-merge-release.yml`)

Triggered by: PR merge to main (when PR branch starts with `release/`)

Steps:
1. Extract version from branch name
2. Get previous tag for changelog
3. Create and push new tag
4. Generate changelog from commits
5. Create release draft with changelog
6. Trigger build workflow
7. Delete release branch

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
