"""Mission framework (Loop 5 / UX-1) — the Domain Forge submit contract.

Generalises the steward's flat signals into a *mission system*: a steward-ranked
daily feed (the 5-minute loop) plus the spec's non-negotiable rule —

    a mission that doesn't produce an artifact *and* an eval doesn't ship.

``submit_mission`` enforces that contract: every accepted submission yields a
governed PROPOSED Delta, a gold EvalCase, and an explicit SME confidence. No
direct writes; nothing reaches an agent until the Delta is governed.

Tier B (factory): may import ontowiz_core (bridge) + ontowiz_spec. The Forge is
internal/client-licensed IP and is deliberately NOT exposed on the Tier-A read
API (which serves only compiled packs).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ontowiz_core.bridge import propose_artifact, propose_transition
from ontowiz_core.models import Delta
from ontowiz_spec import ArtifactBase, EvalCase, Lifecycle

from .steward import collect_signals, signals_to_missions


class MissionContractError(ValueError):
    """Raised when a submission violates the delta+eval+confidence contract."""


def _slug(text: str) -> str:
    """Reduce a free string to a safe id fragment (no collisions / unsafe chars)."""
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower() or "x"


@dataclass
class Mission:
    """A steward-ranked unit of curation work surfaced to an SME."""

    id: str
    type: str  # the Forge mission type (validate, name_the_caveat, ...)
    artifact_id: str
    prompt: str
    impact: float  # [0, 1] — higher = more worth an SME's time


@dataclass
class MissionSubmission:
    """What an SME hands back when completing a mission."""

    mission_type: str
    artifact: ArtifactBase
    confidence: float
    gold_answer: str = ""  # eval material for a new/validated artifact
    correction: str = ""  # eval material when fixing an existing artifact
    question: str = ""
    submitted_by: str = "sme"


@dataclass
class MissionResult:
    """The three required outputs of a shipped mission."""

    delta: Delta
    eval_case: EvalCase
    confidence: float


def daily_missions(
    artifacts: list[ArtifactBase], *, eval_targets: set[str] | None = None, limit: int = 5
) -> list[Mission]:
    """The 5-minute loop: steward-ranked missions over a pack (highest impact first)."""
    signals = collect_signals(artifacts, eval_targets=eval_targets)
    missions = signals_to_missions(signals, limit=limit)
    return [
        Mission(
            id=f"mission-{i}",
            type=ms.type,
            artifact_id=ms.artifact_id,
            prompt=ms.prompt,
            impact=sig.impact,
        )
        for i, (sig, ms) in enumerate(zip(signals, missions, strict=False), start=1)
    ]


def _enforce_contract(
    submission: MissionSubmission, existing: ArtifactBase | None
) -> str:
    """Enforce the Forge contract; return the eval material or raise."""
    if not 0.0 <= submission.confidence <= 1.0:
        raise MissionContractError(f"confidence {submission.confidence} must be in [0, 1]")
    eval_material = submission.gold_answer or submission.correction
    if not eval_material:
        raise MissionContractError("a mission must produce an eval (gold answer or correction)")
    if existing is not None and existing.id != submission.artifact.id:
        raise MissionContractError(
            f"submission artifact {submission.artifact.id!r} does not match the "
            f"edited artifact {existing.id!r}"
        )
    return eval_material


def submit_mission(
    submission: MissionSubmission, *, existing: ArtifactBase | None = None
) -> MissionResult:
    """Validate and govern a mission submission.

    Enforces the Forge contract (valid confidence AND eval material, else it does
    not ship), then returns a PROPOSED Delta, a gold EvalCase, and the confidence.
    ``existing`` set => the SME corrected a served artifact (Delta → REVIEW);
    otherwise a new candidate is proposed for addition.
    """
    eval_material = _enforce_contract(submission, existing)
    artifact = submission.artifact
    # Discriminate the eval id by submitter so two SMEs (or re-submissions) on the
    # same artifact mint distinct gold cases instead of silently overwriting.
    eval_case = EvalCase(
        id=f"ec-mission-{_slug(artifact.id)}-{_slug(submission.submitted_by)}",
        name=f"mission eval for {artifact.id}",
        question=submission.question or "(from mission)",
        gold_answer=eval_material,
        must_contain=[eval_material],
        validates=[artifact.id],
    )

    if existing is not None:
        delta = propose_transition(
            existing,
            Lifecycle.REVIEW,
            proposed_by=submission.submitted_by,
            reason=submission.correction or "mission re-curation",
            confidence=submission.confidence,
        )
    else:
        candidate = artifact.model_copy(update={"confidence": submission.confidence})
        delta = propose_artifact(
            candidate, proposed_by=submission.submitted_by, confidence=submission.confidence
        )

    return MissionResult(delta=delta, eval_case=eval_case, confidence=submission.confidence)
