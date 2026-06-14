# Design Document: SME Game → Delta Pipeline

## Overview

This document describes the complete pipeline from SME game session to ontology deltas. The key insight: SMEs never see ontology terms, but their reasoning is captured as structured artifacts.

## Problem Statement

Traditional knowledge management fails because:
1. Experts won't fill out forms
2. Ontology terms are intimidating
3. Documentation feels like work

The solution: Make it feel like a case discussion.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SME Game UI                                                    │
│  (Scenario → Hypothesis → Signals → Change-my-mind)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP POST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  ReasoningEvent Creation                                        │
│  - Parse SME inputs                                             │
│  - Normalize to canonical terms                                 │
│  - Create BrandProfile + ScenarioContext                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  DeltaGenerator.generate(event)                                 │
│  - Pattern delta                                                │
│  - Guardrail deltas                                             │
│  - Edge deltas                                                  │
│  - Metric semantic deltas                                       │
│  - Action template deltas                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Review Queue                                                   │
│  - All deltas status = PROPOSED                                 │
│  - Sorted by blast_radius                                       │
│  - HITL approval required                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Approved
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PromotionPipeline                                              │
│  - Create active artifacts                                      │
│  - Add to GraphStore                                            │
│  - Update SemanticStore                                         │
└─────────────────────────────────────────────────────────────────┘
```

## ReasoningEvent Schema

The structured output from one SME game session:

```python
@dataclass
class ReasoningEvent:
    # Session metadata
    id: str
    sme_persona: str  # "commercial_lead"
    
    # Scenario context (rich brand profiling)
    scenario: ScenarioContext
    scenario_type: str  # "regional_performance_dip"
    
    # SME responses
    primary_hypothesis: HypothesisRanking
    alternative_hypotheses: List[HypothesisRanking]
    signal_priorities: List[SignalPriority]
    disconfirming_logic: List[DisconfirmingLogic]
    pattern_recognition: PatternRecognition
    common_mistakes: List[CommonMistake]
    recommended_actions: List[RecommendedAction]
    sme_confidence: float
```

## Brand Profile (Context-Aware)

Different contexts produce different patterns:

```python
@dataclass
class BrandProfile:
    brand_name: str
    therapeutic_area: TherapeuticArea  # Oncology, CNS, etc.
    lifecycle: BrandLifecycle  # Launch, Growth, LOE
    asset_class: AssetClass  # Biologic, Small Molecule
    channel: ChannelType  # Specialty, Retail
    market_archetype: MarketArchetype  # Monopoly, Fragmented
    is_specialty: bool
    requires_rems: bool
    has_hub: bool
```

## Delta Generation

From one session, DeltaGenerator creates:

| Delta Type | Count | Source |
|:---|:---|:---|
| Pattern | 1 | Primary hypothesis + drivers |
| Guardrail | 1 per mistake | Common mistakes |
| Edge (supports) | 1 per signal | Signal priorities |
| Edge (contradicts) | 1 per rule_out | Disconfirming logic |
| Metric semantic | 1 per signal | Signal roles |
| Action template | 1 per action | Recommended actions |

**Total: ~10 deltas per 5-minute session**

## Context Scoping

All deltas are scoped to the original context:

```python
scope = {
    "therapeutic_area": "oncology",
    "lifecycle": "growth",
    "channel": "specialty",
    "geography": "US",
    "region": "Northeast"
}
```

This ensures:
- Oncology patterns don't fire for CNS brands
- Launch patterns don't apply to mature brands
- Regional patterns stay regional

## Decay Configuration

Context determines decay period:

| Lifecycle | Decay (days) | Rationale |
|:---|:---|:---|
| Pre-launch | 90 | Uncertainty high |
| Launch | 90 | Fast-changing |
| Growth | 180 | Moderate stability |
| Maturity | 365 | Stable dynamics |
| LOE | 90 | Competitive disruption |

## Example: Full Pipeline Trace

**Input:** SME plays "Brand X regional dip" scenario

**ReasoningEvent captured:**
```json
{
  "scenario_type": "regional_performance_dip",
  "brand": {
    "name": "Brand X",
    "therapeutic_area": "oncology",
    "lifecycle": "growth"
  },
  "primary_hypothesis": "market_access",
  "signal_priorities": ["TRx", "payer_policy_change"],
  "common_mistakes": ["Assume demand erosion too quickly"],
  "sme_confidence": 0.70
}
```

**Deltas generated:**
1. `PROPOSED_PATTERN`: "Access friction for regional dips (oncology/growth)"
2. `PROPOSED_GUARDRAIL`: "Block demand_erosion without NBRx evidence"
3. `PROPOSED_EDGE`: TRx → supports → access_friction
4. `PROPOSED_EDGE`: payer_policy_change → supports → access_friction
5. `PROPOSED_EDGE`: decile_stable → contradicts → demand_erosion
6. `PROPOSED_MAPPING`: TRx.role = "validation"
7. `PROPOSED_MAPPING`: payer_policy_change.role = "validation"
8. `PROPOSED_ACTION`: "Investigate payer edits"
9. `PROPOSED_ACTION`: "Pull PA reject data"

## Semantic Capture

During DeltaGenerator processing:
1. SME terms normalized via SemanticStore
2. New synonyms proposed as deltas
3. Usage patterns logged for future extraction

## Implementation Status

| Component | Status |
|:---|:---|
| ReasoningEvent schema | ✅ Done |
| BrandProfile | ✅ Done |
| DeltaGenerator | ✅ Done |
| Pattern generation | ✅ Done |
| Guardrail generation | ✅ Done |
| Edge generation | ✅ Done |
| Metric semantic generation | ✅ Done |
| Action template generation | ✅ Done |
| Semantic capture | ✅ Basic |
| Consolidation/Reconciler | 🔲 Pending |

## File Locations

- `src/core/reasoning_event.py` - ~360 lines
- `src/core/delta_generator.py` - ~510 lines
- `src/api/server.py` - ~516 lines with endpoints

## API Endpoints

| Endpoint | Method | Purpose |
|:---|:---|:---|
| `POST /game/session` | Create session | Start SME game |
| `POST /game/session/{id}/submit` | Submit answers | Complete game |
| `GET /deltas` | List deltas | View queue |
| `POST /deltas/{id}/approve` | Approve | HITL approval |
