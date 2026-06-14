# EPIC-006: Expert Mode — Direct Knowledge Contribution

## Epic Summary

**As a** power user or domain expert
**I want to** contribute knowledge directly without going through the gamified flow
**So that** I can efficiently update entities, rules, scenarios, and artifacts when I already know what needs to change

## Business Value

- Removes friction for repeat contributors who find the 9-step game redundant
- Enables bulk knowledge contribution from domain leads
- Supports scenario authoring by ontology curators
- Allows direct artifact editing for corrections and refinements
- Complements EPIC-001 (game) — two input surfaces for different user types

## Epic Scope

### In Scope
- Expert Mode toggle (game mode ↔ expert mode)
- Direct entity creation/editing forms
- Direct rule/pattern authoring
- Scenario creation and editing UI
- Artifact annotation and enrichment
- Direct contribution API (non-game delta creation)
- All contributions still flow through Delta model (DEC-001)

### Out of Scope (Future)
- Bulk import UI (covered by EPIC-007)
- LLM-assisted form completion (covered by EPIC-008)
- Collaborative editing (multi-user simultaneous)

---

## User Stories

### US-060: Toggle Between Game and Expert Mode
**As a** SME
**I want to** switch between game mode and expert mode
**So that** I can use the approach that fits my current task

**Acceptance Criteria:**
- [ ] Persistent toggle in the UI header/navigation
- [ ] PersonaMode extends to 'sme' | 'curator' | 'expert'
- [ ] Expert mode shows structured forms instead of game flow
- [ ] Mode preference remembered across sessions (localStorage)
- [ ] Both modes produce deltas through the same pipeline

**Story Points:** 3

---

### US-061: Direct Entity Contribution
**As an** expert
**I want to** create or edit ontology entities directly
**So that** I can add missing concepts without playing a scenario

**Acceptance Criteria:**
- [ ] Form for entity creation: name, type, attributes, relationships
- [ ] Entity types: Brand, Account, Signal, Biomarker, Indication, Metric
- [ ] Auto-suggest existing entities to prevent duplicates
- [ ] Creates PROPOSED_ENTITY delta (enters review queue)
- [ ] Can propose edits to existing entities (creates modification delta)

**Story Points:** 5

---

### US-062: Direct Rule/Pattern Authoring
**As an** expert
**I want to** author inference rules and judgment patterns
**So that** I can encode knowledge that doesn't fit a scenario context

**Acceptance Criteria:**
- [ ] Form for rule creation: conditions (tags), conclusion, confidence range
- [ ] Preview: shows which existing scenarios would fire this rule
- [ ] Creates PROPOSED_PATTERN delta
- [ ] Can propose guardrails directly (condition + what it blocks)
- [ ] Validation: rule must reference at least one existing entity type

**Story Points:** 5

---

### US-063: Scenario Authoring
**As an** expert or curator
**I want to** create and edit scenarios
**So that** I can expand the scenario library without ATLAS team involvement

**Acceptance Criteria:**
- [ ] Form follows scenario YAML schema: id, name, description, TA, indication, brand_context, trigger_signal
- [ ] Live validation against existing ontology entities
- [ ] Preview: shows which rules would fire for this scenario
- [ ] Export to YAML for gold set testing
- [ ] Does NOT modify ontology files directly — creates proposal for review

**Story Points:** 5

---

### US-064: Artifact Annotation
**As an** expert
**I want to** annotate existing artifacts with context, evidence, or corrections
**So that** the knowledge base is refined iteratively

**Acceptance Criteria:**
- [ ] Add notes/context to any existing pattern, guardrail, or entity
- [ ] Link evidence items to artifacts
- [ ] Propose confidence adjustments with justification
- [ ] Creates annotation delta (lightweight, low blast radius)

**Story Points:** 3

---

### US-065: Direct Contribution API
**As a** system integrator
**I want to** submit structured knowledge via API without the game UI
**So that** external tools can feed the ontology

**Acceptance Criteria:**
- [ ] `POST /contributions` — accepts entity, rule, scenario, or annotation payloads
- [ ] Validates against ontology schema
- [ ] Creates appropriate delta types
- [ ] Returns delta IDs for tracking
- [ ] Rate-limited and authenticated (future: RBAC)

**Story Points:** 3

---

## Technical Tasks

| Task | Story | Ticket | Team | Est |
|:---|:---|:---|:---|:---|
| Expert mode toggle + routing | US-060 | LENS-025 | LENS | M |
| Direct entity/rule editor forms | US-061, US-062 | LENS-026 | LENS | L |
| Scenario authoring UI | US-063 | LENS-027 | LENS | L |
| Artifact annotation UI | US-064 | LENS-026 | LENS | (included) |
| Direct contribution API | US-065 | CTX-029 | CORTEX | M |

---

## Dependencies

- **Delta Model (EPIC-002)** — All contributions flow through deltas (DONE)
- **HITL Routing (CTX-006)** — Expert contributions route to review queue (DONE)
- **PersonaContext** — `frontend/src/lib/persona.ts` already defines mode toggle (DONE)
- **Curator Dashboard (LENS-005)** — Expert mode shares approval workflow UI

## Risks

| Risk | Mitigation |
|:---|:---|
| Experts create duplicate entities | Auto-suggest + fuzzy matching |
| Direct edits bypass quality gates | All changes are deltas, same review queue |
| Low adoption if forms are complex | Progressive disclosure — start simple, expand |
| Schema drift between UI and backend | Shared Pydantic/TypeScript types |
