# Release Workflow Changes Summary

## Problem
Repository có branch protection rules:
- Không được push trực tiếp vào `main`
- Yêu cầu status check "test" phải pass
- Phải tạo Pull Request

Workflow cũ cố gắng push trực tiếp vào `main` → bị reject.

## Solution: 2-Stage Workflow

### Stage 1: Release Preparation (Manual)
**Workflow**: `.github/workflows/release.yml`
**Trigger**: Manual dispatch từ GitHub Actions UI

**Flow**:
1. User chọn version bump type (patch/minor/major)
2. Workflow tính toán version mới
3. Tạo release branch: `release/vX.Y.Z`
4. Update version trong `pyproject.toml`
5. Commit và push lên release branch
6. **Tự động tạo Pull Request** vào `main`
7. Hiển thị link PR trong workflow summary

**Kết quả**: Release PR được tạo, CI tests tự động chạy

### Stage 2: Release Publishing (Automatic)
**Workflow**: `.github/workflows/post-merge-release.yml`
**Trigger**: Tự động khi PR merge vào `main` (chỉ với branch `release/*`)

**Flow**:
1. Phát hiện PR merge từ release branch
2. Extract version từ branch name
3. Tạo và push git tag (e.g., `v1.0.0`)
4. Generate changelog từ commits
5. Tạo GitHub release draft
6. Trigger build workflow
7. Xóa release branch

**Kết quả**: Release draft sẵn sàng với builds đang chạy

## Files Changed

### 1. `.github/workflows/release.yml` (Modified)
**Thay đổi**:
- ❌ Removed: Direct push to main
- ❌ Removed: Tag creation in this workflow
- ❌ Removed: Changelog generation
- ❌ Removed: Release draft creation
- ✅ Added: Release branch creation
- ✅ Added: Pull Request creation
- ✅ Added: PR link in summary

**Before**: 228 lines → **After**: 167 lines

### 2. `.github/workflows/post-merge-release.yml` (New)
**Purpose**: Automatic release publishing after PR merge
**Lines**: 194 lines
**Features**:
- Detects merged release PRs
- Creates git tags
- Generates changelog
- Creates release draft
- Triggers build workflow
- Cleans up release branch

### 3. `docs/RELEASE.md` (Updated)
**Changes**:
- Updated overview to reflect 2-stage process
- Added PR review steps
- Added troubleshooting for PR failures
- Updated checklist with new steps
- Added post-merge workflow documentation

## New Release Process for Users

### Quick Steps:
```
1. GitHub Actions → Release → Run workflow → Choose bump type
2. Wait for PR creation (~1 min)
3. Review PR, wait for CI tests to pass
4. Merge PR
5. Automatic: Tag created, release draft created, builds triggered
6. Review release draft and publish
```

## Benefits

✅ **Complies with branch protection rules**
- No direct push to main
- Tests must pass before merge
- Changes go through PR review

✅ **Better visibility**
- Version bump visible in PR diff
- CI tests run before release
- Clear approval step

✅ **Safer process**
- Can cancel before merge (just close PR)
- Tests catch issues early
- No failed pushes in workflow logs

✅ **Traceable**
- PR shows what changed
- Clear audit trail
- Easy to reference in future

## Migration Notes

### For release managers:
- Same trigger point (GitHub Actions UI)
- Extra step: Merge PR after tests pass
- Everything else automated as before

### Existing releases:
- No impact on existing tags/releases
- Works with current versioning scheme
- Compatible with existing build workflow

## Testing Checklist

- [ ] Run release workflow with patch bump
- [ ] Verify PR is created
- [ ] Verify CI tests run on PR
- [ ] Merge PR
- [ ] Verify post-merge workflow creates tag
- [ ] Verify release draft is created
- [ ] Verify build workflow is triggered
- [ ] Verify release branch is deleted

## Rollback Plan

If needed, can rollback by:
1. Revert commits in this PR
2. Old workflow still exists in git history
3. No data loss (tags/releases not affected by workflow changes)
