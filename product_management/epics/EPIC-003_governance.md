# EPIC-003: Governance & Compliance Layer

## Epic Summary

**As a** compliance officer  
**I want to** ensure all AI reasoning is auditable and governed  
**So that** the organization can trust AI decisions

## Business Value

- Regulatory compliance (explainability requirements)
- Risk classification prevents unauthorized decisions
- Full audit trail for investigations
- Judgment type classification enables policy enforcement

## Epic Scope

### In Scope
- Artifact ownership and approval
- Judgment type classification
- Risk class enforcement
- Audit trail enhancement
- Review cycle tracking

### Out of Scope
- External compliance reporting
- Regulatory submission automation

---

## User Stories

### US-030: Define Artifact Ownership
**As a** administrator  
**I want to** assign owners to artifacts  
**So that** accountability is clear

**Acceptance Criteria:**
- [ ] Every artifact has owner field
- [ ] Every artifact has approver field
- [ ] approved_on timestamp tracked
- [ ] Owner can be team or individual

**Story Points:** 3

---

### US-031: Classify Judgment Type
**As a** curator  
**I want to** classify judgments by type  
**So that** appropriate governance applies

**Acceptance Criteria:**
- [ ] Types: empirical, causal_hypothesis, normative
- [ ] Normative requires justification
- [ ] Causal_hypothesis requires evidence
- [ ] Empirical can be auto-derived

**Story Points:** 3

---

### US-032: Enforce Risk Class
**As a** system  
**I want to** enforce risk class restrictions  
**So that** high-risk judgments require approval

**Acceptance Criteria:**
- [ ] Advisory: No restrictions
- [ ] Decision_support: HITL for normative
- [ ] Restricted: Always HITL, compliance review

**Story Points:** 5

---

### US-033: Route to HITL Queue
**As a** system  
**I want to** automatically route high-risk items  
**So that** humans review before activation

**Acceptance Criteria:**
- [ ] Level 2 (causal) → HITL queue
- [ ] Level 3 (normative) → HITL + compliance queue
- [ ] Blocked until approval
- [ ] SLA tracking for queue items

**Story Points:** 5

---

### US-034: Track Review Cycles
**As a** governance lead  
**I want to** track artifact refresh cycles  
**So that** stale judgments are reviewed

**Acceptance Criteria:**
- [ ] Default review cycle: 90 days
- [ ] Critical guardrails: 30 days
- [ ] Notification before expiry
- [ ] Auto-flag expired artifacts

**Story Points:** 3

---

### US-035: Enhanced Audit Trail
**As a** auditor  
**I want to** see full traversal details  
**So that** I can investigate any decision

**Acceptance Criteria:**
- [ ] mission_id on every entry
- [ ] persona on every entry
- [ ] client_id for multi-tenant
- [ ] traversal_id for path tracing
- [ ] evidence_used list
- [ ] guardrails_hit list

**Story Points:** 5

---

### US-036: Export Audit Logs
**As a** compliance officer  
**I want to** export audit logs  
**So that** I can analyze patterns and respond to inquiries

**Acceptance Criteria:**
- [ ] Export by mission
- [ ] Export by persona
- [ ] Export by date range
- [ ] Format: JSON or CSV

**Story Points:** 3

---

## Technical Tasks

| Task | Story | Estimate | Status |
|:---|:---|:---|:---|
| Add owner/approver to models | US-030 | 1d | 🔲 |
| Implement JudgmentType classification | US-031 | 2d | 🔲 |
| RiskClass enforcement logic | US-032 | 2d | 🔲 |
| HITL routing engine | US-033 | 3d | 🔲 |
| Review cycle scheduler | US-034 | 2d | 🔲 |
| AuditEntry schema extension | US-035 | 1d | 🔲 |
| Audit export API | US-036 | 1d | 🔲 |

---

## Governance Matrix

| Judgment Type | Risk Class | Approval |
|:---|:---|:---|
| Empirical | Advisory | Auto |
| Empirical | Decision_support | Auto |
| Causal | Advisory | Auto |
| Causal | Decision_support | HITL |
| Normative | Any | HITL + Compliance |

---

## Audit Entry Schema (Target)

```python
@dataclass
class AuditEntry:
    id: str
    timestamp: datetime
    action: str
    actor: str
    
    # Traversal context
    mission_id: str
    persona: str
    client_id: str
    traversal_id: str
    
    # What was accessed/used
    evidence_used: List[str]
    guardrails_hit: List[str]
    patterns_fired: List[str]
    
    # Decision trace
    confidence: float
    outcome: str
    halted: bool
    halt_reason: Optional[str]
```

---

## Dependencies

- **Delta Model** - For approval integration (DONE)
- **JudgmentStore** - For artifact storage (DONE)

## Risks

| Risk | Mitigation |
|:---|:---|
| Review bottleneck | Priority queues, SLAs |
| Over-classification | Start with advisory, escalate as needed |
| Audit data volume | Retention policies, archival |
