# Onto_Wiz Full Backlog

> **Last Updated:** 2026-01-31

## Summary Metrics

| Metric | Value |
|:---|:---|
| **Epics** | 5 |
| **User Stories** | 57 |
| **Technical Tasks** | 85+ |
| **Story Points** | 280 (estimated) |
| **Completed** | ~40% |
| **Current Sprint** | Phase 2.1 (Structural Gaps) |

---

## Epic Summary

| Epic | Stories | Points | Status |
|:---|:---|:---|:---|
| [EPIC-001: SME Game](epics/EPIC-001_sme_game.md) | 11 | 40 | 🟡 In Progress |
| [EPIC-002: Delta Model](epics/EPIC-002_delta_model.md) | 7 | 25 | ✅ 90% Done |
| [EPIC-003: Governance](epics/EPIC-003_governance.md) | 7 | 30 | 🔲 Not Started |
| [EPIC-004: Agent Traversal](epics/EPIC-004_agent_traversal.md) | 8 | 27 | 🟡 Partial |
| [EPIC-005: Production](epics/EPIC-005_production.md) | 8 | 45 | 🔲 Not Started |

---

## Current Sprint: Phase 2.1

**Goal:** Address structural gaps before governance layer

### Completed ✅

- [x] Evidence Model (EvidenceStore, EvidenceItem, reliability classes)
- [x] GraphStore (nodes, edges, traversal)
- [x] ConfidenceEngine (evidence-weighted computation)
- [x] ReasoningEvent Schema (SME game output)
- [x] DeltaGenerator (game → 10 deltas)
- [x] SemanticStore (synonyms, taxonomy, domains)

### Remaining 🔲

| Task | Priority | Effort |
|:---|:---|:---|
| Pattern Matching v2 (ranked scoring) | High | 3d |
| Guardrail Evaluation v2 (blocks_drivers) | Medium | 2d |
| PromotionPipeline governance preservation | Medium | 2d |
| Consolidation/Reconciler | Medium | 3d |

---

## Next Sprint: Phase 3 (Governance)

### Stories

| ID | Story | Points |
|:---|:---|:---|
| US-030 | Artifact ownership model | 3 |
| US-031 | Judgment type classification | 3 |
| US-032 | Risk class enforcement | 5 |
| US-033 | HITL routing | 5 |
| US-034 | Review cycle tracking | 3 |
| US-035 | Enhanced audit trail | 5 |
| US-036 | Audit export | 3 |

---

## Prioritized Backlog

### P0 - Critical (This Week)

| ID | Story | Epic |
|:---|:---|:---|
| - | Pattern Matching v2 | E-002 |
| US-044 | Guardrail.is_violated() v2 | E-004 |

### P1 - High (Next 2 Weeks)

| ID | Story | Epic |
|:---|:---|:---|
| US-030 | Artifact ownership | E-003 |
| US-031 | Judgment type classification | E-003 |
| US-041 | Halt on low confidence | E-004 |
| US-042 | Halt on high conflict | E-004 |

### P2 - Medium (Sprint 3)

| ID | Story | Epic |
|:---|:---|:---|
| US-001-009 | SME Game UI | E-001 |
| US-032 | Risk class enforcement | E-003 |
| US-033 | HITL routing | E-003 |
| US-053 | Multi-tenancy | E-005 |

### P3 - Low (Future)

| ID | Story | Epic |
|:---|:---|:---|
| US-054 | RBAC | E-005 |
| US-056 | Telemetry dashboard | E-005 |
| US-057 | Performance benchmarks | E-005 |

---

## Design Documents

| Document | Status | Location |
|:---|:---|:---|
| Confidence Engine | ✅ Done | [designs/design_confidence_engine.md](designs/design_confidence_engine.md) |
| Semantic Store | ✅ Done | [designs/design_semantic_store.md](designs/design_semantic_store.md) |
| Game → Delta Pipeline | ✅ Done | [designs/design_game_to_delta_pipeline.md](designs/design_game_to_delta_pipeline.md) |
| Pattern Matching v2 | 🔲 Pending | - |
| Guardrail Evaluation | 🔲 Pending | - |
| Multi-Tenancy | 🔲 Pending | - |

---

## Technical Debt

| Item | Priority | Effort |
|:---|:---|:---|
| Replace datetime.utcnow() | Low | 1h |
| Add integration tests | Medium | 2d |
| Add GraphStore unit tests | Medium | 1d |
| API error handling | Medium | 1d |
| Type hints cleanup | Low | 0.5d |

---

## Definition of Done

For a story to be marked complete:

- [ ] Code implemented
- [ ] Unit tests passing
- [ ] Integration tests (if applicable)
- [ ] Design doc updated (if applicable)
- [ ] Code reviewed (if pair working)
- [ ] Demo-able

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|:---|:---|:---|:---|
| SME game adoption | High | Medium | UX research, iterate on flow |
| Pattern explosion | Medium | Medium | Consolidation/reconciler |
| Confidence gaming | Medium | Low | Evidence-only computation |
| Multi-tenant bugs | High | Medium | Comprehensive isolation tests |
| Performance at scale | Medium | Medium | Caching, indexing, benchmarks |

---

## Dependencies

### External

| Dependency | Status | Blocking |
|:---|:---|:---|
| Postgres | 🔲 Not deployed | Phase 6 |
| Neo4j | 🔲 Not deployed | Phase 6 |
| Redis | 🔲 Not deployed | Phase 6 |
| Auth provider | 🔲 TBD | Phase 5-6 |

### Internal

| Dependency | Status | Required By |
|:---|:---|:---|
| Evidence Model | ✅ Done | GraphStore |
| GraphStore | ✅ Done | Agent Traversal |
| ConfidenceEngine | ✅ Done | Agent Traversal |
| SemanticStore | ✅ Done | DeltaGenerator |
| Governance Layer | 🔲 Pending | Production |

---

## Team & Roles

| Role | Responsibility |
|:---|:---|
| Product Owner | Backlog prioritization, acceptance |
| Tech Lead | Architecture decisions, code review |
| Backend Dev | Core models, API, stores |
| Frontend Dev | SME Game UI |
| QA | Test automation, regression |
| DevOps | Infrastructure, deployment |
