FROM python:3.11-slim

# Install Node.js v22, FFmpeg, and curl
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify Node.js installation
RUN node --version && npm --version

WORKDIR /app

# Copy production requirements first for better caching
COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p static templates

# Expose port (default 8000, overridable via PORT env)
EXPOSE 8000

# Health check using curl (lighter than requests)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application (use PORT env var from Render)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
