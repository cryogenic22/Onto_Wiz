# Domain Discovery to Pack - Backend Build Instruction Set

**Status:** DRAFT FOR INT/REV - not implementation authorization  
**Date:** 2026-07  
**Reference vertical:** Pharma Launch Control Room  
**Applies to:** any domain assembled from documents, presentations, transcripts, structured data, and SME judgment

## 1. Executive Decision

Onto_Wiz has the correct architectural ambition for this workflow, but the current
repository does not yet provide an end-to-end production path from a client corpus to
a released domain pack.

Build the missing capability as a **generic Domain Discovery and Curation backend**.
Launch Control Room is its first reference vertical, not a separate application or
special-purpose extraction stack.

The required path is:

```text
immutable sources
  -> deterministic parsing and exact spans
  -> versioned agentic extraction runs
  -> typed candidates and relationship proposals
  -> normalization, reconciliation and coverage analysis
  -> targeted SME ratification and challenge
  -> proposed Deltas and regression evals
  -> curator decisions
  -> deterministic candidate compile
  -> independent evaluation receipts
  -> release attestation
  -> typed REST/MCP context operations
  -> usage/correction feedback into new Deltas
```

Claude, Codex, or another coding/chat agent may act as a client of this backend during
development and internal curation. It must not become the workflow database, source of
record, identity provider, approval mechanism, or only user experience.

## 2. Grounded Repository Audit

### 2.1 Capability scorecard

| Capability | Current implementation | Status | Required decision |
|---|---|---|---|
| Canonical artifact lifecycle | `ontowiz_spec.ArtifactBase`, lifecycle transitions and Delta-backed ACTIVE/VERIFIED checks | Partial foundation | Retain and extend |
| Generic knowledge artifacts | MetricDefinition, SourceContract, QuestionPlaybook, DecisionHeuristic, ProcessPlaybook, AntiPattern, ExceptionRule, EvalCase | Partial | Current schemas are too thin for launch decisions, temporal questions, tables, joins and exact evidence |
| Delta proposal/application | `ontowiz_core.bridge` | Useful kernel | All accepted candidates must use it |
| Durable governance | `ontowiz_runtime.governance` on SQLite | Implemented foundation | Complete F0.2H and expose canonical API |
| Source registration | reference source manifests only | Missing runtime capability | Build one source registry and immutable version model |
| DOCX/PPTX/PDF/VTT parsing | F0.4A mini-spec plus legacy parser fragments | Not implemented in canonical packages | Build adapters behind one parser contract |
| Exact source chunks/spans | planned in E1/E5 | Missing | Required before LLM extraction |
| Text mining | regex `mine_text()` for if/then and data-lag phrases | Prototype only | Do not use as production extraction |
| Agentic extraction | no run ledger, schema-bound extractor, critic or retry policy | Missing | Build a bounded extraction pipeline |
| Candidate persistence | no canonical source-candidate tables/API | Missing | Build before Intake or Launch UX |
| Ontology/taxonomy | artifact models plus legacy in-memory semantic/graph stores | Partial/prototype | Make governed artifacts canonical; graph is a rebuildable projection |
| Decision/question graph | QuestionPlaybook only | Missing | Add first-class generic contracts |
| Decision episode reconstruction | none | Missing | Add a provenance-backed observation model |
| Deduplication/reconciliation | legacy similarity helpers and curator concepts | Insufficient | Build deterministic and reviewable reconciliation |
| Forge mission kernel | `steward.py`, `missions.py`, `forge.py` | Useful prototype kernel | Persist, expose and strengthen after prerequisites |
| Conversation/Studio | fixed legacy Situation Room; E5 specification only | Not canonical | Reuse shared source/turn and structurer services |
| Eval execution | deterministic must-contain suite and lift helpers | Prototype/partial | Add typed, failure-linked, held-out evaluation |
| Deterministic candidate build | existing compiler plus S1.1 submission under review | In progress, not VERIFIED | Complete review and hardening before downstream reliance |
| External eval receipt/release attestation | S1.2/S1.3 specifications | Not yet implemented | Required before production release |
| Pack registry/context serving | `ontowiz_runtime` registry/context plus REST/MCP | Useful foundation | Add release verification and typed domain operations |
| Search/vector projection | architectural design only | Missing | Build only as a rebuildable candidate/release-scoped projection |
| Table/join semantic layer | reference pharma pack specification only | Missing | Required for launch analytics agents |
| Control-plane frontend | mock-data prototype and catalog UI | Prototype | Do not treat mock state as platform state |
| Tenant/client/base overlays | ADR/specification | Not implemented | Required before reusable-IP/client deployment |

