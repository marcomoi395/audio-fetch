# GitHub Actions CI — Task Checklist

## Phase 1: Implementation

- [x] Task 1: Tạo `.github/workflows/ci.yml` hoàn chỉnh
  - Trigger: `pull_request` → `main` only
  - Setup Python 3.10 + pip cache
  - Install FFmpeg + requirements.txt
  - `ruff format --check .`
  - `ruff check .`
  - `mypy . --ignore-missing-imports`
  - `pytest --cov=. --cov-report=term-missing`

## Checkpoint: Complete

- [x] File tồn tại và YAML hợp lệ
- [x] Chỉ trigger PR → main (không có push trigger)
- [x] 4 checks đủ, không thừa
