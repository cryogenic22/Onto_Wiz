# Cathedral Keeper

Cathedral Keeper (CK) is a portable **architecture governance** module: policy-as-code + evidence-first findings.

It is designed to complement (not replace) `quality-gate/`:
- `quality-gate/`: fast deterministic merge gate (file-level PRS + rule checks)
- **Cathedral Keeper**: higher-order architecture checks (boundaries, cycles, async risks) + consolidated reporting

## Integrations (optional, not dependencies)

CK can integrate with SDLC tools by contract, without depending on them:
- `quality_gate` integration (ingests PRS/issue JSON if `quality-gate/` exists)
- `external_findings_json` integration (run any command that outputs CK Findings JSON)

## Requirements

- Python 3.10+
- No network access required (stdlib only)

## Quick Start (this repo)

```bash
python medcontent-ai-platform/cathedral-keeper/ck.py analyze --root .
```

Outputs:
- Markdown report: `.quality-reports/cathedral-keeper/report.md`
- JSON report: `.quality-reports/cathedral-keeper/report.json`

## Modes

- Repo sweep (full): `ck.py analyze --root . --mode repo`
- PR/diff sweep (changed-files-only): `ck.py analyze --root . --mode diff`
- Disable quality-gate ingestion: `ck.py analyze --root . --no-qg`

## Notes

- Architecture/value analysis: `medcontent-ai-platform/cathedral-keeper/ANALYSIS.md`

## Portability

To reuse in another repo:
1. Copy `cathedral-keeper/` to your repo root.
2. Add a repo override config at `/.cathedral-keeper.json` (optional).
3. Run `python cathedral-keeper/ck.py analyze --root .`.
