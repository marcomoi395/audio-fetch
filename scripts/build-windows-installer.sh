#!/usr/bin/env bash
# Build script for Audio Fetch Windows Installer
# Purpose: Create a Windows installer using PyInstaller + Inno Setup
#
# Requirements (Windows):
# - Python 3.10+ with venv
# - PyInstaller
# - Inno Setup 6+
# - FFmpeg (runtime dependency, not bundled)
#
# Requirements (Linux cross-compile):
# - Wine
# - Python for Windows
# - Inno Setup via Wine
#
# Usage:
#   ./build-windows-installer.sh <version>
#
# Arguments:
#   version: Version number (e.g., "0.1.0" or "v0.1.0")
#
# Output:
#   dist/audio-fetch-v{version}-setup.exe

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
  Builds a Windows installer for Audio Fetch with the specified version.
  Output: dist/audio-fetch-v{version}-setup.exe
  
  This script should be run on Windows with Inno Setup installed.
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
APP_PUBLISHER="Audio Fetch Team"
APP_URL="https://github.com/audio-fetch/audio-fetch"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build-windows"
DIST_DIR="${PROJECT_ROOT}/dist"

# Inno Setup compiler path (common locations)
ISCC_PATHS=(
    "/c/Program Files (x86)/Inno Setup 6/ISCC.exe"
    "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
    "/mnt/c/Program Files (x86)/Inno Setup 6/ISCC.exe"
    "$(which iscc 2>/dev/null || echo '')"
)

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Python version
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        log_error "Python is not installed"
        exit 1
    fi
    
    PYTHON_CMD="python"
    if ! command -v python &> /dev/null; then
        PYTHON_CMD="python3"
    fi
    
    PYTHON_VER=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Found Python ${PYTHON_VER}"
    
    # Check for Inno Setup
    ISCC=""
    for path in "${ISCC_PATHS[@]}"; do
        if [ -n "$path" ] && [ -f "$path" ]; then
            ISCC="$path"
            log_info "Found Inno Setup at: $ISCC"
            break
        fi
    done
    
    if [ -z "$ISCC" ]; then
        log_error "Inno Setup not found"
        log_error "Install from: https://jrsoftware.org/isdl.php"
        log_error "Expected locations: ${ISCC_PATHS[0]}"
        exit 1
    fi
}

setup_build_env() {
    log_info "Setting up build environment..."
    
    # Create build directories
    mkdir -p "${BUILD_DIR}"
    mkdir -p "${DIST_DIR}"
    
    # Clean previous build
    if [ -d "${BUILD_DIR}/pyinstaller-dist" ]; then
        log_info "Cleaning previous build..."
        rm -rf "${BUILD_DIR}/pyinstaller-dist"
    fi
}

build_with_pyinstaller() {
    log_info "Building with PyInstaller..."
    
    cd "${PROJECT_ROOT}"
    
    # Check if PyInstaller is installed
    if ! $PYTHON_CMD -c "import PyInstaller" 2>/dev/null; then
        log_error "PyInstaller is not installed. Install it with: pip install pyinstaller"
        exit 1
    fi
    
    # Build with PyInstaller
    log_info "Running PyInstaller (this may take a few minutes)..."
    $PYTHON_CMD -m PyInstaller audio-fetch.spec --clean --distpath "${BUILD_DIR}/pyinstaller-dist"
    
    if [ ! -f "${BUILD_DIR}/pyinstaller-dist/audio-fetch.exe" ]; then
        log_error "PyInstaller build failed. Executable not found."
        exit 1
    fi
    
    log_info "PyInstaller build completed successfully"
}

