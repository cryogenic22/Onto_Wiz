# EPIC-004: Bounded Agent Traversal

## Epic Summary

**As a** AI agent  
**I want to** traverse the reasoning graph with guardrails  
**So that** I produce safe, confident, and auditable outputs

## Business Value

- Prevents hallucination and overclaims
- Confidence-based halting avoids bad recommendations
- Agent modes prevent unauthorized actions
- Full trace for debugging and audit

## Epic Scope

### In Scope
- Agent mode enforcement
- Hard stops (confidence, conflict, evidence)
- Traversal policy enforcement
- Intelligence packet generation

### Out of Scope
- Agent implementation (that's the AI team)
- Natural language generation

---

## User Stories

### US-040: Enforce Agent Modes
**As a** system  
**I want to** enforce agent operation modes  
**So that** agents can't exceed their authorization

**Acceptance Criteria:**
- [ ] `explore`: Read-only, no recommendations
- [ ] `apply`: Can use patterns, no graph changes
- [ ] `recommend`: Can suggest actions
- [ ] `explain`: Can trace reasoning

**Story Points:** 3

---

### US-041: Halt on Low Confidence
**As a** agent  
**I want to** halt when confidence is too low  
**So that** I don't make uncertain claims

**Acceptance Criteria:**
- [x] ConfidenceEngine computes value
- [ ] Halt if confidence < 0.55
- [ ] Return halt reason to caller
- [ ] Log in audit trail

**Story Points:** 3

---

### US-042: Halt on High Conflict
**As a** agent  
**I want to** halt when evidence conflicts  
**So that** I don't make contradictory claims

**Acceptance Criteria:**
- [x] Conflict ratio computed
- [ ] Halt if conflict_ratio > 0.4
- [ ] Return competing hypotheses
- [ ] Suggest what would resolve

**Story Points:** 3

---

### US-043: Halt on Missing Evidence
**As a** agent  
**I want to** halt when required evidence is missing  
**So that** I don't claim without basis

**Acceptance Criteria:**
- [x] Patterns specify required_evidence
- [ ] Check evidence availability
- [ ] Halt if missing
- [ ] List what's needed

**Story Points:** 3

---

### US-044: Halt on Guardrail Violation
**As a** agent  
**I want to** halt when a guardrail blocks my path  
**So that** I don't make prohibited claims

**Acceptance Criteria:**
- [ ] Guardrail.is_violated() implemented
- [ ] blocks_drivers checked
- [ ] Halt and escalate
- [ ] Explain why blocked

**Story Points:** 5

---

### US-045: Enforce Traversal Depth
**As a** system  
**I want to** limit traversal depth  
**So that** agents don't explore infinitely

**Acceptance Criteria:**
- [ ] max_traversal_depth configurable
- [ ] Count edges traversed
- [ ] Halt at limit
- [ ] Return partial results

**Story Points:** 2

---

### US-046: Mission Scope Checking
**As a** agent  
**I want to** stay within mission scope  
**So that** I don't access unauthorized areas

**Acceptance Criteria:**
- [ ] TraversalPolicy defines allowed_missions
- [ ] Check scope on each node access
- [ ] Halt if out of scope
- [ ] Log scope violations

**Story Points:** 3

---

### US-047: Generate Intelligence Packet
**As a** agent  
**I want to** produce a structured output  
**So that** downstream systems can use my reasoning

**Acceptance Criteria:**
- [x] IntelligencePacket schema defined
- [x] Drivers with confidence
- [x] Evidence used
- [x] Actions recommended
- [x] Full trace included

**Story Points:** 5 (DONE)

---

## Technical Tasks

| Task | Story | Estimate | Status |
|:---|:---|:---|:---|
| AgentMode enum and validation | US-040 | 1d | 🔲 |
| Confidence halt logic | US-041 | 0.5d | 🔲 |
| Conflict halt logic | US-042 | 0.5d | 🔲 |
| Evidence check logic | US-043 | 1d | 🔲 |
| Guardrail.is_violated() v2 | US-044 | 2d | 🔲 |
| Depth tracking | US-045 | 0.5d | 🔲 |
| Scope enforcement | US-046 | 1d | 🔲 |
| IntelligencePacket builder | US-047 | 2d | ✅ |

---

## Hard Stop Matrix

| Condition | Threshold | Action |
|:---|:---|:---|
| Confidence | < 0.55 | Halt, explain uncertainty |
| Conflict ratio | > 0.4 | Halt, show competing |
| Missing evidence | Required type absent | Halt, list needed |
| Guardrail violation | Any | Halt, escalate |
| Depth exceeded | > max_depth | Halt, partial results |
| Scope violation | Out of mission | Halt, log |

---

## TraversalPolicy Schema

```python
@dataclass
class TraversalPolicy:
    allowed_modes: List[AgentMode]
    max_traversal_depth: int = 10
    
    # Hard stops
    min_confidence_threshold: float = 0.55
    max_conflict_ratio: float = 0.4
    require_evidence: bool = True
    
    # Scope
    allowed_missions: List[str] = field(default_factory=list)
    allowed_risk_class: RiskClass = RiskClass.DECISION_SUPPORT
    
    # Restrictions
    can_create_edges: bool = False
    only_approved_artifacts: bool = True
```

---

## Dependencies

- **ConfidenceEngine** - For confidence computation (DONE)
- **Guardrails** - For violation checking (PARTIAL)
- **Evidence** - For availability checking (DONE)

## Risks

| Risk | Mitigation |
|:---|:---|
| Too many halts | Tune thresholds based on telemetry |
| Agents bypass checks | Enforce in API layer, not just client |
| Performance overhead | Cache pattern matches |
