# Onto_Wiz Foundry — Engineering Instruction Set v1.0

**Audience:** the dev team · **UI source of truth:** `ontowiz_nextgen_prototype 9.html` (the Foundry: five production-line stations — Intake → Forge → Queue → Ontology → Packs — plus Capture and Studio) · **Strategy source of truth:** STRATEGIC_REVIEW_2026-07.md, UX_UI_PLAN_2026-07.md, FORGE_MODULE_DESIGN_2026-07.md

---

## 0. Verdict on Prototype 9, and three build-relevant critiques

The Foundry framing is right and everything in it preserves the product's constitutional invariant (one pipe: every mutation from every surface becomes a governed delta; the publish button structurally absent for ungated packs). Build to it. Three critiques that shape sequencing, not scope:

1. **Studio is the most technically ambitious surface in the product** (live LLM structuring onto a canvas, grounding guarantee "I've structured only what you said", per-turn provenance). It is also the least essential to the month-3 pilot. It builds **last** (Epic E5), behind a working Intake — which exercises the same extraction machinery in batch, where failures are cheap.
2. **Forge calibration ("your calibration curve", crew standing "ranked on calibration") requires the gold-probe infrastructure to exist first.** Probes before calibration UI; v0 ships rating + impact feed only, calibration panel arrives with probes in v1.
3. **The Hunt mission ("catch a mis-fired rule") needs a mis-fire signal source** — eval failures and gold-set dry-runs. It therefore depends on the eval gate running continuously (F0.6) and lands in Forge v1, not v0.

One cosmetic note: the Capture section of Prototype 9 has a broken `onclick` string leaking into visible text ("…',false,4200)"). Ignore it; it's a prototype artefact.

---

## 1. Rules of engagement (the discipline — read first, applies to every unit)

These extend the repo's existing ADR-015 loop, which the strategic review verified is genuinely followed. They are not optional.

- **R1 — One pipe.** No code path writes an artifact to ACTIVE except via an APPROVED Delta through `bridge.py`. This includes curator edits, hierarchy moves, Studio commits, Forge consensus, and Intake promotions. Any PR adding a bypass is rejected regardless of justification.
- **R2 — The unit loop.** Every work unit below follows: mini-spec in `docs/specs/` (½ page: contract, API surface, test list) → failing tests first → implement → `verify-audit.sh` green → evidence pasted into `PROJECT_STATUS.md`. No unit larger than one person-week; split anything bigger.
- **R3 — The gate set** (per the review's pruning): ruff, mypy, pytest with **≥85% coverage on all shipped code** (including the retained ctx core — no exemptions), `check_boundaries.py`, and the frontend Vitest suite **wired into CI as a blocking job** (it currently isn't). slop_checker and quality-gate are removed from the blocking path in F0.1.
- **R4 — Definition of Done** for any unit: tests green in a clean environment; API changes reflected in the master endpoint table (§8); new tables in the master DDL (§9); attribution and provenance fields populated (never the literal string `'curator'`); one screenshot or curl transcript in the PR description proving the acceptance behaviour.
- **R5 — LLM calls live in exactly two places:** the Intake/Studio structurer service and the offline eval/lift runner. The serving path stays key-free. Every structurer output is confirmable-by-human before persistence (propose-not-promote enforced server-side).
- **R6 — No speculative infra.** SQLite until a second tenant exists. No encryption/sealed-build work. No marketplace features beyond the catalogue. Anything not in this document needs a new mini-spec and a reason.

---

## 2. Locked architecture decisions

One deployed FastAPI app — **ontowiz-serve** — owning capture, intake, forge, governance, ontology, catalog, and context serving, mounted as routers: `/v1/auth`, `/v1/context`, `/v1/packs`, `/v1/deltas`, `/v1/ontology`, `/v1/intake`, `/v1/forge`, `/v1/studio`. Libraries: ontowiz-spec (contracts), ontowiz-runtime (assembly + PackRegistry + the SQLite `db.py` seam + folded-in ctx core), ontowiz-core (reduced to Delta/bridge governance), ontowiz-factory (offline: parsers, extraction, compiler, eval runner, forge scoring — the only Anthropic-key holder besides the structurer). One Next.js app, one typed API client, JWT throughout, role-shaped nav (SME / curator / consumer / admin). Legacy `src/` and verify-audit gate 6 are deleted at the end of F0. Design tokens and components come from Prototype 9 (extract into `frontend/src/ui/` — the existing seven primitives get adopted, not deleted).

