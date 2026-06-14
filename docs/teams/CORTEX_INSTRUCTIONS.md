# Team CORTEX — "The Reasoning Brain" — Instruction Packet

> **Team Code:** `CTX`  |  **Ticket Prefix:** `CTX-NNN`
> Read this file FIRST at the start of every session.
> Then: `anti_slop.md` → `docs/BOARD.md` → `docs/Lead2Dev.md` → `docs/DECISION_LOG.md` → sprint files
> Protocol: `docs/AUTONOMOUS_AGENT_PROTOCOL.md`

---

## 1. Project Context

**Onto_Wiz** is an Agentic Semantic Readiness Platform. It captures expert judgment through a scenario-based game and converts it into a deployable knowledge layer for enterprise AI agents.

**The Pipeline:** `SME Game → ReasoningEvent → DeltaGenerator → Delta Queue → Approval → Graph Promotion → Intelligence Packet`

**Core Principle:** Everything is a proposal (Delta Model). Experts play 5-minute scenario games. The system extracts ~10 semantic deltas per session. Deltas are reviewed before becoming active patterns, guardrails, and graph edges. AI agents then traverse this graph to answer business questions safely.

**What Gets Deployed:** A "Semantic Readiness Package" — ontology slices, judgment patterns, guardrails, and evidence mappings.

---

## 2. Your Mission

You own the **judgment layer** — the brain of the system. Your code determines how the system reasons, scores confidence, matches patterns, enforces guardrails, and generates intelligence packets.

**Your tickets (CTX-NNN) map to:**
- **EPIC-002:** Delta Model & Governance (US-024 to US-026)
- **EPIC-003:** Governance & Compliance Layer (US-030 to US-036)
- **EPIC-004:** Bounded Agent Traversal (US-040 to US-046)
- Phase 2.1 P0: Pattern Matching v2 (CTX-001), Guardrail Evaluation v2 (CTX-002)

**Product management docs:** `product_management/epics/`, `product_management/designs/`, `product_management/specs/`

---

## 3. File Ownership

**You own (exclusive write access):**
```
src/core/models.py          — Domain models, enums, dataclasses (529 lines)
src/core/stores.py          — DeltaStore, JudgmentStore, PromotionPipeline
src/core/graph_store.py     — GraphStore: nodes, edges, traversal
src/core/evidence.py        — EvidenceItem, EvidenceStore
src/core/confidence.py      — ConfidenceEngine: weighted multi-factor scoring
src/core/reasoning_event.py — ReasoningEvent, BrandProfile, SME response models
src/core/delta_generator.py — Converts ReasoningEvents into Deltas
src/core/semantic_store.py  — CanonicalTerm, SemanticRelation, synonym resolution
src/core/__init__.py        — Public API exports
src/reasoning/engine.py     — ReasoningEngine: main reasoning pipeline
src/ingestion/pipeline.py   — Multi-modal evidence ingestion (skeleton)
ontology/commercial.yaml    — Commercial pharma ontology definitions
ontology/synthetic_data/    — Test/demo synthetic data ONLY
tests/test_core.py          — Core model and store tests (489 lines, 32 tests)
tests/test_graph_evidence.py — Graph and evidence tests (327 lines, 22 tests)
tests/test_reasoning.py     — Reasoning engine tests (56 lines, 3 tests)
tests/gold_set/             — Gold-set regression framework
```

**You do NOT touch:**
```
src/api/**          — Owned by Team LENS
frontend/**         — Owned by Team LENS
tests/test_api.py   — Owned by Team LENS
docs/**             — Owned by Tech Lead
```

---

## 4. Current State of Your Files

### What Works (57 tests passing)
- **Delta lifecycle:** PROPOSED → APPROVED/REJECTED → MERGED. Auto-approval for LOW blast + high confidence.
- **JudgmentPattern:** Creation, activation, staleness decay, signal matching. Scoped by geography/lifecycle/brand/indication.
- **Guardrail:** `is_violated()` checks action type, evidence presence, persona exclusion.
- **TraversalPolicy:** Hard stops on low confidence, missing evidence, conflicting drivers, guardrail violations.
- **ConfidenceEngine:** 5-factor weighted computation (base prior 30%, evidence 25%, corroboration 15%, conflict 15%, freshness 15%).
- **GraphStore:** Node/edge CRUD, neighbor lookup, path finding, subgraph extraction, ontology seeding.
- **EvidenceStore:** Items with reliability weighting, dedup by hash, permission-filtered access.
- **SemanticStore:** Canonical term resolution, synonym/alias/anti-synonym, taxonomy hierarchy.
- **DeltaGenerator:** Converts ReasoningEvent → ~10 deltas (pattern, guardrail, edges, metrics, actions).
- **ReasoningEngine:** Loads ontology + synthetic data, reasons over questions with context.

