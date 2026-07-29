#!/usr/bin/env bash
#
# Setup script for git hooks
# Run this after cloning the repository
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setting up git hooks...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}Error: Not a git repository!${NC}"
    echo "Run this script from within the git repository."
    exit 1
fi

# Check if hooks already exist
if [ -f "$HOOKS_DIR/pre-commit" ] && [ -f "$HOOKS_DIR/pre-push" ]; then
    echo -e "${YELLOW}Git hooks already exist.${NC}"
    read -p "Do you want to overwrite them? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Skipping hook installation.${NC}"
        exit 0
    fi
fi

# Create pre-commit hook
echo -e "${YELLOW}Creating pre-commit hook...${NC}"
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/usr/bin/env bash
#
# Git pre-commit hook
# Automatically formats Python code with ruff and black before committing
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running pre-commit checks...${NC}"

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}No Python files to check.${NC}"
    exit 0
fi

echo -e "${YELLOW}Formatting Python files with ruff...${NC}"
if ! ruff format $STAGED_FILES; then
    echo -e "${RED}Ruff formatting failed!${NC}"
    exit 1
fi

echo -e "${YELLOW}Checking Python files with ruff linter...${NC}"
if ! ruff check --fix $STAGED_FILES; then
    echo -e "${RED}Ruff linting failed!${NC}"
    echo -e "${YELLOW}Some issues may need manual fixes.${NC}"
    exit 1
fi

# Create pre-push hook
echo -e "${YELLOW}Creating pre-push hook...${NC}"
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/usr/bin/env bash
#
# Git pre-push hook
# Runs formatting, linting, and tests before pushing to remote
# Auto-formats code and amends commit if formatting issues are found
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Running pre-push validation...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if there are any Python files in the repo
PYTHON_FILES=$(find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./env/*" -not -path "./.env/*" -not -path "./__pycache__/*" | head -n 1)

if [ -z "$PYTHON_FILES" ]; then
    echo -e "${GREEN}No Python files found. Skipping checks.${NC}"
    exit 0
fi

# 1. Check and auto-fix formatting
echo -e "${YELLOW}[1/5] Checking code formatting...${NC}"
FORMAT_NEEDED=0

if ! ruff format --check . >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Code is not formatted with ruff. Auto-formatting...${NC}"
    FORMAT_NEEDED=1
fi

if ! black --check . >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Code is not formatted with black. Auto-formatting...${NC}"
    FORMAT_NEEDED=1
fi

if [ $FORMAT_NEEDED -eq 1 ]; then
    echo -e "${YELLOW}Running formatters...${NC}"
    ruff format .
    black .
    
    # Check if there are changes to commit
    if ! git diff --quiet; then
        echo -e "${YELLOW}Staging formatted files...${NC}"
        git add -u
        
        echo -e "${YELLOW}Amending commit with formatted code...${NC}"
        git commit --amend --no-edit
        
        echo -e "${GREEN}✓ Code formatted and commit amended${NC}"
    fi
else
    echo -e "${GREEN}✓ Code formatting check passed${NC}"
fi
echo ""

# 2. Run ruff linter
echo -e "${YELLOW}[2/5] Running ruff linter...${NC}"
if ! ruff check .; then
    echo -e "${RED}✗ Linting failed!${NC}"
    echo -e "${YELLOW}Run: ruff check --fix .${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Ruff linting passed${NC}"
echo ""

# 3. Run type checking with mypy (optional - warn but don't fail)
echo -e "${YELLOW}[3/5] Running type checking with mypy...${NC}"
if ! mypy . --ignore-missing-imports 2>/dev/null; then
    echo -e "${YELLOW}⚠ Type checking found issues (non-blocking)${NC}"
else
    echo -e "${GREEN}✓ Type checking passed${NC}"
fi
echo ""

# 4. Run tests
echo -e "${YELLOW}[4/5] Running tests...${NC}"
if ! pytest tests/ -v --tb=short; then
    echo -e "${RED}✗ Tests failed!${NC}"
    echo -e "${YELLOW}Fix the failing tests before pushing.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All tests passed${NC}"
echo ""

# 5. Final verification
echo -e "${YELLOW}[5/5] Final verification...${NC}"
if ! ruff format --check . >/dev/null 2>&1 || ! black --check . >/dev/null 2>&1; then
    echo -e "${RED}✗ Code formatting check failed after fixes!${NC}"
    echo -e "${YELLOW}This shouldn't happen. Please check manually.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Final verification passed${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All pre-push checks passed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Proceeding with push...${NC}"

exit 0
EOF

# Make hooks executable
chmod +x "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-push"

echo -e "${GREEN}✓ Git hooks installed successfully!${NC}"
echo ""
echo -e "${BLUE}Installed hooks:${NC}"
echo -e "  - ${GREEN}pre-commit${NC}: Auto-formats code before commit"
echo -e "  - ${GREEN}pre-push${NC}: Runs tests before push"
echo ""
echo -e "${YELLOW}To skip hooks temporarily:${NC}"
echo -e "  git commit --no-verify"
echo -e "  git push --no-verify"
echo ""
echo -e "${BLUE}For more information, see: ${NC}docs/GIT_HOOKS.md"
echo ""

exit 0
