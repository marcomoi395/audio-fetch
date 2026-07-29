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

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Lint code
ruff check .
```

## Deployment

For production deployment:

```bash
# Install production dependencies only
pip install fastapi uvicorn[standard] yt-dlp aiofiles jinja2

# Run with production settings
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Requirements:**
- Ensure FFmpeg is installed on the server
- Configure CORS origins in `main.py` for production
- Use a reverse proxy (nginx/caddy) for HTTPS

## License

This project is licensed under the MIT License - see the LICENSE file for details.
