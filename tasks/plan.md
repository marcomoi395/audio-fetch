# Implementation Plan: User-Provided Cookie Authentication

## Overview

Transition from environment-variable-based cookie authentication to mandatory user-provided cookies. Users must paste YouTube cookies into the web interface before any fetch/download operation. This removes deployment barriers caused by bot detection and makes the application usable in production environments.

## Architecture Decisions

- **Cookies are required, not optional**: Change all `cookies: str | None = None` to `cookies: str` throughout the stack
- **Validate early**: Check for cookies at the API boundary before calling yt-dlp
- **Clear error messages**: Return HTTP 400 with explicit "Cookies required" message when missing
- **Remove environment fallback**: Completely remove YOUTUBE_COOKIES and YOUTUBE_COOKIES_FILE support
- **Frontend enforcement**: Prevent fetch/download actions if cookies not provided (cookie UI already exists)
- **Maintain existing UI**: Cookie input UI already exists, just needs enforcement logic and label updates

## Dependency Graph

```
Backend Models (require cookies)
    │
    ├── Downloader Service (require cookies, remove env fallback)
    │   │
    │   └── API Routes (validate cookies before processing)
    │       │
    │       └── Frontend (enforce cookies before API calls)
    │           │
    │           └── Tests (update to pass required cookies)
```

## Task List

### Phase 1: Backend Foundation

#### Task 1: Update API models to require cookies

**Description:** Change `cookies` field from optional to required in both `VideoInfoRequest` and `DownloadRequest` models.

**Acceptance criteria:**
- [ ] `VideoInfoRequest.cookies` is `str` (not `str | None`)
- [ ] `DownloadRequest.cookies` is `str` (not `str | None`)
- [ ] Pydantic validation enforces non-empty cookie strings

**Verification:**
- [ ] Run: `pytest tests/test_api.py -v`
- [ ] Manual check: API should reject requests with missing `cookies` field

**Dependencies:** None

**Files to modify:**
- `api/models.py`

**Estimated scope:** Small (1 file, ~4 lines changed)

---

#### Task 2: Update downloader service to require cookies

**Description:** Change `youtube_cookies_context`, `get_video_info`, and `download_audio` to require cookies as mandatory parameters. Remove environment variable fallback logic completely.

**Acceptance criteria:**
- [ ] `youtube_cookies_context(cookies: str)` requires cookies parameter
- [ ] `get_video_info(url: str, cookies: str)` requires cookies parameter
- [ ] `download_audio(..., cookies: str)` requires cookies parameter
- [ ] No environment variable reading (YOUTUBE_COOKIES, YOUTUBE_COOKIES_FILE)
- [ ] Context manager always creates temp file from provided cookies
- [ ] Remove dead code at lines 248-255 (as noted in spec)

**Verification:**
- [ ] Run: `pytest tests/test_downloader.py -v`
- [ ] Build succeeds: `python -m py_compile services/downloader.py`
- [ ] Manual check: grep for "YOUTUBE_COOKIES" returns no matches in downloader.py
- [ ] Security check: Temp cookie files are cleaned up (verify finally block executes)
- [ ] Security check: Cookie content never logged (check logger calls)

**Dependencies:** Task 1 (models updated first)

**Files to modify:**
- `services/downloader.py`

**Estimated scope:** Medium (1 file, ~30 lines changed, logic removal)

---

#### Task 3: Add cookie validation in API routes

**Description:** Add explicit cookie validation at the route level. Return HTTP 400 with clear error message if cookies are empty or whitespace-only.

**Acceptance criteria:**
- [ ] `/video-info` endpoint validates cookies before calling `get_video_info`
- [ ] `/download` endpoint validates cookies before calling `download_audio`
- [ ] Empty or whitespace-only cookies return HTTP 400 with message "YouTube cookies are required"
- [ ] Valid requests pass cookies to downloader service

**Verification:**
- [ ] Run: `pytest tests/test_api.py::test_video_info_without_cookies -v`
- [ ] Run: `pytest tests/test_api.py::test_download_without_cookies -v`
- [ ] Manual check: curl without cookies returns 400

**Dependencies:** Task 2 (downloader service updated)

**Files to modify:**
- `api/routes.py`

**Estimated scope:** Small (1 file, ~10 lines added)

---

### Checkpoint: Backend Foundation
- [ ] All backend code requires cookies
- [ ] No environment variable fallback exists
- [ ] API returns clear errors for missing cookies
- [ ] Run: `pytest tests/test_api.py tests/test_downloader.py -v`

---

### Phase 2: Frontend Enforcement

#### Task 4: Add cookie validation before API calls

**Description:** Add validation in `handleFetchInfo` and `handleDownload` to check if cookies exist before making API requests. Show clear error if cookies are missing. No UI changes needed - cookie management interface already exists.

