# Testing Guide

Because this project uses both `pytest-asyncio` for unit tests and `pytest-playwright` for end-to-end tests, they compete for the `asyncio` event loop policy. Running them in the same pytest session will cause `RuntimeError: Runner.run() cannot be called from a running event loop`.

You **must** run them in two separate commands.

## Running Unit and Integration Tests

These tests cover backend logic and API routes without spinning up a real browser.

```bash
# Run unit and integration tests (ignore E2E)
pytest tests/ --ignore=tests/e2e/ -v

# Run with coverage report
pytest tests/ --ignore=tests/e2e/ --cov=. --cov-report=term-missing
```

## Running End-to-End Tests

These tests spin up a background `uvicorn` live server and use Playwright to automate actual browser interactions.

```bash
# Run E2E tests headlessly
pytest tests/e2e/ -v

# Run E2E tests with a visible browser (for debugging)
pytest tests/e2e/ -v --headed --slowmo=500

# Run E2E tests on specific browsers
pytest tests/e2e/ --browser chromium --browser firefox
```
