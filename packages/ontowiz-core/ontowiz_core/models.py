"""
Onto_Wiz Core Domain Models

This module defines the enterprise-grade data models for the Judgment Layer.
Everything is a proposal (Delta Model) - agents propose, humans approve, system promotes.

Architecture Layers:
1. Delta Model - All changes are proposals
2. Judgment Artifacts - Patterns, Guardrails, ActionTemplates
3. Governance - Ownership, approval states, audit trails
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# =============================================================================
# ENUMS - Status, Types, Risk Classes
# =============================================================================

class ArtifactStatus(str, Enum):
    """Lifecycle states for all governed artifacts."""
    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class DeltaStatus(str, Enum):
    """Status of a proposed change (delta)."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class DeltaType(str, Enum):
    """Types of changes that can be proposed."""
    PROPOSED_MAPPING = "proposed_mapping"
    PROPOSED_SYNONYM = "proposed_synonym"
    PROPOSED_EDGE = "proposed_edge"
    PROPOSED_ENTITY = "proposed_entity"
    PROPOSED_PATTERN = "proposed_pattern"
    PROPOSED_GUARDRAIL = "proposed_guardrail"
    PROPOSED_ACTION = "proposed_action"


class JudgmentType(str, Enum):
    """
    Classification of judgment - determines governance requirements.

    EMPIRICAL: Data-derived, can be auto-updated
    CAUSAL_HYPOTHESIS: Mixed, requires proposal + review
    NORMATIVE: Human-only, requires explicit approval
    """
    EMPIRICAL = "empirical"
    CAUSAL_HYPOTHESIS = "causal_hypothesis"
    NORMATIVE = "normative"


class RiskClass(str, Enum):
    """
    Risk level of an artifact - determines traversal permissions.

    ADVISORY: Low risk, informational only
    DECISION_SUPPORT: Medium risk, agents can traverse
    RESTRICTED: High risk, requires HITL for every use
    """
    ADVISORY = "advisory"
    DECISION_SUPPORT = "decision_support"
    RESTRICTED = "restricted"