### 2.2 Existing code that must not become production architecture

1. `ontowiz_factory.mining.mine_text()` is a narrow regular-expression demo. It
   cannot preserve slide/table/turn structure, distinguish observation from decision,
   or establish evidence.
2. `mine_govern_compile()` and `promote_candidate()` can approve with the default
   string `steward`. They prove composition in tests but are not an authenticated,
   persistent approval workflow.
3. The legacy `src/api/server.py` Situation Room uses in-memory session state and a
   fixed questionnaire. It is not the Forge/Studio service.
4. Legacy semantic, graph, evidence and judgment stores duplicate newer package
   concepts and are primarily in-memory. Do not add another store for Launch.
5. Current `EvalCase` scoring is mostly `must_contain` matching. It cannot prove
   numeric correctness, temporal applicability, decision quality or causal restraint.
6. Current `QuestionPlaybook` lacks owner, cadence, SLA, decision parent, applicability,
   answer schema, escalation, freshness and evidence requirements.
7. Current frontend control-plane data is simulated. No backend contract may be
   inferred from the mock object shapes without an accepted mini-spec.

### 2.3 Useful assets already present

- governed artifact models and lifecycle enforcement;
- Delta proposal and application bridge;
- SQLite transaction seam and persistent governance records;
- mission output contract requiring a Delta, eval and confidence;
- basic consensus with preserved dissent;
- compiler, pack registry, REST/MCP context serving and catalog views;
- commercial analytics rules, launch-stall/trajectory examples and eval fixtures;
- synthetic pharma marketing reference pack with source, ontology, analytics and
  evaluation modules; and
- accepted platform architecture and backend-first delivery sequence.

These are foundations, not evidence that the complete workflow already works.

## 3. Generic Target Architecture

### 3.1 Source plane

Owns source identity, immutable source versions, binary content, access class,
retention, rights, parse status and exact locators.

```text
SourceAsset -> SourceVersion -> ParsedDocument -> SourceChunk -> SourceSpan
```

The raw source body belongs in an object store or controlled filesystem. Its identity,
rights and workflow metadata belong in the relational store. A checksum identifies
content; a filename does not.

### 3.2 Discovery plane

Runs deterministic parsers and bounded model workflows. It produces candidates,
never governed knowledge.

```text
ExtractionRun
  -> CandidateArtifact
  -> CandidateRelation
  -> CandidateDecisionEpisode
  -> CriticFinding
  -> ReconciliationProposal
```

Every output records source spans, model/prompt/schema versions, run inputs, retry
history and confidence basis. Model prose without a typed schema and exact grounding
is retained only as run diagnostics.

### 3.3 Semantic and governance plane

Owns canonical artifacts and change authority:

- ontology nodes, concepts, aliases and typed relations;
- decision definitions and operational questions;
- playbooks, heuristics, exceptions, guardrails and actions;
- metrics, tables, joins, data quality and freshness contracts;
- applicability, evidence assertions and failure taxonomy;
- eval cases, coverage contracts and dependant links; and
- proposed Deltas, reviews, dissent, amendments and audit events.

### 3.4 Build and assurance plane

Resolves governed source artifacts into an immutable candidate, runs structural and
behavioral evaluation externally, and creates an authorized release mapping.

