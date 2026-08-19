# Onto_Wiz — Hypothesis-Validation Plan

**Status:** **Direction ratified; experiment execution pending pre-registration approval.**
**Revision 3** (2026-07-25) — folds the pre-registration review's five material findings +
secondary changes into Revision 2. Mode: platform-building → **hypothesis-validation**.
**Lane:** BE · Mints no card IDs · Product/commercial decisions flagged as owner+INT calls.
**Gate:** no experiment arm is built until the **pre-registration addendum**
(`EXPERIMENT_PRE_REGISTRATION_2026-07.md`) is approved.

> **Team message (authoritative):** Onto_Wiz has moved from platform-building mode into
> **hypothesis-validation mode**. The only authorized product work is the minimum integrity,
> evidence, context-receipt and evaluation **spine** required to test **one structured** and
> **one unstructured** decision workflow against strong native and harness baselines. All
> broader platform capabilities are **parked** until those tests demonstrate domain lift,
> lifecycle value, reuse, and credible buyer demand.

---

## 0. What changed

- **Rev 2** flipped the doc from a delivery plan to a validation programme.
- **Rev 3** (this) resolves the pre-registration review: the three-way hypothesis split
  (§1), a hard time/scope ceiling on the spine (§6), the evaluation firebreak (§6b), the
  corrected shared-kernel failure condition (§4b), a single locked baseline (§2 + addendum),
  minimal MR privacy/source-rights kept **out** of the park list (§4, §7), and precise
  definitions of reuse / onboarding / critical-failure / the commercial gate.
- Nothing is authorized to execute as an experiment until the **pre-registration addendum** is
  approved; the minimal spine build remains gated on the **A1** review of S1.1/F0.10.

---

## 1. Hypotheses — three explicit tests (was ambiguous in Rev 2)

The Rev-2 "H2 = measurable lift **and/or** lifecycle value" allowed H1 and H2 to recombine.
Rev 3 splits them so each is decided independently:

| Test | Statement | Passes if |
|---|---|---|
| **H1 — Domain IP** | Your proprietary methodology improves the decision over commodity native tooling. | **Arm 2 materially outperforms Arm 1** on decision quality (hard cases), beyond the pre-set margin. |
| **H2a — Platform non-inferiority** | Onto_Wiz does not degrade decision quality relative to an *equally-informed* prompt implementation. | **Arm 3 is non-inferior to Arm 2** on decision quality (within a pre-registered non-inferiority margin). |
| **H2b — Platform lifecycle value** | Onto_Wiz measurably improves governance/maintenance/reuse. | **Arm 3 materially outperforms Arm 2** on the pre-defined **lifecycle outcomes** below. |

**Platform continuation = H1 ∧ H2a ∧ H2b ∧ commercial gate (§5b).**

**Principle:** Onto_Wiz **need not beat an equally-informed Arm 2 on answer accuracy** — its value
is governance and lifecycle. But it **must not materially degrade** accuracy (that is H2a).

**H2b lifecycle outcomes (measured, Arm 3 vs Arm 2):**
- Stale / withdrawn context served (rate).
- Time to propagate a change safely (label/market/data change → served).
- Reproducibility of an answer from its receipt.
- Cross-tenant / rights-policy violations.
- SME hours required for maintenance.
- Effort + time to bind a **second brand**.

---

## 2. Experiment design — three arms + expert ceiling, one **locked** baseline

Same data, same questions, same models, same source access, same compute budget; blinded scoring.

| Arm | Configuration | Measures |
|---|---|---|
| **Arm 1** | The **single locked** native platform, ordinary configuration | Commodity baseline |
| **Arm 2** | Native platform **+ the canonical methodology** in prompts/files | **H1** |
| **Arm 3** | Native platform **+ the Onto_Wiz spine**, deriving from the **same canonical methodology** | **H2a / H2b** |
| **Ceiling** | Human expert result (where practical) | Quality ceiling / headroom |

**Effects:** Arm 1→2 = **H1**. Arm 2→3 = **H2a** (quality non-inferiority) and **H2b** (lifecycle).

- **One canonical methodology source** (finding 3). Arm 2 and Arm 3 are **both derived from the
  same frozen methodology artifact** — this is the evidence that Onto_Wiz did not secretly receive
  better knowledge. Any divergence between Arm 2 and Arm 3 must be **governance/assembly/receipts/
  lifecycle only**, never content.
- **Fairness caveat (retained):** Arm 2 must be a *genuinely strong* prompt implementation of that
  methodology, or the test flatters Onto_Wiz.
