# Implementation Plan: Audio-Fetch Web App

## Overview

Convert the CLI audio-fetch tool into a FastAPI web application with an 8-bit retro interface. Work is sliced vertically to deliver complete, testable feature paths incrementally. Each task leaves the system in a working state.

## Architecture Decisions

- **Single-threaded download queue**: Use asyncio.Lock to prevent concurrent downloads, reject requests with HTTP 503 when busy
- **Stateless design**: No database, temporary files cleaned immediately after streaming to browser
- **Reuse existing logic**: Adapt `audio_downloader.py` AudioDownloader class for web context
- **Vanilla JS frontend**: No framework overhead, direct integration with NES.css
- **Sound effect strategy**: Pre-load sounds on page load, play via Web Audio API with error handling
- **Testing approach**: Mock yt-dlp responses with fixtures, avoid live YouTube API calls in tests

## Dependency Graph

```
Project Structure
    │
    ├── Dependencies (requirements.txt)
    │       │
    │       ├── Downloader Service (video info)
    │       │       │
    │       │       ├── API Models (Pydantic)
    │       │       │       │
    │       │       │       └── Video Info Endpoint
    │       │       │               │
    │       │       │               └── Frontend Video Info UI
    │       │       │
    │       │       └── Download Queue
    │       │               │
    │       │               └── Download Endpoint
    │       │                       │
    │       │                       └── Frontend Download UI
    │       │
    │       └── 8-bit Sound Effects
    │               │
    │               └── Sound Integration in UI
    │
    └── Tests (after implementation complete)
```

---

## Phase 1: Foundation

### Task 1: Project Setup and Dependencies

**Description:** Initialize FastAPI project structure, create requirements.txt, set up virtual environment, and verify FFmpeg availability.

**Acceptance Criteria:**
- [ ] Directory structure matches SPEC.md (api/, services/, static/, templates/, tests/)
- [ ] requirements.txt includes: fastapi, uvicorn, yt-dlp, aiofiles, pytest, pytest-asyncio, httpx, pytest-cov, ruff, black, mypy
- [ ] Virtual environment created and dependencies installed
- [ ] FFmpeg check passes (available in PATH)

**Verification:**
- [ ] `pip list` shows all required packages
- [ ] `ffmpeg -version` returns version info
- [ ] All directories exist with __init__.py where needed

**Dependencies:** None

**Files to Create:**
- `requirements.txt`
- `api/__init__.py`
- `api/models.py`
- `api/routes.py`
- `services/__init__.py`
- `services/downloader.py`
- `services/queue.py`
- `static/css/custom.css`
- `static/js/app.js`
- `static/js/audio.js`
- `tests/__init__.py`

**Estimated Complexity:** Small (setup task)

---

### Task 2: FastAPI App with Health Endpoint

**Description:** Create main.py FastAPI application with CORS, static file serving, template rendering, and /health endpoint.

**Acceptance Criteria:**
- [ ] FastAPI app starts on port 8000 with uvicorn
- [ ] /health endpoint returns {"status": "ok", "ffmpeg_available": true/false, "queue_active": false}
- [ ] Static files served from /static/
- [ ] Templates configured for Jinja2
- [ ] CORS configured for local development

**Verification:**
- [ ] `uvicorn main:app --reload` starts without errors
- [ ] `curl http://localhost:8000/health` returns JSON response
- [ ] Browser can access http://localhost:8000/health

**Dependencies:** Task 1

**Files to Create:**
- `main.py`

**Estimated Complexity:** Small

---

## Checkpoint: Foundation Complete
- [ ] Server runs and health endpoint responds
- [ ] FFmpeg is available
- [ ] Ready to build core services

---

## Phase 2: Video Info Flow

### Task 3: Downloader Service - Video Info Extraction

**Description:** Adapt AudioDownloader class from audio_downloader.py to extract video metadata (title, uploader, duration, thumbnail) using yt-dlp without downloading.

**Acceptance Criteria:**
- [ ] `get_video_info(url: str)` async function returns dict with title, uploader, duration, thumbnail_url
- [ ] Handles invalid URLs with descriptive error messages
- [ ] Uses yt-dlp extract_info with download=False
- [ ] Format duration as MM:SS or HH:MM:SS
- [ ] Includes format/quality constants from original AudioDownloader

