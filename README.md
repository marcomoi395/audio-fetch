# Audio Fetch

A simple YouTube audio downloader with an 8-bit themed web interface.

## Prerequisites

- Python 3.9+
- FFmpeg (for audio conversion)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd audio-fetch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## YouTube Authentication (Cookies)

This application **strictly requires** YouTube cookies to bypass bot detection and download audio successfully.

See [docs/YOUTUBE_COOKIES.md](docs/YOUTUBE_COOKIES.md) for step-by-step instructions on how to extract and configure your cookies.

## Running

```bash
# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the app at `http://localhost:8000`

## Development

### Git Hooks

This project uses git hooks to ensure code quality:

- **pre-commit**: Auto-formats code with `ruff` before each commit
- **pre-push**: Runs tests and validates formatting before pushing

Hooks are automatically active in `.git/hooks/`. See [docs/GIT_HOOKS.md](docs/GIT_HOOKS.md) for details.

### Running Tests

Due to event loop conflicts between `pytest-asyncio` and `pytest-playwright`, tests must be run separately:

```bash
# Run all tests (recommended)
./run_all_tests.sh

# Or run separately:
# Unit tests only
pytest tests/ -m "not e2e" -v

# E2E tests only  
pytest tests/e2e/ -v

# With coverage
pytest tests/ -m "not e2e" --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Type check
mypy . --ignore-missing-imports
```

## Deployment

### Quick Deploy to Render

**Recommended: Docker Deployment (with FFmpeg support)**

1. Push code to GitHub
2. Create new Web Service on [Render](https://dashboard.render.com/)
3. Select **Docker** as environment
4. Set environment variable: `PORT=8000`
5. Deploy!

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed instructions.

### Local Production Mode

```bash
# Install production dependencies only
pip install -r requirements-prod.txt

# Run with production settings
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Production Requirements:**
- FFmpeg installed on server (for MP3/OPUS/WAV conversion)
- Configure CORS via `CORS_ORIGINS` environment variable
- Use reverse proxy (nginx/caddy) for HTTPS in self-hosted setups

**Format Support Without FFmpeg:**
- ✅ m4a (native YouTube format)
- ✅ best (no conversion needed)
- ❌ mp3, opus, wav (requires FFmpeg)

For complete deployment guide including Docker setup, see [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
