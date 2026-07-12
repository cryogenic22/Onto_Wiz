# Onto_Wiz Domain Pack Platform Build Instruction Set

**Status:** INTENT - requires read-only architecture review before build cards become READY  
**Audience:** integration lead, platform builders, domain-module builders, evaluators, security reviewers, and release reviewers  
**Date:** 2026-07-12  
**Purpose:** build the reusable Onto_Wiz container, contracts, compiler, harness, and operating model that can safely hold high-grade domain content

## 1. Instruction

The synthetic pharma marketing pack is an example of what fills the bucket. It is not the bucket.

The Onto_Wiz platform must provide a domain-independent but pharma-grade structure in which ontology, evidence, claims, policy, analytics, omnichannel logic, agent contracts, evaluations, and feedback can be:

- authored in human-reviewable modules;
- validated through one typed contract boundary;
- governed through attributable Deltas and role-specific decisions;
- compiled deterministically into immutable candidates;
- projected into graph, lexical, vector, catalog, context, and tool views;
- evaluated against held-out and adversarial cases;
- released only through immutable attestations;
- served through typed, access-aware contracts; and
- improved without mutating production directly.

The platform succeeds only when content teams can add a new high-quality domain pack without adding domain-specific parsing, lifecycle, release, tenancy, or serving code.

## 2. Governing Documents

Read these before drafting a mini-spec:

1. `docs/specs/BUILD_INSTRUCTION_SET_2026-07.md`
2. `docs/specs/DELIVERY_LOOPS_BACKLOG_2026-07.md`
3. `docs/specs/PHARMA_MARKETING_DOMAIN_PACK_REFERENCE_2026-07.md`
4. `examples/reference_domain_packs/auravia_marketing/0.1.0/README.md`
5. `examples/reference_domain_packs/auravia_marketing/0.1.0/VALIDATION.md`
6. `examples/reference_domain_packs/auravia_marketing/0.1.0/SETU_PATTERN_CROSSWALK.md`
7. `docs/DELIVERY_PROTOCOL.md`
8. `docs/adr/ADR-007-architecture-boundaries.md`
9. `docs/adr/ADR-008-mini-spec-before-impl.md`
10. `docs/adr/ADR-011-sentinel-reviews-read-only.md`
11. `docs/adr/ADR-012-monorepo-two-tier-packaging.md`

This document supplements the existing build instruction set. It does not relax its gates, branch isolation, evidence, reviewer independence, or integration authority.

When documents conflict:

1. Accepted ADRs and security constraints win.
2. The latest accepted mini-spec controls its build unit.
3. This document controls the domain-pack platform shape.
4. The reference pack supplies acceptance examples, not production truth.

## 3. Non-Negotiable Platform Invariants

1. There is one canonical identity for each governed artifact.
2. Content identity is separate from source-instance identity.
3. Every material fact, claim, rule, metric, or decision can resolve to provenance.
4. Applicability is explicit; missing scope never means globally permitted.
5. LLM output is a candidate, never an authority or release decision.
6. Embeddings, indexes, graph stores, catalogs, and context files are derived projections.
7. Agents call typed contracts, never storage directly.
8. Compilation is deterministic and contains no network or model call.
9. Candidate bytes never change after the candidate digest is calculated.
10. Evaluation creates a separate immutable receipt; it never edits or reseals a candidate.
11. A release maps to one unchanged candidate digest and passing receipt set.
12. Failed or unrun candidates may be inspected but cannot publish or serve as released.
13. Runtime loads only the exact attested inventory; it never discovers artifacts by glob.
14. Tenant, access, retention, withdrawal, and deletion constraints propagate to every projection.
15. Every material correction creates a Delta and a regression case.
16. Aggregate scores cannot hide a critical compliance, privacy, tenancy, provenance, or numeric failure.
17. Synthetic content is permanently prevented from production release.
18. The semantic kernel is not allowed to hard-code Auravia, pharma marketing, or any one client.

## 4. What the Platform Owns

The platform owns the reusable mechanics:

```text
shared schema and identity kernel
  -> source/evidence and applicability contracts
  -> governance and Delta lifecycle
  -> module registry and authoring SDK
  -> composition resolver and immutable build lock
  -> deterministic compiler
  -> staged validation harness
  -> evaluation runner and immutable receipts
  -> rebuildable projections
  -> release registry and attestation
  -> typed REST/MCP serving
  -> telemetry, feedback, invalidation, and regression loop
```

Domain teams own governed content inside those mechanics:

```text
ontology and terminology
evidence, claims, risks, and policies
audiences, journeys, channels, and actions
metrics, tables, joins, quality, and analytical interpretation
agent task contracts
golden and adversarial evaluation cases
```

A domain team must not create a second identity system, source registry, lifecycle, approval vocabulary, compiler, release mechanism, access layer, or agent-serving stack.

### Package boundaries