**Verification:**
- [ ] Manual test with pytest: `pytest tests/test_downloader.py::test_get_video_info -v`
- [ ] Test with valid YouTube URL returns metadata
- [ ] Test with invalid URL raises exception with detail

**Dependencies:** Task 2

**Files to Edit:**
- `services/downloader.py`

**Estimated Complexity:** Medium

---

### Task 4: Video Info API Endpoint

**Description:** Create Pydantic models and POST /api/video-info endpoint that calls downloader service and returns JSON response.

**Acceptance Criteria:**
- [ ] VideoInfoRequest model validates YouTube URLs (HttpUrl type)
- [ ] VideoInfoResponse model matches spec structure
- [ ] POST /api/video-info endpoint implemented
- [ ] Returns 200 with metadata on success
- [ ] Returns 400 with detailed error on failure
- [ ] Error messages include yt-dlp error details

**Verification:**
- [ ] `curl -X POST http://localhost:8000/api/video-info -H "Content-Type: application/json" -d '{"url":"https://youtube.com/watch?v=dQw4w9WgXcQ"}'` returns JSON
- [ ] Invalid URL returns 400 error
- [ ] Response matches VideoInfoResponse schema

**Dependencies:** Task 3

**Files to Edit:**
- `api/models.py`
- `api/routes.py`
- `main.py` (register router)

**Estimated Complexity:** Small

---

### Task 5: Frontend - Video Info UI

**Description:** Create index.html with NES.css, implement URL input form, fetch button, and display video metadata (thumbnail, title, uploader, duration).

**Acceptance Criteria:**
- [ ] index.html uses NES.css CDN and custom.css
- [ ] URL input field with NES.css styling (nes-input)
- [ ] "Fetch Info" button (nes-btn is-primary)
- [ ] 8-bit loading spinner shows during fetch (CSS animation)
- [ ] Video info displayed: thumbnail image, title, uploader, duration
- [ ] Format/quality dropdowns populated (nes-select)
- [ ] Error messages displayed in nes-container is-error
- [ ] app.js implements fetchVideoInfo() function

**Verification:**
- [ ] Manual test: Open http://localhost:8000, paste YouTube URL, click Fetch Info
- [ ] Video metadata displays correctly
- [ ] Loading spinner shows during fetch
- [ ] Error messages display for invalid URLs

**Dependencies:** Task 4

**Files to Create:**
- `templates/index.html`

**Files to Edit:**
- `static/js/app.js`
- `static/css/custom.css`
- `main.py` (add root route serving index.html)

**Estimated Complexity:** Medium

---

## Checkpoint: Video Info Flow Complete
- [ ] User can paste URL and see video metadata
- [ ] UI matches 8-bit aesthetic (basic version)
- [ ] Error handling works end-to-end
- [ ] Ready to add download functionality

---

## Phase 3: Download Flow

### Task 6: Download Queue Service

**Description:** Implement single-threaded download queue using asyncio.Lock to prevent concurrent downloads.

**Acceptance Criteria:**
- [ ] DownloadQueue class with async context manager
- [ ] is_active() method checks if download in progress
- [ ] download() method acquires lock, raises HTTP 503 if busy
- [ ] Lock released in finally block (even on error)
- [ ] Singleton pattern (single global queue instance)

**Verification:**
- [ ] Unit test: concurrent requests blocked with 503
- [ ] Unit test: lock released after download completes
- [ ] Unit test: lock released after download fails

**Dependencies:** Task 3

**Files to Edit:**
- `services/queue.py`

**Estimated Complexity:** Small

---

### Task 7: Download API Endpoint

**Description:** Create POST /api/download endpoint that uses queue to download audio, stream to browser, and cleanup temp files.

**Acceptance Criteria:**
- [ ] DownloadRequest model validates url, format, quality
- [ ] POST /api/download endpoint implemented
- [ ] Uses DownloadQueue to prevent concurrent downloads
- [ ] Downloads to temp directory (tempfile.mkdtemp)
- [ ] Streams file with FileResponse (streaming mode)
- [ ] Content-Disposition header sets filename
- [ ] Temp files deleted in background task after streaming
- [ ] Returns 503 if queue is busy
- [ ] Returns 400 with yt-dlp error details on failure

