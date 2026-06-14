# Cathedral Keeper Adoption Guide

Cathedral Keeper (CK) is an **architecture governance module** you can drop into any repo.
It complements `quality-gate/` by running higher-order checks (boundaries/cycles/async risks) and producing evidence-first findings.

## Install

1. Copy `cathedral-keeper/` to your repo root.
2. (Optional) Add a repo config override at `/.cathedral-keeper.json`.
3. Run:

```bash
python cathedral-keeper/ck.py analyze --root .
```

## Modes

- Full repo sweep:
  - `python cathedral-keeper/ck.py analyze --root . --mode repo`
- Diff-based (CI-friendly):
  - `python cathedral-keeper/ck.py analyze --root . --mode diff --base origin/main`

## How to keep it trustworthy (anti-slop rules)

- Findings must include **evidence** (file + line + snippet).
- Prefer deterministic analyzers (AST/graph/regex) over LLM judgments.
- If/when you add LLM checks, they should be optional and scoped to touched files only.

## Integrating with Quality Gate

If `quality-gate/` exists, CK can ingest its JSON output and include it in a consolidated report.

By default, CK expects `quality-gate/quality_gate.py` via an **integration** (optional, not a dependency).
Override via `/.cathedral-keeper.json`:

```json
{
  "integrations": {
    "quality_gate": { "enabled": true, "qg_path": "quality-gate/quality_gate.py" }
  }
}
```

## Integrating with other SDLC tooling

Use the `external_findings_json` integration to run any tool that emits CK Findings JSON:

```json
{
  "integrations": {
    "external_findings_json": {
      "enabled": true,
      "argv": ["python", "tools/my_sdlc_exporter.py"],
      "cwd": "."
    }
  }
}
```

Your exporter reads:
- `CK_ROOT` (repo root)
- `CK_PATHS_FILE` (newline-delimited list of paths to analyze)

And prints JSON:

```json
{ "findings": [ { "policy_id": "...", "title": "...", "severity": "high", "confidence": "high", "why_it_matters": "...", "evidence": [ { "file": "...", "line": 1, "snippet": "..." } ] } ] }
```
