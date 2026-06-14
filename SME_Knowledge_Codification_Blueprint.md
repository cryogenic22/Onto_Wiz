# SME Knowledge Codification Agent — Architecture Blueprint

**Architecture Blueprint & Lead Guidance for Building Domain Packs that Make Every Agentic Solution Accurate, Relevant, and Auditable**

Prepared for: Cryogenic / ZS Analytics Practice • 28 March 2026 • Onto_Wiz + SpecOmagic Programme

---

## Contents

1. [Lead Vision & Strategic Direction](#1-lead-vision--strategic-direction)
2. [The Problem: Why SME Knowledge Leaks](#2-the-problem-why-sme-knowledge-leaks)
3. [System Architecture: The Knowledge Codification Agent](#3-system-architecture-the-knowledge-codification-agent)
4. [Domain Pack Specification](#4-domain-pack-specification)
5. [Knowledge Capture Pipelines](#5-knowledge-capture-pipelines)
6. [Data Models & Code Scaffolding](#6-data-models--code-scaffolding)
7. [Governance & Quality Gates](#7-governance--quality-gates)
8. [Integration with Onto_Wiz & SpecOmagic](#8-integration-with-onto_wiz--specomagic)
9. [The Agentic Loop: From Capture to Deployment](#9-the-agentic-loop-from-capture-to-deployment)
10. [Implementation Roadmap](#10-implementation-roadmap)
11. [Open Decisions for PM](#11-open-decisions-for-pm)

---

## 1. Lead Vision & Strategic Direction

> **The Core Thesis**
> Every consulting engagement generates irreplaceable domain knowledge — decision heuristics, data quirks, process shortcuts, terminology translations — that currently lives in people's heads and scattered documents. When a senior analyst leaves or a new team spins up, that knowledge is gone. The SME Knowledge Codification Agent turns this tacit expertise into versioned, governed, machine-consumable *Domain Packs* that become the foundation of every agentic solution your practice builds.

### 1.1 Where We Are

You have built two complementary systems with 1,062 passing tests, 52+ API endpoints, and 10 frontend pages. **Onto_Wiz** provides the reasoning engine, judgment layer, and governance model. **SpecOmagic** provides the knowledge supply chain — parsing, extraction, tagging, context assembly, and agent personas. The foundations are solid.

### 1.2 Where We Need to Go

The next evolutionary step is not more features — it is **systematising the capture loop**. Right now, knowledge enters the system through two channels: document ingestion (SpecOmagic) and SME game sessions (Onto_Wiz). Both work, but they're ad-hoc. What's missing is:

- **A structured taxonomy of knowledge types** — so the team knows exactly what to capture and how
- **Domain Packs as the unit of distribution** — versioned, composable bundles that any agentic solution can consume
- **A continuous capture agent** — that interviews SMEs, observes analytics workflows, and proposes codified artifacts through the Delta governance pipeline
- **Quality feedback loops** — so domain packs improve every time an agent uses them and an SME reviews the output

### 1.3 Guidance for the Team

**Principle 1: Knowledge is the Product**
Code is the delivery mechanism. The real value is in the curated knowledge that makes agents accurate. Every sprint should ship knowledge artifacts, not just code.

**Principle 2: Domain Packs Over Monoliths**
Don't build one giant knowledge base. Build composable packs — base analytics, oncology overlay, payer overlay, client overlay — that stack and override. SpecOmagic's LayeredStore already supports this.

**Principle 3: Capture is Continuous**
Knowledge capture is not a one-time migration. It's an ongoing process embedded in the analytics workflow. Every client engagement, every data review, every model iteration generates knowledge worth codifying.

**Principle 4: Governance is Non-Negotiable**
Onto_Wiz's Delta Model applies to all knowledge. No artifact reaches production without review. Judgment type (empirical/causal/normative) determines the review bar. This is what makes the system trustworthy.

**Principle 5: Measure What Matters**
Track: artifacts per domain, artifacts per lifecycle stage, context assembly hit rate, agent accuracy with/without domain packs, SME review turnaround time, knowledge freshness (staleness %).

**Principle 6: Start With Your Best SMEs**
Identify 3–5 senior analysts who know their domains cold. Run structured capture sessions. Their knowledge becomes the seed packs that prove the value proposition to the wider practice.

---

## 2. The Problem: Why SME Knowledge Leaks

In a consulting analytics practice, domain knowledge exists in five forms, each with its own leak pattern:

| Knowledge Type | Example | Where It Lives Today | How It Leaks |
|---|---|---|---|
| **Decision Heuristics** | "If PA reject rate > 30% and no peer-to-peer programme, escalate to MSL — the field team can't fix this alone" | Senior analyst's intuition | Attrition, team rotation |
| **Data Knowledge** | "IQVIA DDD undercounts specialty pharmacy by ~15% for oncology — always cross-reference with SP claims" | Tribal knowledge, ad-hoc Slack messages | Never documented, discovered by pain |
| **Process Knowledge** | "For brand share analysis, always run the waterfall decomposition before the driver attribution — the ordering matters for the narrative" | BRDs, methodology docs (often outdated) | Document rot, version sprawl |
| **Terminology/Jargon** | "When the client says 'pull-through', they mean formulary-to-prescription conversion, not demand generation" | Onboarding calls, context-dependent | Lost when context changes |
| **Few-Shot Patterns** | "Here's how we structured the competitive landscape slide for Merck last quarter — this format works" | Previous deliverables, personal folders | Unfindable, untagged, stale |

> **The Compounding Cost**
> Each time a new analyst joins a project, they spend 2–4 weeks rebuilding context that a departing analyst had internalised over months. Multiply across 50+ engagements per year, and the lost productivity is staggering. Domain Packs eliminate this cold-start problem entirely.

---

## 3. System Architecture: The Knowledge Codification Agent

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          SME KNOWLEDGE CODIFICATION AGENT                               │
│                                                                                         │
│  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌───────────────┐ │
│  │  CAPTURE LAYER   │   │  EXTRACTION LAYER │   │  CURATION LAYER  │   │ DISTRIBUTION  │ │
│  │                  │   │                   │   │                  │   │    LAYER      │ │
│  │ • SME Interviews │──▶│ • Pattern Extract │──▶│ • Delta Proposals│──▶│ • Domain Packs│ │
│  │ • Doc Ingestion  │   │ • LLM-Assisted    │   │ • HITL Review    │   │ • Layer Stack │ │
│  │ • Workflow Obs.  │   │ • Cross-Reference │   │ • Quality Gates  │   │ • Version Mgmt│ │
│  │ • Game Sessions  │   │ • Deduplication   │   │ • Consolidation  │   │ • SDK Access  │ │
│  └─────────────────┘   └──────────────────┘   └──────────────────┘   └───────────────┘ │
│           │                                             │                      │        │
│           │              ┌──────────────────┐           │                      │        │
│           └─────────────▶│  FEEDBACK LAYER   │◀──────────┘                      │        │
│                          │                   │                                  │        │
│                          │ • Agent Output QA │◀─────────────────────────────────┘        │
│                          │ • SME Corrections │                                           │
│                          │ • Usage Analytics │                                           │
│                          └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
             ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐
             │  Onto_Wiz    │   │  SpecOmagic   │   │  Any Agentic     │
             │  Reasoning   │   │  Context      │   │  Solution        │
             │  Engine      │   │  Assembly     │   │  (Client Apps)   │
             └─────────────┘   └──────────────┘   └──────────────────┘
```

### 3.1 Layer Responsibilities

| Layer | Responsibility | Existing Foundation | New Build |
|---|---|---|---|
| **Capture** | Acquire raw knowledge from humans and documents | SpecOmagic parsers (6 formats), Onto_Wiz ReasoningEvent | Structured SME Interview Agent, Workflow Observer, Analytics Session Recorder |
| **Extraction** | Transform raw input into typed knowledge artifacts | SpecOmagic ExtractionPipeline (7 extractors), Onto_Wiz DeltaGenerator | Decision Heuristic Extractor, Data Quirk Extractor, Process Step Extractor |
| **Curation** | Governance, review, quality assurance | Onto_Wiz DeltaStore + PromotionPipeline, SpecOmagic lifecycle gates | Cross-pack conflict detection, Freshness enforcement, Consolidation agent |
| **Distribution** | Package and deliver knowledge to consumers | SpecOmagic LayeredStore + ContextAssembler + SDK | Domain Pack builder, Pack versioning, Pack registry, pip-installable distribution |
| **Feedback** | Improve knowledge based on usage outcomes | SpecOmagic FeedbackStore + FeedbackPipeline, Onto_Wiz ContributionStore | Agent output scoring, Automatic staleness detection, Feedback-to-Delta pipeline |

---

## 4. Domain Pack Specification

> **What is a Domain Pack?**
> A Domain Pack is a versioned, composable bundle of curated knowledge artifacts that gives any AI agent the domain expertise it needs to perform accurately in a specific context. It is the unit of knowledge distribution — analogous to a Python package, but for domain intelligence rather than code.

### 4.1 Pack Structure

```
# Domain Pack directory layout (maps to SpecOmagic's knowledge_base/ structure)
commercial_analytics_pack/
├── pack.yaml                    # Pack manifest (metadata, version, dependencies)
├── instruction_sets/
│   ├── IS-brand-share.yaml      # Rules for brand share calculation
│   ├── IS-waterfall-decomp.yaml # Rules for waterfall decomposition
│   └── IS-driver-attrib.yaml    # Rules for driver attribution
├── jargon_maps/
│   ├── JM-commercial.yaml       # Commercial analytics terminology
│   └── JM-data-sources.yaml     # Data source terminology
├── entity_registry/
│   ├── ER-drugs.yaml            # Drug entities (name, class, manufacturer, aliases)
│   ├── ER-data-sources.yaml     # Data source entities (IQVIA, Symphony, etc.)
│   └── ER-metrics.yaml          # Metric entities (TRx, NBRx, market_share, etc.)
├── few_shots/
│   ├── FS-brand-share.yaml      # Few-shot examples for brand share queries
│   └── FS-competitive.yaml      # Few-shot examples for competitive analysis
├── taxonomies/
│   ├── TX-therapy-areas.yaml    # Therapy area hierarchy
│   └── TX-data-hierarchy.yaml   # Data source hierarchy
├── overrides/
│   └── OR-safety-rules.yaml     # Hard constraints (always-fire rules)
├── decision_heuristics/         # NEW artifact type
│   ├── DH-pa-escalation.yaml    # PA reject rate escalation heuristic
│   └── DH-launch-sequencing.yaml
├── data_quirks/                 # NEW artifact type
│   ├── DQ-iqvia-specialty.yaml  # IQVIA specialty pharmacy undercount
│   └── DQ-symphony-lag.yaml     # Symphony data lag patterns
├── process_playbooks/           # NEW artifact type
│   ├── PP-brand-review.yaml     # Brand review analytics workflow
│   └── PP-launch-readiness.yaml # Launch readiness assessment process
└── judgment_patterns/           # Onto_Wiz JudgmentPatterns exported
    └── JP-oncology-signals.yaml # Learned oncology signal patterns
```

### 4.2 Pack Manifest (`pack.yaml`)

```yaml
# pack.yaml — Domain Pack manifest
id: "dp-commercial-analytics-v2"
name: "Commercial Analytics Base Pack"
version: "2.1.0"
pack_type: "base"                  # base | therapy_area | client

# Authorship & Governance
created_by: "kapil.pant@zs.com"
owner_team: "Commercial Analytics CoE"
review_cycle: "quarterly"
last_reviewed: "2026-03-15"
status: "active"                   # draft | active | deprecated

# Scope
therapeutic_areas: ["all"]         # or specific: ["oncology", "immunology"]
analytics_domains:
  - "Commercial Analytics"
  - "Forecasting"
geography: "US"

# Contents summary (auto-generated)
artifact_counts:
  instruction_sets: 12
  jargon_maps: 4
  entity_registry: 5
  few_shots: 8
  taxonomies: 3
  overrides: 2
  decision_heuristics: 15
  data_quirks: 9
  process_playbooks: 6
  judgment_patterns: 7

# Dependencies (other packs this one extends)
dependencies:
  - pack_id: "dp-pharma-base-v1"
    version: ">=1.0.0"
    layer_type: "base"

# Compatibility
min_specomagic_version: "0.6.0"
min_onto_wiz_version: "0.4.0"

# Quality metrics (auto-computed)
quality:
  total_artifacts: 71
  active_artifacts: 64
  stale_artifacts: 3
  avg_freshness_days: 42
  coverage_score: 0.82            # What % of expected knowledge areas are covered
  sme_review_rate: 0.91           # What % have been reviewed by an SME
```

### 4.3 New Artifact Types

The existing SpecOmagic artifact types (InstructionSet, JargonMap, EntityRegistry, Taxonomy, FewShotLibrary, OverrideRule, PromptTemplate) cover document-derived knowledge well. For SME-originated knowledge, we introduce three new types:

**DecisionHeuristic** — A codified decision rule that an SME applies intuitively — the "if X then Y unless Z" patterns. Maps to Onto_Wiz JudgmentPattern (signal matching + driver attribution). Fields: `trigger_signals`, `decision_logic`, `exceptions`, `confidence`, `evidence_required`, `typical_outcome`, `anti_patterns`.

**DataQuirk** — A known data limitation, bias, or gotcha that affects analytical accuracy. Maps to SpecOmagic OverrideRule (always-fire constraint) + Onto_Wiz Guardrail. Fields: `data_source`, `quirk_description`, `impact_severity`, `workaround`, `validation_query`, `known_since`, `affects_metrics`.

**ProcessPlaybook** — A step-by-step analytical workflow with decision points, dependencies, and quality checks. Maps to Onto_Wiz ActionTemplate (cross-functional actions) + SpecOmagic InstructionSet (ordered rules). Fields: `steps[]` (order, action, inputs, outputs, quality_check, decision_point), `prerequisites`, `estimated_duration`, `common_pitfalls`.

### 4.4 Layer Stacking Model

```
  Priority ▲
           │
    100    │  ┌──────────────────────────────────────┐
           │  │         CLIENT OVERLAY                │  "For Merck, use 'pull-through'
           │  │    (per-engagement customisation)     │   to mean formulary conversion"
           │  └──────────────────────────────────────┘
           │
     50    │  ┌──────────────────────────────────────┐
           │  │      THERAPY AREA LAYER               │  "In oncology, biomarker-driven
           │  │    (oncology, immunology, CNS...)     │   segmentation is mandatory"
           │  └──────────────────────────────────────┘
           │
     10    │  ┌──────────────────────────────────────┐
           │  │         BASE ANALYTICS LAYER          │  "Brand share = Brand TRx /
           │  │    (universal pharma analytics)       │   Total Market TRx"
           │  └──────────────────────────────────────┘
           │
           └──────────────────────────────────────────▶ Scope (broad → narrow)

  Resolution: Higher-priority layers override lower ones for the same artifact ID.
  SpecOmagic LayeredStore handles this natively via StackConfig.
```

---

## 5. Knowledge Capture Pipelines

### 5.1 Pipeline Overview

| Pipeline | Input Source | Agent Role | Output Artifacts | Governance Path |
|---|---|---|---|---|
| **SME Interview Agent** | Structured conversation with domain expert | Interviewer — asks targeted questions per knowledge type | DecisionHeuristic, DataQuirk, ProcessPlaybook, JargonMap entries | Delta → DeltaStore → HITL review → Promotion |
| **Document Ingestion** | BRDs, methodology docs, SOPs, training materials | Extractor — pattern + LLM hybrid pipeline | InstructionSet, EntityRegistry, JargonMap, FewShotLibrary, Taxonomy | SpecOmagic lifecycle gates (DRAFT → REVIEW → ACTIVE) |
| **Game Session Capture** | SME reasoning game (Onto_Wiz Situation Room) | Observer — records signal prioritisation, hypothesis ranking | JudgmentPattern, Guardrail, ActionTemplate (via DeltaGenerator) | Delta → DeltaStore → classified → routed → promoted |
| **Workflow Observer** | Analytics session logs, notebook traces | Pattern detector — identifies repeated analytical steps | ProcessPlaybook, DataQuirk, FewShotLibrary | Delta → DeltaStore → SME validation |
| **Feedback Loop** | Agent output corrections from end users | Improver — converts corrections to artifact updates | Updates to any existing artifact type | FeedbackPipeline → ArtifactSuggestion → Delta |

### 5.2 SME Interview Agent — Detailed Design

This is the primary new component. It conducts structured knowledge elicitation sessions with domain experts, producing typed artifacts that flow through governance.

#### Interview Structure

```yaml
# Interview session configuration
interview_session:
  id: "INT-20260328-001"
  sme_id: "kapil.pant"
  sme_role: "Senior Analytics Lead"
  domain: "Commercial Analytics"
  therapy_area: "Oncology"

  # The interview follows a structured protocol per knowledge type
  modules:
    - type: "decision_heuristics"
      prompt_sequence:
        - "Walk me through a recent situation where you had to interpret an unexpected
           signal — say, a sudden drop in market share. What was your first instinct?
           What did you check? What would have been a mistake to conclude?"
        - "What are the 2-3 rules of thumb you always apply when you see {signal_type}?"
        - "When would those rules NOT apply? What's the exception?"
        - "What evidence would make you change your mind about this conclusion?"
      extraction_targets:
        - trigger_signals        # What activated the heuristic
        - decision_logic         # The if-then reasoning
        - exceptions             # When it doesn't apply
        - anti_patterns          # Common mistakes
        - evidence_thresholds    # What flips the conclusion

    - type: "data_quirks"
      prompt_sequence:
        - "What's the most important thing a new analyst needs to know about
           {data_source} that isn't in any documentation?"
        - "Have you ever seen {data_source} give misleading results? What happened?"
        - "What's your standard workaround or validation check?"
      extraction_targets:
        - data_source
        - quirk_description
        - impact_severity
        - workaround
        - validation_query

    - type: "process_knowledge"
      prompt_sequence:
        - "If you were training a new analyst to do {task_type}, what are the
           steps in order? Where do people usually go wrong?"
        - "What quality checks do you run at each step?"
        - "What are the inputs and outputs at each stage?"
      extraction_targets:
        - steps[]
        - dependencies
        - quality_checks
        - common_pitfalls

    - type: "terminology"
      prompt_sequence:
        - "What terms does this client use differently from standard industry usage?"
        - "What abbreviations trip people up in this therapy area?"
      extraction_targets:
        - canonical_term
        - client_synonyms
        - confusion_risks
```

#### Agent Conversation Flow

```
SME Interview Agent                                        SME (Human)
       │                                                       │
       │  1. "Let's capture your expertise on {domain}.        │
       │     I'll ask structured questions and turn your        │
       │     answers into reusable knowledge artifacts."        │
       │ ────────────────────────────────────────────────────▶  │
       │                                                       │
       │  2. Module: Decision Heuristics                       │
       │     "Walk me through a recent situation where..."     │
       │ ────────────────────────────────────────────────────▶  │
       │                                                       │
       │  ◀──────────────── (SME narrates their reasoning) ──  │
       │                                                       │
       │  3. EXTRACT: Parse response into structured fields    │
       │     trigger_signals: ["market_share_drop", "PA_spike"]│
       │     decision_logic: "If concurrent PA spike, check..." │
       │     exceptions: ["Unless seasonal pattern in Q4"]     │
       │                                                       │
       │  4. VALIDATE: "I understood this as: {summary}.       │
       │     Is that right? Anything to add or correct?"       │
       │ ────────────────────────────────────────────────────▶  │
       │                                                       │
       │  ◀──────────────── (SME confirms or corrects) ──────  │
       │                                                       │
       │  5. CODIFY: Generate DecisionHeuristic artifact       │
       │     → Create Delta(PROPOSED_PATTERN)                  │
       │     → Submit to DeltaStore                            │
       │     → Route for HITL review                           │
       │                                                       │
       │  6. Continue to next module...                        │
       │                                                       │
       │  7. SESSION SUMMARY:                                  │
       │     "This session produced:                           │
       │      • 3 decision heuristics (PROPOSED)               │
       │      • 2 data quirks (PROPOSED)                       │
       │      • 1 process playbook (PROPOSED)                  │
       │      • 4 jargon entries (PROPOSED)                    │
       │     All submitted for review."                        │
       │ ────────────────────────────────────────────────────▶  │
```

---

## 6. Data Models & Code Scaffolding

### 6.1 New Artifact Models (SpecOmagic Extension)

These models extend SpecOmagic's `ArtifactBase` and follow the same lifecycle, tagging, and versioning conventions.

```python
"""New artifact types for SME knowledge codification.

File: src/specomagic/models/sme_artifacts.py
Extends: specomagic.models.artifacts.ArtifactBase
"""

from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from specomagic.models.artifacts import ArtifactBase
from specomagic.models.tags import Tag


# ─── Decision Heuristic ───────────────────────────────────────────

class TriggerCondition(BaseModel):
    """A signal or condition that activates this heuristic."""
    signal_name: str                          # e.g., "market_share_drop"
    threshold: str | None = None              # e.g., "> 5% quarter-over-quarter"
    data_source: str | None = None            # e.g., "IQVIA TRx"

class AntiPattern(BaseModel):
    """A common mistake this heuristic guards against."""
    wrong_conclusion: str
    why_wrong: str
    unless_evidence: list[str] = Field(default_factory=list)

class DecisionHeuristic(ArtifactBase):
    """A codified decision rule from SME expertise.

    Maps to Onto_Wiz JudgmentPattern for reasoning engine integration.
    Captures the if-then-unless logic that senior analysts apply intuitively.
    """
    # Trigger conditions
    trigger_signals: list[TriggerCondition] = Field(default_factory=list)
    trigger_context: list[str] = Field(
        default_factory=list,
        description="Context keywords that must be present (e.g., 'specialty', 'oncology')"
    )

    # Decision logic
    decision_logic: str = Field(
        description="The core reasoning: 'When X is observed, conclude Y because Z'"
    )
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    judgment_type: str = Field(
        default="causal_hypothesis",
        description="empirical | causal_hypothesis | normative"
    )

    # Exceptions and guards
    exceptions: list[str] = Field(
        default_factory=list,
        description="Conditions under which this heuristic does NOT apply"
    )
    anti_patterns: list[AntiPattern] = Field(default_factory=list)
    evidence_required: list[str] = Field(
        default_factory=list,
        description="Evidence that must be checked before applying this heuristic"
    )

    # Outcome
    typical_outcome: str = ""
    recommended_actions: list[str] = Field(default_factory=list)

    # Provenance
    captured_from: str = ""           # "sme_interview", "game_session", "document"
    sme_id: str = ""
    sme_confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    # Scope
    scope: dict[str, str] = Field(
        default_factory=dict,
        description="therapy_area, lifecycle, geography, channel"
    )

    # Decay
    valid_for_days: int = Field(default=180, description="Days before review required")

    def to_prompt_text(self) -> str:
        lines = [f"## Decision Heuristic: {self.name}"]
        if self.trigger_signals:
            triggers = ", ".join(t.signal_name for t in self.trigger_signals)
            lines.append(f"\n**When you see:** {triggers}")
        lines.append(f"\n**Then:** {self.decision_logic}")
        if self.exceptions:
            lines.append(f"\n**UNLESS:** {'; '.join(self.exceptions)}")
        if self.anti_patterns:
            lines.append("\n**Common mistakes:**")
            for ap in self.anti_patterns:
                lines.append(f"- Do NOT conclude '{ap.wrong_conclusion}' — {ap.why_wrong}")
        if self.evidence_required:
            lines.append(f"\n**Check first:** {', '.join(self.evidence_required)}")
        return "\n".join(lines)

    def to_judgment_pattern_dict(self) -> dict:
        """Convert to Onto_Wiz JudgmentPattern-compatible dict for reasoning engine."""
        return {
            "applies_when_signals": [t.signal_name for t in self.trigger_signals],
            "applies_when_context": self.trigger_context,
            "typical_drivers": [
                {"driver": self.decision_logic, "confidence": self.confidence}
            ],
            "disallowed_drivers": [ap.wrong_conclusion for ap in self.anti_patterns],
            "judgment_type": self.judgment_type,
            "decay": {"valid_for_days": self.valid_for_days},
            "scope": self.scope,
        }


# ─── Data Quirk ───────────────────────────────────────────────────

class DataQuirk(ArtifactBase):
    """A known data limitation, bias, or gotcha.

    Maps to SpecOmagic OverrideRule (always-fire) + Onto_Wiz Guardrail.
    These are critical for analytical accuracy — they prevent silent errors.
    """
    data_source: str = Field(description="Affected data source (e.g., 'IQVIA DDD')")
    quirk_description: str = Field(description="What the quirk is and why it matters")
    impact_severity: str = Field(
        default="medium",
        description="low | medium | high | critical"
    )

    # Affected scope
    affects_metrics: list[str] = Field(
        default_factory=list,
        description="Metrics impacted (e.g., ['TRx', 'market_share'])"
    )
    affects_therapy_areas: list[str] = Field(default_factory=list)

    # Mitigation
    workaround: str = Field(default="", description="How to work around this quirk")
    validation_query: str = Field(
        default="",
        description="SQL/logic to detect when the quirk is affecting results"
    )
    cross_reference: str = Field(
        default="",
        description="Alternative data source to validate against"
    )

    # Temporal
    known_since: str = ""
    expected_fix: str | None = None   # If the data vendor plans to fix it
    seasonal: bool = False            # Does it recur at specific times?
    seasonal_pattern: str = ""        # e.g., "Q4 undercount due to holiday closures"

    def to_prompt_text(self) -> str:
        lines = [f"## Data Quirk: {self.data_source}"]
        lines.append(f"\n**WARNING [{self.impact_severity.upper()}]:** {self.quirk_description}")
        if self.affects_metrics:
            lines.append(f"**Affects:** {', '.join(self.affects_metrics)}")
        if self.workaround:
            lines.append(f"**Workaround:** {self.workaround}")
        if self.validation_query:
            lines.append(f"**Validation:** {self.validation_query}")
        return "\n".join(lines)

    def to_override_rule_dict(self) -> dict:
        """Convert to SpecOmagic OverrideRule for context assembly injection."""
        return {
            "rule": f"DATA QUIRK [{self.impact_severity.upper()}]: {self.quirk_description}. "
                    f"Workaround: {self.workaround}",
            "reason": f"Known limitation of {self.data_source} affecting "
                      f"{', '.join(self.affects_metrics)}",
        }


# ─── Process Playbook ─────────────────────────────────────────────

class PlaybookStep(BaseModel):
    """A single step in a process playbook."""
    order: int
    action: str                        # What to do
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    quality_check: str = ""            # How to verify this step
    decision_point: str = ""           # If-then branch at this step
    estimated_minutes: int = 0
    tools: list[str] = Field(default_factory=list)  # Tools/systems used
    common_mistake: str = ""

class ProcessPlaybook(ArtifactBase):
    """A step-by-step analytical workflow.

    Maps to Onto_Wiz ActionTemplate (cross-functional) +
    SpecOmagic InstructionSet (ordered rules).
    """
    task_type: str = Field(description="e.g., 'brand_share_analysis', 'launch_readiness'")
    description: str = ""

    # Steps
    steps: list[PlaybookStep] = Field(default_factory=list)

    # Dependencies
    prerequisites: list[str] = Field(
        default_factory=list,
        description="What must be true/available before starting"
    )
    required_data_sources: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)

    # Quality & timing
    estimated_total_minutes: int = 0
    common_pitfalls: list[str] = Field(default_factory=list)
    quality_criteria: list[str] = Field(
        default_factory=list,
        description="How to judge if the output is good"
    )

    # Scope
    scope: dict[str, str] = Field(default_factory=dict)

    def to_prompt_text(self) -> str:
        lines = [f"## Process Playbook: {self.name}"]
        if self.description:
            lines.append(f"\n{self.description}")
        if self.prerequisites:
            lines.append(f"\n**Prerequisites:** {', '.join(self.prerequisites)}")
        lines.append("\n### Steps")
        for step in sorted(self.steps, key=lambda s: s.order):
            lines.append(f"\n**Step {step.order}: {step.action}**")
            if step.inputs:
                lines.append(f"  Inputs: {', '.join(step.inputs)}")
            if step.outputs:
                lines.append(f"  Outputs: {', '.join(step.outputs)}")
            if step.quality_check:
                lines.append(f"  Quality check: {step.quality_check}")
            if step.decision_point:
                lines.append(f"  Decision: {step.decision_point}")
            if step.common_mistake:
                lines.append(f"  Caution: {step.common_mistake}")
        if self.common_pitfalls:
            lines.append("\n### Common Pitfalls")
            for p in self.common_pitfalls:
                lines.append(f"- {p}")
        return "\n".join(lines)


# ─── Domain Pack Manifest ─────────────────────────────────────────

class PackDependency(BaseModel):
    """A dependency on another domain pack."""
    pack_id: str
    version: str = ">=1.0.0"
    layer_type: str = "base"

class QualityMetrics(BaseModel):
    """Auto-computed quality metrics for a domain pack."""
    total_artifacts: int = 0
    active_artifacts: int = 0
    stale_artifacts: int = 0
    avg_freshness_days: float = 0.0
    coverage_score: float = 0.0
    sme_review_rate: float = 0.0

class DomainPackManifest(BaseModel):
    """Manifest for a Domain Pack — the unit of knowledge distribution."""
    id: str
    name: str
    version: str
    pack_type: str = "base"           # base | therapy_area | client

    # Authorship
    created_by: str = ""
    owner_team: str = ""
    review_cycle: str = "quarterly"
    last_reviewed: datetime | None = None
    status: str = "draft"             # draft | active | deprecated

    # Scope
    therapeutic_areas: list[str] = Field(default_factory=list)
    analytics_domains: list[str] = Field(default_factory=list)
    geography: str = "US"

    # Contents (auto-populated)
    artifact_counts: dict[str, int] = Field(default_factory=dict)

    # Dependencies
    dependencies: list[PackDependency] = Field(default_factory=list)

    # Quality
    quality: QualityMetrics = Field(default_factory=QualityMetrics)

    # Compatibility
    min_specomagic_version: str = "0.6.0"
    min_onto_wiz_version: str = "0.4.0"
```

### 6.2 SME Interview Agent (Core Module)

```python
"""SME Interview Agent — structured knowledge elicitation.

File: src/specomagic/capture/interview_agent.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol
from uuid import uuid4


class KnowledgeModule(str, Enum):
    """Types of knowledge to elicit from SMEs."""
    DECISION_HEURISTICS = "decision_heuristics"
    DATA_QUIRKS = "data_quirks"
    PROCESS_KNOWLEDGE = "process_knowledge"
    TERMINOLOGY = "terminology"
    FEW_SHOT_PATTERNS = "few_shot_patterns"


@dataclass
class InterviewConfig:
    """Configuration for an SME interview session."""
    sme_id: str
    sme_role: str
    domain: str                           # "Commercial Analytics", "Market Access", etc.
    therapy_area: str = ""
    client_context: str = ""              # Optional client-specific framing
    modules: list[KnowledgeModule] = field(
        default_factory=lambda: list(KnowledgeModule)
    )
    max_questions_per_module: int = 5
    auto_validate: bool = True            # Ask SME to confirm extractions


@dataclass
class InterviewTurn:
    """A single turn in the interview conversation."""
    role: str                             # "agent" or "sme"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    module: KnowledgeModule | None = None
    extracted_artifacts: list[dict] = field(default_factory=list)


@dataclass
class InterviewSession:
    """Complete record of an SME interview session."""
    id: str = field(default_factory=lambda: f"INT-{uuid4().hex[:12]}")
    config: InterviewConfig = field(default_factory=lambda: InterviewConfig(
        sme_id="", sme_role="", domain=""
    ))
    turns: list[InterviewTurn] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    # Outputs
    artifacts_proposed: list[str] = field(default_factory=list)  # Artifact IDs
    delta_ids: list[str] = field(default_factory=list)           # Delta IDs

    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts_proposed)


class LLMService(Protocol):
    """Protocol for LLM interaction (matches both SpecOmagic and Onto_Wiz patterns)."""
    def complete(self, prompt: str, system: str = "") -> str: ...


# ─── Prompt Templates ─────────────────────────────────────────────

INTERVIEW_PROMPTS: dict[KnowledgeModule, list[str]] = {
    KnowledgeModule.DECISION_HEURISTICS: [
        "Walk me through a recent situation where you had to interpret an unexpected "
        "analytical signal in {domain}. What was your first instinct? What did you "
        "check first? What would have been a mistake to conclude?",

        "What are the 2-3 rules of thumb you always apply when you see "
        "{signal_context}? When would those rules NOT apply?",

        "What evidence would make you change your mind about a conclusion "
        "in {domain}? What's the threshold for 'this is noise' vs 'this is real'?",

        "What's the most common mistake a junior analyst makes when interpreting "
        "{metric_context} results?",
    ],

    KnowledgeModule.DATA_QUIRKS: [
        "What's the single most important thing a new analyst needs to know "
        "about {data_source} that isn't in any documentation?",

        "Have you ever seen {data_source} give misleading results? What happened "
        "and how did you catch it?",

        "What's your standard validation check or cross-reference when working "
        "with {data_source}?",
    ],

    KnowledgeModule.PROCESS_KNOWLEDGE: [
        "If you were training someone from scratch to do {task_type}, "
        "what are the steps in order? Where do people usually go wrong?",

        "What quality checks do you run at each step? What tells you "
        "the output is good vs questionable?",

        "What are the dependencies between steps? What can be done in "
        "parallel and what must be sequential?",
    ],

    KnowledgeModule.TERMINOLOGY: [
        "What terms does this {context} use differently from standard "
        "industry usage? Any terms that trip people up?",

        "What abbreviations or acronyms have different meanings depending "
        "on who's using them in {domain}?",
    ],

    KnowledgeModule.FEW_SHOT_PATTERNS: [
        "Can you show me a good example of {task_type} output? What makes "
        "it good vs a mediocre version?",

        "If I gave you this input: {example_input}, what would the ideal "
        "output look like and why?",
    ],
}


EXTRACTION_SYSTEM_PROMPT = """You are a knowledge extraction agent. Given an SME's
response to an interview question, extract structured knowledge artifacts.

RULES:
1. Extract ONLY what the SME explicitly stated — never infer or hallucinate.
2. Preserve the SME's language for decision logic and descriptions.
3. Flag uncertainty: if the SME hedged ("usually", "mostly"), set confidence lower.
4. Identify anti-patterns: whenever the SME says "don't", "mistake", "wrong",
   capture it as an anti_pattern.
5. Tag with appropriate dimensions from: therapy_area, drug, indication,
   data_source, analytics_domain, task_type, geography.

Output JSON matching the artifact schema for {artifact_type}.
"""


VALIDATION_PROMPT = """Based on our conversation, I've captured the following
knowledge artifact:

{artifact_summary}

Is this accurate? Would you like to:
1. Confirm as-is
2. Correct something specific
3. Add more detail
4. Discard this one"""


class InterviewAgent:
    """Conducts structured SME interviews and produces knowledge artifacts.

    Usage:
        agent = InterviewAgent(llm=llm_client, store=knowledge_store)
        session = agent.start_session(InterviewConfig(
            sme_id="kapil.pant",
            sme_role="Senior Analytics Lead",
            domain="Commercial Analytics",
            therapy_area="Oncology",
        ))

        # Agent generates first question
        question = agent.next_question(session)

        # SME responds (in chat interface or API)
        artifacts = agent.process_response(session, sme_response)

        # Agent validates with SME
        validation = agent.validate_extraction(session, artifacts[0])

        # On confirmation, submit to governance
        deltas = agent.submit_to_governance(session)
    """

    def __init__(
        self,
        llm: LLMService,
        store: Any = None,           # KnowledgeStore
        delta_store: Any = None,     # DeltaStore (Onto_Wiz)
    ):
        self.llm = llm
        self.store = store
        self.delta_store = delta_store
        self._sessions: dict[str, InterviewSession] = {}

    def start_session(self, config: InterviewConfig) -> InterviewSession:
        """Initialise a new interview session."""
        session = InterviewSession(config=config)
        self._sessions[session.id] = session

        # Add opening turn
        opening = InterviewTurn(
            role="agent",
            content=f"Let's capture your expertise on {config.domain}"
                    f"{f' ({config.therapy_area})' if config.therapy_area else ''}. "
                    f"I'll ask structured questions across {len(config.modules)} areas "
                    f"and turn your answers into reusable knowledge artifacts. "
                    f"Everything goes through review before it's active.",
        )
        session.turns.append(opening)
        return session

    def next_question(self, session: InterviewSession) -> str:
        """Generate the next interview question based on session state."""
        current_module = self._get_current_module(session)
        if current_module is None:
            return self._generate_closing(session)

        prompts = INTERVIEW_PROMPTS.get(current_module, [])
        q_index = self._get_question_index(session, current_module)

        if q_index >= len(prompts) or q_index >= session.config.max_questions_per_module:
            return self.next_question(session)

        template = prompts[q_index]
        question = self._fill_template(template, session.config)

        turn = InterviewTurn(role="agent", content=question, module=current_module)
        session.turns.append(turn)
        return question

    def process_response(
        self, session: InterviewSession, response: str
    ) -> list[dict]:
        """Process an SME response: record it and extract artifacts."""
        current_module = self._get_current_module(session)

        turn = InterviewTurn(
            role="sme", content=response, module=current_module
        )
        session.turns.append(turn)

        artifact_type = self._module_to_artifact_type(current_module)
        extraction_prompt = self._build_extraction_prompt(
            response, artifact_type, session.config
        )

        extraction_result = self.llm.complete(
            prompt=extraction_prompt,
            system=EXTRACTION_SYSTEM_PROMPT.format(artifact_type=artifact_type),
        )

        artifacts = self._parse_extraction(extraction_result, artifact_type)
        turn.extracted_artifacts = artifacts
        return artifacts

    def validate_extraction(
        self, session: InterviewSession, artifact: dict
    ) -> str:
        """Generate a validation prompt for the SME to confirm."""
        summary = self._format_artifact_summary(artifact)
        return VALIDATION_PROMPT.format(artifact_summary=summary)

    def submit_to_governance(self, session: InterviewSession) -> list[str]:
        """Submit all confirmed artifacts through the governance pipeline."""
        delta_ids = []
        for turn in session.turns:
            for artifact in turn.extracted_artifacts:
                if artifact.get("confirmed", False):
                    delta_id = self._create_delta(artifact, session)
                    delta_ids.append(delta_id)

        session.delta_ids = delta_ids
        session.completed_at = datetime.now()
        return delta_ids

    # ─── Private helpers ──────────────────────────────────────

    def _get_current_module(self, session: InterviewSession) -> KnowledgeModule | None:
        completed_modules = set()
        for module in session.config.modules:
            q_count = self._get_question_index(session, module)
            prompts = INTERVIEW_PROMPTS.get(module, [])
            max_q = min(len(prompts), session.config.max_questions_per_module)
            if q_count >= max_q:
                completed_modules.add(module)

        for module in session.config.modules:
            if module not in completed_modules:
                return module
        return None

    def _get_question_index(
        self, session: InterviewSession, module: KnowledgeModule
    ) -> int:
        return sum(
            1 for t in session.turns
            if t.role == "agent" and t.module == module
        )

    def _fill_template(self, template: str, config: InterviewConfig) -> str:
        replacements = {
            "{domain}": config.domain,
            "{therapy_area}": config.therapy_area or "your area",
            "{data_source}": "the primary data source you use",
            "{task_type}": "the most common analytical task",
            "{signal_context}": "a key metric change",
            "{metric_context}": config.domain,
            "{context}": config.client_context or config.domain,
            "{example_input}": "a standard analytical query",
        }
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        return result

    def _module_to_artifact_type(self, module: KnowledgeModule | None) -> str:
        mapping = {
            KnowledgeModule.DECISION_HEURISTICS: "DecisionHeuristic",
            KnowledgeModule.DATA_QUIRKS: "DataQuirk",
            KnowledgeModule.PROCESS_KNOWLEDGE: "ProcessPlaybook",
            KnowledgeModule.TERMINOLOGY: "JargonMap",
            KnowledgeModule.FEW_SHOT_PATTERNS: "FewShotLibrary",
        }
        return mapping.get(module, "InstructionSet")

    def _build_extraction_prompt(
        self, response: str, artifact_type: str, config: InterviewConfig
    ) -> str:
        return (
            f"SME Response (from {config.sme_role} in {config.domain}):\n\n"
            f"{response}\n\n"
            f"Extract a {artifact_type} artifact from this response. "
            f"Include all relevant fields. Output valid JSON."
        )

    def _parse_extraction(self, llm_output: str, artifact_type: str) -> list[dict]:
        import json
        try:
            data = json.loads(llm_output)
            if isinstance(data, list):
                return data
            return [data]
        except json.JSONDecodeError:
            return [{"raw_extraction": llm_output, "artifact_type": artifact_type}]

    def _format_artifact_summary(self, artifact: dict) -> str:
        lines = []
        for key, value in artifact.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                lines.append(f"  {key}:")
                for item in value:
                    lines.append(f"    - {item}")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    def _create_delta(self, artifact: dict, session: InterviewSession) -> str:
        delta_id = f"DELTA-{uuid4().hex[:8]}"

        if self.delta_store:
            from core.models import Delta, DeltaType, DeltaStatus, BlastRadius

            delta = Delta(
                id=delta_id,
                type=DeltaType.PROPOSED_PATTERN,
                status=DeltaStatus.PROPOSED,
                content=artifact,
                confidence=artifact.get("confidence", 0.7),
                evidence_pointers=[f"interview:{session.id}"],
                blast_radius=BlastRadius.MEDIUM,
                impacted_missions=[],
                impacted_personas=[session.config.sme_role],
                owner=session.config.sme_id,
                source_type="interview",
                source_id=session.id,
            )
            self.delta_store.propose(delta)

        return delta_id

    def _generate_closing(self, session: InterviewSession) -> str:
        artifact_count = sum(
            len(t.extracted_artifacts)
            for t in session.turns
            if t.extracted_artifacts
        )
        return (
            f"Excellent — we've covered all {len(session.config.modules)} knowledge areas. "
            f"This session produced {artifact_count} knowledge artifacts, "
            f"all submitted as proposals for review. "
            f"Thank you for your expertise, {session.config.sme_id}."
        )
```

### 6.3 Domain Pack Builder

```python
"""Domain Pack Builder — assembles and validates domain packs.

File: src/specomagic/packs/builder.py
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class DomainPackBuilder:
    """Builds, validates, and exports Domain Packs.

    Usage:
        builder = DomainPackBuilder(store=knowledge_store)

        # Build from tagged artifacts
        pack = builder.build(
            pack_id="dp-commercial-analytics-v2",
            name="Commercial Analytics Base Pack",
            pack_type="base",
            tag_filters={"analytics_domain": ["Commercial Analytics"]},
            owner="kapil.pant@zs.com",
        )

        # Validate
        issues = builder.validate(pack)

        # Export to directory
        builder.export(pack, Path("./packs/commercial_analytics/"))

        # Compute quality metrics
        metrics = builder.compute_quality(pack)
    """

    def __init__(self, store: Any):
        self.store = store

    def build(
        self,
        pack_id: str,
        name: str,
        pack_type: str = "base",
        tag_filters: dict[str, list[str]] | None = None,
        artifact_ids: list[str] | None = None,
        owner: str = "",
        therapeutic_areas: list[str] | None = None,
        analytics_domains: list[str] | None = None,
        geography: str = "US",
        dependencies: list[dict] | None = None,
    ) -> dict:
        """Build a domain pack from store artifacts."""
        artifacts = []

        if tag_filters:
            from specomagic.models.tags import Tag, TagDimension, TagQuery
            tags = []
            for dim, values in tag_filters.items():
                for v in values:
                    tags.append(Tag(dimension=TagDimension(dim), value=v))
            query = TagQuery(tags=tags, min_match_ratio=0.3)
            results = self.store.query_scored(query)
            artifacts.extend([a for a, _ in results])

        if artifact_ids:
            for aid in artifact_ids:
                a = self.store.get(aid)
                if a and a not in artifacts:
                    artifacts.append(a)

        if pack_type != "draft":
            artifacts = [
                a for a in artifacts
                if a.lifecycle.value in ("active", "verified")
            ]

        by_type: dict[str, list] = {}
        for a in artifacts:
            by_type.setdefault(a.artifact_type, []).append(a)

        manifest = {
            "id": pack_id,
            "name": name,
            "version": "1.0.0",
            "pack_type": pack_type,
            "created_by": owner,
            "status": "draft",
            "therapeutic_areas": therapeutic_areas or ["all"],
            "analytics_domains": analytics_domains or [],
            "geography": geography,
            "artifact_counts": {k: len(v) for k, v in by_type.items()},
            "dependencies": dependencies or [],
            "created_at": datetime.now().isoformat(),
        }

        return {
            "manifest": manifest,
            "artifacts": by_type,
            "total_artifacts": len(artifacts),
        }

    def validate(self, pack: dict) -> list[str]:
        """Validate a domain pack for completeness and consistency."""
        issues = []
        manifest = pack.get("manifest", {})
        artifacts = pack.get("artifacts", {})

        if pack.get("total_artifacts", 0) == 0:
            issues.append("Pack contains no artifacts")

        essential = {"InstructionSet", "JargonMap", "EntityRegistry"}
        present = set(artifacts.keys())
        missing = essential - present
        if missing:
            issues.append(f"Missing essential artifact types: {missing}")

        for atype, arts in artifacts.items():
            for a in arts:
                if hasattr(a, "updated_at"):
                    age = (datetime.now() - a.updated_at).days
                    if age > 180:
                        issues.append(
                            f"Stale artifact: {a.id} ({a.name}) — "
                            f"last updated {age} days ago"
                        )

        entity_ids = set()
        for a in artifacts.get("EntityRegistry", []):
            for e in a.entities:
                entity_ids.add(e.id)

        for a in artifacts.get("InstructionSet", []):
            for rule in a.rules:
                for ref in rule.applies_to:
                    if ref and ref not in entity_ids:
                        issues.append(
                            f"Rule {rule.id} references unknown entity: {ref}"
                        )

        return issues

    def export(self, pack: dict, output_dir: Path) -> Path:
        """Export a domain pack to a directory structure."""
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = output_dir / "pack.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(pack["manifest"], f, default_flow_style=False, sort_keys=False)

        type_to_dir = {
            "InstructionSet": "instruction_sets",
            "JargonMap": "jargon_maps",
            "EntityRegistry": "entity_registry",
            "FewShotLibrary": "few_shots",
            "Taxonomy": "taxonomies",
            "OverrideRule": "overrides",
            "PromptTemplate": "templates",
            "DecisionHeuristic": "decision_heuristics",
            "DataQuirk": "data_quirks",
            "ProcessPlaybook": "process_playbooks",
        }

        for atype, arts in pack.get("artifacts", {}).items():
            dir_name = type_to_dir.get(atype, atype.lower())
            type_dir = output_dir / dir_name
            type_dir.mkdir(exist_ok=True)

            for a in arts:
                file_path = type_dir / f"{a.id}.yaml"
                data = a.model_dump() if hasattr(a, "model_dump") else a.__dict__
                with open(file_path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return output_dir

    def compute_quality(self, pack: dict) -> dict:
        """Compute quality metrics for a domain pack."""
        artifacts = []
        for arts in pack.get("artifacts", {}).values():
            artifacts.extend(arts)

        total = len(artifacts)
        if total == 0:
            return {"total_artifacts": 0}

        active = sum(1 for a in artifacts if a.lifecycle.value == "active")
        reviewed = sum(1 for a in artifacts if a.reviewed_by)

        ages = []
        for a in artifacts:
            if hasattr(a, "updated_at") and a.updated_at:
                ages.append((datetime.now() - a.updated_at).days)

        stale = sum(1 for age in ages if age > 180)

        return {
            "total_artifacts": total,
            "active_artifacts": active,
            "stale_artifacts": stale,
            "avg_freshness_days": sum(ages) / len(ages) if ages else 0,
            "sme_review_rate": reviewed / total if total else 0,
            "coverage_score": active / total if total else 0,
        }
```

---

## 7. Governance & Quality Gates

### 7.1 Unified Governance Model

All knowledge — whether from documents, SME interviews, game sessions, or feedback — flows through the same governance pipeline. The key insight is that Onto_Wiz's Delta Model and SpecOmagic's lifecycle gates are **complementary**, not competing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED GOVERNANCE PIPELINE                      │
│                                                                     │
│  Knowledge Source        Delta Model (Onto_Wiz)     Lifecycle Gates │
│  ─────────────          ────────────────────        (SpecOmagic)    │
│                                                                     │
│  SME Interview ──┐                                                  │
│  Game Session  ──┤      ┌──────────┐                                │
│  Feedback Loop ──┼─────▶│ PROPOSED │─── Auto-classify ──┐          │
│                  │      └────┬─────┘    (judgment_type)  │          │
│                  │           │                           │          │
│  Document Ingest─┘      ┌───▼────────┐              ┌───▼───┐      │
│                         │ REVIEW     │◀─────────────│ DRAFT │      │
│                         │ (routed by │              └───────┘      │
│                         │  blast     │                              │
│                         │  radius)   │                              │
│                         └───┬────────┘                              │
│                             │                                       │
│              ┌──────────────┼──────────────┐                       │
│              │              │              │                        │
│         ┌────▼─────┐  ┌────▼─────┐  ┌────▼──────┐                │
│         │ AUTO     │  │ DOMAIN   │  │ GOVERNANCE │                │
│         │ APPROVE  │  │ EXPERT   │  │ BOARD      │                │
│         │ (low     │  │ REVIEW   │  │ (normative │                │
│         │  blast)  │  │ (24h SLA)│  │  5h SLA)   │                │
│         └────┬─────┘  └────┬─────┘  └────┬──────┘                │
│              │              │              │                        │
│              └──────────────┼──────────────┘                       │
│                             │                                       │
│                        ┌────▼─────┐     ┌──────────┐               │
│                        │ APPROVED │────▶│ VERIFIED │               │
│                        └────┬─────┘     └────┬─────┘               │
│                             │                │                      │
│                        ┌────▼─────┐     ┌────▼─────┐               │
│                        │ MERGED   │────▶│ ACTIVE   │               │
│                        │ (in KB)  │     │ (in prod)│               │
│                        └──────────┘     └──────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Quality Gates per Knowledge Type

| Knowledge Type | Judgment Type | Default Blast Radius | Review Requirement | Freshness Window |
|---|---|---|---|---|
| Terminology/Jargon | EMPIRICAL | LOW | Auto-approve if confidence > 0.85 | 365 days |
| Entity records | EMPIRICAL | LOW | Auto-approve if from trusted source | 180 days |
| Data Quirks | CAUSAL | MEDIUM | Domain expert review (24h SLA) | 90 days |
| Decision Heuristics | CAUSAL | MEDIUM–HIGH | Domain expert review + peer validation | 180 days |
| Process Playbooks | CAUSAL | MEDIUM | Domain expert review | 180 days |
| Few-Shot Examples | EMPIRICAL | LOW | Quality score > 0.8 auto-approves | 90 days |
| Guardrails / Overrides | NORMATIVE | HIGH | Governance board (5h SLA) | Quarterly review cycle |
| Instruction Sets | CAUSAL | MEDIUM | Domain expert review | 180 days |

### 7.3 Conflict Detection

When a new artifact enters the pipeline, the system checks for conflicts with existing knowledge:

- **Contradicting heuristics:** Two DecisionHeuristics with overlapping triggers but different decision_logic → escalate for consolidation
- **Stale overrides:** A DataQuirk referencing a data source quirk that's been fixed → flag for deprecation
- **Scope collision:** Two InstructionSets covering the same task_type + therapy_area → compare rules, suggest merge
- **Cross-layer conflict:** Client overlay contradicts base pack without explicit override → warn the curator

> **Design Principle: Fail Loud**
> Conflicts are surfaced, never silently resolved. The system proposes a resolution (merge, override, deprecate) but a human must confirm. This is enforced by Onto_Wiz's Delta Model — conflicting deltas are routed to the escalated queue.

---

## 8. Integration with Onto_Wiz & SpecOmagic

### 8.1 Integration Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE CODIFICATION AGENT                         │
│                                                                              │
│  ┌───────────────────┐    ┌─────────────────────┐    ┌───────────────────┐  │
│  │ InterviewAgent     │    │ DomainPackBuilder    │    │ FeedbackToDelta   │  │
│  │ (New)             │    │ (New)               │    │ (New)             │  │
│  └─────────┬─────────┘    └──────────┬──────────┘    └─────────┬─────────┘  │
│            │                         │                          │            │
│  ┌─────────▼─────────────────────────▼──────────────────────────▼─────────┐  │
│  │                    INTEGRATION LAYER (New)                             │  │
│  │                                                                        │  │
│  │  ArtifactBridge:                                                       │  │
│  │  • DecisionHeuristic ↔ JudgmentPattern (bidirectional conversion)     │  │
│  │  • DataQuirk ↔ Guardrail + OverrideRule (dual output)                 │  │
│  │  • ProcessPlaybook ↔ ActionTemplate + InstructionSet (dual output)    │  │
│  │                                                                        │  │
│  │  GovernanceBridge:                                                     │  │
│  │  • SpecOmagic lifecycle → Onto_Wiz DeltaStatus mapping                │  │
│  │  • Onto_Wiz Delta approval → SpecOmagic lifecycle transition          │  │
│  │                                                                        │  │
│  │  StoreBridge:                                                          │  │
│  │  • LayeredStore → JudgmentStore synchronisation                       │  │
│  │  • DeltaStore → KnowledgeStore promotion                              │  │
│  └───────────┬──────────────────────────────────┬────────────────────────┘  │
│              │                                  │                           │
└──────────────┼──────────────────────────────────┼───────────────────────────┘
               │                                  │
    ┌──────────▼──────────┐           ┌───────────▼──────────┐
    │      Onto_Wiz       │           │     SpecOmagic       │
    │                     │           │                      │
    │ • DeltaStore        │           │ • KnowledgeStore     │
    │ • JudgmentStore     │           │ • LayeredStore       │
    │ • ReasoningEngine   │           │ • ContextAssembler   │
    │ • SemanticStore     │           │ • ExtractionPipeline │
    │ • GraphStore        │           │ • FeedbackStore      │
    │ • PromotionPipeline │           │ • SDK (get_context)  │
    └─────────────────────┘           └──────────────────────┘
```

### 8.2 Artifact Bridge — Code Scaffold

```python
"""Bidirectional conversion between codification artifacts and system models.

File: src/integration/artifact_bridge.py
"""

from __future__ import annotations
from typing import Any


class ArtifactBridge:
    """Converts between Domain Pack artifacts and Onto_Wiz/SpecOmagic models."""

    @staticmethod
    def heuristic_to_judgment_pattern(heuristic: Any) -> dict:
        """Convert DecisionHeuristic → Onto_Wiz JudgmentPattern fields."""
        return {
            "id": f"JP-{heuristic.id}",
            "version": str(heuristic.version) + ".0.0",
            "status": _lifecycle_to_artifact_status(heuristic.lifecycle.value),
            "applies_when_signals": [
                t.signal_name for t in heuristic.trigger_signals
            ],
            "applies_when_context": heuristic.trigger_context,
            "typical_drivers": [{
                "driver": heuristic.decision_logic,
                "confidence": heuristic.confidence,
                "evidence": heuristic.evidence_required,
            }],
            "disallowed_drivers": [
                ap.wrong_conclusion for ap in heuristic.anti_patterns
            ],
            "governance": {
                "owner": heuristic.sme_id or heuristic.created_by or "",
                "review_cycle": "quarterly",
                "risk_class": "decision_support",
            },
            "decay": {"valid_for_days": heuristic.valid_for_days},
            "judgment_type": heuristic.judgment_type,
            "scope": heuristic.scope,
            "trained_from_scenarios": [],
        }

    @staticmethod
    def judgment_pattern_to_heuristic(pattern: Any) -> dict:
        """Convert Onto_Wiz JudgmentPattern → DecisionHeuristic fields."""
        return {
            "id": f"DH-{pattern.id}",
            "name": f"Heuristic from pattern {pattern.id}",
            "trigger_signals": [
                {"signal_name": s} for s in pattern.applies_when_signals
            ],
            "trigger_context": pattern.applies_when_context,
            "decision_logic": (
                pattern.typical_drivers[0].driver
                if pattern.typical_drivers else ""
            ),
            "confidence": (
                pattern.typical_drivers[0].confidence
                if pattern.typical_drivers else 0.5
            ),
            "anti_patterns": [
                {"wrong_conclusion": d, "why_wrong": "Disallowed by learned pattern"}
                for d in pattern.disallowed_drivers
            ],
            "scope": {
                "therapy_area": pattern.scope.therapeutic_area if pattern.scope else "",
                "lifecycle": pattern.scope.lifecycle if pattern.scope else "",
                "geography": pattern.scope.geography if pattern.scope else "",
            },
            "valid_for_days": (
                pattern.decay.valid_for_days if pattern.decay else 180
            ),
            "judgment_type": pattern.judgment_type.value,
        }

    @staticmethod
    def quirk_to_guardrail(quirk: Any) -> dict:
        """Convert DataQuirk → Onto_Wiz Guardrail fields."""
        return {
            "id": f"GR-{quirk.id}",
            "status": _lifecycle_to_artifact_status(quirk.lifecycle.value),
            "blocks_action_types": ["data_interpretation"],
            "blocks_drivers": quirk.affects_metrics,
            "unless_evidence": [quirk.validation_query] if quirk.validation_query else [],
            "governance": {
                "owner": quirk.created_by or "",
                "risk_class": _severity_to_risk_class(quirk.impact_severity),
            },
            "log_all_invocations": quirk.impact_severity in ("high", "critical"),
            "escalate_on_override_attempt": quirk.impact_severity == "critical",
        }

    @staticmethod
    def quirk_to_override_rule(quirk: Any) -> dict:
        """Convert DataQuirk → SpecOmagic OverrideRule fields."""
        return {
            "id": f"OR-{quirk.id}",
            "name": f"Data Quirk: {quirk.data_source}",
            "trigger_tags": [
                {"dimension": "data_source", "value": quirk.data_source}
            ],
            "rule": (
                f"DATA QUIRK [{quirk.impact_severity.upper()}]: "
                f"{quirk.quirk_description}. "
                f"Workaround: {quirk.workaround}"
            ),
            "reason": (
                f"Known limitation of {quirk.data_source} "
                f"affecting {', '.join(quirk.affects_metrics)}"
            ),
        }

    @staticmethod
    def playbook_to_action_template(playbook: Any) -> dict:
        """Convert ProcessPlaybook → Onto_Wiz ActionTemplate fields."""
        actions_by_function: dict[str, list] = {}
        for step in playbook.steps:
            function = "analytics"
            for tool in step.tools:
                if "field" in tool.lower():
                    function = "field"
                elif "access" in tool.lower() or "payer" in tool.lower():
                    function = "access"
                elif "medical" in tool.lower():
                    function = "medical"

            actions_by_function.setdefault(function, []).append({
                "action": step.action,
                "priority": "high" if step.order <= 2 else "medium",
                "owner_function": function,
            })

        return {
            "id": f"AT-{playbook.id}",
            "status": _lifecycle_to_artifact_status(playbook.lifecycle.value),
            "brand_actions": actions_by_function.get("brand", []),
            "field_actions": actions_by_function.get("field", []),
            "access_actions": actions_by_function.get("access", []),
            "medical_actions": actions_by_function.get("medical", []),
        }

    @staticmethod
    def playbook_to_instruction_set(playbook: Any) -> dict:
        """Convert ProcessPlaybook → SpecOmagic InstructionSet fields."""
        rules = []
        for step in playbook.steps:
            rule = {
                "id": f"R{step.order:03d}",
                "rule": step.action,
                "priority": step.order,
                "condition": step.decision_point or None,
                "source": f"ProcessPlaybook:{playbook.id}",
            }
            rules.append(rule)

            if step.quality_check:
                rules.append({
                    "id": f"R{step.order:03d}-QC",
                    "rule": f"Quality check: {step.quality_check}",
                    "priority": step.order,
                    "condition": f"After step {step.order}",
                    "source": f"ProcessPlaybook:{playbook.id}",
                })

        return {
            "id": f"IS-{playbook.id}",
            "name": playbook.name,
            "scope": playbook.scope,
            "context": playbook.description,
            "rules": rules,
            "warnings": playbook.common_pitfalls,
        }


def _lifecycle_to_artifact_status(lifecycle: str) -> str:
    """Map SpecOmagic lifecycle to Onto_Wiz ArtifactStatus."""
    mapping = {
        "draft": "draft",
        "review": "draft",
        "verified": "approved",
        "active": "approved",
        "deprecated": "deprecated",
        "archived": "deprecated",
    }
    return mapping.get(lifecycle, "draft")


def _severity_to_risk_class(severity: str) -> str:
    """Map DataQuirk severity to Onto_Wiz RiskClass."""
    mapping = {
        "low": "advisory",
        "medium": "decision_support",
        "high": "restricted",
        "critical": "restricted",
    }
    return mapping.get(severity, "decision_support")
```

### 8.3 ContextAssembler Extension

The SpecOmagic ContextAssembler needs to be extended to include the new artifact types in its priority ordering:

```python
# Extended priority ordering for context assembly:
#
# 1. Guardrails / Override Rules     (NEVER cut — safety constraints)
# 2. Data Quirks                     (NEVER cut — accuracy constraints)
# 3. Decision Heuristics             (by match_score — learned judgment)
# 4. Instruction Sets / Process Steps (by relevance — analytical rules)
# 5. Jargon Maps                     (terminology resolution)
# 6. Entity context                  (reference data)
# 7. Few-Shot Examples               (cut first — examples are helpful but not critical)
#
# Token budget allocation (for 3000-token budget):
#   Guardrails + Quirks:    ~400 tokens  (protected)
#   Heuristics:             ~600 tokens
#   Instructions + Process: ~800 tokens
#   Jargon + Entities:      ~600 tokens
#   Few-Shots:              ~600 tokens  (flexible, cut first)
```

---

## 9. The Agentic Loop: From Capture to Deployment

The complete lifecycle of a piece of SME knowledge, from initial capture to production use and continuous improvement:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    THE KNOWLEDGE LIFECYCLE                           │
│                                                                      │
│    ① CAPTURE                                                        │
│    ┌─────────────────────────────────────┐                          │
│    │ SME Interview Agent asks:           │                          │
│    │ "When PA reject rate spikes, what   │                          │
│    │  do you check first?"               │                          │
│    │                                     │                          │
│    │ SME: "I look at whether there's a   │                          │
│    │ new PA requirement or if it's a     │                          │
│    │ seasonal pattern. If reject rate    │                          │
│    │ > 30% AND no peer-to-peer, it's    │                          │
│    │ definitely an access barrier."      │                          │
│    └────────────────┬────────────────────┘                          │
│                     │                                                │
│    ② EXTRACT        ▼                                               │
│    ┌─────────────────────────────────────┐                          │
│    │ DecisionHeuristic {                 │                          │
│    │   trigger: PA_reject_rate > 30%     │                          │
│    │   + no_peer_to_peer                 │                          │
│    │   logic: "Access barrier — escalate │                          │
│    │   to MSL team"                      │                          │
│    │   exceptions: ["seasonal Q4"]       │                          │
│    │   anti_pattern: "Don't assume       │                          │
│    │   field execution failure"          │                          │
│    │ }                                   │                          │
│    └────────────────┬────────────────────┘                          │
│                     │                                                │
│    ③ GOVERN         ▼                                               │
│    ┌─────────────────────────────────────┐                          │
│    │ Delta(PROPOSED_PATTERN)             │                          │
│    │ → classified as CAUSAL_HYPOTHESIS   │                          │
│    │ → blast_radius: MEDIUM             │                          │
│    │ → routed to domain_expert          │                          │
│    │ → SLA: 24 hours                    │                          │
│    │                                     │                          │
│    │ Reviewer: "Confirmed. Adding       │                          │
│    │ evidence threshold: > 2 months."   │                          │
│    │ → APPROVED → MERGED                │                          │
│    └────────────────┬────────────────────┘                          │
│                     │                                                │
│    ④ DISTRIBUTE     ▼                                               │
│    ┌─────────────────────────────────────┐                          │
│    │ Added to:                           │                          │
│    │ • SpecOmagic KB (DH artifact)      │                          │
│    │ • Onto_Wiz JudgmentStore (pattern) │                          │
│    │ • Commercial Analytics Pack v2.2    │                          │
│    │                                     │                          │
│    │ Available via:                      │                          │
│    │ • SDK: get_context("PA rejection") │                          │
│    │ • API: /context                    │                          │
│    │ • Reasoning: engine.reason()       │                          │
│    └────────────────┬────────────────────┘                          │
│                     │                                                │
│    ⑤ USE            ▼                                               │
│    ┌─────────────────────────────────────┐                          │
│    │ Agent processes query:              │                          │
│    │ "Why did market share drop in Q1?" │                          │
│    │                                     │                          │
│    │ ContextAssembler injects:          │                          │
│    │ • Heuristic: PA reject threshold   │                          │
│    │ • Quirk: IQVIA SP undercount       │                          │
│    │ • Override: Check seasonal pattern │                          │
│    │                                     │                          │
│    │ Agent output is grounded in curated │                          │
│    │ domain knowledge, not raw retrieval │                          │
│    └────────────────┬────────────────────┘                          │
│                     │                                                │
│    ⑥ IMPROVE        ▼                                               │
│    ┌─────────────────────────────────────┐                          │
│    │ User feedback:                      │                          │
│    │ "The PA threshold should be 25%    │                          │
│    │ for specialty drugs, not 30%"      │                          │
│    │                                     │                          │
│    │ → FeedbackPipeline → ArtifactSugg. │                          │
│    │ → New Delta(PROPOSED_PATTERN)       │                          │
│    │ → Version bumped: v1 → v2          │                          │
│    │ → Reviewed → Active                │                          │
│    │                                     │                          │
│    │ Knowledge improves with every use. │                          │
│    └─────────────────────────────────────┘                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Weeks 1–2)

**Goal:** New artifact models + basic capture

- Implement `DecisionHeuristic`, `DataQuirk`, `ProcessPlaybook` models in SpecOmagic
- Register new artifact types in `KnowledgeStore` and `ParserRegistry`
- Extend `ContextAssembler` priority ordering for new types
- Add `DomainPackManifest` model and basic `pack.yaml` loader
- **Tests:** ~40 new tests (model validation, store round-trips, context assembly)

### Phase 2: Capture Agent (Weeks 3–4)

**Goal:** SME Interview Agent operational

- Implement `InterviewAgent` with structured prompt sequences
- Build LLM-based extraction for each knowledge type
- Wire to `DeltaStore` for governance submission
- Add interview session API endpoints (`POST /interview/start`, `POST /interview/respond`)
- Build minimal chat UI for SME interviews (React page)
- **Tests:** ~50 new tests (session management, extraction quality, delta creation)

### Phase 3: Integration Bridge (Weeks 5–6)

**Goal:** Bidirectional sync between systems

- Implement `ArtifactBridge` with all conversion methods
- Build `GovernanceBridge` — lifecycle ↔ DeltaStatus mapping
- Extend `PromotionPipeline` to promote new artifact types
- Wire `FeedbackPipeline` → Delta creation for feedback-driven updates
- **Tests:** ~35 new tests (bridge conversions, round-trip fidelity)

### Phase 4: Domain Pack Builder (Weeks 7–8)

**Goal:** Build and distribute domain packs

- Implement `DomainPackBuilder` (build, validate, export, compute_quality)
- Add CLI commands: `pack build`, `pack validate`, `pack export`, `pack install`
- Build Pack Registry UI (browse, search, install packs)
- Create first seed pack: **Commercial Analytics Base** from existing knowledge
- **Tests:** ~30 new tests (build, validation, export round-trips)

### Phase 5: Seed & Validate (Weeks 9–10)

**Goal:** Prove the value with real knowledge

- Run 5–10 SME interview sessions with senior analysts
- Build 4 seed domain packs: Commercial, Market Access, Clinical, Forecasting
- Benchmark: agent accuracy with domain packs vs without (target: 50+ pharma questions)
- Measure token economics: curated context vs raw RAG retrieval
- Collect feedback loop data for first improvement cycle

---

## 11. Open Decisions for PM

| # | Decision | Options | Recommendation |
|---|---|---|---|
| 1 | **Pack distribution mechanism** | pip packages, git submodules, YAML directory copy, pack registry API | Start with YAML directory + `pack install` CLI. Move to pip packages for cross-team distribution later. |
| 2 | **Interview agent interface** | Chat UI, Slack bot, CLI, API-only | Chat UI (React page in existing frontend). API-only as secondary for programmatic use. |
| 3 | **New artifact types location** | SpecOmagic models (extend ArtifactBase), separate models package, shared library | SpecOmagic models — they already have lifecycle, tagging, and versioning infrastructure. |
| 4 | **Cross-system governance authority** | Onto_Wiz DeltaStore as single source, SpecOmagic lifecycle as single source, dual-write | Onto_Wiz DeltaStore for SME-originated knowledge (interviews, games). SpecOmagic lifecycle for document-originated knowledge. ArtifactBridge syncs. |
| 5 | **Seed pack scope** | Start with 1 pack (Commercial), 4 packs (all domains), therapy-area-first | Start with Commercial Analytics base + Oncology overlay (aligns with existing scenarios). |
| 6 | **LLM provider for extraction** | OpenAI only (current Onto_Wiz), litellm (current SpecOmagic), Anthropic-first | Adopt litellm across both systems. Provider-agnostic, already proven in SpecOmagic. |

> **Final Word**
> The goal is not to build a knowledge management system. The goal is to make every agentic solution your practice builds *as good as your best SME on their best day* — and to make that expertise available to every team, on every engagement, from day one. Domain Packs are how we get there.

---

*Onto_Wiz + SpecOmagic Programme • SME Knowledge Codification Blueprint • v1.0*

*1,062 passing tests • 52+ API endpoints • 10 frontend pages • and growing*