class BlastRadius(str, Enum):
    """Impact scope of a proposed change."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AgentMode(str, Enum):
    """
    Traversal modes for bounded agent behavior.

    EXPLORE: Evidence gathering only
    APPLY: Approved judgment only
    RECOMMEND: Action nodes only
    EXPLAIN: Trace generation only
    """
    EXPLORE = "explore"
    APPLY = "apply"
    RECOMMEND = "recommend"
    EXPLAIN = "explain"


# =============================================================================
# GOVERNANCE - Ownership, Approval, Audit
# =============================================================================

@dataclass
class Governance:
    """Ownership and approval metadata for governed artifacts."""
    owner: str
    approver: str | None = None
    approved_on: datetime | None = None
    review_cycle: str = "quarterly"  # quarterly, monthly, annual
    risk_class: RiskClass = RiskClass.DECISION_SUPPORT

    def is_approved(self) -> bool:
        return self.approved_on is not None

    # --- Review cycle enforcement (CTX-007) ---

    _CYCLE_DAYS = {"monthly": 30, "quarterly": 90, "annual": 365}

    def get_review_cycle_days(self) -> int:
        """Convert categorical review_cycle to numeric days."""
        return self._CYCLE_DAYS.get(self.review_cycle, 90)

    def is_review_due(self) -> bool:
        """True if this artifact is past its review cycle deadline."""
        if self.approved_on is None:
            return False
        age = (datetime.utcnow() - self.approved_on).days
        return age >= self.get_review_cycle_days()

    def days_until_review(self) -> int | None:
        """Days remaining until review is due. Negative if overdue. None if not approved."""
        if self.approved_on is None:
            return None
        age = (datetime.utcnow() - self.approved_on).days
        return self.get_review_cycle_days() - age


@dataclass
class AuditEntry:
    """Single audit log entry for traversals and changes."""
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    actor: str = ""  # user or system who performed the action
    action: str = ""  # specific action (propose, approve, reject, etc.)
    artifact_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    evidence_pointers: list[str] = field(default_factory=list)
    # Enhanced fields (CTX-008)
    store_type: str = ""  # delta, judgment, contribution
    action_category: str = ""  # create, approve, reject, escalate, merge, record
    before_snapshot: dict[str, Any] = field(default_factory=dict)
    after_snapshot: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# DECAY - Confidence over time
# =============================================================================

@dataclass
class DecayConfig:
    """Configuration for confidence decay over time."""
    valid_for_days: int = 180
    decay_type: str = "linear"  # linear, exponential, step
    refresh_triggers: list[str] = field(default_factory=lambda: ["new_evidence", "sme_replay"])

    def is_stale(self, created_at: datetime) -> bool:
        age = (datetime.utcnow() - created_at).days
        return age > self.valid_for_days


@dataclass
class Scope:
    """Applicability scope for judgment artifacts."""
    geography: list[str] = field(default_factory=lambda: ["US"])
    lifecycle: list[str] = field(default_factory=lambda: ["launch", "growth", "mature"])
    brand: str | None = None
    indication: str | None = None

    def matches(self, context: dict[str, Any]) -> bool:
        """Check if context matches this scope."""
        if context.get("geography") and context["geography"] not in self.geography:
            return False
        if context.get("lifecycle") and context["lifecycle"] not in self.lifecycle:
            return False
        return not (self.brand and context.get("brand") != self.brand)


# =============================================================================
# CONFLICT DETECTION
# =============================================================================

@dataclass
class ConflictResult:
    """Detected conflict between two deltas."""
    delta_id: str = ""
    conflict_type: str = ""  # canonical_id_collision, scope_overlap, edge_contradiction
    description: str = ""
    severity: str = "warning"  # warning or blocker


# =============================================================================
# HITL ROUTING
# =============================================================================

@dataclass
class RoutingDecision:
    """Result of routing a delta to a review queue."""
    assigned_to: str = "system_auto"
    queue: str = "auto"  # auto, standard, escalated
    priority: str = "normal"  # low, normal, high, critical
    sla_hours: int = 48
    reason: str = ""


# =============================================================================
# CONTRIBUTION TRACKING
# =============================================================================

@dataclass
class Contribution:
    """A single SME contribution from a game session."""
    id: str = field(default_factory=lambda: str(uuid4()))
    reasoning_event_id: str = ""
    sme_id: str = ""
    sme_persona: str = ""
    delta_ids: list[str] = field(default_factory=list)
    contributed_at: datetime = field(default_factory=datetime.utcnow)
    therapeutic_area: str = ""
    scenario_type: str = ""
    sme_confidence: float = 0.5


# =============================================================================
# DELTA MODEL - Everything is a proposal
# =============================================================================

@dataclass
class Delta:
    """
    The core primitive: All changes are proposals.

    Agents propose deltas. Humans approve. System promotes to graph.
    This is the foundation of self-healing and governance.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    type: DeltaType = DeltaType.PROPOSED_EDGE
    status: DeltaStatus = DeltaStatus.PROPOSED

    # The actual change
    content: dict[str, Any] = field(default_factory=dict)

    # Metadata
    confidence: float = 0.5
    evidence_pointers: list[str] = field(default_factory=list)
    blast_radius: BlastRadius = BlastRadius.MEDIUM
    impacted_missions: list[str] = field(default_factory=list)
    impacted_personas: list[str] = field(default_factory=list)

    # Review state
    assigned_to: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None
    rejection_reason: str | None = None

    # Ownership and classification
    owner: str = "system"  # who proposed this delta
    judgment_type: JudgmentType = JudgmentType.EMPIRICAL

    # Source tracking
    source_type: str = "agent"  # agent, upload, game, manual
    source_id: str | None = None

    def approve(self, reviewer: str) -> None:
        """Approve this delta for promotion to the graph."""
        self.status = DeltaStatus.APPROVED
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewer

    def reject(self, reviewer: str, reason: str) -> None:
        """Reject this delta with a reason."""
        self.status = DeltaStatus.REJECTED
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewer
        self.rejection_reason = reason

    def is_auto_approvable(self) -> bool:
        """Level 1 deltas (low risk, high confidence) can auto-approve."""
        return (
            self.blast_radius == BlastRadius.LOW and
            self.confidence >= 0.9 and
            self.type in [DeltaType.PROPOSED_SYNONYM, DeltaType.PROPOSED_MAPPING]
        )


