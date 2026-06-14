# Team ATLAS — "The Knowledge Foundation" — Instruction Packet

> **Team Code:** `ATL`  |  **Ticket Prefix:** `ATL-NNN`
> Read this file FIRST at the start of every session.
> Then: `anti_slop.md` → `docs/BOARD.md` → `docs/Lead2Dev.md` → `docs/DECISION_LOG.md` → sprint files
> Protocol: `docs/AUTONOMOUS_AGENT_PROTOCOL.md`

---

## 1. Project Context

**Onto_Wiz** is an Agentic Semantic Readiness Platform. It captures expert judgment through a scenario-based game and converts it into a deployable knowledge layer for enterprise AI agents.

**The Pipeline:** `SME Game → ReasoningEvent → DeltaGenerator → Delta Queue → Approval → Graph Promotion → Intelligence Packet`

**Your Role in the Pipeline:** You build the baseline knowledge that the entire system reasons over. Without your ontology files, taxonomy hierarchies, inference rules, scenarios, and evidence — the reasoning engine has nothing to work with, SMEs have no scenarios to play, and agents have no knowledge graph to traverse.

**Core Principle:** You are the pharma domain expert team. You research, structure, and curate the domain knowledge that engineering teams (LENS and CORTEX) consume as YAML artifacts. Your output is the "database" that SMEs validate and refine through the game loop.

---

## 2. Your Mission

You own the **pharma domain knowledge layer** — ontology definitions, therapeutic area taxonomies, inference rules, scenario libraries, evidence seed data, and gold set tests.

**Your tickets (ATL-NNN) map to:**
- **Ontology expansion:** Entity types, relationships, inference rules across the pharma value chain
- **Therapeutic area taxonomies:** Deep classification of indications, mechanisms, biomarkers, treatment lines per TA
- **Scenario libraries:** Realistic SME game scenarios with expected reasoning paths
- **Evidence corpus:** Seed evidence items (metrics, field notes, competitor intel) that ground the reasoning
- **Gold set tests:** Regression scenarios that validate the reasoning engine produces correct outputs
- **Playbooks:** Cross-functional response patterns (field, medical, access teams)
- **Metrics ontology:** Standardized pharma metric definitions with relationships

---

## 3. File Ownership

**You own (exclusive write access):**
```
ontology/commercial.yaml              — Commercial pharma ontology (current: 3 rules, target: 30+)
ontology/therapeutic_areas/            — Per-TA taxonomy files (oncology, immunology, CNS, CV, etc.)
ontology/domains/                      — Cross-cutting domain files (market_access, competitive_intel, regulatory, supply_chain)
ontology/rules/                        — Inference rule library (cross-TA reasoning rules)
ontology/playbooks/                    — Response pattern playbooks (launch, field, medical, access)
ontology/markets/                      — Regional market archetype files
ontology/metrics.yaml                  — Pharma metrics ontology (TRx, NBRx, NPS, PDC, etc.)
content/scenarios/                     — SME game scenario YAML files organized by TA
content/evidence/                      — Seed evidence items (YAML)
content/demo/                          — Demo data packages
content/validation/                    — SME validation protocols and feedback forms
tests/gold_set/                        — Gold set regression test scenarios
```

**You do NOT touch:**
```
src/**              — Owned by Team CORTEX and Team LENS
frontend/**         — Owned by Team LENS
tests/test_*.py     — Owned by CORTEX/LENS (you own tests/gold_set/ only)
docs/**             — Owned by Tech Lead
quality/**          — Owned by Team SENTINEL
```

---

## 4. Current State

### What Exists
- `ontology/commercial.yaml` — 3 inference rules (access_barrier_detection, competitive_response_pattern, launch_trajectory_analysis). Basic entity types and relationships.
- `ontology/synthetic_data/` — Test/demo synthetic data (brands, scenarios, evidence items)
- `tests/gold_set/` — Gold set framework with 3 baseline scenarios

### What's Missing
- No therapeutic area taxonomies (oncology, immunology, CNS, CV, etc.)
- Only 3 inference rules (target: 50+ cross-TA rules)
- No scenario library (target: 10+ per TA)
- No evidence corpus (target: 100+ seed items)
- No market access domain model
- No competitive intelligence ontology
- No regional market archetypes
- No pharma metrics standardization
- No playbook patterns

