# OntoWiz Authoring Kit — Critique & v0 Build Spec

**For:** the team building the authoring path (BE/Core + the Codex/Claude skill owner).
**Status:** Revision 2 (2026-07-25). Grounded in the current codebase + the ratified validation
plan (`ENTERPRISE_MATURITY_CONSOLIDATION_2026-07.md` Rev 3, `EXPERIMENT_PRE_REGISTRATION_2026-07.md`).
**Purpose:** turn a rich multi-part discussion (scaffolding · ingestion · visual explorer ·
Grill/Forge · evaluation module) into ONE buildable, disciplined v0 spec.

---

## 0. Verdict

The discussion is right and I endorse it: **Codex/Claude is the authoring agent; the Authoring Kit
is a framework-neutral skill backed by a small repo of the platform's real schemas/validators/eval;
OntoWiz later governs and distributes what the kit proves can be manufactured.** The additions —
use-case scaffolding, source ingestion, a visual explorer, Grill-with-Docs + Forge missions, and a
first-class evaluation module — are all correct in principle. **The risk is scope:** the thread now
describes a large product, and "build the kit" is the same over-build trap we've flagged all session.
So this spec does one thing — **defines the thin v0 that tests the core hypothesis** — and stages the
rest. The core hypothesis is unchanged:

> Can one qualified SME, using Codex/Claude + the Authoring Kit, produce a **better candidate
> context pack** (more grounded, more testable, more reusable, safely governed) than the same
> expert with an ordinary folder — **without degrading decision quality**?

That is the produce-side of **Arm 2 vs Arm 3** in the ratified experiment. The kit is not a new
initiative; **it is how Arm 2 and Arm 3 get authored, and the eval module is the experiment's
scoring apparatus.** Build it as one track.

---

## 1. What the discussion gets right (endorse)

- **Candidates, not authority** — matches the platform's strongest built invariant (delta_id-gated
  ACTIVE, `artifacts.py:135-151`).
- **Decisions-first scaffolding** ("describe the use case → the kit builds the pack structure").
- **Archetype composition, not a template per use case** (core → domain core → capability module →
  overlay).
- **Source ingestion as candidate claims**, confirmed by the SME before they change the pack.
- **Grill-with-Docs + Forge missions + a Question Compiler** as the authoring engine (adaptive,
  gap-driven, finite).
- **A visual explorer** as the SME's comprehension surface — generated from canonical files.
- **A mandatory evaluation module** split into pack-integrity / decision-quality / implemented-agent
  layers, with a protected held-out vault.
- **The eval set may be the most defensible IP** — the failure taxonomy captures how experts know an
  answer is wrong.
- **Gamify contribution quality, not activity** (no leaderboards-as-authority in pharma).

None of that needs re-arguing. The rest of this doc is scope + traps + the concrete v0.

---

## 2. Grounded reality the kit must respect

The kit will emit richer artifacts than the platform ingests today. This is fine **only if** output
is pinned to one target contract. What actually exists:

| Concept the kit emits | Platform status | Implication |
|---|---|---|
| Typed artifacts (19 kinds), lifecycle+Delta approval | **BUILT** | Reuse; wire the candidate/approval boundary |
| Metric / evidence / applicability / decision-eval contracts | **NOT BUILT** (Rev 3 spine work) | The kit is the forcing function — build these as `ontowiz-spec/vNext-min` |
| Tool contracts (`query_metric`, `block_when`, `abstain_when`) | **DESIGN FIXTURE** (synthetic auravia, no consumer) | Emit, but no runtime runs them yet — pin to target |
| Overlays / precedence / multi-pack composition | **SCHEMA ONLY — nothing resolves it** | v0 "composition" = an **authoring-time template merge**, NOT runtime overlay resolution |
| Decision-level evaluation | **NOT BUILT** — current evals are `must_contain` term matching (`evals.py:43-61`) | The kit must ship decision-level eval |
| Auto-activation | Seeder does `system:seed → MERGED → ACTIVE` (`seed.py:96-108`) | Do **not** inherit — candidate by construction |

**Load-bearing distinction:** when the kit "composes" `core + domain + capability + overlay` into a
scaffold, that is a **file-assembly step inside the authoring project**, not the runtime overlay
resolution the platform hasn't built. Don't let the team conflate the two.

