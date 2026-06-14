# Onto_Wiz Product Roadmap

## Timeline Overview

```
Q1 2026                          Q2 2026                          Q3 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1-2 ✅    Phase 2.1       Phase 3         Phase 4-5       Phase 6-7
Foundation      Structural      Governance      Learning Loop   Production
Delta Model     Gaps            Layer           Agent Safety    Demo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      ↑              ↑              ↑                ↑              ↑
   DONE           NOW           2 weeks         4 weeks        6 weeks
```

---

## Phase 1: Foundation & Architecture ✅ COMPLETE

**Goal:** Establish core architecture and validate concept

| Milestone | Status | Delivered |
|:---|:---|:---|
| System Architecture | ✅ | Hybrid store design, expansion layers |
| Commercial Ontology | ✅ | Entities, relationships, dark data nodes |
| Reasoning Test Harness | ✅ | TDD verification with scenarios |
| Semantic Harvester Prototype | ✅ | Golden scenarios, review UI flow |
| Strategic Alignment | ✅ | 300 scenarios, UBI integration, architecture v2 |

**Artifacts:**
- `complete_scenario_library.md` - 300 foundation scenarios
- `ubi_integration_design.md` - UBI platform integration
- `architecture_v2_hardened.md` - Enterprise architecture

---

## Phase 2: Delta Model & Judgment Artifacts ✅ COMPLETE

**Goal:** Implement core delta-first mutation model and artifact system

| Milestone | Status | Delivered |
|:---|:---|:---|
| Delta Model | ✅ | Delta schema, DeltaStore, conflict detection |
| Judgment Artifacts | ✅ | JudgmentPattern, Guardrail, ActionTemplate |
| Review Queue API | ✅ | 15 endpoints for HITL workflow |
| Intelligence Packet | ✅ | UBI output format |

**Code Delivered:**
- `src/core/models.py` - 473 lines
- `src/core/stores.py` - 464 lines
- `src/api/server.py` - 516 lines
- 56 tests passing

---

## Phase 2.1: Structural Gaps 🟡 IN PROGRESS

**Goal:** Address critical gaps identified in architecture review

| Gap | Priority | Status | Owner |
|:---|:---|:---|:---|
| Evidence Model | 🔴 Critical | ✅ Done | - |
| GraphStore | 🔴 High | ✅ Done | - |
| ConfidenceEngine | 🔴 High | ✅ Done | - |
| Pattern Matching v2 | 🟡 High | 🔲 Pending | - |
| Guardrail Evaluation v2 | 🟡 Medium | 🔲 Pending | - |
| PromotionPipeline Governance | 🟡 Medium | 🔲 Pending | - |

**Code Delivered:**
- `src/core/graph_store.py` - 526 lines
- `src/core/evidence.py` - 472 lines
- `src/core/confidence.py` - 300 lines
- `src/core/reasoning_event.py` - 360 lines
- `src/core/delta_generator.py` - 510 lines
- `src/core/semantic_store.py` - 500 lines

---

## Phase 3: Governance Layer (2 weeks)

**Goal:** Enterprise-grade safety and compliance

| Milestone | Effort | Dependencies |
|:---|:---|:---|
| Artifact Ownership Model | 3d | Phase 2.1 |
| Approval Workflows | 4d | Ownership model |
| Audit Trail Enhancement | 3d | None |
| Judgment Type Classification | 2d | Approval workflows |

**Acceptance Criteria:**
- [ ] All artifacts have owner, approver, approved_on
- [ ] Level 2/3 judgments require HITL approval
- [ ] Full audit trace exportable per mission
- [ ] Normative judgments blocked without justification

---

## Phase 4: Learning Loop (2 weeks)

**Goal:** Complete game → graph pipeline

| Milestone | Effort | Dependencies |
|:---|:---|:---|
| ReasoningEvent Schema | ✅ Done | - |
| DeltaGenerator | ✅ Done | - |
| Consolidation/Reconciler | 3d | DeltaGenerator |
| Semantic Capture Pipeline | 2d | SemanticStore |

**Acceptance Criteria:**
- [ ] SME game produces 10+ deltas per session
- [ ] Duplicate patterns auto-merged
- [ ] Conflicting patterns flagged for review
- [ ] Synonyms extracted and proposed

---

## Phase 5: Bounded Agent Traversal (2 weeks)

**Goal:** Safe AI agent execution with guardrails

| Milestone | Effort | Dependencies |
|:---|:---|:---|
| Agent Mode Enforcement | 3d | Phase 3 |
| Hard Stops | 2d | ConfidenceEngine |
| Traversal Policy Enforcement | 3d | Guardrails v2 |

**Acceptance Criteria:**
- [ ] Agent halts on confidence < 0.55
- [ ] Agent halts on missing required evidence
- [ ] Agent respects max_traversal_depth
- [ ] Guardrail violations trigger escalation

---

## Phase 6: Production Hardening (3 weeks)

**Goal:** Production-ready infrastructure

| Milestone | Effort | Dependencies |
|:---|:---|:---|
| Persistence (Postgres/Neo4j) | 5d | Phase 4 |
| Multi-Tenancy | 3d | Persistence |
| RBAC/ABAC | 4d | Multi-tenancy |
| Telemetry | 3d | All phases |

**Acceptance Criteria:**
- [ ] Data persisted to Postgres + Neo4j
- [ ] Global pack + client overlays work
- [ ] Evidence access respects permissions
- [ ] Telemetry dashboard operational

---

## Phase 7: Demo & Validation (2 weeks)

**Goal:** Enterprise demo and validation suite

| Milestone | Effort | Dependencies |
|:---|:---|:---|
| End-to-End Demo | 3d | Phase 5-6 |
| Quality Comparison | 2d | Demo |
| Regression Suite | 3d | All phases |

**Demo Flow:** "Why did Brand X dip in Northeast?"
1. Pull structured metrics + unstructured evidence
2. Fire ranked patterns (access friction > demand erosion)
3. Compute confidence via ConfidenceEngine
4. Enforce guardrails (no demand claim without NBRx)
5. Produce IntelligencePacket with full trace

---

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|:---|:---|:---|
| SME adoption | High | Game feels like case discussion, not work |
| Pattern explosion | Medium | Consolidation/reconciler auto-merges |
| Confidence gaming | Medium | Evidence-based computation only |
| Multi-tenant complexity | High | Start with single-tenant MVP |

---

## Success Metrics (MVP)

| Metric | Target | Measurement |
|:---|:---|:---|
| SME game time | < 7 min | Timer in UI |
| Deltas per session | 8-12 | DeltaGenerator output |
| Pattern match accuracy | > 80% | Test harness |
| Guardrail efficacy | 0 overclaims | Audit review |
| Demo completion | End-to-end | Manual validation |
