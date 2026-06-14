"""
Onto_Wiz API Schemas (Pydantic Models)

These are the request/response models for the REST API.
Separate from the core domain models for clean layering.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS (Mirror core enums for API boundary)
# =============================================================================

class DeltaTypeAPI(str, Enum):
    PROPOSED_MAPPING = "proposed_mapping"
    PROPOSED_SYNONYM = "proposed_synonym"
    PROPOSED_EDGE = "proposed_edge"
    PROPOSED_ENTITY = "proposed_entity"
    PROPOSED_PATTERN = "proposed_pattern"
    PROPOSED_GUARDRAIL = "proposed_guardrail"
    PROPOSED_ACTION = "proposed_action"


class DeltaStatusAPI(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class BlastRadiusAPI(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ArtifactStatusAPI(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


# =============================================================================
# DELTA API MODELS
# =============================================================================

class DeltaCreate(BaseModel):
    """Request to create a new delta (proposal)."""
    type: DeltaTypeAPI
    content: Dict[str, Any]
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    blast_radius: BlastRadiusAPI = BlastRadiusAPI.MEDIUM
    evidence_pointers: List[str] = []
    source_type: str = "manual"  # manual, agent, upload, game
    source_id: Optional[str] = None


class DeltaResponse(BaseModel):
    """Response containing delta details."""
    id: str
    type: DeltaTypeAPI
    status: DeltaStatusAPI
    content: Dict[str, Any]
    confidence: float
    blast_radius: BlastRadiusAPI
    evidence_pointers: List[str]
    impacted_missions: List[str]
    impacted_personas: List[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    rejection_reason: Optional[str]
    source_type: str
    auto_approved: bool = False


class DeltaApprove(BaseModel):
    """Request to approve a delta."""
    reviewer: str


class DeltaReject(BaseModel):
    """Request to reject a delta."""
    reviewer: str
    reason: str


class DeltaListResponse(BaseModel):
    """Response containing list of deltas."""
    deltas: List[DeltaResponse]
    total: int
    pending: int


# =============================================================================
# JUDGMENT PATTERN API MODELS
# =============================================================================

class DriverAttributionAPI(BaseModel):
    """Driver with confidence."""
    driver: str
    prior_confidence: float = 0.5


class JudgmentPatternCreate(BaseModel):
    """Request to create a judgment pattern."""
    applies_when_signals: List[str]
    applies_when_context: List[str] = []
    typical_drivers: List[DriverAttributionAPI] = []
    disallowed_drivers: List[str] = []
    owner: str = "system"


class JudgmentPatternResponse(BaseModel):
    """Response containing pattern details."""
    id: str
    status: ArtifactStatusAPI
    applies_when_signals: List[str]
    applies_when_context: List[str]
    typical_drivers: List[DriverAttributionAPI]
    disallowed_drivers: List[str]
    owner: str
    approver: Optional[str]
    created_at: datetime
    is_active: bool


# =============================================================================
# GUARDRAIL API MODELS
# =============================================================================

class GuardrailCreate(BaseModel):
    """Request to create a guardrail."""
    blocks_action_types: List[str]
    blocks_drivers: List[str] = []
    unless_evidence: List[str] = []
    applies_to_personas: List[str] = []
    excludes_personas: List[str] = []
    owner: str = "compliance"


class GuardrailResponse(BaseModel):
    """Response containing guardrail details."""
    id: str
    status: ArtifactStatusAPI
    blocks_action_types: List[str]
    blocks_drivers: List[str]
    unless_evidence: List[str]
    applies_to_personas: List[str]
    owner: str
    is_active: bool


# =============================================================================
# INTELLIGENCE PACKET API MODELS
# =============================================================================

class SourceContributionAPI(BaseModel):
    """Sub-entity contribution."""
    entity: str
    entity_type: str
    contribution: float
    confidence: float = 0.8


class DriverResultAPI(BaseModel):
    """Driver attribution result."""
    driver: str
    confidence: float
    evidence: List[str] = []
    pattern_id: Optional[str] = None


class ActionRecommendationAPI(BaseModel):
    """Recommended action."""
    function: str
    action: str
    priority: str
    expected_impact: Optional[str] = None


class IntelligencePacketRequest(BaseModel):
    """Request to generate an intelligence packet."""
    signal: str
    signal_metric: str
    signal_change: float
    context: Dict[str, Any] = {}
    mission_id: str = ""
    persona: str = ""


class IntelligencePacketResponse(BaseModel):
    """Response containing intelligence packet."""
    id: str
    signal: str
    signal_metric: str
    signal_change: float
    sources: List[SourceContributionAPI]
    drivers: List[DriverResultAPI]
    implication: str
    recommendations: List[ActionRecommendationAPI]
    confidence: float
    guardrails_applied: List[str]
    evidence_trace: List[str]
    patterns_used: List[str]
    created_at: datetime
    time_to_generate_ms: int


# =============================================================================
# STATS & HEALTH
# =============================================================================

class StoreStats(BaseModel):
    """Statistics about the stores."""
    deltas: Dict[str, int]
    patterns: Dict[str, int]
    guardrails: Dict[str, int]
    action_templates: Dict[str, int]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    engine_loaded: bool
    stores_initialized: bool
    pending_reviews: int


# =============================================================================
# LEGACY API MODELS
# =============================================================================

class LegacyReasonRequest(BaseModel):
    """Legacy reasoning request."""
    account_id: str
    brand_id: str
    question: str


class LegacyReasonResponse(BaseModel):
    """Legacy reasoning response."""
    verdict: str
    confidence_score: float
    risks: List[str]
    evidence: List[str]


# =============================================================================
# GAME SESSION API MODELS
# =============================================================================

class HypothesisInput(BaseModel):
    """SME hypothesis selection from the game."""
    category: str  # matches HypothesisCategory enum values
    specific_driver: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = ""
    model_config = {"populate_by_name": True}

class SignalInput(BaseModel):
    """Signal priority from the game."""
    signal_name: str = Field(alias="signalName")
    role: str = "validation"  # validation, disconfirming, leading
    priority_rank: int = Field(default=1, alias="priorityRank")
    model_config = {"populate_by_name": True}

class DisconfirmInput(BaseModel):
    """Disconfirming logic from the game."""
    condition: str = ""
    would_suggest: str = Field(default="", alias="wouldSuggest")
    would_rule_out: str = Field(default="", alias="wouldRuleOut")
    model_config = {"populate_by_name": True}

class PatternInput(BaseModel):
    """Pattern recognition from the game."""
    frequency: str = "sometimes"  # often, sometimes, rarely, never
    typical_outcome: str = Field(default="", alias="typicalOutcome")
    time_to_resolution: str = Field(default="", alias="timeToResolution")
    model_config = {"populate_by_name": True}

class MistakeInput(BaseModel):
    """Common mistake from the game."""
    wrong_conclusion: str = Field(alias="wrongConclusion")
    why_wrong: str = Field(default="", alias="whyWrong")
    unless_evidence: str = Field(default="", alias="unlessEvidence")
    model_config = {"populate_by_name": True}

class ActionInput(BaseModel):
    """Recommended action from the game."""
    action: str
    action_type: str = Field(default="investigate", alias="actionType")
    priority: int = 1
    owner_function: str = Field(default="", alias="ownerFunction")
    model_config = {"populate_by_name": True}

class ConfidenceInput(BaseModel):
    """Confidence calibration from the game."""
    final_confidence: float = Field(ge=0.0, le=1.0, alias="finalConfidence")
    reasoning: str = ""
    model_config = {"populate_by_name": True}

class GameSessionCreate(BaseModel):
    """Full game session payload from the frontend."""
    scenario_id: str = Field(alias="scenarioId")
    hypothesis: HypothesisInput
    signals: List[SignalInput] = []
    disconfirm: Optional[DisconfirmInput] = None
    pattern: Optional[PatternInput] = None
    mistakes: List[MistakeInput] = []
    actions: List[ActionInput] = []
    confidence: Optional[ConfidenceInput] = None
    model_config = {"populate_by_name": True}

class GameSessionResponse(BaseModel):
    """Response after creating a game session."""
    session_id: str
    deltas_generated: int
    delta_ids: List[str]
    reasoning_event_id: str

class GameSessionSummary(BaseModel):
    """Summary of a stored game session."""
    id: str
    scenario_id: str
    started_at: datetime
    deltas_generated: int

class GameSessionDetail(BaseModel):
    """Full detail of a stored game session."""
    id: str
    scenario_id: str
    started_at: datetime
    deltas_generated: int
    delta_ids: List[str]
    hypothesis_category: Optional[str] = None
    sme_confidence: float = 0.5
    processed: bool = False


# =============================================================================
# HITL ROUTING + AUDIT API MODELS
# =============================================================================

class ReviewQueueItem(BaseModel):
    """Delta with routing metadata for review queue display."""
    delta: DeltaResponse
    queue: str
    assigned_to: str
    priority: str
    sla_hours: int
    reason: str
    judgment_type: str


class QueueStatsResponse(BaseModel):
    """Queue counts for dashboard display."""
    auto: int = 0
    standard: int = 0
    escalated: int = 0
    total_pending: int = 0


class EscalateRequest(BaseModel):
    """Request to escalate a delta to next review level."""
    reason: str


class AuditEntryResponse(BaseModel):
    """Single audit log entry."""
    id: str
    timestamp: datetime
    actor: str
    action: str
    artifact_id: str
    details: Dict[str, Any]


# =============================================================================
# CONTRIBUTION / SME IMPACT API MODELS
# =============================================================================

class ContributionResponse(BaseModel):
    """Single contribution record."""
    id: str
    reasoning_event_id: str
    sme_id: str
    sme_persona: str
    delta_ids: List[str]
    contributed_at: datetime
    therapeutic_area: str
    scenario_type: str
    sme_confidence: float


class ContributorSummaryResponse(BaseModel):
    """Aggregated stats for a single SME contributor."""
    sme_id: str
    total_contributions: int
    total_deltas: int
    domains: Dict[str, int]
    avg_confidence: float
    last_contributed: Optional[datetime]


class ContributionStatsResponse(BaseModel):
    """Store-level contribution statistics."""
    total_contributions: int
    unique_smes: int
    total_deltas: int
