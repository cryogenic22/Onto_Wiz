# Data Schemas: Onto_Wiz

## Core Models

### Delta

```python
@dataclass
class Delta:
    id: str                          # UUID
    type: DeltaType                  # PROPOSED_PATTERN, PROPOSED_GUARDRAIL, etc.
    status: DeltaStatus              # PROPOSED, APPROVED, REJECTED, PROMOTED
    content: Dict[str, Any]          # Type-specific content
    confidence: float                # 0.0 to 1.0
    evidence_pointers: List[str]     # Evidence IDs
    blast_radius: BlastRadius        # LOW, MEDIUM, HIGH, CRITICAL
    impacted_missions: List[str]     # Mission names
    impacted_personas: List[str]     # Persona names
    source_type: str                 # sme_game, auto_derive, manual
    source_id: str                   # Source reference
    created_at: datetime
    created_by: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
```

### DeltaType Enum

```python
class DeltaType(str, Enum):
    PROPOSED_PATTERN = "proposed_pattern"
    PROPOSED_GUARDRAIL = "proposed_guardrail"
    PROPOSED_EDGE = "proposed_edge"
    PROPOSED_ENTITY = "proposed_entity"
    PROPOSED_MAPPING = "proposed_mapping"
    PROPOSED_ACTION = "proposed_action"
```

---

## Judgment Artifacts

### JudgmentPattern

```python
@dataclass
class JudgmentPattern:
    id: str
    version: str
    name: str
    
    # When to apply
    applies_when_signals: List[str]
    applies_when_context: List[str]
    
    # What to recommend
    typical_drivers: List[DriverAttribution]
    disallowed_drivers: List[str]
    
    # Required evidence
    required_evidence_types: List[str]
    
    # Governance
    governance: Governance
    
    # Decay
    decay: DecayConfig
    
    # Scope
    scope: Scope
```

### Guardrail

```python
@dataclass
class Guardrail:
    id: str
    name: str
    
    # What it blocks
    blocks_claims: List[str]
    blocks_drivers: List[str]
    
    # When blocking doesn't apply
    unless_evidence: List[str]
    
    # Risk level
    risk_class: RiskClass
    
    # Governance
    governance: Governance
    scope: Scope
```

### ActionTemplate

```python
@dataclass
class ActionTemplate:
    id: str
    name: str
    
    # What to do
    action_type: str              # investigate, pull_data, escalate, wait
    description: str
    
    # Who does it
    owner_function: str           # market_access, field, analytics
    
    # When to suggest
    trigger_drivers: List[str]
    priority: int
    
    governance: Governance
```

---

## Evidence Model

### EvidenceItem

```python
@dataclass
class EvidenceItem:
    id: str
    type: EvidenceType            # PAYER_DATA, FIELD_NOTE, MARKET_RESEARCH, etc.
    source_system: SourceSystem   # IQVIA, VEEVA, MANUAL, etc.
    
    # Location
    uri: Optional[str]            # Where to find raw data
    extracted_claims: List[ExtractedClaim]
    
    # Reliability
    reliability_class: ReliabilityClass  # HARD, SOFT, RUMOR
    verification_status: str
    
    # Access control
    permission_tags: List[str]
    
    # Timestamps
    captured_at: datetime
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
```

### ReliabilityClass

```python
class ReliabilityClass(str, Enum):
    HARD = "hard"                 # Verified data (weight: 1.0)
    SOFT = "soft"                 # Credible reports (weight: 0.6)
    RUMOR = "rumor"               # Unverified (weight: 0.3)
```

---

## Graph Model

### GraphNode

```python
@dataclass
class GraphNode:
    id: str
    type: NodeType                # ENTITY, METRIC, SIGNAL, etc.
    name: str
    properties: Dict[str, Any]
    created_at: datetime
    status: str
```

### GraphEdge

```python
@dataclass
class GraphEdge:
    id: str
    type: EdgeType                # SUPPORTS, CONTRADICTS, LEADS_TO, etc.
    source_id: str                # Node ID
    target_id: str                # Node ID
    weight: float                 # Edge strength
    properties: Dict[str, Any]
    created_at: datetime
```

