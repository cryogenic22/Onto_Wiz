"""Feedback loop (Loop 5 of the 5) — usage telemetry → Deltas + EvalCases.

Consumes agent-usage events: EWMA per-artifact reliability from helpful/unhelpful
signals, turns corrections into gold EvalCases (so one correction prevents a
class of error — the 'correction reuse' metric), and pushes corrected artifacts
back into governance as PROPOSED transitions to REVIEW.

Tier B (factory).
"""

from __future__ import annotations

from dataclasses import dataclass

from ontowiz_core.bridge import propose_transition
from ontowiz_core.models import Delta
from ontowiz_spec import ArtifactBase, EvalCase, Lifecycle


@dataclass
class UsageEvent:
    artifact_id: str
    helpful: bool
    correction: str = ""  # the fix, if the answer was wrong
    query: str = ""


def update_reliability(
    prior: dict[str, float], events: list[UsageEvent], *, alpha: float = 0.3
) -> dict[str, float]:
    """EWMA per-artifact reliability from helpful/unhelpful usage."""
    rel = dict(prior)
    for e in events:
        obs = 1.0 if e.helpful else 0.0
        rel[e.artifact_id] = round(alpha * obs + (1 - alpha) * rel.get(e.artifact_id, 0.5), 3)
    return rel


def correction_to_evalcase(event: UsageEvent) -> EvalCase:
    """A user correction becomes a gold EvalCase validating the corrected artifact.

    Requires a non-empty correction — an empty one would yield a vacuous case
    that passes every answer and inflates pass-rate.
    """
    if not event.correction.strip():
        raise ValueError("correction_to_evalcase requires a non-empty correction")
    return EvalCase(
        id=f"ec-fix-{event.artifact_id}",
        name=f"correction for {event.artifact_id}",
        question=event.query or "(from correction)",
        gold_answer=event.correction,
        must_contain=[event.correction],
        validates=[event.artifact_id],
    )


def feedback_to_deltas(
    events: list[UsageEvent], artifacts_by_id: dict[str, ArtifactBase]
) -> list[Delta]:
    """Corrections on existing artifacts → PROPOSED transition to REVIEW (re-curate)."""
    deltas: list[Delta] = []
    for e in events:
        if e.correction and e.artifact_id in artifacts_by_id:
            deltas.append(
                propose_transition(
                    artifacts_by_id[e.artifact_id],
                    Lifecycle.REVIEW,
                    proposed_by="feedback",
                    reason=f"user correction: {e.correction}",
                )
            )
    return deltas
