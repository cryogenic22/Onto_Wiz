# Onto_Wiz — State of the Project

> Deep analysis by Tech Lead / Team CORTEX
> Date: 2026-02-16
> Context: 8 sprints completed, 247 tests passing, ~6,200 LOC backend

---

## Executive Summary

Onto_Wiz has a **real, working governance engine** — not scaffolding. The delta model, judgment artifacts, HITL routing, and API layer are production-grade. The game UI captures SME knowledge and feeds it through a genuine approval workflow. 247 tests exercise actual business logic, not mocks.

But the system is architecturally lopsided. **We've over-invested in governance plumbing and under-invested in reasoning.** The core promise — "turn pharma expertise into grounded intelligence packets" — has a working front door (game capture) and a working back office (approval pipeline), but the engine room (reasoning, graph traversal, inference) is a 120-line tag matcher. That's the honest truth.

---

## What's Actually Built (Not Planned — Built)

### Tier 1: Production-Grade (Real, Tested, Wired End-to-End)

| Component | LOC | Tests | Status |
|-----------|-----|-------|--------|
| **Delta Model** — propose/approve/reject/escalate lifecycle | ~400 | 40+ | Rock solid. Full governance with blast radius, confidence, classification, routing. |
| **JudgmentStore** — patterns, guardrails, action templates with approval workflow | ~500 | 30+ | Complete CRUD + governance. Pattern matching with ranked scoring. Consolidation. Semantic search. |
| **HITL Routing** — auto/standard/escalated queues, role-based assignment | ~200 | 15+ | Routing matrix works: empirical→auto, causal→domain_expert, normative→governance_board. |
| **API Server** — 40+ FastAPI endpoints, all wired to real stores | ~750 | 73 | Every endpoint hits real in-memory stores. No mock data. Proper HTTP contracts. |
| **Audit Trail** — every operation logged with actor, before/after snapshots | ~150 | 11 | Full audit on all 3 stores. Combined query with filtering. Export endpoint. |
| **Game UI** — 9-step SME knowledge capture | ~800 | — | Hypothesis → signals → disconfirm → pattern → mistakes → actions → confidence. All wired to API. |
| **Delta Generator** — transforms game sessions into deltas | ~500 | 14 | Maps ReasoningEvent → typed deltas (pattern, guardrail, edge, metric, action). |
| **Promotion Pipeline** — approved deltas → live judgment artifacts | ~100 | 1 | Pattern/guardrail/action promotion handlers. Marks deltas as merged. |
| **Review Cycle Enforcement** — governance freshness tracking | ~45 | 9 | Monthly/quarterly/annual review detection. Upcoming review lookahead. |
| **Pattern Consolidation** — overlap detection, merge, lineage | ~95 | 13 | Jaccard similarity, pairwise scan, consolidate with superseded_by tracking. |
| **Semantic Search** — synonym-expanded pattern + evidence queries | ~75 | 11 | Bridges SemanticStore into JudgmentStore and EvidenceStore search. |

### Tier 2: Functional But Thin

| Component | LOC | Tests | Status |
|-----------|-----|-------|--------|
| **SemanticStore** — synonym/alias/taxonomy management | ~540 | — | Real store with canonical terms, relations, anti-synonyms. Seeded with pharma terms. But no tests in test_core.py (tested indirectly via semantic search). |
| **EvidenceStore** — first-class evidence with reliability classes | ~490 | 12 | CRUD, deduplication, permission-aware retrieval. But evidence is never populated from real sources — it's a container waiting for content. |
| **GraphStore** — typed node/edge graph | ~540 | 10 | Node/edge CRUD, neighbor queries, subgraph extraction, path finding. But not used by the reasoning engine. It's a data structure nobody reads from. |
| **ConfidenceEngine** — decay, evidence weighting, credibility | ~440 | — | DecayConfig, refresh triggers, scoring. Exists in models. But `compute()` is 75 lines (slop) and not integrated into the main flow. |
| **Curator Dashboard** — review queue + audit UI | ~300 | — | Basic but functional. Approve/reject/escalate buttons work. No bulk actions, no advanced filtering. |
| **SME Dashboard** — contribution stats + leaderboard | ~200 | — | Stats, leaderboard, domain coverage. Basic cards. |

