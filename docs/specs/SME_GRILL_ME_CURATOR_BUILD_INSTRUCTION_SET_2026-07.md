# SME Grill Me Curator - Build Instruction Set

**Status:** DRAFT FOR INT/REV - not an implementation authorization  
**Date:** 2026-07  
**Audience:** product, domain engineering, backend, frontend, evaluation, security, and pilot operations  
**Maps to:** E2 Forge, E5 Studio, E1 Intake, E3 governance, and the Domain Pack Platform build sequence

## 1. Decision

Build **Grill Me** as a guided discovery mode of Forge that reuses the planned
Studio conversation-as-source and grounded structurer capabilities. Do not create a
new chatbot service, extraction path, artifact schema, approval path, or pack writer.

The experience is conversational, but the product is not a generic chat interface.
It is a controlled interrogation protocol that:

1. profiles where an SME can contribute;
2. selects the highest-value unresolved domain question;
3. challenges definitions, boundaries, differences, evidence, and counterexamples;
4. structures only claims grounded in the SME's exact words or linked sources;
5. asks the SME to confirm or amend the exact candidate artifact and eval;
6. emits proposed Deltas, durable dissent, and regression evals; and
7. stops at `READY_FOR_CURATOR`, never at released or active.

The chatbot does not commit a final domain pack when it "feels" that quality is
high. Readiness is a deterministic, inspectable result. Release remains a separate
authorized action over an unchanged candidate digest and passing eval receipts.

## 2. Current Implementation Audit

### 2.1 What exists and should be reused

| Capability | Current evidence | Assessment |
|---|---|---|
| Static SME reasoning exercise | `frontend/src/components/SituationRoom.tsx`, `useGameSession.ts`, game components | Useful UX research; not an adaptive interview |
| Session-to-proposed-Delta conversion | legacy `src/api/server.py` plus `packages/ontowiz-core/.../delta_generator.py` | Demonstrates the idea; not production-safe |
| Gap-ranked curation missions | `ontowiz_factory/steward.py` and `missions.py` | Correct kernel for targeted questions |
| Delta + eval + confidence contract | `submit_mission()` and tests | Preserve and strengthen |
| Dissent-preserving consensus | `ontowiz_factory/forge.py` | Reuse after the k=1 pilot gate |
| Governance persistence seam | `ontowiz_runtime/governance.py` and F0.2 work | Foundation, not yet Forge/Studio persistence |
| SME contribution/impact UI | SME dashboard components | Rework around verified impact, not activity counts |
| Target product design | `FORGE_MODULE_DESIGN_2026-07.md` and E2/E5 build instructions | Strong direction; Grill Me makes the guided discovery protocol explicit |

### 2.2 What is not implemented

The canonical `ontowiz-serve` app has no `/v1/forge` or `/v1/studio` routes. There
are no canonical Forge question, assignment, answer, ratification, probe, Studio
session, turn, or staged-object tables. There is no adaptive question planner,
SME capability profile, contradiction ledger, readiness calculation, or grounded
chat structurer wired into the governed platform.

### 2.3 Why the legacy Situation Room cannot be promoted as-is

1. The flow is a fixed sequence rather than a gap-driven adaptive interrogation.
2. Reasoning events are held in memory and disappear on restart.
3. The request does not carry an authenticated SME principal or durable capability profile.
4. Scenario identity is used as session identity, and brand context is replaced with `Unknown`.
5. A single submission can generate several Deltas without exact turn/span grounding.
6. The legacy generator does not create a discriminating eval for every generated artifact.
7. It has no confirm step over the exact structured payload before knowledge persistence.
8. It does not test contradictions against the current pack or prior SME answers.
9. Its success test is "a Delta appeared," not "a validated gap was closed."

Treat this path as a disposable prototype and source of interaction patterns. Port
no endpoint until its behavior is expressed through the canonical contracts.

## 3. Product Modes

Grill Me must support two modes on one engine.

### 3.1 Validate and improve an existing pack