---

## 3. The guardrails (build it this way)

1. **G1 — Share the platform's contracts; never fork them.** The kit's `schemas/` **are**
   `ontowiz-spec` (pinned `vNext-min`). Author the kit and the minimal schema kernel together.
2. **G2 — Validators are adversarial / fail-closed.** The kit's value is **refusal**, not
   generation. `validate` must reject: no source · no evidence · a causal claim without a
   disconfirming clause · missing applicability · no abstention. *If `validate` passes today's
   `commercial_analytics/0.1.0`, it is wrong.*
3. **G3 — Candidate-only by construction.** Output lands `draft`/`candidate`, `reviewed_by:null`;
   approval requires a different principal. Reuse Forge's submit path — **after** fixing its two
   correctness gaps (dropped edited body; must-contain gold).
4. **G4 — The held-out firebreak is code.** `freeze-heldout` hashes+locks the held-out set; the
   drafting agent cannot read it; `evaluate` refuses to score on post-freeze drift.
5. **G5 — Thin slice first, under the spine ceiling.** One decision · ~5–10 concepts · 1–2 metric
   contracts · one method · one challenge pass · ~15–20 eval cases. Prove the loop; then widen.
6. **G6 — The explorer is a generated, disposable view.** Canonical YAML/JSON is the source of
   truth; `explorer.html` is regenerated from a `context-model.json`. It must never become a second
   source of truth.
7. **G7 — "Any SME" is wrong; route by authority.** One SME can lead, but the pack records which
   questions need a data steward / brand owner / MR methodologist / rights-privacy owner / approver.

---

## 4. The v0 build spec

### 4a. Scope — what is v0 vs later

| Capability | v0 (build) | v1 | v2 (platform) |
|---|---|---|---|
| Framework-neutral core skill + **Codex adapter** | ✅ | Claude adapter | Web front ends over governed tools |
| Use-case → scaffold by **archetype file-merge** | ✅ (BA + MR, +V&A example) | more archetypes | runtime composition/overlay resolution |
| Source ingestion → source register + **candidate claims** | ✅ | richer extractors (deck→image) | tenant intake + retention |
| Authoring engine: discover → scenario → challenge → **Forge-ratify** + Question Compiler + DDRs | ✅ (single SME + optional reviewer) | multi-role routing | multi-SME consensus, ForgeRating, curator queues |
| Candidate ontology / metric / evidence / method / policy / tool contracts | ✅ (candidate-only, evidence-anchored) | — | — |
| **Evaluation module** (charter → taxonomy → matrix → cases; dev/regression/held-out; freeze; agent-adapter; receipt; baseline-vs-pack) | ✅ | calibrated LLM-judge | production monitoring |
| Visual explorer | ✅ **regenerated static `explorer.html`** per checkpoint | live local refresh | collaborative review UI |
| Packaging | ✅ candidate + authoring receipt | signed candidate | attested release |
| Gamification | ✅ progress + impact only | private ForgeRating | optional org dashboards |

**Explicitly not v0:** live-refresh explorer · multi-SME consensus/leaderboards · LLM-judge as
authority · production monitoring · automated approval · runtime multi-pack composition · full
platform.

### 4b. Directory structure (one workspace per use case, per ADR-018 isolation)

```
<usecase>/                     # e.g. value-access-pricing/
├── workspace.yaml             # target schema version, archetypes selected, owner roles
├── sources/
│   ├── inbox/                 # uploaded transcripts/decks/docs (raw, gitignored from dist)
│   ├── source-register.yaml   # owner, rights, dates, confidentiality, checksum, scope
│   ├── extracted/             # SRC-*.json  (passages, spans, slide/timestamp refs)
│   └── candidate-claims/      # SRC-*.yaml  (claims mapped to artefacts — CANDIDATE)
├── authoring/
│   ├── session-state.yaml     # resume pointer (stage, last delta, open questions, next mission)
│   ├── sessions/<date-id>/    # session.yaml, questions.yaml, responses.yaml, receipt.yaml
│   ├── proposals/DELTA-*.yaml # every SME answer → a proposed delta (awaiting confirmation)
│   └── decisions/DDR-*.yaml   # Domain Decision Records
├── pack/                      # CANONICAL source of truth
│   ├── pack.yaml  scope/ ontology/ metrics/ methods/ policies/ retrieval/ workflows/
│   ├── tools/ evaluations/ governance/
├── reports/                   # validation.json, semantic-findings.json, readiness.json
├── build/                     # context-model.json, explorer.html  (DISPOSABLE, regenerated)
└── dist/                      # <usecase>-<ver>-candidate.zip  (governed citations, NOT raw sources)
```