### Tier 3: Exists But Undercooked

| Component | LOC | Tests | Status |
|-----------|-----|-------|--------|
| **Reasoning Engine** | 120 | ~10 | **This is the core gap.** Tag-matching against YAML rules. No graph traversal, no pattern chaining, no confidence propagation, no multi-step inference. The "brains" of the system is the simplest part. |
| **Ingestion Pipeline** | 85 | — | Stub. No document ingestion, no data feed processing, no ETL. |
| **Ontology Content** | 19 rules, 15 scenarios | 18 gold sets | Good pharma domain knowledge. But rules are static YAML — they don't learn from approved patterns. Two parallel rule systems (YAML rules in engine vs JudgmentPatterns in store) that don't talk to each other. |

---

## The Architecture's Honest Problem

There are **two disconnected reasoning paths**, and neither is complete:

```
PATH A: Static Rules (ReasoningEngine)
  YAML ontology rules → tag matching → winning rule → verdict
  - Works for gold-set scenarios
  - 19 rules, priority-ranked
  - Cannot learn from SME input
  - Not connected to JudgmentStore

PATH B: Learned Patterns (JudgmentStore → Intelligence Packet)
  Game session → delta → approval → pattern → find_matching_patterns → packet
  - The "living knowledge" vision
  - Pattern matching with ranked scoring
  - Connected to governance, audit, semantic search
  - But: no graph traversal, no multi-step reasoning, no rule chaining
```

**Neither path does what the product promises end-to-end.** Path A can reason but can't learn. Path B can learn but doesn't truly reason — it matches signals to patterns and returns drivers, which is retrieval, not inference.

The Intelligence Packet generation (`POST /intelligence-packet`) is essentially:
1. Take a signal metric
2. Find patterns with overlapping signals
3. Collect their drivers
4. List active guardrails
5. Package it

That's a **lookup**, not reasoning. It doesn't chain rules, propagate confidence across a graph, weigh contradicting evidence, or synthesize a novel conclusion. It returns what SMEs already told it.

---

## What's Missing for Genuine Value

### Critical Path (Must Have)

**1. Unify the two reasoning paths**
The YAML rules and JudgmentPatterns need to converge. When an SME plays a game and the pattern gets approved, it should become a queryable rule — not sit in a separate store. The ReasoningEngine should query JudgmentStore patterns alongside YAML rules.

**Effort:** M — wire `find_matching_patterns()` into `ReasoningEngine._find_winning_rule()`. Not architecturally hard, but requires deciding which takes priority (static vs learned).

**2. Persistent storage**
Everything is in-memory. Server restart = total knowledge loss. This isn't about scaling — it's about the product being usable for more than one session.

Options:
- SQLite for quick persistence (patterns, deltas, audit — all serializable)
- Neo4j/PostgreSQL for production (graph queries + relational governance)

**Effort:** L — schema design, migration scripts, store adapter pattern. But clean separation already exists (stores have clear interfaces).

**3. The "so what" layer — actionable output**
The Intelligence Packet has `recommendations` but they're generic. For real value, the packet needs:
- **Specificity:** "Pull PA reject data for Keytruda in Northeast, Q1 2026" — not "investigate access barriers"
- **Quantification:** "Estimated $2.3M revenue at risk based on formulary position changes"
- **Comparison:** "This pattern was seen with Brand X in 2024, resolved in 6 weeks via payer engagement"

This is where LLM integration (CTX-020, currently Sprint 11) becomes essential. The system knows the patterns; it needs language to make them actionable.

