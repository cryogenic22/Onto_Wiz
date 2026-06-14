# EPIC-008: Agentic AI Extraction & Curation Layer

## Epic Summary

**As a** platform
**I want to** use a hybrid deterministic + LLM approach to extract, link, and curate knowledge
**So that** both game sessions and document ingestion produce richer, more connected ontology artifacts

## Business Value

- Transforms free-text SME responses into structured entities and relationships
- Enables document ingestion (EPIC-007) — the extraction engine
- Reduces curator workload by auto-linking new artifacts to existing ontology
- Improves pattern quality through entity resolution and deduplication
- Makes the "Game → Graph → Guardrail" pipeline intelligent, not just mechanical

## Epic Scope

### In Scope
- LLM provider abstraction (swap providers without code changes)
- Entity extraction from free text (game responses + documents)
- Relationship extraction (identify links between entities)
- Entity resolution (fuzzy matching, synonym detection, deduplication)
- Smart linking (connect new artifacts to existing ontology graph)
- Confidence calibration (LLM-assisted scoring against evidence)
- Deterministic fallback (rule-based extraction when LLM unavailable)
- Prompt engineering for pharma domain

### Out of Scope (Future)
- Fine-tuned models (use general-purpose LLMs with prompts)
- Multi-modal extraction (images, diagrams)
- Real-time streaming extraction
- Model training / RLHF

---

## User Stories

### US-080: LLM Provider Abstraction
**As a** developer
**I want to** call LLMs through a provider-agnostic interface
**So that** we can switch between OpenAI, Anthropic, or local models

**Acceptance Criteria:**
- [ ] `LLMProvider` protocol/interface with `extract()`, `classify()`, `resolve()` methods
- [ ] Concrete implementations: `AnthropicProvider`, `OpenAIProvider`, `MockProvider`
- [ ] `MockProvider` for testing (deterministic, no API calls)
- [ ] Configuration via environment variables or config file
- [ ] Rate limiting and retry logic built in
- [ ] Cost tracking per call (token count, model, estimated cost)

**Story Points:** 5

---

### US-081: Entity Extraction from Free Text
**As a** system
**I want to** extract entities from SME game responses and documents
**So that** implicit knowledge becomes explicit ontology nodes

**Acceptance Criteria:**
- [ ] Given free text, return: entity name, type, attributes, confidence
- [ ] Entity types aligned with ontology: Brand, Account, Signal, Biomarker, Indication, Metric, HCP, Payer
- [ ] Pharma-specific prompt templates (e.g., "Identify clinical signals, commercial dynamics, and therapeutic concepts")
- [ ] Deterministic pre-filter: regex/keyword extraction before LLM call (reduces cost)
- [ ] Post-processing: normalize entity names, validate against known types
- [ ] Creates PROPOSED_ENTITY deltas

**Story Points:** 8

---

### US-082: Relationship Extraction
**As a** system
**I want to** detect relationships between extracted entities
**So that** the ontology graph captures connections, not just nodes

**Acceptance Criteria:**
- [ ] Relationship types: supports, contradicts, requires_evidence, leads_to, associated_with
- [ ] Given text + extracted entities, return: (entity_a, relationship, entity_b, confidence)
- [ ] Cross-reference with existing graph edges to avoid duplicates
- [ ] Creates PROPOSED_EDGE deltas
- [ ] Handles negation: "X does NOT cause Y" → contradicts edge

**Story Points:** 8

---

### US-083: Entity Resolution
**As a** system
**I want to** match new entities against existing ones
**So that** duplicates are merged and synonyms are detected

**Acceptance Criteria:**
- [ ] Fuzzy name matching (Levenshtein, token overlap)
- [ ] Semantic similarity check (via LLM embedding or prompt)
- [ ] Auto-merge if confidence > 0.95 (propose SYNONYM delta)
- [ ] Flag for review if confidence 0.7-0.95
- [ ] Uses existing SemanticStore synonym registry
- [ ] Handles abbreviations, brand names, generic names

**Story Points:** 5

---

### US-084: Smart Linking
**As a** system
**I want to** automatically connect new artifacts to existing ontology nodes
**So that** knowledge is integrated, not isolated

**Acceptance Criteria:**
- [ ] New pattern → find relevant entities, create edges
- [ ] New entity → find similar entities, suggest hierarchy placement
- [ ] New guardrail → find patterns it should block
- [ ] New scenario → find matching rules, verify coverage
- [ ] All links are proposals (PROPOSED_EDGE deltas)
- [ ] Uses graph traversal to find connection candidates

**Story Points:** 5

---

### US-085: Enhance Game Pipeline with AI
**As a** system
**I want to** apply AI extraction to SME game responses
**So that** a 5-minute game produces richer artifacts than mechanical mapping

**Acceptance Criteria:**
- [ ] Hypothesis text → extract driver entities + relationships
- [ ] Disconfirming logic text → extract guardrail conditions
- [ ] Pattern recognition text → extract pattern context and frequency signals
- [ ] Mistake description → extract specific anti-patterns
- [ ] Action recommendations → extract action templates with preconditions
- [ ] Fallback: if LLM unavailable, use existing deterministic pipeline
- [ ] A/B metric: compare delta count and quality (game+AI vs game-only)

