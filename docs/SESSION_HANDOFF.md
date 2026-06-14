# Session Handoff — Onto_Wiz (resume pointer)

> **Authoritative status is `docs/PROJECT_STATUS.md`** (single source of truth) and
> the visual companion `docs/LOOP_DASHBOARD.html`. This file is just the resume
> pointer + open threads, so context can be cleared and work picked up cleanly.
> Last updated: 2026-06-14.

## Where things stand (verified)

- **`bash scripts/verify-audit.sh` → PASS** — all 6 owned gates green:
  **191 package tests + 308 src tests; coverage 98.2%**; ruff/mypy(Tier A)/boundary
  clean; CK new-code clean (6 tracked legacy-debt findings).
- **Served Domain Intelligence Catalog (2026-06-14, Loops C1–C10):** the catalog is
  real and served from the live registry — `catalog_index`/`catalog_search`,
  `pack_functions`, `artifact_view`, `pack_diff`, `CommentStore`, `UsageStore`+`catalog_stats`
  (all Tier-A runtime) + REST doors + a page at `GET /` + RBAC-lite. Spec:
  `docs/specs/CATALOG_LOOPS.md`; evidence in `PROJECT_STATUS.md` → "Domain Intelligence
  Catalog — served". (See open thread 00 for follow-ups.)
- **Functionalized commercial pack (2026-06-13, Loops L1–L5):** one licensable pack
  sub-divided by `TagDimension.FUNCTION`; `context_for_function()` serves a slice;
  drop-a-file modules under `ontology/commercial/` (added `forecasting.yaml`); recompiled
  to `commercial_analytics@0.3.0` (24 artifacts, sealed). (See open thread 0.)
- **End-to-end living loop runs (MVP, 2026-06-13):** consult → UsageEvent →
  Forge mission → `orchestrate.evolve_pack` → next pack version that serves the
  new knowledge. Proven offline (`test_living_loop.py`) + live
  (`scripts/run_living_loop.py`): a cyberattack-gap query produces
  `commercial_analytics@0.2.0` (21 artifacts, sealed) whose answer is now grounded
  in the new `rule_cyber_disruption`. New seam: `evolve_pack`, `consume.consult`,
  `benchmark.answer_with_pack`. See the "End-to-end living loop" section in
  `PROJECT_STATUS.md` for the honest MVP boundaries.
- **Live agent-lift benchmark + suite hardened + pack fine-tuned** (2026-06-12):
  real pack measured against a live LLM (Haiku 4.5) via the faithful CTX router
  loop. Suite = **26 cases** (19 heuristics + 7 traps). A 10-loop fine-tuning pass
  closed seed data gaps (rule `description`, `conditions`/`priority`, adjacency
  `anti_patterns`, and **15 dropped entity relationships**) and fixed the one
  genuine with-pack failure (`pathway_exclusion`, was conflated with
  `guideline_driven_shift`). Added **temperature-0** determinism so lift is
  attributable, not blind-sampling noise. Result (temp 0, reproducible):
  **with-pack 26/26**, blind 0.692, **lift +0.308**; `pack.yaml` `agent_lift: 0.308`.
  See the "Live agent-lift benchmark" section in `PROJECT_STATUS.md`.
- **All 6 delivery loops complete:** 10 core loops (F0–F4: artifact model, Delta
  bridge, pack factory, headless REST+MCP, mining/steward/eval/feedback) + Loop 5
  UX-1..4 (mission framework, registry detail, lineage, ForgeRating+consensus).
- **3 red-team rounds done**, all findings fixed and re-verified. See the two
  red-team sections in `PROJECT_STATUS.md` for the full ledger. Headline fixes:
  governance invariant enforced at the `transition()` primitive; path-traversal
  closed (REST+MCP); CTX compiler now emits real knowledge (BODY) and survives a
  bracket-injection round-trip; **the factory composes end-to-end** via
  `ontowiz_factory.orchestrate.mine_govern_compile` (e2e test: raw text → mined →
  governed → ACTIVE → compiled → served); **pack signing is real** (SHA-256
  integrity seal, `verify_pack`); query-relevance ranking; `backing_deltas`
  populated.

