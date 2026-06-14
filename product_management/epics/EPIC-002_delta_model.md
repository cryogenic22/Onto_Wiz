# EPIC-002: Delta Model & Artifact Governance

## Epic Summary

**As a** platform administrator  
**I want to** manage all changes through a delta-first model  
**So that** every modification is auditable, reviewable, and reversible

## Business Value

- Every change is a proposal, not an overwrite
- Full audit trail for compliance
- HITL review for high-risk changes
- Blast radius estimation prevents cascading failures

## Epic Scope

### In Scope
- Delta creation and lifecycle
- Artifact types: Pattern, Guardrail, Action, Edge
- Review queue and approval workflow
- Promotion pipeline to graph
- Conflict detection

### Out of Scope
- Automated approval (always HITL for now)
- Rollback automation

---

## User Stories

### US-020: Propose Delta
**As a** system or curator  
**I want to** create a proposed delta  
**So that** changes enter the review queue

**Acceptance Criteria:**
- [x] Delta has type, content, confidence, evidence_pointers
- [x] Blast radius estimated automatically
- [x] Impacted missions and personas tracked
- [x] Status starts as PROPOSED

**Story Points:** 3 (DONE)

---

### US-021: View Delta Queue
**As a** reviewer  
**I want to** see pending deltas  
**So that** I can prioritize my review

**Acceptance Criteria:**
- [x] Filter by status (proposed, approved, rejected)
- [x] Filter by type (pattern, guardrail, edge)
- [x] Sort by blast radius (high first)
- [x] Show source (sme_game, auto_derive, manual)

**Story Points:** 3 (DONE)

---

### US-022: Approve Delta
**As a** reviewer  
**I want to** approve a delta  
**So that** it can be promoted to the graph

**Acceptance Criteria:**
- [x] Approval sets status to APPROVED
- [x] Records approver and timestamp
- [x] Optional: require justification

**Story Points:** 2 (DONE)

---

### US-023: Reject Delta
**As a** reviewer  
**I want to** reject a delta with reason  
**So that** the proposer understands why

**Acceptance Criteria:**
- [x] Rejection sets status to REJECTED
- [x] Reason stored in audit
- [x] Notification to proposer (future)

**Story Points:** 2 (DONE)

---

### US-024: Promote Delta to Graph
**As a** system  
**I want to** promote approved deltas to the reasoning graph  
**So that** they affect AI agent behavior

**Acceptance Criteria:**
- [x] Promotion creates active artifacts
- [x] Delta status changes to PROMOTED
- [ ] Governance payload preserved
- [ ] Scope payload preserved
- [ ] Conflict detection before promotion

**Story Points:** 5 (PARTIAL)

---

### US-025: Detect Conflicts
**As a** system  
**I want to** detect conflicting deltas  
**So that** reviewers can resolve them

**Acceptance Criteria:**
- [ ] Detect canonical ID collisions
- [ ] Detect scope overlap
- [ ] Detect edge contradictions
- [ ] Flag for human review

**Story Points:** 5

---

### US-026: Track Blast Radius
**As a** system  
**I want to** estimate delta impact  
**So that** high-risk changes get extra review

**Acceptance Criteria:**
- [x] LOW: Regional/context-specific
- [x] MEDIUM: TA-wide or persona-wide
- [x] HIGH: Global patterns
- [x] CRITICAL: Guardrails or compliance-related

**Story Points:** 3 (DONE)

---

## Technical Tasks

| Task | Story | Estimate | Status |
|:---|:---|:---|:---|
| Delta schema definition | US-020 | 1d | ✅ |
| DeltaStore implementation | US-020 | 2d | ✅ |
| API: POST /deltas | US-020 | 0.5d | ✅ |
| API: GET /deltas | US-021 | 0.5d | ✅ |
| API: POST /deltas/{id}/approve | US-022 | 0.5d | ✅ |
| API: POST /deltas/{id}/reject | US-023 | 0.5d | ✅ |
| PromotionPipeline base | US-024 | 2d | ✅ |
| Governance preservation | US-024 | 1d | 🔲 |
| Conflict detection | US-025 | 3d | 🔲 |
| Blast radius calculation | US-026 | 1d | ✅ |

---

## Artifact Types

| Type | Description | Blast Radius Default |
|:---|:---|:---|
| `PROPOSED_PATTERN` | JudgmentPattern delta | MEDIUM |
| `PROPOSED_GUARDRAIL` | Guardrail delta | HIGH |
| `PROPOSED_EDGE` | Graph edge delta | LOW |
| `PROPOSED_ENTITY` | Graph node delta | MEDIUM |
| `PROPOSED_MAPPING` | Metric semantics | LOW |
| `PROPOSED_ACTION` | ActionTemplate | LOW |

---

## API Endpoints (Implemented)

| Endpoint | Method | Description | Status |
|:---|:---|:---|:---|
| `/deltas` | POST | Create proposed delta | ✅ |
| `/deltas` | GET | List/filter deltas | ✅ |
| `/deltas/{id}/approve` | POST | Approve delta | ✅ |
| `/deltas/{id}/reject` | POST | Reject with reason | ✅ |
| `/deltas/promote` | POST | Promote approved | ✅ |

---

## Dependencies

- **GraphStore** - For promotion target (DONE)
- **JudgmentStore** - For artifact storage (DONE)

## Risks

| Risk | Mitigation |
|:---|:---|
| Review queue backlog | Priority by blast radius |
| Conflict resolution complexity | Start with detection, manual resolution |
