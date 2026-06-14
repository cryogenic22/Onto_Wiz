"""ForgeRating + multiplayer consensus (Loop 5 / UX-4).

ForgeRating: a calibrated judgement score (Elo-like, baseline 1000) computed from
five signals — correctness, novelty, impact, eval value, and dissent value
(weighted highest). It rewards improving the firm's brain, never volume or speed.

Anti-gaming / decay are modelled as a per-contribution ``weight`` multiplier the
caller supplies: a weight of 0 fully excludes a contribution (e.g. a flagged
duplicate/rapid click), and a fractional weight down-weights stale ones. The
weight-*derivation* policy (consensus clustering, time decay) is intentionally
out of scope here — this module consumes the weight, it does not compute it.

Multiplayer consensus: settle disagreeing SME answers into a consensus, the
dissenting positions, and a consensus-weighted confidence — then manufacture an
ExceptionRule that captures the situated judgement for governance.

Tier B (factory): may import ontowiz_spec.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ontowiz_spec import ExceptionRule

_BASELINE = 1000.0
_SPREAD = 1000.0  # a perfect contribution adds up to this many rating points

# Signal weights — dissent is the highest-status signal (provably contrarian and
# right is what most improves the pack); volume and speed are deliberately absent.
SIGNAL_WEIGHTS: dict[str, float] = {
    "correctness": 1.0,
    "novelty": 1.0,
    "impact": 1.2,
    "eval_value": 1.3,
    "dissent_value": 1.6,
}


@dataclass
class Contribution:
    """One scored SME contribution. Signals are each in [0, 1]."""

    sme_id: str
    artifact_id: str
    correctness: float = 0.0
    novelty: float = 0.0
    impact: float = 0.0
    eval_value: float = 0.0
    dissent_value: float = 0.0
    weight: float = 1.0  # decay / anti-gaming multiplier; 0 = ignored


@dataclass
class SMEAnswer:
    sme_id: str
    answer: str
    confidence: float


@dataclass
class ConsensusResult:
    consensus: str
    agreement: float  # fraction of SMEs choosing the consensus answer
    dissent: list[str]  # distinct minority answers
    confidence: float  # consensus-weighted, [0, 1]


def _clamp(x: float) -> float:
    return min(1.0, max(0.0, x))


def _contribution_score(c: Contribution) -> float:
    """Weighted mean of the five signals, in [0, 1].

    Each signal is clamped to [0, 1] first, so an un-normalised input (e.g. a raw
    usage count fed as ``impact``) cannot push the rating outside [1000, 2000].
    """
    total = sum(SIGNAL_WEIGHTS.values())
    earned = (
        _clamp(c.correctness) * SIGNAL_WEIGHTS["correctness"]
        + _clamp(c.novelty) * SIGNAL_WEIGHTS["novelty"]
        + _clamp(c.impact) * SIGNAL_WEIGHTS["impact"]
        + _clamp(c.eval_value) * SIGNAL_WEIGHTS["eval_value"]
        + _clamp(c.dissent_value) * SIGNAL_WEIGHTS["dissent_value"]
    )
    return earned / total


def forge_rating(contributions: list[Contribution]) -> float:
    """Calibrated judgement rating from contributions (Elo-like, baseline 1000).

    Weighted by each contribution's ``weight`` so stale/gamed clicks (weight 0)
    contribute nothing. Empty history returns the baseline.
    """
    weighted = [(c, c.weight) for c in contributions if c.weight > 0]
    if not weighted:
        return _BASELINE
    total_w = sum(w for _, w in weighted)
    mean_score = sum(_contribution_score(c) * w for c, w in weighted) / total_w
    return round(_BASELINE + _SPREAD * mean_score, 1)


def resolve_consensus(answers: list[SMEAnswer]) -> ConsensusResult:
    """Settle disagreeing SME answers into consensus + dissent + confidence."""
    if not answers:
        return ConsensusResult(consensus="", agreement=0.0, dissent=[], confidence=0.0)
    tally = Counter(a.answer for a in answers)
    consensus, top_n = tally.most_common(1)[0]
    agreement = top_n / len(answers)
    dissent = [ans for ans in tally if ans != consensus]
    agreeing_conf = [a.confidence for a in answers if a.answer == consensus]
    # consensus-weighted: average confidence of the agreeing SMEs, scaled by how
    # strongly they agree, so a split room yields a lower, honest confidence.
    confidence = round((sum(agreeing_conf) / len(agreeing_conf)) * agreement, 3)
    return ConsensusResult(
        consensus=consensus, agreement=agreement, dissent=dissent, confidence=confidence
    )


def consensus_to_exception_rule(
    result: ConsensusResult,
    *,
    rule_id: str,
    name: str,
    applies_to: str,
    condition: str = "",
) -> ExceptionRule:
    """Capture a settled consensus as a governable ExceptionRule (situated judgement)."""
    return ExceptionRule(
        id=rule_id,
        name=name,
        applies_to_artifact_id=applies_to,
        condition=condition,
        instead=result.consensus,
        reason="multiplayer consensus" + (f"; dissent: {', '.join(result.dissent)}" if result.dissent else ""),
        confidence=result.confidence,
    )
