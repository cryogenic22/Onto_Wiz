# Onto_Wiz Foundry - Engineering Instruction Set v2.0

**Audience:** BE, FE, Knowledge/Evaluation, Integrator, and read-only Reviewer
**Companion control:** `DELIVERY_LOOPS_BACKLOG_2026-07.md`

---

## -1. How to use this v2 instruction set

This file is normative for technical implementation and Definition of Done.
`DELIVERY_LOOPS_BACKLOG_2026-07.md` is normative for sequence, ownership, status
and review isolation. Sections 12-16 below split the original coarse epics into
reviewable units and supersede conflicting coarse wording.

Build teams may clarify implementation inside an accepted mini-spec. They may not
weaken an invariant, acceptance criterion or evidence requirement without an
amendment accepted by the Integrator before code changes.

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
- **R3 — The gate set** (per the review's pruning): ruff, mypy, pytest with **≥85% coverage on all shipped code** (including the retained ctx core — no exemptions), `check_boundaries.py`, and the frontend Vitest suite **wired into CI as a blocking job**. F0.1 verified this; slop_checker and quality-gate remain advisory.
- **R4 — Definition of Done** for any unit: tests green in a clean environment; API changes reflected in the master endpoint table (§8); new tables in the master DDL (§9); attribution and provenance fields populated (never the literal string `'curator'`); one screenshot or curl transcript in the PR description proving the acceptance behaviour.
- **R5 — LLM calls live in exactly two places:** the Intake/Studio structurer service and the offline eval/lift runner. The serving path stays key-free. Every structurer output is confirmable-by-human before persistence (propose-not-promote enforced server-side).
- **R6 — No speculative infra.** SQLite until a second tenant exists. No encryption/sealed-build work. No marketplace features beyond the catalogue. Anything not in this document needs a new mini-spec and a reason.
- **R7 — Evidence before confidence.** A knowledge assertion cannot be accepted
  from extraction without a `SourceRef` containing source hash, chunk, exact locator
  and quoted span. Confidence without navigable evidence is not a trust signal.
- **R8 — Applicability is first-class.** Jurisdiction, organization/client, therapy,
  indication/population, function/channel and valid-from/to are structured fields.
  A globally-scoped default must be an explicit reviewed choice, never an omission.
- **R9 — Agent runs are replayable.** Every extraction/structuring/eval run records
  input hashes, model/provider, prompt/schema version, parameters, outputs, cost,
  timestamps, retries and human disposition. Retry uses an idempotency key.
- **R10 — Candidate is not release.** Candidate compilation exists so evaluation can
  run. Only `publish` creates a release, and publish plus production registry/serve
  reject an unrun or failing gate.
- **R11 — Contract before consumer.** OpenAPI, generated TS client and fixtures merge
  before FE implementation. Production FE has one API client and no handwritten
  response types or direct corpus mutations.
- **R12 — Dissent is durable.** Consensus never deletes minority answers. A split
  produces a contested state, an ExceptionRule candidate or explicit escalation.
- **R13 — Data egress is policy-controlled.** Source access class determines whether
  content may be sent to a model provider. Serving stays source-text- and key-free.
- **R14 — Builder/reviewer separation.** The builder submits an immutable SHA; the
  read-only reviewer cannot edit/commit/push/merge; only the Integrator marks VERIFIED.


---

## 2. Locked architecture decisions

One deployed FastAPI app — **ontowiz-serve** — owning capture, intake, forge, governance, ontology, catalog, and context serving, mounted as routers: `/v1/auth`, `/v1/context`, `/v1/packs`, `/v1/deltas`, `/v1/ontology`, `/v1/intake`, `/v1/forge`, `/v1/studio`. Libraries: ontowiz-spec (contracts), ontowiz-runtime (assembly + PackRegistry + the SQLite `db.py` seam + folded-in ctx core), ontowiz-core (reduced to Delta/bridge governance), ontowiz-factory (offline: parsers, extraction, compiler, eval runner, forge scoring — the only Anthropic-key holder besides the structurer). One Next.js app, one typed API client, JWT throughout, role-shaped nav (SME / curator / consumer / admin). Legacy `src/` and verify-audit gate 6 are deleted at the end of F0. Design tokens and components come from Prototype 9 (extract into `frontend/src/ui/` — the existing seven primitives get adopted, not deleted).

---

### Public serve plane and privileged build plane

There is one public product backend (`ontowiz-serve`) but two process roles:

1. **Serve plane (Tier A, key-free):** auth, reads, persistent Delta decisions,
   catalog/context, job status and MCP. It never imports Tier B.
2. **Build worker (Tier B, private):** consumes durable outbox jobs, applies the
   canonical Delta bridge, parses/extracts, builds candidates, runs evals and emits
   release files/receipts. It is the only process with model credentials.

Approval and job creation are atomic. The worker is idempotent. The serve plane
observes flat job/output records and released pack files; it does not call Tier-B
functions in-process. This preserves the package boundary while presenting one
coherent application to users.

---

## 3. Epic F0 — Foundations (everything else depends on this; ~3–4 weeks)

| Unit | Instruction | Acceptance |
|---|---|---|
| **F0.1 - VERIFIED** | CI gate set and secret-history hygiene. `.env` was never committed; destructive history rewrite was correctly skipped. | Project-status evidence and permanent CI governance tests. |
| **F0.2 - VERIFIED** | Durable Delta / approval / audit / contribution records on the `db.py` seam. | Restart-survival and project-status evidence; route wiring remains F0.3. |
| **F0.3** | Port the SME endpoint surface (~14–18 endpoints: sessions/capture, review queue, approve/reject/escalate, audit, contributors) from legacy `src/api/server.py` into ontowiz-serve under JWT with real principals | Frontend `services/api.ts` re-pointed to `:8080`; every mutation attributed to a JWT identity; `'curator'` string gone |
| **F0.4** | Port `src/knowledge/parsers` (PDF/DOCX + chunking) into ontowiz-factory; add pptx (python-pptx), vtt/txt, xlsx (openpyxl), eml parsers behind one `parse(source) → Chunk[]` interface | Golden-file tests per format |
| **F0.5** | Delete `src/` and verify-audit gate 6; collapse the duplicate domain models (ontowiz_spec artifacts canonical); drop `reasoning_event.py` pharma-game types | Repo builds green without `src/`; LOC report in PR |
| **F0.6** | Split candidate build from release publish. Candidates may be ungated so eval can run; `publish` and production registry/serve reject unrun or failing gates. Re-evaluate 0.3.0 and fix geography leakage. | Failed candidates cannot publish/serve; passing 0.4.0 has a reproducible receipt or production rolls back. |
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

`/v1/auth` login/refresh/me · `/v1/deltas` list/get/propose/approve/reject/escalate/resubmit/dryrun · `/v1/jobs` get/retry · `/v1/ontology` nodes, layers, mappings, validate, lineage, graph · `/v1/intake` sources/chunks/jobs and candidates promote/edit/reject · `/v1/forge` next/answer/confirm/impact (ratings/probes/config only in v1) · `/v1/studio` sessions/turns/stage/commit · `/v1/packs` list/compose/candidate/evaluate/receipt/diff/publish/withdraw · `/v1/usage` and `/v1/corrections` · existing `/v1/context` and MCP. Every mutation requires JWT capability, resource ownership, `Idempotency-Key`, expected version/ETag and audit row.

## 9. Data model additions (SQLite, `db.py` seam — one migration file per epic)

F0: `deltas, delta_events, approvals, audit_log, contributions, jobs, outbox_events, domain_nodes, artifact_versions, applicability, evidence_refs` · E1: `sources, source_chunks, candidates, agent_runs` · E2: `forge_questions, forge_assignments, forge_answers, forge_ratifications, forge_ratings, forge_probes` · E3: `mappings, terminology_bindings, validation_runs` · E4: `eval_receipts, release_attestations` · E6: `usage_events, correction_events` · E5: `studio_sessions, studio_turns, staged_objects`. Use one migration per unit, TEXT IDs, UTC ISO timestamps, actor/tenant where applicable, immutable log records, foreign-link/application integrity, bounded indexes and status-based lifecycle. No ad hoc `CREATE TABLE` outside the migration runner once it lands.

## 10. Sequencing, phase gates, kill-tests

**F0 (weeks 1–4) → G0.** **E1 + E2.1 (weeks 4–7) → G1: the pilot gate** — live URL, Intake + Forge v0 + upgraded Queue in front of 3–5 real SMEs. *Kill-test at G1+2 weeks:* deltas/SME-hour ≥ quick-capture baseline AND week-2 SME return > 0, else Forge stops at v0 and effort shifts to Intake+Queue. **E3 (weeks 7–10) → G2:** curators manage hierarchy/mappings in production. **E4 (weeks 10–12) → G3:** a gated pack with SME-authored held-out evals published and consumed via MCP by one real agent workflow. **E2.2–2.3 + E5 (months 4–6),** each gated on the preceding evidence. The strategic kill-test stands above all of it: if SMEs won't engage by month 4–5, the salvage asset is the governance/eval engine — build nothing in E5 before that's answered.

## 11. Test matrix (minimum per epic)

Unit tests per module (R3 coverage); contract tests: every mutating endpoint → delta pipe (R1 regression suite — try to write around it and fail); golden-file tests for parsers; structurer grounding tests (adversarial transcripts that tempt invention); E2E happy paths per station (Playwright): intake-promote, forge-shift, approve-recompile, compose-publish-blocked-then-passed; a restart-survival test (F0.2) that runs in CI forever.

---

## 12. Required unit mini-spec and canonical contracts

### 12.1 Mini-spec template

Before implementation, every unit creates or updates one `docs/specs/<UNIT>.md`
with these sections:

1. **Objective and user-observable outcome.**
2. **Preconditions and pinned dependency SHAs/contracts.**
3. **Files and ownership paths.**
4. **API/events/schema changes**, including generated-client and migration impact.
5. **State machine and invariants**, with forbidden transitions.
6. **Threat and data-egress delta.**
7. **Tests mapped one-to-one to acceptance criteria**, including negative, retry,
   concurrency and restart cases.
8. **Migration, rollback and recovery.**
9. **Telemetry and operational failure behaviour.**
10. **Out of scope and known residual risk.**
11. **Dependency change**, if any: ADR approval, license/security review and lockfile impact.

An accepted mini-spec is frozen for the unit. A material change requires an
amendment before the implementation diff grows.

### 12.2 Canonical semantic and operational records

These are contracts, not suggestions. Add them incrementally in their owning units
without duplicating equivalent models.

- **DomainNode:** stable ID, canonical label, description, parent ID, domain, status,
  aliases, owner, version and lifecycle history. Reparenting never changes stable ID.
- **Applicability:** jurisdictions, organizations/clients, therapy areas, indications,
  populations, functions, channels, valid-from, valid-to and explicit global flag.
- **EvidenceRef:** source ID/hash, chunk ID/hash, locator type/value, exact quoted
  span, access class, captured-at and extraction/confirmation actor.
- **TerminologyBinding:** internal concept ID, external system/code/version/display,
  mapping type, confidence, rationale, source/license and review status.
- **AgentRun:** run ID/type, input hashes, model/provider, prompt/schema versions,
  parameters, output hashes, token/cost data, retries, status and human disposition.
- **EvalReceipt:** suite/split hash, pack digest, model config, cases by provenance
  and failure type, with/without results, uncertainty, failures and timestamp.
- **ReleaseAttestation:** pack/version/digest, source commit, compiler version,
  artifact and dependency digests, eval-receipt hash, publisher and published-at.

Do not overload free-form tags to stand in for these contracts. Backward-compatible
loading is required while current packs are migrated.

### 12.3 Common API behaviour

- Base path `/v1`; one generated TS client.
- Error envelope: stable code, human message, request ID and optional field details.
- Mutations require Bearer principal, capability check and `Idempotency-Key`.
- Mutable resources expose version/ETag; stale decisions return 409.
- Collection endpoints support bounded pagination and stable ordering.
- 401, 403, 404, 409, 413, 415, 422 and 429 semantics are contract-tested.
- Request logs contain IDs and timing, never source text, credentials or model prompts.

## 13. Foundation task cards

F0.1 and F0.2 are VERIFIED. Do not reopen them unless a later unit demonstrates a
regression. Their permanent regression tests remain in the gate set.

### F0.2H - Governance state and persistence hardening

**Steps**

1. Define allowed Delta transitions and decision preconditions in one typed contract.
2. Add resource/artifact ID, base artifact version, idempotency key and expected
   status/version to durable records.
3. Add migration-managed foreign keys/application integrity checks and indexes for
   Delta status, artifact, actor and created time.
4. Make approve/reject conditional on `proposed`; repeat of the same idempotency key
   returns the original result; a conflicting repeat returns 409.
5. Add optimistic concurrency so two reviewers cannot silently overwrite decisions.
6. Preserve append-only events/approvals/audit and atomic transaction boundaries.
7. Add recovery tests for rollback, restart and a decision interrupted mid-transaction.

**DoD:** illegal and double transitions fail deterministically; two concurrent
reviewers yield exactly one accepted decision; audit/event counts are correct;
migration/restore works; existing restart-survival test remains green.

### F0.3A - Contract handshake

**Steps**

1. Inventory every legacy endpoint consumed by `frontend/src/services/api.ts` and
   classify keep/rename/drop.
2. Specify auth, Delta list/get/propose/approve/reject/escalate/resubmit, review queue,
   audit, contribution and contributor-summary endpoints in OpenAPI.
3. Define principal/capability rules, request/response schemas, pagination, ETags,
   idempotency and common errors.
4. Generate the TS client from the contract and add representative fixtures for
   success, empty, stale, unauthorized and validation cases.
5. Add contract-lint and generated-client-drift checks to CI.

**DoD:** route inventory has no unexplained legacy consumer; OpenAPI validates;
generated client type-checks; fixtures satisfy schemas; FE can render all Loop-1
states without hand-authored endpoint types.

### F0.3B - Unified served governance and capture API

**Steps**

1. Mount small routers in `ontowiz-serve` using `GovernanceStore` and existing auth.
2. Resolve actor and role exclusively from JWT; remove reviewer names from request
   bodies and reject header-based privilege escalation for authenticated users.
3. Enforce capabilities and resource ownership for every route.
4. Map store/state failures to the common 404/409/422 envelope.
5. Implement bounded filters/pagination for queue, audit and contributions.
6. Emit request/audit IDs and safe structured logs.

**DoD:** all OpenAPI examples pass against the live app; auth/capability/ownership
negative tests exist per mutation; no literal `curator`; restart preserves API-visible
state; API modules do not import Tier B.

### F0.3C - Approval to build-worker outbox

**Steps**

1. Add durable `jobs` and `outbox_events` records with unique idempotency keys,
   attempts, lease/heartbeat, status, error code and timestamps.
2. In one transaction, approve the Delta and append `artifact_promotion_requested`.
3. Implement a private Tier-B worker that reconstructs the canonical Delta, calls
   the bridge, writes a versioned candidate artifact and records output digest.
4. Make leases/retries safe after process death; identical jobs cannot create
   duplicate artifact versions.
5. Surface queued/running/succeeded/failed/dead-letter state through Tier-A records.
6. Add explicit retry and curator-visible failure reason; never auto-ignore failure.

**DoD:** kill worker after each step and restart without duplicate promotion or lost
approval; failed work cannot mark an artifact ACTIVE/released; serve plane remains
Tier A/key-free; end-to-end audit links decision, job and output.

### F0.3D - Frontend live rewire

**Steps**

1. Replace legacy `services/api.ts` calls with the generated client.
2. Use one auth/session mechanism and role-shaped navigation.
3. Implement loading, empty, validation, 401/403, stale 409, retry and offline states.
4. Disable repeated decisions while pending and reconcile server state after failure.
5. Link every reviewed Delta to actor, evidence summary and build-job state.
6. Add component tests against fixtures and Playwright against the live API.

**DoD:** no production frontend reference to legacy base URL/routes; no handwritten
response interface duplicates OpenAPI; named-principal approval survives restart;
desktop/mobile and keyboard flows pass.

### F0.4A/F0.4B - Managed parser boundary

**Steps**

1. Define `Source`, `Chunk`, `Locator`, parser result/error and parser registry.
2. Port PDF/DOCX/TXT/VTT first; add PPTX/XLSX/EML only in F0.4B.
3. Preserve page, slide, sheet/cell, message-part and timestamp locators.
4. Hash original bytes and normalized chunks; record parser/version and warnings.
5. Enforce allowlisted type, extension/content agreement, size/page/sheet limits,
   archive expansion bounds and safe filenames.
6. Quarantine unsupported/encrypted/malformed sources; never partially promote them.
7. Add golden, malformed, oversized, duplicate and locator-round-trip tests.

**DoD:** all formats implement one interface; source->chunk->locator is deterministic;
identical source is deduplicated; unsafe input cannot escape storage or exhaust
configured bounds; no parser requires a model key.

### F0.5 - Legacy deletion and model collapse

**Steps**

1. Produce route, model, store and test equivalence inventory for `src/`.
2. Migrate required data and fixtures; prove counts and hashes.
3. Repoint all clients/scripts/deployment imports.
4. Delete legacy code only after the integrated G0 test passes.
5. Remove obsolete dependencies, gate 6 and compatibility shims with no consumers.
6. Record before/after source LOC and remaining duplicate-model search.

**DoD:** clean checkout builds/tests/deploys without `src/`; no import/string route
references remain except history/docs; migration reconciliation is exact; rollback
uses the prior release and backup, not resurrected dual-write code.

### F0.6A - Candidate, evaluation and release state machine

**Steps**

1. Define states: draft artifacts -> candidate build -> evaluated pass/fail ->
   published release -> deprecated/withdrawn.
2. Permit candidate compilation with explicit non-production status.
3. Make eval runner write an immutable receipt tied to candidate digest.
4. Make publish require matching passing receipt, authorization and unchanged digest.
5. Make production registry/context reject candidate, failed, withdrawn and tampered
   packs even if a caller knows their path.
6. Add TOCTOU tests: modify artifact after eval; publish must fail.

**DoD:** failing/unrun candidate is buildable for diagnosis but impossible to publish
or production-serve; passing unchanged candidate publishes once; receipt and release
digests match; UI/API cannot override the gate.

### F0.6B - Credible evaluation and 0.4.0 decision

**Steps**

1. Partition development and held-out cases; hash/freeze the held-out split.
2. Label case author/provenance and prevent generated/dev-authored cases being counted
   as SME-held-out.
3. Add geography, temporal validity, abstention, safety, conflict and negative cases.
4. Remove Germany/US payer-mechanics leakage and audit all case applicability.
5. Add leakage checks between questions, expected terms and served artifact bodies.
6. Report case counts, failures and uncertainty alongside aggregate lift.
7. Re-run against a candidate from current content; release 0.4.0 only if it passes,
   otherwise select the last passing production version.

**DoD:** independent replay yields the same scored receipt; failures are inspectable;
held-out provenance is honest; no failing pack becomes default; lift is not claimed
without model/config/case counts and uncertainty.

### F0.7A - Hierarchy and applicability contract

**Steps**

1. Add stable `DomainNode` and `Applicability` models from section 12.2.
2. Migrate current commercial/function structure with an explicit mapping report.
3. Validate no cycles, orphan parents, duplicate sibling IDs or invalid date ranges.
4. Stamp node path and applicability on artifacts without using path as identity.
5. Implement ancestor/descendant and effective-scope roll-up queries.
6. Define inheritance/override precedence and conflict output.

**DoD:** Field Force rolls up to Commercial; reparent keeps stable ID; geography is
queryable; ambiguous missing scope is rejected for new active L3 knowledge; current
pack migration round-trips without silent loss.

### F0.8A - Deployment and recovery

**Steps**

1. Deploy serve and private worker roles with distinct secrets/capabilities.
2. Add liveness/readiness; readiness checks DB, pack registry and required migrations.
3. Configure persistent storage, secret rotation path and least-privilege service users.
4. Run backup, destructive test-environment loss and restore drill.
5. Add request/job correlation, safe logs, basic latency/error/retry alerts.
6. Run a seven-day availability observation before marking VERIFIED.

**DoD:** live URL and health evidence exist; no model key in serve role; restore
reconstructs governance and releases; worker failure does not break read serving;
runbook names owner and recovery steps.

### F0.9 - CTX product surface and coverage

**Steps**

1. Trace imports from runtime/factory and classify CTX files retain/fold/delete.
2. Delete checked-in `build/` duplicates and unused subpackages after consumer search.
3. Add behaviour tests for retained parse/serialize/hydrate/restrict/security paths.
4. Put all shipped CTX code under >=85% coverage, ruff and mypy or document a
   deliberate typed boundary accepted by REV.
5. Benchmark context size, hydration correctness and query latency on the real pack.

**DoD:** no shipped unowned CTX island; coverage gate includes retained source;
candidate and production context cannot leak gated artifacts; benchmark is recorded.

### D0 and D1 - Frontend foundation

| Unit | Concrete output | Unit DoD |
|---|---|---|
| D0.1 | Tokens and `/ui` gallery | Existing mini-spec; isolated review; no token drift |
| D0.2 | Lifecycle/gate badges | Icon+label, not colour-only; all true states represented |
| D0.3 | attribution/provenance/layer chips | Long names/locators responsive; links keyboard accessible |
| D0.4 | Existing primitives on Foundry tokens | No nested-card regressions; focus/error/disabled states |
| D0.5 | ConfirmSheet | Shows exact generated artifact+eval and requires explicit confirm |
| D0.6 | CardStack | Stable phone layout, keyboard alternative and no gesture-only action |
| D0.7 | Drawer | Focus trap/return, URL/deep-link state and responsive full-screen mode |
| D0.8 | DiffView | Human semantic diff primary; raw YAML secondary; additions/removals accessible |
| D0.9 | Tree | Keyboard tree semantics, stable IDs and depth/overflow handling |
| D1.1 | App shell | Role navigation, auth and route skeletons against generated fixtures |
| D1.2 | Dashboard/Queue v1 | Honest validated metrics, live states and no fake prototype counts |

**Shared FE DoD:** WCAG 2.2 AA target; 360px, 768px and 1440px screenshots; no overlap
or clipped text; Vitest/type/lint/build pass; relevant Playwright path passes; no
feature-complete claim from `/ui` gallery alone.

---

## 14. Product and compounding-loop task cards

### E1.1 - Managed source registry and ingestion jobs

**Steps**

1. Add source metadata: owner, purpose, access class, provider-egress permission,
   retention/deletion policy, original hash, MIME, status and timestamps.
2. Persist chunks and locators from F0.4; encrypt/storage hardening follows deployment
   policy, not ad hoc application code.
3. Create idempotent parse jobs and `AgentRun` ledger records.
4. Enforce duplicate detection, access checks and deletion propagation.
5. Expose upload/list/get/chunks/job-status through contract-first endpoints.
6. Record per-layer yield and accepted/rejected candidate counts without source text
   in operational logs.

**DoD:** approved source can be traced and deleted per policy; unauthorized users
cannot enumerate metadata/chunks; identical upload does not duplicate; restart resumes
or safely retries; source text is never sent to a provider unless policy permits.

### E1.2 - Agentic extraction, alignment and critique

Use bounded stages rather than one opaque prompt:

1. **Extractor:** proposes entities, relations, rules, metrics and eval seeds with
   exact evidence spans; no span means rejection.
2. **Normalizer:** resolves duplicates/canonical labels and proposes stable IDs.
3. **Terminology aligner:** proposes internal/external mappings with version/rationale;
   it does not assert equivalence without review.
4. **Scope classifier:** proposes applicability and explicitly flags unknown scope.
5. **Critic:** searches for contradiction, over-generalization, missing exception,
   geography leakage and unsupported causality.
6. **Eval author:** drafts positive, negative, abstention and boundary cases for L3.
7. Validate every stage against typed schema; retry boundedly; persist run ledger,
   raw structured output hash, validation errors and human disposition.
8. Present the combined proposal to a human; only confirm/fix creates a Delta.

**DoD:** adversarial documents cannot create accepted unsupported fields; each field
has evidence or explicit human-authored provenance; model/prompt upgrade is replayable
against a frozen corpus; agents have no ACTIVE/publish credential.

### E1.3 - Intake experience

**Steps**

1. Build Source Library with status, access class, parse warnings and yield.
2. Build two-pane Extraction Sheet with locator-synchronized chunk/evidence view.
3. Candidate card shows layer, node, scope, evidence, confidence basis and critic flags.
4. `Promote` creates a proposed Delta; `Fix` records human amendment; `Reject` requires
   a typed reason usable as evaluation/training feedback.
5. Implement batch selection only after individual provenance is preserved.
6. Test long transcripts, missing pages, permission loss and stale candidate version.

**DoD:** a real VTT and one slide/document source complete source->candidate->Delta;
SME never sees raw YAML; exact evidence remains one interaction away; all action,
error and permission states are accessible on phone and desktop.

### E2.1A - Forge question compiler v0

**Steps**

1. Query four signals: unvalidated artifact, low confidence, missing eval and missing
   anti-pattern/exception.
2. Rank by impact using usage, safety criticality, uncertainty, age and coverage gap;
   record factor breakdown so ranking is explainable.
3. Exclude own artifacts, already-answered assignments, invalid scope and inaccessible
   sources.
4. Emit version-pinned Assay or Name-the-caveat questions with evidence and target.
5. Deduplicate and retire questions when the source artifact changes/resolves.

**DoD:** same corpus snapshot gives deterministic queue; no inaccessible evidence
leaks; retired/stale question cannot accept an answer; impact score is inspectable.

### E2.1B - Forge answer, confirmation and ladder v0

**Steps**

1. Add question/assignment/answer/ratification-event tables and bounded leases.
2. Accept agree/disagree/depends and caveat text with explicit SME confidence.
3. Structure free text into candidate artifact+eval, then require ConfirmSheet approval
   of the exact payload before persistence.
4. Route accepted artifact-producing answers through `submit_mission` and Delta pipe.
5. Preserve raw answer, dissent and amendment attribution; do not average them away.
6. Use states `unvalidated -> endorsed` for k=1. Ratified is impossible in v0.

**DoD:** no accepted answer disappears or writes ACTIVE; unconfirmed model output is
not persisted as knowledge; own-artifact answer is rejected; contribution, Delta,
eval, evidence and actor are linked.

### E2.1C/E2.1D - Forge UI and pilot operations

**Steps**

1. Phone-first five-card shift with time estimate and evidence disclosure.
2. Make `It depends` a first-class path to caveat/ExceptionRule, not a penalty.
3. Show impact history as real release/eval links; no fake counts or public rating.
4. Add resume, expiry, error, offline and accessibility behaviour.
5. Define SME briefing/consent, support contact, data use and withdrawal process.
6. Instrument time, completion, confirmed deltas/evals, correction/reject, return and
   qualitative trust feedback.

**DoD:** 3-5 real SMEs can complete without developer intervention; every displayed
impact is verifiable; no k=1 ratification claim; G2 metrics and cohort limitations are
recorded two weeks later.

### E2.2 - Forge v1 (only after G2 continuation)

**Steps**

1. Add k=3 routing by domain/scope, freshness, conflicts and calibrated reliability.
2. Seed curator-settled gold probes; keep probe content protected and monitor leakage.
3. Establish an unweighted consensus baseline before rating-weighted decisions.
4. Calibrate contribution weights from sufficient probe history; publish uncertainty.
5. Implement contested/adjudication/exception/escalation transitions and Duel.
6. Preserve minority answers verbatim and exclude self/conflicted review.
7. Add ratings/leaderboard only after minimum-sample and calibration DoD is met.

**DoD:** consensus result is reproducible; a split never becomes false certainty;
probe failure lowers trust without deleting contribution history; rating gaming and
rapid-click tests fail; calibration UI states sample size and uncertainty.

### E3.1 - Deep review drawer

**Steps**

1. Render semantic before/after diff; raw YAML stays secondary.
2. Show target artifact version, node/scope, conflicts and job state.
3. Render source/session/Forge evidence with exact locator and permissions.
4. Add dry-run, approve, reject-reason, escalate and edit/resubmit.
5. Curator edits create a new revision with dual attribution, never overwrite SME text.
6. Require fresh ETag/version at decision time.

**DoD:** stale approve returns 409 with safe recovery; inaccessible source is not
leaked; amendment lineage retains both authors; keyboard/screen-reader flow passes.

### E3.2 - Semantic conformance validator

**Steps**

1. Validate stable IDs, parent/reference existence, no hierarchy cycles and no orphan.
2. Detect duplicate canonical labels/aliases in overlapping scope.
3. Validate terminology binding system/code/version and allowed mapping type.
4. Detect overlapping/conflicting applicability, invalid dates and global omissions.
5. Detect rule-priority collisions, missing evidence, stale evidence and missing evals.
6. Produce stable error codes, severity, affected IDs and remediation hints.
7. Run on Delta dry-run, candidate build and release gate.

**DoD:** seeded invalid corpus triggers every rule; no release with validator errors;
warnings require recorded accept/defer; report is deterministic and machine-readable.

### E3.3 - Governed hierarchy operations

**Steps**

1. Model add, rename, move, merge, deprecate and reparent as typed Delta operations.
2. Compute affected descendants, inherited artifacts, mappings, pack slices and evals.
3. Show impact preview before proposal and dry-run again before decision.
4. Keep aliases/redirects for merge/rename and preserve stable IDs.
5. Emit rollback Delta; never directly rewrite history.

**DoD:** every operation is reversible/auditable; cycle/orphan creation fails; pack
composition reflects approved move; existing citations resolve through redirects.

### E3.4 - Mapping and terminology workbench

**Steps**

1. Add typed mapping artifact: exact, close, broader, narrower, related.
2. Add external binding with terminology system, code, display, version and license.
3. Provide side-by-side search/selection, rationale, confidence and evidence.
4. Make mappings governed and scope-aware; detect one-to-many/exact conflicts.
5. Export accepted mappings through the interoperability adapter in Loop 7.

**DoD:** no free-text link type; exact-map conflicts block release; version/license
is visible; mapping change lineage and round-trip tests pass.

### E3.5/E3.6 - Lineage, conflict, dry-run and blast radius

**Steps**

1. Build one query joining source/span -> extraction run -> Delta revisions/decisions
   -> artifact versions -> candidate/releases -> evals -> usage/corrections.
2. Detect conflicts by shared semantic target, scope overlap, priority and mapping.
3. Run proposed Delta against gold/held-out-eligible simulation without contaminating
   held-out answers; return changed firings and failures.
4. Record dry-run input hashes and result digest.
5. Show compile/eval jobs and failure details in Queue/Packs.

**DoD:** lineage answers who stands behind an artifact without log archaeology;
dry-run is reproducible; conflict is not just tag co-occurrence; held-out secrecy is
preserved; expensive run has bounds and timeout.

### E4.1/E4.2 - Composer and gated publication

**Steps**

1. Compose by stable nodes, layers, functions and dependency version pins.
2. Preview inclusions/exclusions, inherited/overridden artifacts, unresolved conflicts
   and estimated context footprint.
3. Build candidate and run validator/eval pipeline.
4. Show receipt: case provenance counts, failure classes, with/without performance,
   uncertainty and SME-held-out count.
5. Authorize publish separately; omit/disable publish structurally on failure.
6. Produce immutable version diff and withdrawal/deprecation path.

**DoD:** same manifest/pins reproduce digest; excluded artifacts cannot hydrate;
failing/changed candidate cannot publish; release UI never labels an internal case
SME-held-out; authorization and audit tests pass.

### E4.3/E4.4 - Release attestation and consumption

**Steps**

1. Emit `ReleaseAttestation` and integrity digest; name it digest/seal until real
   cryptographic authorship signing exists.
2. Verify attestation and receipt at registry load and before context serve.
3. Return pack/version/attestation and relevant artifact citations in trust envelope.
4. Provide REST/MCP examples and try-it console with bounded input and safe output.
5. Test old/withdrawn/tampered/unknown pack and artifact-path attacks.

**DoD:** agent can cite exact released artifact; tamper/withdrawal blocks production;
REST and MCP apply identical eligibility; docs do not overclaim cryptographic signing.

### E6.1/E6.2 - Continuous learning and correction reuse

**Steps**

1. Define privacy-safe usage/outcome event with tenant/engagement, agent, task,
   pack/version, artifact IDs, result class, latency and optional feedback reference.
2. Do not log prompt/source/customer text by default; enforce retention and ownership.
3. Capture explicit correction, abstention failure, eval failure and low-confidence
   consultation as typed learning signals.
4. Convert accepted correction to proposed artifact Delta plus regression EvalCase.
5. Route through normal review/build/eval/release; link contribution to shipped impact.
6. Measure recurrence and correction reuse across future consultations.

**DoD:** one real agent failure completes the full return loop; no feedback auto-
promotes; deleted/restricted data is not retained in telemetry; impact feed links to
real release/eval; recurrence metric has a documented denominator.

### E7 - Standards and interoperability (after G4)

**Steps**

1. Define stable internal concept URI policy without making file paths identities.
2. Implement SKOS/JSON-LD export for nodes, labels, hierarchy and mappings.
3. Add import validation, namespace collision handling and explicit loss report.
4. Add RDF/OWL adapter only for a named interoperability need; never promise lossless
   round-trip for unsupported constructs.
5. Test reference fixtures and terminology version changes.

**DoD:** exported graph validates; import cannot bypass Deltas; loss is explicit;
license/restriction metadata survives; internal packs do not depend on RDF tooling.

### E5 - Studio (last, after Intake quality and G2)

**Steps**

1. Store conversation/turns as a managed source under the same access policy.
2. Structure only fields grounded to an exact turn/span; bounded retry on violation.
3. Ask boundary/exception questions for under-scoped L3 proposals.
4. Keep staged objects session-local and visually distinct from corpus knowledge.
5. Confirm exact object+eval; commit emits one proposed Delta per object.
6. Preserve speaker, turn, span, model run and human amendment lineage.

**DoD:** adversarial replay yields zero accepted invented fields; abandoning session
does not mutate corpus; access/deletion propagates; every committed object reaches the
same queue; Studio does not introduce a third extraction stack.

### E8 - Enterprise overlays and tenancy (second-consumer gate)

**Steps**

1. Define tenant, client and engagement ownership at API, row and storage boundaries.
2. Add base->client->engagement inheritance and explicit override/conflict rules.
3. Prove cross-tenant denial for list, ID-guess, search, export, job and MCP paths.
4. Add SSO/role mapping, retention/deletion/legal-hold and audit export as required.
5. Implement Postgres only when measured concurrency/tenant needs justify it, with
   migration and load tests.
6. Add cryptographic signing/key rotation only where distribution requires authorship.

**DoD:** automated isolation suite has zero cross-tenant disclosure; overlay composes
without copying base; deletion/restore drills pass; second domain/client introduces no
schema fork; operational SLOs are measured.

## 15. Verification matrix

| Area | Required verification |
|---|---|
| Governance | state/property tests, concurrent decisions, idempotency, restart, one-pipe bypass attempts |
| Auth/security | 401/403/ownership matrix, ID guessing, path traversal, upload bounds, log/secret scan |
| Contracts | OpenAPI lint, generated-client drift, request/response/error contract tests |
| Persistence/jobs | migration/restore, transaction rollback, lease expiry, retry/dead-letter, duplicate suppression |
| Semantics | references/cycles/scope/mapping/priority/evidence/expiry validator fixtures |
| Agentic extraction | frozen corpus replay, schema/grounding adversarial cases, model/prompt run ledger |
| Evaluation | split/leakage checks, applicability cases, independent replay, gate/TOCTOU negatives |
| Packs/runtime | digest/attestation, tamper/withdraw, artifact eligibility, REST/MCP parity, token/latency |
| Frontend | unit/component, axe/accessibility, keyboard, 360/768/1440 screenshots, Playwright live paths |
| Learning loop | feedback privacy, correction-to-Delta/eval, recurrence/reuse and impact lineage |

Minimum live Playwright paths: login/approve/restart; intake/promote; Forge shift;
conflict/dry-run/amend/approve; failed publish then passing publish; MCP consume;
agent correction returns to queue.

## 16. Final system DoD and reviewer protocol

The desired goal is reached only when:

1. G0-G4 are VERIFIED at reviewed integrated SHAs.
2. Full gate set passes on every shipped package, including retained CTX.
3. Live demonstrations use approved real data and named principals.
4. The released pack has claim-level evidence, structured applicability, SME evidence
   and credible held-out evaluation; generated content is labelled honestly.
5. Public serve stays key-free/Tier-A and private worker runs replayable jobs.
6. Candidate/release separation and registry checks make gate bypass impossible.
7. A real agent consumption and correction complete the compounding loop.
8. SME and value metrics pass continuation tests or deferred modules stay stopped.
9. Backup/restore, withdrawal and failure recovery are demonstrated.
10. REV has no P0/P1 findings and all accepted P2 debt has owner/date/kill criterion.

### Read-only review execution

INT gives REV the accepted mini-spec, baseline SHA, submitted SHA and evidence bundle.
REV works in a detached read-only worktree and may run tests/static analysis but may
not edit files, commit, push, merge or update status. Findings lead, with severity,
file/line evidence, reproduction and missing tests. A new builder commit starts a
new review. INT alone merges the passed SHA and records VERIFIED evidence.