### Ontology File Format

All ontology files use YAML with this structure:
```yaml
# ontology/therapeutic_areas/oncology.yaml
name: oncology
version: "1.0"
description: "Oncology therapeutic area taxonomy"

entity_types:
  - name: indication
    attributes: [icd10_code, prevalence, line_of_therapy]
  - name: mechanism_of_action
    attributes: [target, pathway, modality]

relationships:
  - name: treats
    source: drug
    target: indication
    attributes: [line, evidence_level]

taxonomy:
  indications:
    solid_tumors:
      - nsclc
      - breast_cancer
      - colorectal_cancer
    hematologic:
      - aml
      - cll
      - dlbcl

inference_rules:
  - name: biosimilar_erosion_pattern
    applies_when:
      signals: [market_share_decline, new_entrant]
      context: {lifecycle_stage: mature, has_biosimilar: true}
    typical_drivers: [competitive_pressure, price_erosion]
    confidence_modifier: 0.8
```

### Integration with Engineering Teams

Your YAML files are consumed by:
1. **CORTEX** — `ReasoningEngine` loads ontology rules, `DeltaGenerator` references entity types, `SemanticStore` uses taxonomy hierarchies
2. **LENS** — `GET /scenarios` serves scenario definitions, game UI renders scenario cards from your content
3. **SENTINEL** — Gold set tests validate that reasoning engine produces expected outputs for your scenarios

---

## 5. Domain Research Approach

### Sources for Ontology Content
- Pharma industry standard classifications (ATC, ICD-10, MedDRA, SNOMED)
- Commercial pharma operations knowledge (sales, marketing, access, medical affairs, field operations)
- Regulatory frameworks (FDA, EMA, PMDA approval pathways)
- Market dynamics (payer landscape, formulary structures, rebate models)
- Competitive intelligence patterns (pipeline analysis, pricing strategies, launch sequencing)

### Quality Standards
- Every entity type must have clear attributes and relationships
- Every inference rule must have `applies_when` conditions and `typical_drivers`
- Every scenario must have expected reasoning paths (for gold set validation)
- Terminology must match industry standard usage
- Rules must be evidence-grounded (cite source or reasoning)

### Anti-Slop Rules
- Do NOT invent fake drug names or company names — use realistic archetypes (e.g., "Brand A in oncology" or use well-known public examples)
- Do NOT create overly simplistic rules — pharma reasoning is nuanced
- Do NOT duplicate rules across files — shared rules go in `ontology/rules/`
- Do NOT mix therapeutic areas in a single file — one TA per file
- Keep YAML files under 300 lines — split into sub-files if needed

---

## 6. Your Ticket Queue

Check `docs/BOARD.md` for current board state. Your active tickets:

| Ticket | Title | Sprint | Est |
|--------|-------|--------|-----|
| ATL-001 | Commercial Ontology Expansion — Full Value Chain | 1 | L |
| ATL-002 | Oncology Deep Taxonomy | 2 | L |
| ATL-003 | Scenario Library v1 — 10 Oncology Scenarios | 3 | XL |
| ATL-004 → ATL-020 | See BOARD.md for full backlog | 4-20 | Various |

Sprint details (acceptance criteria) are in `docs/Lead2Dev.md`.

---

## 7. How to Start

```
1. READ this file (done)
2. READ anti_slop.md
3. READ docs/BOARD.md — see full board state
4. READ docs/Lead2Dev.md — find your ticket marked EXECUTE NOW
5. READ docs/DECISION_LOG.md — settled decisions
6. READ existing ontology files (ontology/commercial.yaml, ontology/synthetic_data/)
7. READ src/core/models.py — understand entity types and enums your YAML maps to
8. READ src/core/reasoning_event.py — understand ReasoningEvent structure
9. WRITE mini-spec in docs/Dev2Lead.md
10. IMPLEMENT YAML files
11. VALIDATE: Ensure YAML parses correctly, structure matches expected schema
12. REPORT in docs/Dev2Lead.md
```

---

_Team ATLAS Instruction Packet v1.0 — Tech Lead_