The planner starts from real weaknesses in a pinned pack snapshot: unvalidated
artifacts, missing evidence, missing evals, low confidence, absent exceptions,
conflicts, staleness, agent failures, and high-usage gaps. This is the primary mode.

### 3.2 Build a base pack from a coverage contract

For a new domain, the domain lead first defines a **coverage contract**: required
subdomains, artifact families, critical decisions, data semantics, failure modes,
and minimum eval suites. The planner interrogates SMEs against missing cells in
that contract. It must not use an open-ended request such as "tell me everything
about pharma marketing."

Base-pack contributions land in an engagement-scoped workspace first. Promotion
to reusable base IP is an explicit curator/IP-owner decision with source rights,
confidentiality, and tenant checks. Client-specific knowledge never silently enters
the shared base pack.

## 4. SME Experience

### 4.1 Entry and capability calibration

The first session captures a versioned, self-declared profile:

- functions and subdomains;
- therapeutic areas and product lifecycle experience;
- countries/markets and channels;
- evidence, data, analytics, content, MLR, access, or operations focus;
- experience recency and declared limitations;
- conflicts of interest and restricted client/brand affiliations;
- preferred question modes and accessibility needs; and
- explicit `I do not know` and `outside my scope` behaviors.

Self-declared expertise improves routing but grants no authority. Reliability may
be calibrated only from sufficient protected-probe and adjudication history, with
sample size and uncertainty shown.

### 4.2 One conversational turn

Each turn must show:

1. one question and why it matters;
2. the pack/version, node, and artifact or coverage gap being tested;
3. relevant evidence with access-aware disclosure;
4. an expected response mode;
5. `I do not know`, `outside my scope`, `needs another expert`, and dissent actions;
6. the structured artifact and eval drafted from the answer; and
7. confirm, amend, reject, or save-for-later controls.

Response modes are typed: select, rank, compare, free text, numeric definition,
table/join description, evidence link/upload, scenario outcome, or boundary case.
Free text is available, but it is never the only interaction method.

### 4.3 Interrogation pattern

For each material proposition, the planner works through applicable challenges:

| Challenge | Example ask | Intended output |
|---|---|---|
| Define | "What exactly does an eligible HCP mean here?" | concept or definition |
| Differentiate | "How is engagement different from qualified engagement?" | boundaries and near-neighbor relation |
| Apply | "In which market, audience, channel, and lifecycle does this hold?" | applicability |
| Disconfirm | "What observation would make this explanation wrong?" | anti-pattern or eval |
| Exception | "When does this rule not hold?" | exception rule |
| Counterexample | "Give a real-shaped case where the usual answer fails." | held-out scenario |
| Evidence | "What source or experience supports this, and how strong is it?" | evidence assertion or unverified marker |
| Operationalize | "What decision changes if this is true?" | heuristic or playbook |
| Quantify | "What is the formula, grain, period, and denominator?" | metric definition |
| Locate data | "Which table, keys, filters, and joins implement it?" | source/table/join contract |
| Contrast peers | "Another SME said X. Under what condition is X right?" | dissent, priority, or adjudication |
| Refresh | "What event would make this stale?" | validity and refresh trigger |

The system must not exhaustively ask every challenge. It chooses the next question
from unresolved risk and value, and explains that choice.

## 5. Architecture

```text
SME UI
  -> Forge interview API
     -> authenticated session + version-pinned SME profile
     -> deterministic question planner
        -> pack/coverage gaps + usage + eval failures + conflicts + staleness
     -> conversation source/turn store (shared with Studio and Intake provenance)
     -> grounded answer structurer
        -> exact turn spans + typed staged artifacts + draft evals
     -> ConfirmSheet
        -> confirmed answer / amendment / dissent
     -> submit_mission + Delta pipe
        -> proposed artifact versions + eval cases + contribution lineage
     -> curator queue
        -> semantic review + conflict resolution + independent evals
     -> deterministic compile -> sealed candidate
     -> eval receipts -> release attestation
     -> REST/MCP typed context serving
```

### 5.1 Module ownership