Evaluation never edits candidate bytes. Search and vector projections are derived
from a candidate/release digest and can be deleted and rebuilt.

### 3.5 Serving plane

Agents call typed operations, not storage:

```text
resolve_question(question_id, scope, as_of)
answer_question(question_id, scope, as_of, filters)
get_decision_brief(decision_id, scope, as_of)
get_playbook(playbook_id, current_state)
get_metric_definition(metric_id)
get_table_contract(table_id)
trace_evidence(artifact_id)
search_context(query, scope, filters)
```

Every response includes release, artifact versions, applicability, evidence, freshness,
access decision, eval receipt and required human authority. Missing evidence or stale
inputs must produce an explicit unresolved/abstain result.

## 4. Canonical Contracts to Add or Strengthen

### 4.1 Source contracts

`SourceAsset`, `SourceVersion`, `SourceChunk`, `SourceSpan`, `ParseRun`,
`AccessPolicy`, `RetentionPolicy` and `SourceAuthority`.

### 4.2 Discovery contracts

`ExtractionRun`, `ModelRun`, `CandidateArtifact`, `CandidateRelation`,
`CriticFinding`, `ReconciliationProposal` and `CandidateDecisionEpisode`.

Candidate state:

```text
EXTRACTED -> CRITIQUED -> NEEDS_REVIEW -> CONFIRMED -> DELTA_PROPOSED
                         |               |
                         -> REJECTED     -> CONTESTED / ESCALATED
```

### 4.3 Domain contracts

#### `DecisionDefinition`

Stable ID, question/decision statement, decision owner role, objective, options,
required evidence, required questions, decision window, escalation, applicability,
dependencies, risks and outcome measures.

#### `OperationalQuestion`

Stable ID, parent decision, intent (`MONITOR`, `DIAGNOSE`, `PREDICT`, `DECIDE`,
`ESCALATE`), wording variants, answer schema, owner, cadence, event trigger, answer
SLA, freshness, required metrics/sources, playbook, applicability, escalation and
abstention behavior.

#### `DecisionEpisode`

A source-grounded historical observation:

```text
situation -> signals -> questions asked -> evidence available -> interpretation
          -> decision -> action -> accountable role -> observed outcome
```

It does not assert that the action caused the outcome. Causal interpretation requires
a separate eligible artifact and evidence.

#### `CoverageContract`

Required domain nodes, decisions, question families, artifact families, criticality,
minimum evidence, independent confirmation, eval families and release blockers.

### 4.4 Analytics contracts

Strengthen `MetricDefinition` and add `TableContract`, `ColumnSemantic`, `JoinContract`,
`DataQualityRule`, `FreshnessRule`, `ThresholdDefinition` and `QueryPlanReceipt`.

A launch question that requires numbers is incomplete until formula, grain, time,
filters, denominator, table, keys, join cardinality, lag and quality conditions resolve.

## 5. Storage and Projection Rules

| Information | System of record | Projection/consumer |
|---|---|---|
| Raw PPTX, DOCX, PDF, VTT and attachments | controlled object store/filesystem | parser jobs |
| Source identity, rights, versions, spans and job state | relational database | Source Library UI |
| Candidate artifacts, turns, critic findings and reconciliation | relational database | Intake/Forge workbench |
| Governed source-pack artifacts | versioned source repository/registry | compiler |
| Deltas, approvals, audit, eval and release receipts | append-oriented relational records | governance/control plane |
| Compiled candidate | immutable digest-addressed object/filesystem storage | release registry/runtime |
| Chunk and artifact embeddings | OpenSearch/vector projection scoped by tenant and candidate/release | semantic retrieval |
| Graph adjacency | rebuildable graph/search projection | lineage and traversal |
| Business facts and launch measures | governed client data platform/warehouse | typed metric query adapter |

