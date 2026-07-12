# Pharma Marketing Domain Pack Reference

**Status:** Reference architecture and synthetic design fixture  
**Date:** 2026-07  
**Scope:** Brand content generation, MLR assistance, omnichannel decisioning, and brand performance analytics  
**Production status:** Not production eligible

## 1. Purpose

This specification defines the first end-to-end reference domain pack for Onto_Wiz. It is intentionally built around a fictional pharmaceutical brand so that the team can prove the knowledge, governance, compilation, evaluation, and serving architecture without presenting invented clinical or regulatory content as real.

The reference pack is not an ontology demonstration. It is a context product for four related agent workloads:

1. Generate a scoped promotional content draft.
2. Perform MLR preflight and assemble review evidence without claiming approval.
3. Select or propose a governed omnichannel next action.
4. Explain brand performance using governed metrics, data contracts, and causal restraint.

The source fixture is located at:

`examples/reference_domain_packs/auravia_marketing/0.1.0/`

It is a proposed source-pack shape. It must not be copied into `packs/` or served as a compiled release until the necessary artifact contracts, compiler validation, and release gates exist.

## 2. Product Decision

Onto_Wiz owns the governed semantic core, compiler, evaluation spine, and typed serving contract. Search engines, vector stores, graph stores, warehouses, and model providers are replaceable projections or execution systems behind that boundary.

The pack therefore separates:

- **Canonical governed artifacts:** concepts, claims, evidence assertions, rules, metrics, tables, joins, applicability, decisions, and eval cases.
- **Derived projections:** graph indexes, vector embeddings, lexical indexes, data-catalog views, prompt/context bundles, and tool schemas.
- **Operational records:** review decisions, query receipts, next-action receipts, evaluation receipts, telemetry, and feedback Deltas.

An embedding or an LLM output is never the authority for a claim, rule, metric, or approval status.

## 3. Vertical Spine

```text
Named agent decision and failure modes
  -> request scope: client + brand + market + audience + purpose + channel + time
  -> immutable source instances and access policy
  -> parsed chunks with exact SourceSpan[] locators
  -> agent-proposed semantic candidates
  -> normalization, entity resolution, and terminology alignment
  -> SME confirm / correct / dissent / supply counterexample
  -> curator ratification as governed Delta
  -> canonical semantic core
  -> deterministic compilation of all projections
  -> candidate pack and manifest
  -> structural, grounding, task, safety, privacy, and lift evaluations
  -> release attestation or rejection
  -> typed agent contract
  -> query/decision receipts and telemetry
  -> failure or SME correction
  -> new Delta plus regression evaluation
```

Every material response must be traceable through this spine. A user must be able to move from an answer or decision to the release, artifacts, source spans, review decisions, and evaluation receipt that made it eligible to serve.

## 4. Four Workloads, One Semantic Core

### 4.1 Content generation

Input must declare brand, market, audience, communication purpose, channel, objective, and intended format. The service resolves eligible claims, approved or permitted wording, required limitations, risk material, references, channel rules, and prohibited transformations.

The output is a **draft** with a preflight receipt. It is never an approval decision.

### 4.2 MLR assistance

The assistant identifies potential findings, cites the governing rule and evidence, assigns a configured severity, and explains uncertainty. It can route, block, or request human review. Only authorized client reviewers operating under client SOPs can record an approval decision.

Claim approval and asset approval are distinct. Layout, prominence, juxtaposition, references, and overall impression can change the review outcome even when individual claims are eligible.

### 4.3 Omnichannel decisioning

The service returns eligible actions, exclusions, policy checks, the selected or proposed action, and a decision receipt. Content selection and next-action selection are separate decisions. Production orchestration normally selects released assets; generated content remains in a draft workflow.

### 4.4 Brand performance analytics

The analytics service answers:

> What happened, where, compared with what, what might explain it, what can validly be concluded, and what should be investigated next?

It keeps observations, descriptive attribution, predictions, causal estimates, hypotheses, and recommendations as different artifact types. It may return `UNRESOLVED`; it must not invent a cause.

## 5. Pack Composition

The intended layer order is:

```text
pharma-commercial-base
  -> market-policy
  -> therapy-area
  -> brand-and-label
  -> client-operating-model
  -> campaign-or-engagement-release
```

Precedence is deterministic. A higher layer may narrow a permission. It must not silently broaden a label, safety, privacy, or regulatory constraint. Conflicting correctness-critical artifacts fail compilation.