| Concern | Owner |
|---|---|
| Question signals, ranking, routing, probes, and impact | Forge |
| Session/turn-as-source, exact spans, grounded structuring, staged objects | shared Intake/Studio structurer service |
| Artifact schemas and cross-artifact validation | `ontowiz-spec` |
| Proposed changes, approvals, audit, and contribution lineage | Delta/governance core |
| Candidate build, eval, attestation, and serving | domain pack platform |
| Chat/mission experience and coverage view | one frontend application |

No module may write directly to a source pack, candidate directory, release mapping,
vector index, search projection, or active artifact.

## 6. State Contracts

### 6.1 Interview session

`ACTIVE -> PAUSED -> READY_FOR_REVIEW -> SUBMITTED`

Terminal alternatives are `ABANDONED`, `EXPIRED`, and `BLOCKED`. Resuming uses the
same durable session and pinned corpus snapshot. Abandoning a session leaves its
source/audit record but mutates no governed artifact.

### 6.2 Turn and answer

`ASKED -> ANSWER_RECORDED -> STRUCTURED -> SME_CONFIRMED -> PROPOSED`

Alternatives are `SKIPPED`, `OUT_OF_SCOPE`, `REJECTED`, `CONTESTED`, and
`ESCALATED`. Unconfirmed structurer output is session-local and cannot be queried
as pack knowledge.

### 6.3 Readiness

The planner returns one of:

- `NEEDS_COVERAGE`;
- `NEEDS_EVIDENCE`;
- `NEEDS_CHALLENGE`;
- `CONTESTED`;
- `BLOCKED_BY_RIGHTS_OR_ACCESS`; or
- `READY_FOR_CURATOR`.

It never returns `APPROVED`, `ACTIVE`, `PUBLISHED`, or `RELEASED`.

## 7. Minimum Data Contracts

Do not freeze physical schemas before the F0 migration and tenancy seams are
accepted. The logical records are nevertheless mandatory:

### 7.1 `SMECapabilityProfile`

`id`, `principal_id`, `tenant_id`, `version`, `domains`, `nodes`, `markets`,
`functions`, `experience_recency`, `limitations`, `conflicts`, `access_classes`,
`self_declared_at`, `calibration_summary`, and `superseded_by`.

### 7.2 `InterviewSession`

`id`, `tenant_id`, `principal_id`, `profile_version`, `mode`, `workspace_scope`,
`pack_name`, `base_release_digest`, `coverage_contract_digest`, `status`,
`started_at`, `updated_at`, `expected_version`, and `source_id`.

### 7.3 `QuestionPlan`

`question_id`, `session_id`, `question_type`, `target_node`, `target_artifact_ids`,
`target_artifact_families`, `signal_ids`, `prompt_template_version`, `response_schema`,
`challenge_policy`, `impact_factors`, `selection_reason`, `evidence_refs`,
`snapshot_digest`, `lease`, and `status`.

### 7.4 `AnswerRecord`

`id`, `question_id`, `principal_id`, `raw_answer`, `typed_answer`, `confidence`,
`turn_id`, `source_spans`, `source_links`, `model_run_id`, `structurer_version`,
`confirmed_payload_digest`, `confirmation_event`, `dissent`, `amendments`, and
`created_at`.

### 7.5 `CoverageLedger`

For each required cell: domain node, artifact family, criticality, minimum evidence,
minimum independent confirmations, eval requirements, current eligible artifacts,
open conflicts, freshness, and readiness blockers. This ledger is a derived view,
not a second source of truth.

## 8. Question Planner Rules

The planner's target selection must be deterministic for a pinned snapshot. An LLM
may phrase a question or structure an answer; it may not decide authorization,
silently change priority factors, or declare readiness.

Minimum selection signals:

1. required coverage gap;
2. correctness/safety criticality;
3. missing or weak evidence;
4. missing discriminating eval;
5. missing exception or anti-pattern;
6. low confidence or high uncertainty;
7. unresolved contradiction or dissent;
8. usage or agent-failure impact;
9. staleness and refresh trigger; and
10. SME profile fit, conflict exclusion, access, prior answers, and fatigue.

