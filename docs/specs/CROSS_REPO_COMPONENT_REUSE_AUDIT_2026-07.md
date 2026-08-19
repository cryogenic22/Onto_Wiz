# Cross-Repository Component Reuse Audit

**Date:** 2026-07-13  
**Scope:** OntoWiz domain discovery, source digitization, evidence, evaluation and serving  
**Repositories inspected:** `agentfuel`, `market_zero`, `ProtoCode`  
**Companion specification:** `DOMAIN_DISCOVERY_TO_PACK_BACKEND_BUILD_INSTRUCTION_SET_2026-07.md`

## 1. Executive Decision

Reuse is worthwhile, but the correct unit of reuse is a **bounded adapter, pure algorithm,
contract invariant or test pattern**. Do not merge the repositories, introduce sibling-repo
runtime imports, add git submodules, or transplant another repository's persistence model.

The recommended split is:

- **AgentFuel:** source for an optional Docling adapter, parser capability routing and a small
  set of deterministic utilities. It is MIT licensed and therefore the cleanest source for
  code reuse, subject to attribution and OntoWiz contract tests.
- **Market Zero:** source for production invariants: append-only evidence, content-addressed
  snapshots, explicit empty/unavailable serving states, run-outcome conservation and an
  auditable entity-resolution cascade. Its code is highly coupled to its Postgres schema and
  no repository license was found, so use it as a design and test reference unless ownership
  and reuse rights are explicitly recorded.
- **ProtoCode:** source for extraction-stage metadata, restart/resume concepts, adversarial
  extraction and table/OCR verification patterns. Its README states `Proprietary. All rights
  reserved`; no code is to be copied until an IP owner provides written authorization. Most
  extraction code is also protocol-specific.

The strongest near-term reuse is **not a new generic orchestrator**. It is:

1. Complete OntoWiz F0.4A as the only parser boundary.
2. Add AgentFuel Docling as an optional F0.4B adapter behind that boundary.
3. Recreate Market Zero's evidence/conservation invariants in OntoWiz-native contracts.
4. Use ProtoCode's dual-pass/challenger/OCR ideas only in a later bounded extraction lab.

## 2. Review Method

The audit inspected implementation files and related tests, not only READMEs. Candidates were
classified as:

| Class | Meaning |
|---|---|
| **ADOPT** | Small implementation may be ported after ownership/license recording and OntoWiz tests |
| **ADAPT** | Keep the capability but rewrite its boundary to OntoWiz contracts |
| **REFERENCE** | Recreate the invariant or test; do not copy the implementation |
| **REJECT** | Do not introduce into the OntoWiz architecture |

Targeted AgentFuel verification was run with its existing environment:

- Docling adapter: **3 passed**.
- document router, audited parser, deduplication, evidence linker, grounding and injection
  guard suites: completed with no failures; part of the repository's expanded evaluation set
  is marked expected-failure and is therefore not evidence of production readiness.
- The first `uv` invocation timed out while resolving the environment. Direct execution with
  the existing `.venv` completed. Test cache writes were denied by local filesystem
  permissions; this did not affect test execution.

ProtoCode and Market Zero had no local virtual environment suitable for a dependency-clean
targeted run. Their decisions below are based on implementation and test inspection. This is
adequate for reuse triage, not a certification of either repository.

## 3. Non-Negotiable Porting Rules

1. **F0.4A remains the one parser contract.** Reused parsers return OntoWiz `ParseResult`,
   `Source`, `SourceUnit`, `Chunk` and reconstructable `SourceSpan` values.
2. **No direct dependency on another local repository.** Port small code with provenance or
   implement an adapter in OntoWiz. Builds must succeed when the other repositories are absent.
3. **No parallel domain model.** Reused entity, evidence, stage and confidence dataclasses are
   mapped into OntoWiz contracts at the adapter boundary and do not become a second source of
   truth.
