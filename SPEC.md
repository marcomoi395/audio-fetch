# Specification: YouTube Cookie Support

## Objective
Enable downloading of YouTube audio for videos that require authentication (to bypass "Sign in to confirm you're not a bot" errors). 
This will be achieved by providing YouTube cookies to `yt-dlp`. 
- The application runs in Docker, so browser-based cookie extraction (`--cookies-from-browser`) is out of scope.
- Cookies will be configured system-wide by the administrator, not uploaded per-user via the web UI.
- The cookie strategy will become the **primary and only** bypass mechanism, replacing all existing client-spoofing strategies (android, ios, mweb, tv_embedded).

## Tech Stack
- Python 3.9+
- FastAPI
- `yt-dlp` (Core downloader)
- Docker / Render (Deployment environment)

## Commands
### Development
```bash
# Run tests
pytest tests/ -v

# Format and lint
ruff format . && ruff check .
```
### User Workflow (Examples)
```bash
# Application boots successfully regardless of cookies
uvicorn main:app

# But downloading requires cookies. Test a download request via API:
curl -X POST "http://localhost:8000/api/download" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=BIbgncfLpl0"}'
# -> FAILS with 400 Bad Request if YOUTUBE_COOKIES env var is not set.
```

## Project Structure
Modifications will primarily occur in:
```text
services/downloader.py  → Core download logic and cookie injection
tests/                  → Unit and integration tests
.env.example            → Environment variable documentation
```

## Code Style
- Use Context Managers for temporary file handling to ensure safe cleanup.
- Use explicit type hints.
- Fail fast if cookies are missing when attempting to download (cookies are strictly required).

*Example pattern for temporary file handling:*
```python
@contextlib.contextmanager
def get_cookie_path(
    cookie_string: str | None = None, file_path: str | None = None
) -> Generator[str | None, None, None]:
    if file_path and os.path.exists(file_path):
        yield file_path
        return

    if cookie_string:
        fd, temp_path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(cookie_string)
            yield temp_path
        finally:
            os.unlink(temp_path)
    else:
        yield None
```

## Testing Strategy
- **Unit Tests:** Verify the context manager creates, yields, and deletes temporary files correctly. Verify `yt-dlp` options receive the `cookiefile` argument.
- **Integration Tests:** Verify `get_video_info` and `download_audio` successfully utilize the cookie context manager.
- **Coverage:** Maintain > 80% coverage in `services/downloader.py`.

## Boundaries
- **Always do:** 
  - Automatically and securely clean up any temporary files containing cookies.
  - Throw an explicit error if cookies are missing (no silent fallback).
- **Ask first:** 
  - Before adding any new pip dependencies (should not be needed for this feature).
- **Never do:** 
  - Never log the actual content of the cookies.
  - Never retain temporary cookie files after the `yt-dlp` process finishes.
  - Never attempt to download or fetch info without providing a cookiefile to `yt-dlp`.

## Success Criteria
1. The application can accept cookies via `YOUTUBE_COOKIES` (raw string) or `YOUTUBE_COOKIES_FILE` (file path) environment variables.
2. The legacy `BYPASS_CONFIGS` array, client-spoofing logic, and retry loops are completely removed.
3. The application explicitly requires cookies; requests fail cleanly if cookies are not provided.
4. `yt-dlp` receives the `cookiefile` parameter containing the provided cookies for all requests.
5. Temporary files created for raw string cookies are guaranteed to be deleted immediately after `yt-dlp` execution completes.
6. All tests pass and the application runs successfully in a Docker-like environment.