---

## 3. Epic F0 — Foundations (everything else depends on this; ~3–4 weeks)

| Unit | Instruction | Acceptance |
|---|---|---|
| **F0.1** | Rotate the committed ANTHROPIC_API_KEY; purge `.env` from git history; demote slop_checker/quality-gate to advisory; wire frontend Vitest into blocking CI | Old key dead; CI blocking = R3 gate set exactly |
| **F0.2** | Governance persistence: move Delta / approval / audit / contribution stores from in-memory dicts onto the `db.py` SQLite seam (tables: `deltas`, `delta_events`, `approvals`, `audit_log`, `contributions`) | Approve a delta, restart the process, approval and audit trail survive; test proves it |
| **F0.3** | Port the SME endpoint surface (~14–18 endpoints: sessions/capture, review queue, approve/reject/escalate, audit, contributors) from legacy `src/api/server.py` into ontowiz-serve under JWT with real principals | Frontend `services/api.ts` re-pointed to `:8080`; every mutation attributed to a JWT identity; `'curator'` string gone |
| **F0.4** | Port `src/knowledge/parsers` (PDF/DOCX + chunking) into ontowiz-factory; add pptx (python-pptx), vtt/txt, xlsx (openpyxl), eml parsers behind one `parse(source) → Chunk[]` interface | Golden-file tests per format |
| **F0.5** | Delete `src/` and verify-audit gate 6; collapse the duplicate domain models (ontowiz_spec artifacts canonical); drop `reasoning_event.py` pharma-game types | Repo builds green without `src/`; LOC report in PR |
| **F0.6** | Eval gate hard-fail: `compiler.py` refuses to emit `gate_passed: false`; re-run the suite against 0.3.0 → publish 0.4.0 gated, or roll back to 0.1.0; fix the Germany/US gold-set bug | A failing-gate compile raises; served pack has a passing gate and a lift number |
| **F0.7** | Hierarchy schema: add `parent` to the L0 domain registry (ARCHITECTURE.yaml + spec model); node path stamped on every artifact; roll-up query | Rules scoped to Commercial › Field Force roll up to Commercial in one API call |
| **F0.8** | Deploy: execute the Railway config; `/health` public; seed users per role | A live URL exists and stays up for a week |

**Phase gate G0:** all F0 units done → the product is *one authenticated persistent deployed system*. Nothing from later epics starts before G0 except E1.1 (parser work, which is F0.4).

---

## 4. Epic E1 — Intake (station 01; ~2–3 weeks)

**Backend.** `sources` become durable managed objects: `POST /v1/intake/sources` (upload → parse → store chunks with locators: slide n / timestamp / page), `GET /v1/intake/sources` (library with per-layer yield + promoted counts). Extraction job (factory, offline, Anthropic key): for each source, Claude proposes **layer-classified candidates** (L1 entity / L2 relation / L3 rule / L4 metric / L5 scenario-eval) each carrying: proposed node in the hierarchy, the exact seeding sentence + locator, confidence, and — for L3 — a paired draft eval case. Tables: `sources`, `source_chunks`, `candidates` (status: proposed / promoted / edited / rejected+reason). Rejections store the one-tap reason (training signal). Promotion calls the same delta pipe as everything else (R1).

**Frontend.** Source library table (as in Prototype 9: yield chips by layer, promoted x/y); Extraction Sheet: two-pane view — transcript/document with seeding sentences highlighted, candidate list with click-to-jump sync; candidate card actions *promote / fix (structured editor) / reject-with-reason*. Components: `SourceLibrary`, `ExtractionSheet`, `CandidateCard`, `ChunkViewer` (per-format renderers: transcript, slide thumbnails deferred — text-only first).