Never put approval state, canonical formulas, rules or release truth only in OpenSearch,
a vector database, a chat transcript or a frontend store.

## 6. Agentic Extraction Approach

Use agents for bounded semantic work, not uncontrolled autonomy.

### 6.1 Deterministic work first

- content hashing and source versioning;
- PPTX slide and shape order;
- DOCX paragraph/table coordinates;
- PDF page/block coordinates;
- VTT speaker/timestamp segmentation;
- OCR status and confidence;
- chunk boundaries and span offsets;
- exact duplicate detection; and
- schema/reference validation.

### 6.2 Bounded model stages

1. classify source and relevant domain nodes;
2. extract candidate questions, decisions, metrics, actions and evidence assertions;
3. link each field to exact spans;
4. classify observation versus interpretation, recommendation and decision;
5. propose relations and decision episodes;
6. run an independent critic for missing scope, evidence, contradiction and invention;
7. reconcile candidates against the pinned corpus snapshot; and
8. emit typed review records.

Each stage has a strict input/output schema, maximum attempts, timeout, cost budget,
idempotency key and recorded model/prompt version. A failed stage is visible and
retryable; it cannot silently fall back to unstructured acceptance.

### 6.3 Embeddings

Embeddings help find paraphrases and candidate neighbors. They do not decide that two
questions are equivalent, that a rule is correct, or that evidence supports a claim.
Exact IDs, normalized keys, deterministic features and human-confirmed semantic
relationships remain authoritative.

## 7. Harness Versus Product Experience

### 7.1 Decision

Build the backend and contracts first. Provide two clients over the same APIs:

1. **Engineering/curator harness:** CLI, Python SDK and optionally MCP tools that
   Claude or Codex can call for controlled corpus work.
2. **Product workflow:** a dedicated web experience for SMEs, curators, evaluators
   and release owners.

The harness accelerates development and internal curation. It is not a substitute for
the product workflow required for client SMEs.

### 7.2 Harness requirements

Suggested commands/tools:

```text
source register / source parse / source inspect
extract run / extract replay / candidate list / candidate explain
reconcile propose / reconcile decide
coverage inspect / question next
answer record / answer structure / answer confirm
delta propose / delta inspect
candidate compile / candidate verify
eval run / release inspect
context simulate
```

All tools call authenticated APIs or shared application services. A local chat cannot
manufacture an approval identity, mutate source YAML directly or bypass audit.

### 7.3 Product workflow modules

Build only after their backend contracts exist:

- Source Library and parse diagnostics;
- Extraction Workbench with synchronized evidence;
- Decision and Question Map;
- Grill Me targeted SME workflow;
- reconciliation/conflict workbench;
- deep Delta review drawer;
- coverage, evaluation and release control plane; and
- agent simulator with served-context and decision traces.

The primary user experience is work-focused. It should show one decision or curation
task at a time, explain why it matters, keep evidence one interaction away, and make
candidate, governed and released states visually unambiguous.

## 8. Backend Build Units

The units below extend the accepted backlog. They do not authorize parallel shadow
implementations.

### B0 - Contract and ownership freeze

**Dependencies:** accepted platform baseline.  
**Work:** approve the source, discovery, domain, analytics and receipt contracts;
assign each to `ontowiz-spec`, runtime, factory or serve; identify legacy deletions.

**DoD**

- one canonical model per concept;
- source identity is separate from content identity;
- candidate, governed artifact, compiled candidate and release are different states;
- no Launch-specific field appears in a generic base contract;
- compatibility and migration decisions are recorded; and
- can-fail contract tests reject missing tenant, scope, evidence and schema versions.

### B1 - Candidate, evaluation and release integrity

**Dependencies:** S1.1, S1.2 and S1.3 accepted through independent review.  
**Work:** finish immutable candidate inventory, load verification, external eval receipt,
release attestation, withdrawal and runtime enforcement.

**DoD**

