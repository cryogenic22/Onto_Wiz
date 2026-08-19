from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import JsonValue
from test_authoring_flow import (
    _canonical,
    _decision,
    _digest,
    _evidence,
    _install_authority,
    _prepare_evidence,
    _source,
    _workspace,
    compile_questions,
    confirm_proposal,
    get_workspace_revision,
    load_actor_capability,
    load_proposal,
    load_session_state,
    propose_replacement,
    record_evidence,
    register_source,
    update_session_state,
    validate_authoring,
)

import ontowiz_authoring.authoring as authoring_module
from ontowiz_authoring.authoring import (
    ActorCapability,
    AuthoringConflictError,
    AuthoringValidationError,
    AuthorizationError,
    PrincipalGrant,
    Proposal,
    StaleProposalError,
)
from ontowiz_authoring.workspace import Workspace, WorkspaceError
from ontowiz_spec import EvidenceRef, SourceRecord


def _new_proposal(
    workspace: Workspace,
    actor: ActorCapability,
    *,
    delta_id: str,
    target_path: str = "pack/scope/decision.json",
    expected_target_digest: str | None,
    replacement: Mapping[str, JsonValue],
) -> Proposal:
    return propose_replacement(
        workspace,
        actor=actor,
        delta_id=delta_id,
        target_owner_role="brand_owner",
        allowed_confirmer_roles=("brand_owner",),
        target_path=target_path,
        expected_target_digest=expected_target_digest,
        replacement_body=replacement,
        evidence_ids=("EV-001",),
        rationale="Candidate-only governed change.",
    )


