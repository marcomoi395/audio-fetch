# Spec: User-Provided Cookie Authentication

## Objective

**Problem**: The current implementation relies on environment variables (YOUTUBE_COOKIES, YOUTUBE_COOKIES_FILE) for authentication, which fails in production environments due to bot detection. This creates a deployment barrier and limits the application's usability.

**Solution**: Transition to a user-provided cookie model where users paste their YouTube cookies directly into the web interface. Cookies are stored client-side in the browser (with user consent) and transmitted with each API request.

**Target Users**: Individuals who want to download YouTube audio for personal use and are willing to provide their own YouTube session cookies.

**Success Criteria**:
1. Users can paste Netscape-format cookies into the web interface
2. Cookies persist across browser sessions (with user consent via checkbox)
3. Cookie input is **mandatory** - users must provide cookies before any fetch/download
4. Clear error message shown if user attempts fetch/download without cookies
5. Security warnings are clearly displayed with source code link
6. Environment-based cookie authentication is completely removed
7. All existing tests pass with new cookie-passing mechanism
8. Bot detection no longer occurs in production when valid cookies are provided

## Tech Stack

- **Backend**: Python 3.9+, FastAPI 0.109.0+
- **Frontend**: Vanilla JavaScript (ES6+), NES.css for styling
- **Download Engine**: yt-dlp 2024+
- **Testing**: pytest, pytest-asyncio, pytest-playwright
- **Linting**: ruff, mypy
- **Runtime**: uvicorn (ASGI server)

## Commands

```bash
# Development
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Testing
./run_all_tests.sh                           # Run all tests
pytest tests/ -m "not e2e" -v                # Unit tests only
pytest tests/e2e/ -v                         # E2E tests only
pytest tests/ -m "not e2e" --cov=. --cov-report=html  # With coverage

# Code Quality
ruff format .                                 # Format code
ruff check .                                  # Lint code
ruff check --fix .                           # Auto-fix linting issues
mypy . --ignore-missing-imports              # Type check

# Production
pip install -r requirements-prod.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
audio-fetch/
├── api/
│   ├── __init__.py
│   ├── models.py           # Pydantic request/response models
│   └── routes.py           # FastAPI endpoints
├── services/
│   ├── __init__.py
│   ├── downloader.py       # yt-dlp wrapper with cookie support
│   └── queue.py            # Download queue management
├── static/
│   ├── css/
│   │   └── custom.css
│   ├── js/
│   │   ├── app.js          # Main application logic
│   │   └── audio.js        # Audio playback utilities
│   ├── sounds/
│   └── favicon.png
├── templates/
│   └── index.html          # Main web interface
├── tests/
│   ├── e2e/                # End-to-end tests
│   ├── test_*.py           # Unit and integration tests
│   └── conftest.py         # Test fixtures
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Development dependencies
├── requirements-prod.txt   # Production dependencies
├── pyproject.toml          # Python project configuration
├── .env.example            # Example environment variables
└── SPEC.md                 # This file
```

## Code Style

### Python Style
```python
"""Module-level docstring describing purpose."""

import asyncio
from typing import Any
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel


class VideoInfoRequest(BaseModel):
    """Request model with mandatory cookie support."""
    
    url: str
    cookies: str  # REQUIRED: Netscape-format cookies


async def get_video_info(url: str, cookies: str) -> dict[str, Any]:
    """
    Get video information using yt-dlp.
    
    Args:
        url: YouTube video URL
        cookies: Required Netscape-format cookie string
        
    Returns:
        Dictionary containing video metadata
        
    Raises:
        Exception: If video info extraction fails
    """
    # Implementation here
    pass
```

**Conventions**:
- Use double quotes for strings
- Type hints on all function signatures
- Docstrings for all public functions (Google style)
- f-strings for formatting
- `snake_case` for functions/variables, `PascalCase` for classes
- `|` for union types (Python 3.10+)
- Explicit error messages in exceptions