Persist the factor breakdown and template version. Replaying the same snapshot,
profile, prior-turn state, and configured seed must select the same target. Question
wording may vary only when its semantic target, answer schema, and challenge policy
remain pinned and are recorded.

## 9. Grounding and Evidence Rules

1. Every staged field is grounded to an exact SME turn span or an accessible source span.
2. A statement based only on recollection is marked `SME_ASSERTION`, never upgraded to documentary evidence.
3. An external factual claim without an accessible source stays `UNVERIFIED` and blocks correctness-critical release where evidence is mandatory.
4. The structurer must not infer market, population, channel, metric grain, or authority from conversational context when the SME did not state it.
5. Prompt injection or instructions inside uploaded material are treated as source text, not system instructions.
6. Speaker, source rights, access class, model run, prompt version, amendments, and confirmation are retained.
7. Deletion, withdrawal, or permission loss propagates to dependant artifacts and readiness.

## 10. Artifact and Evaluation Outputs

The interrogation must produce typed objects appropriate to the gap, including:

- concepts, synonyms, entities, and relations;
- claims, support assertions, limitations, risk bundles, and content/channel rules;
- audience, journey, eligibility, suppression, and next-action rules;
- decision heuristics, judgment patterns, exceptions, anti-patterns, and playbooks;
- metric, table, source, join, quality, and freshness contracts;
- failure taxonomy entries and validator requirements; and
- positive, negative, abstain, calculation, boundary, and adversarial eval cases.

`submit_mission()` is the route for an accepted artifact-producing answer, but its
current simple `must_contain` eval is insufficient as the release proof. The answer
may draft a paired regression case. Critical release suites additionally require
independent, held-out, and failure-linked cases so the same statement is not both
the knowledge and the only proof that the knowledge is correct.

## 11. Readiness Calculation

`READY_FOR_CURATOR` requires all configured checks for the selected scope:

- every mandatory coverage cell is satisfied or explicitly waived by an authorized role;
- correctness-critical objects have required evidence and applicability;
- all references resolve and semantic validators pass;
- contradictions are resolved, represented as scoped exceptions, or escalated;
- minimum independent confirmation is met where configured;
- required eval families exist and are not derived solely from the artifact author;
- no rights, tenant, confidentiality, synthetic-production, or access blocker remains;
- no stale source invalidates a dependant object; and
- every proposed object has exact lineage and a confirmed payload digest.

Readiness is recalculated when any source, answer, artifact, policy, coverage contract,
or eval changes. It is advisory to the curator and cannot authorize compile or release.

## 12. API Shape

Extend the planned Forge surface; do not expose the legacy `/sessions` API.

```text
POST   /v1/forge/interviews
GET    /v1/forge/interviews/{id}
POST   /v1/forge/interviews/{id}/resume
GET    /v1/forge/interviews/{id}/next
POST   /v1/forge/interviews/{id}/answers
POST   /v1/forge/interviews/{id}/answers/{answer_id}/structure
POST   /v1/forge/interviews/{id}/answers/{answer_id}/confirm
POST   /v1/forge/interviews/{id}/answers/{answer_id}/reject
GET    /v1/forge/interviews/{id}/coverage
GET    /v1/forge/interviews/{id}/readiness
POST   /v1/forge/interviews/{id}/submit
GET    /v1/forge/impact
```

Every mutation requires JWT capability, resource ownership, `Idempotency-Key`,
expected version/ETag, bounded request size, and an immutable audit event. Confirm
accepts the digest of the exact staged payload shown to the SME; a changed payload
returns `409` and must be reviewed again.

## 13. Frontend Strategy

The default view is a focused work surface, not a marketing page and not a blank chat.

### 13.1 Main regions

1. **Conversation:** one active question, structured response controls, evidence, and challenge thread.
2. **Coverage map:** required areas, confidence/evidence/eval state, conflicts, and staleness.
3. **Staging tray:** exact proposed objects and evals, visibly distinct from corpus knowledge.
4. **Why this question:** inspectable signal and impact factors.
5. **Session readiness:** blockers and completed checks, never a decorative percentage alone.