- repeated compile is byte-identical;
- tampered, incomplete, unsafe-path and wrong-digest candidates refuse load;
- evaluation never changes candidate bytes;
- failed, missing, stale or wrong-candidate receipts cannot release; and
- the full required audit gate is green, not green after excluding an unwaived test.

### B2 - Source registry and immutable version store

**Dependencies:** F0 persistence and tenancy ownership fields.  
**Work:** `PackSource` adapters, source/version/span tables, binary store interface,
rights/access/retention, upload bounds, checksum deduplication and source audit events.

**DoD**

- the same bytes produce one content identity while distinct business sources remain distinct;
- a changed file creates a new immutable version;
- ID guessing and cross-tenant access return no metadata or body;
- deletion, legal hold and permission loss are testable; and
- malware/type/size/path failures quarantine rather than partially register a source.

### B3 - Parser boundary and canonical parsed document

**Dependencies:** accepted F0.4A specification and B2.  
**Work:** PPTX, DOCX, PDF and VTT adapters behind one `ParsedDocument` contract;
table/slide/turn locators, warnings, OCR status and deterministic fixtures.

**DoD**

- repeated parse gives identical structure and locators;
- slide notes, tables, merged cells, speaker turns and page coordinates survive;
- encrypted/corrupt/unsupported files fail explicitly;
- every chunk maps back to exact source bytes or rendered location; and
- golden fixtures cover long, malformed and mixed-content documents.

### B4 - Extraction run ledger and candidate store

**Dependencies:** B0-B3.  
**Work:** job/lease/retry/outbox, model/prompt/schema registry, bounded extraction DAG,
candidate persistence, exact grounding, critic findings and replay.

**DoD**

- every model call is attributable and reproducible from recorded inputs;
- duplicate submission/retry cannot duplicate candidates;
- ungrounded fields and invalid schemas are rejected;
- prompt injection inside sources cannot change system behavior;
- timeout/cost/retry limits are enforced; and
- restart resumes or safely retries every nonterminal job.

### B5 - Domain decision/question semantic kernel

**Dependencies:** B0 and artifact envelope.  
**Work:** DecisionDefinition, OperationalQuestion, DecisionEpisode, CoverageContract,
typed relations, applicability and dependency validators.

**DoD**

- a question resolves to one or more explicit parent decisions;
- cadence, SLA, trigger, answer schema, required evidence and abstention are mandatory
  for critical questions;
- decision episodes remain observations and do not assert unsupported causality;
- cycles, dangling references, incompatible scope and ambiguous ownership fail; and
- the kernel contains no pharma-specific enums or hard-coded launch decisions.

### B6 - Reconciliation and coverage engine

**Dependencies:** B4-B5.  
**Work:** exact duplicate, lexical/embedding neighbor, semantic compare, merge/split/link
proposals, corpus snapshot pinning, conflict ledger and coverage calculation.

**DoD**

- exact duplicate decisions are deterministic;
- semantic merges require human confirmation and preserve all source expressions;
- base versus overlay differences cannot be flattened;
- conflicts and minority interpretations remain durable; and
- coverage is calculated from the accepted contract, not artifact count alone.

### B7 - Evidence, rights and confidence enforcement

**Dependencies:** B2, B4-B6.  
**Work:** EvidenceAssertion and source authority, field-level spans, corroboration,
conflicts, staleness, access propagation and rights blockers.

**DoD**

- model confidence is distinct from evidence strength and SME confidence;
- source removal or permission loss invalidates dependants and projections;
- critical artifacts without required evidence fail closed;
- inaccessible evidence does not leak through snippets, search, errors or exports; and
- every served material statement traces to eligible evidence or an explicit SME assertion.

### B8 - Candidate-to-Delta governance bridge

**Dependencies:** F0.2H plus B4-B7.  
**Work:** promote, amend, reject, contest and escalate candidate operations; exact
payload confirmation; idempotency, ETags, ownership, dual attribution and audit.

**DoD**

