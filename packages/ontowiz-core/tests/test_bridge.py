"""F1 #4 — the Delta bridge: artifact lifecycle transitions only via governed Deltas.

Red-first: ontowiz_core.bridge does not exist yet. Green when the bridge enforces
"no transition without an APPROVED/MERGED Delta".
"""

from __future__ import annotations

import pytest
from ontowiz_core import BlastRadius, DeltaStatus, DeltaType
from ontowiz_core.bridge import GovernanceError, apply_delta, propose_transition
from ontowiz_spec import ArtifactKind, EvalCase, Guardrail, Lifecycle


def _draft() -> EvalCase:
    return EvalCase(id="ec1", name="brand-x", question="why share loss?")


def test_propose_creates_proposed_delta_without_mutating():
    art = _draft()
    delta = propose_transition(art, Lifecycle.ACTIVE, proposed_by="sme:kp", reason="forge round 3")
    assert delta.status == DeltaStatus.PROPOSED
    assert delta.content["artifact_id"] == "ec1"
    assert delta.content["to"] == "active"
    # proposing does NOT change the artifact — governance is not yet granted
    assert art.lifecycle == Lifecycle.DRAFT


def test_unapproved_delta_cannot_drive_a_transition():
    art = _draft()
    delta = propose_transition(art, Lifecycle.ACTIVE)
    with pytest.raises(GovernanceError):
        apply_delta(art, delta)  # still PROPOSED
    assert art.lifecycle == Lifecycle.DRAFT


def test_approved_delta_drives_transition_with_audit_provenance():
    art = _draft()
    delta = propose_transition(art, Lifecycle.ACTIVE, proposed_by="sme:kp", reason="forge round 3")
    delta.approve("curator:lead")
    active = apply_delta(art, delta, at="2026-06-10T00:00:00Z")
    assert active.lifecycle == Lifecycle.ACTIVE
    entry = active.lifecycle_history[-1]
    assert entry.delta_id == delta.id
    assert entry.to_state == Lifecycle.ACTIVE
    assert entry.changed_by == "curator:lead"   # provenance = the approver
    assert entry.reason == "forge round 3"
    assert active.approved_at == "2026-06-10T00:00:00Z"
    # immutability: the input artifact is untouched
    assert art.lifecycle == Lifecycle.DRAFT


def test_merged_delta_also_drives_transition():
    art = _draft()
    delta = propose_transition(art, Lifecycle.VERIFIED)
    delta.status = DeltaStatus.MERGED
    verified = apply_delta(art, delta)
    assert verified.lifecycle == Lifecycle.VERIFIED


def test_rejected_delta_is_refused():
    art = _draft()
    delta = propose_transition(art, Lifecycle.ACTIVE)
    delta.reject("curator:lead", "insufficient evidence")
    with pytest.raises(GovernanceError):
        apply_delta(art, delta)


def test_delta_must_target_the_same_artifact():
    art = _draft()
    other = EvalCase(id="ec2", name="other", question="q")
    delta = propose_transition(art, Lifecycle.ACTIVE)
    delta.approve("c")
    with pytest.raises(GovernanceError):
        apply_delta(other, delta)


def test_blast_radius_scales_with_target_lifecycle():
    art = _draft()
    assert propose_transition(art, Lifecycle.ACTIVE).blast_radius == BlastRadius.HIGH
    assert propose_transition(art, Lifecycle.ARCHIVED).blast_radius == BlastRadius.LOW


def test_delta_type_maps_from_artifact_kind():
    g = Guardrail(id="g1", name="no-promo")
    assert g.kind == ArtifactKind.GUARDRAIL
    assert propose_transition(g, Lifecycle.ACTIVE).type == DeltaType.PROPOSED_GUARDRAIL
    # generic artifact falls back to entity
    assert propose_transition(_draft(), Lifecycle.ACTIVE).type == DeltaType.PROPOSED_ENTITY