**Acceptance:** drop the real Field Force QBR .vtt → candidates appear with correct locators → promoting one lands a PROPOSED delta in the queue with source provenance intact end-to-end (visible in the delta drawer's evidence pane). **Metric instrumented:** candidates promoted / SME-hour.

---

## 5. Epic E2 — Forge (station 02; v0 ~2 weeks inside pilot month, v1 after)

Backend and data model exactly as FORGE_MODULE_DESIGN §6 (question compiler with 8 signals, router, play API, answer structurer, consensus engine, probe/weight service, impact notifier; tables `forge_questions/assignments/answers/ratifications/ratings/probes`). Build order within the epic:

- **E2.1 (v0):** compiler signals 1–3 + 8 (unvalidated, low-confidence, missing-eval, anti-pattern gap) → **Assay** + **Name-the-caveat** missions, k=1, card stack UI, ratification ladder states, impact feed as a simple list. Uses existing `submit_mission` / `steward.py` unchanged.
- **E2.2 (v1):** router k=3 + `resolve_consensus` + ladder transitions + **Duel** (signals 4–5) + gold probes + per-SME weights → only now build the calibration panel and crew standing (critique #2).
- **E2.3 (v1):** **Hunt** — mis-fire candidates from eval failures + gold-set dry-runs (depends on F0.6 continuous evals; critique #3). A caught mis-fire drafts a correction delta (Prototype 9's DELTA-149 flow).
- **E2.4 (v2, gated on v1 evidence):** weekly node challenges, corpus-heat animations, Spot-the-flaw / Teach-back.

**Frontend components:** `ShiftQueue` (card stack, mobile-first), `AssayCard`, `DuelCard`, `CaveatCard`, `ConfirmSheet` (the AI-drafted artifact+eval confirm — shared by all missions and by Intake), `ImpactPanel`, `CalibrationPanel` (v1), `CorpusHeat`.

**Acceptance v0:** an SME completes a 5-question shift on a phone-width viewport in under 4 minutes; every answer produces a queue-visible delta+eval or an explicit ladder signal; **theatre alarm live from day one** (deltas/SME-hour dashboard tile).

---

## 6. Epic E3 — Curation Queue & Ontology workspace (stations 03–04; ~3 weeks)

- **E3.1** Queue upgrade: human-readable diff (YAML behind a tab), conflict surfacing (shared tags / adjacent priorities), evidence pane rendering source-specific provenance (session step / intake seeding sentence / forge mission + consensus stats), dry-run-on-gold-set button, edit-and-resubmit with dual attribution, approve → visible compile-on-approve pipeline (toast sequence → Packs).
- **E3.2** Layer browser per L1–L5 with structured editors (fields mirror ontowiz-spec models; curator saves create deltas — R1); node column + inheritance chips ("↓ inherited from Commercial").
- **E3.3** Hierarchy management: add/rename/move/merge nodes and reparent objects, all as deltas; coverage roll-up drill-down on the dashboard.
- **E3.4** Mapping Workbench: synonyms → cross-domain → standards (glossary already in ARCHITECTURE.yaml) → base↔overlay, in that order; each mapping a typed governed artifact (link type + confidence + rationale).
- **E3.5** Lineage tab (origin → deltas → pack versions → evals, one query) and read-only reactflow graph (entities/relations/rule badges, cross-domain edges dashed). Edit-in-graph explicitly deferred.

**Acceptance:** the DELTA-147 drawer flow from the prototype works end-to-end against real data; a reparent shows up in the queue as a delta; lineage answers "who stands behind R-110?" in one screen.

---

## 7. Epic E4 — Packs & Releases (station 05; ~1–2 weeks) and Epic E5 — Studio (last; ~3 weeks, gated)

**E4:** pack composer (select hierarchy nodes + layers → manifest with what's-in/what's-excluded), release-gate panel (publish button absent when `gate_passed: false`; lift receipt + SME-authored held-out count as the version headline), artifact-level version diff, consume tab (MCP endpoint, function-slice token footprints, try-it console calling `context/get` live). Overlays deferred until a second consumer exists.

**E5 Studio (build last; gate: Intake shipped and Forge v0 evidence positive):**
- **E5.1** Conversation service: `POST /v1/studio/sessions` + turns; every turn stored as a durable source (same `sources` table — a conversation *is* an intake source, which is the elegant part of Prototype 9's design).
- **E5.2** Structurer contract — the hard unit. Server-side, strict: output only objects **groundable to a quoted span of the SME's words** (each staged object carries `grounding_turn_id` + quoted span; a response inventing ungrounded content fails validation and is retried). The model is also prompted to ask the boundary question ("when does this NOT hold?") when an L3 rule is staged without an anti-pattern.
- **E5.3** Canvas staging: dashed = proposed, solid = in-corpus; staged set is session-local until **Commit**, which emits one delta per staged object through the pipe, each carrying conversation provenance. `StudioCanvas`, `TurnStream`, `StagedObjectChip`, shared `ConfirmSheet`.

**Acceptance E5:** replay the Prototype 9 script (accumulator → abandonment; 340B exception) against the live structurer → six grounded proposals, zero invented fields, commit lands them in the queue attributed to the speaker.

---

## 8. API master reference (routers × key endpoints)

`/v1/auth` login/refresh/me · `/v1/deltas` list/get/approve/reject/escalate/resubmit + `GET /deltas/:id/dryrun` · `/v1/ontology` nodes CRUD-as-deltas, layers list per node, mappings, lineage, graph · `/v1/intake` sources upload/list/get, candidates list/promote/edit/reject · `/v1/forge` next/answer/impact/leaderboard + curator: questions, probes, escalations, config(k, thresholds) · `/v1/studio` sessions, turns, stage, commit · `/v1/packs` list/compose/gate/rerun/diff/publish + `/v1/context` (existing, unchanged) + MCP door (existing). Every mutating endpoint: JWT principal, idempotency key, audit row.

## 9. Data model additions (SQLite, `db.py` seam — one migration file per epic)

F0: `deltas, delta_events, approvals, audit_log, contributions, domain_nodes(parent)` · E1: `sources, source_chunks, candidates` · E2: `forge_questions, forge_assignments, forge_answers, forge_ratifications, forge_ratings, forge_probes` · E3: `mappings` · E5: `studio_sessions, studio_turns, staged_objects`. Conventions: TEXT ids, ISO timestamps, `created_by` on every row, soft-delete via status, no ORM cleverness — the existing hand-rolled seam pattern.

## 10. Sequencing, phase gates, kill-tests

**F0 (weeks 1–4) → G0.** **E1 + E2.1 (weeks 4–7) → G1: the pilot gate** — live URL, Intake + Forge v0 + upgraded Queue in front of 3–5 real SMEs. *Kill-test at G1+2 weeks:* deltas/SME-hour ≥ quick-capture baseline AND week-2 SME return > 0, else Forge stops at v0 and effort shifts to Intake+Queue. **E3 (weeks 7–10) → G2:** curators manage hierarchy/mappings in production. **E4 (weeks 10–12) → G3:** a gated pack with SME-authored held-out evals published and consumed via MCP by one real agent workflow. **E2.2–2.3 + E5 (months 4–6),** each gated on the preceding evidence. The strategic kill-test stands above all of it: if SMEs won't engage by month 4–5, the salvage asset is the governance/eval engine — build nothing in E5 before that's answered.

## 11. Test matrix (minimum per epic)

Unit tests per module (R3 coverage); contract tests: every mutating endpoint → delta pipe (R1 regression suite — try to write around it and fail); golden-file tests for parsers; structurer grounding tests (adversarial transcripts that tempt invention); E2E happy paths per station (Playwright): intake-promote, forge-shift, approve-recompile, compose-publish-blocked-then-passed; a restart-survival test (F0.2) that runs in CI forever.