**Effort:** L-XL — requires LLM integration, prompt engineering, template system.

**4. Data ingestion — feeding the beast**
The system captures knowledge through games. But games are slow (10-15 minutes per scenario). For the system to have enough patterns, you need:
- Document ingestion (MSL reports, field notes, market research)
- Data feed connectors (TRx/NBRx data → signals)
- Automated evidence creation from structured data

Without this, the knowledge graph stays thin. SMEs play 10 games, you get 10 patterns. That's a demo, not a product.

**Effort:** XL — this is an engineering initiative, not a ticket.

### Important But Not Blocking

**5. Graph traversal for real reasoning**
The GraphStore exists but nobody queries it for inference. For real reasoning:
- Signal → (leads_to) → Hypothesis → (supported_by) → Evidence
- Hypothesis → (contradicted_by) → Counter-evidence → (unless) → Override condition
- Pattern → (similar_to) → Related patterns → confidence propagation

This is the "thinking" part. Without it, the system is a structured database, not a reasoning engine.

**6. Multi-tenant and authentication**
No auth at all. No client_id enforcement. The models have `client_id` fields, but nothing enforces them. For any real deployment (even internal), you need basic auth + tenant isolation.

**7. Deployment infrastructure**
No Docker, no cloud config, no secrets management. This is a `python src/api/server.py` application. Getting it to a hosted demo requires containerization at minimum.

---

## Maturity Scorecard

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| **Data Model** | 9/10 | Comprehensive, well-governed, properly typed. Delta model is genuinely good. |
| **Governance** | 9/10 | HITL routing, audit trails, review cycles, consolidation, blast radius. This is the strongest part. |
| **API Layer** | 8/10 | 40+ endpoints, all wired, proper contracts. Missing: pagination on some endpoints, rate limiting. |
| **Knowledge Capture** | 7/10 | Game loop works. Delta generator produces typed artifacts. But only one capture channel (games). |
| **Domain Content** | 7/10 | 19 rules, 15 scenarios, 11 domains, 3 TAs. Real pharma knowledge. But heavy on oncology, thin elsewhere. |
| **Testing** | 8/10 | 247 tests, E2E smoke suite, gold sets. No frontend E2E tests. |
| **Frontend** | 6/10 | Game UI is solid. Dashboards are basic. No Intelligence Packet viewer yet. |
| **Reasoning** | 3/10 | Tag matching only. No graph traversal, no inference chaining, no confidence propagation. |
| **Persistence** | 0/10 | Entirely in-memory. |
| **Deployment** | 1/10 | Local dev only. No Docker, no cloud, no CI/CD deploy step. |
| **Integration** | 2/10 | No external data sources, no LLM integration, no MCP server. |

**Overall: 55/110 = 50%** — but unevenly distributed. The governance layer is production-ready; the reasoning layer is prototype-grade.

---

## What Would Make This Genuinely Valuable

### Scenario 1: Internal Research Tool (3-4 sprints)
**Goal:** A hosted tool where pharma strategists can play scenarios, review patterns, and get intelligence packets.

