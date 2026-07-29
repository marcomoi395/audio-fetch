# Kế hoạch Cải thiện Test Suite - Audio Fetch (v2)

## Hiện trạng (đo thực tế)

| File | Coverage | Dòng miss |
|------|----------|-----------|
| `api/routes.py` | 83% | 95-99, 114, 122-124 |
| `services/downloader.py` | 73% | 91-100, 132, 159, 195, 219-231, 235-236, 248-265 |
| `services/queue.py` | **100%** | — |
| `api/models.py` | 100% | — |
| `main.py` | 96% | 53 |

**Tests:** 22 total — 20 pass, **2 fail**

---

## Chẩn đoán failing tests

### `test_full_workflow_video_info_to_download`
**Nguyên nhân gốc:** Test mock sai điểm. Test mock `services.downloader.yt_dlp.YoutubeDL` nhưng `download_audio` chạy bên trong `run_in_executor` → yt-dlp "download" xảy ra nhưng không tạo file thật → logic tìm file (`glob`) tìm không ra → raise exception → response 400, `FileResponse` không được gọi.

**Sửa:** Mock `services.downloader.download_audio` trực tiếp (giống `test_download.py` đang làm đúng), sau đó tạo một file giả trong temp dir để `FileResponse` có thể đọc.

### `test_concurrent_download_blocking`
**Nguyên nhân gốc:** Cùng vấn đề trên — download raise exception → 400. Test assertion `in [200, 503]` đúng về ý định nhưng mock không đủ để download succeed.

**Sửa:** Mock `download_audio` trả về path hợp lệ.

---

## Implementation Plan

### Phase 1: Fix Failing Integration Tests
**Priority:** URGENT — Không để failing tests tồn tại trong codebase.

#### Task 1.1: Sửa integration test mocking
**Description:** Align mock strategy với cách implementation thực sự hoạt động.

**Root causes:**
1. `test_full_workflow`: Mock sai layer (yt_dlp thay vì `download_audio`)
2. `test_concurrent_download_blocking`: Cùng vấn đề mock layer

**Acceptance Criteria:**
- [ ] `test_full_workflow_video_info_to_download` passes
- [ ] `test_concurrent_download_blocking` passes
- [ ] Mock `services.downloader.download_audio` (không phải yt_dlp bên trong)
- [ ] Tạo file giả trong temp dir để FileResponse serve được

**Verification:**
- [ ] `pytest tests/test_integration.py -v` → 3/3 pass

**Dependencies:** None

**Files:** `tests/test_integration.py`

**Scope:** Small (~30 min)

---

### Phase 2: Fill Coverage Gaps trong Backend (Priority: HIGH)

Mục tiêu: `services/downloader.py` 73% → 95%+, `api/routes.py` 83% → 95%+

#### Task 2.1: Test error branches trong `download_audio`
**Description:** Lines 219-231, 235-236 (file-finding), 248-265 (DownloadError parsing) chưa được test.

**Acceptance Criteria:**
- [ ] Test trường hợp audio file không tìm được sau download (raise exception)
- [ ] Test fallback khi audio_files rỗng nhưng có all_files
- [ ] Test `DownloadError` với "Video unavailable" trong download context
- [ ] Test `DownloadError` với "Postprocessing" / FFmpeg error
- [ ] Test `DownloadError` với "HTTP Error 429" (rate limit)
- [ ] Test `DownloadError` với "network" / "timed out"
- [ ] Test `DownloadError` với "This video is private"

**Verification:**
- [ ] `pytest tests/test_downloader.py -v` → all pass
- [ ] `pytest --cov=services/downloader --cov-report=term-missing` → ≥ 95%

**Dependencies:** Task 1.1

**Files:** `tests/test_downloader.py`

**Scope:** Medium (~1 hour)

---

#### Task 2.2: Test error branches trong `get_video_info`
**Description:** Lines 91-100 (DownloadError parsing trong get_video_info) chưa được test.

**Acceptance Criteria:**
- [ ] Test "This video is private" → đúng error message
- [ ] Test "age-restricted" → đúng error message
- [ ] Test "This live event will begin" → đúng error message
- [ ] Test "Premieres in" → đúng error message
- [ ] Test generic DownloadError → wrapped message

**Verification:**
- [ ] `pytest tests/test_downloader.py::TestGetVideoInfo -v` → all pass

**Dependencies:** Task 1.1

**Files:** `tests/test_downloader.py`

**Scope:** Small (~30 min)

---

#### Task 2.3: Test coverage gaps trong `api/routes.py`
**Description:** Lines 95-99 (ascii fallback), 114 (cleanup exception), 122-124 (HTTPException cleanup path) chưa được test.

**Acceptance Criteria:**
- [ ] Test ascii filename fallback khi title toàn ký tự non-ASCII (e.g., chỉ tiếng Trung) → trả về `download.mp3`
- [ ] Test cleanup path khi HTTPException được re-raise (503)
- [ ] Test cleanup path khi exception xảy ra trong download

