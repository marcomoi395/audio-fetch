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

## Running

```bash
# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the app at `http://localhost:8000`

## Development

### Git Hooks

This project uses git hooks to ensure code quality:

- **pre-commit**: Auto-formats code with `ruff` and `black` before each commit
- **pre-push**: Runs tests and validates formatting before pushing

Hooks are automatically active in `.git/hooks/`. See [docs/GIT_HOOKS.md](docs/GIT_HOOKS.md) for details.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_download.py -v
```

### Code Quality

```bash
# Format code
ruff format .
black .

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