**Acceptance criteria:**
- [ ] `handleFetchInfo` checks `CookieManager.get()` returns non-null before calling API
- [ ] `handleDownload` checks `CookieManager.get()` returns non-null before calling API
- [ ] Missing cookies show error: "YouTube cookies are required. Please add cookies before fetching."
- [ ] Error displayed using existing `showError()` function
- [ ] Existing cookie UI functions unchanged (already implemented)

**Verification:**
- [ ] Manual check: Open app without cookies, click Fetch → see error message
- [ ] Manual check: Add cookies via existing UI, click Fetch → API call proceeds
- [ ] Manual check: Clear cookies, attempt download → see error message
- [ ] Browser console shows no errors

**Dependencies:** Task 3 (API validation in place)

**Files to modify:**
- `static/js/app.js` (add ~10 lines of validation in two functions)

**Estimated scope:** Small (1 file, ~10-15 lines added to existing functions)

---

#### Task 5: Update cookie UI to reflect mandatory requirement

**Description:** Update UI to clearly indicate cookies are mandatory. Change button text, ensure cookie section is visible by default, and disable fetch/download buttons when cookies are missing. No new UI components needed - just configuration of existing elements.

**Acceptance criteria:**
- [ ] Cookie button text changes from "🍪 Optional: Add cookies" to "🍪 Add Cookies (Required)"
- [ ] Cookie section is visible/expanded by default when page loads
- [ ] Help text updated to emphasize requirement (not just bot detection mitigation)
- [ ] Fetch button disabled when cookies are absent (enabled when cookies exist)
- [ ] Download button disabled when cookies are absent (enabled when cookies exist)
- [ ] Visual indication that cookies are mandatory (styling/warning color)
- [ ] All existing cookie UI functionality unchanged (save, clear, persist)

**Verification:**
- [ ] Manual check: Load page → cookie section visible and expanded by default
- [ ] Manual check: No cookies → Fetch button disabled, Download button disabled
- [ ] Manual check: Add cookies → buttons become enabled
- [ ] Manual check: Clear cookies → buttons become disabled again
- [ ] Manual check: Button text emphasizes "Required"
- [ ] Visual regression: NES.css retro theme maintained

**Dependencies:** Task 4 (validation logic in place)

**Files to modify:**
- `templates/index.html` (update button text, section visibility, ~5 lines changed)
- `static/js/app.js` (add button enable/disable logic, ~15 lines added)

**Estimated scope:** Small (2 files, ~20 lines changed/added)

---

### Checkpoint: Frontend Enforcement
- [ ] UI prevents requests without cookies
- [ ] Clear error messages guide users
- [ ] Security warnings displayed
- [ ] Manual test: Complete flow from cookie input to download works

---

### Phase 3: Testing & Cleanup

#### Task 6: Update unit tests to pass required cookies

**Description:** Update all test fixtures and test cases to provide required cookies. Remove tests for optional cookie behavior.

**Acceptance criteria:**
- [ ] All calls to `get_video_info` in tests include cookies parameter
- [ ] All calls to `download_audio` in tests include cookies parameter
- [ ] `conftest.py` fixtures updated to pass cookies to mocks
- [ ] Remove tests for environment variable cookie loading
- [ ] Add new test: `test_get_video_info_requires_cookies`
- [ ] Add new test: `test_download_audio_requires_cookies`

**Verification:**
- [ ] Run: `pytest tests/test_downloader.py -v --cov=services.downloader`
- [ ] Coverage for cookie handling: 100%
- [ ] All tests pass

**Dependencies:** Tasks 1, 2, 3 (backend changes complete)

**Files to modify:**
- `tests/test_downloader.py`
- `tests/conftest.py`

**Estimated scope:** Medium (2 files, ~40 lines changed)

---

#### Task 7: Update integration tests for cookie validation

**Description:** Update API integration tests to validate cookie requirement. Add tests for missing cookie scenarios.

**Acceptance criteria:**
- [ ] All API test requests include cookies in request body
- [ ] New test: `test_video_info_without_cookies` returns 400
- [ ] New test: `test_video_info_with_empty_cookies` returns 400
- [ ] New test: `test_download_without_cookies` returns 400
- [ ] New test: `test_download_with_empty_cookies` returns 400
- [ ] Existing tests updated to pass valid cookie strings

**Verification:**
- [ ] Run: `pytest tests/test_api.py -v --cov=api`
- [ ] Run: `pytest tests/test_integration.py -v`
- [ ] All tests pass
- [ ] Coverage for cookie validation paths: 100%

**Dependencies:** Task 6 (unit tests updated)

