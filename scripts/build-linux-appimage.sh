#!/usr/bin/env bash
# Build script for Audio Fetch AppImage (Linux)
# Purpose: Create a portable AppImage for Linux systems
#
# Requirements:
# - Python 3.10+ with venv
# - PyInstaller
# - wget or curl (for downloading appimagetool)
# - FFmpeg (runtime dependency, not bundled)
#
# Usage:
#   ./build-linux-appimage.sh <version>
#
# Arguments:
#   version: Version number (e.g., "0.1.0" or "v0.1.0")
#
# Output:
#   dist/audio-fetch-v{version}-x86_64.AppImage

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Usage information
usage() {
    cat << EOF
Usage: $0 <version>

Arguments:
  version   Version number (e.g., "0.1.0" or "v0.1.0")

Example:
  $0 0.1.0

Description:
  Builds an AppImage for Audio Fetch with the specified version.
  Output: dist/audio-fetch-v{version}-x86_64.AppImage
EOF
}

# Validate arguments
if [[ $# -ne 1 ]]; then
    log_error "Invalid number of arguments"
    usage
    exit 1
fi

APP_VERSION="$1"

# Strip 'v' prefix if present for internal use
VERSION_NUMBER="${APP_VERSION#v}"

# Validate version format
if ! [[ "$VERSION_NUMBER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    log_error "Invalid version format: '$APP_VERSION'"
    log_error "Expected format: X.Y.Z (e.g., 0.1.0)"
    exit 1
fi

# Configuration
APP_NAME="audio-fetch"
APP_DISPLAY_NAME="Audio Fetch"
PYTHON_VERSION="3.10"
ARCH="x86_64"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build-appimage"
APPDIR="${BUILD_DIR}/AppDir"
DIST_DIR="${PROJECT_ROOT}/dist"

# Tools
APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
APPIMAGETOOL="${BUILD_DIR}/appimagetool-${ARCH}.AppImage"

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Found Python ${PYTHON_VER}"
    
    # Check for wget or curl
    if ! command -v wget &> /dev/null && ! command -v curl &> /dev/null; then
        log_error "Neither wget nor curl is installed. Please install one of them."
        exit 1
    fi
    
    # Warn about FFmpeg (runtime dependency)
    if ! command -v ffmpeg &> /dev/null; then
        log_warn "FFmpeg is not installed. The app will run but audio conversion will be limited."
        log_warn "Install FFmpeg: sudo apt install ffmpeg (Debian/Ubuntu) or sudo pacman -S ffmpeg (Arch)"
    fi
}

setup_build_env() {
    log_info "Setting up build environment..."
    
    # Create build directories
    mkdir -p "${BUILD_DIR}"
    mkdir -p "${APPDIR}"
    mkdir -p "${DIST_DIR}"
    
    # Clean previous AppDir
    if [ -d "${APPDIR}/usr" ]; then
        log_info "Cleaning previous AppDir..."
        rm -rf "${APPDIR}/usr"
    fi
}

download_appimagetool() {
    if [ -f "${APPIMAGETOOL}" ]; then
        log_info "appimagetool already downloaded"
        return
    fi
    
    log_info "Downloading appimagetool..."
    
    if command -v wget &> /dev/null; then
        wget -q --show-progress "${APPIMAGETOOL_URL}" -O "${APPIMAGETOOL}"
    else
        curl -L "${APPIMAGETOOL_URL}" -o "${APPIMAGETOOL}"
    fi
    
    chmod +x "${APPIMAGETOOL}"
    log_info "appimagetool downloaded successfully"
}

build_with_pyinstaller() {
    log_info "Building with PyInstaller..."
    
    cd "${PROJECT_ROOT}"
    
    # Activate virtual environment if it exists
    # In CI environments (like GitHub Actions), dependencies may be installed globally
    if [ -d "${PROJECT_ROOT}/.venv" ]; then
        log_info "Using existing virtual environment (.venv)..."
        source "${PROJECT_ROOT}/.venv/bin/activate"
    elif [ -d "${PROJECT_ROOT}/venv" ]; then
        log_info "Using existing virtual environment (venv)..."
        source "${PROJECT_ROOT}/venv/bin/activate"
    elif [ "${CI:-false}" = "true" ]; then
        log_info "Running in CI environment, using global Python packages..."
    else
        log_error "Virtual environment not found. Please create one and install dependencies:"
        log_error "  python3 -m venv .venv"
        log_error "  source .venv/bin/activate"
        log_error "  pip install -r requirements.txt"
        exit 1
    fi
    
    # Check if PyInstaller is installed
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        log_error "PyInstaller is not installed. Install it with: pip install pyinstaller"
        exit 1
    fi
    
    # Build with PyInstaller
    log_info "Running PyInstaller (this may take a few minutes)..."
    pyinstaller audio-fetch.spec --clean --distpath "${BUILD_DIR}/pyinstaller-dist"
    
    if [ ! -f "${BUILD_DIR}/pyinstaller-dist/audio-fetch" ]; then
        log_error "PyInstaller build failed. Executable not found."
        exit 1
    fi
    
    log_info "PyInstaller build completed successfully"
}

create_appdir_structure() {
    log_info "Creating AppDir structure..."
    
    # Create directory structure
    mkdir -p "${APPDIR}/usr/bin"
    mkdir -p "${APPDIR}/usr/share/applications"
    mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "${APPDIR}/usr/share/metainfo"
    
    # Copy executable
    log_info "Copying executable..."
    cp "${BUILD_DIR}/pyinstaller-dist/audio-fetch" "${APPDIR}/usr/bin/"
    chmod +x "${APPDIR}/usr/bin/audio-fetch"
    
    # Copy icon
    log_info "Copying icon..."
    if [ -f "${PROJECT_ROOT}/static/favicon.png" ]; then
        cp "${PROJECT_ROOT}/static/favicon.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
        # Also place in root for AppImage
        cp "${PROJECT_ROOT}/static/favicon.png" "${APPDIR}/${APP_NAME}.png"
    else
        log_warn "Icon not found at static/favicon.png"
    fi
}

create_desktop_file() {
    log_info "Creating .desktop file..."
    
    cat > "${APPDIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Comment=Download audio from YouTube and other sources
Exec=audio-fetch
Icon=${APP_NAME}
Categories=AudioVideo;Audio;
Terminal=false
StartupNotify=true
EOF
    
    # Copy to AppDir root (required for AppImage)
    cp "${APPDIR}/usr/share/applications/${APP_NAME}.desktop" "${APPDIR}/${APP_NAME}.desktop"
    
    log_info ".desktop file created"
}

create_apprun() {
    log_info "Creating AppRun..."
    
    cat > "${APPDIR}/AppRun" << 'APPRUN_EOF'
#!/bin/bash
# AppRun script for Audio Fetch AppImage

SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Set up environment
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Qt plugin path (for PySide6)
export QT_PLUGIN_PATH="${HERE}/usr/lib/qt6/plugins:${QT_PLUGIN_PATH}"
export QML_IMPORT_PATH="${HERE}/usr/lib/qt6/qml:${QML_IMPORT_PATH}"
export QML2_IMPORT_PATH="${HERE}/usr/lib/qt6/qml:${QML2_IMPORT_PATH}"

# Disable Qt debug output in production
export QT_LOGGING_RULES="*.debug=false;qt.qpa.*=false"

# Execute the application
exec "${HERE}/usr/bin/audio-fetch" "$@"
APPRUN_EOF
    
    chmod +x "${APPDIR}/AppRun"
    log_info "AppRun created"
}

create_appstream_metadata() {
    log_info "Creating AppStream metadata..."
    
    cat > "${APPDIR}/usr/share/metainfo/${APP_NAME}.appdata.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>io.github.audio_fetch.AudioFetch</id>
  <launchable type="desktop-id">${APP_NAME}.desktop</launchable>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <name>${APP_DISPLAY_NAME}</name>
  <summary>Download audio from YouTube and other sources</summary>
  <description>
    <p>
      Audio Fetch is a native desktop application for downloading YouTube audio 
      with automatic cookie extraction and multi-tier fallback strategies.
    </p>
    <p>Features:</p>
    <ul>
      <li>Native desktop window with embedded web interface</li>
      <li>Automatic browser cookie extraction for YouTube authentication</li>
      <li>3-tier download strategy for robust downloading</li>
      <li>Support for Chrome, Firefox, Edge, and Brave browsers</li>
    </ul>
  </description>
  <categories>
    <category>AudioVideo</category>
    <category>Audio</category>
  </categories>
  <developer id="io.github.audio_fetch">
    <name>Audio Fetch Team</name>
  </developer>
  <content_rating type="oars-1.1" />
  <releases>
    <release version="${VERSION_NUMBER}" date="$(date +%Y-%m-%d)">
      <description>
        <p>Version ${VERSION_NUMBER}</p>
      </description>
    </release>
  </releases>
</component>
EOF
    
    log_info "AppStream metadata created"
}

build_appimage() {
    log_info "Building AppImage..."
    
    # Set output filename with version
    OUTPUT_APPIMAGE="${DIST_DIR}/${APP_NAME}-v${VERSION_NUMBER}-${ARCH}.AppImage"
    
    # Remove old AppImage if exists
    if [ -f "${OUTPUT_APPIMAGE}" ]; then
        rm "${OUTPUT_APPIMAGE}"
    fi
    
    # Build AppImage (skip AppStream validation for quick testing)
    ARCH=${ARCH} "${APPIMAGETOOL}" --no-appstream "${APPDIR}" "${OUTPUT_APPIMAGE}"
    
    if [ -f "${OUTPUT_APPIMAGE}" ]; then
        log_info "AppImage built successfully!"
        log_info "Output: ${OUTPUT_APPIMAGE}"
        log_info "Size: $(du -h "${OUTPUT_APPIMAGE}" | cut -f1)"
        
        # Make executable
        chmod +x "${OUTPUT_APPIMAGE}"
        
        log_info ""
        log_info "To run the AppImage:"
        log_info "  ${OUTPUT_APPIMAGE}"
        log_info ""
        log_info "To make it executable from anywhere:"
        log_info "  chmod +x ${OUTPUT_APPIMAGE}"
        log_info "  sudo mv ${OUTPUT_APPIMAGE} /usr/local/bin/"
    else
        log_error "AppImage build failed"
        exit 1
    fi
}

cleanup_build_files() {
    log_info "Cleaning up build files..."
    
    # Keep AppDir for debugging, but remove PyInstaller dist
    if [ -d "${BUILD_DIR}/pyinstaller-dist" ]; then
        rm -rf "${BUILD_DIR}/pyinstaller-dist"
    fi
    
    log_info "Cleanup complete (AppDir preserved for debugging)"
}

# Main execution
main() {
    log_info "========================================="
    log_info "Audio Fetch AppImage Build Script"
    log_info "Version: ${VERSION_NUMBER}"
    log_info "========================================="
    log_info ""
    
    check_requirements
    setup_build_env
    download_appimagetool
    build_with_pyinstaller
    create_appdir_structure
    create_desktop_file
    create_apprun
    create_appstream_metadata
    build_appimage
    cleanup_build_files
    
    log_info ""
    log_info "========================================="
    log_info "Build completed successfully!"
    log_info "========================================="
}

# Run main function
main