## Key artifacts (cumulative)

- Packages: `packages/ontowiz-{spec,ctx,runtime,serve,core,factory}` (Tier A ships,
  Tier B = secret sauce; A↛B enforced by `tools/check_boundaries.py`).
- **Catalog (Tier-A runtime), C1–C10:** `ontowiz_runtime/{catalog,artifact_view,comments,diff,telemetry}.py`;
  `ontowiz_serve/{catalog_page,roles}.py` + ~14 new REST routes in `api.py` (registrar functions).
  Spec: `docs/specs/CATALOG_LOOPS.md`.
- **Functionalization (L1–L5):** `function:`/`therapy_area:` per rule in `ontology/commercial.yaml`;
  `ontology/commercial/forecasting.yaml`; seed multi-module reader + `context_for_function`;
  `FORECASTING_EVAL_CASES` in `commercial_eval_suite.py`.
- Earlier in `ontowiz-factory`: `missions.py`, `forge.py`, `orchestrate.py`, `consume.py`.
  In `ontowiz-runtime`: `registry_view.py`, `lineage.py`. Serve: `/detail`, `/explain`; MCP `dispatch`.
- Compiled packs: `packs/commercial_analytics/{0.1.0,0.2.0,0.3.0}/` (all sealed). 0.3.0 = functionalized
  + forecasting (24 artifacts, carries `domain`). 0.2.0 = living-loop cyber evolution.
- HTML in `vision/`: DOMAIN_INTELLIGENCE_VISION, FOUNDATION_DESIGN, UX_DESIGN_AND_FORGE_SPEC,
  PHARMA_ONTOLOGY, **ONTOWIZ_MICROSITE**, **DOMAIN_INTELLIGENCE_CATALOG** (interactive vision mock;
  the served real version is `GET /`). Dashboard: `docs/LOOP_DASHBOARD.html`.

## Open threads (pick up here)

00. **✅ DONE (2026-06-14) — served Domain Intelligence Catalog (Loops C1–C10 all green).**
    The `vision/DOMAIN_INTELLIGENCE_CATALOG.html` mock is now real, served from the live
    registry. See "Domain Intelligence Catalog — served" in `PROJECT_STATUS.md` and the spec
    `docs/specs/CATALOG_LOOPS.md`. New Tier-A runtime surfaces (`catalog_index`, `catalog_search`,
    `pack_functions`, `artifact_view`, `pack_diff`, `CommentStore`, `UsageStore`+`catalog_stats`)
    + REST doors + a served page at `GET /` + RBAC-lite. 191 pkg tests, verify-audit PASS.
    Open follow-ups: port these routes into the Next.js `frontend/` app; swap the JSON
    comment/usage MVP stores for a DB; live-benchmark the forecasting slice (0.3.0 `agent_lift`
    still unmeasured); bind RBAC to a real auth principal.

