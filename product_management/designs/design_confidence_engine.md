# Design Document: Confidence Engine

## Overview

The ConfidenceEngine computes credible confidence scores from evidence, pattern priors, and conflict analysis. This replaces caller-provided confidence with computed, traceable values.

## Problem Statement

Without computed confidence, any approval or decision is arbitrary. AI agents need defensible confidence values based on:
1. Evidence quality (hard > soft > rumor)
2. Evidence quantity (corroboration)
3. Pattern priors (historical accuracy)
4. Conflicting evidence
5. Freshness (decay)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ConfidenceEngine                              │
├─────────────────────────────────────────────────────────────────┤
│  Inputs:                                                        │
│   - hypothesis: str                                             │
│   - pattern: Optional[JudgmentPattern]                          │
│   - evidence_pointers: List[EvidencePointer]                    │
│   - contradicting_pointers: List[EvidencePointer]               │
│   - required_evidence_types: List[str]                          │
│   - context: Dict[str, Any]                                     │
├─────────────────────────────────────────────────────────────────┤
│  Computation:                                                   │
│   confidence = weighted_sum(                                    │
│       base_prior,              # 30%                            │
│       evidence_reliability,    # 25%                            │
│       corroboration,           # 15%                            │
│       (1 - conflict_penalty),  # 15%                            │
│       freshness                # 15%                            │
│   )                                                             │
│                                                                 │
│   if missing_required_evidence:                                 │
│       confidence *= 0.75                                        │
├─────────────────────────────────────────────────────────────────┤
│  Output: ConfidenceResult                                       │
│   - final_confidence: float                                     │
│   - signals: List[ConfidenceSignal]  (full trace)              │
│   - is_actionable: bool                                         │
│   - requires_evidence: bool                                     │
│   - has_conflicts: bool                                         │
│   - limiting_factors: List[str]                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Confidence Factors

### 1. Base Prior (30%)

From JudgmentPattern, the historical accuracy of this hypothesis in similar contexts.

```python
for driver in pattern.typical_drivers:
    if driver.driver_name == hypothesis:
        prior = driver.prior_confidence
        break
```

### 2. Evidence Reliability (25%)

Weighted average of evidence reliability classes:
- HARD (verified data): 1.0
- SOFT (credible reports): 0.6
- RUMOR (unverified): 0.3

```python
for evidence in evidence_items:
    total += evidence.reliability_weight()
avg_reliability = total / count
```

### 3. Corroboration (15%)

More independent sources = higher confidence:
- 0 sources: 0.0
- 1 source: 0.3
- 2 sources: 0.6
- 3 sources: 0.8
- 4+ sources: 0.9 (diminishing returns)

### 4. Conflict Penalty (15%)

High conflict ratio reduces confidence:

```python
conflict_ratio = contradicting / (supporting + contradicting)
value = 1.0 - conflict_ratio
```

### 5. Freshness (15%)

Patterns decay over time based on DecayConfig:

```python
age_days = (now - pattern.created_at).days
if age_days >= valid_for_days:
    value = 0.2  # Minimum freshness
else:
    value = 1.0 - (0.8 * age_days / valid_for_days)
```

## Thresholds

| Threshold | Value | Effect |
|:---|:---|:---|
| ACTIONABLE_THRESHOLD | 0.55 | Below = halt |
| HIGH_CONFLICT_RATIO | 0.40 | Above = flag |
| MISSING_EVIDENCE_PENALTY | 0.25 | Reduces confidence |

## API

```python
engine = ConfidenceEngine(evidence_store)

result = engine.compute(
    hypothesis="access_friction",
    pattern=regional_dip_pattern,
    evidence_pointers=[pa_data, field_notes],
    contradicting_pointers=[],
    required_evidence_types=["payer_data"],
    context={"region": "Northeast"}
)

if result.is_actionable:
    proceed_with_recommendation()
else:
    halt_with_explanation(result.limiting_factors)
```

## Output Schema

```python
@dataclass
class ConfidenceResult:
    final_confidence: float  # 0.0 to 1.0
    signals: List[ConfidenceSignal]  # Full trace
    is_actionable: bool  # > 0.55
    requires_evidence: bool  # Missing required types
    has_conflicts: bool  # conflict_ratio > 0.4
    primary_driver: str
    limiting_factors: List[str]  # Human-readable
```

## Implementation Status

| Component | Status |
|:---|:---|
| ConfidenceSignal | ✅ Done |
| ConfidenceResult | ✅ Done |
| ConfidenceEngine | ✅ Done |
| Tests | 🔲 Pending |
| Integration with TraversalPolicy | 🔲 Pending |

## File Location

`src/core/confidence.py` - ~300 lines

## Dependencies

- `EvidenceStore` - For evidence lookup
- `JudgmentPattern` - For pattern priors
- `DecayConfig` - For freshness calculation