- no candidate writes ACTIVE or edits source packs directly;
- confirm binds the payload digest actually shown to the reviewer;
- stale decisions return 409 with safe recovery;
- curator amendments retain original and amended authorship; and
- every accepted artifact and eval has candidate, source, actor and Delta lineage.

### B9 - Forge/Grill Me backend

**Dependencies:** B5-B8 and accepted SME Grill Me instruction set.  
**Work:** capability profiles, deterministic question planner, assignments, answers,
turn-as-source, grounding, confirmation, impact and readiness.

**DoD**

- next-question selection is reproducible with inspectable factors;
- own, conflicted, inaccessible, stale and already-answered targets are excluded;
- `I do not know`, out-of-scope, dissent and exception are first-class outcomes;
- no unconfirmed structured answer becomes knowledge; and
- usefulness is measured as confirmed governed outputs per SME hour, not chat turns.

### B10 - Evaluation framework

**Dependencies:** B1, B4-B9.  
**Work:** typed evaluators for extraction, grounding, reconciliation, references,
numeric answers, temporal scope, playbook behavior, abstention, safety and agent lift;
dataset split/leakage registry and immutable receipts.

**DoD**

- each named failure mode has a can-fail fixture;
- the artifact author is not the sole critical evaluator;
- extraction and release eval datasets are separated;
- numeric cases verify exact formula/grain/time/filter semantics;
- held-out corpus replay is supported; and
- unrun/failed/stale receipts block release server-side.

### B11 - Projections and typed serving

**Dependencies:** B1 and B5-B10.  
**Work:** candidate/release-scoped OpenSearch/vector and graph projections, typed domain
operations, warehouse query adapter, trust envelopes, REST/MCP parity and receipts.

**DoD**

- projections rebuild from immutable candidates with equivalent inventory;
- wrong tenant/release/scope returns zero unauthorized records;
- metadata filtering occurs before semantic ranking;
- agents never receive raw warehouse rows or direct storage credentials;
- missing/stale data returns unresolved rather than invented answers; and
- REST and MCP responses carry the same artifact/evidence/eval trace.

### B12 - Operations and enterprise hardening

**Dependencies:** all preceding units before client production.  
**Work:** tenancy/overlays, SSO mapping, retention/deletion/legal hold, backup/restore,
job observability, rate/cost limits, audit export, withdrawal and disaster drills.

**DoD**

- automated isolation tests have zero cross-client disclosure;
- base -> client -> engagement composition has explicit override/conflict semantics;
- restore and projection rebuild drills pass;
- source-to-release and served-response audit exports are complete; and
- operational SLOs and model/data costs are measured.

## 9. Launch Control Room Reference Vertical

### L0 - Corpus governance and experimental design

Inventory the five or six launch rooms. Record client, brand, market, indication,
time period, file rights, confidentiality, allowed reuse and source authority. Select
one complete room as a held-out test before extraction begins.

**DoD:** no held-out material enters prompts, embeddings, examples or SME ratification
for the training rooms; base-IP versus client-overlay rights are explicit.

### L1 - Launch coverage contract

Treat the proposed seven or eight major decisions as hypotheses. Manually label a
representative sample of slides, documents and transcript segments for decisions,
questions, metrics, actions, evidence and episodes.

**DoD:** domain leads approve the provisional decision map, question intent taxonomy,
cadence vocabulary, required artifact families and critical release blockers.

### L2 - Extract and normalize the corpus

Run B2-B7 over the permitted rooms. Produce candidate decisions, approximately 200
source-grounded operational questions, playbooks, metrics, data contracts, episodes,
exceptions and failures. The output count is an observation, not a target.

**DoD:** every field has source spans; paraphrases are linked rather than silently
discarded; brand/market differences are proposed as applicability or overlays;
coverage gaps and conflicts are visible.

### L3 - SME ratification campaign