### NodeType

```python
class NodeType(str, Enum):
    ENTITY = "entity"             # Brand, HCP, Payer
    METRIC = "metric"             # TRx, NBRx, Share
    SIGNAL = "signal"             # TRx_dip, PA_reject
    OBSERVATION = "observation"   # Specific data point
    HYPOTHESIS = "hypothesis"     # access_friction, demand_erosion
    EVIDENCE = "evidence"         # Reference to EvidenceItem
    PATTERN = "pattern"           # Reference to JudgmentPattern
    GUARDRAIL = "guardrail"       # Reference to Guardrail
```

### EdgeType

```python
class EdgeType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REQUIRES_EVIDENCE = "requires_evidence"
    BLOCKED_BY = "blocked_by"
    LEADS_TO = "leads_to"
    INSTANCE_OF = "instance_of"
    MEMBER_OF = "member_of"
```

---

## SME Game Model

### ReasoningEvent

```python
@dataclass
class ReasoningEvent:
    id: str
    session_id: str
    sme_persona: str
    
    # Context
    scenario: ScenarioContext
    scenario_type: str
    
    # SME responses
    primary_hypothesis: HypothesisRanking
    alternative_hypotheses: List[HypothesisRanking]
    signal_priorities: List[SignalPriority]
    disconfirming_logic: List[DisconfirmingLogic]
    pattern_recognition: PatternRecognition
    common_mistakes: List[CommonMistake]
    recommended_actions: List[RecommendedAction]
    sme_confidence: float
    
    # Processing
    processed: bool
    deltas_generated: List[str]
    
    created_at: datetime
```

### BrandProfile

```python
@dataclass
class BrandProfile:
    brand_name: str
    therapeutic_area: TherapeuticArea
    lifecycle: BrandLifecycle
    asset_class: AssetClass
    channel: ChannelType
    market_archetype: MarketArchetype
    is_specialty: bool
    requires_rems: bool
    has_hub: bool
```

---

## Semantic Model

### CanonicalTerm

```python
@dataclass
class CanonicalTerm:
    id: str
    term: str                     # "Prior_Authorization"
    domains: List[FunctionalDomain]
    definition: str
    parent_term_id: Optional[str]
    status: str
```

### SemanticRelation

```python
@dataclass
class SemanticRelation:
    id: str
    source_term: str              # "PA"
    target_term_id: str           # ID of Prior_Authorization
    relation_type: SemanticRelationType
    domains: List[FunctionalDomain]
    confidence: float
    source_event_id: Optional[str]
    context_note: Optional[str]
    status: str
```

---

## Governance Model

### Governance

```python
@dataclass
class Governance:
    owner: str
    status: ArtifactStatus
    approved_by: Optional[str]
    approved_on: Optional[datetime]
    review_cycle_days: int
    next_review: Optional[datetime]
    risk_class: RiskClass
    judgment_type: JudgmentType
```

### RiskClass

```python
class RiskClass(str, Enum):
    ADVISORY = "advisory"
    DECISION_SUPPORT = "decision_support"
    RESTRICTED = "restricted"
```

### JudgmentType

```python
class JudgmentType(str, Enum):
    EMPIRICAL = "empirical"             # Data-derived
    CAUSAL_HYPOTHESIS = "causal_hypothesis"  # Requires evidence
    NORMATIVE = "normative"             # Policy/value judgment
```

---

## Intelligence Packet (Output)

```python
@dataclass
class IntelligencePacket:
    mission_id: str
    question: str
    
    # Results
    drivers: List[DriverResult]
    actions: List[ActionRecommendation]
    
    # Evidence
    sources: List[SourceContribution]
    
    # Quality
    overall_confidence: float
    guardrails_hit: List[str]
    
    # Trace
    patterns_matched: List[str]
    edges_traversed: int
    halted: bool
    halt_reason: Optional[str]
    
    created_at: datetime
```