### JavaScript Style
```javascript
// Cookie management utilities
class CookieManager {
    /**
     * Save cookies to browser storage
     * @param {string} cookies - Netscape format cookie string
     * @param {boolean} persist - Whether to persist across sessions
     */
    static saveCookies(cookies, persist = false) {
        const storage = persist ? localStorage : sessionStorage;
        storage.setItem('youtube_cookies', cookies);
    }
    
    /**
     * Retrieve stored cookies
     * @returns {string|null} Stored cookies or null
     */
    static getCookies() {
        return localStorage.getItem('youtube_cookies') 
            || sessionStorage.getItem('youtube_cookies');
    }
}
```

**Conventions**:
- Use single quotes for strings
- JSDoc comments for functions
- `camelCase` for functions/variables, `PascalCase` for classes
- `const` by default, `let` when reassignment needed
- Arrow functions for callbacks
- Async/await for promises

## Testing Strategy

### Framework
- **pytest** for unit and integration tests
- **pytest-playwright** for E2E browser tests
- **pytest-asyncio** for async test support

### Test Organization
```
tests/
├── test_api.py              # API endpoint tests
├── test_downloader.py       # Downloader service tests with cookie mocking
├── test_integration.py      # Integration tests
├── test_queue.py            # Queue management tests
├── test_health.py           # Health check tests
├── e2e/
│   └── test_cookie_flow.py  # E2E cookie input flow tests
└── conftest.py              # Shared fixtures
```

### Coverage Requirements
- Minimum 80% coverage for business logic
- 100% coverage for cookie handling code (security-critical)
- All API endpoints must have integration tests
- E2E tests for complete cookie input → download workflow

### Test Levels
- **Unit tests**: Individual functions in isolation (cookie parsing, validation)
- **Integration tests**: API endpoints with mocked yt-dlp
- **E2E tests**: Full browser flow with real cookie input UI

### Cookie Testing Strategy
```python
# Mock cookies in tests
@pytest.fixture
def valid_netscape_cookies():
    """Valid Netscape format cookies for testing."""
    return """# Netscape HTTP Cookie File
.youtube.com\tTRUE\t/\tTRUE\t0\tCONSENT\tYES+1
.youtube.com\tTRUE\t/\tFALSE\t1234567890\tSID\tmock_sid_value
"""

# Test cookie parameter passing
async def test_get_video_info_with_cookies(valid_netscape_cookies):
    """Test video info extraction with user-provided cookies."""
    info = await get_video_info(
        url="https://www.youtube.com/watch?v=test",
        cookies=valid_netscape_cookies
    )
    assert info["title"]
    assert info["duration"] > 0
```

## Architecture Changes

### 1. Backend Changes

