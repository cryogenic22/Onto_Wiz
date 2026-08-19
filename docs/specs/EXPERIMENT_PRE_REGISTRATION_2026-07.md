# Onto_Wiz — Experiment Pre-Registration Addendum

**Status:** DRAFT — requires **owner approval** to freeze. Once approved and frozen, **no field
below may change after any arm has been run**; changes require a new versioned pre-registration.
**Gates:** governs `ENTERPRISE_MATURITY_CONSOLIDATION_2026-07.md` (Rev 3). Experiment execution is
**not authorized** until this is approved. Covers **Experiment A (primary)**; Experiment B (MR) has
its own frozen section (§B) filled before B begins.
**Date:** 2026-07-25 · **Fields marked `[OWNER]` are product/commercial decisions, not builder calls.**

---

## 1. Frozen primary baseline (finding 5)

| Field | Value |
|---|---|
| Primary native platform | `[OWNER]` — **one** of: Snowflake Cortex Analyst/Agents · Databricks Genie |
| Product + model versions | `[OWNER]` — exact platform build + LLM model IDs/versions for **all** arms |
| Agent instructions | `[frozen text, identical harness across arms except the methodology/spine variable]` |
| Tool permissions | `[frozen — same tools/scopes across arms]` |
| Retrieval configuration | `[frozen — semantic model / index config for Arm 1; same native retrieval available to all]` |
| Token + compute budget per question | `[frozen — equal across arms]` |
| Number of runs per question | `[frozen — see §5; planning: ≥5]` |
| Evaluation period (window) | `[OWNER — fixed dates]` |

Secondary platforms may be compared **after** the primary result is locked; they cannot replace the
primary baseline retroactively.

---

## 2. Canonical methodology source (finding 3)

- A **single frozen methodology artifact** (the domain IP: metric definitions, diagnostic logic,
  evidence bindings, applicability, causal-restraint rules) is authored and **SME-approved before
  freeze**.
- **Arm 2** = that methodology rendered into prompts/files. **Arm 3** = that **same** methodology
  compiled into an Onto_Wiz pack. Both derive from the identical source; the **only** permitted
  difference is governance/assembly/receipts/lifecycle.
- Fairness check: an independent reviewer confirms Arm 2 and Arm 3 carry the **same knowledge** before
  any run (evidence that Onto_Wiz did not receive better content).

---

## 3. Dataset split + evaluation firebreak (finding 3)

- **Gold set frozen before any pack tuning.** Authored by SMEs; split into a **tuning/dev** set and a
  **held-out** set.
- **Held-out is sealed:** pack authors and the drafting LLM **never see held-out answers**.
- **Blinding:** responses randomized, **arm identity stripped** before scoring.
- Sample size: **[pilot + power calculation]**; **75–100 is a planning range**, not the frozen N.
- Composition: includes hard cases, contradictory evidence, missing data, and **should-refuse**
  questions (with the correct action = refuse/abstain).

---

## 4. Hypothesis thresholds (finding 1)

| Test | Metric | Threshold (`[OWNER/SME to set]`) |
|---|---|---|
| **H1** | Arm 2 − Arm 1, decision quality on hard cases | ≥ `[planning ~15pts]` |
| **H2a** | Arm 3 vs Arm 2, decision quality | within non-inferiority margin `[δ]` |
| **H2b** | Arm 3 vs Arm 2, lifecycle outcomes (§6) | material improvement on `[named outcomes]` |
| **Commercial (§5b of Rev 3)** | buyer/price/access/pilot | `[OWNER — see §8]` |

**Continue = H1 ∧ H2a ∧ H2b ∧ commercial.** Any one failing → the corresponding §5 decision-matrix row.

---

## 5. Statistical + repeated-run protocol (finding 3)

- **N runs per question** (`[≥5]`) to account for nondeterminism; report **means + confidence intervals**.
- **≥2 SMEs** score a meaningful subset; report **inter-rater agreement**; a named **adjudicator**
  resolves disagreements.
- Pre-registered scoring rubric per metric (correctness, diagnostic, unsupported-causal, uncertainty,
  traceability, abstention).
- **Power calculation** fixes N before freeze.

---

## 6. Critical-failure policy (finding, replaces "near-zero")

- **Critical failures reported separately from average quality** and never averaged in.
- **Analytics critical failures:** invented metric/join/definition · numeric answer with no query
  receipt · unsupported high-impact causal recommendation · wrong-market answer.
- **Hard-fail threshold:** `[explicit max rate — planning: 0 tolerated on the top severity class]`.
- **H2b lifecycle outcomes (Arm 3 vs Arm 2):** stale/withdrawn-served rate · safe-change-propagation
  time · receipt reproducibility · cross-tenant/rights violations · SME maintenance hours ·
  second-brand binding effort.

---

## 7. Time, cost, scope ceilings (finding 2)

| Ceiling | Value |
|---|---|
| Elapsed-time budget | `[OWNER]` — planning **10–12 weeks after data + SMEs available** |
| Max engineering effort | `[OWNER]` |
| Max SME effort | `[OWNER]` |
| Design-freeze date | `[OWNER]` |
| Scope rule | **No generic abstraction unless required by BOTH experiments** |
| Scope owner | `[OWNER — named person who can reject additions]` |
| Mandatory decision date | `[OWNER]` — go/no-go happens even if results are incomplete |

---

## 8. Named roles + commercial gate

| Role | Person |
|---|---|
| SME scorers (≥2) | `[OWNER]` |
| Adjudicator | `[OWNER]` |
| Decision owner (go/no-go) | `[OWNER]` |
| Scope owner | `[OWNER]` |

**Commercial gate evidence (Rev 3 §5b):** economic buyer `[OWNER]` · problem `[OWNER]` · indicative
price `[OWNER]` · committed SME/data access `[OWNER]` · paid-pilot or signed design-partner `[OWNER]`.

---

## 9. Minimal MR privacy / source-rights controls (secondary finding) — frozen before Experiment B

Consent · PII/PHI handling · permitted-use · quotation rights · retention · withdrawal. Enforced in
the MR spine (not parked). Corpus must include ≥1 withdrawable source and rights-varied sources.

---

## §B. Experiment B (MR) — frozen section (completed before B begins)

Baseline, corpus manifest (incl. the withdrawable source + rights variation), gold synthesis cases,
citation/verbatim scoring rubric, the withdrawal-lifecycle test spec, and the **same control-spine**
assertion (§4b of Rev 3). Staged **after** the Experiment-A result.

---

## 10. Fixed go/no-go meeting

**Date:** `[OWNER]`. Attendees: decision owner, scope owner, ≥2 SME scorers/adjudicator, BE/Core/FE
leads. Inputs: A results (H1/H2a/H2b + critical-failure), commercial-gate evidence, ceiling status.
Output: the §5 decision-matrix outcome, recorded.

---

*Approve this addendum (fill every `[OWNER]` field and freeze the thresholds) to authorize experiment
execution. Until then, only the minimal spine (Rev 3 §6, gated on A1) is authorized.*
