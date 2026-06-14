"""
Onto_Wiz Confidence Engine

Computes confidence from evidence, pattern priors, and conflict analysis.
This replaces caller-provided confidence with computed confidence.

Confidence Factors:
1. Base confidence from pattern priors
2. Evidence reliability weighting (HARD > SOFT > RUMOR)
3. Corroboration count bonus
4. Conflict ratio penalty
5. Missing required evidence penalty
6. Staleness/decay penalty

This is the engine that makes "credible reasoning" possible.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .evidence import EvidencePointer, EvidenceStore
from .models import JudgmentPattern

# =============================================================================
# CONFIDENCE SIGNALS
# =============================================================================

@dataclass
class ConfidenceSignal:
    """
    A single factor contributing to confidence computation.
    """
    factor: str           # e.g., "evidence_reliability", "conflict_ratio"
    weight: float         # Contribution weight
    value: float          # Raw value (0-1)
    contribution: float   # weight * value
    explanation: str      # Human-readable explanation


@dataclass
class ConfidenceResult:
    """
    Result of confidence computation with full trace.
    """
    final_confidence: float
    signals: list[ConfidenceSignal]

    # Decision support
    is_actionable: bool       # > threshold
    requires_evidence: bool   # Missing required evidence
    has_conflicts: bool       # Conflict ratio > limit

    # Explanations
    primary_driver: str
    limiting_factors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": round(self.final_confidence, 3),
            "is_actionable": self.is_actionable,
            "requires_evidence": self.requires_evidence,
            "has_conflicts": self.has_conflicts,
            "primary_driver": self.primary_driver,
            "limiting_factors": self.limiting_factors,
            "signal_breakdown": [
                {"factor": s.factor, "contribution": round(s.contribution, 3), "explanation": s.explanation}
                for s in self.signals
            ]
        }


# =============================================================================
# CONFIDENCE ENGINE
# =============================================================================

class ConfidenceEngine:
    """
    Computes confidence from evidence and pattern priors.

    This is the core of "credible reasoning" - without computed confidence,
    any approval or decision is arbitrary.

    Confidence = Base Prior
                 × Evidence Reliability Factor
                 × Corroboration Bonus
                 × (1 - Conflict Penalty)
                 × (1 - Missing Evidence Penalty)
                 × Freshness Factor
    """

    # Thresholds
    ACTIONABLE_THRESHOLD = 0.55
    HIGH_CONFLICT_RATIO = 0.4
    MISSING_EVIDENCE_PENALTY = 0.25

    # Weights for each factor
    WEIGHTS = {
        "base_prior": 0.30,
        "evidence_reliability": 0.25,
        "corroboration": 0.15,
        "conflict_penalty": 0.15,
        "freshness": 0.15,
    }

    def __init__(self, evidence_store: EvidenceStore | None = None):
        self._evidence_store = evidence_store or EvidenceStore()

    def compute(
        self,
        hypothesis: str,
        pattern: JudgmentPattern | None = None,
        evidence_pointers: list[EvidencePointer] = None,
        contradicting_pointers: list[EvidencePointer] = None,
        required_evidence_types: list[str] = None,
        context: dict[str, Any] | None = None
    ) -> ConfidenceResult:
        """
        Compute confidence for a hypothesis given evidence and pattern.

        Args:
            hypothesis: The driver/hypothesis being evaluated
            pattern: Optional JudgmentPattern providing priors
            evidence_pointers: Evidence supporting the hypothesis
            contradicting_pointers: Evidence contradicting the hypothesis
            required_evidence_types: Evidence types that must be present
            context: Additional context (for freshness check)

        Returns:
            ConfidenceResult with full trace
        """
        evidence_pointers = evidence_pointers or []
        contradicting_pointers = contradicting_pointers or []
        required_evidence_types = required_evidence_types or []

        signals = []

        # 1. Base Prior from Pattern
        base_prior = self._compute_base_prior(hypothesis, pattern)
        signals.append(base_prior)

        # 2. Evidence Reliability
        evidence_reliability = self._compute_evidence_reliability(evidence_pointers)
        signals.append(evidence_reliability)

        # 3. Corroboration Bonus
        corroboration = self._compute_corroboration(evidence_pointers)
        signals.append(corroboration)

        # 4. Conflict Penalty
        conflict = self._compute_conflict_penalty(evidence_pointers, contradicting_pointers)
        signals.append(conflict)

        # 5. Freshness Factor
        freshness = self._compute_freshness(pattern, context)
        signals.append(freshness)

        # Compute weighted sum
        total_weight = sum(self.WEIGHTS.values())
        weighted_sum = sum(s.contribution for s in signals)
        final_confidence = weighted_sum / total_weight

        # Apply missing evidence penalty
        has_missing = self._check_missing_evidence(evidence_pointers, required_evidence_types)
        if has_missing:
            final_confidence *= (1 - self.MISSING_EVIDENCE_PENALTY)

        # Clamp to [0, 1]
        final_confidence = max(0.0, min(1.0, final_confidence))

        # Decision support
        conflict_ratio = len(contradicting_pointers) / max(1, len(evidence_pointers) + len(contradicting_pointers))

        # Determine limiting factors
        limiting_factors = []
        sorted_signals = sorted(signals, key=lambda s: s.contribution)
        for s in sorted_signals[:2]:
            if s.contribution < self.WEIGHTS.get(s.factor, 0.15) * 0.5:
                limiting_factors.append(s.explanation)

        if has_missing:
            limiting_factors.append("Missing required evidence types")

        return ConfidenceResult(
            final_confidence=final_confidence,
            signals=signals,
            is_actionable=final_confidence >= self.ACTIONABLE_THRESHOLD,
            requires_evidence=has_missing,
            has_conflicts=conflict_ratio > self.HIGH_CONFLICT_RATIO,
            primary_driver=hypothesis,
            limiting_factors=limiting_factors,
        )

    def _compute_base_prior(
        self,
        hypothesis: str,
        pattern: JudgmentPattern | None
    ) -> ConfidenceSignal:
        """Get base prior from pattern's driver attributions."""
        prior = 0.5  # Default if no pattern

        if pattern:
            for driver in pattern.typical_drivers:
                if driver.driver == hypothesis or hypothesis in driver.driver:
                    prior = driver.prior_confidence
                    break

        return ConfidenceSignal(
            factor="base_prior",
            weight=self.WEIGHTS["base_prior"],
            value=prior,
            contribution=self.WEIGHTS["base_prior"] * prior,
            explanation=f"Pattern prior for {hypothesis}: {prior:.2f}"
        )

    def _compute_evidence_reliability(
        self,
        evidence_pointers: list[EvidencePointer]
    ) -> ConfidenceSignal:
        """Compute average reliability of supporting evidence."""
        if not evidence_pointers:
            return ConfidenceSignal(
                factor="evidence_reliability",
                weight=self.WEIGHTS["evidence_reliability"],
                value=0.0,
                contribution=0.0,
                explanation="No evidence provided"
            )

        # Get reliability weights from evidence items
        total_reliability = 0.0
        count = 0

        for pointer in evidence_pointers:
            evidence = self._evidence_store.get(pointer.evidence_id)
            if evidence:
                total_reliability += evidence.reliability_weight()
                count += 1
            else:
                # Use pointer's confidence as fallback
                total_reliability += pointer.confidence * 0.6  # Soft default
                count += 1

        avg_reliability = total_reliability / max(1, count)

        return ConfidenceSignal(
            factor="evidence_reliability",
            weight=self.WEIGHTS["evidence_reliability"],
            value=avg_reliability,
            contribution=self.WEIGHTS["evidence_reliability"] * avg_reliability,
            explanation=f"Avg evidence reliability: {avg_reliability:.2f} ({count} items)"
        )

    def _compute_corroboration(
        self,
        evidence_pointers: list[EvidencePointer]
    ) -> ConfidenceSignal:
        """More independent sources = higher confidence."""
        count = len(evidence_pointers)

        # Diminishing returns: 1 source = 0.3, 2 = 0.6, 3+ = 0.8+
        if count == 0:
            value = 0.0
        elif count == 1:
            value = 0.3
        elif count == 2:
            value = 0.6
        elif count == 3:
            value = 0.8
        else:
            value = min(1.0, 0.8 + 0.05 * (count - 3))

        return ConfidenceSignal(
            factor="corroboration",
            weight=self.WEIGHTS["corroboration"],
            value=value,
            contribution=self.WEIGHTS["corroboration"] * value,
            explanation=f"{count} corroborating evidence items"
        )

    def _compute_conflict_penalty(
        self,
        supporting: list[EvidencePointer],
        contradicting: list[EvidencePointer]
    ) -> ConfidenceSignal:
        """Penalty for contradicting evidence."""
        total = len(supporting) + len(contradicting)

        conflict_ratio = 0.0 if total == 0 else len(contradicting) / total

        # Convert ratio to penalty (0 conflicts = 1.0 value, 50% conflicts = 0.5 value)
        value = 1.0 - conflict_ratio

        return ConfidenceSignal(
            factor="conflict_penalty",
            weight=self.WEIGHTS["conflict_penalty"],
            value=value,
            contribution=self.WEIGHTS["conflict_penalty"] * value,
            explanation=f"Conflict ratio: {conflict_ratio:.2f} ({len(contradicting)} of {total})"
        )

    def _compute_freshness(
        self,
        pattern: JudgmentPattern | None,
        context: dict[str, Any] | None
    ) -> ConfidenceSignal:
        """Decay pattern confidence over time."""
        if not pattern or not pattern.decay:
            return ConfidenceSignal(
                factor="freshness",
                weight=self.WEIGHTS["freshness"],
                value=1.0,
                contribution=self.WEIGHTS["freshness"] * 1.0,
                explanation="No decay configured"
            )

        decay = pattern.decay
        created = pattern.created_at
        now = datetime.utcnow()

        age_days = (now - created).days
        valid_days = decay.valid_for_days

        if age_days <= 0:
            value = 1.0
        elif age_days >= valid_days:
            value = 0.2  # Minimum freshness
        else:
            # Linear decay
            value = 1.0 - (0.8 * age_days / valid_days)

        return ConfidenceSignal(
            factor="freshness",
            weight=self.WEIGHTS["freshness"],
            value=value,
            contribution=self.WEIGHTS["freshness"] * value,
            explanation=f"Pattern age: {age_days} days (valid for {valid_days})"
        )

    def _check_missing_evidence(
        self,
        evidence_pointers: list[EvidencePointer],
        required_types: list[str]
    ) -> bool:
        """Check if required evidence types are missing."""
        if not required_types:
            return False

        provided_types = set()
        for pointer in evidence_pointers:
            evidence = self._evidence_store.get(pointer.evidence_id)
            if evidence:
                provided_types.add(evidence.type.value)

        return any(req not in provided_types for req in required_types)

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    def is_actionable(self, confidence: float) -> bool:
        """Check if confidence is above actionable threshold."""
        return confidence >= self.ACTIONABLE_THRESHOLD

    def should_halt(
        self,
        confidence: float,
        conflict_ratio: float = 0.0,
        missing_required: bool = False
    ) -> tuple[bool, str]:
        """
        Check if agent should halt based on TraversalPolicy rules.

        Returns (should_halt, reason).
        """
        if confidence < self.ACTIONABLE_THRESHOLD:
            return True, f"Confidence {confidence:.2f} below threshold {self.ACTIONABLE_THRESHOLD}"

        if conflict_ratio > self.HIGH_CONFLICT_RATIO:
            return True, f"Conflict ratio {conflict_ratio:.2f} exceeds limit {self.HIGH_CONFLICT_RATIO}"

        if missing_required:
            return True, "Missing required evidence"

        return False, ""

    def compute_quick(
        self,
        evidence_count: int,
        hard_evidence_count: int = 0,
        conflict_count: int = 0,
        base_prior: float = 0.5
    ) -> float:
        """
        Quick confidence computation without full evidence lookup.
        Useful for fast filtering.
        """
        # Evidence reliability (weighted average)
        if evidence_count == 0:
            reliability = 0.0
        else:
            # Assume non-hard evidence is SOFT
            hard_weight = hard_evidence_count * 1.0
            soft_weight = (evidence_count - hard_evidence_count) * 0.6
            reliability = (hard_weight + soft_weight) / evidence_count

        # Corroboration
        if evidence_count == 0:
            corroboration = 0.0
        elif evidence_count == 1:
            corroboration = 0.3
        elif evidence_count == 2:
            corroboration = 0.6
        else:
            corroboration = min(1.0, 0.8 + 0.05 * (evidence_count - 3))

        # Conflict
        total = evidence_count + conflict_count
        conflict_ratio = conflict_count / max(1, total)
        conflict_value = 1.0 - conflict_ratio

        # Weighted sum
        confidence = (
            0.30 * base_prior +
            0.25 * reliability +
            0.15 * corroboration +
            0.15 * conflict_value +
            0.15 * 1.0  # Freshness (assume fresh)
        )

        return max(0.0, min(1.0, confidence))
