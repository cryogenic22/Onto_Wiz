# Onto_Wiz Foundry - Delivery Loops Backlog v2.0

**Date:** 2026-07-10 - **Cadence:** 2-week loops; units are at most one person-week
**Normative build detail:** `BUILD_INSTRUCTION_SET_2026-07.md` - **Status:** `docs/PROJECT_STATUS.md`

**North star:** an SME's tacit judgment enters through Intake / Forge / Capture / Studio and leaves as a gated, versioned, provenance-carrying pack that measurably lifts an agent — with every object SME-ratified and every change through one governed pipe.

---

## 0A. v2 delivery contract (normative)

Sections 0A-0C and sections 4-7 are the v2 control layer. They supersede any
conflicting wording in the original loop summary retained below.

### Product outcome

Onto_Wiz is a Domain Intelligence Foundry: managed evidence and tacit SME judgment
become governed, versioned, eval-gated Domain Packs consumed through REST/MCP.
The architecture may support any domain, but the first proof stays deep in pharma
commercial operations until the factory has produced two credible reusable packs.

The production loop is:

```text
source -> chunks/locators -> agent candidates -> SME confirm/correct/dissent
       -> persistent Delta -> curator review/dry-run -> candidate pack
       -> held-out eval/lift -> gated release -> agent telemetry
       -> failure/correction -> new Delta + regression eval
```

### Twelve-week exit criteria

1. One deployed `ontowiz-serve` owns auth, capture, intake, governance, ontology,
   packs, catalog, REST context and MCP context.
2. No production client calls `src/`; deletion occurs only after route-equivalence
   and migration evidence passes independent review.
3. A real source reaches a proposed Delta with source hash, chunk, exact locator,
   quoted span, access class and extraction-run identity intact.
4. Every mutation uses the persistent Delta pipe and a named JWT principal.
5. Candidate packs can be evaluated, but publish and production serving reject
   an unrun or failing gate.
6. One pharma pack ships with SME-authored held-out cases, applicability coverage,
   reproducible lift receipt and named SME endorsement/ratification.
7. A real agent consumes that pack and emits privacy-safe usage events tied to
   pack version and artifact IDs.
8. A real failure or SME correction becomes a Delta plus regression eval and
   returns to the queue.
9. Three to five real SMEs complete the pilot; quality, effort, dissent, return
   rate and downstream impact are measured.
10. A second function slice or client overlay reuses the governed base without
    copying source artifacts or forking the schema.

### Status vocabulary

| Status | Meaning | Who may set it |
|---|---|---|
| `PLANNED` | Sequenced; mini-spec not accepted | Integrator |
| `READY` | Preconditions and mini-spec accepted | Integrator |
| `IN PROGRESS` | Builder branch/worktree active | Builder |
| `READY FOR REVIEW` | Evidence frozen at submitted SHA | Builder |
| `CHANGES REQUIRED` | Blocking review finding | Read-only reviewer |
| `VERIFIED` | Reviewed SHA merged and independently proven | Integrator only |
| `BLOCKED` | External dependency prevents progress | Integrator |

Builders never mark their own unit `VERIFIED`. Only verified outcomes are copied
to `docs/PROJECT_STATUS.md`.

### Current baseline - 2026-07-10

| Unit | Status | Honest boundary |
|---|---|---|
| F0.1 CI gate set | `VERIFIED` | Frontend Vitest blocks; quality/slop advisory |
| F0.2 governance persistence | `VERIFIED` | Restart-safe; not served by Delta routes |
| D0.1 tokens/gallery | `IN PROGRESS` | Working-tree implementation requires isolated review and merge |
| F0.2H persistence hardening | `PLANNED` | State preconditions, idempotency, links, indexes, concurrency |
| F0.3 unified API | `PLANNED` | SME/review surface remains on legacy backend |
| F0.4 parser port | `PLANNED` | Parsers remain under `src/knowledge` |
| F0.6 release integrity | `PLANNED` | Served `0.3.0` has `gate_passed: false` |
| F0.7 hierarchy/applicability | `PLANNED` | No canonical governed node and scope model |
| F0.8 deployment | `PLANNED` | No accepted live-environment evidence |
| F0.9 CTX scope/coverage | `PLANNED` | Retained CTX remains outside full coverage gate |

This table is reconciled with `PROJECT_STATUS.md` at every loop close.

## 0B. Team topology and review isolation

