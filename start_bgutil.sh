#!/usr/bin/env bash
# Start bgutil PO Token provider server for local development

set -e

BGUTIL_DIR="$HOME/bgutil-ytdlp-pot-provider"
BGUTIL_VERSION="1.3.1"

echo "🔐 BgUtil PO Token Provider Setup"
echo "=================================="
echo ""

# Check if bgutil is already installed
if [ ! -d "$BGUTIL_DIR" ]; then
    echo "📦 Installing bgutil-ytdlp-pot-provider..."
    echo "   This is a one-time setup."
    echo ""
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is required but not installed"
        echo "   Install Node.js 20+ from https://nodejs.org/"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION found"
    
    # Clone and setup
    git clone --depth 1 --branch "$BGUTIL_VERSION" \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        "$BGUTIL_DIR"
    
    cd "$BGUTIL_DIR/server"
    npm ci
    npx tsc
    
    echo ""
    echo "✅ bgutil installed successfully"
else
    echo "✅ bgutil already installed at $BGUTIL_DIR"
fi

echo ""
echo "🚀 Starting bgutil HTTP server on port 4416..."
echo "   This server generates PO Tokens to bypass YouTube bot detection"
echo "   Press Ctrl+C to stop"
echo ""

cd "$BGUTIL_DIR/server"
node build/main.js --port 4416
