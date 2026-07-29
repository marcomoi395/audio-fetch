# Audio-Fetch Web App - Task List

## Phase 1: Foundation

- [ ] **Task 1:** Project Setup and Dependencies
  - Create directory structure
  - Write requirements.txt
  - Set up virtual environment
  - Verify FFmpeg availability
  - **Files:** requirements.txt, all __init__.py files, empty module files

- [ ] **Task 2:** FastAPI App with Health Endpoint
  - Create main.py with FastAPI app
  - Configure CORS, static files, templates
  - Implement /health endpoint
  - **Files:** main.py

**Checkpoint:** Server runs and health endpoint responds

---

## Phase 2: Video Info Flow

- [ ] **Task 3:** Downloader Service - Video Info Extraction
  - Adapt AudioDownloader from audio_downloader.py
  - Implement get_video_info() async function
  - Extract metadata using yt-dlp (download=False)
  - **Files:** services/downloader.py

- [ ] **Task 4:** Video Info API Endpoint
  - Create Pydantic models (VideoInfoRequest, VideoInfoResponse)
  - Implement POST /api/video-info endpoint
  - Return 200 on success, 400 on error with details
  - **Files:** api/models.py, api/routes.py, main.py

- [ ] **Task 5:** Frontend - Video Info UI
  - Create index.html with NES.css
  - Build URL input form and fetch button
  - Display video metadata (thumbnail, title, uploader, duration)
  - Implement fetchVideoInfo() in app.js
  - Add 8-bit loading spinner
  - **Files:** templates/index.html, static/js/app.js, static/css/custom.css, main.py

**Checkpoint:** User can paste URL and see video metadata

---

## Phase 3: Download Flow

- [ ] **Task 6:** Download Queue Service
  - Implement DownloadQueue with asyncio.Lock
  - Prevent concurrent downloads (return 503 if busy)
  - Ensure lock release in finally block
  - **Files:** services/queue.py

- [ ] **Task 7:** Download API Endpoint
  - Create DownloadRequest Pydantic model
  - Implement POST /api/download endpoint
  - Download to temp directory, stream with FileResponse
  - Background cleanup of temp files
  - Return 503 if queue busy, 400 on error
  - **Files:** api/models.py, api/routes.py, services/downloader.py

- [ ] **Task 8:** Frontend - Download UI
  - Add format/quality dropdown selectors
  - Implement download button with loading states
  - Implement downloadAudio() in app.js
  - Handle browser download trigger
  - Show success/error messages
  - **Files:** templates/index.html, static/js/app.js, static/css/custom.css

**Checkpoint:** End-to-end download flow works, queue prevents concurrency

---

## Phase 4: 8-bit Theme

- [ ] **Task 9:** Source and Integrate 8-bit Sounds
  - Find 5 free 8-bit sound effects (click, fetch, download, success, error)
  - Add sounds to static/sounds/
  - Implement SoundManager in audio.js
  - Preload sounds on page load
  - **Files:** static/sounds/*.mp3, static/js/audio.js

- [ ] **Task 10:** NES.css Theme Implementation
  - Apply NES.css white mode theme
  - Add 8-bit visual elements (header, pixel art)
  - Wire sound effects to UI interactions
  - Responsive layout for mobile/desktop
  - **Files:** templates/index.html, static/css/custom.css, static/js/app.js

**Checkpoint:** Full 8-bit aesthetic with sound effects on all interactions

---

## Phase 5: Testing

- [ ] **Task 11:** Unit Tests for Services
  - Write test_downloader.py (get_video_info, download methods)
  - Write test_queue.py (single download, concurrent blocking)
  - Create fixtures for mocked yt-dlp responses
  - Achieve ≥90% coverage for services/
  - **Files:** tests/test_downloader.py, tests/test_queue.py, tests/fixtures.py

- [ ] **Task 12:** Integration Tests for API
  - Write test_api.py (test all endpoints)
  - Use FastAPI TestClient with mocked services
  - Test success and error cases (200, 400, 503)
  - Achieve ≥80% overall coverage
  - **Files:** tests/test_api.py

**Checkpoint:** All tests pass, coverage goals met

---

## Phase 6: Polish

- [ ] **Task 13:** Documentation and Final Polish
  - Write comprehensive README.md
  - Create .env.example
  - Run black, ruff, mypy
  - Complete manual test checklist
  - Verify all SPEC.md success criteria
  - **Files:** README.md, .env.example, all code files (formatting)

**Final Checkpoint:** Ready for human review and deployment

---

## Quick Reference

**Total Tasks:** 13  
**Estimated Timeline:** 3-4 focused sessions  
**Critical Path:** Tasks 1→2→3→4→5→7→8 (video info + download flow)  
**Can Parallelize:** Task 9 (sounds) with Phase 2-3

**Run Commands:**
```bash
# Development
uvicorn main:app --reload

# Testing
pytest tests/ --cov=. --cov-report=term-missing

# Quality
black . && ruff check . && mypy .
```