#### API Models (`api/models.py`)
```python
class VideoInfoRequest(BaseModel):
    """Request model for video info endpoint."""
    url: HttpUrl
    cookies: str  # REQUIRED: Netscape-format cookies

class DownloadRequest(BaseModel):
    """Request model for download endpoint."""
    url: HttpUrl
    format: str
    quality: str
    cookies: str  # REQUIRED: Netscape-format cookies
#### Downloader Service (`services/downloader.py`)
- **Modify**: `youtube_cookies_context()` - accept `cookies: str` parameter (required, not optional)
- **Remove**: Environment variable reading (YOUTUBE_COOKIES, YOUTUBE_COOKIES_FILE) from context manager
- **Remove**: Android client fallback logic (cookies always provided)
- **Modify**: `get_video_info()` - change `cookies: str | None` to `cookies: str` (required parameter)
- **Modify**: `download_audio()` - change `cookies: str | None` to `cookies: str` (required parameter)
- **Keep**: `_clean_cookie_content()` - still needed for Netscape format cleaning
- **Keep**: Context manager pattern with try/finally for guaranteed temp file cleanup
- **Clean up**: Remove duplicate code at lines 248-255 (dead code after return statement)
**New signature**:
**Modified context manager signature**:
def youtube_cookies_context(cookies: str) -> Generator[str, None, None]:
    """
    Context manager that yields the path to a YouTube cookies temp file.
    
    Args:
        cookies: Required Netscape-format cookie string from user
        
    Yields:
        Path to temporary cookie file
    """
    # Clean and write to temp file (cookies always provided)
    cleaned_cookies = _clean_cookie_content(cookies)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(cleaned_cookies)
        yield temp_path
    finally:
        try:
            os.unlink(temp_path)
        except OSError as e:
            logger.error(f"Failed to delete temp cookie file {temp_path}: {e}")


async def get_video_info(url: str, cookies: str) -> dict[str, Any]:
    """Get video information with required user-provided cookies."""
    with youtube_cookies_context(cookies) as cookie_path:
        ydl_opts: dict[str, Any] = {
            "quiet": False,
            "verbose": True,
            # ... other options
        }
        
        logger.info(f"Using user-provided cookies with web client")
        ydl_opts["cookiefile"] = cookie_path
        ydl_opts["extractor_args"] = {
            "youtube": {"player_client": ["web"]}
        }
        
        return await asyncio.to_thread(_extract_info_sync, url, ydl_opts)
```
```python
@router.post("/video-info", response_model=VideoInfoResponse)
async def fetch_video_info(request: VideoInfoRequest):
    """Fetch video info with required user cookies."""
    try:
        info = await get_video_info(
            url=str(request.url),
            cookies=request.cookies  # REQUIRED: Pass cookies from request
        return VideoInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.post("/download")
async def download_audio_endpoint(request: DownloadRequest):
    """Download audio with required user cookies."""
    # Pass required cookies to download_audio()
```

### 2. Frontend Changes

#### Cookie Management Module (`static/js/cookies.js` - NEW FILE)
```javascript
/**
 * Cookie management utilities for YouTube authentication
 */
class CookieManager {
    static STORAGE_KEY = 'youtube_cookies';
    
    /**
     * Validate Netscape cookie format
     */
    static isValidNetscapeFormat(cookieText) {
        // Basic validation: check for required headers and structure
        const lines = cookieText.trim().split('\n');
        return lines.some(line => 
            line.includes('.youtube.com') || 
            line.includes('# Netscape HTTP Cookie File')
        );
    }
    
    /**
     * Save cookies to storage
     */
    static save(cookies, persist = false) {
        const storage = persist ? localStorage : sessionStorage;
        storage.setItem(this.STORAGE_KEY, cookies);
    }
    
    /**
     * Retrieve cookies from storage
     */
    static get() {
        return localStorage.getItem(this.STORAGE_KEY) 
            || sessionStorage.getItem(this.STORAGE_KEY);
    }
    
    /**
     * Clear stored cookies
     */
    static clear() {
        localStorage.removeItem(this.STORAGE_KEY);
        sessionStorage.removeItem(this.STORAGE_KEY);
    }
    
    /**
     * Check if cookies are currently stored
     */
    static hasStored() {
        return this.get() !== null;
    }
}
```

#### Main Application (`static/js/app.js`)
- **Modify**: `fetchVideoInfo()` - validate cookies exist before request, include cookies in request body
- **Modify**: `downloadAudio()` - validate cookies exist before request, include cookies in request body
- **Add**: Cookie input section show/hide handlers
- **Add**: Cookie save/clear handlers
- **Add**: Security warning dialog handlers
- **Add**: Button disable/enable logic based on cookie presence
- **Modify**: Error handling to show clear message when cookies missing

