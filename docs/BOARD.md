# Onto_Wiz Agile Board

> Single-view board for all teams. Stories flow: BACKLOG → READY → IN_PROGRESS → REVIEW → DONE
> Updated by: Tech Lead (column moves), Teams (status notes in Dev2Lead)
> Ticket format: `[TEAM]-NNN` where TEAM = `LENS`, `CTX`, `ATL`, or `SEN`
> Teams: LENS (API + UI), CORTEX (Core Engine), ATLAS (Domain Content), SENTINEL (Quality Gate)
> Last Updated: 2026-02-17 (Sprint 9 — Reasoning Pivot Sprint)

---

## Board View

### DONE

| Ticket | Title | Team | Sprint | Completed |
|--------|-------|------|--------|-----------|
| CTX-001 | Pattern Matching v2 — Ranked Scoring | CORTEX | Phase 2.1 | 2026-01-31 |
| CTX-002 | Guardrail Evaluation v2 — blocks_drivers | CORTEX | Phase 2.1 | 2026-01-31 |
| CTX-003 | Conflict Detection (US-025) | CORTEX | Phase 2.1 | 2026-01-31 |
| CTX-004 | Reasoning Engine Decomposition | CORTEX | Phase 2.1 | 2026-01-31 |
| LENS-001 | API Integration Tests + Infra Hardening | LENS | Phase 2.1 | 2026-01-31 |
| LENS-002 | SituationRoom Game Loop MVP (US-001→009) | LENS | Phase 2.1 | 2026-02-01 |
| LENS-003 | Server.py Decomposition | LENS | Phase 2.1 | 2026-01-31 |
| CTX-017 | ReasoningEvent Ingestion + Delta Generation | CORTEX | Sprint 1 | 2026-02-01 |
| LENS-012 | Design System + Persona Modes | LENS | Sprint 1 | 2026-02-01 |
| ATL-001 | Commercial Ontology Expansion — Full Value Chain | ATLAS | Sprint 1 | 2026-02-01 |
| SEN-001 | Quality Gate Infrastructure | SENTINEL | Sprint 1 | 2026-02-01 |
| SEN-002 | Automated Anti-Slop Checker | SENTINEL | Sprint 2 | 2026-02-01 |
| ATL-002 | Oncology Therapeutic Area — Deep Taxonomy | ATLAS | Sprint 2 | 2026-02-01 |
| SEN-003 | Cross-Team Architecture Review (Phase 2.5) | SENTINEL | Sprint 3 | 2026-02-01 |
| SEN-004 | Integration Test Coverage Audit + Gap Report | SENTINEL | Sprint 4 | 2026-02-01 |
| LENS-011 | Game Session Submission API + Hook | LENS | Sprint 2 | 2026-02-01 |
| SEN-005 | Performance Baseline | SENTINEL | Sprint 2 | 2026-02-01 |
| CTX-005 | Artifact Ownership + Judgment Classification | CORTEX | Sprint 2 | 2026-02-01 |
| CTX-006 | HITL Routing Logic | CORTEX | Sprint 3 | 2026-02-01 |
| LENS-004 | HITL Routing Endpoints + Audit Export API | LENS | Sprint 3 | 2026-02-01 |
| SEN-006 | Security Review (OWASP Top 10) | SENTINEL | Sprint 3 | 2026-02-01 |
| SEN-007 | Architecture Decision Records (ADR-001→011) | SENTINEL | Sprint 3 | 2026-02-01 |
| CTX-018 | Contribution Tracking Store | CORTEX | Sprint 4 | 2026-02-02 |
| ATL-003 | Scenario Library v1 — 10 Oncology Scenarios | ATLAS | Sprint 3 | 2026-02-02 |
| LENS-005 | Curator Dashboard MVP | LENS | Sprint 4 | 2026-02-02 |
| SEN-008 | E2E Smoke Test Suite | SENTINEL | Sprint 4 | 2026-02-02 |
| ATL-004 | Market Access Domain — Payer/Formulary | ATLAS | Sprint 4 | 2026-02-02 |
| CTX-008 | Enhanced Audit Trail | CORTEX | Sprint 5 | 2026-02-02 |
| LENS-013 | SME Impact Dashboard | LENS | Sprint 5 | 2026-02-02 |
| CTX-007 | Review Cycle Enforcement | CORTEX | Sprint 6 | 2026-02-02 |
| CTX-009 | Pattern Consolidation / Reconciler | CORTEX | Sprint 7 | 2026-02-16 |
| CTX-019 | Semantic Search over Patterns + Evidence | CORTEX | Sprint 8 | 2026-02-16 |

### REVIEW
_None._

### IN_PROGRESS

| Ticket | Title | Team | Sprint | Started |
|--------|-------|------|--------|---------|
| CTX-041 | Unify Reasoning Paths — YAML Rules + JudgmentPatterns | CORTEX | Sprint 9 | 2026-02-17 |
| LENS-014 | Intelligence Packet Viewer | LENS | Sprint 9 | 2026-02-16 |
| ATL-006 | Immunology TA — Taxonomy + Scenarios | ATLAS | Sprint 9 | 2026-02-17 |
| SEN-009 | Load Testing Framework | SENTINEL | Sprint 9 | 2026-02-17 |

### READY (Sprint-planned, mini-spec approved)
_None._

---