| Lane | Owns | Must not own |
|---|---|---|
| Backend / Factory (BE) | `packages/`, API/OpenAPI, generated client, migrations, jobs, compiler, eval runner, MCP | Product UI or self-approval |
| Frontend (FE) | `frontend/`, state, accessibility, component/e2e tests | Endpoint shapes, DB rules, direct corpus writes |
| Knowledge & Evaluation (KE) | Ontology content, mappings, evidence policy, eval protocol, SME pilot | Runtime bypasses or marking generated content validated |
| Integrator / Release (INT) | Baseline SHA, contracts, merge order, deployment, status | Implementing and approving the same unit |
| Read-only Reviewer (REV) | Independent diff/quality/threat review and verdict | Editing, committing, pushing, merging, or changing DoD |

One person may cover multiple lanes only across different units. A builder cannot
be the final reviewer for the same submitted SHA.

### Branch and worktree protocol

1. INT publishes a pinned loop baseline SHA.
2. Each unit uses `build/<unit-id>-<short-name>` in its own worktree.
3. The builder writes only within unit ownership paths and the accepted mini-spec.
4. BE merges OpenAPI, generated TypeScript client and fixtures before FE starts a
   feature. FE does not hand-write endpoint calls or response types.
5. The builder submits one immutable review SHA plus the evidence bundle in section 6.
6. REV checks out that SHA in a detached worktree such as
   `C:/tmp/ontowiz-review-<unit>-<sha>` with filesystem write, commit, push and merge
   permissions disabled.
7. REV reports findings only. P0/P1 block; P2 needs an explicit accept/defer decision.
8. New commits invalidate the prior verdict. INT merges only the reviewed SHA.

### Change control

- Acceptance criteria freeze when a unit becomes `READY`.
- A design error requires a spec amendment and decision-log entry before code changes.
- Scope changes occur at loop boundaries unless a P0 security, data-loss or governance
  bypass issue requires immediate action.
- Prototype interactions are intent, not evidence of implemented behaviour.
- `PROJECT_STATUS.md` records verified outcomes, not builder claims.

## 0C. Gates and dependencies

| Gate | Required outcome | Required evidence |
|---|---|---|
| G0 - One System | Persistent authenticated create/review/activation in one service; legacy callers gone | Restart demo, principal audit, one-pipe test, live Playwright/curl |
| G1 - Trustworthy Intake | Real source -> grounded candidate -> Delta; no ungrounded promotion | Golden/adversarial tests and source-to-Delta trace |
| G2 - Pilot / Ratification | Real SMEs create useful artifacts/evals and return | Cohort log, deltas/SME-hour, return, dissent and correction metrics |
| G3 - Semantic Quality | Hierarchy, applicability, mappings, conflicts, lineage and validation are governed | Validator report, reparent Delta, mapping and lineage demo |
| G4 - Gated Release | Attested passing pack consumed by a real monitored agent | Eval receipt, release digest, MCP trace and usage-to-artifact trace |

Hard dependency order:

```text
F0.2H -> F0.3A -> F0.3B -> F0.3C -> F0.3D -> F0.5
F0.4A -> F0.4B -> E1.1 -> E1.2 -> G1
F0.6A -> F0.6B -> E4.1 -> G4
F0.7A -> E3.2 -> E3.3 -> G3
G1 -> E2.1 -> G2 -> E2.2
G4 -> E6.1 -> E6.2
```

---

## 0. First, your question: should the backend team own the FE↔BE linking?

**Yes — with one refinement, and it's the thing that makes the whole parallel plan work.** Raw "backend does integration" has a known failure mode: FE builds against imagined APIs for two weeks, then integration becomes a crunch of mismatched shapes and blame. The refinement is **contract-first**: the BE team's first deliverable in every loop is not the implementation but the **handshake artefact** — the OpenAPI contract for that loop's endpoints, the generated TypeScript client, and a fixture pack (realistic mock responses). FE builds the whole loop against the mock client; BE implements against the same contract; in the last 2–3 days of the loop BE swaps mocks for real and owns making the wire work (auth, error shapes, pagination, latency).

So the allocation you proposed stands: **BE owns the contract, the generated client, the fixtures, and the final wiring. FE never hand-writes a fetch call** — it consumes the typed client only. What FE owns is everything from the client boundary up: components, state, interaction, accessibility, tests. The rule that keeps everyone honest: *if integration breaks, the contract was wrong or the implementation drifted from it — both BE-owned; if the UI misuses a correctly-shaped response, that's FE-owned.* Clean seam, no blame ambiguity, and each loop ends with a joint demo on the live URL, never on mocks.