| Package | Boundary |
|---|---|
| `ontowiz-spec` | Shared strict contracts, schema registry, canonical serialization, references, migrations, and receipts. No database, LLM, web framework, compiler, or runtime dependency. |
| `ontowiz-core` | Governed write model, Delta lifecycle, approval, versioning, evidence/applicability policy, and persistence interfaces. No compiler or serving implementation. |
| `ontowiz-factory` | Private build plane for parsing, agent-assisted extraction, normalization, resolution, compilation, projections, and evaluation. It may hold provider credentials but cannot activate artifacts directly. |
| `ontowiz-runtime` | Key-free read plane for verification, registry, dependency assembly, projections, context resolution, and trust envelopes. No extraction, LLM calls, or governance mutations. |
| `ontowiz-serve` | Authentication, tenant resolution, authorization, REST/MCP routing, and public error contracts. Tenant comes from authenticated identity, not request payload. No duplicated domain logic. |
| Persistence adapters | Separate immutable audit/event records, workflow state, candidate storage, release mappings, and projection stores behind explicit interfaces. |

Every row, object, job, cache entry, vector namespace, and projection carries tenant and candidate/release scope where applicable.

## 5. Required Platform Modules

### 5.1 Semantic kernel and schema registry

**Package owner:** `ontowiz-spec`  
**Primary team:** Platform Contracts

Provide strict, versioned contracts for:

- stable artifact identity and namespace;
- semantic version and schema version;
- lifecycle and ownership;
- `Applicability`;
- `ContentObject`, `SourceInstance`, `ParsedChunk`, and `SourceSpan`;
- `EvidenceRef` and evidence-support relationships;
- `DomainNode`, `Relationship`, and `TerminologyBinding`;
- `ReviewDecision` and `Delta`;
- `MetricDefinition`, `TableContract`, `ColumnContract`, and `JoinContract`;
- `EvalCase`, `ValidationReport`, and `EvalReceipt`;
- `CompositionRequest`, `ResolvedBuildManifest`, and `CompiledPackManifest`;
- `ReleaseAttestation`, `QueryReceipt`, and `DecisionReceipt`; and
- the common trust envelope.

Create one immutable schema registry. Each entry contains:

```text
schema_id
schema_version
artifact_kind
strict Pydantic model
canonical serializer
typed reference declarations
allowed lifecycle states
validation profiles
explicit migrations
projection adapters
```

Rules:

- strict validation and `extra="forbid"`;
- unknown schema IDs and versions fail closed;
- no silent string-to-number, string-to-boolean, or enum coercion;
- registry keys are unique by `(schema_id, schema_version)`;
- one current schema exists for every artifact kind;
- migrations are pure, explicit `vN -> vN+1` functions with golden tests;
- sorted JSON Schema snapshots and a `schema_registry_digest` are generated;
- runtime rejects an unsupported registry version or digest; and
- shared contracts remain available in a clean built wheel.

**DoD:** every reference-pack artifact kind has a registered schema, canonical serializer, typed references, migration position, and positive/negative fixture.

### 5.2 Source, parsing, and evidence module

**Package owner:** shared spec plus private factory worker  
**Primary team:** Intake and Evidence

Responsibilities:

- immutable content hashing;
- distinct source instances for filename, authority, capture time, access, and applicability;
- safe format detection and quarantine;
- deterministic parsing and chunking;
- structured `SourceSpan[]` locators with exact round-trip resolution;
- source authority and evidence-strength classification;
- prompt-injection and unsafe-content marking;
- provider egress policy;
- PII/PHI and confidentiality classification;
- retention, legal hold, deletion, and withdrawal propagation; and
- source-to-artifact dependency invalidation.

F0.4A must not standardize a single scalar locator. Chunks and extracted artifacts can span, split, or combine multiple source regions. Content deduplication must not erase source-instance metadata.

**DoD:** all supported source fixtures parse deterministically; every accepted field resolves to one or more exact spans; quarantined inputs never enter extraction; deletion and access changes invalidate every dependent projection.

### 5.3 Governance and Delta module

**Package owner:** `ontowiz-core` governed write model plus persistence adapters  
**Primary team:** Governance

Responsibilities:

- append-only proposed changes;
- idempotent mutation handling;
- role-specific review decisions;
- evidence, rationale, dissent, and counterexample capture;
- state-machine enforcement;
- concurrent-review correctness;
- audit, retention, erasure, and export;
- dependency impact analysis; and
- promotion into candidate-eligible artifact versions.

Use a common lifecycle with artifact-specific decision policies:

```text
OBSERVED_SOURCE
  -> EXTRACTED_CANDIDATE
  -> NORMALIZED_CANDIDATE
  -> SME_ENDORSED
  -> APPROVED_FOR_SCOPE
  -> COMPILED_CANDIDATE
  -> EVAL_QUALIFIED
  -> RELEASED
  -> SUPERSEDED or WITHDRAWN
```

This is not one generic approval. Claims, metrics, ontology relations, policies, assets, and releases retain different authorities and required roles.

