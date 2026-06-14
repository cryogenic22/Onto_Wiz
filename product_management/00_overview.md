# Onto_Wiz Product Overview

> **Enterprise Judgment Layer for Agentic AI**

## Vision Statement

Onto_Wiz is a **living Judgment Layer** that captures, governs, and operationalizes expert judgment for Enterprise AI. It transforms implicit expert reasoning into explicit, auditable, and reusable patterns that improve AI agent quality over time.

## The Problem

Enterprise AI systems fail because:
1. **Knowledge Management Tax** - SMEs won't fill out forms, ontologies, or documentation
2. **Hallucination Risk** - Agents make claims without evidence or proper guardrails
3. **Context Blindness** - Same metric means different things in Oncology vs CNS
4. **Unauditable Decisions** - No trace of why an AI said something

## The Solution: "Game → Graph → Guardrail"

```
SME Game Session (5 min)     →    Reasoning Graph      →    Safe AI Output
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SME answers scenario          Patterns, edges,          "Access friction likely,
questions naturally.          guardrails created.       not demand erosion.
No ontology terms.            All context-scoped.       Check PA edits first."
```

## Key Differentiators

| Traditional KM | Onto_Wiz |
|:---|:---|
| SME fills ontology forms | SME plays scenario game |
| Static rules | Decaying, context-scoped patterns |
| Boolean pattern matching | Ranked scoring with evidence |
| Trust the AI output | Evidence trace + guardrails |
| Single domain | Modular: Commercial → Supply Chain → Clinical |

## Target Users

| Persona | Value |
|:---|:---|
| **SME / Expert** | "It felt like a case discussion, not documentation" |
| **AI Agent** | Gets patterns, guardrails, and required evidence |
| **Business Leader** | Auditable AI with ROI telemetry |
| **Governance/Compliance** | Full trace, judgment types, approval workflows |

## Current Status

| Metric | Value |
|:---|:---|
| **Core Models** | 8 modules, ~5,000 lines |
| **Test Coverage** | 56 tests passing |
| **Phase** | 2.1 (55% complete) |
| **Demo Ready** | MVP: "Why did Brand X dip?" |

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  SME Game UI                                                    │
│  (Scenario → Hypothesis → Signals → Change-my-mind → Actions)  │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Delta Layer (All changes are proposals)                        │
│  ReasoningEvent → DeltaGenerator → Review Queue → Approve       │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Judgment Layer                                                 │
│  JudgmentPattern | Guardrail | ActionTemplate | SemanticStore   │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Graph Layer                                                    │
│  GraphStore (Nodes: Signal, Hypothesis, Evidence, Driver)       │
│  Edges: supports, contradicts, requires_evidence, leads_to      │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Evidence Layer                                                 │
│  EvidenceStore (Hard > Soft > Rumor) + ConfidenceEngine         │
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Output: Intelligence Packet                                    │
│  Drivers + Confidence + Evidence + Next Actions + Trace         │
└─────────────────────────────────────────────────────────────────┘
```

## Success Metrics

| Metric | Target | Current |
|:---|:---|:---|
| SME game completion | 5-7 min | N/A (pending UI) |
| Patterns per game | 1-2 | 1 |
| Guardrails per game | 1-3 | 1 |
| Test regression | 0 failures | ✅ |
| Demo: "Why dip?" | End-to-end | 70% ready |

---

## Folder Structure

```
product_management/
├── 00_overview.md              # This file
├── 01_roadmap.md               # Phase timeline and milestones
├── epics/                      # High-level capability areas
│   ├── EPIC-001_sme_game.md
│   ├── EPIC-002_delta_model.md
│   ├── EPIC-003_governance.md
│   ├── EPIC-004_agent_traversal.md
│   ├── EPIC-005_production.md
│   ├── EPIC-006_expert_mode.md
│   ├── EPIC-007_document_ingestion.md
│   └── EPIC-008_agentic_ai.md
├── stories/                    # User stories with acceptance criteria
├── designs/                    # Technical design documents
│   ├── design_confidence_engine.md
│   ├── design_semantic_store.md
│   └── design_pattern_matching.md
└── specs/                      # API and data specifications
```