The synthetic example uses these modules:

| Module | Responsibility |
|---|---|
| `pack.yaml` | Exact manifest, layers, outputs, gates, and production blockers |
| `sources/source_manifest.yaml` | Immutable source identities, authority, access, and validity |
| `ontology/marketing_ontology.yaml` | Stable concepts, entity types, relation types, and applicability |
| `knowledge/content_mlr.yaml` | Claims, support assertions, risk bundles, content brief, and MLR policy |
| `omnichannel/decisioning.yaml` | Audience, journey state, channel policy, next actions, and receipts |
| `analytics/brand_performance.yaml` | KPI tree, metric contracts, data contracts, joins, and diagnostics |
| `agents/contracts.yaml` | Typed operations and trust envelopes |
| `quality/error_taxonomy.yaml` | Named failure modes linked to checks and evaluations |
| `evaluations/golden_cases.yaml` | Allow, block, abstain, calculation, and causal-restraint cases |

This follows the strongest Setu pattern: human-reviewable facets, an exact manifest, one typed compiler boundary, cross-module integrity checks, and failure-linked tests. Onto_Wiz extends it with evidence spans, applicability, releases, typed relations, client isolation, evaluation receipts, and rebuildable projections.

## 6. Canonical Artifact Families

### 6.1 Semantic and provenance

- `DomainNode`
- `Relationship`
- `TerminologyBinding`
- `Applicability`
- `SourceInstance`
- `SourceSpan`
- `EvidenceRef`
- `ReviewDecision`
- `Delta`
- `ReleaseManifest`
- `ReleaseAttestation`

### 6.2 Product, medical, and evidence

- `Brand`
- `ActiveIngredient`
- `Indication`
- `Population`
- `DoseRegimen`
- `Contraindication`
- `Warning`
- `AdverseReaction`
- `ClinicalEndpoint`
- `Study`
- `LabelVersion`
- `EvidenceItem`
- `SupportAssertion`

### 6.3 Claims, messages, and assets

- `Claim`
- `ClaimVariant`
- `RiskBundle`
- `MandatoryStatement`
- `ProhibitedExpression`
- `Message`
- `ContentBrief`
- `ContentBlock`
- `Asset`
- `AssetVariant`
- `ReferenceCitation`
- `MLRFinding`

### 6.4 Audience and omnichannel

- `StakeholderType`
- `Audience`
- `SegmentDefinition`
- `ConsentState`
- `ContactPolicy`
- `JourneyState`
- `StateObservation`
- `Trigger`
- `NextAction`
- `Channel`
- `FrequencyRule`
- `SuppressionRule`
- `DecisionReceipt`

### 6.5 Analytics and performance

- `MetricDefinition`
- `KPIEdge`
- `Dataset`
- `TableContract`
- `ColumnContract`
- `JoinContract`
- `QualityRule`
- `PlanSnapshot`
- `PerformanceObservation`
- `Variance`
- `DriverHypothesis`
- `Confounder`
- `AttributionAnalysis`
- `Experiment`
- `CausalAnalysis`
- `QueryReceipt`
- `PerformanceBrief`

## 7. Mandatory Common Fields

Every governed artifact needs, directly or through an envelope:

```text
stable ID
artifact kind and schema version
semantic version
lifecycle state
owner and review authority
client/tenant applicability
market, audience, purpose, channel, brand, indication, and time applicability
evidence references with SourceSpan[]
effective and expiry dates
supersedes/superseded-by links
confidentiality and access class
creation method: imported, agent-proposed, SME-authored, or derived
review decisions
evaluation links
release identity
```

Missing applicability is not interpreted as globally permitted. Correctness-critical artifacts fail closed when required scope is absent.

## 8. Claim and Evidence Contract

A promotional claim is a semantic proposition, not a sentence. It needs:

```text
subject + predicate + object
claim class and communication purpose
indication and population qualifiers
endpoint and timepoint
comparator
result, unit, and uncertainty
market/audience/channel applicability
governing label version
required risk bundle
mandatory qualifications
prohibited contexts and transformations
support assertions
effective and expiry dates
review state
```

Textual variants are separate governed artifacts. Paraphrasing must not broaden the population, endpoint, comparator, duration, certainty, or indication.

`SupportAssertion` expresses the relationship between claim and evidence: `DIRECT`, `DERIVED`, `CONSISTENT_WITH_LABEL`, `INSUFFICIENT`, `CONFLICTING`, or `WITHDRAWN`. Model confidence is not evidence strength and is not an approval.