## Sprint Roadmap (20 Sprints)

### Sprint 1 — SME Pipeline + Design Foundation

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-017 | ReasoningEvent Ingestion + Delta Generation | L |
| LENS | LENS-012 | Design System + Persona Modes | L |
| ATLAS | ATL-001 | Commercial Ontology Expansion — Full Value Chain | L |
| SENTINEL | SEN-001 | Quality Gate Infrastructure (CI, linting, coverage thresholds) | M |

### Sprint 2 — Session Wiring + Governance Foundation

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-005 | Artifact Ownership + Judgment Classification | M |
| LENS | LENS-011 | Game Session Submission API + Hook | M |
| ATLAS | ATL-002 | Oncology Therapeutic Area — Deep Taxonomy | L |
| SENTINEL | SEN-002 | Automated Anti-Slop Checker (function size, complexity, imports) | M |

### Sprint 3 — HITL Logic + Scenario Library

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-006 | HITL Routing Logic | L |
| LENS | LENS-004 | HITL Routing Endpoints + Audit Export API | M |
| ATLAS | ATL-003 | Scenario Library v1 — 10 Oncology Scenarios | XL |
| SENTINEL | SEN-003 | Cross-Team Architecture Review (Phase 2.5 code) | S |

### Sprint 4 — Contribution Tracking + Curator UI

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-018 | Contribution Tracking Store | M |
| LENS | LENS-005 | Curator Dashboard MVP (Delta Queue + Conflicts + Diffs) | XL |
| ATLAS | ATL-004 | Market Access Domain — Payer/Formulary Taxonomy | L |
| SENTINEL | SEN-004 | Integration Test Coverage Audit + Gap Report | M |

### Sprint 5 — Audit Trail + Impact Dashboard

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-008 | Enhanced Audit Trail | M |
| LENS | LENS-013 | SME Impact Dashboard | L |
| ATLAS | ATL-005 | Gold Set Expansion — 5 Scenarios per TA | L |
| SENTINEL | SEN-005 | Performance Baseline (response times, memory, store sizes) | M |

### Sprint 6 — Review Cycles

> LENS-014 and ATL-006 pulled forward to Sprint 9 (Reasoning Pivot).

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-007 | Review Cycle Enforcement | S |
| LENS | ~~LENS-014~~ | ~~Intelligence Packet Viewer~~ → moved to Sprint 9 | L |
| ATLAS | ~~ATL-006~~ | ~~Immunology TA~~ → moved to Sprint 9 | L |
| SENTINEL | SEN-006 | Security Review (injection, auth, CORS, input validation) | M |

### Sprint 7 — Pattern Consolidation + Graph Explorer

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-009 | Pattern Consolidation / Reconciler | L |
| LENS | LENS-007 | Curator Graph Explorer | L |
| ATLAS | ATL-007 | CNS Therapeutic Area — Taxonomy + Scenarios | L |
| SENTINEL | SEN-007 | Architecture Decision Records (ADR-001 through ADR-010) | M |

### Sprint 8 — Progressive Disclosure + Semantic Search

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-019 | Semantic Search over Patterns + Evidence | L |
| LENS | LENS-015 | Progressive Disclosure Layers | M |
| ATLAS | ATL-008 | Competitive Intelligence Domain — Competitor Ontology | L |
| SENTINEL | SEN-008 | End-to-End Smoke Test Suite | L |

### Sprint 9 — Reasoning Pivot: Unification + Intelligence Viewer

> **Rebalanced 2026-02-17:** Per `product_management/state_of_the_project.md` — stop adding governance plumbing, start making the reasoning work. CTX-010 (Agent Mode Enforcement) deferred to Sprint 12. LENS-016 (Notifications) deferred to Sprint 12. ATL-006 (Immunology) pulled forward from Sprint 6.

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-041 | Unify Reasoning Paths — YAML Rules + JudgmentPatterns | M |
| LENS | LENS-014 | Intelligence Packet Viewer | L |
| ATLAS | ATL-006 | Immunology TA — Taxonomy + Scenarios | L |
| SENTINEL | SEN-009 | Load Testing Framework | M |

### Sprint 10 — Persistence + Progressive Disclosure

> **Rebalanced 2026-02-17:** Pull forward SQLite persistence (critical path from state report). CTX-011 deferred to Sprint 12. LENS-017 deferred to Sprint 13.

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-012 | SQLite Persistence Layer (pull forward from Sprint 13) | XL |
| LENS | LENS-015 | Progressive Disclosure Layers | M |
| ATLAS | ATL-007 | CNS Therapeutic Area — Taxonomy + Scenarios | L |
| SENTINEL | SEN-010 | Dependency Audit + Vulnerability Scan | S |

### Sprint 11 — LLM Gate + Expert Mode

> **Rebalanced 2026-02-17:** CTX-033 (LLM Framework) is EPIC-008 foundation, gated by DEC-012. LENS-025 (Expert Mode) pulled forward. ATL-010 (Inference Rules) feeds unified reasoning engine.

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-033 | LLM Integration Framework (EPIC-008 foundation) | M |
| LENS | LENS-025 | Expert Mode Toggle + Route (EPIC-006) | M |
| ATLAS | ATL-010 | Inference Rule Library v1 — 50 Cross-TA Rules | XL |
| SENTINEL | SEN-011 | API Contract Testing (OpenAPI spec validation) | M |

