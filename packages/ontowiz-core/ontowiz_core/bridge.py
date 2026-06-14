"""Governance bridge — artifact lifecycle transitions only via governed Deltas.

Ties ``ontowiz_spec`` artifacts to ``ontowiz_core``'s Delta model. The rule
(ADR-001 Delta model): nothing transitions by direct write; a lifecycle change is
the *effect* of an APPROVED or MERGED Delta. This is the seam that makes the
SpecOmagic lifecycle (DRAFT→…→ACTIVE) governed by Onto_Wiz Deltas.

Tier B: may import ``ontowiz_spec`` (Tier A); never imported by Tier A.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ontowiz_spec import ArtifactBase, ArtifactKind, Lifecycle

from .models import BlastRadius, Delta, DeltaStatus, DeltaType


class GovernanceError(RuntimeError):
    """Raised when a lifecycle transition is attempted without a granted Delta."""


# Target lifecycle → impact of making that change.
_LIFECYCLE_BLAST: dict[Lifecycle, BlastRadius] = {
    Lifecycle.REVIEW: BlastRadius.LOW,
    Lifecycle.VERIFIED: BlastRadius.MEDIUM,
    Lifecycle.ACTIVE: BlastRadius.HIGH,  # promotion to production = highest impact
    Lifecycle.DEPRECATED: BlastRadius.MEDIUM,
    Lifecycle.ARCHIVED: BlastRadius.LOW,
}

# Artifact kind → the Delta type that best represents changing it.
_KIND_DELTA_TYPE: dict[ArtifactKind, DeltaType] = {
    ArtifactKind.GUARDRAIL: DeltaType.PROPOSED_GUARDRAIL,
    ArtifactKind.JUDGMENT_PATTERN: DeltaType.PROPOSED_PATTERN,
    ArtifactKind.ACTION_TEMPLATE: DeltaType.PROPOSED_ACTION,
    ArtifactKind.JARGON_MAP: DeltaType.PROPOSED_SYNONYM,
}

# Delta statuses that actually grant a transition.
_GRANTED = (DeltaStatus.APPROVED, DeltaStatus.MERGED)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def propose_transition(
    artifact: ArtifactBase,
    to_state: Lifecycle,
    *,
    proposed_by: str = "system",
    reason: str = "",
    confidence: float = 0.5,
) -> Delta:
    """Create a PROPOSED Delta requesting a lifecycle change.

    Does NOT mutate the artifact — governance has not been granted yet.
    """
    return Delta(
        type=_KIND_DELTA_TYPE.get(artifact.kind, DeltaType.PROPOSED_ENTITY),
        status=DeltaStatus.PROPOSED,
        content={
            "artifact_id": artifact.id,
            "kind": artifact.kind.value,
            "from": artifact.lifecycle.value,
            "to": to_state.value,
            "reason": reason,
        },
        confidence=confidence,
        blast_radius=_LIFECYCLE_BLAST.get(to_state, BlastRadius.MEDIUM),
        owner=proposed_by,
        source_type="manual",
    )


def apply_delta(artifact: ArtifactBase, delta: Delta, *, at: str | None = None) -> ArtifactBase:
    """Apply a granted (APPROVED/MERGED) Delta's transition to ``artifact``.

    Returns a new artifact instance advanced to the target lifecycle, with the
    delta recorded in its audit trail (provenance = the approver). Raises
    ``GovernanceError`` if the delta is not granted or targets another artifact.
    """
    if delta.status not in _GRANTED:
        raise GovernanceError(
            f"Delta {delta.id} is {delta.status.value}; only APPROVED/MERGED "
            "deltas may drive a lifecycle transition"
        )
    if delta.content.get("artifact_id") != artifact.id:
        raise GovernanceError(
            f"Delta {delta.id} targets {delta.content.get('artifact_id')!r}, not {artifact.id!r}"
        )
    return artifact.transition(
        Lifecycle(delta.content["to"]),
        changed_by=delta.reviewed_by or delta.owner,
        reason=delta.content.get("reason", ""),
        delta_id=delta.id,
        at=at or _now(),
    )


def propose_artifact(
    artifact: ArtifactBase, *, proposed_by: str = "system", confidence: float = 0.5
) -> Delta:
    """Propose ADDING a new candidate artifact as a PROPOSED Delta.

    The artifact itself stays DRAFT; the Delta carries it for review. Mining and
    feedback loops use this to push candidates into governance.
    """
    return Delta(
        type=_KIND_DELTA_TYPE.get(artifact.kind, DeltaType.PROPOSED_ENTITY),
        status=DeltaStatus.PROPOSED,
        content={
            "artifact_id": artifact.id,
            "kind": artifact.kind.value,
            "op": "add",
            "artifact": artifact.model_dump(mode="json"),
        },
        confidence=confidence,
        blast_radius=BlastRadius.LOW,
        owner=proposed_by,
        source_type="mining",
    )