# Convert Unix path to Windows path
# Handles both Git Bash paths (/d/path) and WSL paths (/mnt/d/path)
convert_to_windows_path() {
    local unix_path="$1"
    
    # If running on Windows with Git Bash or similar
    if command -v cygpath &> /dev/null; then
        # Use cygpath if available (Git Bash)
        cygpath -w "$unix_path"
    elif [[ "$unix_path" =~ ^/([a-z])/(.+)$ ]]; then
        # Git Bash style: /d/path -> D:\path
        local drive="${BASH_REMATCH[1]}"
        local path="${BASH_REMATCH[2]}"
        echo "${drive^^}:\\${path//\//\\}"
    elif [[ "$unix_path" =~ ^/mnt/([a-z])/(.+)$ ]]; then
        # WSL style: /mnt/d/path -> D:\path
        local drive="${BASH_REMATCH[1]}"
        local path="${BASH_REMATCH[2]}"
        echo "${drive^^}:\\${path//\//\\}"
    else
        # Already Windows style or relative path, just convert slashes
        echo "$unix_path" | sed 's|/|\\|g'
    fi
}

generate_inno_script() {
    log_info "Generating Inno Setup script..."

    ISS_FILE="${BUILD_DIR}/audio-fetch-installer.iss"

    # Copy LICENSE into BUILD_DIR so Inno Setup can find it via relative path
    cp "${PROJECT_ROOT}/LICENSE" "${BUILD_DIR}/LICENSE"

    # Convert paths to Windows format for Inno Setup
    WIN_DIST_DIR=$(convert_to_windows_path "$DIST_DIR")
    WIN_BUILD_DIR=$(convert_to_windows_path "$BUILD_DIR")

    cat > "${ISS_FILE}" << EOF
; Inno Setup Script for Audio Fetch
; Generated by build-windows-installer.sh

#define MyAppName "${APP_DISPLAY_NAME}"
#define MyAppVersion "${VERSION_NUMBER}"
#define MyAppPublisher "${APP_PUBLISHER}"
#define MyAppURL "${APP_URL}"
#define MyAppExeName "audio-fetch.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=${WIN_DIST_DIR}
OutputBaseFilename=${APP_NAME}-v${VERSION_NUMBER}-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "${WIN_BUILD_DIR}\\pyinstaller-dist\\audio-fetch.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  MsgBox('FFmpeg is required for audio conversion.' #13#10 #13#10 +
         'Please install FFmpeg separately if not already installed.' #13#10 +
         'Download from: https://ffmpeg.org/download.html', mbInformation, MB_OK);
end;
EOF

    log_info "Inno Setup script generated: ${ISS_FILE}"
}

build_installer() {
    log_info "Building Windows installer with Inno Setup..."
    
    ISS_FILE="${BUILD_DIR}/audio-fetch-installer.iss"
    
    # Run Inno Setup compiler
    "$ISCC" "$ISS_FILE"
    
    INSTALLER_PATH="${DIST_DIR}/${APP_NAME}-v${VERSION_NUMBER}-setup.exe"
    
    if [ -f "${INSTALLER_PATH}" ]; then
        log_info "Windows installer built successfully!"
        log_info "Output: ${INSTALLER_PATH}"
        log_info "Size: $(du -h "${INSTALLER_PATH}" | cut -f1)"
        
        log_info ""
        log_info "To test the installer:"
        log_info "  ${INSTALLER_PATH}"
    else
        log_error "Installer build failed"
        exit 1
    fi
}

cleanup_build_files() {
    log_info "Cleaning up build files..."
    
    if [ -d "${BUILD_DIR}/pyinstaller-dist" ]; then
        rm -rf "${BUILD_DIR}/pyinstaller-dist"
    fi
    
    log_info "Cleanup complete"
}

# Main execution
main() {
    log_info "========================================="
    log_info "Audio Fetch Windows Installer Build"
    log_info "Version: ${VERSION_NUMBER}"
    log_info "========================================="
    log_info ""
    
    check_requirements
    setup_build_env
    build_with_pyinstaller
    generate_inno_script
    build_installer
    cleanup_build_files
    
    log_info ""
    log_info "========================================="
    log_info "Build completed successfully!"
    log_info "========================================="
}

# Run main function
main