### Sprint 12 — Agent Mode + Deferred Governance

> **Rebalanced 2026-02-17:** Absorbs CTX-010 (deferred from Sprint 9), LENS-016 (deferred from Sprint 9).

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-010 | Agent Mode Enforcement (deferred from Sprint 9) | L |
| LENS | LENS-016 | Notification System (deferred from Sprint 9) | L |
| ATLAS | ATL-011 | Evidence Corpus v1 — 100 Evidence Items | XL |
| SENTINEL | SEN-012 | Code Coverage Gate (80%+ enforcement) | M |

### Sprint 13 — Traversal + Scenario Builder + Cross-Brand

> **Rebalanced 2026-02-17:** CTX-012 pulled forward to Sprint 10. Absorbs deferred CTX-011, CTX-021, LENS-017.

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-011 | Traversal Depth + Mission Scope Checking (deferred from Sprint 10) | M |
| LENS | LENS-017 | Scenario Builder UI (deferred from Sprint 10) | XL |
| ATLAS | ATL-012 | Supply Chain + Manufacturing Domains | L |
| SENTINEL | SEN-013 | Database Migration Testing Framework | M |

### Sprint 14 — Neo4j Graph + Collaboration

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-013 | Neo4j Graph Persistence | XL |
| LENS | LENS-020 | Collaboration Features (comments, @mentions) | L |
| ATLAS | ATL-014 | Respiratory + Metabolic TAs | L |
| SENTINEL | SEN-014 | Data Migration Verification | L |

### Sprint 15 — Redis Cache + WebSocket Updates

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-014 | Redis Cache Integration | M |
| LENS | LENS-021 | Real-Time Updates (WebSocket) | L |
| ATLAS | ATL-015 | Cross-Functional Playbooks | L |
| SENTINEL | SEN-015 | Chaos Testing | L |

### Sprint 16 — RBAC + NLP Extraction

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-022 | NLP Extraction Pipeline | L |
| LENS | LENS-008 | RBAC Middleware + Auth Endpoints | L |
| ATLAS | ATL-016 | Pharma Metrics Ontology — 200+ Definitions | XL |
| SENTINEL | SEN-016 | Accessibility Audit (WCAG 2.1 AA) | M |

### Sprint 17 — Multi-Tenant + Telemetry

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-015 | Multi-Tenant Architecture | XL |
| LENS | LENS-009 | Telemetry Dashboard UI | L |
| ATLAS | ATL-017 | Regulatory + Pharmacovigilance Domain | L |
| SENTINEL | SEN-017 | Multi-Tenant Isolation Testing | L |

### Sprint 18 — Time-Series + Mobile

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-023 | Time-Series Pattern Detection | L |
| LENS | LENS-022 | Mobile-Responsive SME Interface | L |
| ATLAS | ATL-018 | Regional Market Archetypes (US, EU5, JP, CN) | L |
| SENTINEL | SEN-018 | Performance Regression Suite | M |

### Sprint 19 — Benchmarks + Demo Flow

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-016 | Performance Benchmarks (<50ms p95) | M |
| LENS | LENS-010 | End-to-End Demo Flow | L |
| ATLAS | ATL-019 | Demo Data Package — "Day in the Life" Dataset | XL |
| SENTINEL | SEN-019 | Full Regression Suite | L |

### Sprint 20 — Hardening + Knowledge Validation

| Team | Ticket | Title | Est |
|------|--------|-------|-----|
| CORTEX | CTX-024 | Confidence Calibration Engine | L |
| LENS | LENS-023 | Onboarding Flow (tutorial, walkthrough) | L |
| ATLAS | ATL-020 | SME Validation Protocol — Expert Review | XL |
| SENTINEL | SEN-020 | Production Readiness Checklist + Sign-Off | M |

---

## Full Backlog by Team

### Team CORTEX (CTX)

