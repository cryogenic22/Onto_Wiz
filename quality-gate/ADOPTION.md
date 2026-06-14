# Quality Gate Adoption Guide

This guide is designed to be copied with `quality-gate/` into any repo.

## Policy (recommended defaults)

- **All changed code files must have PRS ≥ 85.**
- **Errors must be 0** (warnings are allowed unless you opt into strict mode).
- PRS formula:
  - `PRS = 100 - (errors * 10) - (warnings * 2)`

## Install (local enforcement)

**Requires:** Python 3.10+.

### Option A: `pre-commit` (recommended)

1. Copy `quality-gate/` into your repo root.
2. Copy `quality-gate/.pre-commit-config.yaml` to your repo root as `.pre-commit-config.yaml`.
3. Run `pre-commit install`.

This repo ships an offline-friendly default pre-commit config. If your environment allows network access and you want extra lint/format hooks, use `quality-gate/.pre-commit-config.extended.yaml` instead.

### Option B: Installers (no pre-commit)

- Linux/macOS: `./quality-gate/install.sh`
- Windows: `.\quality-gate\install.ps1`

## Developer workflow (day-to-day)

- Before committing:
  - Stage changes
  - Run `python quality-gate/quality_gate.py --staged --root .`
  - Fix any blocking issues (including `prs_score` failures)
- Before pushing (strict mode, optional but recommended):
  - `python quality-gate/quality_gate.py --strict --root .`

## CI workflow (avoid legacy-debt blocking)

Prefer gating **only changed files** in CI so legacy debt doesn’t block new work:

1. Compute changed file list (newline-delimited).
2. Run:
   - `python quality-gate/quality_gate.py --root . --paths-from <changed.txt> --json`
   - `python quality-gate/quality_gate.py --root . --paths-from <changed.txt> --verbose`

The bundled GitHub Actions workflow template lives at `quality-gate/workflows/quality-gate.yml`.

## Auditing & Backlog (tech debt paydown)

- Find the top offenders:
  - `python quality-gate/quality_gate.py --mode audit --root . --top 20`
- Export metrics to CSV (PRS + issues + heuristic review score):
  - `python quality-gate/tools/export_quality_csv.py`

## Configuration (`/.quality-gate.json`)

Place overrides in your repo root:

- Exclude generated artifacts (recommended)
- Adjust thresholds per repo
- Enable/disable optional rule packs

See `quality-gate/examples/` for ready-to-copy configs.

## Team operating rules (recommended)

- Use the quality gate output as the **merge gate**: no “waive” for errors.
- For larger changes, include a short micro-spec in the PR:
  - files to touch, slop risks, and test plan.