---

## 1. The loop map (what runs in parallel, what must be sequential)

```
Loop 0        Loop 1        Loop 2        Loop 3        Loop 4        Loop 5        Loops 6–8
Foundations   One System    Intake        Forge v0      Curation      Compose &     Forge v1 →
(parallel,    (G0 gate)     (+ gate       (G1: PILOT    Depth +       Release       Studio
no wire)                    release gate) STARTS)       Ontology v1   (G3 gate)     (gated)
BE ████       BE ████       BE ████       BE ████       BE ████       BE ████       BE ████
FE ████       FE ████       FE ████       FE ████       FE ████       FE ████       FE ████
   no integ.     integ.²       integ.²       integ.²       integ.²       integ.²      integ.²
```
² = BE-owned wiring in the final days of the loop, joint demo to close.

Sequencing constraints that cannot be traded away: persistence (L0) before anything user-facing; one authenticated backend (L1) before any new station; candidate/release separation and production gate enforcement (L2) before the pilot; Forge v0 (L3) *is* the pilot instrument so it lands exactly at pilot start; Forge v1 waits for pilot evidence; Studio waits for Intake's extraction machinery to be proven in batch. Everything else parallelises.

---

## 2. The loops

### Loop 0 — Foundations (weeks 1–2) · *fully parallel, deliberately zero integration*

| | Backend team | Frontend team |
|---|---|---|
| Work | **F0.1/F0.2 VERIFIED** · **F0.2H** harden state/idempotency · **F0.3A** OpenAPI/client/fixtures · **F0.4A** canonical parser boundary | **D0** deliver tokens and components through the zero-dependency `/ui` gallery + Vitest · **D1** role-shaped shell against generated fixtures |
| Exit demo | Restart-survival remains green; generated contract/client/fixtures compile | `/ui` gallery at phone/desktop widths; shell click-through in both roles |

### Loop 1 — One System (weeks 3–4) · **gate G0**

| | Backend team | Frontend team |
|---|---|---|
| Handshake (day 1–2) | **Contract v1:** `/v1/auth`, `/v1/deltas` (list/get/approve/reject/escalate/resubmit), `/v1/ontology` (nodes + layers read), dashboard stats + fixtures | — consumes |
| Work | **F0.3** port the ~14–18 SME endpoints under JWT/real principals · **F0.7** hierarchy `parent` + roll-up query · **F0.8** deploy to Railway · **F0.5** delete `src/` + gate 6 once FE has re-pointed | **Dashboard** (stat tiles, expandable coverage board, attention feed) and **Curation Queue v1** (table + drawer with human-readable diff, approve/reject) — built on mocks days 1–8 |
| Integration (BE, days 8–10) | Swap mock→real; auth flows; error/empty/loading states verified against live | joint bug-bash |
| Exit demo | On the **live URL**: log in as curator, approve a delta, restart the server, approval survives, audit shows a named principal. Legacy `src/` deleted same day. |

### Loop 2 — Intake + Gate Integrity (weeks 5–6)

| | Backend team | Frontend team |
|---|---|---|
| Handshake | Contract v2: `/v1/intake` (sources, candidates, promote/edit/reject) + fixtures incl. a real parsed VTT | — |
| Work | **E1** extraction job (layer-classified candidates w/ seeding sentence + locator + paired eval for L3), sources/candidates tables + API · **F0.6A/B** candidate build separated from publish; production rejects failed/unrun gates; re-evaluate 0.3.0 and fix geography leakage | **SourceLibrary** (yield-by-layer chips, promoted x/y) · **ExtractionSheet** (two-pane: highlighted transcript ↔ candidate list, click-to-jump) · **CandidateCard** (promote / fix / reject-with-reason) |
| Exit demo | Drop the real Field Force QBR .vtt on the live system → triage a candidate → its delta appears in the queue with the seeding sentence in the evidence pane. The served pack has `gate_passed: true` + a lift number. **Metric live:** candidates promoted/SME-hour. |

### Loop 3 — Forge v0 (weeks 7–8) · **gate G1 — the pilot starts here**