4. **No source text or client path in logs.** Telemetry uses source/version/run IDs, hashes,
   counts, status, duration and bounded error codes.
5. **Similarity is a candidate signal, never proof.** Fuzzy matching, token overlap, MinHash,
   embeddings and LLM agreement can queue candidates; only exact spans or governed structured
   records satisfy evidence gates.
6. **Model calls never run inside the parser.** Model-based structure extraction starts only
   after guarded, immutable source parsing.
7. **Optional heavy dependencies stay in adapters.** Docling, OCR and VLM packages must not be
   imported by `ontowiz-spec`, runtime or serve packages.
8. **Every adopted behavior gets a can-fail OntoWiz test.** Copying a source repository's test
   without changing it to the OntoWiz contract is insufficient.
9. **IP is resolved before copying.** Record source repository, source path, source commit,
   license/authorization and material changes in the implementation review bundle.
10. **No aggregate confidence gate without calibration.** Confidence dimensions remain
    separate: extraction confidence, evidence sufficiency, source authority, agreement,
    freshness and reviewer status.

## 4. AgentFuel Audit

AgentFuel has the most portable implementation boundaries. Its main weakness for OntoWiz is
that its document and evidence models are less strict than F0.4A and the planned managed-source
contract.

### 4.1 Component decisions

| Component | Source | Decision | Why | Required OntoWiz change |
|---|---|---|---|---|
| Docling digitization adapter | `packages/sdk_core/src/agentfuel_sdk_core/digitization/docling_adapter.py`, `types.py`, `ports.py` | **ADAPT P0** | Working PDF, DOCX and image conversion; layout blocks, bounding boxes and tables; 3 tests passed | Map output to F0.4A/F0.4B units and spans; remove local paths; add content identity, access class, quarantine and limits |
| Parser capability router | `knowledge/document_router.py` | **ADAPT P1** | Clear capability/cost routing and 16 focused tests | Make routing policy versioned and deterministic; return explicit unsupported/quarantine result; never silently relax a required capability |
| Exact and near dedup | `knowledge/deduplication.py` | **ADOPT/ADAPT P1** | Pure SHA-256 and deterministic advisory MinHash | Raw-byte hash is canonical identity; normalized-text/MinHash is only a review signal; persist decisions in E1.1, not an in-memory index |
| Document element shapes | `knowledge/document_elements.py` | **REFERENCE** | Useful table/cell/bbox vocabulary | Extend F0.4B IR rather than introducing these dataclasses |
| Audited parser decorator | `knowledge/audited_parser.py` | **REJECT direct** | Useful intent, but logs local source names, stores volatile timing with the document and silently swallows all audit failures | Implement OntoWiz run telemetry outside candidate bytes and fail visibly when mandatory audit persistence fails |
| Evidence linker | `knowledge/provenance/evidence_linker.py` | **REFERENCE only** | Deterministic helpers, but bullet-order IDs and `SequenceMatcher` can map evidence to the wrong claim | Link claims to exact `SourceSpan`s; fuzzy matches enter a reconciliation queue only |
| Grounding checker | `evaluation/grounding.py` | **REFERENCE only** | Useful smoke metric and hashed telemetry | Token Jaccard is not factual grounding; use only as a diagnostic feature in eval receipts |
| Source linker | `validation/source_linker.py` | **REFERENCE only** | Separates heuristic and LLM linkers | Require source-version IDs and exact spans; no release gate based on best-effort similarity |
| Injection guard | `security/injection/classifier.py`, `guard.py` | **ADAPT as defence-in-depth** | Useful trust labels and simple known-pattern detection | Preserve source text as evidence; quarantine or isolate instructions rather than deleting lines; never call this a complete injection defence |
| Stage contracts | `orchestration/contracts.py` | **REJECT direct** | Mostly mutable `dict[str, Any]`, generated timestamps and Markdown output | Use typed extraction-run/stage-attempt contracts from B4 with durable idempotency and evidence references |