**DoD:** no API, job, import, conversation, or admin path can bypass Delta governance; restart, concurrency, idempotency, audit, and erasure tests pass.

### 5.4 Domain module SDK and registry

**Package owner:** `ontowiz-spec` and `ontowiz-factory`  
**Primary team:** Platform Contracts plus Domain Developers

Define a module profile rather than permitting arbitrary YAML dictionaries. Each module type declares:

```text
module kind and schema profile
owned artifact kinds
permitted references
applicability requirements
layer and override rules
semantic validators
projection handlers
serving operations
evaluation adapters
owner roles
```

Initial module profiles:

1. `ontology`
2. `terminology`
3. `sources_and_evidence`
4. `claims_and_content`
5. `policy_and_mlr`
6. `audience_journey_channel`
7. `semantic_analytics`
8. `agent_contracts`
9. `evaluations`

Extension rules:

- a module references a canonical concept; it does not privately redefine it;
- extensions use a distinct extension artifact ID and an explicit target;
- cross-module references are typed and validated;
- module discovery comes from the exact source manifest, not filesystem globbing;
- unsupported modules fail rather than being ignored;
- correctness-critical overrides explicitly target a lower-precedence artifact;
- higher layers may narrow permission but may not silently broaden label, safety, privacy, evidence, or access constraints; and
- no implicit last-writer-wins behavior is permitted.

**DoD:** the pharma reference modules and a second non-brand fixture load through the same registry without conditional domain code.

### 5.5 Composition resolver

**Package owner:** `ontowiz-factory`  
**Primary team:** Compiler

Separate three contracts:

1. `CompositionRequest`: requested layers, functions, selectors, exclusions, and dependency ranges.
2. `ResolvedBuildManifest`: exact artifact IDs, versions, kinds, schemas, content digests, dependency release digests, and compiler settings.
3. `CompiledPackManifest`: exact emitted-file inventory, byte counts, digests, roles, and immutable candidate digest.

The resolver must:

- operate inside one consistent database snapshot;
- resolve all selectors before compilation;
- pin dependency version and release digest;
- reject floating `latest` dependencies;
- record explicit exclusions and reasons;
- calculate the transitive dependency closure;
- detect layer cycles and conflicts;
- recheck artifact versions and digests immediately before compile; and
- persist the immutable resolved build lock.

**DoD:** the same composition request resolved against the same snapshot produces the same build lock; any concurrent source change produces a new lock or an explicit conflict.

### 5.6 Deterministic compiler

**Package owner:** `ontowiz-factory`  
**Primary team:** Compiler

The compiler must:

1. Consume only a `ResolvedBuildManifest`.
2. Make no network or model calls.
3. Normalize Unicode to NFC, line endings to LF, and text to UTF-8.
4. Sort artifacts by documented stable keys such as namespace, kind, stable ID, and version.
5. Canonicalize mappings, references, and manifests.
6. Use canonical JSON for digest calculation even when YAML remains the review format.
7. Exclude timestamps, run IDs, local paths, and environment data from reproducible digests.
8. Write to a new staging directory, verify it, and atomically promote it.
9. Never write into an existing candidate directory.
10. Address candidates by digest.

Behavior:

- same digest already present: idempotent success;
- same semantic version with a different digest: conflict;
- removed source artifact: absent from the new fresh output;
- unsafe path, symlink/reparse point, normalized collision, or traversal: fatal;
- invalid semantic content: retain a sealed diagnostic candidate and validation report only if safe, never release it.

**DoD:** shuffled input order, different work directories, sharded versus equivalent flattened input, and repeated builds produce byte-identical outputs and the same digest.

### 5.7 Validation engine

**Package owner:** `ontowiz-factory` using registry contracts  
**Primary team:** Validation and Evaluation

Run stable stages in stable order:

1. `syntax`
2. `schema`
3. `identity`
4. `governance`
5. `references`
6. `graph`
7. `applicability`
8. `evidence`
9. `semantic`
10. `projection`
11. `release`

Every issue has:

```text
code
rule_version
stage
severity
blocking
artifact_id
field_path
related_ids
message
remediation
```

Issue order is deterministic by stage, severity, artifact, field path, and code.

Failure classes:

- **Fatal:** unsafe parse, unknown schema, invalid path, duplicate identity, manifest mismatch, or tamper. Emit no loadable candidate.
- **Blocking:** governance, references, graph, applicability, evidence, semantic, projection, or release failure. Diagnostic output may exist but cannot release.
- **Warning:** requires an attributable waiver, rationale, rule version, and expiry.

Required checks include:

- duplicate IDs and normalized filenames;
- hierarchy cycles, orphans, and illegal cardinality;
- unknown target ID, kind, version, or namespace;
- missing or overlapping applicability;
- unresolved or inaccessible evidence spans;
- access broader than supporting evidence;
- terminology conflicts and namespace collisions;
- metric formula, unit, grain, dimension, table, column, and join compatibility;
- unsafe fan-out and undeclared joins;
- rule references to concepts, evidence, metrics, and eval cases;
- illegal override broadening;
- source, label, policy, and metric expiry;
- held-out answer leakage into compiled context;
- projection loss or stale artifact inclusion; and
- candidate, receipt, attestation, withdrawal, and authorization mismatch.

