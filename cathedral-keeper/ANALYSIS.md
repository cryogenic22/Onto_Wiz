# Cathedral Keeper (CK) — Architecture Governance Analysis

## Recommendation: CK is a separate module (not part of `quality-gate/`)

`quality-gate/` is optimized for **fast, deterministic, per-file merge gating** (PRS + rule checks).

`cathedral-keeper/` is optimized for **architecture/regression detection** across modules (dependency edges, boundary drift, async hygiene, reliability contracts) and for producing an evidence-first report that can be used in:
- PR diff checks (fast subset)
- scheduled repo sweeps (trend + hotspots)
- agent workflows (agents call CK before generating large changes)

Keeping these separate avoids turning the merge gate into a slow “framework”, while still allowing optional integration (CK can ingest quality-gate output).

## What CK adds (beyond PRS)

CK focuses on “architecture regression” failure modes that appear in both human and AI-written code:
- **Reliability regressions**: network calls without timeouts (hangs, stuck workers, non-deterministic latency).
- **Throughput/latency regressions**: blocking calls inside `async def` (event loop stalls under load).
- **Environment coupling**: `sys.path` manipulation (import ambiguity, local-only behavior, packaging drift).

CK is intentionally:
- **stdlib-only** (works offline; no pip dependency footprint)
- **evidence-first** (findings include file + line anchors)
- **policy-driven** (repo overrides via `/.cathedral-keeper.json`)
- **integrable** (can consume other tools’ JSON findings without depending on them)

## Evidence: “47 findings without QG” (this repo)

From `.quality-reports/cathedral-keeper/report_no_qg.json`:
- Total findings: **47**
- Policy breakdown:
  - `CK-PY-SYSPATH`: **21**
  - `CK-PY-ASYNC-BLOCKING`: **14**
  - `CK-PY-REQUESTS-TIMEOUT`: **12**
- Severity breakdown:
  - `high`: **26**
  - `medium`: **21**

Top concentration (by file):
- `medcontent-ai-platform/scripts/test_literature_review_pipeline.py` (8)
- `medcontent-ai-platform/backend/services/document/services/storage.py` (4)
- `medcontent-ai-platform/scripts/export_session_no_qc.py` (4)
- `medcontent-ai-platform/agents/src/api/v1/app.py` (3)

## Does CK identify real architecture regression risks?

Yes — these findings are not “style nitpicks”; they correlate strongly with production regressions:

### Missing request timeouts (`CK-PY-REQUESTS-TIMEOUT`)
Risk:
- threads/worker slots get stuck indefinitely during upstream degradation
- latency becomes unbounded (hard to SLO/monitor)

Prevent:
- enforce a single HTTP client wrapper (or shared helper) that always sets `timeout=`
- add a gate rule (CK or QG) that blocks `requests.*` without timeout

### Blocking calls in `async def` (`CK-PY-ASYNC-BLOCKING`)
Risk:
- event loop stalls → requests pile up → cascading timeouts and poor throughput

Prevent:
- require “async-safe IO”: use async libraries or `asyncio.to_thread()` for blocking work
- add a CI diff-mode CK check for new async-blocking patterns

### `sys.path` manipulation (`CK-PY-SYSPATH`)
Risk:
- import behavior differs between dev/CI/prod; “works on my machine” failures
- hidden coupling between modules and launch directories

Prevent:
- fix packaging/import roots instead of runtime path edits (explicit packages, entrypoints)
- ban `sys.path.insert/append` except in clearly-scoped CLI bootstrap code (and document it)

## How to make teams/agents prevent regressions (process)

Minimum standard that stays low-friction:
1. **Pre-commit / local**: run `quality-gate` on staged files.
2. **PR gate**: run `ck analyze --mode diff` on changed files (fast).
3. **Nightly**: run `ck analyze --mode repo` to track drift and hotspots.
4. **Agent instruction**: agents must run CK on touched paths before generating large patches; treat findings as hard constraints (especially `high` severity).

## Integration posture (non-dependent)

CK should remain independent, but can integrate via contracts:
- ingest quality-gate JSON (optional)
- ingest any external SDLC tool JSON via `external_findings_json` integration

This makes CK portable to other repos without requiring them to adopt a specific gate implementation on day 1.

