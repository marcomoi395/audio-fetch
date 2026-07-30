#!/bin/bash
# Test PO Token integration locally

set -e

echo "🧪 Testing PO Token Integration"
echo "================================"
echo ""

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "🔐 Next steps:"
echo "1. Start bgutil server (Terminal 1):"
echo "   ./start_bgutil.sh"
echo ""
echo "2. Start main app (Terminal 2):"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. Test at http://localhost:8000"
echo ""