Roles are deliberately distinct: `sources/` = evidence · `authoring/` = the conversation + proposals
· `pack/` = canonical pack · `build/` = disposable views · `dist/` = distributable candidate
(**raw client docs excluded by default** — ship citations + provenance, not confidential source bytes).

### 4c. Use-case → scaffold (archetype composition, authoring-time)

The SME says *"I want a value-and-access agent for pricing."* The kit first converts that into a
**decision contract** (which decisions · which markets/products/lifecycle · advise vs calculate vs
recommend vs approve · what must stay human-owned · what is out of scope · what is a materially
unsafe answer), then assembles the scaffold from **archetype files** (`enterprise_core +
pharma_commercial_core + value_access_core + pricing_module + overlay`). Do **not** hard-code a
template per use case; compose from reusable archetypes. (Reminder G-reality: this is a file merge in
the authoring project, not runtime overlay resolution.)

The kit must also be **good at exposing missing context** — it should be able to say *"this pack
cannot be completed: country net-price rights, evidence-recency rules, and independent eval cases are
missing,"* and record for every artefact: who supplied it · which source supports it · extracted /
SME-authored / AI-inferred · confidence + open questions · applicability · reviewer/approval status ·
schema+pack version.

### 4d. Source ingestion

Upload/reference → **register + classify** (owner, rights, dates, confidentiality, checksum, scope,
permitted-use, PII, client boundary) → **extract passages + candidate claims** → **map to artefacts**
→ **targeted SME questions** → **SME confirms/corrects/contests** → **governed candidate deltas** →
validate + refresh explorer. Everything from a document is a **candidate** until confirmed. Decks
should be rendered to PDF/slide-images when visual charts carry meaning (text-only extraction misses
them).

### 4e. The authoring engine — four loops + a Question Compiler

One skill, four loops (the SME experience, not one long interview):
1. **Discover** (new pack, little doc) — open questions → use-case brief, glossary, decision map,
   ontology candidates, source requests, open-question register.
2. **Teach through scenarios** — the SME works realistic situations; answers update ontology, method,
   rules, and eval cases simultaneously.
3. **Challenge** — the agent is an adversarial colleague (what disproves this? when has it failed?
   which relationship is not causal? when must the agent refuse?). *This is where the tacit IP is.*
4. **Ratify** (content exists) — Forge missions: **Ratify · It-depends · Adjudicate · Order-the-
   cascade · Spot-the-flaw · Teach-back.**

A small **Question Compiler** examines the evolving pack and picks the next highest-value question
(undefined concept → definition; two metric defs → which applies; rule without exception → when does
it fail; unsupported assertion → what evidence; conflicting answers → which wins). This makes the
session adaptive and finite.

**Forge rule (keep):** every meaningful interaction produces a proposed artefact change, an eval
case, a confidence statement, or an explicit documented gap — *and a significant rule contribution
normally produces both a pack delta and an eval delta* (rule + positive case + exception case).

**Domain Decision Records** capture *why* a definition/rule was chosen (question, decision,
alternatives, conditions, exceptions, rationale, evidence, approver, status). These are high-value
when a second SME/overlay/agent later meets the pack.

**MCQs** are allowed for terminology/classification/ranking, but every MCQ carries *It depends · None
of these · I don't know · a rationale field · propose-a-new-answer* — else the kit manufactures false
certainty.

### 4f. The visual explorer (comprehension surface)

Generated from a normalized `context-model.json` after each checkpoint; **disposable** (G6). Views:
decision map · **ontology graph** (nodes colored by status: grey=AI-suggested, amber=source-supported,
green=SME-confirmed, red=conflict/incomplete, purple=inherited governed concept) · **metrics explorer**
(definition + lineage + conflicts) · evidence/source map (claim → source → permission/freshness) ·
**readiness** (per-area % derived from explicit requirements, each linking to the underlying gaps —
not an arbitrary score) · change/provenance (what was added/changed/challenged this session).
**v0 = regenerate a self-contained `explorer.html` after each checkpoint** (opens locally, no server,
works in a secure client env). v1 = live local refresh. v2 = in-platform collaborative review.

