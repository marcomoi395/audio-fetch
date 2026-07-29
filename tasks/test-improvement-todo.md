# Test Improvement Tasks - Audio Fetch (v2)

## Phase 1: Fix Failing Tests ⚠️ URGENT

- [ ] 1.1: Fix integration test mocking (mock `download_audio` trực tiếp, không phải yt_dlp)

## Phase 2: Fill Coverage Gaps (song song với Phase 3)

- [ ] 2.1: Test tất cả DownloadError branches trong `download_audio` (lines 248-265)
- [ ] 2.2: Test DownloadError branches trong `get_video_info` (lines 91-100)
- [ ] 2.3: Test ascii fallback + cleanup paths trong `api/routes.py` (lines 95-99, 122-124)
- [ ] 2.4: Test GET `/` route trong `main.py` (line 53)

**Checkpoint 1:** `pytest tests/ --ignore=tests/e2e -v` → 0 failures, coverage ≥ 95%

## Phase 3: Setup E2E Infrastructure (song song với Phase 2)

- [ ] 3.1: Install pytest-playwright, tạo `conftest.py` với live_server + mock fixtures
- [ ] 3.2: Tạo `AudioFetchPage` page object với selectors khớp HTML thực tế

## Phase 4: E2E Tests ⭐ CRITICAL

- [ ] 4.1: E2E happy path (URL → info → download với mock backend)
- [ ] 4.2: E2E error handling (server error → error UI → retry/new URL)
- [ ] 4.3: E2E queue busy (503 → error message trên UI)
- [ ] 4.4: E2E cross-browser (Chromium + Firefox)

**Checkpoint 2:** `pytest tests/e2e/ -v` → 0 failures, 3+ flows covered

## Phase 5: Cleanup

- [ ] 5.1: Xóa `print(f"DEBUG: ...")` trong `services/downloader.py` (8 chỗ, lines 207-238)

---

## Không làm

- Queue tests thêm → `queue.py` đã 100% coverage
- CORS tests → middleware `*` wildcard, không có logic
- JS unit tests → không có build toolchain, E2E đủ
- "Real" integration test với YouTube API thật → flaky

## Current Status

- **Tests:** 22 total — 20 pass, **2 fail**
- **Coverage:** `routes.py` 83%, `downloader.py` 73%, `queue.py` 100%
- **E2E:** 0 tests (target: 4+ tests covering 3 flows)