Use Forge/Grill Me to validate decision hierarchy, question equivalence, cadence,
answer contracts, evidence, priority, boundaries, exceptions and escalation. Do not
ask SMEs to review a 200-row spreadsheet in one pass.

**DoD:** critical questions have independent confirmation or explicit escalation;
dissent is retained; every confirmed artifact produces a proposed Delta plus an
appropriate regression eval or ratification event.

### L4 - Analytics and operating-data binding

Map questions requiring numbers to governed metric, table, join, quality, freshness
and query contracts. Use synthetic or approved de-identified fixtures until production
data access is authorized.

**DoD:** at least one decision brief calculates from governed test tables end to end;
fan-out, wrong grain, stale data, missing denominator and unavailable data fail safely.

### L5 - Held-out replay and domain evaluation

Replay the untouched launch room against the candidate pack. Measure decision/question
coverage, correct routing, evidence retrieval, numeric correctness, boundary handling,
abstention and curator correction cost.

**DoD:** thresholds are approved before looking at results; failures become named
taxonomy entries and regression cases; the held-out room remains independently
traceable and is not retroactively relabeled merely to pass.

### L6 - Release and consume

Compile a candidate, run required suites, obtain release attestation and serve it to
one named Launch Control Room agent workflow through typed operations.

**DoD:** a user question traces through release, OperationalQuestion, parent Decision,
playbook, metrics/data, source evidence and eval receipt; a correction completes the
Delta-to-new-release loop without modifying the released version.

## 10. Backend-First Delivery Order

```text
B0
 -> B1 candidate/release integrity
 -> B2 source registry
 -> B3 parsers
 -> B4 extraction ledger
 -> B5 decision/question kernel
 -> B6 reconciliation + B7 evidence
 -> B8 governance bridge
 -> B9 SME ratification
 -> B10 evaluation
 -> B11 serving
 -> B12 enterprise hardening
```

Launch work can begin with L0/L1 and a controlled manual gold sample while B0-B4 are
built. L2 must not create canonical artifacts until B4-B8 exist. UI implementation
starts only after the relevant API contract and restart-survival tests pass.

## 11. Immediate Team Instructions

1. Do not build a Launch chatbot or dashboard first.
2. Finish independent review of S1.1 and implement S1.2/S1.3 before relying on release claims.
3. Accept B0 contracts before adding tables or endpoints.
4. Build B2-B4 as the first new vertical slice using one PPTX and one VTT fixture.
5. In parallel, the domain team completes L0 and labels a small L1 gold sample.
6. Add DecisionDefinition, OperationalQuestion, DecisionEpisode and CoverageContract
   only through reviewed `ontowiz-spec` mini-specs.
7. Demonstrate one source span -> candidate -> confirmation -> Delta -> eval trace before
   scaling corpus ingestion.
8. Demonstrate one question -> metric/table/join -> governed answer trace before adding
   OpenSearch or a polished simulator.
9. Use Claude/Codex through the harness to accelerate controlled curation, but persist
   every source, run, candidate, answer and decision in Onto_Wiz.
10. Begin the dedicated UI only when backend contracts, permissions, idempotency,
    restart and failure behavior are executable.

## 12. Program Definition of Done

The generic platform and Launch reference vertical are ready only when:

1. permitted documents, slides and transcripts ingest with immutable identity and exact locators;
2. bounded extraction produces typed, grounded and reproducible candidates;
3. decisions, operational questions, episodes, playbooks, metrics and data contracts form a validated graph;
4. SMEs can ratify, challenge, dissent and amend without bypassing governance;
5. every accepted correction creates a Delta and regression evidence;
6. candidates compile deterministically and evaluation produces external immutable receipts;
7. only an authorized attestation makes an unchanged passing candidate releasable;
8. the held-out launch room demonstrates useful generalization and safe abstention;
9. agents consume typed operations with complete trust envelopes, not raw storage; and
10. the same backend accepts a second non-launch domain without a schema fork, new
    governance pipe, new compiler or new serving stack.
