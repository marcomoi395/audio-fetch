#!/usr/bin/env bash
# Build script for Audio Fetch .rpm package (Fedora/RHEL/CentOS)
# Purpose: Create an RPM package for Red Hat-based systems
#
# Requirements:
# - Python 3.10+ with venv
# - PyInstaller
# - fpm (Effing Package Management)
# - FFmpeg (runtime dependency, not bundled)
#
# Usage:
#   ./build-linux-rpm.sh <version>
#
# Arguments:
#   version: Version number (e.g., "0.1.0" or "v0.1.0")
#
# Output:
#   dist/audio-fetch-{version}-1.x86_64.rpm

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
  Builds an .rpm package for Audio Fetch with the specified version.
  Output: dist/audio-fetch-{version}-1.x86_64.rpm
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
ARCH="x86_64"
RELEASE="1"
MAINTAINER="Audio Fetch Team <audio-fetch@example.com>"
DESCRIPTION="Download audio from YouTube and other sources"
LONG_DESCRIPTION="Audio Fetch is a native desktop application for downloading YouTube audio with automatic cookie extraction and multi-tier fallback strategies."

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build-rpm"
PACKAGE_ROOT="${BUILD_DIR}/package"
DIST_DIR="${PROJECT_ROOT}/dist"

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Found Python ${PYTHON_VER}"
    
    # Check for fpm
    if ! command -v fpm &> /dev/null; then
        log_error "fpm (Effing Package Management) is not installed"
        log_error "Install it with: sudo dnf install ruby-devel && sudo gem install fpm"
        exit 1
    fi
    
    log_info "Found fpm $(fpm --version | head -1)"
}

setup_build_env() {
    log_info "Setting up build environment..."
    
    # Create build directories
    mkdir -p "${BUILD_DIR}"
    mkdir -p "${PACKAGE_ROOT}"
    mkdir -p "${DIST_DIR}"
    
    # Clean previous build
    if [ -d "${PACKAGE_ROOT}" ]; then
        log_info "Cleaning previous build..."
        rm -rf "${PACKAGE_ROOT}"
        mkdir -p "${PACKAGE_ROOT}"
    fi
}

build_with_pyinstaller() {
    log_info "Building with PyInstaller..."
    
    cd "${PROJECT_ROOT}"
    
    # Activate virtual environment if it exists
    if [ -d "${PROJECT_ROOT}/.venv" ]; then
        log_info "Using existing virtual environment..."
        source "${PROJECT_ROOT}/.venv/bin/activate"
    elif [ -d "${PROJECT_ROOT}/venv" ]; then
        log_info "Using existing virtual environment..."
        source "${PROJECT_ROOT}/venv/bin/activate"
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

create_package_structure() {
    log_info "Creating package structure..."
    
    # Create directory structure
    mkdir -p "${PACKAGE_ROOT}/usr/bin"
    mkdir -p "${PACKAGE_ROOT}/usr/share/applications"
    mkdir -p "${PACKAGE_ROOT}/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "${PACKAGE_ROOT}/usr/share/doc/${APP_NAME}"
    
    # Copy executable
    log_info "Copying executable..."
    cp "${BUILD_DIR}/pyinstaller-dist/audio-fetch" "${PACKAGE_ROOT}/usr/bin/"
    chmod +x "${PACKAGE_ROOT}/usr/bin/audio-fetch"
    
    # Copy icon
    log_info "Copying icon..."
    if [ -f "${PROJECT_ROOT}/static/favicon.png" ]; then
        cp "${PROJECT_ROOT}/static/favicon.png" "${PACKAGE_ROOT}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    else
        log_warn "Icon not found at static/favicon.png"
    fi
    
    # Create desktop file
    log_info "Creating .desktop file..."
    cat > "${PACKAGE_ROOT}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Comment=${DESCRIPTION}
Exec=audio-fetch
Icon=${APP_NAME}
Categories=AudioVideo;Audio;
Terminal=false
StartupNotify=true
EOF
    
    # Create README file
    log_info "Creating README file..."
    cat > "${PACKAGE_ROOT}/usr/share/doc/${APP_NAME}/README" << EOF
${APP_DISPLAY_NAME} ${VERSION_NUMBER}

${LONG_DESCRIPTION}

FFmpeg Requirement:
  Audio Fetch requires FFmpeg for audio conversion.
  Install it with: sudo dnf install ffmpeg

Usage:
  Run 'audio-fetch' to start the application.

License:
  MIT License - see LICENSE file for details.

More Information:
  https://github.com/audio-fetch/audio-fetch
EOF
}

build_rpm_package() {
    log_info "Building .rpm package with fpm..."
    
    cd "${BUILD_DIR}"
    
    # Output filename
    OUTPUT_RPM="${DIST_DIR}/${APP_NAME}-${VERSION_NUMBER}-${RELEASE}.${ARCH}.rpm"
    
    # Remove old package if exists
    if [ -f "${OUTPUT_RPM}" ]; then
        rm "${OUTPUT_RPM}"
    fi
    
    # Build package with fpm
    fpm \
        -s dir \
        -t rpm \
        -n "${APP_NAME}" \
        -v "${VERSION_NUMBER}" \
        --iteration "${RELEASE}" \
        -a "${ARCH}" \
        --description "${DESCRIPTION}" \
        --maintainer "${MAINTAINER}" \
        --license "MIT" \
        --url "https://github.com/audio-fetch/audio-fetch" \
        --category "Applications/Multimedia" \
        --rpm-summary "${DESCRIPTION}" \
        --after-install "${SCRIPT_DIR}/rpm-postinstall.sh" \
        --after-remove "${SCRIPT_DIR}/rpm-postrm.sh" \
        -C "${PACKAGE_ROOT}" \
        -p "${OUTPUT_RPM}" \
        .
    
    if [ -f "${OUTPUT_RPM}" ]; then
        log_info ".rpm package built successfully!"
        log_info "Output: ${OUTPUT_RPM}"
        log_info "Size: $(du -h "${OUTPUT_RPM}" | cut -f1)"
        
        log_info ""
        log_info "To install the package:"
        log_info "  sudo rpm -i ${OUTPUT_RPM}"
        log_info "  # or"
        log_info "  sudo dnf install ${OUTPUT_RPM}"
        log_info ""
        log_info "To inspect the package:"
        log_info "  rpm -qip ${OUTPUT_RPM}"
        log_info "  rpm -qlp ${OUTPUT_RPM}"
    else
        log_error ".rpm package build failed"
        exit 1
    fi
}

cleanup_build_files() {
    log_info "Cleaning up build files..."
    
    if [ -d "${BUILD_DIR}/pyinstaller-dist" ]; then
        rm -rf "${BUILD_DIR}/pyinstaller-dist"
    fi
    
    log_info "Cleanup complete (package structure preserved for debugging)"
}

# Main execution
main() {
    log_info "========================================="
    log_info "Audio Fetch .rpm Package Build Script"
    log_info "Version: ${VERSION_NUMBER}"
    log_info "========================================="
    log_info ""
    
    check_requirements
    setup_build_env
    build_with_pyinstaller
    create_package_structure
    build_rpm_package
    cleanup_build_files
    
    log_info ""
    log_info "========================================="
    log_info "Build completed successfully!"
    log_info "========================================="
}

# Run main function
main
