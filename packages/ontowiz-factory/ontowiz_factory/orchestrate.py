"""Factory orchestrator — the weld that makes the loops one pipeline.

The loops (mining, steward, eval, feedback) each produce governed *proposals*;
this module is the missing seam that carries an approved proposal all the way to
a compiled, servable pack:

    raw text → mine (PROPOSED add-Deltas) → govern (approve) → ACTIVE artifacts
             → compile_pack → (servable Domain Pack)

The approval call IS the governance decision point — a human/steward approves a
candidate; nothing reaches ACTIVE without that approval being recorded as a
granted Delta (the bridge enforces it).

Tier B (factory).
"""

from __future__ import annotations

from ontowiz_core.bridge import apply_delta, propose_transition
from ontowiz_core.models import Delta, DeltaStatus
from ontowiz_spec import ARTIFACT_MODELS, ArtifactBase, ArtifactKind, Lifecycle

from .compiler import CompiledPack, compile_pack
from .mining import mine_to_deltas


def _artifact_from_delta(delta: Delta) -> ArtifactBase:
    data = delta.content["artifact"]
    model = ARTIFACT_MODELS[ArtifactKind(data["kind"])]
    return model.model_validate(data)


def promote_candidate(delta: Delta, *, approved_by: str = "steward") -> ArtifactBase:
    """Govern a PROPOSED add-Delta into an ACTIVE artifact.

    Records the approval on the proposal, then drives the promotion to ACTIVE
    through a granted transition Delta (so the artifact carries a governing
    ``delta_id``). Raises if the Delta is not an add-proposal.
    """
    if delta.content.get("op") != "add":
        raise ValueError(f"promote_candidate expects an add-delta, got {delta.content.get('op')!r}")
    artifact = _artifact_from_delta(delta)
    delta.approve(approved_by)  # the governance decision: PROPOSED → APPROVED
    transition = propose_transition(
        artifact, Lifecycle.ACTIVE, proposed_by=approved_by,
        reason=f"approved mined candidate {delta.id}",
    )
    transition.status = DeltaStatus.APPROVED
    transition.reviewed_by = approved_by
    return apply_delta(artifact, transition)


def evolve_pack(
    base: list[ArtifactBase],
    additions: list[Delta],
    *,
    name: str,
    version: str,
    domain: str = "commercial",
    approved_by: str = "steward",
    description: str = "evolved from usage-driven missions",
) -> CompiledPack:
    """Carry approved add-proposals into the *next* version of an existing pack.

    The closing weld of the loop: usage surfaces a gap → a Forge mission proposes
    a new artifact (a PROPOSED add-Delta) → here each is governed to ACTIVE and
    joined with the pack's current artifacts, and the union is recompiled at the
    new version. ``base`` is a loaded pack's ``artifacts``; ``additions`` are the
    ``MissionResult.delta`` add-proposals an approver accepted.
    """
    promoted = [promote_candidate(d, approved_by=approved_by) for d in additions]
    return compile_pack(
        [*base, *promoted],
        name=name,
        version=version,
        domain=domain,
        description=description,
    )


def mine_govern_compile(
    text: str,
    *,
    name: str,
    version: str,
    source_id: str = "",
    approved_by: str = "steward",
    domain: str = "commercial",
) -> CompiledPack:
    """End-to-end: raw text → mined proposals → governed ACTIVE artifacts → pack.

    Proves the factory composes: every candidate that an approver accepts becomes
    a governed, ACTIVE artifact and is compiled into a servable pack.
    """
    deltas = mine_to_deltas(text, source_id=source_id, domain=domain)
    active = [promote_candidate(d, approved_by=approved_by) for d in deltas]
    return compile_pack(
        active, name=name, version=version, domain=domain,
        description="mined → governed → compiled",
    )
