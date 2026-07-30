#!/bin/bash
set -e

echo "=========================================="
echo "🚀 Audio Fetch - Starting Services"
echo "=========================================="
echo ""

# Start bgutil PO Token provider in background
echo "🔐 Starting bgutil PO Token provider..."
cd /opt/bgutil/server
node build/main.js --port 4416 &
BGUTIL_PID=$!

echo "   ✅ bgutil provider started (PID: $BGUTIL_PID)"
echo ""

# Wait for bgutil to be ready
echo "⏳ Waiting for bgutil server to be ready..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:4416/ > /dev/null 2>&1; then
        echo "   ✅ bgutil server is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ⚠️  bgutil server not responding, continuing anyway..."
    fi
    sleep 1
done

echo ""
echo "🌐 Starting main FastAPI application..."
cd /app

# Start uvicorn in foreground (so container stays alive)
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