**Verification:**
- [ ] Manual test: trigger download, verify file downloaded to browser
- [ ] Verify temp files cleaned up after download
- [ ] Test concurrent downloads: second request gets 503
- [ ] Test various formats (mp3, m4a, opus) and qualities

**Dependencies:** Task 6

**Files to Edit:**
- `api/models.py`
- `api/routes.py`
- `services/downloader.py` (add download method)

**Estimated Complexity:** Large (complex file handling)

---

### Task 8: Frontend - Download UI

**Description:** Add format/quality selection dropdowns, download button, progress states, and trigger browser download.

**Acceptance Criteria:**
- [ ] Format dropdown populated with 5 options (mp3, m4a, opus, wav, best)
- [ ] Quality dropdown populated with 3 options (0, 5, 9) with Vietnamese labels
- [ ] Download button enabled only after video info fetched
- [ ] Download button disabled during download (shows loading spinner)
- [ ] app.js implements downloadAudio() function
- [ ] Handles FileResponse and triggers browser download
- [ ] Shows "downloading" state with 8-bit spinner
- [ ] Shows success message after download completes
- [ ] Shows error message on failure (503 or 400)

**Verification:**
- [ ] Manual test: complete flow from URL to download
- [ ] Test all 5 formats download successfully
- [ ] Test concurrent download attempt shows "busy" error
- [ ] Test download failure shows detailed error

**Dependencies:** Task 7

**Files to Edit:**
- `templates/index.html`
- `static/js/app.js`
- `static/css/custom.css`

**Estimated Complexity:** Medium

---

## Checkpoint: Download Flow Complete
- [ ] End-to-end flow works: paste URL → fetch info → download audio
- [ ] All formats and qualities work
- [ ] Queue prevents concurrent downloads
- [ ] Temp files cleaned up
- [ ] Ready to add 8-bit polish

---

## Phase 4: 8-bit Theme

### Task 9: Source and Integrate 8-bit Sounds

**Description:** Find free 8-bit sound effects, add to static/sounds/, implement audio.js sound manager.

**Acceptance Criteria:**
- [ ] 5 sound files sourced: click.mp3, fetch.mp3, download.mp3, success.mp3, error.mp3
- [ ] All sounds are 8-bit/chiptune style
- [ ] Sounds placed in static/sounds/
- [ ] audio.js implements SoundManager class with preload() and play(soundName) methods
- [ ] Sounds preloaded on page load
- [ ] Volume set to 0.5 by default
- [ ] Graceful fallback if sound fails to play

**Verification:**
- [ ] Manual test: open browser console, call SoundManager.play('click')
- [ ] All 5 sounds play successfully
- [ ] Sounds match 8-bit aesthetic

**Dependencies:** None (can be done in parallel)

**Files to Create:**
- `static/sounds/click.mp3`
- `static/sounds/fetch.mp3`
- `static/sounds/download.mp3`
- `static/sounds/success.mp3`
- `static/sounds/error.mp3`

**Files to Edit:**
- `static/js/audio.js`

**Estimated Complexity:** Small

---

### Task 10: NES.css Theme Implementation

**Description:** Apply NES.css white mode theme, add 8-bit visual elements, wire sound effects to UI interactions.

**Acceptance Criteria:**
- [ ] All UI elements use NES.css classes (nes-container, nes-btn, nes-input, nes-select)
- [ ] White mode theme applied (default NES.css)
- [ ] 8-bit pixel art header/logo added
- [ ] Custom CSS for layout and spacing in custom.css
- [ ] Loading spinners use 8-bit style animation
- [ ] Sound effects wired: button hover → click.mp3 (low volume), fetch button → fetch.mp3, download button → download.mp3, success → success.mp3, error → error.mp3
- [ ] Responsive layout (works on mobile and desktop)

**Verification:**
- [ ] Manual test: all interactions play sounds
- [ ] Visual appearance matches 8-bit retro aesthetic
- [ ] Test on Chrome, Firefox, Safari
- [ ] Test on mobile viewport

**Dependencies:** Task 9

**Files to Edit:**
- `templates/index.html`
- `static/css/custom.css`
- `static/js/app.js` (wire sounds to events)

**Estimated Complexity:** Medium

---