On phone width, show one question at a time with evidence and the staging confirmation
one interaction away. On desktop, keep the coverage map and staging tray visible.
Support keyboard operation, screen readers, long values, pause/resume, network retry,
expired assignments, inaccessible evidence, and model-unavailable fallback.

### 13.2 Gamification

Use missions, progress through the coverage contract, impact receipts, team challenges,
and attributable shipped expertise. Do not initially use a public leaderboard.

Never reward answer volume, speed, agreement with the majority, unsupported certainty,
or approval rate. Points, ratings, streaks, and badges can influence recognition and
routing only. They cannot grant access or medical, legal, regulatory, privacy, data,
MLR, curator, compile, or release authority.

## 14. Pharma Starter Campaigns

Use the synthetic pharma marketing reference pack to prove three campaigns.

### 14.1 Content and MLR

- define claim, message, asset, audience, channel, and approval boundaries;
- distinguish claim approval from asset approval;
- elicit required qualifications, risk coupling, prohibited transformations, and exceptions;
- challenge wording across market, population, endpoint, comparator, duration, and certainty; and
- create allow, block, abstain, evidence, and overall-impression evals.

### 14.2 Omnichannel

- define audience state, consent, eligibility, suppression, frequency, journey freshness, and channel constraints;
- distinguish content eligibility from next-action eligibility;
- compare actions under concrete scenarios and ask what would reverse the preference;
- elicit decision receipts, escalation paths, and stale-data behavior; and
- create boundary cases for missing consent, stale state, and unavailable released assets.

### 14.3 Brand analytics

- define KPI tree, metric formula, grain, denominator, period, filters, and namespace;
- locate authoritative tables, keys, joins, quality thresholds, and freshness;
- distinguish observation, attribution, prediction, causal estimate, hypothesis, and recommendation;
- challenge a proposed explanation with disconfirming evidence and alternative causes; and
- create calculation, fan-out, leakage, missing-data, and causal-restraint evals.

## 15. Build Units and Definition of Done

Do not interrupt the current candidate/release and semantic-kernel build. The rule in
the platform instruction set still applies: polished Forge/Studio work waits until
the underlying artifact, governance, compiler, eval, and release contracts are stable.

### GM0 - Contract consolidation

**Work:** map legacy Situation Room fields, Forge missions, E2, E5, and the domain-pack
artifact families into one canonical contract; write migration/deletion decisions for
the legacy path.

**DoD:** one accepted state model, one API namespace, one source/turn model, one Delta
path, one eval model, and an explicit list of legacy code that will not be ported.

### GM1 - Durable profile, session, and turn spine

**Work:** capability profiles, authenticated interviews, conversation-as-source,
turns, pause/resume, optimistic concurrency, access and audit.

**DoD:** restart preserves the exact session; cross-tenant and ID-guess tests deny;
abandon mutates no artifact; duplicate answer/confirm requests are idempotent.

### GM2 - Deterministic question planner v0

**Work:** coverage contract plus four E2.1 signals: unvalidated, low confidence,
missing eval, and missing exception. Use fixed question templates before LLM phrasing.

**DoD:** pinned input produces the same ordered targets and factor breakdown; own,
conflicted, inaccessible, stale, answered, and retired targets are excluded.

### GM3 - Grounded structurer and confirmation

**Work:** exact turn/span grounding, typed staged objects, draft eval, ConfirmSheet,
amend/reject/dissent, and `submit_mission`/Delta integration.

**DoD:** adversarial conversations produce zero accepted ungrounded fields; changed
payload digest cannot confirm; every accepted answer links source, answer, candidate,
Delta, eval, actor, and amendment history; no answer writes ACTIVE.

### GM4 - Challenge and contradiction engine

**Work:** difference, boundary, counterexample, evidence, metric/data, contradiction,
and freshness challenges; coverage/readiness ledger.

**DoD:** a vague rule cannot become ready without required scope; contradictory SME
answers remain visible and route to exception/adjudication; readiness blockers are
reproducible and inspectable.

### GM5 - Pilot UI and operations