- **The primary baseline is locked in pre-registration** (finding 5): one primary native platform,
  product + model versions, agent instructions, tool permissions, retrieval config, token/compute
  budgets, number of runs, evaluation period. Other platforms may be **secondary** comparisons —
  the team may not pick the baseline that most flatters Onto_Wiz after seeing results.

Pre-register hypotheses, datasets, rubric, and stop conditions **before** running (§addendum).

---

## 3. Experiment A — Brand Performance Investigator (structured, primary)

**Decision:** explain a material brand-performance variance, rank defensible hypotheses, identify
missing evidence, recommend the next analytical or commercial action. (Native NL→SQL can find NBRx
is 12% below plan; the proprietary layer decides whether it is meaningful, where it concentrates,
whether it resembles access vs awareness vs adoption vs execution failure, which hypotheses are ruled
out, what evidence is missing, which intervention to test, what would falsify it. *A decision product.*)

**Dataset:** an SME-authored gold set — hard cases, contradictory evidence, missing data, and
questions that **should be refused**. Target **75–100** as a *planning range*; final N is set by a
**pilot + power calculation** (§addendum).

**Metrics (pre-registered):** metric/cohort correctness · diagnostic correctness · unsupported
causal claims · appropriate uncertainty · evidence traceability · **critical-error rate** · SME
hours to build/maintain · **definition-update time (person-hours, fixed start/end)** · **second-brand
reuse** · runtime cost · commercial signal.

**Continue gates (thresholds finalized in pre-registration):**
- H1: ≥ **[pre-reg margin, planning ~15pts]** on hard decision cases, Arm 2 over Arm 1.
- H2a: Arm 3 within the **[pre-reg non-inferiority margin]** of Arm 2 on decision quality.
- H2b: Arm 3 materially better than Arm 2 on the §1 lifecycle outcomes.
- **Critical-failure threshold (finding, replaces "near-zero"):** an explicit maximum rate of
  high-impact unsupported recommendations, **reported separately from average quality** and treated
  as a hard fail if exceeded.
- **Reuse — defined:** "≥70% reused unchanged" = **weighted semantic-capability artifacts**
  (metric definitions, diagnostic rules, evidence bindings, applicability), **excluding client
  mappings and configuration**.
- **Onboarding — defined:** person-hours between fixed start/end events for a second implementation.
- **Two-runtime portability** is **staged after** the primary three-arm result (§8), not run in
  parallel — otherwise it doubles implementation scope prematurely.

**Stop/park gates:** native within the non-inferiority margin of Arm 3 *and* no lifecycle advantage ·
second implementation mostly bespoke · SMEs prefer maintaining the native semantic model directly ·
buyers pay for consulting but not the reusable capability · packs stay AI-generated assertions
without evidence/reviewers · receipts don't affect any real approval/audit/risk decision.

---

## 4. Experiment B — MR Evidence Synthesizer (unstructured, narrow probe)

**Purpose:** an **architecture probe**, not a second product build — it stops analytics assumptions
from defining the kernel.

**Decision:** across primary+secondary research, what are the leading barriers to initiation, what
evidence supports/contradicts each, how confidently can we generalize, and what research/commercial
action follows?

**Controlled corpus:** transcripts · discussion guides / study designs · reports & summaries ·
surveys · secondary publications / market reports · **conflicting studies** · **superseded evidence**
· **≥1 source that must later be withdrawn** · **sources with different usage/redistribution rights**.

**Required outputs:** ranked themes/hypotheses · **exact verbatims with stable source refs** ·
contradictions & minority views · study/market/audience/time applicability · sample & method limits ·
**observed-evidence vs agent-interpretation** · missing evidence · next research/commercial action ·
an **execution receipt** naming sources + context versions used.

**Minimal privacy & source-rights controls — part of the MR spine, NOT parked (secondary finding):**
consent · PII/PHI handling · permitted-use · quotation rights · retention · withdrawal. Full
enterprise IP governance stays parked (§7); these do not.

**Evaluation — stricter than RAG:** citation precision/recall · verbatim exactness · claim-entailed-
by-evidence · unsupported-synthesis rate · contradiction/dissent coverage · method-limit representation
· **refusal to generalize qualitative → statistical** · primary/secondary/inferred separation · PII &
rights compliance · appropriate abstention · expert usefulness.

**Critical failures (zero-tolerance, reported separately):** fabricated quotes · invented respondent
counts · "most HCPs believe…" without support · concealing contradictions · source used outside its
permitted purpose · interpretation presented as a research finding · **using claims after their source
is withdrawn**.