### 4.2 Docling adapter acceptance conditions

The AgentFuel Docling code may enter OntoWiz only after these tests pass:

- identical bytes and declared type produce identical content IDs and normalized units;
- every emitted chunk/table cell has a reconstructable source locator;
- no local path, source text, client name or access label appears in logs;
- malformed, encrypted, oversized and decompression-hostile inputs are quarantined whole;
- the adapter performs no network calls and succeeds with model API keys absent;
- missing Docling dependency reports a typed capability-unavailable result;
- scanned/image input is explicitly marked OCR-derived with engine/version metadata;
- Docling output is golden-tested on a reviewed PDF, DOCX table and image fixture;
- the base F0.4A suite passes with Docling uninstalled.

## 5. Market Zero Audit

Market Zero contains the strongest operational patterns and the deepest tests of the three
repositories, but its implementation assumes its own Postgres schema and hard-coded pharma
record types. Reuse its invariants and negative tests, not its service layer.

### 5.1 Component decisions

| Component | Source | Decision | Why | Required OntoWiz change |
|---|---|---|---|---|
| Connector/RawRecord contract | `connectors/base.py` | **ADAPT P1** | Source-agnostic connector output with provenance and health checks | Replace static source/record enums with registered source types; emit immutable source versions, rights and access class; separate fetch from parse |
| Run outcome classifier | `integration/pipeline.py::classify_run_outcome` | **REFERENCE/ADOPT P0** | Correctly distinguishes landed, no-change, zero-row, partial and failure | Recreate as a pure OntoWiz ingestion outcome function; add expected-empty policy and staleness SLA; never mark zero output generically successful |
| Evidence ledger and snapshots | `services/evidence_ledger.py` | **REFERENCE P0** | Append-only evidence, deterministic hashes and content-addressed claim/evidence snapshots; 35 API tests | Implement OntoWiz `EvidenceAssertion`/snapshot contracts using source-version + span identity and tenant/access enforcement; do not copy DB SQL |
| Explicit fill state | `services/context_layer.py` | **REFERENCE P0** | Makes silent empty sections structurally invalid; 15 contract tests plus a no-silent-empty lint test | Add typed `available`, `not_found`, `stale`, `blocked`, `error` result states to serving operations; do not return successful empty lists for backend faults |
| Conservation gates | `tests/test_conservation_gates.py` and context tests | **REFERENCE P0** | Tests that records, provenance and non-empty semantics survive boundaries | Add cross-boundary count, ID, access class, evidence and status conservation tests to B2-B11 |
| Entity-resolution cascade | `integration/entity_resolver.py` | **REFERENCE P1** | Exact ID, alias, fuzzy, combination, embedding, LLM, unresolved and audit trace; 39 cascade tests | Implement a generic resolver strategy protocol and governed alias artifacts; only exact/approved aliases auto-link; all probabilistic resolutions remain candidates |
| Cross-linker | `integration/cross_linker.py` | **REJECT direct** | 627 lines, Postgres SQL and drug/company/trial-specific branching | Compile relationships from governed OntoWiz artifacts and domain-pack rules into a rebuildable projection |
| Data quality engine | `integration/data_quality.py` | **REFERENCE P1** | Completeness, freshness, consistency and cross-source rule categories | Express rules as versioned `QualityRule`/eval artifacts; evaluation produces external receipts and never mutates candidate bytes |
| CTX query/context pipeline | `services/ctx_pipeline.py`, `ctx_context.py`, `ctx_evidence.py` | **REJECT direct** | Useful experience, but query heuristics and entity logic are product-specific and several paths are legacy/stubbed | Keep OntoWiz typed serving contract; use this only to derive replay questions and failure cases |
| User document connector | `connectors/user_document.py` | **REJECT direct** | Basic extractor/chunker without F0.4A reconstruction, quarantine and immutable source-version guarantees | Superseded by F0.4A/F0.4B |

### 5.2 Conservation invariants to recreate

