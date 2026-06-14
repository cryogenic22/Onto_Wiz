"""
Onto_Wiz Delta Generator

Transforms a ReasoningEvent (SME game output) into structured deltas.
Each delta is properly scoped to the context (TA, lifecycle, geography).

From ONE SME session, this generates:
1. JudgmentPattern deltas (reusable heuristics)
2. Guardrail deltas (safety rules)
3. Edge deltas (supports/contradicts relationships)
4. Metric semantics deltas
5. Action template deltas
6. Few-shot prompt templates

All deltas are PROPOSED, not active - they go to the review queue.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from .models import (
    BlastRadius,
    Delta,
    DeltaStatus,
    DeltaType,
)
from .reasoning_event import (
    BrandProfile,
    HypothesisCategory,
    ReasoningEvent,
    ScenarioContext,
    TherapeuticArea,
)

# =============================================================================
# DELTA GENERATOR
# =============================================================================

class DeltaGenerator:
    """
    Transforms SME game output into ontology deltas.

    Each ReasoningEvent generates multiple deltas, properly scoped
    to the context (TA, lifecycle, geography, channel).

    Key design principle: Patterns are context-specific.
    - Oncology specialty has different access dynamics than retail CNS
    - Launch phase has different signals than LOE phase
    - US market has different payer dynamics than EU
    """

    def __init__(self):
        self._generated_deltas: list[Delta] = []

    def generate(self, event: ReasoningEvent) -> list[Delta]:
        """
        Generate all deltas from a ReasoningEvent.

        Returns list of proposed deltas ready for review queue.
        """
        self._generated_deltas = []

        # 1. Generate JudgmentPattern delta
        pattern_delta = self._generate_pattern_delta(event)
        if pattern_delta:
            self._generated_deltas.append(pattern_delta)

        # 2. Generate Guardrail deltas from common mistakes
        guardrail_deltas = self._generate_guardrail_deltas(event)
        self._generated_deltas.extend(guardrail_deltas)

        # 3. Generate Edge deltas (supports/contradicts)
        edge_deltas = self._generate_edge_deltas(event)
        self._generated_deltas.extend(edge_deltas)

        # 4. Generate Metric semantics deltas
        metric_deltas = self._generate_metric_deltas(event)
        self._generated_deltas.extend(metric_deltas)

        # 5. Generate Action template deltas
        action_deltas = self._generate_action_deltas(event)
        self._generated_deltas.extend(action_deltas)

        # Mark event as processed
        event.processed = True
        event.deltas_generated = [d.id for d in self._generated_deltas]

        return self._generated_deltas

    # -------------------------------------------------------------------------
    # Pattern Generation
    # -------------------------------------------------------------------------

    def _generate_pattern_delta(self, event: ReasoningEvent) -> Delta | None:
        """
        Generate a JudgmentPattern delta from the SME's reasoning.

        The pattern is scoped to the specific context (TA, lifecycle, geography).
        """
        if not event.primary_hypothesis:
            return None

        brand = event.scenario.brand
        hypothesis = event.primary_hypothesis

        # Build scope from context
        scope = self._build_scope(event.scenario)

        # Build typical drivers from hypothesis ranking
        typical_drivers = [
            {
                "driver_name": self._hypothesis_to_driver(hypothesis.category),
                "prior_confidence": event.sme_confidence,
                "specific_variant": hypothesis.specific_driver,
            }
        ]

        # Add alternatives with lower confidence
        for alt in event.alternative_hypotheses:
            typical_drivers.append({
                "driver_name": self._hypothesis_to_driver(alt.category),
                "prior_confidence": alt.confidence,
                "specific_variant": alt.specific_driver,
            })

        # Build disallowed drivers from common mistakes
        disallowed_drivers = []
        for mistake in event.common_mistakes:
            disallowed_drivers.append({
                "driver_name": mistake.wrong_conclusion,
                "unless_evidence": mistake.unless_evidence,
            })

        # Generate pattern ID based on context
        pattern_id = self._generate_pattern_id(event)

        # Build the pattern content
        pattern_content = {
            "pattern_id": pattern_id,
            "version": "1.0.0",
            "name": f"{event.scenario_type}_{brand.therapeutic_area.value}",

            # Context-specific scope
            "applies_when": {
                "signals": [s.signal_name for s in event.signal_priorities],
                "context": [event.scenario_type],
                "therapeutic_area": brand.therapeutic_area.value,
                "lifecycle": brand.lifecycle.value,
                "channel": brand.channel.value,
            },

            "scope": scope,

            "typical_drivers": typical_drivers,
            "disallowed_drivers": disallowed_drivers,

            "pattern_recognition": {
                "frequency": event.pattern_recognition.frequency if event.pattern_recognition else "unknown",
                "typical_outcome": event.pattern_recognition.typical_outcome if event.pattern_recognition else None,
            },

            "decay": {
                "valid_for_days": self._decay_by_context(brand),
                "decay_type": "linear",
                "refresh_triggers": ["new_evidence", "sme_replay", "market_change"],
            },

            "governance": {
                "owner": event.sme_persona,
                "source": "sme_game",
                "source_event_id": event.id,
            },
        }

        # Determine blast radius
        blast_radius = self._compute_blast_radius(event)

        return Delta(
            type=DeltaType.PROPOSED_PATTERN,
            status=DeltaStatus.PROPOSED,
            content=pattern_content,
            confidence=event.sme_confidence,
            evidence_pointers=[f"reasoning_event:{event.id}"],
            blast_radius=blast_radius,
            impacted_missions=[event.scenario_type],
            impacted_personas=[event.sme_persona],
            source_type="sme_game",
            source_id=event.id,
        )

    # -------------------------------------------------------------------------
    # Guardrail Generation
    # -------------------------------------------------------------------------

    def _generate_guardrail_deltas(self, event: ReasoningEvent) -> list[Delta]:
        """
        Generate Guardrail deltas from common mistakes.

        Each "common mistake" becomes a guardrail that blocks
        premature conclusions without proper evidence.
        """
        deltas = []
        brand = event.scenario.brand

        for mistake in event.common_mistakes:
            guardrail_content = {
                "guardrail_id": f"guard_{uuid4().hex[:8]}",
                "name": f"Block: {mistake.wrong_conclusion[:50]}",

                # What this blocks
                "blocks_claims": [mistake.wrong_conclusion],
                "blocks_drivers": [mistake.wrong_conclusion],

                # When blocking doesn't apply
                "unless_evidence": [mistake.unless_evidence] if mistake.unless_evidence else [],

                # Context scope
                "applies_to": {
                    "therapeutic_area": brand.therapeutic_area.value,
                    "lifecycle": brand.lifecycle.value,
                    "scenario_types": [event.scenario_type],
                },

                # Governance
                "risk_class": "decision_support",
                "rationale": mistake.why_wrong or "SME flagged as common mistake",
                "source_event_id": event.id,
            }

            delta = Delta(
                type=DeltaType.PROPOSED_GUARDRAIL,
                status=DeltaStatus.PROPOSED,
                content=guardrail_content,
                confidence=0.8,  # Guardrails from SME are high confidence
                evidence_pointers=[f"reasoning_event:{event.id}"],
                blast_radius=BlastRadius.MEDIUM,  # Guardrails affect many paths
                source_type="sme_game",
                source_id=event.id,
            )
            deltas.append(delta)

        return deltas

    # -------------------------------------------------------------------------
    # Edge Generation
    # -------------------------------------------------------------------------

    def _generate_edge_deltas(self, event: ReasoningEvent) -> list[Delta]:
        """
        Generate edge deltas from disconfirming logic.

        Each "change my mind" condition becomes:
        - SUPPORTS edges (signal -> hypothesis)
        - CONTRADICTS edges (signal -> alternative hypothesis)
        """
        deltas = []
        brand = event.scenario.brand

        # Edges from signal priorities (SUPPORTS)
        for signal in event.signal_priorities:
            if event.primary_hypothesis:
                edge_content = {
                    "source_node": f"signal.{signal.signal_name}",
                    "target_node": f"driver.{self._hypothesis_to_driver(event.primary_hypothesis.category)}",
                    "edge_type": "supports" if signal.role == "validation" else "leads_to",
                    "confidence": event.sme_confidence * 0.8,  # Slightly lower than overall
                    "context": {
                        "therapeutic_area": brand.therapeutic_area.value,
                        "lifecycle": brand.lifecycle.value,
                        "scenario_type": event.scenario_type,
                    },
                    "source_event_id": event.id,
                }

                delta = Delta(
                    type=DeltaType.PROPOSED_EDGE,
                    status=DeltaStatus.PROPOSED,
                    content=edge_content,
                    confidence=event.sme_confidence * 0.8,
                    blast_radius=BlastRadius.LOW,
                    source_type="sme_game",
                    source_id=event.id,
                )
                deltas.append(delta)

        # Edges from disconfirming logic (CONTRADICTS)
        for disconfirm in event.disconfirming_logic:
            if disconfirm.would_rule_out:
                edge_content = {
                    "source_node": f"condition.{disconfirm.condition[:30]}",
                    "target_node": f"driver.{disconfirm.would_rule_out}",
                    "edge_type": "contradicts",
                    "confidence": 0.7,
                    "condition": disconfirm.condition,
                    "context": {
                        "therapeutic_area": brand.therapeutic_area.value,
                        "lifecycle": brand.lifecycle.value,
                    },
                    "source_event_id": event.id,
                }

                delta = Delta(
                    type=DeltaType.PROPOSED_EDGE,
                    status=DeltaStatus.PROPOSED,
                    content=edge_content,
                    confidence=0.7,
                    blast_radius=BlastRadius.LOW,
                    source_type="sme_game",
                    source_id=event.id,
                )
                deltas.append(delta)

        return deltas

    # -------------------------------------------------------------------------
    # Metric Semantics Generation
    # -------------------------------------------------------------------------

    def _generate_metric_deltas(self, event: ReasoningEvent) -> list[Delta]:
        """
        Generate metric semantics deltas from signal priorities.

        Captures how metrics should be interpreted in this context:
        - Which metrics are leading vs lagging
        - Which metrics validate vs disconfirm
        """
        deltas = []
        brand = event.scenario.brand

        for signal in event.signal_priorities:
            metric_content = {
                "metric_name": signal.signal_name,
                "role_in_context": signal.role,  # validation, disconfirming, leading
                "priority_rank": signal.priority_rank,

                # Context-specific interpretation
                "context": {
                    "therapeutic_area": brand.therapeutic_area.value,
                    "lifecycle": brand.lifecycle.value,
                    "scenario_type": event.scenario_type,
                },

                "interpretation_notes": self._metric_interpretation(signal, event),
                "source_event_id": event.id,
            }

            delta = Delta(
                type=DeltaType.PROPOSED_MAPPING,  # Metric semantics are mappings
                status=DeltaStatus.PROPOSED,
                content=metric_content,
                confidence=0.75,
                blast_radius=BlastRadius.LOW,
                source_type="sme_game",
                source_id=event.id,
            )
            deltas.append(delta)

        return deltas

    # -------------------------------------------------------------------------
    # Action Template Generation
    # -------------------------------------------------------------------------

    def _generate_action_deltas(self, event: ReasoningEvent) -> list[Delta]:
        """
        Generate action template deltas from recommended actions.
        """
        deltas = []
        brand = event.scenario.brand

        for action in event.recommended_actions:
            action_content = {
                "action_id": f"action_{uuid4().hex[:8]}",
                "name": action.action[:50],
                "description": action.action,
                "action_type": action.action_type,
                "priority": action.priority,
                "owner_function": action.owner_function,

                # When this action applies
                "trigger_context": {
                    "scenario_type": event.scenario_type,
                    "hypothesis": event.primary_hypothesis.category.value if event.primary_hypothesis else None,
                    "therapeutic_area": brand.therapeutic_area.value,
                },

                "source_event_id": event.id,
            }

            delta = Delta(
                type=DeltaType.PROPOSED_ACTION,
                status=DeltaStatus.PROPOSED,
                content=action_content,
                confidence=0.8,
                blast_radius=BlastRadius.LOW,
                source_type="sme_game",
                source_id=event.id,
            )
            deltas.append(delta)

        return deltas

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _build_scope(self, scenario: ScenarioContext) -> dict[str, Any]:
        """Build scope dictionary from scenario context."""
        brand = scenario.brand
        return {
            "geography": scenario.geography,
            "region": scenario.region,
            "therapeutic_area": brand.therapeutic_area.value,
            "lifecycle": brand.lifecycle.value,
            "channel": brand.channel.value,
            "asset_class": brand.asset_class.value,
            "market_archetype": brand.market_archetype.value,
            "is_specialty": brand.is_specialty,
        }

    def _hypothesis_to_driver(self, category: HypothesisCategory) -> str:
        """Map hypothesis category to canonical driver name."""
        mapping = {
            HypothesisCategory.COMMERCIAL_EXECUTION: "field_execution_gap",
            HypothesisCategory.MARKET_ACCESS: "access_friction",
            HypothesisCategory.CLINICAL_SAFETY: "safety_signal",
            HypothesisCategory.COMPETITIVE_PRESSURE: "competitor_displacement",
            HypothesisCategory.DEMAND_EROSION: "demand_erosion",
            HypothesisCategory.SUPPLY_DISRUPTION: "supply_disruption",
            HypothesisCategory.TOO_EARLY: "insufficient_data",
        }
        return mapping.get(category, category.value)

    def _generate_pattern_id(self, event: ReasoningEvent) -> str:
        """Generate a unique pattern ID based on context."""
        brand = event.scenario.brand
        parts = [
            "JP",  # JudgmentPattern prefix
            event.scenario_type.upper()[:10],
            brand.therapeutic_area.value.upper()[:4],
            brand.lifecycle.value.upper()[:4],
            f"V{datetime.utcnow().strftime('%y%m')}",
        ]
        return "_".join(parts)

    def _decay_by_context(self, brand: BrandProfile) -> int:
        """
        Determine decay period based on context.

        Fast-moving contexts decay faster:
        - Launch: 90 days (things change quickly)
        - Growth: 180 days
        - Maturity: 365 days
        - LOE/biosimilar: 90 days (competitive dynamics shifting)
        """
        lifecycle_decay = {
            "pre_launch": 90,
            "launch": 90,
            "growth": 180,
            "maturity": 365,
            "loe": 90,
            "post_loe": 180,
        }
        return lifecycle_decay.get(brand.lifecycle.value, 180)

    def _compute_blast_radius(self, event: ReasoningEvent) -> BlastRadius:
        """
        Compute blast radius based on pattern scope.

        Broader scope = higher blast radius.
        """
        brand = event.scenario.brand

        # Context-specific patterns have lower blast radius
        if event.scenario.region:  # Regional scope
            return BlastRadius.LOW

        # TA-specific but national
        if brand.therapeutic_area != TherapeuticArea.OTHER:
            return BlastRadius.MEDIUM

        # Broad patterns
        return BlastRadius.HIGH

    def _metric_interpretation(self, signal, event: ReasoningEvent) -> str:
        """Generate interpretation note for metric."""
        if signal.role == "validation":
            return f"Primary validation metric for {event.scenario_type}"
        elif signal.role == "disconfirming":
            return "Disconfirms hypothesis if pattern doesn't match"
        elif signal.role == "leading":
            return "Leading indicator - changes before other signals"
        return f"Supporting signal for {event.scenario_type}"


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def process_sme_session(
    event: ReasoningEvent,
    contribution_store=None,
) -> list[Delta]:
    """
    Process an SME game session and generate all deltas.

    This is the main entry point for the game -> backend flow.
    If contribution_store is provided, records the contribution.
    """
    generator = DeltaGenerator()
    deltas = generator.generate(event)
    if contribution_store is not None:
        contribution_store.record(event, [d.id for d in deltas])
    return deltas