**Lifecycle test:** withdraw/supersede a study → dependent insights **identified, invalidated, and no
longer served** (where Onto_Wiz should beat a folder of prompts).

---

## 4b. The shared-kernel test — corrected failure condition (finding 4)

Analytics and MR need **different domain ontologies and adapters — that is expected and healthy.**
The generalization test is about the **control spine**, not the domain concepts.

| Shared control spine (must be one) | Domain adapter (may differ) |
|---|---|
| Governance kernel · lifecycle model · policy mechanism · context-envelope · release mechanism · receipt architecture · evaluation harness · invalidation | Metric vs study/source definitions · dataset vs transcript rights · grain vs fieldwork date · query vs verbatim binding |

- **Pass:** the same **control spine** supports both; only the domain ontology/adapters differ.
- **Fail (corrected):** MR requires a **second governance kernel, lifecycle model, policy mechanism,
  context envelope, release mechanism, or receipt architecture** — a duplicated control spine. A
  second domain *ontology* is **not** a failure.

---

## 5. The decision matrix

| H1 (domain IP improves decisions) | H2a ∧ H2b (platform: non-inferior **and** lifecycle value) | Decision |
|---|---|---|
| Yes | Yes | **Continue Onto_Wiz as a product platform** (+ §5b) |
| Yes | No | Sell **domain packs + native accelerators + consulting** (no platform) |
| No | (irrelevant) | **Stop the platform**; keep only as an internal consulting tool |
| Unclear | Unclear | **Do not expand**; improve the experiment & evidence |

### 5b. Commercial gate (defined — secondary finding)

Platform continuation additionally requires a real commercial signal: a named **economic buyer**, a
stated **problem**, an **indicative price**, **committed SME/data access**, and **paid-pilot or
signed design-partner** evidence. Absent this, at best "Yes/Yes" supports packs+consulting, not a
platform bet.

---

## 6. CONTINUE now — the minimum spine (only authorized product work) + a hard ceiling