## Checkpoint: 8-bit Theme Complete
- [ ] UI has full retro 8-bit aesthetic
- [ ] All interactions have sound effects
- [ ] Visual polish complete
- [ ] Ready for testing phase

---

## Phase 5: Testing

### Task 11: Unit Tests for Services

**Description:** Write pytest unit tests for downloader and queue services with mocked yt-dlp responses.

**Acceptance Criteria:**
- [ ] test_downloader.py covers get_video_info and download methods
- [ ] Fixtures created for mocked yt-dlp responses
- [ ] Tests cover: success case, invalid URL, unavailable video, network error
- [ ] test_queue.py covers single download, concurrent blocking, lock release
- [ ] Coverage ≥90% for services/ directory

**Verification:**
- [ ] `pytest tests/test_downloader.py -v` passes
- [ ] `pytest tests/test_queue.py -v` passes
- [ ] `pytest tests/ --cov=services --cov-report=term-missing` shows ≥90% coverage

**Dependencies:** Task 7, Task 8 (implementation complete)

**Files to Create:**
- `tests/test_downloader.py`
- `tests/test_queue.py`
- `tests/fixtures.py` (yt-dlp mock responses)

**Estimated Complexity:** Medium

---

### Task 12: Integration Tests for API

**Description:** Write pytest integration tests for FastAPI endpoints using TestClient.

**Acceptance Criteria:**
- [ ] test_api.py tests /health, /api/video-info, /api/download endpoints
- [ ] Tests use FastAPI TestClient with mocked services
- [ ] Tests cover: 200 success, 400 bad request, 503 queue busy
- [ ] Response schemas validated
- [ ] Coverage ≥80% for api/ directory

**Verification:**
- [ ] `pytest tests/test_api.py -v` passes
- [ ] `pytest tests/ --cov=api --cov-report=term-missing` shows ≥80% coverage
- [ ] `pytest tests/ --cov=. --cov-report=term-missing` shows ≥80% overall

**Dependencies:** Task 11

**Files to Create:**
- `tests/test_api.py`

**Estimated Complexity:** Medium

---

## Checkpoint: Testing Complete
- [ ] All tests pass
- [ ] Coverage goals met (≥80% overall)
- [ ] CI/CD ready (tests can run in automation)
- [ ] Ready for final polish

---

## Phase 6: Polish

### Task 13: Documentation and Final Polish

**Description:** Write README.md with setup instructions, update .env.example, add deployment notes, perform final manual testing.

**Acceptance Criteria:**
- [ ] README.md includes: project description, setup steps, development commands, testing commands, deployment guide
- [ ] .env.example created (if needed for configuration)
- [ ] Code formatted with black
- [ ] Code linted with ruff (no errors)
- [ ] Type checking with mypy passes
- [ ] All manual test scenarios pass (spec success criteria)
- [ ] SPEC.md marked complete

**Verification:**
- [ ] `black . --check` passes
- [ ] `ruff check .` passes
- [ ] `mypy .` passes
- [ ] Follow README setup steps on fresh clone
- [ ] Complete manual test checklist from SPEC.md

**Dependencies:** Task 12 (all implementation complete)

**Files to Edit:**
- `README.md`
- All code files (formatting)

**Files to Create:**
- `.env.example`

**Estimated Complexity:** Small

---

## Final Checkpoint: Complete
- [ ] All success criteria from SPEC.md met
- [ ] Documentation complete
- [ ] Code quality gates pass
- [ ] Ready for human review and deployment

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| yt-dlp API changes break extraction | High | Pin yt-dlp version in requirements.txt, add error handling |
| Large video files cause memory issues | Medium | Stream directly to response, use temp files, set file cleanup |
| FFmpeg not available on server | High | Add FFmpeg check in health endpoint, document in README |
| Browser blocks sound autoplay | Low | User interaction required before sounds play (already handled) |
| Concurrent download attempts | Medium | Queue with 503 responses (explicitly designed for this) |
| Temp file cleanup fails | Medium | Use try/finally blocks, background cleanup task |

## Parallelization Opportunities

- **Task 9** (sound effects) can be done in parallel with Phase 2-3
- **Task 11-12** (tests) should be sequential (integration tests depend on unit test patterns)
- Frontend and backend work in Phases 2-3 must be sequential (API contract needed first)

## Open Questions

None - all requirements clarified during spec phase.