### What's Broken / Incomplete
| Issue | File | Detail |
|-------|------|--------|
| Oversized function | `reasoning/engine.py:27` | `reason()` = 109 lines, complexity 19 |
| Oversized function | `confidence.py:111` | `compute()` = 84 lines |
| Oversized function | `delta_generator.py:94` | `_generate_pattern_delta()` = 96 lines |
| Oversized function | `delta_generator.py:248` | `_generate_edge_deltas()` = 66 lines |
| Oversized function | `semantic_store.py:396` | `seed_commercial_synonyms()` = 85 lines |
| Low PRS | `delta_generator.py` | PRS 78/100 |
| Low PRS | `semantic_store.py` | PRS 78/100 |
| Missing feature | Pattern Matching | Boolean only — no ranked scoring |
| Missing feature | Guardrail Eval | No `blocks_drivers` logic |
| Missing feature | Conflict Detection (US-025) | No duplicate/contradiction checks |
| Missing feature | Governance (EPIC-003) | None of 7 stories started |
| Tech debt | 10+ places | `datetime.utcnow()` deprecated |

### Quality Baseline
- 7 HIGH CK findings (all PRS-related from oversized functions)
- 0 boundary violations, 0 circular imports

---

## 5. Architecture Rules

### Import Boundaries (Enforced by Cathedral Keeper)
```
src/core/      →  MUST NOT import from  →  src/api/
src/reasoning/ →  MUST NOT import from  →  src/api/
src/ingestion/ →  MUST NOT import from  →  src/api/
```

### The Delta Model is Sacred
- Every mutation to the knowledge graph MUST go through a Delta
- No direct writes to GraphStore/JudgmentStore/SemanticStore from outside PromotionPipeline
- Exception: seeding functions for initial ontology loading

### Evidence-First
- Every assertion must link to evidence
- New data structures need `evidence_ids: List[str]` or equivalent

### Function Size: Max 50 Lines (quality gate enforced)

### Type Safety: Full type hints on all public functions. No `Any` at boundaries.

---

## 6. Key Data Models (Quick Reference)

```python
# Enums
DeltaStatus: PROPOSED | APPROVED | REJECTED | MERGED
DeltaType: PROPOSED_MAPPING | PROPOSED_SYNONYM | PROPOSED_EDGE | PROPOSED_ENTITY | PROPOSED_PATTERN | PROPOSED_GUARDRAIL | PROPOSED_ACTION
JudgmentType: EMPIRICAL | CAUSAL_HYPOTHESIS | NORMATIVE
RiskClass: ADVISORY | DECISION_SUPPORT | RESTRICTED
BlastRadius: LOW | MEDIUM | HIGH
AgentMode: EXPLORE | APPLY | RECOMMEND | EXPLAIN

# Core types
Delta(id, type, status, content, confidence, blast_radius, evidence_pointers, conflicts)
JudgmentPattern(pattern_id, name, applies_when_signals, applies_when_context, typical_drivers, governance, decay, scope)
Guardrail(guardrail_id, name, rule, blocks_claims, unless_evidence, applicable_personas, governance)
TraversalPolicy(risk_class, max_traversal_depth, requires_evidence, confidence_threshold, allowed_missions)
IntelligencePacket(question, drivers, confidence, evidence, actions, trace)
```

### Confidence Formula
```
Final = (0.30 × base_prior) + (0.25 × evidence_reliability) + (0.15 × corroboration)
      + (0.15 × (1 - conflict_penalty)) + (0.15 × freshness)
Thresholds: ACTIONABLE=0.55, HIGH_CONFLICT=0.40, MISSING_EVIDENCE_PENALTY=0.25
Evidence: HARD=1.0, SOFT=0.6, RUMOR=0.3
```

---

## 7. Your Ticket Queue

Check `docs/BOARD.md` for current board state. Your active tickets:

| Ticket | Title | Priority | Phase |
|--------|-------|----------|-------|
| CTX-001 | Pattern Matching v2 — Ranked Scoring | P0 | 2.1 |
| CTX-002 | Guardrail Evaluation v2 — blocks_drivers | P0 | 2.1 |
| CTX-003 | Conflict Detection (US-025) | P0 | 2.1 |
| CTX-004 | Reasoning Engine Decomposition | P1 | 2.1 |
| CTX-005 → CTX-016 | See BOARD.md for full backlog | P1-P2 | 3-7 |

Sprint details (acceptance criteria) are in `docs/Lead2Dev.md`.

---

## 8. How to Start

```
1. READ this file (done)
2. READ anti_slop.md
3. READ docs/BOARD.md — see full board state
4. READ docs/Lead2Dev.md — find your ticket marked 🟢 EXECUTE NOW
5. READ docs/DECISION_LOG.md — settled decisions
6. READ sprint-scoped source files
7. READ relevant test files
8. WRITE mini-spec in docs/Dev2Lead.md
9. IMPLEMENT (if Low/Medium) or WAIT for Lead (if HIGH)
10. RUN: python -m pytest tests/ -v
11. RUN: python quality-gate/quality_gate.py --root .
12. REPORT in docs/Dev2Lead.md
```

---

_Team CORTEX Instruction Packet v2.0 — Tech Lead_
