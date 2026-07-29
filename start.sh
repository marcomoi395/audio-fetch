#!/usr/bin/env bash
# Quick start script for local development

set -e

echo "🚀 Audio Fetch - Quick Start"
echo "=============================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION found"

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    echo "✅ FFmpeg $FFMPEG_VERSION found"
else
    echo "⚠️  FFmpeg not found - MP3/OPUS/WAV conversion will not work"
    echo "   Install: sudo apt install ffmpeg (Ubuntu/Debian)"
    echo "   Or: brew install ffmpeg (macOS)"
fi

echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🔧 Creating required directories..."
mkdir -p static templates

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting development server..."
echo "   Access at: http://localhost:8000"
echo "   Health check: http://localhost:8000/health"
echo "   Press Ctrl+C to stop"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