| Ticket | Title | Sprint | Blocked By | Est |
|--------|-------|--------|-----------|-----|
| CTX-017 | ReasoningEvent Ingestion + Delta Generation | 1 | — | L |
| CTX-005 | Artifact Ownership + Judgment Classification | 2 | — | M |
| CTX-006 | HITL Routing Logic | 3 | CTX-005 | L |
| CTX-018 | Contribution Tracking Store | 4 | CTX-017 | M |
| CTX-008 | Enhanced Audit Trail | 5 | CTX-005 | M |
| CTX-007 | Review Cycle Enforcement | 6 | CTX-005 | S |
| CTX-009 | Pattern Consolidation / Reconciler | 7 | CTX-001 | L |
| CTX-019 | Semantic Search over Patterns + Evidence | 8 | — | L |
| CTX-041 | Unify Reasoning Paths — YAML Rules + JudgmentPatterns | 9 | CTX-001 ✓, CTX-019 ✓ | M |
| CTX-010 | Agent Mode Enforcement | 12 | CTX-001, CTX-002 | L |
| CTX-011 | Traversal Depth + Mission Scope Checking | 13 | CTX-010 | M |
| CTX-020 | LLM-Assisted Pattern Summarization | 11 | — | L |
| CTX-021 | Cross-Brand Pattern Transfer | 12 | — | L |
| CTX-012 | SQLite/PostgreSQL Persistence Layer | 10 | — | XL |
| CTX-013 | Neo4j Graph Persistence | 14 | CTX-012 | XL |
| CTX-014 | Redis Cache Integration | 15 | CTX-012 | M |
| CTX-022 | NLP Extraction Pipeline | 16 | — | L |
| CTX-015 | Multi-Tenant Architecture | 17 | CTX-012 | XL |
| CTX-023 | Time-Series Pattern Detection | 18 | — | L |
| CTX-016 | Performance Benchmarks (<50ms p95) | 19 | — | M |
| CTX-024 | Confidence Calibration Engine | 20 | — | L |
| CTX-025 | Process Trace Model — Session Timing + Step Durations | — | CTX-017 ✓ | M |
| CTX-026 | Decision-Time Context Snapshot — Market State Capture | — | CTX-005 | M |
| CTX-027 | Canonical Procedure Extraction — Cross-Session Mining | — | CTX-025 | L |
| CTX-028 | Expert Profile Model — Composite SME Profiles | — | CTX-018 | L |
| CTX-029 | Direct Contribution API (EPIC-006: Expert Mode) | — | CTX-006 ✓ | M |
| CTX-030 | File Upload Endpoint + Parser Registry (EPIC-007: Ingestion) | — | DEC-012 | L |
| CTX-031 | Document Parser Implementations (EPIC-007) | — | CTX-030 | L |
| CTX-032 | Extraction Pipeline Orchestrator (EPIC-007) | — | CTX-033, CTX-030 | L |
| CTX-033 | LLM Integration Framework (EPIC-008: Agentic AI) | — | DEC-012 | M |
| CTX-034 | Entity Extraction Agent (EPIC-008) | — | CTX-033 | L |
| CTX-035 | Relationship Extraction Agent (EPIC-008) | — | CTX-033 | L |
| CTX-036 | Entity Resolution Agent (EPIC-008) | — | CTX-033 | M |
| CTX-037 | Smart Linking Agent (EPIC-008) | — | CTX-034, CTX-036 | M |
| CTX-038 | Game Pipeline AI Enhancement (EPIC-008) | — | CTX-034 | L |
| CTX-039 | Confidence Calibration Enhancement (EPIC-008) | — | CTX-033 | M |
| CTX-040 | MCP Server — Tool Exposure for AI Agents | — | CTX-010 | L |

### Team LENS (LENS)

| Ticket | Title | Sprint | Blocked By | Est |
|--------|-------|--------|-----------|-----|
| LENS-012 | Design System + Persona Modes | 1 | — | L |
| LENS-011 | Game Session Submission API + Hook | 2 | CTX-017 | M |
| LENS-004 | HITL Routing Endpoints + Audit Export API | 3 | CTX-006 | M |
| LENS-005 | Curator Dashboard MVP | 4 | LENS-004, LENS-012 | XL |
| LENS-013 | SME Impact Dashboard | 5 | CTX-018, LENS-012 | L |
| LENS-014 | Intelligence Packet Viewer | 9 | LENS-012 | L |
| LENS-007 | Curator Graph Explorer | 7 | CTX-003, LENS-012 | L |
| LENS-015 | Progressive Disclosure Layers | 8 | LENS-014 | M |
| LENS-016 | Notification System | 12 | — | L |
| LENS-017 | Scenario Builder UI (Curator) | 13 | LENS-012 | XL |
| LENS-006 | Agent Traversal API Endpoints | 11 | CTX-010 | M |
| LENS-018 | Export & Reporting (CSV/PDF) | 12 | — | L |
| LENS-019 | Admin Panel | 13 | — | L |
| LENS-020 | Collaboration Features | 14 | — | L |
| LENS-021 | Real-Time Updates (WebSocket) | 15 | — | L |
| LENS-008 | RBAC Middleware + Auth Endpoints | 16 | CTX-012 | L |
| LENS-009 | Telemetry Dashboard UI | 17 | LENS-008 | L |
| LENS-022 | Mobile-Responsive SME Interface | 18 | LENS-012 | L |
| LENS-010 | End-to-End Demo Flow | 19 | ATL-019 | L |
| LENS-023 | Onboarding Flow (tutorial, walkthrough) | 20 | LENS-012 | L |
| LENS-024 | Question Sequence Analytics — Step Navigation Tracking | — | LENS-011 ✓ | M |
| LENS-025 | Expert Mode Toggle + Route (EPIC-006) | — | LENS-012 ✓ | M |
| LENS-026 | Direct Entity/Rule Editor UI (EPIC-006) | — | LENS-025, CTX-029 | L |
| LENS-027 | Scenario Authoring UI (EPIC-006) | — | LENS-025 | L |
| LENS-028 | Document Upload UI + Progress Tracking (EPIC-007) | — | CTX-030 | L |

### Team ATLAS (ATL)