### 4g. The evaluation module (mandatory — the experiment's scoring apparatus)

Split by location: **authoring workflow** (in the kit) · **domain eval definitions** (in the pack) ·
**held-out cases** (in a separate protected vault) · **runner/validators** (kit tooling) · **results/
receipts** (reports) · **production monitoring** (later, platform). The kit generates and curates
candidates; it must **not** have unrestricted access to the final held-out benchmark (G4).

**Three layers:** (1) **pack integrity** — deterministic, no agent (ids, formula inputs/units/grain,
references resolve, applicability set, evidence permitted, no silent rule contradiction, high-risk
rules have exceptions+owners, every decision has eval coverage). (2) **domain decision quality** —
cases: normal · boundary · exception · conflicting-evidence · missing-info · stale-info ·
inappropriate-automation · required-abstention · tool/data failure · adversarial. (3) **implemented-
agent performance** — end-to-end after an agent exists (right context retrieved? right tools? correct
calc? cited? respected human boundary? abstained? beat baseline?). The kit fully designs 1–2 and
**prepares the contract** for 3.

**Strategy is built, not random:** decision contract → **failure taxonomy** (domain IP: how experts
know an answer goes wrong) → **coverage matrix** (decision × market × lifecycle × evidence-condition ×
exception × risk × expected behaviour) → scenarios + expected *behaviours* (required/prohibited, not
one exact paragraph) → rubrics + deterministic checks → **development / regression / held-out /
challenge** suites. "Ready" = important matrix cells covered, not case count.

**Case essentials:** id · decision · applicability (markets/stage/effective-date) · scenario (incl.
`deliberately_missing`) · `required_behaviours` · `prohibited_behaviours` · `required_context` ·
`evidence_expectations` · weighted `scoring` (decision-quality/method/evidence/uncertainty/human-
boundary) · `critical_failures` (reported separately, never averaged in) · provenance · `status:
candidate`.

**Scoring methods:** deterministic (formulas, dates, ids, citations, tool-call sequence, numeric
tolerance, prohibited-data-exposure) — strongest; SME-scored (judgment/synthesis) with a good/
acceptable/unsafe rubric; LLM-assisted (first-pass only, calibrated to SME, never sole authority on
high-risk); **pairwise** (agent-without-pack vs with-pack vs prior-version — often stronger than
absolute).

**Held-out discipline:** dev cases improve the pack; regression cases stop known failures returning;
**held-out cases are frozen and read-locked** — if the drafting agent can read the held-out answers,
they are regression tests, not held-out. Freeze the suite; re-run the changed pack against the same
frozen suite; version the suite only when the benchmark intentionally changes.

**Feeds agent development:** the pack exports a portable **evaluation contract**; agent devs write a
thin adapter (case → agent → answer+citations+tool-trace → deterministic checks + rubric →
**evaluation receipt**). Every run records pack/suite/agent/model/prompt/retrieval/tool/data versions +
retrieved-context ids + tool calls + output + scores + critical failures. Without this trace, teams
blame the model for every failure.

**Prove pack value (= the experiment):** paired A (no pack) / B (with pack) / C (ablated), holding
model/prompt/tools/data/cases constant; measure task success · critical-error rate · evidence
accuracy · correct abstention · citation traceability · method adherence · human-boundary compliance
· cost/latency. A pilot shows feasibility; robustness comes from independent cases + risk-weighted
coverage + realistic data + frozen comparisons, **not case count** — and no generic "15% better"
claim beyond what the independent results + uncertainty support.

**Why the eval set is IP:** an ontology says what experts know; the eval suite captures how they
recognise a *good* decision, the failure modes, the dangerous mistakes, and when the answer is "do
not decide." It is measurable proof of value, an implementation spec for agent devs, regression
protection across model/prompt changes, portability across vendors, and a commercial benchmark. Ship
some dev cases with a client pack; retain the larger benchmark as OntoWiz IP.