For every boundary `source -> parse -> extract -> candidate -> delta -> candidate build ->
release -> serve`, automated tests must prove:

- input source-version ID is present or deliberately transformed through a recorded mapping;
- access class and tenant scope never become less restrictive;
- evidence references still resolve to the same immutable source bytes and exact spans;
- item counts cannot drop silently; every drop has an outcome and reason code;
- backend error cannot be represented as a successful empty result;
- probabilistic resolution cannot become an approved canonical link without a policy decision;
- candidate and release IDs are deterministic and do not include clock/run/local-path values;
- projection rebuilds preserve candidate/release identity and do not become the source of truth.

## 6. ProtoCode Audit

ProtoCode provides useful high-rigor extraction ideas, especially for complex tables. It is not
a generic extraction engine today: the orchestrator, schemas, trust calculation and most table
logic are coupled to clinical protocol schedules of activities.

### 6.1 Component decisions

| Component | Source | Decision | Why | Required OntoWiz change |
|---|---|---|---|---|
| Extraction tool metadata/registry | `app/core/extraction/registry.py` | **REFERENCE P1** | Side-effect, trust, timeout, retry and use/not-use metadata are useful | Build a real OntoWiz `StageDefinition`; ProtoCode wrappers currently return values from context and do not execute the underlying tools |
| Pipeline events | `app/core/extraction/events.py` | **REFERENCE** | Stable typed event vocabulary and 13 tests | Persist events through B4 job/event/outbox records; in-memory pub/sub is not an audit trail |
| Pipeline session | `app/core/extraction/session.py` | **REJECT direct** | Atomic file-write idea is useful, but save failures are logged and swallowed, IDs/path globs are not a tenant-safe store, and completed evidence is deleted | Use durable relational stage attempts, leases, idempotency keys and retained receipts |
| PDF rendering | `app/core/extraction/pdf_ingestion.py` | **REFERENCE for optional visual adapter** | Small PyMuPDF renderer useful for page images | Keep outside F0.4A core; sandbox and resource-bound it; preserve page/source identity |
| Table detection/stitching/text grid | `table_detection.py`, `table_stitcher.py`, `text_grid_extractor.py` | **ADAPT later, P2** | Potentially useful complex-table techniques | First separate generic geometry from SoA keywords/models; prove on marketing, launch and analytics tables, not only protocol schedules |
| Structural/cell extraction | `structural_analyzer.py`, `cell_extractor.py` | **REFERENCE P2** | Dual-pass VLM pattern and deterministic sorting are useful | Run as bounded candidate generators; retain both passes and exact page regions; no direct canonical writes |
| Challenger/reconciler | `challenger_agent.py`, `reconciler.py` | **REFERENCE P1** | Adversarial check and multi-pass disagreement are relevant to SME curation | Generalize to typed assertions and disagreements; agreement does not equal truth; unresolved conflict goes to review |
| OCR grounding | `ocr_grounding.py` | **REFERENCE P2** | Cross-modal verification can catch visual extraction errors; 8 threshold tests | Record OCR engine/version and geometry; calibrate thresholds on a held-out multi-domain corpus |
| Trust engine | `app/core/trust/models.py`, `engine.py` | **REFERENCE only** | Good verification-step trace, but scores are cell/protocol specific | Preserve dimension-level evidence and gate reasons; do not port a single aggregate trust score |
| Structured Model Builder | `app/core/smb/` | **REJECT direct** | Creates a second entity/relationship model and embeds protocol-specific queries/validation | OntoWiz governed artifacts remain canonical; build projections from them |
| Whole orchestrator | `app/core/extraction/orchestrator.py` | **REJECT** | 1,167 lines with protocol, procedure, SoA, LLM and budget coupling | Compose small OntoWiz stages under B4; no transplant |

## 7. Target OntoWiz Placement

Approved reuse must land behind existing ownership boundaries:

