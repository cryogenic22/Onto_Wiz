# Onto_Wiz — Project Status (single source of truth)

> **This file is the authoritative status. Status does NOT live in chat or memory.**
> A row is `✅ VERIFIED` only with pasted evidence and a passing
> `scripts/verify-audit.sh`. "Written" / "committed" ≠ "done" (see ADR-015,
> adopted from Content_medical_hub ADR-0001).

_Last audit (2026-07-10, after **F0.2 — Governance persistence** (Foundry build, Loop 0, backend lane): the delta lifecycle — proposed deltas, approvals, audit trail, SME contributions — now persists on the `db.py` SQLite seam via a new **Tier A** `GovernanceStore` (tables `deltas`/`delta_events`/`approvals`/`audit_log`/`contributions`), mirroring the `CommentStore` pattern (no new persistence machinery). **Restart-survival proven**: approve a delta → fresh store instance on the same DB → approval + audit survive. Tier A holds (no Tier B import); R1's one pipe untouched. 218 package + 312 src/gov tests green; coverage 98.49%; `bash scripts/verify-audit.sh` → PASS._
_Prior audit (2026-07-09, after **F0.1 — CI gate set = R3** (Foundry build, Loop 0, backend lane): frontend Vitest wired into CI as a **blocking** step (`npm run test:cov`), quality-gate + slop_checker demoted to advisory, and the `.env`/API-key hygiene **verified** (never committed → history purge is a no-op). New governance test `tests/test_ci_gate_set.py` machine-checks the blocking/advisory split. 209 package + **312** src/gov tests green; coverage 98.38%; `bash scripts/verify-audit.sh` → PASS. Frontend gate: 20 Vitest tests, 96.1% stmts (≥85%)._
_Prior audit (2026-06-15, after the **catalog frontend port + DB + RBAC** — Loops F-DB1..3, F-RB1..2, F-FE0..5: SQLite store engine behind a `Database` wrapper, JWT/bcrypt RBAC bound to a real Bearer principal, and the Domain Intelligence Catalog ported into the Next.js `frontend/` app): 209 package + 308 src tests green; coverage 98.38%; ruff/mypy(Tier A)/boundary clean; CK new-code clean (6 tracked legacy-debt findings). `bash scripts/verify-audit.sh` → PASS. Frontend gate (new, ADR-017): 25 Vitest tests, 96%+ coverage on catalog code, `tsc`/`eslint`/`next build` clean._
_Prior audit (2026-06-14, after the **served Domain Intelligence Catalog** — Loops C1–C10: catalog index/search, function-slice + artifact surfaces, a live-served catalog page, comments, RBAC-lite, version diff, telemetry, + a forecasting eval suite): 191 package + 308 src tests green; coverage 98.2%; ruff/mypy(Tier A)/boundary clean; CK new-code clean (6 tracked legacy-debt findings). `bash scripts/verify-audit.sh` → PASS._
_Prior audit (2026-06-13, after **functionalizing the commercial pack** — L1–L5: per-function tags, multi-module seed, tag-sliced serving, a new forecasting module): 163 package + 308 src tests; the one licensable `commercial_analytics` pack is sub-divided by `TagDimension.FUNCTION` and serves any function slice in isolation; recompiled to `0.3.0` (24 artifacts, sealed)._
_Prior audit (2026-06-13, after the **end-to-end living-loop MVP** — consume→signal→mission→evolve→serve): 151 package + 308 src tests green; coverage ~98%. Pack: `agent_lift 0.308`, with-pack 26/26; living loop produces `commercial_analytics@0.2.0` from a usage gap._

## Build status

| Phase | Item | Status | Evidence |
|---|---|---|---|
| F0 | Scaffold monorepo + vendor CTX + contracts seam | ✅ VERIFIED | CTX imports OK; Tier-A wiring smoke (now covered by package suite) |
| 0 | Harden delivery harness for `packages/` | ✅ VERIFIED | gates wired (CK include, pre-commit boundary hook, Make targets); `DELIVERY_PROTOCOL.md` |
| F1 #2 | Unify artifact model in `ontowiz-spec` (19 kinds) | ✅ VERIFIED | 50 tests, 98.56% cov (library.py 98%), ruff/mypy/boundary clean, 0 CK pkg findings, YAML round-trip per kind |
| F1 #3 | Re-home `src/core` → `ontowiz-core` | ✅ VERIFIED | impl moved to `ontowiz_core` (Tier B); `src/core` now 9 re-export shims; 312 tests (308 src + 4 core) green; 931 ruff fixes applied to legacy + 6 hand-fixes; ruff/boundary clean; verify-audit PASS |
| F1 #4 | Delta bridge (transitions only via Deltas) | ✅ VERIFIED | 8 bridge tests, `bridge.py` 100% cov; transition only via APPROVED/MERGED Delta; `GovernanceError` on ungoverned/mismatched; verify-audit PASS. **F1 COMPLETE.** |
| F2 | Pack compiler + registry + runtime store (Loops 1–3) | ✅ VERIFIED | compiler, write/load round-trip, PackRegistry; real `commercial_analytics@0.1.0` (20 artifacts) compiled to `packs/` |
| F3 | Headless serve — REST + MCP (Loops 4–6) | ✅ VERIFIED | `get_context()` end-to-end on a loaded pack; FastAPI `/v1/context`+`/v1/packs`; MCP `context/get`·`pack/list`·`pack/query` |
| F4 | The product loops (Loops 7–10) | ✅ VERIFIED | mining→PROPOSED Deltas; steward signals→missions + quality score (weighted blend); eval gate (word-boundary judge) + **gateable** agent-lift; feedback EWMA + corrections→Deltas/EvalCases. _Lift is computed and can gate (`gate(..., lift=, min_lift=)`); it is reported, not enforced by default — see round-2 fixes._ |
| F5 UX-1 | Mission framework — Forge submit contract + daily feed | ✅ VERIFIED | `ontowiz_factory.missions`: `daily_missions()` (reuses steward); `submit_mission()` enforces delta+eval+confidence ("no artifact+eval ⇒ doesn't ship"); rejects missing eval/bad confidence; PROPOSED Delta + gold EvalCase. 6 tests; Tier-B IP (off the Tier-A read API by design). verify-audit PASS. |
| F5 UX-2 | Pack Registry detail surface (artifact explorer + gaps) | ✅ VERIFIED | `ontowiz_runtime.pack_detail()` (Tier A): per-artifact served/eval-coverage flags + gaps list (served-but-untested → Forge missions); `GET /v1/packs/{n}/{v}/detail`. 3 lib + 1 API tests. verify-audit PASS. |
| F5 UX-3 | Knowledge Workbench lineage ("explain this definition") | ✅ VERIFIED | `ontowiz_runtime.explain_concept()` (Tier A): trace a concept → governed artifacts with provenance (sources, confidence, served, eval coverage, governance steps); `GET /v1/packs/{n}/{v}/explain?concept=`. 3 lib + 1 API tests. verify-audit PASS. |
| F5 UX-4 | ForgeRating + multiplayer consensus | ✅ VERIFIED | `ontowiz_factory.forge`: `forge_rating()` 5-signal Elo (dissent weight strictly highest, asserted; signals clamped to [0,1]; weight-0 fully excludes a contribution); `resolve_consensus()` → consensus+dissent+confidence; `consensus_to_exception_rule()` → governable ExceptionRule. 7 tests; Tier-B. **Loop 5 backend contracts COMPLETE** (interactive web UI is conceptual — see `vision/ONTOWIZ_MICROSITE.html` demo; production UI not built). verify-audit PASS. |

## Red-team pass (2026-06-11) — adversarial review + gap fixes

Four code-grounded reviewers (boundary/IP · governance · test-honesty · correctness) audited all work to date. Real gaps found and **fixed** (each re-verified by `verify-audit`):

| Finding | Severity | Fix |
|---|---|---|
| `ArtifactBase.transition()` could promote to ACTIVE/VERIFIED with no governing delta — "governance" was convention, not invariant | HIGH | `transition()` now raises `UngovernedTransitionError` unless a `delta_id` is supplied for governed states (Tier-A primitive-level enforcement) + test |
| `seed.py` activated seeds via a direct ungoverned `transition()` (delta_id=None) into the shipped pack | MED | Seeds now activate through a system-approved Delta via the bridge; every ACTIVE seed carries an auditable `delta_id` |
| `dev_mode` was client-settable over REST → any caller could pull REVIEW/VERIFIED artifacts | MED | `dev_mode` gated server-side (`allow_dev_context` / `ONTOWIZ_ALLOW_DEV_CONTEXT`); default refuses + test |
| `forge_rating` didn't clamp signals — un-normalised input escaped the 1000–2000 range | MED | signals clamped to [0,1] + test |
| `submit_mission` EvalCase id collided on re-submission; no existing/artifact id check | MED | eval id discriminated by submitter; id-mismatch rejected + tests |
| Two ForgeRating tests passed under mutation ("dissent highest", "weight-0 anti-gaming") | HIGH (honesty) | both rewritten to fail under mutation; ranking/empty/clamp coverage added |
| `forge.py` docstring overstated decay/consensus-weighting as implemented | LOW (honesty) | docstring corrected — weight is consumed, not derived (derivation out of scope) |

Open recommendations (defense-in-depth, not gaps — boundary is enforced 3 ways today): upgrade `check_boundaries.py` regex → AST to catch dynamic/aliased imports; enable Cathedral Keeper's `python_boundaries` policy; add `packages/tests_governance` to routine `testpaths`.

## Red-team round 2 (2026-06-11) — deep engine/security audit + fixes

A second, deeper pass (verify-fixes · CTX compiler/hydration · F4 loop math · serve/MCP security) found defects the first pass missed. All **fixed** and re-verified:

| Finding | Severity | Fix |
|---|---|---|
| **Path traversal** in `PackRegistry.load` — `name`/`version` unvalidated (REST + MCP) could escape `packs_root` | CRITICAL | resolved-path containment check; `..`/absolute → "pack not found" + test. Artifact-id charset validator (`^[A-Za-z0-9_-]+$`) closes the id-as-filename vector |
| **Compiled CTX shipped no knowledge** — sections held only metadata (id/name/kind), not the artifact's content | CRITICAL | compiler emits a `BODY` of the artifact's content fields; round-trip test asserts the formula reaches the context |
| **Gate/directory decoupling** — system prompt built from full doc, so a gated-out artifact was still listed/hydratable | HIGH | directory rebuilt from the *eligible* set only + test |
| **Section-name collision / field-newline injection** (C2/C3) | HIGH | collision raises at compile; field values collapsed to one safe line (cannot forge a section) + tests |
| **transition() bypass** — blank `delta_id`, constructor `lifecycle=ACTIVE`, stale YAML | HIGH | `delta_id` stripped; model-validator requires a governing delta to *be* ACTIVE/VERIFIED; on-disk pack regenerated with real delta_ids + tests |
| **agent-lift not gated** — `gate()` ignored lift; docs sold a "lift CI gate" | HIGH (honesty) | `gate(..., lift=, min_lift=)` blocks a zero-lift pack; docs corrected to "reported, gateable" + test |
| **score_answer** substring false-positives + vacuous empty case inflating pass-rate | HIGH | word-boundary matching; empty case scores 0 (non-vacuous); `correction_to_evalcase` rejects empty + tests |
| **pack_quality_score** multiplicative collapse + free 1.0 for unprovable packs | HIGH | weighted blend; `testable=0` → coverage 0 |
| **MCP** leaked tracebacks/paths + no dev gate | HIGH | `dispatch()` error boundary (clean JSON); `allow_dev_context` parity with REST + tests |
| **REST** 500 on bad tag dimension; no field length caps | MED | bad dimension → 422; `query`/`pack_*` length-capped + test |

Honestly deferred as **MVP limitations** (documented, not silently shipped): mining is regex-only (misses `"if X, Y."` with no "then"); EWMA reliability carries no sample-count (1 event ≈ many); `tokens_estimate` is a word count, not BPE; `model_copy(update=lifecycle)` is a residual in-process bypass (no live caller). The CTX `BODY` is a flattened one-line projection of content (structure-lossy but complete).

## Red-team round 3 (2026-06-11) — engine/IP/end-to-end audit + fixes

A third pass (CTX engine internals · IP-protection reality · Windows security/regressions · end-to-end composition) found the deepest issues yet. All **fixed** and re-verified:

| Finding | Severity | Fix |
|---|---|---|
| **CTX parser data-loss** — an unbalanced `[` in a BODY value made the parser swallow every following section (silent loss of governed knowledge) | CRITICAL | compiler neutralises brackets/backticks + renders content cleanly (no Python-repr); round-trip test asserts both sections survive |
| **The factory didn't compose** — mine→govern→compile was unwired; only the hand-seeded path produced a pack (mined DRAFT artifacts compiled to 0) | HIGH | new `orchestrate.mine_govern_compile` welds the chain; **e2e test proves raw text → mined → governed (approved) → ACTIVE → compiled → served** |
| **Pack signing was vaporware** — `signed`/`pack.sig` claimed in docs, never produced | HIGH (honesty) | `write_pack` writes a SHA-256 **integrity seal** (`pack.sig`), `verify_pack` checks it, `signed=True`; tamper-detection test. (Integrity, not PKI authorship — labelled as such) |
| **Encryption / license binding** claimed as existing in FOUNDATION/microsite | HIGH (honesty) | **not implemented** — corrected to ROADMAP in `pack_manifest.py` field docs; packs ship as plaintext today |
| **"Relevance gate" was query-blind** — selection used only tags+lifecycle; identical output for any query | HIGH (honesty) | `get_context` now ranks the eligible set by query-term overlap (directory leads with the most relevant; LLM-as-router still chooses) + test |
| **`backing_deltas` always empty** — trust envelope implied delta provenance it didn't carry | MED | populated from each eligible artifact's governing `delta_id`; surfaced in REST + test |
| **Path guard `target==base`** degenerate case; reserved device-name ids (`con`/`nul`) | LOW | strict-descendant check + empty-component reject; reserved-name denylist in id validator + tests |

Still honestly deferred (documented, not claimed done): **encryption-at-rest and per-client license binding** (plaintext today); a real **BPE token counter** (estimates use word-count); the CTX L3 directory **scales linearly** past ~60 artifacts (the "<500 tokens regardless of size" claim is per-page, not per-corpus); the IP boundary is **lint-time, no sealed client build artifact** yet (Task #21). _(The live-LLM `agent_lift` benchmark — previously listed here — is now done; see below.)_

## Live agent-lift benchmark (2026-06-11/12) — the headline number, measured + tuned

The deferred "run `agent_lift` against a live LLM on the real pack" item is **done**. The benchmark runs the *faithful* CTX product path, not a shortcut: with-pack answers come from the genuine LLM-as-router loop (L3 directory in the system prompt → model calls the `ctx_hydrate` tool → the pack's L2 section body is returned → model answers); blind answers ask the same question with no pack and no tools. Per-case scoring reuses the deterministic word-boundary judge in `ontowiz_factory.evals`; lift is the mean per-case score delta.

| What | Value (after fine-tuning, **temperature 0**) |
|---|---|
| Model | `claude-haiku-4-5-20251001` (live Anthropic API) |
| Suite | **26 cases** — all 19 governed heuristics + 7 distractor traps (`commercial_eval_suite.py`) |
| Blind pass-rate | **0.692** (18/26) |
| With-pack pass-rate | **1.000** (26/26) |
| **Agent lift (mean Δ)** | **+0.308** — reproduces exactly across repeat temp-0 runs |
| Gate | **passed** (`min_lift=0.05`) |

`packs/commercial_analytics/0.1.0/pack.yaml` carries `agent_lift: 0.308`, `eval_cases: 26`, `pass_rate: 1.0`, `gate_passed: true`, `last_run_at` stamped; re-sealed (`verify_pack` → True). The manifest writer re-seals after the governed edit (`compiler.reseal_pack` + a `verify_pack` regression test).

**The suite is hard by construction** (replacing the first 9-case probe): one+ case per heuristic for full-pack coverage; each `must_contain` is the *specific governed term* (verified present in the pack), and the term never appears in its own question (test-enforced) so the model must supply it; 7 traps put a plausible wrong cause on the surface. The pack's value concentrates in the ~8 counter-intuitive discriminations a capable model misses blind (copay-accumulator, competitor-lockout, demand-erosion, pathway-exclusion, biomarker-testing, demand-over-access, rebate-over-price-war …); the rest Haiku already handles, so the pack adds 0 there.

### Fine-tuning pass (2026-06-12, 10 loops on data gaps + measurement)

The first run surfaced one genuine with-pack failure — `pathway_exclusion` scored 0.00 *with* the pack because the model conflated it with the adjacent `guideline_driven_shift` (both share the `Clinical:Guideline` condition). Root cause: **the seed was discarding the ontology data that disambiguates them.** Closed these data gaps in `seed.py` (each verified by the pack test):

| Gap (dropped by the seed) | Fix |
|---|---|
| Rule `description` (the disambiguating prose) | → `trigger_context` (rides into the hydrate BODY) |
| Adjacent-heuristic confusion (pathway/guideline, lockout/budget, channel/demand, formulary/field, safety/competitive, supply/demand) | explicit `HeuristicAntiPattern` ("this is NOT X, because …") per cluster |
| Rule `conditions` + `priority` | → `trigger_signals` + `scope.priority` |
| **All 15 entity `relationships`** (entirely dropped) | folded onto each source `EntityRecord.relationships` |

**Result, attributable and reproducible:** with-pack pass-rate **0.923 → 1.000** — `pathway_exclusion` now scores **1.00** (confirmed in isolated re-runs), and the `competitor_lockout` "failure" was a **mis-calibrated suite forbidden term** (`must_not_contain=["crisis"]` penalised the correct "not a budget crisis" answer), removed.

**Honesty caveat on the lift number:** the enrichment only touches the *with-pack* path, yet at the API's default temperature (~1.0) the *blind* pass-rate swung run-to-run (0.769, then 0.615) — so default-temp lift readings ranged +0.19…+0.39 mostly from blind sampling noise, **not** the pack. Fix: `AnthropicChatAgent` now defaults to **temperature 0** (greedy), so the blind baseline is stable and the lift is attributable; the +0.308 above reproduces exactly. The durable, noise-free claim is **with-pack → 26/26**, not the precise decimal. Remaining caveats: single suite; word-boundary token scoring (inflected synonym can false-miss). Reproduce: `python scripts/run_agent_lift_benchmark.py [--dry-run] [--model M]` (reads `ANTHROPIC_API_KEY` from env or `./.env`).

## End-to-end living loop (2026-06-13) — the MVP comes to life

The factory's loops existed as separate contracts (mining, steward, missions, feedback, eval, compile) but nothing carried a *usage signal* all the way back to an improved, served pack. That closing weld now exists and runs end to end — consciously MVP-robust (offline regression + a live driver), not production-hardened:

```
consult v0.1.0 (gap) → UsageEvent → SME Forge mission (submit_mission, governed add-Delta)
    → evolve_pack (govern → ACTIVE → recompile) → v0.2.0 → re-consult serves the new knowledge
```

New seam, all reusing existing pieces (no logic re-implemented):
- `orchestrate.evolve_pack(base, add-deltas) → next compiled version` — promotes each approved add-Delta via the existing `promote_candidate`, joins the pack's current artifacts, recompiles. The missing weld.
- `consume.consult(query, pack, agent) → answer + TrustEnvelope + UsageEvent` — the reference consumer (the consumption half), sharing the one with-pack router path (`benchmark.answer_with_pack`); the "was the pack useful?" signal reuses CTX's `needs_rehydration`.
- `scripts/run_living_loop.py` — the runnable, **live** demo of the full cycle.

**Proven, two ways.** Offline regression (`test_living_loop.py`, no network): v0.1.0 has no cyber heuristic → SME mission → `evolve_pack` → **v0.2.0 (sealed) serves `rule_cyber_disruption`**, v0.1.0 does not. Live driver: against Haiku 4.5, v0.1.0 answers the cyberattack query generically (top artifacts: formulary/channel); after evolution, v0.2.0's answer is grounded in the new `rule_cyber_disruption` (now the top served artifact), and the registry offers both versions. The pack measurably gained a capability from a single governed interaction.

**MVP boundaries (honest, deferred):** corrections currently take the add path; the transition-to-REVIEW re-curation path (`feedback_to_deltas`) is wired but not yet driven end-to-end. v0.2.0 ships with `agent_lift: null` (not re-benchmarked — evolution and measurement are separate steps). Versioning is manual (caller bumps `0.1.0`→`0.2.0`). No telemetry persistence (`UsageEvent`s are in-process). These are MVP scope choices, not hardening gaps.

## Functionalized domain packs (2026-06-13) — one pack, sliced by FUNCTION

The decided plan (SESSION_HANDOFF open-thread 0) ran end to end as five loops.
`commercial_analytics` stays **one licensable pack** (ADR-012), sub-divided by
`TagDimension.FUNCTION` (tags-first, no overlay/compose engine needed); functions
version together. Each loop was TDD red→green and re-verified by `verify-audit`:

| Loop | What shipped | Evidence |
|---|---|---|
| L1 | Every heuristic carries a `function:` tag (`base` · `market_access` · `brand_performance` · `competitive_intel`); the 3 oncology rules also carry a `therapy_area:oncology` overlay (a therapy tag, not a function); the entity registry is `base`. `function:`/`therapy_area:` are declared per rule in `commercial.yaml` (data, overridable). | `test_functionalize_pack.py` (4 tests): every heuristic has exactly one function; taxonomy mapping; oncology overlay; `gate(tags=[function:market_access])` returns only that slice |
| L2 | Multi-module seed: `artifacts_from_commercial_modules(base, dir)` reads the base ontology + every `ontology/commercial/*.yaml` module (each declaring its `function` once, the default for its rules), merging entities into one de-duplicated registry. `build_commercial_pack` auto-includes a sibling `<base>/` dir — **drop-a-file expansion**, no seed change. | `test_pack_modules.py` (2 tests): modules merge into one artifact set; sibling dir auto-included on build |
| L3 | Tier-A serving helper `context_for_function(query, pack, function)` over the existing tag gate — narrows a loaded pack to one function slice. Exported from `ontowiz_runtime`. | `test_function_serving.py` (3 tests): market-access slice serves only its 8 core + the L3 directory is built from the slice only; full pack still serves everything (slicing is opt-in); **a slice ships a leaner directory + smaller token estimate than the full pack** (the offline functionalization payoff) |
| L4 | New function module `ontology/commercial/forecasting.yaml` (4 forecasting heuristics — LOE erosion curve, demand-sensing divergence, analog launch trajectory, scenario sensitivity — + 2 entities `Forecast`/`ScenarioDriver`). Ships in the real pack via drop-a-file. | `test_forecasting_module.py` (3 tests): forecasting rules ship in the real pack (base intact, all ACTIVE); the forecasting slice serves exactly its 4 rules; module entities merge into the registry |
| L5 | Recompiled to disk: `packs/commercial_analytics/0.3.0/` — **24 artifacts** (1 registry + 19 base + 4 forecasting), sealed (`verify_pack` → True). Slices serve: forecasting = 4, market_access = 9. `verify-audit` → PASS (163 pkg + 308 src tests; 98% cov). 0.1.0/0.2.0 left untouched. | this section + `verify-audit` PASS |

**Honest boundaries (deferred, not hidden):** market_access slices to **9** (the 8 core members + `pathway_exclusion`, which is itself an institutional access barrier with an oncology overlay) — see the function map in `commercial.yaml`. The **forecasting slice is not yet live-benchmarked**: the 26-case agent-lift suite still targets the original 19 heuristics, and `0.3.0` ships `agent_lift` unmeasured (evolution and measurement are separate steps, as with `0.2.0`). The forecasting heuristics' value is asserted offline (slice serves + leaner directory), not yet by a live LLM lift number. Stage-2 extraction of a function into its **own** pack still needs the overlay/compose engine (`layers`/`depends_on` are schema-only today; `get_context` serves a single pack).

## Domain Intelligence Catalog — served, end to end (2026-06-14) — Loops C1–C10

The `vision/DOMAIN_INTELLIGENCE_CATALOG.html` mock is now a **real, served catalog**
backed by the live pack registry. Ten TDD loops (spec: `docs/specs/CATALOG_LOOPS.md`),
all additive, Tier A held (Tier A imports Tier A only), each re-verified by
`verify-audit`. New runtime (Tier A) surfaces + REST doors:

| Loop | Shipped | Surface / route | Tests |
|---|---|---|---|
| C1 | `catalog_index` — one rich entry per pack (domain, versions desc, artifact_count, **function slices w/ counts**, sealed, eval/lift). Added `domain` to the manifest. | `GET /v1/catalog` | 2 + 1 |
| C2 | `pack_functions` — per-function count, served/eval coverage, **slice-vs-full token leanness** (reuses the real serving path). | `GET /v1/packs/{n}/{v}/functions` | 2 + 1 |
| C3 | `catalog_search` — lexical rank over packs + surfaced matching artifacts; function/domain filters. | `GET /v1/catalog/search` | 4 + 1 |
| C4 | `artifact_view` — verdict, anti-patterns, trigger signals, provenance + governance trail (delta ids), eval coverage, raw YAML. | `GET /v1/packs/{n}/{v}/artifacts/{id}` (404 on miss) | 2 + 1 |
| C5 | A self-contained catalog page served from the **live** API (grid → slices → artifact drawer → comments). | `GET /` (HTML) | 1 |
| C6 | `CommentStore` — JSON-backed, role-attributed comments per (pack, version, artifact). | `GET/POST .../artifacts/{id}/comments` | 3 + 1 |
| C7 | RBAC-lite — role→capability map; a curator/manager-only review action (sme/builder/unknown → 403). | `GET /v1/roles`, `POST .../review` | 1 |
| C8 | 4 forecasting `EvalCase`s (suite 26→**30**); each term verified present in its served heuristic and absent from its question. | `commercial_eval_suite.FORECASTING_EVAL_CASES` | 2 |
| C9 | `pack_diff` — added/removed/changed artifacts + per-function deltas between two versions. | `GET /v1/packs/{n}/diff?from=&to=` | 2 + 1 |
| C10 | `UsageStore` + `catalog_stats` — persisted consult telemetry, per-pack consults/hit-rate/by-function. | `POST /v1/usage`, `GET /v1/catalog/stats` | 2 + 1 |

Net: **+28 package tests (163→191), coverage 98.2%**, ruff/mypy(Tier A)/boundary clean,
CK new-code 0. `commercial_analytics@0.3.0` regenerated to carry the `domain` field
(sealed, `verify_pack` → True). `verify-audit` → PASS.

**Honest boundaries (deferred, not hidden):** the comment + usage stores are
**JSON-on-disk MVPs**, not a database (a `.catalog/` dir beside the packs).
RBAC is **header-asserted** (`X-OntoWiz-Role`) with **no identity/auth provider** —
it gates capabilities, not principals. C8 proves the forecasting eval cases are
**well-formed and grounded offline**; the live LLM **agent-lift for `0.3.0` is still
unmeasured** (a separate step). The served page is a real client over the API but is
not the production Next.js app in `frontend/` — porting these routes into that app is
the natural follow-up.

## Catalog frontend port + DB + RBAC (2026-06-15) — Loops F-DB/F-RB/F-FE

The catalog's four open follow-ups (SESSION_HANDOFF thread 00) were taken as one
coordinated unit, by the user's explicit call, adopting architecture/decisions from
the sister repo `market_zero`. Spec: `docs/specs/CATALOG_FRONTEND_PORT.md`. Two
SETTLED decisions were knowingly amended and recorded first: **ADR-016** (SQLite for
dev/test, Postgres for prod via DSN — amends ADR-013 in part) and **ADR-017** (dep
approval for pyjwt/bcrypt + the Vitest stack, per ADR-006; logged in `Lead2Dev.md`).

| Loop | What shipped | Evidence |
|---|---|---|
| F-DB1 | `ontowiz_runtime.Database` — thin SQLite wrapper (execute/fetch_one/fetch_all/transaction), DSN/path-driven, ported from market_zero `db.py`. Thread-safe (lock + `check_same_thread=False`) for the serve threadpool. | `test_db.py` (6 tests) |
| F-DB2 | `CommentStore` re-backed on `Database` (`<root>/catalog.db`); same `CommentStore(root)` + `add`/`list` contract. | `test_comments.py` (4; existing 3 stay green + a SQLite-backing assertion) |
| F-DB3 | `UsageStore` re-backed on `Database` (shared `catalog.db`); same contract + `catalog_stats`. | `test_telemetry.py` (3) |
| F-RB1 | `ontowiz_serve.auth` — bcrypt `hash/verify_password` + pyjwt HS256 `issue/decode_token` (`ONTOWIZ_JWT_SECRET`); ported from market_zero `services/auth.py`. | `test_auth.py` (5) |
| F-RB2 | RBAC bound to a real principal: `get`/resolve from a Bearer JWT; `require_capability` derives the role from the **token**, not the `X-OntoWiz-Role` header (header now a dev fallback only). `POST /v1/auth/login` + `GET /v1/auth/me` over a seeded SQLite `UserStore`. | `test_rbac.py` (5) — incl. **a header cannot escalate an authenticated principal**; existing `test_api.py` (18) stay green |
| F-FE0 | Frontend test gate (ADR-017): Vitest + RTL + jsdom; `vitest.config.ts` (coverage scoped to catalog code, ≥85% thresholds), `npm test`/`test:cov`/`typecheck`. | smoke test green |
| F-FE1 | `src/types/catalog.ts` (mirrors the runtime dataclasses) + `src/services/catalog.ts` client (catalog/search/functions/detail/artifact/comments/diff/stats/roles/login/me) against `NEXT_PUBLIC_CATALOG_API_URL`. | `catalog.test.ts` (mocked fetch) |
| F-FE2..5 | `/catalog` route in the Next.js app: grid + search → pack detail (function slices w/ token-leanness note + artifact list) → artifact drawer (verdict, anti-patterns, governance trail, YAML) → comments + Bearer-authed posting + curator/manager review; `LoginBar` + `useCatalogAuth` (JWT in localStorage). | `catalog.test.tsx` (component RTL) |

Net: **+18 package tests (191→209)**, coverage 98.38%; ruff/mypy(Tier A)/boundary
clean; CK new-code 0; 308 src tests green; `verify-audit` → PASS. **Frontend gate:**
25 Vitest tests, **96%+ coverage on the catalog code**, `tsc --noEmit` clean,
`eslint` clean, `next build` clean (`/catalog` prerendered).

**Honest boundaries (deferred, not hidden):** SQLite is the dev/test engine —
**Postgres is the production target** (ADR-016) but is **not yet exercised by an
automated test** (no local PG credential; docker daemon down). The `UserStore` is
**seeded** (one demo user per role, password `ONTOWIZ_SEED_PASSWORD`/`ontowiz-demo`);
no signup/reset/refresh-token/SSO; JWT has no rotation. The frontend gate is
**Vitest component/client tests**, not full e2e against a live backend; the served
self-contained page (`GET /`) remains as a zero-dependency fallback alongside the new
Next.js route. `verify-audit.sh` stays Python-only — the FE gate is run and recorded
beside it, not folded in.

## Foundry build — Loop 0 (2026-07-09 → 07-10) — backend lane

The July 2026 Foundry build program (`docs/specs/DELIVERY_LOOPS_BACKLOG_2026-07.md`
+ `docs/specs/BUILD_INSTRUCTION_SET_2026-07.md`) opens with Loop 0. Backend lane,
one unit at a time under the R2 loop; mini-specs in `docs/specs/`.

| Unit | What shipped | Evidence |
|---|---|---|
| **F0.1** — CI gate set = R3 | Frontend Vitest wired into CI as a **blocking** step (`npm run test:cov` added to the existing `frontend-build` job — no new job/toolchain); quality-gate + slop_checker demoted to **advisory** (`continue-on-error: true`). New governance test `tests/test_ci_gate_set.py` (4 tests) parses `ci.yml` and asserts the blocking/advisory split, so the gate set is machine-checked, not eyeballed. Spec: `docs/specs/F0-1_CI_GATE_SET.md`. | `verify-audit` → PASS (209 pkg + **312** src/gov tests, 98.38% cov); FE gate green (20 Vitest tests, 96.1% stmts ≥85%). |
| **F0.2** — Governance persistence | New **Tier A** `ontowiz_runtime.GovernanceStore` on the `db.py` SQLite seam — the durable delta lifecycle (5 DDL §9 tables: `deltas`/`delta_events`/`approvals`/`audit_log`/`contributions`). Flat hand-rolled rows (no Tier B import, no ORM), mirroring `CommentStore`/`UsageStore`. `propose`/`approve`/`reject`/`escalate`/`record_contribution` each append a delta-event **and** an audit row atomically. Records the lifecycle only — does **not** promote to ACTIVE (R1's `bridge.py` pipe untouched). Endpoint wiring is F0.3. Spec: `docs/specs/F0-2_GOVERNANCE_PERSISTENCE.md`. | `verify-audit` → PASS (**218** pkg + 312 src/gov tests, **98.49%** cov); **restart-survival test green** (`test_approval_and_audit_survive_restart`); boundary clean (no Tier A→B). |

**Security hygiene verified (F0.1), not assumed:** the `ANTHROPIC_API_KEY` was
**never committed** — exact-path `git log -- .env` is empty; the only `.env*` blob
in history is the intended `.env.example`; `.env` is git-ignored (working-tree only,
126 bytes). So the backlog's "purge `.env` from history" is a **no-op** (no destructive
rewrite performed), and "rotate the *committed* key" is inaccurate — the key never
leaked via git. Rotation remains available as user-side Anthropic-console hygiene.

**Honest boundary (R3 gap, deferred to its own unit):** the retained ctx core
(`ontowiz-ctx`) has substantial source but only a smoke test and is **not yet under
the ≥85% coverage gate** (verify-audit covers spec/runtime/factory/serve/core.bridge).
R3 says "no exemptions"; closing it is a dedicated follow-up unit, **not** folded into
F0.1. Tracked here so it is not lost.

**Honest boundary (F0.2):** the durable `GovernanceStore` is the system-of-record for
the *deployed* process; the legacy **Tier B** in-memory `DeltaStore`/`ContributionStore`
(`ontowiz-core/stores.py`) still back the offline factory composition flows and are
slated for reduction (§2) — F0.2 did **not** rewrite that legacy-debt file. The store
persists the delta lifecycle but is **not yet wired to any endpoint**; `/v1/deltas`
(approve/reject/escalate over JWT principals) is **F0.3**, which will consume this store
and route approval→ACTIVE promotion through `bridge.py` (R1).

## Known debt (tracked, not hidden)

| Item | Severity | Note |
|---|---|---|
| Pre-existing `src/**` quality-gate debt | ⚠️ ~8 high CK findings | "PRS below threshold" on legacy app files (`json_parser.py`, `api/server.py`, `knowledge/*`). Predates the monorepo work. Excluded from the verify-audit owned-gate count. |
| Re-homed `ontowiz-core` legacy PRS debt | ⚠️ 6 CK findings (tracked) | `confidence·delta_generator·graph_store·reasoning_event·semantic_store·stores.py` — pre-existing readability debt (oversized fns / complexity), faithfully relocated from `src/core`. Now fully **ruff-clean** (931 fixes); CK still scans them. mypy-strict not yet applied to Tier B. Pay-down = Task #5. Verify-audit gate 5 excludes this named baseline (NEW code stays 0). |

## How to verify

```bash
bash scripts/verify-audit.sh     # the independent gate — must PASS for any ✅
```

Owned gates: package tests + ≥85% coverage · ruff · mypy (Tier A) · A↛B boundary
· zero CK findings on `packages/` · legacy `src/` suite green.
