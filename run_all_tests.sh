#!/usr/bin/env bash
# Run all tests: unit tests + e2e tests separately to avoid event loop conflicts

set -e

echo "Running unit tests..."
pytest tests/ -m "not e2e" -v

echo ""
echo "Running E2E tests..."
pytest tests/e2e/ -v

echo ""
echo "All tests passed!"