| Capability | OntoWiz target | Source of truth |
|---|---|---|
| Parser IR, guards and base adapters | F0.4A `ontowiz_factory/parsers/` | Immutable source bytes + parser-local IR |
| Docling/PPTX/XLSX/EML/visual adapters | F0.4B optional adapter modules | Same F0.4A contract |
| Source registration/dedup decisions | B2/E1.1 managed source service | Relational source/version records + object storage |
| Extraction stages, attempts and events | B4 discovery service | Relational run/stage/candidate/event records |
| Evidence assertions and snapshots | B7 | Immutable source-version/span references + append-oriented records |
| Resolution and reconciliation | B6 | Candidate mappings, governed aliases and review decisions |
| Quality/evaluation rules | B10 | Versioned eval artifacts + external receipts |
| Domain pack compilation | S1 compiler/release units | Immutable deterministic candidate and verified release |
| Search/vector/graph | B11 | Rebuildable release-scoped projections |
| Agent API/MCP | B11 serve layer | Typed operations over verified release, never direct storage |

The legacy `src/knowledge/parsers/` pipeline is not the destination. F0.4A already defines how
its useful PDF/DOCX/chunking behavior is ported and then retired. Do not add Docling or new
reuse work to `src/`.

## 8. Recommended Build Units

### R0 - IP and provenance gate

**Steps**

1. Add a reuse record template to implementation review bundles.
2. Record AgentFuel MIT source paths and commit for any copied material.
3. Obtain explicit ownership/reuse decisions for Market Zero and ProtoCode.
4. Prohibit copied code from unknown/proprietary sources until the decision exists.

**Definition of Done**

- Every copied file or substantive algorithm has source repo/path/commit, license or written
  authorization, change summary and test mapping.
- CI has no runtime import or filesystem dependency on sibling repositories.

### R1 - F0.4A completion and legacy containment

**Steps**

1. Build the accepted F0.4A mini-spec without expanding scope.
2. Prove PDF, DOCX, TXT and VTT exact reconstruction, quarantine and no-egress behavior.
3. Mark `src/knowledge/parsers/` legacy and block new imports from canonical packages.

**Definition of Done**

- All F0.4A named tests pass.
- A dependency/boundary test proves spec/runtime/serve packages do not import parser adapters.
- No new digitization code is added under `src/`.

### R2 - Optional Docling adapter spike

**Steps**

1. Port only the AgentFuel Docling conversion/mapping logic with provenance.
2. Map page text, layout blocks, bounding boxes and tables into F0.4B extensions of parser IR.
3. Keep Docling optional and worker-only.
4. Run the acceptance conditions in section 4.2 and benchmark quality/cost/time against the
   base pypdf/python-docx adapters.

**Definition of Done**

- All base parsing tests pass with Docling absent.
- Golden layout/table fixtures pass with Docling installed.
- A benchmark report shows where Docling improves extraction and where it must not be routed.
- Adapter failure returns an explicit result and cannot partially promote a source.

### R3 - Source connector and ingestion outcome contracts

**Steps**

1. Define `SourceConnectorPort`, `FetchResult` and `IngestionOutcome` in OntoWiz terms.
2. Recreate Market Zero's landed/no-change/zero-row/partial/failure classification.
3. Add source freshness SLA and expected-empty policy.
4. Persist fetch, parse and promotion as separate attempts.

**Definition of Done**

- Zero-row full fetch cannot be green.
- Legitimate no-change incremental fetch is distinct from a broken or stale source.
- Retry does not create another source version for identical bytes.
- Rights/access/tenant labels are conserved through fetch and parse.

### R4 - Evidence ledger and conservation spine

**Steps**

1. Add typed `EvidenceAssertion` with source-version, exact span(s), relation, extraction method,
   authority, access class and reviewer state.
2. Add deterministic evidence snapshots outside candidate bytes.
3. Add cross-boundary conservation tests from source through serve.
4. Add explicit unavailable states to typed serving responses.

