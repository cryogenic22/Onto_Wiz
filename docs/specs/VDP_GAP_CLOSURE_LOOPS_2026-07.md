# VDP Gap-Closure Loops — 2026-07 (v2, PROPOSED)

**v2 supersedes v1 (same day).** v1 was drafted against the Step 0–10 crosswalk but **without
reconciling `DELIVERY_LOOPS_BACKLOG_2026-07.md` v2.0** (the F0.x/E-x/D-x card set, Gates
G0–G4, Loops 0–8), the B0–B12 discovery units, GM0–GM7, or control-plane Slices A–J. That
produced duplicate cards. v2 retires every v1 ID that duplicated an existing card (§1) and
re-expresses the plan **using the existing card inventory**. Net new cards: **five small ones**
(A1, A2, F0.10, SCALE-1, DOC-1) plus a proposed unit split for Steps 6–7 (V-series), each
declared for ratification.

**Authority chain.** `ONTOWIZ_VALIDATED_DOMAIN_PACK_BLUEPRINT_2026-07.html` (architecture
baseline, 2026-07-21) → `PLATFORM_READINESS_AUDIT_2026-07.html` (archived evidence snapshot)
→ `DELIVERY_LOOPS_BACKLOG_2026-07.md` v2.0 (card inventory, gates, loops — **the backlog of
record**) → `DOMAIN_PACK_PLATFORM_BUILD_INSTRUCTION_SET_2026-07.md` Steps 0–10 +
`PLATFORM_BASELINE_STRUCTURE_2026-07.md` §6 crosswalk → B0–B12 / GM0–GM7 / Slices A–J
instruction sets. **No renumbering; no parallel paths.**

**Two status vocabularies, different axes (both kept):**
- *Unit workflow* (backlog §0A): `PLANNED / READY / IN PROGRESS / READY FOR REVIEW /
  CHANGES REQUIRED / VERIFIED / BLOCKED` — who-may-set rules apply.
- *Capability truth* (VDP §02): `VERIFIED / SUBMITTED / SPECIFIED / DESIGN-FIXTURE / MISSING`
  — for capability rows in status docs. A2 records this distinction in the ledger.

---

## 0. Operating rules (unchanged from the standing discipline)

1. One unit at a time: `mini-spec → reuse-first → TDD red → build → gates → §6 bundle →
   immutable review SHA on build/<unit-id> → HOLD`; only INT sets `VERIFIED` (v2 contract §0A).
2. The red test is named in the mini-spec before implementation.
3. Unit cap ≤ 1 person-week; split before speccing, never during.
4. Review throughput: 48h REV SLA; S1.2 + S1.3 pre-authorized as a batch; the review-bundle
   cut is scripted. (Observed: repo idle 8 days post 07-12 while implementation-ready specs
   waited.)
