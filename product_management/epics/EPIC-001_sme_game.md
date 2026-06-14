# EPIC-001: SME Game & Judgment Capture

## Epic Summary

**As a** Subject Matter Expert  
**I want to** share my reasoning through a scenario-based game  
**So that** my judgment is captured without feeling like documentation work

## Business Value

- Bypasses "KM tax" that kills adoption
- Captures implicit reasoning that ontologies miss
- Generates 10+ artifacts per 5-minute session
- Makes experts feel heard, not harvested

## Epic Scope

### In Scope
- Scenario presentation UI
- Hypothesis selection flow
- Signal prioritization
- "Change my mind" capture
- Pattern recognition questions
- Common mistake capture
- Action recommendation flow
- Confidence calibration

### Out of Scope (Future)
- Multiplayer game mode
- Competitive leaderboards
- Mobile app

---

## User Stories

### US-001: View Scenario Card
**As a** SME  
**I want to** see a crisp scenario description  
**So that** I can quickly understand the situation

**Acceptance Criteria:**
- [ ] Scenario shows brand, region, timeframe
- [ ] Key observation stated clearly (e.g., "Sales down 10%")
- [ ] National context provided (e.g., "National flat")
- [ ] Conflicting stakeholder views shown (Field vs Marketing)
- [ ] No data tables or jargon visible
- [ ] Load time < 2 seconds

**Story Points:** 3

---

### US-002: Select Primary Hypothesis
**As a** SME  
**I want to** pick my first instinct from clear options  
**So that** I can start the reasoning process quickly

**Acceptance Criteria:**
- [ ] Options: Commercial execution, Market access, Clinical/safety, Competitive, Too early
- [ ] Single-tap selection
- [ ] "Too early" is a valid and valued response
- [ ] Selection can be changed later
- [ ] Backend captures: hypothesis, priority, timestamp

**Story Points:** 2

---

### US-003: Prioritize Signals
**As a** SME  
**I want to** select which signals I'd check first  
**So that** the system learns my diagnostic approach

**Acceptance Criteria:**
- [ ] Options shown based on context (TA, lifecycle)
- [ ] Pick up to 2 signals
- [ ] Options include: NBRx, TRx, Decile, Payer changes, Field activity, Safety
- [ ] Backend captures: signal roles (validation, leading, disconfirming)

**Story Points:** 2

---

### US-004: Provide Disconfirming Logic
**As a** SME  
**I want to** explain what would change my mind  
**So that** the system learns my guardrails

**Acceptance Criteria:**
- [ ] Free-text input with examples shown
- [ ] Examples: "If NBRx flat but TRx drops", "If top deciles stable"
- [ ] Backend parses for: condition, would_suggest, would_rule_out
- [ ] NLP extracts potential entities/metrics

**Story Points:** 5

---

### US-005: Share Pattern Recognition
**As a** SME  
**I want to** indicate if I've seen this before  
**So that** the pattern gets appropriate confidence

**Acceptance Criteria:**
- [ ] Options: Often, Sometimes, Rarely, Never
- [ ] If Often/Sometimes: ask "How did it usually turn out?"
- [ ] Free-text for typical outcome
- [ ] Backend sets pattern frequency and prior

**Story Points:** 3

---

### US-006: Flag Common Mistakes
**As a** SME  
**I want to** share what people commonly get wrong  
**So that** the system creates guardrails

**Acceptance Criteria:**
- [ ] Free-text input
- [ ] Prompt: "What's the most common wrong conclusion?"
- [ ] Backend creates Guardrail delta
- [ ] Guardrail linked to scenario context

**Story Points:** 3

---

### US-007: Recommend Next Actions
**As a** SME  
**I want to** suggest what I'd do next week  
**So that** the system learns action templates

**Acceptance Criteria:**
- [ ] Options: Pull data, Ask access team, Shift field, Escalate, Wait, Do nothing
- [ ] Pick up to 2
- [ ] Backend creates ActionTemplate deltas
- [ ] Actions linked to hypothesis and context

**Story Points:** 2

---

### US-008: Calibrate Confidence
**As a** SME  
**I want to** indicate my confidence level  
**So that** the system learns confidence thresholds

**Acceptance Criteria:**
- [ ] Slider: 0% to 100%
- [ ] Haptic feedback on mobile
- [ ] Backend uses for pattern prior
- [ ] Calibrates persona-specific thresholds

**Story Points:** 2

---

### US-009: View Session Summary
**As a** SME  
**I want to** see acknowledgment of my input  
**So that** I feel my contribution was valuable

**Acceptance Criteria:**
- [ ] "Thanks - you helped improve [topic]"
- [ ] Optional: Show disagreement with peers
- [ ] Optional: Preview of impact on AI
- [ ] No ontology terms visible

**Story Points:** 2

---

## Backend Stories

### US-010: Create ReasoningEvent
**As a** system  
**I want to** capture all SME inputs into a structured ReasoningEvent  
**So that** the DeltaGenerator can create artifacts

**Acceptance Criteria:**
- [x] ReasoningEvent schema with brand profile, TA, lifecycle
- [x] Captures all SME inputs
- [x] Semantic capture for synonyms
- [x] Stored for audit

**Story Points:** 5 (DONE)

---

### US-011: Generate Deltas from Game
**As a** system  
**I want to** automatically generate deltas from a ReasoningEvent  
**So that** patterns/guardrails enter the review queue

**Acceptance Criteria:**
- [x] One session → 10+ deltas
- [x] Pattern delta (context-scoped)
- [x] Guardrail deltas (from mistakes)
- [x] Edge deltas (supports/contradicts)
- [x] Metric semantic deltas
- [x] Action template deltas

**Story Points:** 8 (DONE)

---

## Technical Tasks

| Task | Story | Estimate | Status |
|:---|:---|:---|:---|
| Design scenario card component | US-001 | 2d | 🔲 |
| Build hypothesis selection UI | US-002 | 1d | 🔲 |
| Build signal priority selector | US-003 | 1d | 🔲 |
| Build free-text input with NLP | US-004 | 3d | 🔲 |
| Build pattern recognition flow | US-005 | 1d | 🔲 |
| Build confidence slider | US-008 | 0.5d | 🔲 |
| Build session summary view | US-009 | 1d | 🔲 |
| ReasoningEvent schema | US-010 | 2d | ✅ |
| DeltaGenerator implementation | US-011 | 3d | ✅ |
| API: POST /game/session | - | 1d | 🔲 |
| API: POST /game/session/{id}/submit | - | 1d | 🔲 |

---

## Dependencies

- **Semantic Store** - For synonym extraction (DONE)
- **Delta Model** - For artifact creation (DONE)
- **Review Queue API** - For delta submission (DONE)

## Risks

| Risk | Mitigation |
|:---|:---|
| SME finds questions awkward | UX research with real SMEs |
| Free-text hard to parse | Start with structured options, enhance NLP later |
| Too many questions | A/B test shorter flows |