**Spine work (gated on A1 for the S1.1/F0.10 parts):**
1. Finish **S1.1** (verify-before-load) and **F0.10** (serve-door) via A1.
2. **EOL-robust seal fix** — **canonicalize declared text formats** before hashing (normalize line
   endings for the pack's known text files); **do not indiscriminately normalize arbitrary file
   bytes** (finding, EOL). Correct `PROJECT_STATUS.md` known-debt (done — §10).
3. Mark existing commercial packs **`production_eligible:false`** (reseal under the canonicalized seal).
4. **Minimal contracts only:** source, evidence, applicability, **decision-level evaluation**, and
   **minimal MR privacy/source-rights** — just enough to run both experiments. No universal Skill
   type; a **lightweight task contract inside the experiments** is allowed.
5. **Build the two evaluation datasets** (analytics + MR). *The real critical path — SME time + a
   data/corpus environment, not manifests.*
6. **Minimal context assembly + execution receipts.**
7. **Candidate-pack load** (eval-gated, not `system:seed`-active).
8. Use AI grilling to draft artifacts; **SME review before draft → approved test material.**

**Hard ceiling on the spine (finding 2) — set in pre-registration:**
- A fixed **elapsed-time budget** (planning: **10–12 weeks** after data + SMEs are available).
- A **maximum engineering + SME effort** budget.
- A **design-freeze date**.
- **No generic abstraction is added unless required by *both* experiments.**
- A **named owner** empowered to reject scope additions.
- A **mandatory decision date** — the go/no-go happens even if results are incomplete.

> Without this ceiling, platform-building simply continues under the name "experiment infrastructure."

---

## 6b. Evaluation firebreak (finding 3)

- **Gold cases are frozen before any pack tuning.**
- **Pack authors cannot access held-out answers**; the **LLM used to draft pack content does not see
  the held-out set.**
- Responses are **randomized and stripped of arm identity** before scoring.
- **Multiple runs** per question (agent outputs are nondeterministic); report **confidence intervals**.
- **≥2 SMEs** score a meaningful subset; record **inter-rater agreement + adjudication**.
- **Sample size** from a **pilot + power calculation** (75–100 is a *planning range*, not the result).
- **Critical safety failures reported separately** from average quality scores.
- **One canonical methodology source** feeds both Arm 2 and Arm 3 (see §2).

---

## 7. PARK — conditional on the §5 decision; no implied commitment

General-purpose **Skills** type · **Solution-bundle** infra · complex **multi-pack composition** ·
**Forge reputation/consensus/leaderboards** (Forge *drafting* aid is allowed, §6.8) · **marketplace**
· **property-graph** expansion · **autonomous learning** · **supply-chain / R&D** packs · broad
**control-plane UI** · a proprietary **structured-query engine** · **full IP-governance release gate**
· **full MLR** (the third exam — only if both experiments pass, §8).

**Explicitly NOT parked** (moved into the spine): **minimal privacy + source-rights** for MR
(consent/PII/permitted-use/quotation-rights/retention/withdrawal). The Rev-1 platform material
(layered model, IP release gate, Forge service, EM overlay, multi-loop sequencing) is retained
**only as a reference to activate on a pass**.

---

## 8. Sequence

1. **Pre-registration addendum approved** (hard gate before any experiment code).
2. Complete the minimal integrity spine (S1.1/F0.10, on A1).
3. Run **Experiment A** (primary, single locked baseline).
4. Reuse the same **control spine** for **Experiment B** (MR).
5. **Lifecycle tests:** change, withdrawal, client overlay, reproducibility, cross-tenant isolation.
6. **Two-runtime portability** test (staged *after* the primary three-arm).
7. Independent expert scoring + commercial buyer feedback.
8. **Fixed go/no-go meeting** (mandatory date) → §5 decision.
9. Only if both pass → Exam 3: deterministic MLR policy enforcement.

---

## 9. Re-scoped decisions (Rev-1 D1–D7)

| Rev-1 decision | Status |
|---|---|
| D1 EM lens · D2 Skills scope · D3 Forge consensus · D5 IP release gate | **PARKED-conditional** |
| D4 mark `0.1.0` fixtures | **ACTIVE** (§6.3, on the canonicalized seal) |
| D6 status-integrity fix | **ACTIVE — done for the status line (§10); EOL seal fix pending A1** |
| D7 "analytics leads" | **SUPERSEDED** by this validation programme |

**New gate:** experiment execution requires **pre-registration approval** + the four owner inputs
(primary native platform; SME scorers + target brand; data/corpus env; commercial-gate/buyer status).

---

## 10. Retained do-now hygiene

- **Report corrections** to `ENTERPRISE_CONTEXT_LAYER_ARCHITECTURE_2026-07.html`: byte-for-byte →
  deterministic derivation; drop "structural" for in-context guardrails; averaged confidence →
  multi-axis trust; keep ontology / KG / property-graph / graph-DB distinct.
- **Status-integrity fix — applied this revision:** `PROJECT_STATUS.md` known-debt entry corrected —
  the reseal "red" is an **EOL artifact** (passes on the CRLF main tree at HEAD `5ebbda3`;
  `verify_pack(0.1.0)` True), not a stale fixture; the fix is a **canonicalized (declared-text-format)
  seal**, not a reseal/waiver.
- **`0.1.0` disposition:** `production_eligible:false`; `signed` = integrity seal, not authorship.

---

## 11. Grounding citations

- **Forge:** `ontowiz-factory/{missions.py,forge.py,steward.py}` (missions.py:95,120-136; forge.py:74-116);
  `bridge.py:61-75,111-124`; `docs/reviews/FORGE_MODULE_DESIGN_2026-07.md`;
  `docs/specs/SME_GRILL_ME_CURATOR_BUILD_INSTRUCTION_SET_2026-07.md`.
- **Pack + status:** `packs/commercial_analytics/{0.1.0,0.2.0,0.3.0}/pack.yaml`, `artifacts/rule_*.yaml`;
  `seed.py:96-108,168-193`; `library.py:324-335`; `evals.py:43-61`; `compiler.py:156-202`;
  `test_benchmark.py:136-149`; `PROJECT_STATUS.md:151,310`.
- **Layering substrate:** `pack_manifest.py:19-49`; `registry.py:34-78`; `context.py:64-240`;
  `benchmark.py:44-60`; `roles.py:15-20`; `examples/reference_domain_packs/auravia_marketing/0.1.0/`.
- **Backlog & rules:** `DELIVERY_LOOPS_BACKLOG_2026-07.md`; `DELIVERY_PROTOCOL.md:96-101`;
  `VDP_GAP_CLOSURE_LOOPS_2026-07.md:1-16`.
- **Pre-registration contents:** `docs/specs/EXPERIMENT_PRE_REGISTRATION_2026-07.md`.

---

*This document is a validation programme. Direction is ratified; **experiment execution is gated on
approval of the pre-registration addendum** and the minimal spine build is gated on the A1 review.*
