"""
Onto_Wiz Reasoning Event & Game Session

This is the structured output from an SME game session.
The SME sees simple questions; this captures their judgment invisibly.

A ReasoningEvent captures:
- Scenario context (brand profile, TA, geography, lifecycle)
- SME's hypothesis ranking
- Signal prioritization
- Disconfirming evidence ("change my mind")
- Common mistakes (anti-patterns)
- Recommended actions
- Confidence calibration

This becomes the input for DeltaGenerator, which creates:
- JudgmentPattern deltas
- Guardrail deltas
- Edge deltas (supports/contradicts)
- Metric semantics updates
- Few-shot prompt templates
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# =============================================================================
# BRAND & CONTEXT PROFILING
# =============================================================================

class TherapeuticArea(str, Enum):
    """Therapeutic areas with distinct commercial dynamics."""
    ONCOLOGY = "oncology"
    IMMUNOLOGY = "immunology"
    CNS = "cns"                     # Central Nervous System
    CARDIOVASCULAR = "cardiovascular"
    RARE_DISEASE = "rare_disease"
    INFECTIOUS_DISEASE = "infectious_disease"
    RESPIRATORY = "respiratory"
    METABOLIC = "metabolic"         # Diabetes, obesity
    DERMATOLOGY = "dermatology"
    OPHTHALMOLOGY = "ophthalmology"
    HEMATOLOGY = "hematology"
    WOMENS_HEALTH = "womens_health"
    OTHER = "other"


class BrandLifecycle(str, Enum):
    """Brand lifecycle stage - affects commercial dynamics significantly."""
    PRE_LAUNCH = "pre_launch"       # Before approval
    LAUNCH = "launch"               # First 12-18 months
    GROWTH = "growth"               # Expanding indications/share
    MATURITY = "maturity"           # Stable, defending share
    LOE = "loe"                     # Loss of exclusivity
    POST_LOE = "post_loe"           # Generic competition


class AssetClass(str, Enum):
    """Drug modality - affects commercial model."""
    SMALL_MOLECULE = "small_molecule"
    BIOLOGIC = "biologic"
    BIOSIMILAR = "biosimilar"
    CELL_GENE = "cell_gene"
    VACCINE = "vaccine"
    DEVICE = "device"
    COMBINATION = "combination"


class ChannelType(str, Enum):
    """Distribution channel - affects access dynamics."""
    RETAIL = "retail"
    SPECIALTY = "specialty"
    BUY_AND_BILL = "buy_and_bill"   # Physician-administered
    HUB = "hub"                     # Patient services hub
    DIRECT = "direct"


class MarketArchetype(str, Enum):
    """Market structure archetypes."""
    MONOPOLY = "monopoly"           # Single player
    DUOPOLY = "duopoly"             # Two major players
    FRAGMENTED = "fragmented"       # Many small players
    BIOSIMILAR_WAVE = "biosimilar_wave"
    GENERIC_DOMINANT = "generic_dominant"


@dataclass
class BrandProfile:
    """
    Rich brand context for scenario interpretation.

    Different TAs and lifecycles have different:
    - Access dynamics (oncology vs chronic)
    - Competitive pressures
    - Field model requirements
    - Typical failure modes
    """
    brand_name: str
    therapeutic_area: TherapeuticArea = TherapeuticArea.OTHER
    lifecycle: BrandLifecycle = BrandLifecycle.GROWTH
    asset_class: AssetClass = AssetClass.SMALL_MOLECULE
    channel: ChannelType = ChannelType.RETAIL
    market_archetype: MarketArchetype = MarketArchetype.FRAGMENTED

    # Key product attributes
    indications: list[str] = field(default_factory=list)
    launch_date: datetime | None = None
    loe_date: datetime | None = None

    # Commercial context
    is_specialty: bool = False
    requires_rems: bool = False      # Risk Evaluation and Mitigation Strategy
    has_hub: bool = False
    has_patient_support: bool = False

    # Competitive context
    primary_competitors: list[str] = field(default_factory=list)
    biosimilar_exposure: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand_name": self.brand_name,
            "therapeutic_area": self.therapeutic_area.value,
            "lifecycle": self.lifecycle.value,
            "asset_class": self.asset_class.value,
            "channel": self.channel.value,
            "market_archetype": self.market_archetype.value,
            "indications": self.indications,
            "is_specialty": self.is_specialty,
            "requires_rems": self.requires_rems,
            "has_hub": self.has_hub,
            "primary_competitors": self.primary_competitors,
        }


@dataclass
class ScenarioContext:
    """
    Full context for a reasoning scenario.
    """
    # Brand profile
    brand: BrandProfile

    # Geographic scope
    geography: str = "US"
    region: str | None = None    # e.g., "Northeast", "Midwest"

    # Temporal scope
    time_period: str = ""           # e.g., "Last 8 weeks"
    comparison_period: str | None = None

    # The triggering observation
    observation: str = ""           # e.g., "Sales down 10%"
    national_context: str | None = None  # e.g., "National flat"

    # Stakeholder perspectives
    field_says: str | None = None
    marketing_says: str | None = None
    access_says: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand": self.brand.to_dict(),
            "geography": self.geography,
            "region": self.region,
            "time_period": self.time_period,
            "observation": self.observation,
            "national_context": self.national_context,
            "field_says": self.field_says,
            "marketing_says": self.marketing_says,
            "access_says": self.access_says,
        }


# =============================================================================
# SME RESPONSE CAPTURE
# =============================================================================

class HypothesisCategory(str, Enum):
    """High-level hypothesis categories (what SME picks first)."""
    COMMERCIAL_EXECUTION = "commercial_execution"
    MARKET_ACCESS = "market_access"
    CLINICAL_SAFETY = "clinical_safety"
    COMPETITIVE_PRESSURE = "competitive_pressure"
    DEMAND_EROSION = "demand_erosion"
    SUPPLY_DISRUPTION = "supply_disruption"
    TOO_EARLY = "too_early"         # Very valuable signal!


@dataclass
class HypothesisRanking:
    """SME's hypothesis with reasoning."""
    category: HypothesisCategory
    specific_driver: str | None = None  # e.g., "PA edits" vs general "access"
    confidence: float = 0.5
    reasoning: str | None = None


