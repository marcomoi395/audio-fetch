# Git Hooks Documentation

## Overview

This project has automated git hooks to ensure code quality before committing and pushing.

## Installed Hooks

### 1. Pre-Commit Hook (`.git/hooks/pre-commit`)

**Runs automatically before each commit.**

This hook:
- ✓ Formats staged Python files with `ruff format`
- ✓ Lints and auto-fixes issues with `ruff check --fix`
- ✓ Formats with `black` for consistent style
- ✓ Re-stages formatted files automatically

**Behavior:**
- Only checks **staged** Python files (`.py`)
- Automatically fixes formatting issues
- Fails the commit if formatting/linting fails
- Re-adds fixed files to staging area

### 2. Pre-Push Hook (`.git/hooks/pre-push`)

**Runs automatically before pushing to remote.**

This hook performs comprehensive validation with auto-formatting:
1. ✓ **Checks code formatting** with `ruff format` and `black`
2. ✓ **Auto-formats code** if formatting issues found
3. ✓ **Automatically amends your last commit** with formatted code
4. ✓ Runs linter with `ruff check`
5. ⚠️  Runs type checking with `mypy` (warning only, non-blocking)
6. ✓ Runs full test suite with `pytest`
7. ✓ Final verification that formatting is correct

**Behavior:**
- Checks **all** Python files in the project
- **Auto-formats and amends commit** if formatting issues detected
- Blocks push if linting or tests fail
- Shows detailed error messages

**⚠️ Important:** The pre-push hook will automatically format your code and amend your commit if formatting issues are found. This means your commit hash may change during push.

## Usage

### Normal Workflow

```bash
# 1. Make changes to Python files
vim main.py

# 2. Stage your changes
git add main.py

# 3. Commit (pre-commit hook runs automatically)
git commit -m "Add new feature"
# → Auto-formats code and re-stages files

# 4. Push (pre-push hook runs automatically)
git push origin main
# → If code not formatted: auto-formats, amends commit, then validates and runs tests
# → Your commit hash may change if formatting was needed
```

### What Happens During Push

If your code is not properly formatted:

```bash
git push origin main
# Output:
# [1/5] Checking code formatting...
# ⚠ Code is not formatted with ruff. Auto-formatting...
# Running formatters...
# Staging formatted files...
# Amending commit with formatted code...
# ✓ Code formatted and commit amended
# [2/5] Running ruff linter...
# ✓ Ruff linting passed
# [3/5] Running type checking with mypy...
# ✓ Type checking passed
# [4/5] Running tests...
# ✓ All tests passed
# [5/5] Final verification...
# ✓ Final verification passed
# Proceeding with push...
```

### Skipping Hooks (Not Recommended)

If you need to bypass hooks temporarily:

```bash
# Skip pre-commit hook
git commit --no-verify -m "WIP: temporary commit"

# Skip pre-push hook
git push --no-verify origin main
```

⚠️ **Warning:** Only skip hooks for temporary work. Always run checks before merging!

## Manual Commands

You can run the same checks manually:

```bash
# Format code
ruff format .
black .

# Lint and fix
ruff check --fix .

# Type check
mypy . --ignore-missing-imports

# Run tests
pytest tests/ -v
```

## Configuration

Tool configurations are in `pyproject.toml`:

- **Ruff**: Line length 100, Python 3.10+, common linting rules
- **Black**: Line length 100, Python 3.10+
- **Mypy**: Basic type checking with warnings
- **Pytest**: Auto-async mode, coverage reporting

### Customizing Rules

Edit `pyproject.toml` to adjust:

```toml
[tool.ruff]
line-length = 100  # Change line length

[tool.ruff.lint]
ignore = [
    "E501",  # Add rules to ignore
]
```

## Troubleshooting

### Hook not running

```bash
# Check if hooks are executable
ls -l .git/hooks/pre-commit .git/hooks/pre-push

# Make executable if needed
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

### Tests failing on push

```bash
# Run tests manually to debug
pytest tests/ -v --tb=long

# Run specific test file
pytest tests/test_download.py -v
```

### Formatting issues

```bash
# Check what needs formatting
ruff format --check .
black --check .

# Auto-fix formatting
ruff format .
black .
```

### Linting errors

```bash
# See all linting issues
ruff check .

# Auto-fix what's possible
ruff check --fix .
```

### Commit hash changed after push

This is expected behavior when the pre-push hook auto-formats your code:

```bash
# Before push
git log -1 --oneline
# abc1234 Add new feature

# After push (if formatting was needed)
git log -1 --oneline
# def5678 Add new feature  # <- Hash changed because commit was amended
```

If you've already pushed and then the hook amends your commit, you may need to force push:

```bash
git push --force-with-lease origin main
```

**Recommendation:** Always format your code before committing to avoid commit hash changes:

```bash
ruff format . && black .
git add -u
git commit -m "Your message"
git push  # No amendment needed
```

## CI/CD Integration

These hooks complement CI/CD pipelines:

- **Hooks**: Fast feedback during development
- **CI/CD**: Final validation before merge

Both should use the same tools and configuration from `pyproject.toml`.

## Benefits

1. **Consistent code style** across the team
2. **Catch issues early** before pushing
3. **Automatic formatting** reduces manual work
4. **Tests always run** before code reaches remote
5. **Zero manual setup** for new contributors

## Notes

- Hooks are **local** (in `.git/hooks/`, not tracked by git)
- Each developer needs to set up hooks after cloning (run `scripts/setup-hooks.sh`)
- For team-wide hooks, consider using `pre-commit` framework
- Hooks use tools already in `requirements.txt`
- Pre-push hook may amend your commit if formatting is needed
