"""FastAPI application for audio-fetch web app."""

import os
import shutil
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.routes import router as api_router

app = FastAPI(
    title="Audio Fetch",
    description="8-bit themed YouTube audio downloader",
    version="1.0.0",
)

# CORS configuration - configurable via environment variable
cors_origins = os.getenv("CORS_ORIGINS", "*")
allowed_origins = cors_origins.split(",") if cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Templates
templates_path = Path(__file__).parent / "templates"
templates_path.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_path))

# Register API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root(request: Request):
    """
    Serve the main application page.

    Args:
        request: FastAPI request object

    Returns:
        TemplateResponse rendering index.html
    """
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status information including FFmpeg availability and queue status
    """
    from api.routes import download_queue

    # Check if FFmpeg is available
    ffmpeg_available = shutil.which("ffmpeg") is not None

    return {
        "status": "ok",
        "ffmpeg_available": ffmpeg_available,
        "queue_active": download_queue.is_active(),
    }