**Files to modify:**
- `tests/test_api.py`
- `tests/test_integration.py`

**Estimated scope:** Medium (2 files, ~60 lines changed/added)

---

#### Task 8: Remove environment variable support and documentation

**Description:** Remove all environment variable references from code and documentation. Update .env.example to remove YOUTUBE_COOKIES.

**Acceptance criteria:**
- [ ] No references to YOUTUBE_COOKIES in codebase (except in spec/migration docs)
- [ ] No references to YOUTUBE_COOKIES_FILE in codebase
- [ ] `.env.example` does not contain YOUTUBE_COOKIES
- [ ] README updated to explain user-provided cookie model
- [ ] COOKIE_EXPORT_GUIDE.md remains (users still need to export cookies)

**Verification:**
- [ ] Run: `grep -r "YOUTUBE_COOKIES" --exclude-dir=.git --exclude="*.md" --exclude-dir=docs .`
- [ ] Should return 0 matches (except in spec/documentation)
- [ ] Manual check: README accurately describes cookie flow

**Dependencies:** Tasks 6, 7 (all tests pass with new model)

**Files to modify:**
- `.env.example`
- `README.md`
- Any other documentation mentioning environment variables

**Estimated scope:** Small (2-3 files, documentation updates)

---

#### Task 9: Add E2E test for complete cookie flow

**Description:** Create end-to-end browser test using Playwright that covers the complete user workflow: cookie input → fetch video info → download. Verify both error handling (no cookies) and success flow (with cookies).

**Acceptance criteria:**
- [ ] E2E test: `test_cookie_flow_without_cookies` - verify error message shown
- [ ] E2E test: `test_cookie_flow_complete` - add cookies → fetch → download succeeds
- [ ] Test verifies cookie section is visible by default
- [ ] Test verifies buttons are disabled without cookies
- [ ] Test verifies buttons are enabled after adding cookies
- [ ] Test verifies security warning dialog appears on first cookie save
- [ ] Test verifies cookie status indicator shows when cookies active

**Verification:**
- [ ] Run: `pytest tests/e2e/test_cookie_flow.py -v`
- [ ] Both test scenarios pass
- [ ] E2E test covers spec requirement (line 602): "complete cookie input → download flow"

**Dependencies:** Tasks 4, 5 (frontend enforcement complete)

**Files to modify:**
- `tests/e2e/test_cookie_flow.py` (create new file or update existing, ~80 lines)

**Estimated scope:** Medium (1 file, ~80 lines new E2E test code)

---

### Checkpoint: Complete
- [ ] All tests pass: `pytest -v`
- [ ] E2E tests pass: `pytest tests/e2e/ -v`
- [ ] Linting passes: `ruff check .`
- [ ] Type checking passes: `mypy .`
- [ ] Manual E2E flow works: cookie input → fetch → download
- [ ] No environment variable references remain
- [ ] Documentation updated
- [ ] Security verified: temp files cleaned up, cookies not logged
---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking existing deployments with env vars | High | This is intentional per spec; document migration path |
| Users don't understand cookie requirement | Medium | Clear UI messaging, security warnings, help documentation |
| Cookie validation too strict | Medium | Accept any non-empty string, let yt-dlp validate format |
| Tests fail after making cookies required | Medium | Update tests incrementally (phase 3), verify each step |

## Parallel Work Opportunities

- **Can parallelize**: Tasks 6 and 7 (different test files)
- **Must be sequential**: Tasks 1 → 2 → 3 (dependency chain)
- **Must be sequential**: Tasks 3 → 4 (backend before frontend)

## Verification Commands

```bash
# Run after each task
pytest tests/test_api.py tests/test_downloader.py -v

# Run at each checkpoint
pytest -v

# Run before completion
pytest -v --cov=. --cov-report=term-missing
ruff check .
mypy .
```

## Estimated Timeline

- Phase 1 (Backend): ~3 hours (3 small/medium tasks)
- Phase 2 (Frontend): ~2.5 hours (2 small/medium tasks)
- Phase 3 (Testing): ~4 hours (4 medium tasks including E2E)
- **Total: ~9.5 hours** (~1.5 focused days)

## Success Criteria

All items from SPEC.md "Success Criteria" section:
1. ✓ Users can paste Netscape-format cookies into web interface (already exists)
2. ✓ Cookies persist across browser sessions (already implemented)
3. ✓ Cookie input **mandatory** - users must provide cookies before fetch/download
4. ✓ Clear error message shown when user attempts fetch/download without cookies
5. ✓ Security warnings clearly displayed (already exists, enhance visibility)
6. ✓ Environment-based cookie authentication completely removed
7. ✓ All existing tests pass with new cookie-passing mechanism
8. ✓ Bot detection resolved (verified through manual production testing)
