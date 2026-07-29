#!/bin/bash
# Script khởi động nhanh cho Audio Downloader

# Màu sắc cho output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "================================================"
echo "  🎵 YouTube Audio Downloader - Quick Start"
echo "================================================"
echo -e "${NC}"

# Kiểm tra virtual environment
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment chưa được tạo!${NC}"
    echo "Đang tạo virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Đã tạo virtual environment${NC}"
fi

# Kiểm tra dependencies
if ! ./venv/bin/python -c "import yt_dlp" 2>/dev/null; then
    echo -e "${BLUE}📦 Đang cài đặt dependencies...${NC}"
    ./venv/bin/pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Đã cài đặt dependencies${NC}"
fi

# Kiểm tra FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}⚠️  CẢNH BÁO: FFmpeg chưa được cài đặt!${NC}"
    echo "FFmpeg cần thiết để convert audio và embed thumbnail."
    echo ""
    echo "Cài đặt FFmpeg:"
    echo "  - Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  - Arch Linux:    sudo pacman -S ffmpeg"
    echo "  - macOS:         brew install ffmpeg"
    echo ""
    read -p "Bạn có muốn tiếp tục không? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ FFmpeg đã được cài đặt${NC}"
fi

echo ""
echo -e "${BLUE}🚀 Khởi động Audio Downloader...${NC}"
echo ""

# Chạy script với tất cả arguments được truyền vào
./venv/bin/python audio_downloader.py "$@"