0. **✅ DONE (2026-06-13) — functionalized the commercial pack (L1–L5 all green).**
   See "Functionalized domain packs" in `PROJECT_STATUS.md` for the evidence. The
   pack is now sub-divided by `TagDimension.FUNCTION`; `context_for_function()`
   serves a single slice; a `forecasting` module was added via drop-a-file; recompiled
   to `commercial_analytics@0.3.0` (24 artifacts, sealed); `verify-audit` PASS. Open
   follow-up: live-benchmark the forecasting slice (0.3.0 ships `agent_lift` unmeasured).
   _Original plan, for reference:_
   Decision: `commercial_analytics` stays **one licensable pack**, sub-divided by
   `TagDimension.FUNCTION` (Stage 1, tags-first); functions version together;
   extract a function into its own pack only later (Stage 2 needs the overlay/
   compose engine, which is currently a schema-only placeholder — `layers`/
   `depends_on` are NOT wired; `get_context` serves a single pack). Agreed 5-loop plan:
   - **L1** add a `function:` field per rule in `commercial.yaml`; seed tags each
     artifact `FUNCTION=<x>` (+ existing `analytics_domain`; + `therapy_area=oncology`
     for the 3 onc rules). Proposed taxonomy mapping today's 19 heuristics:
     `base`={safety_signal, supply_disruption}; `market_access`={budget_crisis,
     pa_access_barrier, formulary_exclusion, copay_accumulator, reimbursement_squeeze,
     340b_erosion, rebate_trap, competitor_lockout}; `brand_performance`={demand_erosion,
     launch_stall, channel_shift, field_execution_gap}; `competitive_intel`=
     {competitive_displacement, biosimilar_erosion}; oncology overlay (therapy tag,
     not a function)={guideline_shift, biomarker_testing_gap, pathway_exclusion}.
   - **L2** generalize the seed to read **multiple module YAMLs** (`ontology/commercial/*.yaml`),
     each declaring its function, merged into one pack (drop-a-file expansion).
   - **L3** tag-filtered serving helper + test: `get_context(tags=[function:market_access])`
     serves only that slice.
   - **L4** author one new function module — `ontology/commercial/forecasting.yaml`
     (LOE/biosimilar erosion curve, demand sensing, analog launch trajectory, scenario
     sensitivity) to prove expansion.
   - **L5** recompile, benchmark the new slice, gates, record.
   Two open sub-calls (defaults chosen, user can override): taxonomy = the 4 functions
   above; first new module = `forecasting`.
1. **Living-loop MVP completion** (the 3 honest gaps from the "End-to-end living loop"
   section): drive the correction/re-curation path (`feedback_to_deltas` → REVIEW)
   end-to-end; auto-bump version + auto-benchmark the evolved pack (today `0.2.0`
   ships `agent_lift: null`); persist `UsageEvent` telemetry (in-process today).
2. **Benchmark next steps**: model sweep (Sonnet — lift should shrink as base model
   improves); periodically refresh/expand the 26-case suite to avoid overfit.
3. **Microsite IP claims** — `vision/ONTOWIZ_MICROSITE.html` + `FOUNDATION_DESIGN.html`
   still present-tense claim packs are "encrypted / license-gated"; those are roadmap
   (signing is real). Soften the HTML to match `pack_manifest.py`. Do this WITH the
   encryption/license loop, not before.
4. **Task #5** — pay down re-homed `ontowiz-core` PRS debt (6 legacy modules) + mypy-strict Tier B.
5. **Task #21** — AST boundary check, enable CK `python_boundaries`, add
   `packages/tests_governance` to testpaths, + a sealed Tier-A-only client build (boundary is lint-time only today).
6. **Other deferred** (PROJECT_STATUS round-2/3): real BPE token counter; mining beyond
   regex; EWMA sample-count; L3 directory linear scaling past ~60 artifacts (matters once functions grow the pack).

## How to resume / verify

```bash
bash scripts/verify-audit.sh        # must PASS before marking anything done
```
- **Editable installs:** spec/ctx/runtime/core are pip-installed; **`ontowiz-factory` and
  `ontowiz-serve` are NOT** — run `pip install -e packages/ontowiz-factory --no-deps`
  before invoking the scripts (pytest works regardless via `packages/conftest.py`).
- **Live LLM scripts** (read `ANTHROPIC_API_KEY` from `./.env`, model `claude-haiku-4-5`):
  `python scripts/run_agent_lift_benchmark.py [--dry-run]` (writes pack evals, temp 0);
  `python scripts/run_living_loop.py` (consume→mission→evolve→serve demo; wrote
  `packs/commercial_analytics/0.2.0/`).
- **Pack regenerate** (after seed/compiler changes):
  `build_commercial_pack('ontology/commercial.yaml', 'packs')`.
- **`.env`** holds a live `ANTHROPIC_API_KEY` at repo root — keep out of any commit.

## Working discipline (from CLAUDE.md)
Loop: mini-spec → reuse-first → TDD red → build → gates → verify → record. Status
only in `PROJECT_STATUS.md`. "Written" ≠ "done" — a unit is DONE only when
verify-audit passes AND evidence is recorded. Tier A never imports Tier B.