#### HTML Template (`templates/index.html`)
**New sections to add**:
1. **Cookie Input Section** (expanded by default with "Required" label, after URL input):
```html
<section id="cookie-section" class="nes-container with-title" style="margin-top: 20px;">
    <p class="title">🍪 YouTube Cookies (Required)</p>
    
    <div class="cookie-help">
        <p><strong>⚠️ Cookies are required to avoid bot detection.</strong> You must provide your YouTube cookies before fetching or downloading.</p>
        <button type="button" class="nes-btn is-primary" id="show-cookie-input">
            <i class="nes-icon cookie"></i> Add Cookies
        </button>
        <button type="button" class="nes-btn is-warning" id="show-cookie-guide" style="display:none;">
            <i class="nes-icon question"></i> How to get cookies?
        </button>
    </div>
    
    <div id="cookie-input-container" style="display: none; margin-top: 15px;">
        <div class="nes-field">
            <label for="cookie-text">Paste Netscape format cookies:</label>
            <textarea 
                id="cookie-text" 
                class="nes-textarea" 
                rows="8"
                placeholder="# Netscape HTTP Cookie File&#10;.youtube.com	TRUE	/	TRUE	0	CONSENT	YES+1&#10;.youtube.com	TRUE	/	FALSE	1234567890	SID	..."
            ></textarea>
        </div>
        
        <div class="nes-field">
            <label>
                <input type="checkbox" class="nes-checkbox" id="persist-cookies" />
                <span>Remember cookies for next visit</span>
            </label>
        </div>
        
        <div style="margin-top: 10px;">
            <button type="button" class="nes-btn is-success" id="save-cookies-btn">Save Cookies</button>
            <button type="button" class="nes-btn is-error" id="clear-cookies-btn">Clear Cookies</button>
            <button type="button" class="nes-btn" id="cancel-cookies-btn">Cancel</button>
        </div>
        
        <p id="cookie-status" style="margin-top: 10px; display: none;"></p>
    </div>
</section>
```

2. **Security Warning Dialog** (modal, shown on first cookie save):
```html
<dialog class="nes-dialog" id="security-warning-dialog">
    <form method="dialog">
        <p class="title">⚠️ Security Notice</p>
        <div class="security-content">
            <p><strong>Important information about cookies:</strong></p>
            <ul style="text-align: left; margin-left: 20px;">
                <li>Cookies contain authentication tokens for your YouTube account</li>
                <li>Only use cookies from your own account</li>
                <li>Cookies are stored locally in your browser</li>
                <li>When you fetch or download, cookies are sent to our server in the request</li>
                <li>Our server writes cookies to a temporary file on disk for yt-dlp to use</li>
                <li>The temporary file is deleted immediately after the request completes</li>
                <li>Cookies may appear transiently in server logs during request processing</li>
                <li>We do not store cookies in any database or permanent storage</li>
            </ul>
            <p style="margin-top: 15px;">
                <strong>Transparency:</strong><br>
                This is open source software. You can review how cookies are handled:
                <a href="https://github.com/marcomoi395/audio-fetch" target="_blank">View Source Code</a>
            </p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                📖 <a href="https://github.com/marcomoi395/audio-fetch/wiki/Cookie-Export-Guide" target="_blank">
                    How to export cookies safely
                </a>
            </p>
        </div>
        <menu class="dialog-menu">
            <button class="nes-btn is-primary" id="accept-security-warning">I Understand</button>
        </menu>
    </form>
</dialog>
```

3. **Cookie Status Indicator** (in header, shows if cookies are active):
```html
<div id="cookie-status-indicator" style="display: none;">
    <span class="nes-badge">
        <span class="is-success">🍪 Cookies Active</span>
    </span>
</div>
```

4. **Footer Update** (add GitHub link):
```html
<footer class="footer">
    <p>
        ✨ From youngmarco with love 💙 ✨ | 
        <a href="https://github.com/marcomoi395/audio-fetch" target="_blank" class="github-link">
            <i class="nes-icon github"></i> Source Code
        </a>
    </p>
</footer>
```

### 3. Environment Variables

**Remove completely**:
- `YOUTUBE_COOKIES` - Raw cookie content
- `YOUTUBE_COOKIES_FILE` - Path to cookie file

**Keep**:
- `CORS_ORIGINS` - CORS configuration
- `PORT` - Server port (for deployment)

