# Quality Gate Reference

Owner: Team SENTINEL

This directory contains centralized quality configuration for the Onto_Wiz project.

## Gate Summary

| Gate | Tool | Threshold | CI Step |
|------|------|-----------|---------|
| Lint | ruff | 0 errors | `ruff check src/ tests/` |
| Type check | mypy | 0 errors on public APIs | `mypy src/ --ignore-missing-imports` |
| Test coverage | pytest-cov | Min 70%, target 80% | `pytest --cov=src --cov-fail-under=70` |
| Function size | quality_gate.py | Max 50 lines | `python quality-gate/quality_gate.py --root .` |
| Cyclomatic complexity | quality_gate.py | Max 10 per function | Same as above |
| PRS score | quality_gate.py | Min 85/100 | Same as above |
| Architecture | cathedral-keeper | 0 boundary violations | `python cathedral-keeper/ck.py analyze --root .` |
| Frontend build | next build | 0 errors | `cd frontend && npm run build` |

## How to Fix Common Failures

### Lint failures (ruff)
```bash
ruff check src/ tests/          # See errors
ruff check src/ tests/ --fix    # Auto-fix what's possible
```

### Type check failures (mypy)
```bash
mypy src/ --ignore-missing-imports
```
Add type annotations to public function signatures. No `Any` at API boundaries.

### Coverage below 70%
```bash
pytest tests/ --cov=src --cov-report=term-missing
```
Look at the "Missing" column to find uncovered lines. Add tests for those paths.

### Function too long (>50 lines)
Extract helper functions. Each function should do one thing. See DEC-004 in `docs/DECISION_LOG.md`.

### PRS below 85
PRS = 100 - (errors x 10) - (warnings x 2). Fix errors first (10x impact), then warnings.

### Architecture violation
`src/core/` and `src/reasoning/` must not import from `src/api/`. Dependencies point inward only. See DEC-007.

## Config Files

| File | Purpose |
|------|---------|
| `quality/config.yaml` | Centralized threshold values |
| `.quality-gate.json` | Quality gate tool config (paths, PRS settings) |
| `pyproject.toml` | ruff, mypy, pytest, coverage tool settings |
| `.pre-commit-config.yaml` | Local pre-commit hook definitions |