@dataclass
class SignalPriority:
    """Which signals the SME would check first."""
    signal_name: str                # e.g., "NBRx", "TRx", "PA_rejects"
    role: str = "validation"        # validation, disconfirming, leading
    priority_rank: int = 1


@dataclass
class DisconfirmingLogic:
    """What would change the SME's mind."""
    condition: str                  # e.g., "If NBRx is flat but TRx drops"
    would_suggest: str              # e.g., "Access issue at fulfillment"
    would_rule_out: str | None = None  # e.g., "Demand erosion"


@dataclass
class CommonMistake:
    """What people commonly get wrong (anti-pattern)."""
    wrong_conclusion: str           # e.g., "Assume demand erosion"
    why_wrong: str | None = None
    unless_evidence: str | None = None  # When it might be right


@dataclass
class RecommendedAction:
    """What the SME would do next."""
    action: str                     # e.g., "Pull PA reject data"
    action_type: str = "investigate"  # investigate, escalate, wait, intervene
    priority: int = 1
    owner_function: str | None = None  # "access_team", "field", "analytics"


@dataclass
class PatternRecognition:
    """Has the SME seen this before?"""
    frequency: str = "sometimes"    # often, sometimes, rarely, never
    typical_outcome: str | None = None
    time_to_resolution: str | None = None


# =============================================================================
# REASONING EVENT (The Full Game Output)
# =============================================================================