**DoD:** every registered rule has can-pass, can-fail, and near-miss fixtures; a negative case must reach its intended validation stage.

### 5.8 Evaluation framework

**Package owner:** factory eval runner plus shared receipt contracts  
**Primary team:** independent Evaluation

Evaluation is a first-class module, not a field patched into `pack.yaml`.

Required eval suites:

1. **Structural:** schema, identity, references, lifecycle, manifest, and deterministic build.
2. **Ontology:** competency questions, hierarchy, typed relations, mappings, and applicability.
3. **Evidence/grounding:** exact spans, claim support, contradiction, source authority, and citation integrity.
4. **Retrieval:** lexical/vector/graph recall, precision, scope filters, wrong-client leakage, and inaccessible evidence.
5. **Content/MLR:** unsupported proposition, semantic broadening, risk coupling, wrong market/audience/purpose, route/block/abstain, and no automated approval.
6. **Semantic analytics:** exact formulas, denominator, grain, temporal join, revisions, suppression, numeric receipt, and causal restraint.
7. **Omnichannel:** consent, eligibility, frequency, suppression, journey freshness, released-asset selection, and decision receipt.
8. **Security/privacy:** tenant isolation, ID guessing, access downgrade, log/secret leakage, provider egress, retention, and deletion.
9. **Agent behavior:** with-pack versus without-pack lift, tool selection, abstention, uncertainty, and trust-envelope use.
10. **Release integrity:** tamper, stale receipt, post-eval mutation, withdrawal, rollback, and runtime refusal.

Eval rules:

- expected results are authored independently of system output;
- held-out answers never enter compiled context or retrieval indexes;
- the same prompt/model run cannot create both content and its gold answer;
- critical cases require 100% pass;
- every material production correction creates a regression case;
- statistical results include uncertainty and sample size;
- model/prompt/provider versions are recorded for non-deterministic runs;
- deterministic checks remain separate from model-judged checks; and
- a failure cannot be hidden in a composite average.

Correct immutable flow:

```text
candidate_digest
  -> ValidationReport(candidate_digest)
  -> EvalReceipt(candidate_digest, suite_digest, results)
  -> publish authorization
  -> ReleaseAttestation(candidate_digest, receipt_digests)
```

**DoD:** evaluation never mutates candidate files; stale, failed, missing, or wrong-digest receipts cannot authorize release.

### 5.9 Projection builders

**Package owner:** `ontowiz-factory`  
**Primary team:** Projection and Retrieval

Build projections from the same immutable canonical candidate:

- ontology/relationship graph;
- terminology and lexical index;
- vector index with embedding model/config/version metadata;
- semantic data catalog;
- deterministic rules and policy bundle;
- agent operation schemas;
- compact context and navigation indexes; and
- evaluation bundle without held-out expected answers.

Projection invariants:

- every record carries candidate/release and artifact identity;
- vector records retain chunk and source-span references;
- tenant, client, market, access, and validity filters are indexed and enforced before semantic ranking;
- deletion, withdrawal, expiry, and access changes invalidate every affected projection;
- all projections are disposable and rebuildable;
- projection-specific state never becomes canonical truth; and
- a projection completeness report proves all eligible artifact IDs were included exactly as expected.

**DoD:** delete all projections and rebuild them from the candidate with equivalent semantic inventories; cross-client and wrong-scope retrieval tests return zero unauthorized records.

### 5.10 Release registry and runtime loader

**Package owner:** `ontowiz-runtime`  
**Primary team:** Runtime and Release

Before parsing any artifact, runtime must:

1. Resolve the requested released version to an attested candidate digest.
2. Verify lifecycle and withdrawal state.
3. Verify the release attestation and required eval receipts.
4. Compare the directory exactly with the compiled inventory.
5. Verify every file byte count and digest.
6. Reject missing, extra, changed, duplicate, unknown, or stale files.
7. Load paths only from the manifest.
8. Verify artifact ID, kind, schema, and version against its inventory entry.
9. Enforce tenant, client, access, and applicability before returning data.

Never glob `artifacts/*.yaml` as a source of runtime truth.

Retain v1 loading only for explicit migration or non-production compatibility. New releases require strict manifest v2.

**DoD:** runtime refuses extra, missing, changed, failed, unrun, withdrawn, unauthorized, unknown-schema, and wrong-registry packs with stable error codes.

### 5.11 Typed agent serving

**Package owner:** `ontowiz-serve` and runtime  
**Primary team:** Agent Contracts

Provide REST and MCP parity for typed operations such as:

```text
resolve_concept
get_content_brief
get_eligible_claims
explain_claim_support
validate_draft
get_next_action_options
get_metric_definition
query_metric
compare_metric
decompose_variance
trace_metric_lineage
diagnose_brand_variance
get_experiment_result
submit_feedback
```