**Story Points:** 8

---

### US-086: Confidence Calibration from Evidence
**As a** system
**I want to** adjust artifact confidence using external evidence
**So that** confidence reflects data quality, not just SME opinion

**Acceptance Criteria:**
- [ ] Given pattern + available evidence → compute calibrated confidence
- [ ] Factors: evidence type (hard/soft/rumor), recency, source reliability
- [ ] LLM-assisted: "Given this evidence, how confident should we be in this pattern?"
- [ ] Updates existing ConfidenceEngine with calibrated scores
- [ ] Tracks calibration source in audit

**Story Points:** 5

---

## Technical Tasks

| Task | Story | Ticket | Team | Est |
|:---|:---|:---|:---|:---|
| LLM integration framework | US-080 | CTX-033 | CORTEX | M |
| Entity extraction agent | US-081 | CTX-034 | CORTEX | L |
| Relationship extraction agent | US-082 | CTX-035 | CORTEX | L |
| Entity resolution agent | US-083 | CTX-036 | CORTEX | M |
| Smart linking agent | US-084 | CTX-037 | CORTEX | M |
| Game pipeline AI enhancement | US-085 | CTX-038 | CORTEX | L |
| Confidence calibration enhancement | US-086 | CTX-039 | CORTEX | M |
| Pharma domain prompt library | US-081-085 | ATL-024 | ATLAS | L |

---

## Architecture

```
                    ┌─────────────────────┐
                    │  Input Sources       │
                    │  - SME Game          │
                    │  - Expert Mode       │
                    │  - Document Upload   │
                    └────────┬────────────┘
                             ▼
                    ┌─────────────────────┐
                    │  Preprocessing       │
                    │  - Format parsing    │
                    │  - Chunking          │
                    │  - Regex pre-filter  │
                    └────────┬────────────┘
                             ▼
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Entity    │ │ Relationship│ │   Entity    │
    │ Extraction  │ │ Extraction  │ │ Resolution  │
    │   Agent     │ │   Agent     │ │   Agent     │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           └───────────────┼───────────────┘
                           ▼
                    ┌─────────────────────┐
                    │  Smart Linking       │
                    │  - Graph integration │
                    │  - Duplicate detect  │
                    │  - Hierarchy place   │
                    └────────┬────────────┘
                             ▼
                    ┌─────────────────────┐
                    │  Delta Pipeline      │
                    │  - Create deltas     │
                    │  - Auto-classify     │
                    │  - Route to review   │
                    └─────────────────────┘
```

---

## Hybrid Approach: Deterministic + LLM

| Step | Deterministic | LLM-Assisted |
|:---|:---|:---|
| Entity detection | Regex, keyword lists, known entity dictionaries | Free-text entity extraction, ambiguous cases |
| Relationship detection | Tag co-occurrence, ontology rule matching | Semantic relationship inference from context |
| Entity resolution | Exact match, canonical ID lookup | Fuzzy matching, semantic similarity |
| Confidence scoring | Evidence-based formula (current ConfidenceEngine) | Calibration with context understanding |
| Linking | Graph traversal, type-compatible edges | Semantic relevance scoring |

**Principle:** Deterministic first, LLM for what rules can't handle. Every LLM result is a _proposal_ (delta), never a direct write.

---

## LLM Cost Model

| Operation | Tokens (est.) | Frequency | Monthly Cost (est.) |
|:---|:---|:---|:---|
| Entity extraction per chunk | ~500 in + ~200 out | 100/day | ~$15/mo |
| Relationship extraction per chunk | ~800 in + ~300 out | 50/day | ~$15/mo |
| Entity resolution per entity | ~300 in + ~100 out | 200/day | ~$10/mo |
| Confidence calibration per pattern | ~500 in + ~200 out | 50/day | ~$10/mo |
| **Total estimate** | | | **~$50/mo** |

_Assumes Claude Haiku or GPT-4o-mini for extraction, larger models for complex reasoning only._

---

## Dependencies

- **DEC-012 (proposed)** — Approve LLM SDK dependency (anthropic or openai)
- **Delta Model (EPIC-002)** — All AI output flows through deltas (DONE)
- **SemanticStore** — For synonym registry integration (DONE)
- **ConfidenceEngine** — For calibration integration (DONE)
- **EPIC-007** — Document ingestion is a primary consumer

## Risks

| Risk | Mitigation |
|:---|:---|
| LLM hallucination | All outputs are proposals, never direct writes. Curator review required. |
| API cost runaway | Token budgets, batch processing, cheaper models for simple tasks |
| Provider lock-in | Provider abstraction layer, MockProvider for testing |
| Extraction quality variance | Domain-specific prompt templates, gold set evaluation |
| Latency for game sessions | Async extraction — game completes immediately, AI enrichment runs in background |