@dataclass
class ReasoningEvent:
    """
    Structured output from one SME game session.

    This is the contract between the game UI and the backend.
    Everything the SME provides is captured here, then processed
    by DeltaGenerator to create ontology updates.
    """
    id: str = field(default_factory=lambda: str(uuid4()))

    # Session metadata
    session_id: str = ""
    sme_id: str = ""                # Anonymized SME identifier
    sme_persona: str = ""           # e.g., "commercial_lead", "access_strategist"
    captured_at: datetime = field(default_factory=datetime.utcnow)

    # The scenario
    scenario: ScenarioContext = field(default_factory=lambda: ScenarioContext(
        brand=BrandProfile(brand_name="Unknown")
    ))
    scenario_type: str = ""         # e.g., "regional_performance_dip"

    # SME responses
    primary_hypothesis: HypothesisRanking | None = None
    alternative_hypotheses: list[HypothesisRanking] = field(default_factory=list)

    signal_priorities: list[SignalPriority] = field(default_factory=list)

    disconfirming_logic: list[DisconfirmingLogic] = field(default_factory=list)

    pattern_recognition: PatternRecognition | None = None

    common_mistakes: list[CommonMistake] = field(default_factory=list)

    recommended_actions: list[RecommendedAction] = field(default_factory=list)

    # Confidence calibration
    sme_confidence: float = 0.5     # 0-1 from slider

    # Free-text captures
    additional_notes: str | None = None

    # Processing status
    processed: bool = False
    deltas_generated: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "sme_persona": self.sme_persona,
            "captured_at": self.captured_at.isoformat(),
            "scenario": self.scenario.to_dict(),
            "scenario_type": self.scenario_type,
            "primary_hypothesis": {
                "category": self.primary_hypothesis.category.value,
                "specific_driver": self.primary_hypothesis.specific_driver,
                "confidence": self.primary_hypothesis.confidence,
            } if self.primary_hypothesis else None,
            "signal_priorities": [{"name": s.signal_name, "role": s.role} for s in self.signal_priorities],
            "disconfirming_logic": [{"condition": d.condition, "would_suggest": d.would_suggest} for d in self.disconfirming_logic],
            "common_mistakes": [{"wrong": m.wrong_conclusion} for m in self.common_mistakes],
            "recommended_actions": [{"action": a.action, "type": a.action_type} for a in self.recommended_actions],
            "sme_confidence": self.sme_confidence,
            "processed": self.processed,
        }


# =============================================================================
# EXAMPLE: The SME session from your conversation
# =============================================================================

def example_reasoning_event() -> ReasoningEvent:
    """
    Example capturing the SME session from the conversation.

    Scenario: Brand X | US Northeast | Sales down 10%
    """

    brand = BrandProfile(
        brand_name="Brand X",
        therapeutic_area=TherapeuticArea.ONCOLOGY,  # Example
        lifecycle=BrandLifecycle.GROWTH,
        asset_class=AssetClass.BIOLOGIC,
        channel=ChannelType.SPECIALTY,
        is_specialty=True,
        has_hub=True,
    )

    scenario = ScenarioContext(
        brand=brand,
        geography="US",
        region="Northeast",
        time_period="Last 8 weeks",
        observation="Sales down 10%",
        national_context="National trend flat",
        field_says="Access issue",
        marketing_says="Execution",
    )

    event = ReasoningEvent(
        scenario=scenario,
        scenario_type="regional_performance_dip",
        sme_persona="commercial_sme",

        primary_hypothesis=HypothesisRanking(
            category=HypothesisCategory.MARKET_ACCESS,
            specific_driver="PA edits / localized access friction",
            confidence=0.70,
        ),

        signal_priorities=[
            SignalPriority(signal_name="TRx", role="validation", priority_rank=1),
            SignalPriority(signal_name="payer_policy_change", role="validation", priority_rank=2),
        ],

        disconfirming_logic=[
            DisconfirmingLogic(
                condition="If TRx is flat but NBRx is dropping",
                would_suggest="Initiation/demand issue, not access",
                would_rule_out="Access friction at fulfillment",
            ),
            DisconfirmingLogic(
                condition="If top deciles are stable",
                would_suggest="Localized friction, not broad demand",
                would_rule_out="Demand erosion",
            ),
        ],

        pattern_recognition=PatternRecognition(
            frequency="often",
            typical_outcome="Localized PA edits rather than true access loss",
        ),

        common_mistakes=[
            CommonMistake(
                wrong_conclusion="Assume demand erosion too quickly",
                why_wrong="Need NBRx confirmation first",
                unless_evidence="NBRx decline + engagement deterioration",
            ),
        ],

        recommended_actions=[
            RecommendedAction(
                action="Ask access team to investigate payer edits",
                action_type="investigate",
                priority=1,
                owner_function="access_team",
            ),
            RecommendedAction(
                action="Pull PA reject rate by DMA and payer",
                action_type="investigate",
                priority=2,
                owner_function="analytics",
            ),
        ],

        sme_confidence=0.70,
    )

    return event