| | Backend team | Frontend team |
|---|---|---|
| Handshake | Contract v3: `/v1/forge` next/answer/impact + fixtures for both mission types | — |
| Work | **E2.1** question compiler (signals 1–3, 8), Assay + Name-the-caveat via existing `submit_mission`, ratification-ladder states, impact feed, k=1 routing · **theatre-alarm telemetry** (deltas/SME-hour) from day one | **ShiftQueue** card stack (mobile-width first), **AssayCard**, **CaveatCard**, shared **ConfirmSheet** ("here's the artifact + eval I drafted — ship it?"), **ImpactPanel v0**, ratification-ladder tile on dashboard |
| Exit demo | A real SME completes a 5-question shift on a phone in <4 min; every answer visible in the queue as delta+eval; SME-validated % ticks up on the dashboard. **Pilot cohort (3–5 ZS SMEs) onboarded this week.** |

### Loop 4 — Curation Depth + Ontology v1 (weeks 9–10) · *pilot running in background — expect interrupt capacity ~20%*

| | Backend team | Frontend team |
|---|---|---|
| Handshake | Contract v4: dry-run endpoint, conflict detection, lineage query, layer CRUD-as-deltas | — |
| Work | **E3.1-be** conflict detector (shared tags/adjacent priority), `GET /deltas/:id/dryrun` on gold set, lineage query · **E3.2-be** structured editors' delta composition per layer | **Drawer upgrade** (conflict callout, dry-run button, source-specific evidence renderers, edit-and-resubmit w/ dual attribution) · **Layer browser** L1–L5 with structured editors, node column, inheritance chips · **Lineage tab** |
| Exit demo | The full DELTA-147 flow from the prototype, live: conflict warning → dry-run → edit → approve → watch recompile+eval toast sequence → new version in Packs. |

### Loop 5 — Hierarchy, Mappings, Compose & Release (weeks 11–12) · **gate G3**

| | Backend team | Frontend team |
|---|---|---|
| Work | **E3.3-be** hierarchy ops as deltas + reparent · **E3.4-be** mappings (synonym, cross-domain) as governed artifacts · **E4-be** pack composer (node+layer selection → manifest), version diff, publish gated | **Manage-hierarchy mode**, **Mapping Workbench** (side-by-side, typed links), **Pack composer + release-gate panel** (publish button structurally absent when failing), **consume tab** + try-it console |
| Exit demo | Compose a pack scoped to Commercial › Payer/Access + Field Force → gate passes with ≥1 SME-authored held-out eval → publish → an agent consumes it via MCP live. |

### Loops 6–8 — Evidence-gated expansion (months 4–6)

**Loop 6 — Forge v1** (gated on the G1+2wk kill-test: deltas/SME-hour ≥ quick-capture baseline AND week-2 return > 0): BE — k=3 routing, `resolve_consensus`, gold probes + weights, Duel + Hunt signals; FE — DuelCard, calibration panel, crew standing, corpus heat. **Loop 7 — Standards & graph:** BE — standards-glossary mapping API, graph query; FE — standards workbench tab, read-only reactflow graph. **Loop 8 — Studio** (gated on Intake extraction quality proven in batch): BE — conversation-as-source service, the grounded structurer contract (quoted-span validation, boundary-question behaviour), stage/commit; FE — StudioCanvas (dashed staging), TurnStream, commit flow. If the pilot evidence is weak, Loops 6–8 are replaced by hardening Intake + Queue — that decision is taken at the loop boundary, not mid-loop.

---

## 3. Standing rules for every loop

1. **Handshake before build:** no FE story starts until the loop's contract + fixtures are merged (BE days 1–2). A contract change mid-loop is a BE bug.
2. **Integration is a BE deliverable** with a named owner per loop; FE pairs on the bug-bash but the wire is BE's to make good.
3. **Demo on the live URL or it didn't happen.** Mock-only demos don't close a loop.
4. **The unit loop discipline (R2) applies inside both lanes:** mini-spec → failing test → implement → gates → PROJECT_STATUS evidence.
5. **One pipe regression suite runs every loop** — a test that actively attempts to mutate the corpus around the delta pipe and must fail.
6. **Loop boundaries are the only place scope changes.** Pilot feedback lands in a triage list, not in the current loop.
7. **Metrics reviewed at every close:** deltas/SME-hour, SME-validated %, median review latency, pilot return rate — the north-star dashboard is itself a Loop 1 deliverable and never regresses.

---

## 4. v2 detailed delivery units