## 9. Marketing-Purpose Boundary

Every request declares one purpose:

- `PROMOTIONAL`
- `DISEASE_AWARENESS`
- `MEDICAL_INFORMATION`
- `SCIENTIFIC_EXCHANGE`
- `PATIENT_SUPPORT`
- `CORPORATE_COMMUNICATION`
- `INTERNAL_TRAINING`

The pack must not allow a marketing workflow to answer an unsolicited off-label question as promotional copy. It routes medical-information, adverse-event, product-complaint, privacy, and quality signals to the client-authorized process.

## 10. Brand Analytics Semantic Layer

### 10.1 KPI tree

The reference KPI hierarchy covers:

- Financial outcome: net sales, units, and gross-to-net.
- Demand and adoption: NBRx, TRx, active writers, writer breadth/depth, and share.
- Access and fulfilment: coverage, paid/rejected claims, abandonment, and time to therapy.
- Continuity: refill and persistence proxies.
- Commercial engagement: eligible reach, frequency, content exposure, and field reach.
- Efficiency: spend and cost per governed outcome.
- Operating effectiveness: MLR cycle time, first-pass rate, reuse, and deployment time.
- Measurement health: completeness, freshness, revisions, identity coverage, and suppression.

KPI edges are typed:

- `ARITHMETIC_COMPONENT`
- `FUNNEL_TRANSITION`
- `DIAGNOSTIC_INDICATOR`
- `OBSERVED_ASSOCIATION`
- `CAUSAL_EFFECT`
- `CONSTRAINT`

Position in a KPI tree never implies causality.

### 10.2 Metric namespaces

```text
obs.*       descriptive observation
plan.*      approved plan or forecast
attr.*      allocated attribution credit
model.*     prediction or propensity
causal.*    governed incremental-effect estimate
dq.*        data-quality measure
```

An `attr.*` result cannot support causal or ROI language. Only an eligible `causal.*` artifact with its assumptions, uncertainty, and review state may support an incremental-effect statement.

### 10.3 Metric contract

Every metric defines:

```text
business definition and semantic version
metric type and formula
numerator, denominator, and zero-denominator behavior
grain and time basis
calendar, timezone, cohort, and lookback rules
inclusions and exclusions
allowed dimensions
unit and rounding
source columns and approved join paths
latency and restatement policy
privacy and suppression rules
valid analytical uses
prohibited interpretations
owner and review state
```

Pharma-specific caveats must be machine-readable. Prescriptions are not unique patients; NBRx varies by provider and needs an explicit lookback; indication may not be observable; recent cohorts can be right-censored; shipments are not patient demand; opens are imperfect engagement proxies; and targeted engagement creates selection bias.

### 10.4 Join contract

Joins are governed artifacts with keys, cardinality, temporal rule, required pre-aggregation, fan-out policy, eligible metrics, and quality thresholds. Undeclared joins fail. Many-to-many asset-to-claim or touchpoint-to-prescription paths cannot be summed without the declared analysis grain.

### 10.5 Diagnostic response

A `PerformanceBrief` separates:

```text
observed facts
magnitude, scope, and baseline
data-health qualification
candidate driver hypotheses
supporting and contradicting evidence
confounders and alternatives
causal conclusions, if any
recommended next analyses
permissible action candidates
query receipts
```

## 11. Agent Contract

Agents call typed operations, never storage directly. Minimum operations are:

```text
resolve_concept
get_content_brief
get_eligible_claims
explain_claim_support
get_required_risk
get_channel_policy
validate_draft
explain_finding
get_next_action_options
get_metric_definition
query_metric
compare_metric
decompose_variance
trace_metric_lineage
get_dataset_health
diagnose_brand_variance
get_experiment_result
submit_feedback
```

Every response includes a trust envelope:

```text
pack ID and release ID
artifact IDs and versions
scope and applicability
evidence locators
policy and label versions
effective and expiry dates
access decision
data snapshot and query receipt where numeric
evaluation receipt
human-approval requirement
```

## 12. Evaluation Spine

### 12.1 Structural and release

- Exact manifest equals the module files on disk.
- Duplicate IDs and unresolved references fail.
- Deterministic compilation produces identical outputs for identical inputs.
- Label, policy, metric, and table changes invalidate dependants.
- Candidate diff and rollback are reproducible.
- Synthetic artifacts cannot enter a production release.

### 12.2 Content and MLR