| Ticket | Title | Sprint | Blocked By | Est |
|--------|-------|--------|-----------|-----|
| ATL-001 | Commercial Ontology Expansion — Full Value Chain | 1 | — | L |
| ATL-002 | Oncology Therapeutic Area — Deep Taxonomy | 2 | ATL-001 | L |
| ATL-003 | Scenario Library v1 — 10 Oncology Scenarios | 3 | ATL-002 | XL |
| ATL-004 | Market Access Domain — Payer/Formulary Taxonomy | 4 | ATL-001 | L |
| ATL-005 | Gold Set Expansion — 5 Scenarios per TA | 5 | ATL-003 | L |
| ATL-006 | Immunology TA — Taxonomy + Scenarios | 6 | ATL-001 | L |
| ATL-007 | CNS Therapeutic Area — Taxonomy + Scenarios | 7 | ATL-001 | L |
| ATL-008 | Competitive Intelligence Domain | 8 | ATL-001 | L |
| ATL-009 | Cardiovascular + Rare Disease TAs | 9 | ATL-001 | L |
| ATL-010 | Inference Rule Library v1 — 50 Cross-TA Rules | 10 | ATL-004 | XL |
| ATL-011 | Evidence Corpus v1 — 100 Evidence Items | 11 | ATL-010 | XL |
| ATL-012 | Supply Chain + Manufacturing Domains | 12 | ATL-001 | L |
| ATL-013 | Launch Playbook Ontology | 13 | ATL-001 | L |
| ATL-014 | Respiratory + Metabolic TAs | 14 | ATL-001 | L |
| ATL-015 | Cross-Functional Playbooks | 15 | ATL-001 | L |
| ATL-016 | Pharma Metrics Ontology — 200+ Definitions | 16 | ATL-001 | XL |
| ATL-017 | Regulatory + Pharmacovigilance Domain | 17 | ATL-001 | L |
| ATL-018 | Regional Market Archetypes (US, EU5, JP, CN) | 18 | ATL-001 | L |
| ATL-019 | Demo Data Package — "Day in the Life" Dataset | 19 | ATL-003, ATL-011 | XL |
| ATL-020 | SME Validation Protocol — Expert Review | 20 | ATL-019 | XL |
| ATL-021 | Auto-Scenario Generation from Session Data | — | ATL-003, CTX-025 | L |
| ATL-022 | Controlled Vocabulary Registry — Terminology Governance | — | ATL-001 ✓ | M |
| ATL-023 | Ingestion Prompt Templates per TA (EPIC-007) | — | ATL-003 | M |
| ATL-024 | Pharma Domain Prompt Library (EPIC-008) | — | CTX-033 | L |

### Team SENTINEL (SEN)

| Ticket | Title | Sprint | Blocked By | Est |
|--------|-------|--------|-----------|-----|
| SEN-001 | Quality Gate Infrastructure (CI, linting, coverage) | 1 | — | M |
| SEN-002 | Automated Anti-Slop Checker | 2 | SEN-001 | M |
| SEN-003 | Architecture Review (Phase 2.5 code) | 3 | — | S |
| SEN-004 | Integration Test Coverage Audit + Gap Report | 4 | — | M |
| SEN-005 | Performance Baseline | 5 | — | M |
| SEN-006 | Security Review (OWASP top 10) | 6 | — | M |
| SEN-007 | Architecture Decision Records (ADR-001→010) | 7 | — | M |
| SEN-008 | E2E Smoke Test Suite | 8 | — | L |
| SEN-009 | Load Testing Framework | 9 | — | M |
| SEN-010 | Dependency Audit + Vulnerability Scan | 10 | — | S |
| SEN-011 | API Contract Testing (OpenAPI validation) | 11 | — | M |
| SEN-012 | Code Coverage Gate (80%+ enforcement) | 12 | SEN-001 | M |
| SEN-013 | Database Migration Testing Framework | 13 | — | M |
| SEN-014 | Data Migration Verification | 14 | SEN-013 | L |
| SEN-015 | Chaos Testing | 15 | — | L |
| SEN-016 | Accessibility Audit (WCAG 2.1 AA) | 16 | — | M |
| SEN-017 | Multi-Tenant Isolation Testing | 17 | — | L |
| SEN-018 | Performance Regression Suite | 18 | SEN-005 | M |
| SEN-019 | Full Regression Suite | 19 | SEN-008 | L |
| SEN-020 | Production Readiness Checklist + Sign-Off | 20 | — | M |
| SEN-021 | PII/PHI Redaction Layer | — | — | M |

---

## Estimation Key

| Code | Meaning | Rough Scope |
|------|---------|-------------|
| S | Small | 1-2 functions, < 50 new lines |
| M | Medium | 3-5 functions, 50-150 new lines |
| L | Large | Full feature, 150-300 new lines, multiple files |
| XL | Extra Large | Major subsystem, 300+ lines, architecture impact |

---

## Velocity Tracking

