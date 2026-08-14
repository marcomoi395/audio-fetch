#!/bin/bash
# Post-install script for audio-fetch .deb package
# Runs after package installation

set -e

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications || true
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

echo "Audio Fetch installed successfully!"
echo ""
echo "Note: FFmpeg is required for audio conversion."
echo "Install it with: sudo apt install ffmpeg"
echo ""
echo "Run 'audio-fetch' to start the application."

exit 0