What's needed:
- [ ] SQLite persistence (patterns + deltas survive restarts)
- [ ] Unify reasoning paths (YAML rules + JudgmentPatterns)
- [ ] Intelligence Packet viewer (LENS-014, already spec'd)
- [ ] Docker + basic cloud deployment
- [ ] Basic auth (API key or SSO)

**Value:** "Play a game, get a structured analysis that gets smarter over time."

### Scenario 2: Agent-Consumable Knowledge Service (5-7 sprints)
**Goal:** An MCP server that Claude/GPT agents can query for grounded pharmaceutical intelligence.

What's needed:
- Everything in Scenario 1, plus:
- [ ] MCP Server (CTX-040) exposing tools: `get_intelligence_packet`, `check_guardrails`, `find_patterns`
- [ ] LLM-assisted summarization (CTX-020) for natural language output
- [ ] Document ingestion pipeline for evidence corpus
- [ ] Semantic search with synonym expansion (done)

**Value:** "Ask Claude about Keytruda market dynamics and get an answer grounded in structured expertise, not just training data."

### Scenario 3: Enterprise Knowledge Platform (10+ sprints)
**Goal:** A multi-tenant platform serving multiple brands and therapeutic areas.

What's needed:
- Everything in Scenarios 1-2, plus:
- [ ] Neo4j/PostgreSQL for scale
- [ ] Multi-tenant isolation
- [ ] RBAC (role-based access control)
- [ ] Data feed connectors (IQVIA, claims, CRM)
- [ ] Graph traversal reasoning engine
- [ ] Cross-brand pattern learning
- [ ] PII/PHI redaction (SEN-021)
- [ ] Full frontend suite (scenario builder, expert mode, analytics)

**Value:** "Enterprise knowledge infrastructure that compounds expertise across brands, TAs, and time."

---

## Honest Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **"Good enough" problem** — LLMs can answer pharma questions without structured knowledge | HIGH | HIGH | Differentiate on auditability, governance, and grounding. LLMs hallucinate; Onto_Wiz provides evidence chains. But this only matters if intelligence packets are genuinely better than raw LLM output. |
| **Cold start** — system needs patterns to be useful, patterns need SME time to create | HIGH | MEDIUM | Document ingestion (not just games). Pre-seed with industry patterns. Make the first 30 minutes of use valuable. |
| **Adoption friction** — playing a 9-step game is a lot to ask of busy SMEs | MEDIUM | HIGH | Reduce game to 3-5 critical steps. Add "quick capture" mode. Make the game output immediately visible (intelligence packet from your session). |
| **Two reasoning paths never converge** — tech debt accumulates, neither system is complete | MEDIUM | HIGH | This is the single most important architectural decision. Unify them in the next 2 sprints or accept permanent divergence. |
| **Over-engineering governance for a system that can't reason** — beautiful approval pipeline for a lookup table | HIGH | MEDIUM | Governance is valuable, but only if the governed artifacts produce genuine insight. Shift focus from governance features to reasoning quality. |

---

## Recommendation

**Stop adding governance features. Start making the reasoning work.**

The backlog is heavy on governance plumbing (CTX-010 Agent Mode Enforcement, CTX-011 Traversal Depth Checking, CTX-012-015 persistence/export). These are important for enterprise readiness, but the core product promise — "intelligent analysis" — depends on the reasoning engine being more than a tag matcher.

**Priority order for the next 3 sprints:**

1. **Unify reasoning paths** — make JudgmentPatterns queryable by ReasoningEngine. One source of truth for inference.
2. **Intelligence Packet viewer** (LENS-014) — make the product visible. If you can't show someone an intelligence packet and have them say "that's useful," nothing else matters.
3. **SQLite persistence** — make patterns survive restarts so you can accumulate knowledge across sessions.
4. **Document ingestion v1** — a simple pipeline that takes a field report or MSL note and extracts signals/evidence. Doesn't need to be perfect; needs to exist.

Everything else (MCP server, multi-tenant, graph traversal, LLM summarization) is second-order until the core loop works: **capture → reason → show → improve**.

---

## Test Suite Status

```
247 passed, 0 failed
  test_core.py:       120 tests (delta, pattern, guardrail, conflict, classification,
                       HITL routing, contribution, audit, review cycle, consolidation,
                       semantic search)
  test_api.py:         73 tests (all endpoints, request/response contracts)
  test_e2e_smoke.py:   14 tests (full user journeys: game→delta→review→audit)
  test_graph_evidence:  22 tests (graph store, evidence store, semantic evidence search)
  test_gold_set:       18 tests (all 19 inference rules covered)
```

---

*This document should be revisited after every 3 sprints to reassess priorities.*