| Sprint | Team | Tickets Completed | Points | Notes |
|--------|------|-------------------|--------|-------|
| Phase 2.1 | CORTEX | CTX-001, 002, 003, 004 | 4 (M+M+M+S) | All P0 structural gaps closed |
| Phase 2.1 | LENS | LENS-001, 002, 003 | 3 (L+XL+S) | API tests + Game MVP + server decomp |
| Sprint 1 | CORTEX | CTX-017 | 1 (L) | ReasoningEvent ingestion pipeline |
| Sprint 1 | LENS | LENS-012 | 1 (L) | Design system + persona modes |
| Sprint 1 | ATLAS | ATL-001 | 1 (L) | Commercial ontology 3→12 rules, 4→15 entities |
| Sprint 1 | SENTINEL | SEN-001, SEN-002 | 2 (M+M) | CI pipeline + AST slop checker |
| Sprint 2 | CORTEX | CTX-005 | 1 (M) | Artifact ownership + judgment classification (144 tests) |
| Sprint 2 | LENS | LENS-011 | 1 (M) | Game session submission API + hook |
| Sprint 2 | ATLAS | ATL-002 | 1 (L) | Oncology deep taxonomy (3 files, GOLD-005) |
| Sprint 2 | SENTINEL | SEN-002, SEN-003, SEN-004, SEN-005 | 4 (M+S+M+M) | Anti-slop + arch review + coverage audit + perf baseline |
| Sprint 3 | CORTEX | CTX-006 | 1 (L) | HITL routing logic, 10 new tests, routing matrix |
| Sprint 3 | LENS | LENS-004 | 1 (M) | HITL endpoints + audit export API (167 tests) |
| Sprint 3 | SENTINEL | SEN-006, SEN-007 | 2 (M+M) | OWASP security review + ADR formalization (12 files) |
| Sprint 3 | ATLAS | ATL-003 | 1 (XL) | 10 scenarios, 5 gold sets, 180 tests passing |
| Sprint 4 | CORTEX | CTX-018 | 1 (M) | ContributionStore — 82 tests, 6 public methods |
| Sprint 4 | LENS | LENS-005 | 1 (XL) | Curator Dashboard — 9 files, /curator route, 189 tests |
| Sprint 4 | SENTINEL | SEN-008 | 1 (L) | E2E Smoke Tests — 9 tests, full pipeline coverage |
| Sprint 4 | ATLAS | ATL-004 | 1 (L) | Market Access — 4 rules, 3 gold sets, 192 tests |
| Sprint 5 | CORTEX | CTX-008 | 1 (M) | Enhanced Audit Trail — 11 new tests, 93 total passing |
| Sprint 5 | LENS | LENS-013 | 1 (L) | SME Impact Dashboard — 14 files, /sme-dashboard route, 209 tests |
| Sprint 6 | CORTEX | CTX-007 | 1 (S) | Review Cycle Enforcement — 9 new tests, 102 total passing |
| Sprint 7 | CORTEX | CTX-009 | 1 (L) | Pattern Consolidation — 13 new tests, 115 total passing |
| Sprint 8 | CORTEX | CTX-019 | 1 (L) | Semantic Search — 11 new tests, 148 total passing |
| Sprint 8 | LENS | — | 0 | LENS-014 spec written (IN_PROGRESS:SPEC), carried to Sprint 9 |
| Sprint 8 | ATLAS | ATL-005 | 1 (L) | Gold Set Expansion — 5 new gold sets, 19/19 rule coverage |
| Sprint 8 | SENTINEL | — | 0 | Idle (SEN-009 queued for Sprint 9) |

---

## WIP Limits

| Column | Max Items per Team |
|--------|-------------------|
| IN_PROGRESS | 1 |
| REVIEW | 2 |

One ticket in progress per team at a time. No multitasking. Finish before starting.

---

## Cross-Team Dependencies (Visual)

