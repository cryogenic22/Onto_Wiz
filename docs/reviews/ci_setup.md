# [SEN-001] CI Setup Report

**Date:** 2026-02-01
**Author:** Team SENTINEL
**Scope:** CI/CD pipeline, pre-commit hooks, quality config centralization

## What Was Set Up

### 1. GitHub Actions CI Pipeline (`.github/workflows/ci.yml`)

Two parallel jobs run on every push and PR:

**python-checks:**
1. Checkout repo
2. Set up Python 3.11 with pip cache
3. Install editable package + dev dependencies
4. `ruff check src/ tests/` — lint
5. `mypy src/ --ignore-missing-imports` — type check
6. `pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=70` — tests + coverage gate
7. `python quality-gate/quality_gate.py --root .` — function size, complexity, PRS scoring

**frontend-build:**
1. Checkout repo
2. Set up Node 20 with npm cache
3. `npm ci` — deterministic install
4. `npm run build` — Next.js production build
5. `npm run lint` — ESLint

### 2. Pre-commit Hooks (`.pre-commit-config.yaml`)

Local development hooks (install with `pre-commit install`):
- **ruff** — lint with auto-fix + format check
- **mypy** — type check on `src/` only
- **pytest-fast** — quick test run (`-x -q`, stops on first failure)

### 3. Centralized Quality Config (`quality/config.yaml`)

Single source of truth for all thresholds:
- Coverage: min 70%, target 80%
- Function size: max 50 lines
- Cyclomatic complexity: max 10
- PRS: min 85/100

### 4. Quality Reference (`quality/README.md`)

Documents each gate, its tool, threshold, and how to fix common failures.

## How to Use

### For developers (local)
```bash
# One-time setup
pip install pre-commit
pre-commit install

# Hooks run automatically on git commit
# Manual run:
pre-commit run --all-files
```

### For CI
Push to any branch or open a PR to main. The pipeline runs automatically.

## Verification

- Pipeline uses existing tools only (no new dependencies)
- All 121 existing tests unaffected (infrastructure-only change)
- Pipeline designed to complete in under 5 minutes