**Verification:**
- [ ] `pytest tests/test_download.py -v` → all pass
- [ ] `pytest --cov=api/routes --cov-report=term-missing` → ≥ 95%

**Dependencies:** Task 1.1

**Files:** `tests/test_download.py`

**Scope:** Small (~30 min)

---

#### Task 2.4: Test `main.py` line 53 (TemplateResponse)
**Description:** Route `/` trả về TemplateResponse chưa được test.

**Acceptance Criteria:**
- [ ] Test GET `/` → 200, trả về HTML content
- [ ] Test template render thành công (không raise exception)

**Verification:**
- [ ] `pytest tests/test_health.py -v` → all pass (thêm vào file này)

**Dependencies:** None (độc lập)

**Files:** `tests/test_health.py`

**Scope:** XS (~10 min)

---

### Checkpoint 1: Unit + Integration Tests
- [ ] `pytest tests/ --ignore=tests/e2e -v` → 0 failures
- [ ] Total coverage ≥ 95%
- [ ] Không còn DEBUG print statements trong production code (xem downloader.py lines 207-238)

> **Ghi chú:** Trong `services/downloader.py` có nhiều `print(f"DEBUG: ...")` — nên xóa trước khi tiếp tục, hoặc ít nhất log thay vì print.

---

### Phase 3: Setup E2E Infrastructure (Priority: HIGH)
**Dependency:** Phase 1 xong là đủ, không cần chờ Phase 2.

#### Task 3.1: Install và configure Playwright
**Description:** Setup pytest-playwright với FastAPI live server fixture và mock backend.

**Acceptance Criteria:**
- [ ] `pytest-playwright` và `anyio` thêm vào `requirements.txt`
- [ ] `playwright install chromium firefox` được document
- [ ] `tests/conftest.py` có:
  - `live_server` fixture tự start FastAPI app trên random port
  - `mock_video_info` fixture override `get_video_info` trả về fixture data
  - `mock_download_audio` fixture override `download_audio` tạo file giả
- [ ] `tests/e2e/__init__.py` tạo
- [ ] Demo smoke test pass: `GET /` trả về 200, có `<input id="youtube-url">`

**Verification:**
- [ ] `pytest tests/e2e/test_smoke.py -v` → pass
- [ ] `pytest tests/e2e/test_smoke.py -v --headed` → browser mở và pass

**Dependencies:** Phase 1

**Files:**
- `requirements.txt`
- `tests/conftest.py` (new)
- `tests/e2e/__init__.py` (new)
- `tests/e2e/test_smoke.py` (new)

**Scope:** Medium (~1 hour)

---

#### Task 3.2: Tạo Page Object và E2E helpers
**Description:** Page Object cho `index.html` với selectors khớp với HTML thực tế.

**Acceptance Criteria:**
- [ ] `AudioFetchPage` class có methods:
  - `navigate()` — go to homepage
  - `enter_url(url)` — fill #youtube-url
  - `click_fetch()` — click #fetch-btn
  - `wait_for_video_info()` — wait until #info-section visible
  - `wait_for_error()` — wait until #error-section visible
  - `wait_for_loading()` — wait until #loading-section visible
  - `select_format(fmt)` — select #format-select option
  - `select_quality(q)` — select #quality-select option
  - `click_download()` — click #download-btn
  - `get_error_message()` — read #error-message text
  - `get_video_title()` — read #video-title text
  - `click_retry()` — click #retry-btn
  - `click_new_url()` — click #new-url-btn

**Verification:**
- [ ] `from tests.e2e.page_objects import AudioFetchPage` — import OK

**Dependencies:** Task 3.1

**Files:** `tests/e2e/page_objects.py` (new)

**Scope:** Small (~30 min)

---

### Phase 4: Implement E2E Tests (Priority: CRITICAL)

#### Task 4.1: E2E Happy Path
**Description:** Full flow success — URL → info → download (với mock backend).

**Acceptance Criteria:**
- [ ] Homepage load thành công
- [ ] Input section visible ban đầu, các sections khác ẩn
- [ ] Nhập URL → click Fetch → loading section hiện
- [ ] Mock info trả về → info section hiện với đúng title/uploader/duration
- [ ] Select format mp3, quality 0
- [ ] Click download → browser download event được trigger (verify qua `expect_download()`)

**Verification:**
- [ ] `pytest tests/e2e/test_happy_path.py -v`

**Dependencies:** Task 3.2

**Files:** `tests/e2e/test_happy_path.py` (new)

**Scope:** Medium (~1.5 hours)

---

#### Task 4.2: E2E Error Handling
**Description:** Test UI error scenarios với mock backend trả về errors.