- Every promotional claim has exact evidence spans.
- Population, endpoint, comparator, timepoint, result, and unit match evidence.
- Required risk and qualifications remain coupled to claims.
- Wrong market, audience, purpose, indication, channel, or expired label fails closed.
- Paraphrases do not broaden meaning.
- The service never represents a preflight result as approval.
- Visual prominence and overall impression are routed for human review where automation is insufficient.

### 12.3 Omnichannel

- Consent, eligibility, suppression, frequency, and expiry rules are enforced.
- Journey state includes evidence, confidence, and freshness.
- Generated drafts are not selected as released assets.
- Associations are not presented as causal effects.
- Every decision carries considered options, exclusions, rationale, and policy versions.

### 12.4 Analytics

- Fixed-fixture calculations exactly reproduce expected results.
- Metric version, formula, grain, source snapshot, and plan snapshot are present.
- Temporal joins and fan-out protection work.
- Data quality is checked before business diagnosis.
- Prescriptions are never described as patients.
- Descriptive attribution never becomes incremental language.
- Causal statements require an eligible experiment or causal-analysis artifact.
- Privacy, access, and small-cell rules are hard gates.
- Insufficient or conflicting evidence returns `UNRESOLVED`.

### 12.5 Agent lift

Held-out cases compare the same agent with and without the pack. Report task accuracy, grounding, abstention, critical-error rate, uncertainty, and confidence interval. A release gate cannot be satisfied by aggregate pass rate if a critical compliance, privacy, tenant-isolation, or numeric-correctness case fails.

## 13. Two Executable Vertical Slices

### Slice A: content and MLR

> Create a short US HCP email draft for dermatologists evaluating therapy for eligible adults, then produce an MLR preflight.

The pack must resolve the scoped synthetic claim, evidence, required risk, channel rule, CTA, prohibited transformations, references, and human-review requirement. The same branded request for a GB general-public audience must be blocked.

### Slice B: brand performance

> Explain why synthetic Auravia Northeast NBRx was below plan for a selected week and assess whether HCP email can be named as a cause.

The fixture contains a negative NBRx variance, lower writer depth, lower paid-claim rate, stable eligible reach, higher email engagement proxy, and no controlled email experiment. The correct conclusion treats access as a supported hypothesis, rejects email underperformance as an observed explanation, and leaves the causal question unresolved.

## 14. Definition of Done for a Build-Team Implementation

1. Proposed schemas exist in `ontowiz-spec` with explicit compatibility and migration tests.
2. The source pack compiles through one typed boundary; no runtime component reparses its YAML independently.
3. The manifest is exact and every cross-reference resolves.
4. Source identity is separate from immutable content identity; every material claim has `SourceSpan[]` evidence.
5. All projections are reproducible from the governed release.
6. Candidate packs may fail evaluation, but publish and production serving reject unrun or failing gates.
7. At least 20 held-out cases cover allow, block, abstain, exact calculation, wrong-scope, stale-source, access, fan-out, and causal-restraint behavior.
8. Critical content, privacy, tenant, numeric, and synthetic-production tests all pass.
9. Every served result has a trust envelope; every number has a query receipt.
10. The content assistant never approves; the analytics assistant never invents causality.
11. Release diff, dependency invalidation, rollback, and deterministic rebuild evidence are captured.
12. SME corrections create governed Deltas and regression cases before the next release.

## 15. Build Sequence

1. Accept this reference shape as an intent document, not as an implementation-ready schema.
2. Add shared source, span, applicability, evidence, metric, table, join, eval, and release contracts.
3. Revise the parser boundary to preserve multi-span provenance and source-instance metadata.
4. Implement exact-manifest and cross-module validation.
5. Compile the content/MLR vertical slice with candidate-only status.
6. Add semantic metric and governed query contracts for the analytics slice.
7. Implement failure-linked evaluations and hard release gates.
8. Add curator and SME workflows only after the Delta and artifact contracts are executable.
9. Add vector, graph, lexical, and catalog projections as rebuildable outputs.
10. Promote the fixture only as a tested reference pack; keep `production_eligible: false` permanently.

## 16. Explicit Non-Goals

- This fixture is not medical, legal, regulatory, or promotional advice.
- It does not encode current rules for a real product or client.
- It does not authorize autonomous MLR approval.
- It does not make observational marketing data causal.
- It does not expose patient-level data to general marketing agents.
- It does not require an OWL-first ontology or a particular graph/vector vendor.
- It does not change the current production compiler or artifact schemas by itself.