5. Evidence lands in `docs/PROJECT_STATUS.md` per unit; backlog standing rules hold (demo on
   the live URL or it didn't happen; loop boundaries are the only scope-change point).

---

## 1. Reconciliation — v1 IDs retired into existing cards

| v1 ID (retired) | Existing card(s) that own the scope | Note |
|---|---|---|
| S1.5 release-gate binding | **F0.6A** (candidate build ≠ publish; registry rejects failed/unrun gates) + **F0.6B** (held-out suite, leakage checks, reproducible lift receipt, `0.4.0` decision) | Add dependency note: F0.6A consumes S1.3's external receipt. B1 finishes runtime enforcement. |
| C1 legality matrix + schema_version | **F0.2H** ("lifecycle preconditions, idempotent decisions, version checks") + **B0/S2.1** (schema versions, migration decisions, can-fail contract tests) | Transition legality = F0.2H's precondition scope; `schema_version` = kernel contract work. |
| C3 pilot serve profile | **F0.8A** (live deployment, health/readiness, secrets, backup/restore) | Propose as explicit scope lines in F0.8A's mini-spec: disable `X-OntoWiz-Role` fallback under the profile; required `ONTOWIZ_JWT_SECRET`; server-side usage recording at `/v1/context`. |
| E1 LLM extraction lane | **E1.1** (managed sources/chunks, hashes, run ledger) + **E1.2** (layer-classified extraction, exact span, model/prompt version, paired eval) (+ **B4** target state) | v1's reuse pointers stand: `PatternExtractor` prompts/dedup, `RobustParser`, parser stack. |
| E2 consolidation pass | **E3.1-be** (conflict detector: shared tags/adjacent priority, dry-run, lineage) near-term; **B6** (reconciliation & coverage engine: dedup, merge/split/link with human confirmation, conflict ledger) target state | The "consolidation" mandate maps here — nothing new needed, it was already planned. |
| R1 minimal resolver | **E4-be** (pack composer: node+layer selection → manifest, version diff, gated publish) + Step-5 compiler v2 | Compile-time-resolution ADR still wanted (VDP decision); it governs E4-be's design. |
| H1 ctx harness gating | **F0.9** (keep product-used CTX only; ≥85% shipped-code coverage; remove checked-in build copies) | Exact duplicate. |
| G3-probe scale probe | renamed **SCALE-1** | v1 ID collided with backlog **Gate G3** (Semantic Quality). |
| F0.3 (coarse) | **F0.3A → F0.3B → F0.3C → F0.3D** as already split in Loop 1 | Write-model ADR (GovernanceStore = system of record; approvals need authenticated principals) rides F0.3B/C — consistent with the banked decision that the write-model moves via the DB outbox at F0.3. |
| C2 (partial) | Tag.parent/hierarchy → **F0.7A**; coverage/freshness → **B6**; eval summary → **S1.3** | Remainder (serve-door safety) merges with v1's S1.4 into **F0.10** below. |

**Surviving new cards (for ratification):**

- **A1 / A2** — process + docs actions (no code), defined in §3.
- **F0.10 (NEW · serve-door contract parity · M)** — merges v1's S1.4 + the un-owned rest of
  C2. One theme: *the serve door honors its own contract.* Scope: (a) register a
  governance-gated hydrate tool on the ontowiz-serve MCP door (the served prompt instructs
  `ctx/hydrate`, which the door never registers; the raw file-path hydrate server bypasses the
  gate); (b) typed error on unknown-section hydrate (today: silent empty success); (c) enforce
  `ALWAYS_INCLUDED_KINDS` in the runtime gate (declared safety carve-out has zero non-test
  consumers — an untagged Guardrail is silently dropped); (d) MCP `context/get` gains
  `backing_deltas` parity with REST. *Red seeds:* e2e directory→hydrate→answer through the
  serve door (promoted to a blocking gate); hydrate of a gated-out section → typed refusal;
  untagged Guardrail present in a tag-filtered directory. *Reuse:* `hydration_protocol`,
  `_restrict_doc`, `mcp.dispatch` error boundary.
- **SCALE-1 (NEW · S · parallel-safe)** — compile 100/500/1000-artifact synthetic packs;
  measure L3 directory growth, retrieval quality, real-tokenizer (BPE) counts vs whitespace
  estimates; publish break points. Informs F0.9 scope and Step-8 design; owns no product code.
- **DOC-1 (NEW · S)** — first adopter-facing quickstart (deploy serve → point an agent at
  REST/MCP → interpret the TrustEnvelope) + document the seed-YAML format as the v1 authoring
  interface. *Falsifiable exit:* someone outside the build lane stands the system up from the
  doc alone. (Backlog has consume-tab UI in Loop 5 but no adopter-doc card.)
- **V-series (NEW · proposed unit split for Steps 6–7, ratify at Step-6 spec time):**
  V1a MLR profile kinds → V1b MLR synthetic US-HCP slice (VDP §07 DoD, ≥20 can-fail cases,
  no-approval invariant) · V2a analytics kinds → V2b NBRx-vs-plan slice (VDP §09 DoD, causal
  restraint) · V3 MR study slice (VDP §08 DoD; **after** E-wave — it is the consolidation
  stress test; note `ontology/domains/research.yaml` is R&D research, not MR semantics) ·
  V4 Auravia-executable conformance harness (Step 7). Cross-refs: B5 (semantic kernel),
  B10 (evaluation framework). **Pre-req flag (G16):** claims tables/metric formulas cannot
  survive the one-line BODY flattening — V-units land after the Step-5 compiler-v2 slice
  lifts the ceiling, or their mini-specs must first prove the k=v BODY renders their kinds
  acceptably (compile one, read the served output).

---

## 2. Gap register (19 verified gaps → owning cards, final)

| # | Gap (evidence in v1/audit, all file:line-verified) | Owning card(s) |
|---|---|---|
| G1 | S1.1 submitted, unreviewed (`build/S1.1` @ `4eead82`) | **A1** |
| G2 | Status-language drift; protocol doc lists demoted gates as blocking | **A2** |
| G3 | Glob load, no verify-before-load (`registry.py:43,60`) | **S1.2** |
| G4 | Eval mutates + reseals candidate (`benchmark.py:221–239`) | **S1.3** |
| G5 | Hydrate tool instructed but not served; silent no-op; raw-path bypass | **F0.10** |
| G6 | Latest pack `gate_passed:false`; no pack-eval CI gate | **F0.6A/F0.6B** |
| G7 | 3 governance write models; unauthenticated approver; store endpointless | **F0.3B/F0.3C** (+ADR) |
| G8 | No transition legality; no schema_version | **F0.2H** + **B0/S2.1** |
| G9 | ALWAYS_INCLUDED unenforced; MCP envelope parity; dead schema | **F0.10** (+F0.7A, B6, S1.3) |
| G10 | Pilot-unsafe serve defaults | **F0.8A** (scope addition) |
| G11 | No kernel contracts/registry snapshots/migrations | **S2.1/S2.2** (=B0 seed) |
| G12 | No document→candidate path; extraction placeholder; dead LLM code | **F0.4A v3/F0.4B** + **E1.1/E1.2** |
| G13 | No live consolidation (dedup/contradiction/conflict) | **E3.1-be** → **B6** |
| G14 | Durable-governance hardening incomplete | **F0.2H** |
| G15 | No MLR/analytics/MR kinds; Auravia non-compilable | **V1–V4** (Step 6–7 split) |
| G16 | BODY-flattening format ceiling | Step-5 compiler v2 (pre-req flag on V-series) |
| G17 | Composition dead schema; n=1 pack population | **E4-be** + Step-5 resolver (+ADR) |
| G18 | Scale/token truth unknown | **SCALE-1** |
| G19 | 12.9k-line ctx engine outside all gates; e2e loop not falsifiable | **F0.9** (+F0.10's blocking e2e) |

---

## 3. The plan — existing loops, with the pivot's Step-1 wave slotted in front

**Phase 0 (immediately, no code):**
- **A1 (NEW · process · XS)** — INT/REV review of S1.1 at `4eead82`; merge or return findings.
  Carries: the garbled reviewer finding #3 (obtain clean re-send; do not guess), and the
  pre-existing verify-audit red `test_write_results_reseals_signed_pack` (stale fixture seal,
  fails at baseline `1dc26ca` — needs INT disposition: reseal / regenerate under Step 10 /
  explicit waiver). Institute 48h SLA + S1.2/S1.3 batch pre-auth; script the bundle cut.
  **Everything queues behind this.**
- **A2 (NEW · docs · XS)** — Ledger truth pass: 5-word capability vocabulary + per-capability
  table in `PROJECT_STATUS.md`; record the two-vocabulary rule; fix `DELIVERY_PROTOCOL.md`
  drift (PRS ≥ 85 listed as blocking; R3 made it advisory); mark the 07-20 audit archived.

**Phase 1 — Step-1 trust spine (before Loop-1 features, per the banked sequencing decision):**
`S1.2 → S1.3` (existing mini-specs at `801a35f`; S1.2 reuses S1.1's `verify_candidate_dir`;
S1.3 supplies the external receipt the catalog needs post-amend-2) · **F0.10** (independent of
S1.3; can interleave).

**Phase 2 — backlog Loops 1–2 as already written, now unblocked:**
- Loop 1 (gate **G0**): F0.2H → F0.3A → F0.3B → F0.3C → F0.3D · F0.7A · F0.8A (with the
  pilot-profile scope lines) · F0.5. Write-model ADR lands with F0.3B/C. FE: D1.2, Slice B.
- Loop 2 (gate **G1**): F0.4A v3 (post-Step-2-contracts flip per crosswalk) / F0.4B ·
  E1.1 · E1.2 (reuse pointers from §1) · F0.6A · F0.6B · F0.9. FE: E1.3, Slice C/E.
- **DOC-1** and **SCALE-1** schedule freely inside Phase 2 (parallel-safe).

**Phase 3 — kernel + curation depth (Loops 3–4 / Steps 2, 6-seed):**
S2.1/S2.2 (=B0 execution) · E3.1-be (the consolidation v1 the mandate asks for) · GM-series
enters only here (Forge v0 = E2.1A–D, gate **G2** pilot rules apply — k=1 endorsed-never-
ratified, no leaderboards before probes).

**Phase 4 — verticals + composition (Loop 5 / Steps 5–7, gate **G3**):**
Step-5 compiler-v2 slice (lifts G16) → V1a/V1b · V2a/V2b → E4-be (composition ADR:
compile-time resolution; serve-time merging rejected) → V4 · V3 (after E-wave) → gate **G4**
(attested release consumed by a real monitored agent) → Step-10 second-consumer gate.

---

## 4. Milestones ↔ gates (one frame, not two)

The backlog's Gates G0–G4 are the milestone frame of record; the audit's M1–M4 map onto them:

| Audit milestone | Backlog frame | Content |
|---|---|---|
| M1 Trustworthy serve | pre-G0 hardening | A1, A2, S1.2, S1.3, F0.10 (~3 unit-weeks) |
| M2 Pilot consumption | G0 (Loop 1) | F0.2H, F0.3A–D, F0.7A, F0.8A(+profile), F0.5, DOC-1, Slice B (~4 uw) |
| M3 Governed authoring | G1 (Loop 2) | F0.4A/B, E1.1/E1.2, F0.6A/B, F0.9, SCALE-1 (~4 uw) |
| M4 Second pack / platform | G2→G4 (Loops 3–5) | S2.x, E3.1-be, GM v0, compiler v2, V-series, E4-be, Step 10 |

Single-builder BE lane; FE lane (D-series, Slices) and SCALE-1/DOC-1 run parallel. With a
second BE builder, Loop-2 intake units can start alongside late Loop-1 (disjoint packages
until E1.x meets F0.3C).

---

## 5. Explicit non-goals (unchanged from v1)

OCI/Sigstore/SLSA, SSO/SCIM (B12 last), vector retrieval before lexical+eligibility filters,
serve-time multi-pack merging (rejected), platform-side warehouse connectors (agent-side typed
fixtures until B11), compliance-grade MLR (Part 11/e-signature/PromoMats integration), live
client data (synthetic until source-owner/privacy/legal validation), production-throughput
mining. Named so absence is a decision, not an oversight.

---

*v2, 2026-07-21. Change from v1: full reconciliation against the backlog-of-record and the
B/GM/Slice instruction sets; 9 of 14 v1 NEW IDs retired into existing cards (§1). Acceptance
path: ratify §1's surviving new cards (A1, A2, F0.10, SCALE-1, DOC-1, V-series split), then
open A1.*