These units replace coarse epic-sized assignments. Each unit is at most one
person-week and receives its own mini-spec, branch, review SHA and verdict.

### Loop 0 - Controlled foundations (current, weeks 1-2)

**Goal:** durable primitives, frozen contracts and reusable UI. No feature-level
FE/BE integration occurs before the contract handshake.

| Unit | Owner | Depends on | Deliverable |
|---|---|---|---|
| F0.1 | BE | none | CI gate set - `VERIFIED` |
| F0.2 | BE | F0.1 | Durable governance records - `VERIFIED` |
| F0.2H | BE | F0.2 | Lifecycle preconditions, idempotent decisions, version checks, foreign links and indexes |
| F0.3A | BE | F0.2H | OpenAPI for auth, Deltas, capture, audit and contributors; generated TS client and fixtures |
| F0.4A | BE/KE | none | Canonical `Source`, `Chunk`, `Locator` and parser protocol; PDF/DOCX/TXT/VTT golden files |
| D0.1-D0.9 | FE | none | Tokens/gallery, badges, chips, primitives, confirm sheet, stack, drawer, diff and tree |
| D1.1 | FE | D0.1 | Role-shaped shell and route skeletons using fixtures |

**Loop 0 DoD:** generated client compiles; restart survival stays green; `/ui`
demonstrates completed components at desktop and phone widths; no consumer invents
an API shape; all units meet section 5.

### Loop 1 - One authenticated system (weeks 3-4, closes G0)

| Unit | Owner | Depends on | Deliverable |
|---|---|---|---|
| F0.3B | BE | F0.3A | Served Delta/review/audit/contributor routes on `GovernanceStore`, JWT and common errors/pagination |
| F0.3C | BE | F0.3B | Approval -> canonical bridge -> versioned artifact -> durable job/outbox; idempotent retry |
| F0.3D | BE+FE | F0.3B | Generated client switches fixtures to live API; auth/error/empty/loading/retry states |
| F0.7A | BE/KE | F0.3A | Stable domain-node and applicability contracts, roll-up query and commercial migration |
| D1.2 | FE | F0.3A | Dashboard and Queue v1 with readable diff, evidence summary and review actions |
| F0.8A | INT/BE | F0.3C | Live deployment, health/readiness, persistent volume, secrets and backup/restore smoke |
| F0.5 | BE+FE | F0.3D | Route-equivalence proof; delete `src/`; collapse duplicate models; remove obsolete gate 6 |

**Exit demo:** on the live URL, a named curator approves a proposal. Restart retains
the Delta, decision, audit and resulting artifact/job state. The production app has
no import or call to `src/`.

**G0 DoD:** authorization negatives pass; double/concurrent approval is deterministic;
every mutation has idempotency and actor; restore works; route inventory is complete;
REV finds no alternate ACTIVE write.

### Loop 2 - Intake and release integrity (weeks 5-6, closes G1)

| Unit | Owner | Depends on | Deliverable |
|---|---|---|---|
| F0.4B | BE/KE | F0.4A | PPTX/XLSX/EML; type/size bounds, quarantine and locator fidelity |
| E1.1 | BE/KE | F0.4B,F0.7A | Managed sources/chunks, hashes, access class, retention, ingestion jobs and run ledger |
| E1.2 | BE/KE | E1.1 | Layer-classified extraction with exact span, model/prompt version, scope and paired L3 eval |
| E1.3 | FE | E1.1 contract | Source Library, Extraction Sheet, promote/fix/reject and evidence renderers |
| F0.6A | BE | F0.3C | Candidate build separate from release publish; publish/production registry reject failed or unrun gates |
| F0.6B | KE/BE | F0.6A | Geography-safe held-out suite, leakage checks, reproducible lift receipt and `0.4.0` decision |
| F0.9 | BE | F0.6A | Keep product-used CTX only; >=85% shipped-code coverage; remove checked-in build copies |

**Exit demo:** ingest an approved VTT, inspect a candidate beside its timestamp,
correct scope and promote it. Show a failing candidate pack blocked from publish
and production serve, then publish a passing release with its receipt.

**G1 DoD:** every accepted candidate has valid source/chunk/locator/span hashes;
adversarial corpus produces no ungrounded accepted field; rejections preserve reason;
source permission is enforced; `0.3.0` is not production default.

### Loop 3 - Forge v0 and real SME pilot (weeks 7-8, closes G2)