Update `.env.example`:
```bash
# CORS Configuration
CORS_ORIGINS=*

# Server Configuration (optional, defaults to 8000)
# PORT=8000

# REMOVED: YOUTUBE_COOKIES and YOUTUBE_COOKIES_FILE
# Users now provide cookies through the web interface
```

## User Workflows

### Workflow 1: New User Without Cookies (Blocked)
1. User lands on homepage
2. Sees URL input and required cookie section (expanded by default)
3. Enters YouTube URL and clicks "Fetch Info" **without adding cookies**
4. **Error message displayed**: "❌ Cookies are required. Please add your YouTube cookies to continue."
5. Fetch/download buttons disabled until cookies are provided
6. Cookie section highlighted with warning

### Workflow 2: New User Adding Required Cookies
1. User lands on homepage
2. Cookie section is expanded by default with "Required" label
3. Clicks "Add Cookies" button
4. Security warning dialog appears
5. After accepting, cookie input form expands
6. User pastes Netscape cookies
7. Checks "Remember cookies for next visit" (optional)
8. Clicks "Save Cookies"
9. Success message: "✅ Cookies saved successfully"
10. Cookie status indicator shows "🍪 Cookies Active"
11. Fetch/download buttons now enabled
12. Proceeds with normal URL fetch

### Workflow 3: Returning User With Stored Cookies
1. User lands on homepage
2. Cookie status indicator automatically shows "🍪 Cookies Active"
3. User enters URL and fetches info
4. Cookies automatically included in API requests
5. No additional cookie input needed

### Workflow 4: Updating/Clearing Cookies
1. User clicks "Add Cookies" button (or cookie status indicator)
2. Cookie input section expands
3. Can paste new cookies or click "Clear Cookies"
4. Changes take effect immediately

## Security Considerations

### Client-Side Security
- **localStorage vs sessionStorage**: User chooses persistence duration
- **No encryption**: Cookies stored in plain text (browser security model)
- **XSS protection**: No eval() or innerHTML with user input
- **HTTPS**: Strongly recommended for production (cookie transmission)

### Server-Side Security
- **Temporary file lifecycle**: Cookies written to temp file on disk during request, deleted in finally block after yt-dlp execution
- **Context manager pattern**: `youtube_cookies_context()` ensures cleanup even on exceptions
- **No persistent storage**: Cookies never saved to database or permanent disk storage
- **Log exposure**: Cookies may appear transiently in server logs if verbose logging enabled
- **Request validation**: Pydantic models validate cookie format before processing
- **Error messages**: Don't leak sensitive cookie content in error responses

### Disclaimer Language
⚠️ Security Notice

Cookies contain authentication tokens for your YouTube account.
- Only use cookies from your own account
- Cookies are stored locally in your browser
- When you fetch or download, cookies are sent to our server in the request
- Our server writes cookies to a temporary file on disk for yt-dlp to use
- The temporary file is deleted immediately after the request completes
- Cookies may appear transiently in server logs during request processing
- We do not store cookies in any database or permanent storage

This is open source software. Review the code:
https://github.com/marcomoi395/audio-fetch