```
Phase 2.1 (DONE):
  CTX-001 ──→ CTX-003 ✓
  LENS-001 ──→ LENS-002 ✓, LENS-003 ✓

Sprint 1 (DONE — all unblocked):
  CTX-017 ✓ ──→ LENS-011 ✓
              ──→ CTX-018 (Sprint 4)
              ──→ CTX-025 (Process Trace — backlog)
  LENS-012 ✓ ──→ LENS-005 (Sprint 4)
              ──→ LENS-013 (Sprint 5)
              ──→ LENS-014 (Sprint 6)
              ──→ LENS-007 (Sprint 7)
              ──→ LENS-017 (Sprint 10)
              ──→ LENS-022 (Sprint 18)
              ──→ LENS-023 (Sprint 20)
  ATL-001 ✓  ──→ ATL-002 ✓ ──→ ATL-003 (Sprint 3, NOW UNBLOCKED)
              ──→ ATL-004,006-009,012-018 (Sprints 4+)
  SEN-001 ✓  ──→ SEN-002 ✓, SEN-012 (Sprint 12)
  SEN-002 ✓  (delivered early)
  SEN-003 ✓  (pulled forward, architecture review complete)
  SEN-004 ✓  (pulled forward, coverage audit complete)
  SEN-005 ✓  ──→ SEN-018 (regression needs baseline)
  LENS-011 ✓ ──→ LENS-024 (question sequence analytics — backlog)

Sprint 2-3:
  CTX-005 ✓ ──→ CTX-006 ✓ ──→ LENS-004 ✓
             ──→ CTX-007 (Sprint 6)
             ──→ CTX-008 ✓
             ──→ CTX-026 (Decision-Time Context Snapshot — backlog)
  SEN-006 ✓ (security review — PASS_WITH_FINDINGS)
  SEN-007 ✓ (ADR formalization — 12 files, all 11 decisions documented)

Sprint 4-5:
  LENS-004 ✓ ──→ LENS-005 (Sprint 4, IN_PROGRESS)
  CTX-018 ✓  ──→ LENS-013 (Sprint 5, NOW UNBLOCKED)
  ATL-003 ✓  ──→ ATL-005 (Sprint 5), ATL-023 (Ingestion Prompts)

Sprint 7-8:
  CTX-009 ✓ (consolidation done)
  CTX-019 ✓ (semantic search done)

Sprint 9 (Reasoning Pivot — rebalanced 2026-02-17):
  CTX-041 (Unify Reasoning Paths) — NEW ticket, bridges Path A + Path B
    depends: CTX-001 ✓, CTX-019 ✓
    enables: CTX-010, CTX-020 (learned patterns available to engine)
  LENS-014 (Intelligence Packet Viewer) — pulled forward from Sprint 6
  ATL-006 (Immunology TA) — pulled forward from Sprint 6
  SEN-009 (Load Testing Framework) — on schedule

Sprint 12+ (deferred from Sprint 9):
  CTX-010 ──→ CTX-011 ──→ LENS-006
  LENS-016 (Notifications)

Sprint 13-15 (Persistence):
  CTX-012 ──→ CTX-013 (Sprint 14)
           ──→ CTX-014 (Sprint 15)
           ──→ LENS-008 (Sprint 16) ──→ LENS-009 (Sprint 17)
           ──→ CTX-015 (Sprint 17)

ATLAS chain:
  ATL-001 → ATL-002 → ATL-003 → ATL-005 (gold sets reference scenarios)
  ATL-004 → ATL-010 (rules reference domain taxonomy)
  ATL-010 → ATL-011 (evidence references rules)
  ATL-003 + ATL-011 → ATL-019 (demo data needs scenarios + evidence)
  ATL-019 → ATL-020 (validation needs demo data)
  ATL-019 → LENS-010 (demo flow needs demo data)

SENTINEL chain:
  SEN-005 ✓ → SEN-018 (regression needs baseline)
  SEN-008 → SEN-019 (full regression includes smoke)
  SEN-013 → SEN-014 (migration verify needs framework)

CogniMesh-derived (unscheduled):
  CTX-010 → CTX-040 (MCP Server — expose tools for AI agents)
  SEN-021 (PII/PHI Redaction — gate before production, no blockers)

Research-derived (unscheduled):
  CTX-025 (Process Trace) → CTX-027 (Canonical Procedure Extraction)
  CTX-005 ✓ → CTX-026 (Decision-Time Context Snapshot)
  CTX-018 → CTX-028 (Expert Profile Model)
  LENS-011 ✓ → LENS-024 (Question Sequence Analytics)
  ATL-003 + CTX-025 → ATL-021 (Auto-Scenario Generation)
  ATL-001 ✓ → ATL-022 (Controlled Vocabulary Registry)

EPIC-006 (Expert Mode):
  LENS-012 ✓ → LENS-025 (Expert Mode Toggle)
  CTX-006 ✓ → CTX-029 (Direct Contribution API)
  LENS-025 + CTX-029 → LENS-026 (Entity/Rule Editor)
  LENS-025 → LENS-027 (Scenario Authoring)

EPIC-007 (Document Ingestion):
  DEC-012 → CTX-030 (Upload + Parser Registry)
  CTX-030 → CTX-031 (Parser Implementations)
  CTX-033 + CTX-030 → CTX-032 (Pipeline Orchestrator)
  CTX-030 → LENS-028 (Upload UI)
  ATL-003 → ATL-023 (Ingestion Prompts)

EPIC-008 (Agentic AI):
  DEC-012 → CTX-033 (LLM Framework)
  CTX-033 → CTX-034 (Entity Extraction) → CTX-038 (Game AI Enhancement)
  CTX-033 → CTX-035 (Relationship Extraction)
  CTX-033 → CTX-036 (Entity Resolution)
  CTX-034 + CTX-036 → CTX-037 (Smart Linking)
  CTX-033 → CTX-039 (Confidence Calibration)
  CTX-033 → ATL-024 (Pharma Prompt Library)
```

---

## Research-Derived Backlog (Unscheduled)

> Source: Talisman article analysis + raw notes gap analysis (2026-02-01)
> These tickets are prioritized but unscheduled. Slot into sprints during future planning.

### HIGH Priority

| Ticket | Title | Team | Blocked By | Est | Source |
|--------|-------|------|-----------|-----|--------|
| CTX-025 | Process Trace Model — Session Timing + Step Durations | CTX | CTX-017 ✓ | M | Talisman: PKO framework — distinguish abstract procedure from concrete execution |
| CTX-026 | Decision-Time Context Snapshot — Market State Capture | CTX | CTX-005 | M | Talisman: context at decision-time, not retrieval-time |
| CTX-018 | _(existing)_ Contribution Tracking Store — enhanced with accuracy-over-time | CTX | CTX-017 ✓ | M | Raw notes: "digital twin of SME", track who contributed what |

### MEDIUM Priority

| Ticket | Title | Team | Blocked By | Est | Source |
|--------|-------|------|-----------|-----|--------|
| CTX-027 | Canonical Procedure Extraction — Cross-Session Mining | CTX | CTX-025 | L | Talisman: extract canonical procedures from multiple concrete executions |
| LENS-024 | Question Sequence Analytics — Step Navigation Tracking | LENS | LENS-011 ✓ | M | Raw notes: "question sequence / intent detection" across sessions |
| CTX-028 | Expert Profile Model — Composite SME Profiles | CTX | CTX-018 | L | Raw notes: "digital twin of SME" — build composite expert model |

### LOWER Priority

