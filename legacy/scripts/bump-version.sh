#!/usr/bin/env bash
# Bump semantic version in pyproject.toml
# Usage: ./bump-version.sh <current_version> <bump_type>
#   current_version: e.g., "0.1.0"
#   bump_type: "patch", "minor", or "major"

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

# Usage information
usage() {
    cat << EOF
Usage: $0 <current_version> <bump_type>

Arguments:
  current_version   Current version (e.g., "0.1.0" or "v0.1.0")
  bump_type         Type of version bump: "patch", "minor", or "major"

Examples:
  $0 0.1.0 patch    # 0.1.0 -> 0.1.1
  $0 0.1.9 minor    # 0.1.9 -> 0.2.0
  $0 0.9.9 major    # 0.9.9 -> 1.0.0

Description:
  Bumps the version number in pyproject.toml according to semantic versioning.
  - patch: Increment the patch version (0.0.X)
  - minor: Increment the minor version (0.X.0), reset patch to 0
  - major: Increment the major version (X.0.0), reset minor and patch to 0
EOF
}

# Validate arguments
if [[ $# -ne 2 ]]; then
    log_error "Invalid number of arguments"
    usage
    exit 1
fi

CURRENT_VERSION="$1"
BUMP_TYPE="$2"

# Strip 'v' prefix if present
CURRENT_VERSION="${CURRENT_VERSION#v}"

# Validate version format (MAJOR.MINOR.PATCH)
if ! [[ "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    log_error "Invalid version format: '$CURRENT_VERSION'"
    log_error "Expected format: MAJOR.MINOR.PATCH (e.g., 0.1.0)"
    exit 1
fi

# Validate bump type
if [[ "$BUMP_TYPE" != "patch" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "major" ]]; then
    log_error "Invalid bump type: '$BUMP_TYPE'"
    log_error "Must be one of: patch, minor, major"
    exit 1
fi

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Calculate new version
case "$BUMP_TYPE" in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

log_info "Bumping version: $CURRENT_VERSION -> $NEW_VERSION ($BUMP_TYPE)"

# Find pyproject.toml
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"

if [[ ! -f "$PYPROJECT_FILE" ]]; then
    log_error "pyproject.toml not found at: $PYPROJECT_FILE"
    exit 1
fi

# Backup pyproject.toml
BACKUP_FILE="${PYPROJECT_FILE}.backup"
cp "$PYPROJECT_FILE" "$BACKUP_FILE"
log_info "Created backup: $BACKUP_FILE"

# Update version in pyproject.toml
# Match: version = "X.Y.Z"
# Update version in pyproject.toml using extended regex
# Match: version = "X.Y.Z" where X, Y, Z are one or more digits
# Replace with: version = "NEW_VERSION"
if sed -i.tmp -E "s/^version = \"[0-9]+\.[0-9]+\.[0-9]+\"$/version = \"$NEW_VERSION\"/" "$PYPROJECT_FILE"; then
    log_info "Updated version in pyproject.toml"
else
    log_error "Failed to update pyproject.toml"
    # Restore backup
    mv "$BACKUP_FILE" "$PYPROJECT_FILE"
    log_warn "Restored from backup"
    exit 1
fi

# Verify the update
if grep -q "version = \"$NEW_VERSION\"" "$PYPROJECT_FILE"; then
    log_info "✓ Version successfully updated to $NEW_VERSION"
    rm -f "$BACKUP_FILE"
    echo "$NEW_VERSION"  # Output new version for capture
    exit 0
else
    log_error "Version verification failed - update may not have worked"
    # Restore backup
    mv "$BACKUP_FILE" "$PYPROJECT_FILE"
    log_warn "Restored from backup"
    exit 1
fi