Use at your own risk. We are not responsible for any misuse of this tool.
```

## Migration Path

### For Existing Users (Self-Hosted)
1. Update application code
2. Remove YOUTUBE_COOKIES/YOUTUBE_COOKIES_FILE from environment
3. On first visit, follow "New User With Cookies" workflow
4. Cookies now managed through web interface

### For Developers
1. Update `.env` file - remove cookie-related variables
2. Run tests to verify cookie parameter passing works
3. Test E2E flow with real cookies

## Success Criteria (Testable)

### Functional Requirements
- [ ] Cookie input form accepts Netscape format cookies
- [ ] Cookies can be saved with persist checkbox (localStorage)
- [ ] Cookies can be saved without persist (sessionStorage)
- [ ] Cookies are REQUIRED in all `/api/video-info` POST requests
- [ ] Cookies are REQUIRED in all `/api/download` POST requests
- [ ] Cookie status indicator shows when cookies are active
- [ ] Security warning dialog appears on first cookie save
- [ ] Clear cookies button removes stored cookies
- [ ] Fetch/download buttons disabled until cookies are provided

### Technical Requirements
- [ ] `get_video_info()` accepts required `cookies` parameter
- [ ] `download_audio()` accepts required `cookies` parameter
- [ ] `youtube_cookies_context()` accepts required `cookies` parameter
- [ ] Environment variable cookie loading removed
- [ ] All existing unit tests pass with new signature
- [ ] New tests added for cookie parameter passing
- [ ] E2E test covers complete cookie input → download flow

### Security Requirements
- [ ] Security warning displayed before first cookie save
- [ ] GitHub source code link visible in footer
- [ ] Cookie export guide link included in warning dialog
- [ ] Cookies never logged in server logs
- [ ] Temp cookie files cleaned up after use

### UX Requirements
- [ ] Cookie input is **mandatory** (users must provide cookies before fetch/download)
- [ ] Cookie section visible/expanded by default with "Required" label
- [ ] Clear error message when attempting operations without cookies
- [ ] Cookie status clearly visible when active
- [ ] Cookie management accessible at all times
- [ ] Fetch/download buttons disabled until cookies are provided

## Boundaries

### Always Do
- Include cookies in ALL API requests (required, not optional)
- Clean up temporary cookie files after yt-dlp execution
- Show security warning before accepting first cookie input
- Validate cookie format before sending to backend
- Run all tests before committing changes
- Update documentation to reflect new cookie flow

### Ask First
- Changing cookie storage mechanism (e.g., switching to encrypted storage)
- Adding server-side cookie persistence
- Modifying security warning content
- Adding additional authentication methods
- Changing cookie format requirements

### Never Do
- Store cookies in server database or permanent files
- Log cookie content to server logs
- Send cookies to third-party services
- Accept cookies without showing security warning
- Allow fetch/download operations without cookies
- Deploy without HTTPS in production

## Open Questions

1. **Cookie expiration handling**: Should we detect when cookies expire and prompt for refresh?
   - Current approach: User must manually refresh when cookies expire
   - Could add: Detect 401/403 errors and auto-prompt

2. **Cookie validation**: How strict should client-side validation be?
   - Current approach: Basic format check (contains .youtube.com)
   - Could add: Parse full Netscape format, validate required fields

3. **Multi-account support**: Should users be able to save multiple cookie sets?
   - Current approach: Single cookie set per browser
   - Could add: Named cookie profiles with dropdown selector

4. **Cookie export guide**: Where should we host the detailed cookie export guide?
   - Option A: GitHub wiki (github.com/marcomoi395/audio-fetch/wiki)
   - Option B: Separate docs page in repository
   - Option C: External link to general guide

**Decision**: These can be addressed in future iterations. For MVP, proceed with current approach listed above.

## Documentation Updates Required

- [ ] Update README.md - remove environment cookie instructions
- [ ] Update README.md - add user cookie workflow section
- [ ] Remove docs/YOUTUBE_COOKIES.md (no longer relevant)
- [ ] Create docs/USER_COOKIE_GUIDE.md - how to export cookies
- [ ] Update .env.example - remove YOUTUBE_COOKIES variables
- [ ] Add cookie management section to main documentation

## Timeline Estimate

- **Backend changes**: 2-3 hours (API models, downloader service, routes)
- **Frontend changes**: 3-4 hours (cookie manager, UI components, styling)
- **Testing**: 2-3 hours (unit tests, integration tests, E2E tests)
- **Documentation**: 1-2 hours (README, guides, comments)
- **Testing & debugging**: 2-3 hours (manual testing, bug fixes)

**Total**: ~10-15 hours of development time

---

**Spec Version**: 1.0  
**Created**: 2026-07-30  
**Status**: Ready for Review
