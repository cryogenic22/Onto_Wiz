"""Knowledge Steward loop (Loop 2 of the 5) — signals → curation actions/missions.

Ported in spirit from market_zero's data_steward: collect ranked signals over a
pack's artifacts (low confidence, missing evals), turn the weak/high-impact ones
into Forge missions, and score overall pack quality. This is what makes the game
a targeted curation accelerator instead of a blank-page interview.

Tier B (factory).
"""

from __future__ import annotations

from dataclasses import dataclass

from ontowiz_spec import ArtifactBase, ArtifactKind, Lifecycle

_LOW_CONF = 0.5
_TESTABLE_KINDS = {
    ArtifactKind.DECISION_HEURISTIC,
    ArtifactKind.JUDGMENT_PATTERN,
    ArtifactKind.DATA_QUIRK,
    ArtifactKind.METRIC_DEFINITION,
}


@dataclass
class StewardSignal:
    kind: str  # low_confidence | missing_eval
    artifact_id: str
    reason: str
    impact: float  # [0, 1] — higher = more worth an SME's time


@dataclass
class Mission:
    type: str  # the Forge mission type
    artifact_id: str
    prompt: str


_MISSION_FOR = {
    "low_confidence": ("validate", "Confirm or correct this artifact — is it right?"),
    "missing_eval": ("name_the_caveat", "Write a gold answer that proves this artifact changes behaviour."),
}


def collect_signals(
    artifacts: list[ArtifactBase], *, eval_targets: set[str] | None = None
) -> list[StewardSignal]:
    """Rank curation signals over a set of artifacts (highest impact first)."""
    eval_targets = eval_targets or set()
    signals: list[StewardSignal] = []
    for a in artifacts:
        if a.confidence < _LOW_CONF:
            signals.append(
                StewardSignal("low_confidence", a.id, f"confidence {a.confidence:.2f} < {_LOW_CONF}", round(1 - a.confidence, 3))
            )
        if a.kind in _TESTABLE_KINDS and a.id not in eval_targets:
            signals.append(StewardSignal("missing_eval", a.id, "no EvalCase validates this artifact", 0.6))
    return sorted(signals, key=lambda s: s.impact, reverse=True)


def signals_to_missions(signals: list[StewardSignal], *, limit: int = 5) -> list[Mission]:
    """Turn the top signals into Forge missions."""
    out: list[Mission] = []
    for s in signals[:limit]:
        mtype, prompt = _MISSION_FOR.get(s.kind, ("validate", "Review this artifact."))
        out.append(Mission(type=mtype, artifact_id=s.artifact_id, prompt=prompt))
    return out


def pack_quality_score(artifacts: list[ArtifactBase], *, eval_targets: set[str] | None = None) -> float:
    """Weighted blend of active-fraction, eval-coverage and avg-confidence, [0, 1].

    A *weighted mean* (not a product), so one weak dimension does not annihilate
    the score — a large in-progress pack reads as "partly done", not ~0. A pack
    with no testable artifacts scores 0 on coverage (it cannot be proven), rather
    than getting a free 1.0.
    """
    if not artifacts:
        return 0.0
    eval_targets = eval_targets or set()
    testable = [a for a in artifacts if a.kind in _TESTABLE_KINDS]
    eval_cov = (sum(1 for a in testable if a.id in eval_targets) / len(testable)) if testable else 0.0
    avg_conf = sum(a.confidence for a in artifacts) / len(artifacts)
    active_frac = sum(1 for a in artifacts if a.lifecycle == Lifecycle.ACTIVE) / len(artifacts)
    return round(0.4 * active_frac + 0.3 * eval_cov + 0.3 * avg_conf, 3)
