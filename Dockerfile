FROM python:3.11-slim

# Install Node.js v22, FFmpeg, git, and curl
RUN apt-get update && \
    apt-get install -y curl gnupg git && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify Node.js installation
RUN node --version && npm --version

WORKDIR /app

# Install bgutil-ytdlp-pot-provider server
RUN git clone --depth 1 --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /opt/bgutil && \
    cd /opt/bgutil/server && \
    npm ci && \
    npx tsc

# Copy production requirements first for better caching
COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p static templates

# Expose ports: 8000 for main app, 4416 for bgutil provider
EXPOSE 8000 4416

# Health check using curl (lighter than requests)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Create startup script that runs both services
# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Run the startup script
CMD ["/app/docker-entrypoint.sh"]