@pytest.mark.contract
def test_new_target_proposal_creates_exact_full_document(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    drafter, owner, _ = _prepare_evidence(workspace)
    target = workspace.root / "pack" / "scope" / "decision.json"
    replacement = _decision("Recommend a new evidence-qualified response.")
    proposed = _new_proposal(
        workspace,
        drafter,
        delta_id="DELTA-NEW-001",
        expected_target_digest=None,
        replacement=replacement,
    )
    assert not target.exists()

    confirmed = confirm_proposal(
        workspace,
        proposed.delta_id,
        actor=owner,
        confirmed_at=datetime(2026, 7, 25, 13, 0, tzinfo=UTC),
    )
    assert json.loads(target.read_text(encoding="utf-8")) == replacement
    assert confirmed.applied_from_digest is None
    assert validate_authoring(workspace).confirmed_proposals == 1


@pytest.mark.contract
def test_create_mode_refuses_existing_target(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    drafter, _, _ = _prepare_evidence(workspace)
    target = workspace.root / "pack" / "scope" / "decision.json"
    target.write_bytes(_canonical(_decision("Existing target.")))
    with pytest.raises(StaleProposalError, match="already exists"):
        _new_proposal(
            workspace,
            drafter,
            delta_id="DELTA-CREATE-STALE",
            expected_target_digest=None,
            replacement=_decision("Replacement."),
        )


class _InjectedExitError(RuntimeError):
    pass


@pytest.mark.contract
@pytest.mark.parametrize(
    "kill_point",
    ("after-confirm-journal", "after-confirm-file-0", "after-confirm-commit"),
)
def test_confirmation_kill_points_recover_to_one_coherent_new_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kill_point: str,
) -> None:
    workspace = _workspace(tmp_path)
    drafter, owner, _ = _prepare_evidence(workspace)
    target = workspace.root / "pack" / "scope" / "decision.json"
    original = _decision("Original decision.")
    replacement = _decision("Recovered replacement.")
    target.write_bytes(_canonical(original))
    _new_proposal(
        workspace,
        drafter,
        delta_id="DELTA-RECOVER",
        expected_target_digest=_digest(target.read_bytes()),
        replacement=replacement,
    )
    questions = compile_questions(workspace)
    update_session_state(
        workspace,
        stage="ratify",
        expected_revision=get_workspace_revision(workspace),
        last_delta_id=None,
        open_question_ids=tuple(item.id for item in questions),
        next_mission="challenge",
    )

    def inject(point: str) -> None:
        if point == kill_point:
            raise _InjectedExitError(point)

    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", inject)
    with pytest.raises(_InjectedExitError, match=kill_point):
        confirm_proposal(
            workspace,
            "DELTA-RECOVER",
            actor=owner,
            confirmed_at=datetime(2026, 7, 25, 13, 0, tzinfo=UTC),
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)

    recovered = load_proposal(workspace, "DELTA-RECOVER")
    session = load_session_state(workspace)
    assert recovered.status == "confirmed"
    assert json.loads(target.read_text(encoding="utf-8")) == replacement
    assert session.last_delta_id == "DELTA-RECOVER"
    assert session.open_question_ids == ()
    assert not list((workspace.root / "locks" / "transactions").glob("*"))


@pytest.mark.adversarial
def test_proposal_is_bound_to_exact_workspace_and_immutable_proposer(
    tmp_path: Path,
) -> None:
    workspace_a = _workspace(tmp_path, name="a", workspace_id="workspace-a")
    drafter_a, _, _ = _prepare_evidence(workspace_a)
    _new_proposal(
        workspace_a,
        drafter_a,
        delta_id="DELTA-BOUND",
        expected_target_digest=None,
        replacement=_decision("Workspace A decision."),
    )

    workspace_b = _workspace(tmp_path, name="b", workspace_id="workspace-b")
    _install_authority(
        workspace_b,
        grants=(
            PrincipalGrant(
                principal_id="draft-agent",
                roles=("steward",),
                client_boundary="client-a",
            ),
        ),
    )
    destination = workspace_b.root / "authoring" / "proposals" / "DELTA-BOUND.yaml"
    shutil.copyfile(
        workspace_a.root / "authoring" / "proposals" / "DELTA-BOUND.yaml",
        destination,
    )
    with pytest.raises(AuthoringValidationError, match="another workspace"):
        load_proposal(workspace_b, "DELTA-BOUND")

    spoofed = drafter_a.model_copy(update={"principal_id": "other-agent"})
    with pytest.raises(AuthorizationError, match="proof-of-possession"):
        _new_proposal(
            workspace_a,
            spoofed,
            delta_id="DELTA-BOUND",
            expected_target_digest=None,
            replacement=_decision("Workspace A decision."),
        )


@pytest.mark.adversarial
def test_role_spoof_and_wrong_target_owner_are_rejected(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    drafter, owner, approver = _prepare_evidence(workspace)
    _new_proposal(
        workspace,
        drafter,
        delta_id="DELTA-AUTH",
        expected_target_digest=None,
        replacement=_decision("Governed decision."),
    )
    spoofed = approver.model_copy(update={"roles": ("brand_owner",)})
    with pytest.raises(AuthorizationError, match="proof-of-possession"):
        confirm_proposal(
            workspace,
            "DELTA-AUTH",
            actor=spoofed,
            confirmed_at=datetime(2026, 7, 25, tzinfo=UTC),
        )
    with pytest.raises(AuthorizationError, match="target owner"):
        confirm_proposal(
            workspace,
            "DELTA-AUTH",
            actor=approver,
            confirmed_at=datetime(2026, 7, 25, tzinfo=UTC),
        )
    assert not (workspace.root / "pack" / "scope" / "decision.json").exists()
    assert owner.principal_id == "brand-1"


@pytest.mark.adversarial
def test_confirmation_rechecks_freshness_and_retention(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    drafter, owner, _ = _configure_rights_workspace(
        workspace,
        _source(fresh_until="2026-07-25", retention_until="2026-07-25"),
        _evidence(valid_as_of="2026-07-25"),
    )
    _new_proposal(
        workspace,
        drafter,
        delta_id="DELTA-EXPIRED",
        expected_target_digest=None,
        replacement=_decision("Expired evidence must not apply."),
    )
    with pytest.raises(AuthoringValidationError, match="expired"):
        confirm_proposal(
            workspace,
            "DELTA-EXPIRED",
            actor=owner,
            confirmed_at=datetime(2026, 7, 26, tzinfo=UTC),
        )


def _configure_rights_workspace(
    workspace: Workspace,
    source: SourceRecord,
    evidence: EvidenceRef,
) -> tuple[ActorCapability, ActorCapability, ActorCapability]:
    _install_authority(
        workspace,
        grants=(
            PrincipalGrant(
                principal_id="approver-1",
                roles=("approver",),
                client_boundary="client-a",
            ),
            PrincipalGrant(
                principal_id="brand-1",
                roles=("brand_owner",),
                client_boundary="client-a",
            ),
            PrincipalGrant(
                principal_id="draft-agent",
                roles=("steward",),
                client_boundary="client-a",
            ),
        ),
    )
    actors = (
        load_actor_capability(workspace, "draft-agent"),
        load_actor_capability(workspace, "brand-1"),
        load_actor_capability(workspace, "approver-1"),
    )
    register_source(workspace, source)
    record_evidence(workspace, evidence)
    return actors


@pytest.mark.adversarial
def test_local_source_byte_drift_is_rejected_at_confirmation(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    _install_authority(
        workspace,
        grants=(
            PrincipalGrant(
                principal_id="brand-1",
                roles=("brand_owner",),
                client_boundary="client-a",
            ),
            PrincipalGrant(
                principal_id="draft-agent",
                roles=("steward",),
                client_boundary="client-a",
            ),
        ),
    )
    drafter = load_actor_capability(workspace, "draft-agent")
    owner = load_actor_capability(workspace, "brand-1")
    material = workspace.root / "sources" / "inbox" / "source.bin"
    material.write_bytes(b"governed bytes")
    checksum = _digest(material.read_bytes())
    source = _source(checksum=checksum, raw_transfer_allowed=True)
    evidence = _evidence(source_checksum=checksum)
    register_source(workspace, source, material_path="sources/inbox/source.bin")
    record_evidence(workspace, evidence)
    _new_proposal(
        workspace,
        drafter,
        delta_id="DELTA-BYTES",
        expected_target_digest=None,
        replacement=_decision("Byte-bound decision."),
    )
    material.write_bytes(b"drifted bytes")
    with pytest.raises(AuthoringValidationError, match="byte drift"):
        confirm_proposal(
            workspace,
            "DELTA-BYTES",
            actor=owner,
            confirmed_at=datetime(2026, 7, 25, tzinfo=UTC),
        )


@pytest.mark.adversarial
def test_quote_drift_and_forbidden_personal_data_fail_closed(tmp_path: Path) -> None:
    quoted_workspace = _workspace(tmp_path, name="quoted", workspace_id="quoted")
    _install_authority(
        quoted_workspace,
        grants=(
            PrincipalGrant(
                principal_id="draft-agent",
                roles=("steward",),
                client_boundary="client-a",
            ),
        ),
    )
    register_source(quoted_workspace, _source())
    quote = "governed quote"
    record_evidence(
        quoted_workspace,
        _evidence(
            quoted=True,
            quote_digest=authoring_module._quote_digest(quote),
        ),
        quote_payload=quote,
    )
    evidence_path = quoted_workspace.root / "sources" / "extracted" / "SRC-001.json"
    evidence_doc = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence_doc["quotes"][0]["payload"] = "changed quote"
    evidence_path.write_bytes(_canonical(evidence_doc))
    with pytest.raises(WorkspaceError, match="invalid controlled file"):
        compile_questions(quoted_workspace)

    pii_workspace = _workspace(tmp_path, name="pii", workspace_id="pii")
    _install_authority(
        pii_workspace,
        grants=(
            PrincipalGrant(
                principal_id="draft-agent",
                roles=("steward",),
                client_boundary="client-a",
            ),
        ),
    )
    drafter = load_actor_capability(pii_workspace, "draft-agent")
    register_source(
        pii_workspace,
        _source(
            contains_personal_data=True,
            personal_data_transfer_allowed=False,
            consent_basis="synthetic-test-consent",
        ),
    )
    record_evidence(pii_workspace, _evidence())
    with pytest.raises(AuthoringValidationError, match="personal-data"):
        _new_proposal(
            pii_workspace,
            drafter,
            delta_id="DELTA-PII",
            expected_target_digest=None,
            replacement=_decision("PII-forbidden decision."),
        )


@pytest.mark.adversarial
def test_client_boundary_mismatch_fails_closed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    _install_authority(
        workspace,
        grants=(
            PrincipalGrant(
                principal_id="draft-agent",
                roles=("steward",),
                client_boundary="client-b",
            ),
        ),
    )
    drafter = load_actor_capability(workspace, "draft-agent")
    register_source(workspace, _source(client_boundary="client-a"))
    record_evidence(workspace, _evidence())
    with pytest.raises(AuthoringValidationError, match="client boundary"):
        _new_proposal(
            workspace,
            drafter,
            delta_id="DELTA-BOUNDARY",
            expected_target_digest=None,
            replacement=_decision("Cross-boundary decision."),
        )


@pytest.mark.adversarial
def test_session_rejects_dangling_cross_workspace_and_future_revision(
    tmp_path: Path,
) -> None:
    workspace_a = _workspace(tmp_path, name="session-a", workspace_id="session-a")
    state = update_session_state(
        workspace_a,
        stage="discover",
        expected_revision=get_workspace_revision(workspace_a),
        last_delta_id=None,
        open_question_ids=(),
        next_mission="scenario",
    )
    with pytest.raises(WorkspaceError):
        update_session_state(
            workspace_a,
            stage="discover",
            expected_revision=get_workspace_revision(workspace_a),
            last_delta_id="DELTA-MISSING",
            open_question_ids=(),
            next_mission="scenario",
        )

    session_path_a = workspace_a.root / "authoring" / "sessions" / "current" / "session.yaml"
    tampered = state.model_dump(mode="json")
    tampered["revision"] = get_workspace_revision(workspace_a) + 10
    session_path_a.write_bytes(_canonical(tampered))
    with pytest.raises(AuthoringValidationError, match="ahead"):
        load_session_state(workspace_a)

    tampered["revision"] = get_workspace_revision(workspace_a)
    session_path_a.write_bytes(_canonical(tampered))
    workspace_b = _workspace(tmp_path, name="session-b", workspace_id="session-b")
    session_path_b = workspace_b.root / "authoring" / "sessions" / "current" / "session.yaml"
    session_path_b.parent.mkdir(parents=True)
    shutil.copyfile(session_path_a, session_path_b)
    with pytest.raises(AuthoringValidationError, match="another workspace"):
        load_session_state(workspace_b)


@pytest.mark.adversarial
def test_question_compiler_rejects_malformed_duplicate_unbounded_and_no_owner(
    tmp_path: Path,
) -> None:
    malformed = _workspace(tmp_path, name="malformed", workspace_id="malformed")
    (malformed.root / "pack" / "scope" / "bad.json").write_bytes(
        _canonical({"id": "BAD", "decision": "missing required fields"})
    )
    with pytest.raises(AuthoringValidationError, match="invalid canonical"):
        compile_questions(malformed)

    duplicate = _workspace(tmp_path, name="duplicate", workspace_id="duplicate")
    for name in ("a", "b"):
        (duplicate.root / "pack" / "scope" / f"{name}.json").write_bytes(
            _canonical(_decision(f"Decision {name}."))
        )
    with pytest.raises(AuthoringValidationError, match="duplicate pack document id"):
        compile_questions(duplicate)

    unbounded = _workspace(tmp_path, name="unbounded", workspace_id="unbounded")
    for index in range(257):
        (unbounded.root / "pack" / "scope" / f"d{index:03}.json").write_bytes(
            _canonical(_decision("Bounded.", decision_id=f"DEC-{index:03}"))
        )
    with pytest.raises(AuthoringValidationError, match="count exceeds"):
        compile_questions(unbounded)

    no_owner = _workspace(tmp_path, name="no-owner", workspace_id="no-owner")
    missing_owner = _decision("Owner is required.")
    missing_owner.pop("owner_role")
    (no_owner.root / "pack" / "scope" / "decision.json").write_bytes(_canonical(missing_owner))
    with pytest.raises(AuthoringValidationError, match="invalid canonical"):
        compile_questions(no_owner)

    no_fallback = _workspace(
        tmp_path,
        name="no-fallback",
        workspace_id="no-fallback",
        owner_roles=("approver",),
    )
    blocked = compile_questions(no_fallback)
    assert blocked
    assert all(item.blocking and item.owner_role is None for item in blocked)


@pytest.mark.adversarial
def test_same_delta_drift_and_stale_revision_conflict(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    drafter, _, _ = _prepare_evidence(workspace)
    revision = get_workspace_revision(workspace)
    proposal = _new_proposal(
        workspace,
        drafter,
        delta_id="DELTA-SAME",
        expected_target_digest=None,
        replacement=_decision("First body."),
    )
    assert (
        propose_replacement(
            workspace,
            actor=drafter,
            delta_id=proposal.delta_id,
            target_owner_role=proposal.target_owner_role,
            allowed_confirmer_roles=proposal.allowed_confirmer_roles,
            target_path=proposal.target_path,
            expected_target_digest=proposal.expected_target_digest,
            replacement_body=proposal.replacement_body,
            evidence_ids=proposal.evidence_ids,
            rationale=proposal.rationale,
        )
        == proposal
    )
    with pytest.raises(AuthoringConflictError, match="proposal id"):
        _new_proposal(
            workspace,
            drafter,
            delta_id="DELTA-SAME",
            expected_target_digest=None,
            replacement=_decision("Different body."),
        )
    with pytest.raises(AuthoringConflictError, match="stale workspace revision"):
        update_session_state(
            workspace,
            stage="discover",
            last_delta_id=None,
            open_question_ids=(),
            next_mission="scenario",
            expected_revision=revision,
        )