# =============================================================================
# JUDGMENT ARTIFACTS - Patterns, Guardrails, Actions
# =============================================================================

@dataclass
class DriverAttribution:
    """A potential driver with confidence and evidence."""
    driver: str
    prior_confidence: float = 0.5
    evidence_required: list[str] = field(default_factory=list)


@dataclass
class JudgmentPattern:
    """
    A reusable judgment abstraction learned from scenarios.

    Scenarios train patterns; patterns drive production.
    This is NOT a static rule - it evolves and decays.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    version: str = "1.0.0"
    status: ArtifactStatus = ArtifactStatus.DRAFT

    # When this pattern applies
    applies_when_signals: list[str] = field(default_factory=list)
    applies_when_context: list[str] = field(default_factory=list)
    scope: Scope = field(default_factory=Scope)

    # Driver logic
    typical_drivers: list[DriverAttribution] = field(default_factory=list)
    disallowed_drivers: list[str] = field(default_factory=list)

    # Governance & decay
    governance: Governance = field(default_factory=lambda: Governance(owner="system"))
    decay: DecayConfig = field(default_factory=DecayConfig)
    judgment_type: JudgmentType = JudgmentType.CAUSAL_HYPOTHESIS

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    trained_from_scenarios: list[str] = field(default_factory=list)
    superseded_by: str | None = None  # CTX-009: lineage — ID of pattern that replaced this one

    def is_active(self) -> bool:
        """Check if pattern is approved and not stale."""
        if self.status != ArtifactStatus.APPROVED:
            return False
        return not self.decay.is_stale(self.created_at)

    def matches(self, signals: list[str], context: dict[str, Any]) -> bool:
        """Check if this pattern applies to the given signals and context."""
        return self.match_score(signals, context) > 0.0

    def match_score(self, signals: list[str], context: dict[str, Any]) -> float:
        """
        Ranked match quality score (0.0-1.0).

        Factors: signal overlap (40%), context overlap (25%),
        judgment type weight (20%), freshness decay (15%).
        Returns 0.0 if no signal overlap or scope mismatch.
        """
        signal_score = self._signal_overlap_score(signals)
        if signal_score == 0.0:
            return 0.0

        context_score = self._context_overlap_score(context)
        if context_score == 0.0:
            return 0.0

        type_score = self._judgment_type_weight()
        fresh_score = self._freshness_score()

        return (
            0.40 * signal_score
            + 0.25 * context_score
            + 0.20 * type_score
            + 0.15 * fresh_score
        )

    def _signal_overlap_score(self, signals: list[str]) -> float:
        """Fraction of pattern signals present in input. 0.0 if no overlap."""
        if not self.applies_when_signals:
            return 0.0
        overlap = sum(1 for s in self.applies_when_signals if s in signals)
        if overlap == 0:
            return 0.0
        return overlap / len(self.applies_when_signals)

    def _context_overlap_score(self, context: dict[str, Any]) -> float:
        """Scope match gated by context keyword overlap."""
        if not self.scope.matches(context):
            return 0.0
        if not self.applies_when_context:
            return 1.0
        ctx_values = set()
        for v in context.values():
            if isinstance(v, str):
                ctx_values.add(v)
        if not ctx_values:
            return 1.0
        overlap = sum(1 for c in self.applies_when_context if c in ctx_values)
        return max(0.1, overlap / len(self.applies_when_context))

    def _judgment_type_weight(self) -> float:
        """Weight by judgment type: EMPIRICAL=1.0, CAUSAL=0.7, NORMATIVE=0.5."""
        weights = {
            JudgmentType.EMPIRICAL: 1.0,
            JudgmentType.CAUSAL_HYPOTHESIS: 0.7,
            JudgmentType.NORMATIVE: 0.5,
        }
        return weights.get(self.judgment_type, 0.5)

    def _freshness_score(self) -> float:
        """Linear decay from 1.0 to 0.2 over valid_for_days."""
        age_days = (datetime.utcnow() - self.created_at).days
        valid_days = self.decay.valid_for_days
        if age_days <= 0:
            return 1.0
        if age_days >= valid_days:
            return 0.2
        return 1.0 - (0.8 * age_days / valid_days)


@dataclass
class GuardrailResult:
    """Result of evaluating proposed drivers against a guardrail."""
    guardrail_id: str = ""
    is_blocked: bool = False
    blocked_drivers: list[str] = field(default_factory=list)
    escape_conditions_met: list[str] = field(default_factory=list)
    escape_conditions_unmet: list[str] = field(default_factory=list)


@dataclass
class Guardrail:
    """
    Explicit constraint: what NOT to do.

    Guardrails are normative (human-defined) and cannot be created by agents.
    They enforce safety boundaries on recommendations.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    status: ArtifactStatus = ArtifactStatus.DRAFT

    # What this guardrail blocks
    blocks_action_types: list[str] = field(default_factory=list)
    blocks_drivers: list[str] = field(default_factory=list)

    # Unless specific evidence/conditions
    unless_evidence: list[str] = field(default_factory=list)
    unless_approver_role: list[str] = field(default_factory=list)

    # Scope
    applies_to_personas: list[str] = field(default_factory=list)
    excludes_personas: list[str] = field(default_factory=list)
    scope: Scope = field(default_factory=Scope)

    # Governance (always normative, always restricted)
    governance: Governance = field(default_factory=lambda: Governance(
        owner="compliance",
        risk_class=RiskClass.RESTRICTED
    ))
    judgment_type: JudgmentType = JudgmentType.NORMATIVE

    # Audit requirements
    log_all_invocations: bool = True
    escalate_on_override_attempt: bool = True

    def is_violated(self, action_type: str, evidence: list[str], persona: str) -> bool:
        """Check if an action would violate this guardrail."""
        # Check if persona is covered
        if self.excludes_personas and persona in self.excludes_personas:
            return False  # Not applicable
        if self.applies_to_personas and persona not in self.applies_to_personas:
            return False  # Not applicable

        # Check if action is blocked
        if action_type not in self.blocks_action_types:
            return False  # Not blocked

        # Violated unless the required escape-evidence is fully present.
        return not (self.unless_evidence and all(e in evidence for e in self.unless_evidence))

    def evaluate_drivers(
        self,
        proposed_drivers: list[str],
        available_evidence: list[str],
    ) -> "GuardrailResult":
        """Check if proposed drivers are blocked by this guardrail."""
        if not self.blocks_drivers:
            return GuardrailResult(guardrail_id=self.id)

        blocked = [d for d in proposed_drivers if d in self.blocks_drivers]
        if not blocked:
            return GuardrailResult(guardrail_id=self.id)

        met = [e for e in self.unless_evidence if e in available_evidence]
        unmet = [e for e in self.unless_evidence if e not in available_evidence]

        # Unblocked only if ALL escape conditions are met
        if self.unless_evidence and not unmet:
            return GuardrailResult(
                guardrail_id=self.id,
                is_blocked=False,
                blocked_drivers=blocked,
                escape_conditions_met=met,
                escape_conditions_unmet=[],
            )

        return GuardrailResult(
            guardrail_id=self.id,
            is_blocked=True,
            blocked_drivers=blocked,
            escape_conditions_met=met,
            escape_conditions_unmet=unmet,
        )


