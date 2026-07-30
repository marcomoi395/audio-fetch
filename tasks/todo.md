# Task Checklist: User-Provided Cookie Authentication

## Phase 1: Backend Foundation

- [x] Task 1: Update API models to require cookies
- [x] Task 2: Update downloader service to require cookies (+ security verification)
- [x] Task 3: Add cookie validation in API routes

**Checkpoint: Backend Foundation**
- [ ] All backend code requires cookies
- [ ] No environment variable fallback exists
- [ ] API returns clear errors for missing cookies
- [ ] Security: Temp files cleaned up, cookies not logged
- [ ] Tests pass: `pytest tests/test_api.py tests/test_downloader.py -v`

## Phase 2: Frontend Enforcement

- [x] Task 4: Add cookie validation before API calls
- [x] Task 5: Update cookie UI to reflect mandatory requirement (buttons disabled, section expanded)

**Checkpoint: Frontend Enforcement**
- [ ] UI prevents requests without cookies
- [ ] Buttons disabled when no cookies
- [ ] Cookie section visible by default
- [ ] Clear error messages guide users
- [ ] Manual E2E flow works

## Phase 3: Testing & Cleanup

- [x] Task 6: Update unit tests to pass required cookies
- [x] Task 7: Update integration tests for cookie validation
- [x] Task 8: Remove environment variable support and documentation
- [x] Task 9: Add E2E test for complete cookie flow

**Checkpoint: Complete**
- [ ] All tests pass: `pytest -v`
- [ ] E2E tests pass: `pytest tests/e2e/ -v`
- [ ] Linting passes: `ruff check .`
- [ ] Type checking passes: `mypy .`
- [ ] Manual E2E flow works
- [ ] No environment variable references remain
- [ ] Documentation updated
- [ ] Security verified: temp files cleaned up, cookies not logged

---

**Estimated Time:** ~9.5 hours (~1.5 focused days)

**See `tasks/plan.md` for detailed acceptance criteria and verification steps.**