| Unit | Owner | Depends on | Deliverable |
|---|---|---|---|
| E2.1A | BE/KE | G1 | Questions for unvalidated, low-confidence, missing-eval and anti-pattern gaps |
| E2.1B | BE | E2.1A | k=1 assignment/answer/confirm API; Assay/Caveat; contribution and ladder events |
| E2.1C | FE | E2.1B contract | Phone-first ShiftQueue, ConfirmSheet, impact history and honest validation state |
| E2.1D | KE/INT | E2.1C | Cohort onboarding, consent, support process and metric review |

Pilot rules: k=1 means **endorsed**, never ratified. No public leaderboard or
calibration score before probes and adequate samples. SMEs cannot ratify their own
artifact. Dissent remains verbatim. Confirmation shows the exact Delta and eval.

**Exit demo:** a real SME completes five phone-width questions in under four minutes.
Each accepted answer creates a Delta+eval or typed ladder event and can be traced to
queue status and later pack impact.

**G2 continuation test after two weeks:** proceed to Forge v1 only when useful
deltas/SME-hour meet quick capture, at least one SME returns, no unresolved trust
issue exists and curator correction is acceptable. Otherwise freeze Forge at v0.

### Loop 4 - Curation and semantic quality (weeks 9-10, closes G3)

| Unit | Owner | Depends on | Deliverable |
|---|---|---|---|
| E3.1 | BE+FE | G0 | Three-pane drawer, dual attribution, evidence, conflict and edit/resubmit |
| E3.2 | BE/KE | F0.7A | Validator for references, cycles, labels, scope overlap, stale evidence and priorities |
| E3.3 | BE+FE | E3.2 | Governed add/rename/move/merge/reparent with impact preview and rollback Delta |
| E3.4 | BE/KE/FE | E3.2 | exact/close/broader/narrower/related mappings and versioned terminology bindings |
| E3.5 | BE+FE | E3.1 | Origin -> Delta -> artifact -> pack -> eval lineage and read-only graph |
| E3.6 | BE | F0.6B,E3.1 | Gold-set dry-run, blast-radius diff and visible compile/eval job state |

**Exit demo:** conflict -> evidence -> dry-run -> curator amendment -> approve ->
candidate build -> eval -> gated version using real persisted data. Reparent a rule
without losing its stable ID or provenance.

**G3 DoD:** release candidate has no unresolved semantic errors; active L3 rules
carry applicability, evidence and eval linkage; hierarchy/mappings are Deltas;
lineage answers who, source, decision, pack and eval in one query.

### Loop 5 - Compose, publish, consume and learn (weeks 11-12, closes G4)

| Unit | Owner | Depends on | Deliverable |
|---|---|---|---|
| E4.1 | BE+FE | G3,F0.6A | Compose by node/layer/function; dependency pins, exclusions and candidate/release state |
| E4.2 | BE+FE/KE | E4.1,F0.6B | Gate panel, held-out count, lift receipt, version diff and publish authorization |
| E4.3 | BE | E4.2 | Attestation: digest, source commit, compiler/model versions and eval-receipt hash |
| E4.4 | BE+FE | E4.2 | REST/MCP consume tab and live try-it with trust envelope and artifact citations |
| E6.1 | BE | E4.4 | Privacy-safe usage/outcome events tied to agent, pack version and artifact IDs |
| E6.2 | BE/KE/FE | E6.1 | Failure/correction -> Delta + regression eval -> queue -> impact trace |

**Exit demo:** compose Payer/Access + Field Force; block a failed release; publish a
passing release with SME held-out evidence; consume it from a real agent; submit a
correction and trace it into the next candidate.

**G4 DoD:** production serves passing releases only; attestation reproduces release;
responses identify pack/artifacts; telemetry excludes source text and PII by default;
correction reuse is measured.

### Loops 6-8 - evidence-gated compounding (months 4-6)

- **E2.2 / Loop 6 - Forge v1:** after G2 only: k=3 routing, neutral consensus baseline,
  probes, calibrated weights, self-answer/conflict exclusions, Duel, escalation and
  dissent-preserving ExceptionRules. Expose ratings only when statistically honest.
- **E7 / Loop 7 - Interoperability:** stable concept IDs, terminology bindings, SKOS/JSON-LD
  export, source/license registry and semantic conformance. RDF/OWL round-trip only
  for a named client need, with a loss report.