@dataclass
class FunctionAction:
    """A specific action for a specific function."""
    action: str
    priority: str = "medium"  # low, medium, high
    conditions: list[str] = field(default_factory=list)


@dataclass
class ActionTemplate:
    """
    Cross-functional action recommendations.

    Maps from patterns to coordinated actions across Brand, Field, Access.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    status: ArtifactStatus = ArtifactStatus.DRAFT

    # Trigger
    trigger_pattern_id: str = ""

    # Cross-functional actions
    brand_actions: list[FunctionAction] = field(default_factory=list)
    field_actions: list[FunctionAction] = field(default_factory=list)
    access_actions: list[FunctionAction] = field(default_factory=list)
    medical_actions: list[FunctionAction] = field(default_factory=list)

    # Expected outcome
    expected_impact_metric: str = ""
    expected_impact_timeframe: str = ""
    expected_impact_confidence: float = 0.5

    # Governance
    governance: Governance = field(default_factory=lambda: Governance(owner="cross_functional_lead"))

    def get_actions_for_function(self, function: str) -> list[FunctionAction]:
        """Get actions for a specific function."""
        mapping = {
            "brand": self.brand_actions,
            "field": self.field_actions,
            "access": self.access_actions,
            "medical": self.medical_actions,
        }
        return mapping.get(function.lower(), [])


# =============================================================================
# INTELLIGENCE PACKET - UBI-Compatible Output
# =============================================================================

@dataclass
class SourceContribution:
    """Sub-entity contribution to a signal."""
    entity: str
    entity_type: str  # e.g., "DMA", "Account", "Territory"
    contribution: float  # e.g., -0.021 (2.1% of total decline)
    confidence: float = 0.8


@dataclass
class DriverResult:
    """Attributed driver with confidence and evidence."""
    driver: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    pattern_id: str | None = None  # The pattern that identified this


@dataclass
class ActionRecommendation:
    """A recommended action for a specific function."""
    function: str  # brand, field, access, medical
    action: str
    priority: str
    expected_impact: str | None = None


@dataclass
class IntelligencePacket:
    """
    The UBI-compatible output format.

    Signal → Source → Driver → Implication → Recommendation
    This is what gets delivered to the Mission Concierge.
    """
    # Required fields FIRST (no defaults)
    signal: str
    signal_metric: str
    signal_change: float

    # Optional fields with defaults
    id: str = field(default_factory=lambda: str(uuid4()))
    signal_timestamp: datetime = field(default_factory=datetime.utcnow)

    # Source (sub-entity breakdown)
    sources: list[SourceContribution] = field(default_factory=list)

    # Driver (from Reasoning Graph)
    drivers: list[DriverResult] = field(default_factory=list)

    # Implication (what it means)
    implication: str = ""

    # Recommendation (cross-functional)
    recommendations: list[ActionRecommendation] = field(default_factory=list)

    # Metadata
    confidence: float = 0.5
    mission_id: str = ""
    persona: str = ""

    # Governance trace
    guardrails_applied: list[str] = field(default_factory=list)
    evidence_trace: list[str] = field(default_factory=list)
    patterns_used: list[str] = field(default_factory=list)

    # Telemetry
    created_at: datetime = field(default_factory=datetime.utcnow)
    time_to_generate_ms: int = 0



# =============================================================================
# HARD STOPS - Non-negotiable boundaries
# =============================================================================

@dataclass
class HardStopResult:
    """Result of a hard stop check."""
    triggered: bool = False
    reason: str = ""
    action: str = "continue"  # continue, halt, halt_and_escalate


@dataclass
class TraversalPolicy:
    """Policy governing agent traversal of the graph."""
    allowed_artifact_status: list[ArtifactStatus] = field(
        default_factory=lambda: [ArtifactStatus.APPROVED]
    )
    mission_scope_check: bool = True
    max_risk_class: RiskClass = RiskClass.DECISION_SUPPORT

    # Hard stops
    min_confidence: float = 0.55
    max_conflicting_driver_ratio: float = 0.4
    require_evidence_for_hypothesis: bool = True

    # Agent constraints
    max_traversal_depth: int = 5
    agent_mode: AgentMode = AgentMode.APPLY
    cannot_create_edges: bool = True

    def check_hard_stops(
        self,
        confidence: float,
        evidence_count: int,
        required_evidence: int,
        conflicting_ratio: float,
        guardrail_violations: list[str]
    ) -> HardStopResult:
        """Check all hard stop conditions."""

        if confidence < self.min_confidence:
            return HardStopResult(
                triggered=True,
                reason=f"Confidence {confidence:.2f} below threshold {self.min_confidence}",
                action="halt"
            )

        if evidence_count < required_evidence:
            return HardStopResult(
                triggered=True,
                reason=f"Insufficient evidence ({evidence_count}/{required_evidence})",
                action="halt"
            )

        if conflicting_ratio > self.max_conflicting_driver_ratio:
            return HardStopResult(
                triggered=True,
                reason=f"Conflicting drivers ratio {conflicting_ratio:.2f} exceeds threshold",
                action="halt"
            )

        if guardrail_violations:
            return HardStopResult(
                triggered=True,
                reason=f"Guardrail violations: {', '.join(guardrail_violations)}",
                action="halt_and_escalate"
            )

        return HardStopResult(triggered=False, action="continue")