**Work:** focused interview surface, coverage map, staging tray, impact receipts,
consent/briefing, support, withdrawal, telemetry, and phone/desktop accessibility.

**DoD:** 3-5 SMEs complete sessions without developer help; all evidence and staged
objects are inspectable; 360/768/1440 visual checks, keyboard, screen-reader, retry,
expiry, pause/resume, and model-down paths pass.

### GM6 - Multiplayer, probes, and calibrated routing

**Gate:** build only after the Forge v0 continuation metrics pass.

**Work:** k=3 routing, independent confirmations, protected probes, unweighted baseline,
then calibrated weights, contest/adjudication, and leakage monitoring.

**DoD:** split answers never become false certainty; probe content is protected;
rapid-click, collusion, self-review, rating gaming, and small-sample certainty tests fail;
minority positions remain verbatim and attributable.

### GM7 - Open Studio composition

**Gate:** build only after guided interviews and batch Intake prove the structurer.

**Work:** allow a curator to start an open conversation while reusing the same source,
turn, grounding, staging, confirmation, and Delta services.

**DoD:** open Studio introduces no third extraction stack and cannot bypass the same
readiness, review, compile, eval, and release controls.

## 16. Required Test Matrix

At minimum, automate:

- restart, migration, transaction rollback, lease expiry, and duplicate suppression;
- JWT role, ownership, cross-tenant, source-access, and guessed-ID denial;
- stale ETag, concurrent answer, concurrent confirm, and changed-payload conflict;
- deterministic question target/ranking and inspectable factor replay;
- source deletion, permission loss, confidentiality, and profile conflict propagation;
- ungrounded inference, fabricated quote, prompt injection, and unsupported applicability;
- `I do not know`, out-of-scope, dissent, contradiction, and unresolved escalation;
- one proposed Delta and appropriate eval linkage for every confirmed artifact output;
- no direct source-pack, candidate, release, projection, or ACTIVE write path;
- held-out and independent eval requirements for critical artifacts;
- candidate immutability and receipt/release digest binding;
- rapid-click, answer-volume, majority-bias, collusion, probe-leakage, and self-review abuse;
- accessible choice, rank, free-text, long-value, error, offline, and resume flows; and
- one pharma content/MLR, omnichannel, and analytics end-to-end vertical slice.

## 17. Pilot Measures and Stop Rules

Measure outcomes, not chat activity:

- confirmed artifact-plus-eval outputs per SME hour;
- curator acceptance, amendment, rejection, and escalation rates;
- critical coverage gaps closed per session;
- contradictions and missing boundaries discovered;
- held-out eval improvement and post-release recurrence reduction;
- time from confirmed answer to governed release;
- week-2 SME return and qualitative trust; and
- attributable reuse across agents, packs, or client-safe overlays.

Stop at v0 and invest in Intake/Queue instead when Grill Me does not beat quick
capture on useful governed outputs per SME hour, SMEs do not return, curator correction
cost is excessive, or the questions mostly produce unsupported narrative.

## 18. Non-Negotiable Rejections

Reject any implementation that:

- sends an unconstrained transcript to an LLM and writes its summary as ontology;
- lets model confidence, a readiness score, or SME points authorize release;
- creates a separate chatbot database without source, Delta, and audit lineage;
- stores only the structured answer and drops the raw answer, span, or dissent;
- treats self-declared expertise as approval authority;
- treats consensus as truth or averages away exceptions;
- uses the same SME statement as both the only artifact evidence and the only release eval;
- indexes unconfirmed staged objects into the agent-facing search namespace;
- copies client knowledge into the reusable base pack without rights and scope decisions;
- asks broad questions with no coverage target or impact rationale; or
- describes the current repository as already delivering this capability.

## 19. Acceptance Statement

Grill Me is ready for a real pilot only when an SME answer can be traced from the
authenticated turn and exact evidence span through confirmation, proposed Delta,
paired regression case, curator decision, immutable candidate, independent eval
receipt, release attestation, and a typed agent response - and when abandoning or
failing at any earlier stage leaves released knowledge unchanged.