- **E5 / Loop 8 - Studio:** after Intake quality and SME return: conversation-as-source,
  exact-span grounding, staged proposals, boundary questions, confirm and Delta commit.

If evidence fails, replace expansion with source coverage, eval quality, queue
ergonomics and operational hardening.

### E8 / Months 7-12 - conditional enterprise reuse

- Client/engagement overlays with inheritance and override-conflict tests.
- Tenant isolation, SSO, retention/deletion, legal hold, export and restore drills.
- Postgres only when a second tenant or measured concurrency requires it.
- Cryptographic release signing where authorship verification is required; do not
  describe the current digest as a signature.
- A second domain pack built without schema forks or copied base artifacts.
- SLO/performance work driven by measured ingestion, review and serving load.

## 5. Definition of Done

Every unit must satisfy all applicable items:

1. Accepted mini-spec names files, contracts, migration, threats, tests, rollback
   and explicit out-of-scope items.
2. Tests demonstrate red before implementation and green after it.
3. Shipped paths have >=85% coverage; governance/auth/publish/tenant boundaries
   include branch, negative and concurrency tests.
4. Ruff, mypy, pytest, boundaries, FE type/lint/build/Vitest and relevant Playwright
   pass in a clean environment.
5. OpenAPI, generated client, fixtures and implementation have no drift.
6. Mutations include principal, idempotency, audit and domain provenance.
7. Error, empty, loading, retry, permission-denied and concurrent-action states are
   implemented and tested.
8. Security covers input bounds, authorization, ownership, secrets, source
   sensitivity and model-provider data egress.
9. Migration includes forward and restore/rollback evidence.
10. Documentation is honest: no fixture, prototype, generated content or internal
    benchmark is represented as externally validated.

A loop closes only when gate units are VERIFIED, integrated SHA passes all gates,
the live demo succeeds without mocks, metrics and limitations are recorded, and INT
updates `PROJECT_STATUS.md`.

## 6. Review evidence bundle

The builder submits:

- unit ID, mini-spec, baseline SHA, review SHA and exact file list;
- acceptance-criterion-to-test mapping;
- exact test/type/lint/build commands and summarized results;
- coverage and negative/mutation/concurrency test notes;
- OpenAPI and schema/migration diff;
- threat-model and data-classification delta;
- screenshot/video or curl/MCP transcript of acceptance behaviour;
- performance for affected hot paths;
- rollback procedure and known limitations;
- confirmation that unrelated working-tree changes are excluded.

REV returns line-grounded findings, commands used, residual risk and one verdict:
`PASS`, `PASS WITH ACCEPTED P2`, or `CHANGES REQUIRED`. New commits require review.

## 7. Metrics, kill tests and standing controls

### Trust and semantic quality

- active artifacts with claim-level evidence;
- artifacts with jurisdiction, temporal and population/function applicability;
- SME-endorsed and independently ratified percentages, reported separately;
- conflicts, dangling references, stale evidence and unmapped terms;
- held-out eval coverage by artifact, task, geography and failure mode.

### SME and agent value

- time to first useful Delta; governed deltas and accepted evals per SME-hour;
- curator edit/reject rate by capture route; week-2/week-4 return;
- dissent, exception yield, adjudication time and contribution-to-release lead time;
- with/without-pack results with case counts and uncertainty;
- abstention, safety, geography and temporal-scope error rates;
- context hit/citation/token measures; correction recurrence and reuse;
- ingestion/review/release latency, retry/dead-letter rate and serving SLO.

### Kill tests

1. If SMEs do not return or Forge does not beat quick capture, stop after v0.
2. If an independent stakeholder rejects the eval receipt, stop catalog/marketplace
   work and repair evaluation design.
3. If reuse needs copying or client schema forks, stop adding domains and repair
   layers, applicability and dependencies.
4. If source rights or provider terms forbid approved use, block ingestion rather
   than weaken provenance or audit.

### Standing controls

1. Contract before consumer; generated client before feature UI.
2. One persistent Delta pipe for every human, system and agent mutation.
3. Agents propose; named humans and policy promote.
4. Candidate builds may fail; release and production serving may not bypass gates.
5. Dissent and uncertainty are knowledge, not noise.
6. Geography and applicability are first-class fields.
7. Evidence is claim-level and navigable to its source locator.
8. Loop demos use live service and real approved data, not fixtures.
9. Builder, reviewer and integrator remain separated per submitted SHA.
10. Code existence is not completion; independent evidence and review close a unit.