Every response contains a trust envelope with pack, release, artifacts, resolved scope, evidence, policy/label versions, validity, access decision, eval receipt, and required human authority. Numeric responses also contain metric/version, formula, grain, filters, period, source/plan snapshots, freshness, suppression, uncertainty, and query receipt.

The service rejects arbitrary SQL, direct vector queries, direct graph traversal, direct table access, and unscoped correctness-critical requests.

**DoD:** REST and MCP contract tests match; authorization and applicability decisions are identical; no storage-vendor identifier leaks into the public contract.

### 5.12 Learning and invalidation loop

**Package owner:** governance, runtime telemetry, and factory  
**Primary team:** Learning Loop

Capture:

- served answer/decision receipt;
- user or agent failure category;
- SME correction and evidence;
- MLR finding or override;
- query/data-quality issue;
- affected artifacts and projections;
- proposed Delta;
- regression case; and
- post-release recurrence and reuse.

Feedback never edits released content. It creates a candidate routed through the same governance, compile, eval, and release path.

**DoD:** one real correction can be traced from served receipt to Delta, review, new candidate, regression pass, release, projection rebuild, and reduced recurrence.

## 6. Domain-Team Roles and Accountable Outputs

| Role | Owns | Must deliver |
|---|---|---|
| Domain Product Lead / Business Analyst | Agent decision and scope | `UseCaseContract`, competency questions, failure modes, business acceptance |
| Ontology Developer | Concepts, relations, terminology, applicability | ontology modules, mappings, compatibility and competency coverage |
| Evidence and Claims Curator | Sources, evidence, claims, limitations | `ClaimDossier`, exact spans, support assertions, risk coupling |
| Semantic Analytics Developer | KPI, metric, table, join, data quality | `MetricDossier`, executable fixtures, lineage and prohibited interpretations |
| MLR and SME Workflow Lead | Policy, review roles, findings, routing | `PolicyBundle`, decision rules, invalidation and escalation |
| Omnichannel Domain Developer | Segment, journey, channel, next action | `DecisionPolicy`, eligibility/exclusion cases and receipts |
| Agent Contract Developer | Typed task and serving contract | request/response/error schemas and trust envelope |
| Evaluation Engineer | Independent expected behavior | held-out suites, adversarial cases and immutable receipts |
| Compiler/Platform Developer | Generic machinery | registry, resolver, compiler, validators, projections and runtime compatibility |
| Security and Privacy Reviewer | Boundaries and threat cases | isolation, access, data minimization, egress, retention and deletion evidence |
| Release Owner / Integrator | Candidate promotion | immutable release decision, rollback and compatibility statement |

One person may hold multiple roles in a pilot, but ownership remains explicit. The person generating an artifact must not be the only authority for its critical evaluation or release. Automated MLR assistance never becomes the authorized MLR approver.

## 7. Required Handoff Artifacts

Meetings and transcripts may supply source material, but they are not build handoffs.

| From | To | Required artifact |
|---|---|---|
| Product Lead | All teams | `UseCaseContract` |
| Intake | Curators | source manifest, access policy, parsed chunks and span resolution report |
| Evidence Curator | Ontology/MLR | `ClaimDossier` and evidence graph |
| Ontology Developer | All consumers | `SemanticChangeProposal` and compatibility diff |
| Analytics Developer | Agent/Eval | `MetricDossier`, table/join contracts and fixed fixtures |
| MLR Lead | Compiler/Eval | `PolicyBundle` and structured review decisions |
| Omnichannel Developer | Agent/Eval | `DecisionPolicy` and contact-policy cases |
| Agent Developer | Eval | typed requests, responses, errors and trust envelopes |
| Compiler | Eval | candidate digest, compiled inventory and validation report |
| Eval Engineer | Release Owner | immutable `EvalReceipt` set |
| Release Owner | Consumers | release attestation, compatibility statement and rollback target |

Receivers reject incomplete handoffs. They do not infer missing market, audience, purpose, evidence, metric grain, authority, or expected behavior.

## 8. Required Build Sequence

Do not implement all domain modules in parallel against an unstable kernel. Use the following dependency order and create one accepted mini-spec per bounded unit.

### Step 0 - Accept architecture intent

1. Review this instruction set and the pharma reference pack at immutable SHAs.
2. Record accepted decisions and open issues.
3. Reconcile with the current delivery backlog without silently renumbering or replacing cards.
4. Commit the accepted governance documents before dependent mini-specs reference them.

**DoD:** builders and reviewers cite one immutable architecture baseline; no mini-spec depends on uncommitted text.

### Step 1 - Harden existing candidate/release behavior

Address the known current implementation gaps before adding new artifact kinds:

- compiler output must not depend on caller order;
- output must be written fresh so removed artifacts cannot remain;
- manifests must contain exact input and output inventories, not counts alone;
- runtime must not load undeclared globbed YAML;
- runtime must verify integrity and release eligibility before load;
- benchmarks/evals must not mutate and reseal `pack.yaml`;
- empty diagnostic candidates must never be publishable; and
- `PackEvalSummary` must become a derived catalog view, not mutable release truth.

Affected areas include:

- `packages/ontowiz-spec/ontowiz_spec/pack_manifest.py`
- `packages/ontowiz-factory/ontowiz_factory/compiler.py`
- `packages/ontowiz-factory/ontowiz_factory/benchmark.py`
- `packages/ontowiz-runtime/ontowiz_runtime/registry.py`
- their tests

**DoD:** immutable candidate, external receipt, exact inventory, tamper refusal, fresh-write, shuffled-order, and post-eval-mutation tests pass.

### Step 2 - Establish schema registry and canonical artifacts

Implement the common kernel and migration rules. Start with source/evidence, ontology/terminology, applicability, Delta/review, manifest/receipt, and trust-envelope contracts.

**DoD:** strict registry snapshots and wheel tests pass; every reference resolves through typed declarations; no domain-specific conditional exists in the kernel.

### Step 3 - Complete source/evidence boundary

Revise F0.4A around content objects, source instances, structured multi-span locators, safe quarantine, and persistent-source ownership boundaries. Then add required formats incrementally.

**DoD:** exact round-trip provenance, dedup/source-instance behavior, access/retention, parser safety, and wheel fixtures pass.

### Step 4 - Complete persistent governance

Finish F0.2H and connect all mutation paths to durable Delta governance and idempotency.

**DoD:** migration, restart, concurrency, audit, ownership, escalation, retention, and mutation-bypass suites pass.

### Step 5 - Build resolver, compiler v2, and validators

Implement the three-manifest separation, deterministic compilation, atomic digest-addressed output, validation rule registry, exact inventory, and projection completeness report.

**DoD:** deterministic golden builds, can-pass/can-fail/near-miss rule coverage, stale-file prevention, and runtime tamper refusal pass.

### Step 6 - Add domain artifact profiles vertically

Add only the artifact kinds needed by the first two vertical questions:

1. content/MLR synthetic HCP email and wrong-market block;
2. brand NBRx-versus-plan diagnosis with causal restraint.

Recommended first profile order:

1. ontology and terminology;
2. claims, evidence support, and risk;
3. semantic metrics, tables, columns, joins, and query receipts;
4. policy/MLR;
5. audience/journey/channel;
6. agent contracts; and
7. eval cases.

**DoD:** each new kind has schema, serializer, reference rules, migration position, projection behavior, runtime compatibility, and three-part validator coverage.

### Step 7 - Make the pharma reference pack executable

Move the reference fixture into the compiler test harness without treating it as real product content.

**DoD:** all required modules compile, 24 named failures remain triggerable, 28 golden cases are executable, exact numeric expectations reproduce, example typed operations serve from the candidate, and production release remains impossible.

### Step 8 - Add projections and typed serving

Build the minimal graph, retrieval, catalog, context, and REST/MCP projections required by the two vertical questions.

**DoD:** projections rebuild from scratch, scope/access prefilters work, response receipts match artifacts, and no agent depends on storage directly.

### Step 9 - Add SME curation and continuous learning

Expose targeted tasks only after artifacts, Deltas, review decisions, and regression links are executable.

**DoD:** SME confirm/correct/dissent/counterexample tasks produce governed Deltas; quality-weighted contribution metrics work; no points or reputation can grant regulatory authority.

### Step 10 - Prove the second-consumer gate

Before declaring the kernel stable:

1. migrate the existing commercial analytics pack to the strict contracts; and
2. compile one small neutral or non-brand domain fixture through the same kernel.

**DoD:** no schema fork, copied base ontology, new compiler, new lifecycle, or new serving path is required. Domain-specific extensions remain modules registered through the shared SDK.

## 9. Compiler and Fixture Harness Layout

Use existing package boundaries and introduce focused files rather than a new parallel stack. A target layout is:

```text
packages/ontowiz-spec/ontowiz_spec/
  schema_registry.py
  validation_contracts.py
  source_contracts.py
  semantic_contracts.py
  analytics_contracts.py
  eval_contracts.py
  release_contracts.py

packages/ontowiz-factory/ontowiz_factory/
  resolver.py
  compiler.py
  canonicalize.py
  validation/
  projections/
  evals/

packages/ontowiz-runtime/ontowiz_runtime/
  registry.py
  release_verifier.py
  projection_registry.py

packages/ontowiz-factory/tests/fixtures/compiler/
  valid/minimal/
  valid/layered/
  valid/pharma_marketing_vertical/
  invalid/<stable-rule-code>/
  near_miss/<stable-rule-code>/
  golden/<case>/expected/
```

Names may be adjusted to existing conventions in the mini-spec, but responsibilities and boundaries must not be collapsed.

Fixture helpers should include:

```text
copy_fixture(name)
mutate_artifact(id, mutation)
rewrite_resolved_manifest(mutation)
add_stray_output(path)
tamper_file(path)
remove_inventory_file(path)
shuffle_input_order()
compile_in_fresh_directory()
```

Golden updates require an explicit accept operation and a reviewed diff. A generic parser failure does not count as coverage for a semantic validator.

## 10. The Pharma Reference Pack as the First Platform Exam

The platform passes the first exam when it can consume the reference source pack and demonstrate:

1. exact source-instance and content-object identity;
2. resolvable synthetic evidence spans;
3. canonical ontology nodes and typed relationships;
4. one scoped claim, textual variant, and required risk bundle;
5. wrong-market and wrong-audience blocking;
6. MLR preflight that never emits approval;
7. channel consent/frequency/suppression decisions;
8. 11 governed metrics, 11 table contracts, and four join paths;
9. exact NBRx, plan variance, writer, access, and engagement calculations;
10. observation/hypothesis/causality separation;
11. query, decision, trust, validation, and eval receipts;
12. all 24 named failure rules and 28 golden cases;
13. deterministic candidate rebuild;
14. tamper, extra-file, stale-file, failed-eval, and production-synthetic refusal;
15. full projection deletion and rebuild; and
16. REST/MCP serving of the example outputs.

Passing the authored YAML validation in `VALIDATION.md` proves only that the example is internally coherent. It does not prove the platform exam has passed.

## 11. SME Curation and Gamification Instructions

Design SME work as small decisions:

- confirm or correct a definition;
- validate a relationship;
- confirm claim support;
- add a limitation or counterexample;
- mark market/audience/channel applicability;
- resolve a contradiction;
- validate a metric formula, denominator, grain, or join;
- classify a failure; and
- author or approve a gold case.

Reward:

- accepted high-impact corrections;
- useful counterexamples;
- contradictions discovered;
- calibrated confidence;
- contributions reused across packs; and
- regression cases that prevent repeat failures.

Do not reward:

- number of approvals;
- majority agreement;
- speed without accuracy;
- free-text volume;
- accepting model suggestions; or
- MLR certification decisions.

Contribution score informs routing and recognition. It never grants access, release, medical, legal, regulatory, privacy, data-steward, or MLR authority.

## 12. Security, Privacy, and Tenant Boundary

The mini-spec for every module states:

- tenant/client/engagement ownership;
- access-class inheritance;
- external identity and consent authority;
- PII/PHI and pseudonymous fields;
- provider/model egress permission;
- logs and error redaction;
- retention, deletion, legal hold, and withdrawal;
- source-to-projection invalidation;
- row-level versus aggregate query boundary;
- minimum-cell or suppression behavior where relevant; and
- cross-tenant negative tests for list, ID, search, vector, graph, export, job, REST, and MCP paths.

General marketing agents do not receive patient-level rows, arbitrary SQL, raw identity, or storage credentials. The pack stores semantic contracts and governed references, not unnecessary operational data.

## 13. Definition of Ready for Every Mini-Spec

A unit is not READY until its committed mini-spec contains:

1. immutable baseline SHA and review SHA;
2. objective and named consumer;
3. exact in-scope and out-of-scope behavior;
4. files/packages allowed to change;
5. dependencies and accepted contract versions;
6. typed inputs, outputs, errors, identities, and lifecycle;
7. persistence and transaction behavior;
8. authorization, tenancy, privacy, retention, and egress behavior;
9. deterministic and non-deterministic boundaries;
10. positive, negative, near-miss, migration, rollback, and packaging tests;
11. evaluation cases and critical gate behavior;
12. evidence bundle requirements;
13. performance/resource limits;
14. compatibility and migration position;
15. kill criteria and explicitly deferred work; and
16. objective DoD.

References to uncommitted planning documents do not satisfy readiness.

## 14. Unit Delivery and Review Protocol

For every unit:

1. INT assigns a bounded card and accepted baseline.
2. Builder commits a mini-spec before implementation.
3. Read-only REV reviews the immutable SHA.
4. Builder closes findings in a new commit.
5. REV returns `READY` or findings; REV does not patch builder work.
6. Builder branches from the accepted baseline and works red-green.
7. Builder submits one review SHA and a six-part evidence bundle.
8. REV reviews exact diff, tests, generated artifacts, security, and rollback evidence.
9. INT alone integrates the accepted SHA and records VERIFIED status.
10. Any code change after review requires a new review.

Required evidence bundle:

1. accepted mini-spec and review SHAs;
2. exact changed-file and scope diff;
3. targeted, full, coverage, static, packaging, and migration results as applicable;
4. generated candidate, manifest, projection, and semantic diff;
5. authorization, privacy, tenant, tamper, and failure-path evidence; and
6. deterministic rebuild, rollback, restore, or invalidation proof.

## 15. Platform Leak Tests

The platform is not release-ready until automated tests prove that it rejects or contains:

- an undeclared artifact file;
- a missing declared file;
- a stale artifact left from a prior build;
- a changed file after evaluation;
- a duplicate normalized filename;
- an unknown schema version;
- a broken reference or hierarchy cycle;
- a claim without eligible evidence;
- an expired label or policy;
- an artifact used in the wrong client, market, audience, purpose, or time;
- a vector result from another tenant;
- an inaccessible evidence citation;
- a metric with missing formula, denominator, grain, or unit;
- an undeclared or fan-out join;
- prescription events narrated as unique patients;
- descriptive attribution narrated as causal lift;
- a generated draft selected as a released asset;
- a missing consent/suppression authority response;
- a held-out answer embedded in context;
- a failed or unrun eval hidden by an aggregate score;
- synthetic content targeted at production;
- a withdrawn source remaining in any projection; and
- a feedback event mutating production directly.

## 16. Quality and Value Measures

Track platform quality separately from domain quality.

Platform measures:

- deterministic rebuild rate;
- manifest/inventory integrity failures caught;
- stale/tampered runtime refusal rate;
- source-to-projection invalidation latency;
- cross-tenant leakage count;
- candidate-to-release trace completeness;
- rollback and rebuild success rate;
- schema migration failure rate; and
- REST/MCP contract parity.

Domain measures:

- claim-level evidence completeness;
- applicability completeness;
- competency-question coverage;
- held-out critical pass rate;
- with-pack versus without-pack lift with uncertainty;
- numeric/query-receipt completeness;
- SME correction acceptance and time;
- correction recurrence;
- artifact and eval reuse across agents/packs; and
- time from approved correction to released pack.

Do not use raw artifact count, ontology node count, SME clicks, or vector count as success measures.

## 17. Stop Conditions

Stop dependent expansion and return to the owning unit when:

- shared contracts are still changing without version/migration control;
- the compiler is not deterministic;
- runtime accepts undeclared or tampered files;
- candidate evaluation mutates candidate bytes;
- source spans cannot be resolved;
- critical failures lack can-fail tests;
- held-out expected answers can leak into context;
- tenant or access prefilters are absent;
- analytics can invent joins or causal language;
- MLR assistance can emit approval;
- synthetic content can become production eligible;
- a second consumer requires a schema or compiler fork; or
- curation UI work is proceeding ahead of executable lifecycle and Delta contracts.

## 18. Anti-Patterns

- Building a comprehensive ontology without a named agent decision.
- Treating YAML flexibility as a substitute for typed schemas.
- Treating a vector store as canonical knowledge.
- Creating one parser, compiler, or serving path per domain.
- Letting LLMs write directly into released artifacts.
- Using one generic `approved` status for every artifact kind.
- Assuming an approved claim makes a rendered asset approved.
- Encoding one market policy as a global rule.
- Capturing SME truth only in meetings, transcripts, email, or comments.
- Copying base ontology into each client pack.
- Discovering runtime content through filesystem globbing.
- Updating or resealing a compiled candidate after evaluation.
- Defining pack inventories only as counts.
- Writing compiled output into an existing version directory.
- Allowing input iteration order to affect digest or bytes.
- Defining tables without grain, keys, time, quality, and joins.
- Treating KPI hierarchy as causal structure.
- Calling attributed credit incremental lift.
- Allowing arbitrary SQL or patient-row access from general agents.
- Generating gold answers from the system being evaluated.
- Adding evals only after seeing output.
- Averaging away a critical failure.
- Rewarding SME approval volume.
- Building polished Forge/Studio flows before the semantic kernel and governance are stable.
- Shipping a pack with zero or unrun evaluation cases.

## 19. Final Platform Definition of Done

The Onto_Wiz bucket is fit for controlled domain delivery only when:

1. shared schemas, identity, provenance, applicability, lifecycle, and receipt contracts are versioned and packaged;
2. all mutations flow through durable Delta governance;
3. composition resolves to an immutable exact build lock;
4. compilation is deterministic, fresh, atomic, and digest-addressed;
5. validation is staged, typed, deterministic, and failure-linked;
6. evaluation is independent and produces immutable receipts without modifying candidates;
7. release attestation binds the unchanged candidate to the passing receipt set;
8. runtime verifies exact inventory, integrity, lifecycle, withdrawal, authorization, and tenancy before loading;
9. graph, lexical, vector, catalog, context, and tool projections rebuild from canonical artifacts;
10. typed REST/MCP operations return trust, decision, and query receipts;
11. the pharma reference pack passes the complete executable platform exam while remaining non-production;
12. a second consumer compiles without a schema, lifecycle, compiler, or serving fork;
13. one real SME correction completes the Delta-to-regression-to-release loop;
14. backup, restore, rollback, withdrawal, and deletion propagation are demonstrated;
15. no P0/P1 review finding remains; and
16. all accepted debt has an owner, target date, and kill criterion.

Until then, describe the example as a reference design and the platform as under construction. Do not describe Onto_Wiz as already producing release-grade domain packs.