| Ticket | Title | Team | Blocked By | Est | Source |
|--------|-------|------|-----------|-----|--------|
| ATL-021 | Auto-Scenario Generation from Session Data | ATL | ATL-003, CTX-025 | L | Raw notes: use real session data to generate new scenarios |
| ATL-022 | Controlled Vocabulary Registry — Terminology Governance + MeSH/SNOMED Alignment | ATL | ATL-001 ✓ | M | Talisman + CogniMesh FR-03: vocabulary control + external taxonomy mapping |

### CogniMesh-Derived (HIGH Priority)

> Source: CogniMesh PRD analysis (2026-02-02, `product_management/reference_cognimesh_prd.md`)

| Ticket | Title | Team | Blocked By | Est | Source |
|--------|-------|------|-----------|-----|--------|
| CTX-040 | MCP Server — Tool Exposure for AI Agents | CTX | CTX-010 | L | CogniMesh FR-09: expose patterns, guardrails, intelligence packets as MCP tools for Claude/GPT agents |
| SEN-021 | PII/PHI Redaction Layer | SEN | — | M | CogniMesh FR-13: auto-detect and mask sensitive patient data before LLM context. Gate before production. |

**Spec notes for existing tickets (no new tickets needed):**
- **CTX-031** (Document Parsers): Add parent-child chunking strategy + layout-aware extraction (CogniMesh FR-02)
- **CTX-023** (Time-Series Patterns): Add formal temporal operators — YTD, MoM, trailing windows (CogniMesh FR-08)
- **ATL-016** (Pharma Metrics Ontology): Add metrics governance via delta model — metrics-as-code (CogniMesh FR-07)
- **CTX-030** (Upload Endpoint): Add Croissant 1.1 metadata envelope for ingested document provenance (CogniMesh FR-01)

---

## EPIC Backlog (New Capabilities — Unscheduled)

> Source: User requirements analysis (2026-02-01)
> EPICs: `product_management/epics/EPIC-006_expert_mode.md`, `EPIC-007_document_ingestion.md`, `EPIC-008_agentic_ai.md`
> Gated by DEC-012 (new dependencies approval) for EPIC-007 and EPIC-008.

### EPIC-006: Expert Mode — Direct Knowledge Contribution (4 tickets)

| Ticket | Title | Team | Blocked By | Est | Priority |
|--------|-------|------|-----------|-----|----------|
| LENS-025 | Expert Mode Toggle + Route | LENS | LENS-012 ✓ | M | HIGH |
| CTX-029 | Direct Contribution API | CTX | CTX-006 ✓ | M | HIGH |
| LENS-026 | Direct Entity/Rule Editor UI | LENS | LENS-025, CTX-029 | L | HIGH |
| LENS-027 | Scenario Authoring UI | LENS | LENS-025 | L | MEDIUM |

**Recommended Sprint Slot:** 5-6 (after Curator Dashboard MVP foundations)

### EPIC-007: Document Ingestion Pipeline (5 tickets)

| Ticket | Title | Team | Blocked By | Est | Priority |
|--------|-------|------|-----------|-----|----------|
| CTX-030 | File Upload Endpoint + Parser Registry | CTX | DEC-012 | L | HIGH |
| CTX-031 | Document Parser Implementations (8 formats) | CTX | CTX-030 | L | HIGH |
| CTX-032 | Extraction Pipeline Orchestrator | CTX | CTX-033, CTX-030 | L | HIGH |
| LENS-028 | Document Upload UI + Progress Tracking | LENS | CTX-030 | L | MEDIUM |
| ATL-023 | Ingestion Prompt Templates per TA | ATL | ATL-003 | M | MEDIUM |

**Recommended Sprint Slot:** 8-10 (after Agentic AI foundation)

### EPIC-008: Agentic AI Extraction & Curation Layer (9 tickets)

| Ticket | Title | Team | Blocked By | Est | Priority |
|--------|-------|------|-----------|-----|----------|
| CTX-033 | LLM Integration Framework | CTX | DEC-012 | M | **CRITICAL** |
| CTX-034 | Entity Extraction Agent | CTX | CTX-033 | L | HIGH |
| CTX-035 | Relationship Extraction Agent | CTX | CTX-033 | L | HIGH |
| CTX-036 | Entity Resolution Agent | CTX | CTX-033 | M | HIGH |
| CTX-037 | Smart Linking Agent | CTX | CTX-034, CTX-036 | M | MEDIUM |
| CTX-038 | Game Pipeline AI Enhancement | CTX | CTX-034 | L | HIGH |
| CTX-039 | Confidence Calibration Enhancement | CTX | CTX-033 | M | MEDIUM |
| ATL-024 | Pharma Domain Prompt Library | ATL | CTX-033 | L | HIGH |

**Recommended Sprint Slot:** 7-9 (foundational — blocks EPIC-007)

### Sequencing Summary

```
Sprint 5-6:  EPIC-006 (Expert Mode) — LENS-025, CTX-029, LENS-026
Sprint 7-8:  EPIC-008 foundation — CTX-033, CTX-034, CTX-036, ATL-024
Sprint 8-9:  EPIC-008 advanced — CTX-035, CTX-037, CTX-038, CTX-039
Sprint 9-10: EPIC-007 (Ingestion) — CTX-030, CTX-031, CTX-032, LENS-028
Sprint 10+:  LENS-027, ATL-023 (remaining Expert Mode + Ingestion items)
```

**Decision Gate:** DEC-012 must be approved before Sprint 7 for EPIC-007/008 work to begin.

---

_End of Board — Tech Lead_