**Definition of Done**

- An evidence snapshot is content-addressed and order-independent.
- Evidence records are append-only; correction creates a superseding record.
- Tampered bytes or invalid spans make verification fail.
- An internal error cannot appear as a successful empty response.
- Restricted evidence cannot be served or projected into a less restrictive scope.

### R5 - Resolver and reconciliation strategies

**Steps**

1. Define a strategy protocol for exact ID, governed alias, deterministic normalization,
   advisory similarity and model-assisted proposal.
2. Produce a resolution trace for every attempted strategy.
3. Persist unresolved/ambiguous candidates for SME review.
4. Add exact duplicate, near duplicate, contradiction and competing-definition tests.

**Definition of Done**

- Exact and approved-alias matches may auto-resolve according to policy.
- Fuzzy, embedding and model matches never auto-approve canonical artifacts by default.
- Every resolution can be replayed from strategy version, inputs and governed aliases.
- Review decisions become Deltas and never mutate an ACTIVE pack directly.

### R6 - Bounded table/OCR/challenger lab

**Steps**

1. Create a held-out corpus spanning launch slides, brand-plan tables, performance reports and
   protocol tables.
2. Generalize only the necessary ProtoCode techniques after IP approval.
3. Compare deterministic text/layout extraction, Docling and visual/OCR passes.
4. Retain pass-level outputs and reconcile disagreements into review candidates.

**Definition of Done**

- At least three non-protocol table families are represented.
- Cell value, header hierarchy, merged-cell, footnote and source-region metrics are reported.
- Thresholds are calibrated on held-out documents, not set from intuition.
- No extracted cell becomes canonical without evidence and schema validation.

## 9. Priority and Sequencing

| Order | Unit | Rationale |
|---:|---|---|
| 1 | R0 | Prevents IP and architecture debt before any copy |
| 2 | R1 | Establishes the one safe parser boundary |
| 3 | R3 | Gives ingestion durable identity and honest outcomes |
| 4 | R4 | Establishes the evidence and conservation spine |
| 5 | R2 | Adds richer digitization without destabilizing the core |
| 6 | R5 | Enables generic ontology/question/decision reconciliation |
| 7 | R6 | Adds high-cost visual intelligence only after the substrate is sound |

R0-R4 belong before a Launch Control Room extraction campaign. R5 is required before SME
ratification at scale. R6 is valuable for launch decks and analytics reports but must not block
text-first corpus ingestion.

## 10. Explicit Rejections

The build team must not:

- copy AgentFuel's entire SDK/runtime into OntoWiz;
- make Docling mandatory for all document types;
- use AgentFuel fuzzy evidence linking or token-overlap grounding as a release gate;
- copy Market Zero's Postgres schema, entity resolver or cross-linker wholesale;
- treat Market Zero's search index or graph as canonical storage;
- copy ProtoCode code before proprietary-IP authorization;
- use ProtoCode's file session as the production job ledger;
- introduce ProtoCode's Structured Model Builder as a second ontology model;
- claim prompt-injection safety from substring matching;
- allow an LLM, embedding similarity or multi-agent agreement to directly commit a pack;
- place timestamps, run IDs, local paths, eval results or mutable confidence summaries inside
  deterministic candidate directories.

## 11. Program Exit Criteria

Cross-repository reuse is successful only when:

1. OntoWiz builds and tests without the three source repositories present.
2. There is one parser contract, one managed-source identity model, one governed artifact model
   and one verified release path.
3. Every material assertion served to an agent resolves to immutable source evidence or a
   governed structured-data contract.
4. Every probabilistic step is visible, replayable and separated from approval.
5. Parser, extraction and serving failures are explicit; no successful empty hides a fault.
6. Optional digitization improves measured golden-corpus quality without weakening security,
   determinism or tenant isolation.
7. Domain-specific logic enters through versioned domain packs and adapters, not hard-coded
   branches in the generic engine.