**Acceptance Criteria:**
- [ ] Mock `get_video_info` raise exception → error section hiện
- [ ] Error message text hiển thị đúng nội dung từ backend
- [ ] Click "Thử lại" → quay lại input section, URL input còn giữ giá trị cũ
- [ ] Click "Nhập URL khác" → quay lại input section, URL input bị xóa

**Verification:**
- [ ] `pytest tests/e2e/test_errors.py -v`

**Dependencies:** Task 3.2

**Files:** `tests/e2e/test_errors.py` (new)

**Scope:** Medium (~1 hour)

---

#### Task 4.3: E2E Queue Busy
**Description:** Test 503 response từ server khi queue bận.

**Acceptance Criteria:**
- [ ] Mock download endpoint trả về 503
- [ ] Error message "Another download is in progress" hiện trên UI
- [ ] Retry button visible

**Verification:**
- [ ] `pytest tests/e2e/test_queue_busy.py -v`

**Dependencies:** Task 3.2

**Files:** `tests/e2e/test_queue_busy.py` (new)

**Scope:** Small (~30 min)

---

#### Task 4.4: E2E Cross-browser (Chromium + Firefox)
**Description:** Chạy happy path test trên cả hai browsers.

**Acceptance Criteria:**
- [ ] Task 4.1 happy path pass trên Chromium
- [ ] Task 4.1 happy path pass trên Firefox
- [ ] Parametrize qua pytest-playwright `--browser` flag

**Verification:**
- [ ] `pytest tests/e2e/test_happy_path.py --browser chromium -v` → pass
- [ ] `pytest tests/e2e/test_happy_path.py --browser firefox -v` → pass

**Dependencies:** Task 4.1

**Files:** Không cần file mới — pytest-playwright parametrize built-in

**Scope:** XS (~15 min config)

---

### Checkpoint 2: E2E Tests Complete
- [ ] `pytest tests/e2e/ -v` → 0 failures
- [ ] 3 critical flows covered: happy path, error, queue busy
- [ ] Cross-browser confirmed

---

### Phase 5: Cleanup (Priority: MEDIUM)

#### Task 5.1: Xóa DEBUG print statements trong downloader.py
**Description:** `services/downloader.py` có 8 `print(f"DEBUG: ...")` trong production code (lines 207-238). Cần xóa hoặc thay bằng `logging`.

**Acceptance Criteria:**
- [ ] Không còn `print(f"DEBUG:` trong source code
- [ ] Thay bằng `logger.debug(...)` nếu cần giữ lại
- [ ] Existing tests vẫn pass

**Verification:**
- [ ] `grep -n "DEBUG:" services/downloader.py` → no results
- [ ] `pytest tests/ -v` → all pass

**Dependencies:** None (độc lập)

**Files:** `services/downloader.py`

**Scope:** XS (~10 min)

---

## Những gì KHÔNG làm (và lý do)

| Item | Lý do bỏ |
|------|-----------|
| Queue timeout tests (Task 2.3 cũ) | `queue.py` đã 100% coverage |
| CORS header tests | `*` wildcard — không có logic để test |
| JavaScript unit tests (Jest/Vitest) | Không có build toolchain, E2E đã cover behavior |
| "Real file download" integration test | Phụ thuộc network + yt-dlp real API → flaky |
| Responsive layout E2E | Manual test đủ, viewport resize tests không bắt được layout bugs thực tế |

---

## File structure sau khi hoàn thành

```
tests/
├── __init__.py
├── conftest.py                  # live_server + mock fixtures (NEW)
├── test_health.py               # + test GET /
├── test_api.py                  # unchanged (đã đủ)
├── test_download.py             # + ascii fallback, cleanup paths
├── test_downloader.py           # + all DownloadError branches
├── test_queue.py                # unchanged (100% coverage)
├── test_integration.py          # fixed mocking
└── e2e/
    ├── __init__.py              # NEW
    ├── page_objects.py          # NEW
    ├── test_smoke.py            # NEW
    ├── test_happy_path.py       # NEW
    ├── test_errors.py           # NEW
    └── test_queue_busy.py       # NEW
```

---

## Thứ tự ưu tiên thực hiện

```
Phase 1 (fix) → Phase 3.1 (setup E2E) → Phase 2 (coverage gaps)
                                       → Phase 3.2 (page objects)
                                       → Phase 4 (E2E tests)
                                                  → Phase 5 (cleanup)
```

Phase 2 và Phase 3 có thể song song vì độc lập nhau.

---

## Commands

```bash
# Unit + integration tests
pytest tests/ --ignore=tests/e2e -v --cov=. --cov-report=term-missing

# E2E tests (headless)
pytest tests/e2e/ -v

# E2E debug (browser visible)
pytest tests/e2e/ -v --headed --slowmo=500

# E2E cross-browser
pytest tests/e2e/test_happy_path.py --browser chromium --browser firefox -v
```