### 4h. UI surface + session state

**The chat is the interaction surface; the project directory is the durable source of truth.** The
SME does **not** need Claude Code CLI. v0 = a **desktop, folder-aware agent** (Codex/ChatGPT desktop
primary; Claude Desktop/Cowork equivalent adapter) opening a local workspace: conversation + current
question/proposed-change + a regenerating explorer. CLI is for technical authors/CI only. Every SME
answer becomes a proposed delta (`extracted → proposed → SME-confirmed → independently-reviewed →
candidate → active`); on confirm, the kit updates the canonical file, validates, updates the receipt,
regenerates the explorer, checkpoints, and shows the diff. **Resume from `session-state.yaml`, not
model memory.** Multi-user merge/consensus is Forge/platform, not v0 (single SME + optional reviewer;
separate proposals, never direct canonical writes).

---

## 5. Locked decisions needed before build

The advisor's five, plus mine:
1. The exact **`ontowiz-spec` schema version** the kit targets (`vNext-min`) — and that the kit
   vendors it, not forks it.
2. The **first brand-analytics decision slice** (recommend NBRx-vs-plan variance — matches Experiment A).
3. The **first MR decision slice** (recommend barriers-to-initiation synthesis — matches Experiment B).
4. v0 output = **local candidate packages only** (recommend yes; do **not** make Forge or the platform
   a prerequisite).
5. **Approval + sensitive-source rules** for the initial tests (who confirms; what may be ingested).
6. (Mine) **Owner roles** for the pack (steward/brand/MR-methodologist/rights/approver) so G7 routing
   works.
7. (Mine) **Primary desktop surface** for v0 (Codex/ChatGPT desktop vs Claude Desktop) — pick one to
   build the adapter first.

---

## 6. Build first / not first

**Build (v0):** core skill + Codex adapter · use-case classifier + archetype scaffolder · Grill-with-
Docs discovery + scenario/challenge/ratify missions + Question Compiler + DDRs · ingestion → candidate
claims · candidate ontology/metric/evidence/method/policy/tool contracts (evidence-anchored, fail-
closed) · evaluation module (charter → taxonomy → matrix → cases → dev/regression + held-out freeze/
export + deterministic validators + rubrics + agent-adapter contract + receipt + baseline-vs-pack) ·
regenerated static explorer · candidate packaging + authoring receipt · **two worked slices (BA + MR)**.

**Not v0:** authoring UI beyond the generated explorer · agent-per-pack · marketplace · multi-client
deploy · automated approval · Forge reputation/leaderboards · universal graph DB · query engine ·
runtime multi-pack composition · calibrated LLM-judge · production monitoring.

---

## 7. Success / kill

**Validated if** Expert+Codex+Kit beats Expert+Codex+folder on provenance completeness · applicability
coverage · counterexamples/abstention · structural validity · change traceability · source-withdrawal
handling · second-brand reuse (weighted semantic artifacts, Rev 3 def) · SME experience/time — **without
degrading decision quality** (H2a). **Kill / keep-a-methodology if** a well-organized Codex+Git repo
performs almost as well.

---

## Appendix — sharp edges for the build team

1. **Schema drift is the #1 killer** — the kit's schemas *are* the platform's, pinned to one version.
2. **The kit's job is refusal, not generation** — if `validate` passes today's `0.1.0`, it's wrong.
3. **Auto-approval is already in the tree (`seed.py`)** — candidate by construction.
4. **The held-out firebreak must be code** — `freeze-heldout` + refuse-on-drift; drafting agent can't read it.
5. **The explorer is generated, never a source of truth.**
6. **"Composition" in v0 is a file merge, not runtime overlay resolution** (which the platform hasn't built).
7. **"Any SME" is wrong** — route questions to the right authority; record which.
8. **This is the experiment's tooling, not new scope** — the kit authors Arm 2/Arm 3; the eval module scores them.
9. **The eval set is likely the most defensible IP** — treat the failure taxonomy as a first-class product.

*Built this way, the Authoring Kit doubles as the forcing function for the minimal schema kernel, the
candidate/approval boundary, and decision-level evals — strengthening the OntoWiz spine exactly where
the validation plan already points, while producing the packs the experiment needs to test.*
