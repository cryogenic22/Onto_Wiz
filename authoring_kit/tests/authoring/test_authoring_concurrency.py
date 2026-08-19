from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier

import pytest
from test_authoring_flow import (
    _canonical,
    _decision,
    _digest,
    _prepare_evidence,
    _source,
    _workspace,
    confirm_proposal,
    get_workspace_revision,
    propose_replacement,
    register_source,
    update_session_state,
)

import ontowiz_authoring.authoring as authoring_module
from ontowiz_authoring.authoring import AuthoringConflictError, StaleProposalError


@pytest.mark.contract
def test_simultaneous_confirmations_yield_one_commit_and_one_stale_refusal(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    drafter, owner, _ = _prepare_evidence(workspace)
    target = workspace.root / "pack" / "scope" / "decision.json"
    target.write_bytes(_canonical(_decision("Original decision.")))
    original_digest = _digest(target.read_bytes())

    replacements = {
        "DELTA-RACE-A": _decision("Candidate decision A."),
        "DELTA-RACE-B": _decision("Candidate decision B."),
    }
    for delta_id, replacement in replacements.items():
        propose_replacement(
            workspace,
            actor=drafter,
            delta_id=delta_id,
            target_owner_role="brand_owner",
            allowed_confirmer_roles=("brand_owner",),
            target_path="pack/scope/decision.json",
            expected_target_digest=original_digest,
            replacement_body=replacement,
            evidence_ids=("EV-001",),
            rationale=f"Race test for {delta_id}.",
        )

    barrier = Barrier(2)

    def confirm(delta_id: str) -> str:
        barrier.wait()
        try:
            confirm_proposal(
                workspace.root,
                delta_id,
                actor=owner,
                confirmed_at=datetime(2026, 7, 25, 13, 0, tzinfo=UTC),
            )
            return "confirmed"
        except (StaleProposalError, AuthoringConflictError):
            return "refused"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(confirm, sorted(replacements)))

    assert sorted(outcomes) == ["confirmed", "refused"]
    assert json.loads(target.read_text(encoding="utf-8")) in replacements.values()
    assert not (workspace.root / "locks" / "authoring.lock").exists()


@pytest.mark.contract
def test_same_id_concurrent_registration_never_loses_the_winner(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    barrier = Barrier(2)
    candidates = (_source(title="Version A"), _source(title="Version B"))

    def register(index: int) -> str:
        barrier.wait()
        try:
            return register_source(workspace.root, candidates[index]).title
        except AuthoringConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(register, (0, 1)))

    assert results.count("conflict") == 1
    winner = next(result for result in results if result != "conflict")
    register_path = workspace.root / "sources" / "source-register.yaml"
    persisted = json.loads(register_path.read_text(encoding="utf-8"))
    assert persisted["sources"][0]["title"] == winner


@pytest.mark.contract
def test_revision_cas_rejects_lost_session_update(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    revision = get_workspace_revision(workspace)
    first = update_session_state(
        workspace,
        stage="discover",
        last_delta_id=None,
        open_question_ids=(),
        next_mission="scenario",
        expected_revision=revision,
    )
    assert first.revision == revision + 1
    with pytest.raises(AuthoringConflictError, match="stale workspace revision"):
        update_session_state(
            workspace,
            stage="challenge",
            last_delta_id=None,
            open_question_ids=(),
            next_mission="ratify",
            expected_revision=revision,
        )


@pytest.mark.contract
def test_last_moment_target_drift_is_rechecked_before_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    drafter, owner, _ = _prepare_evidence(workspace)
    target = workspace.root / "pack" / "scope" / "decision.json"
    target.write_bytes(_canonical(_decision("Original decision.")))
    propose_replacement(
        workspace,
        actor=drafter,
        delta_id="DELTA-TOCTOU",
        target_owner_role="brand_owner",
        allowed_confirmer_roles=("brand_owner",),
        target_path="pack/scope/decision.json",
        expected_target_digest=_digest(target.read_bytes()),
        replacement_body=_decision("Replacement decision."),
        evidence_ids=("EV-001",),
        rationale="Exercise the final target precondition.",
    )

    def inject(point: str) -> None:
        if point == "before-target-replace":
            target.write_bytes(_canonical(_decision("External last-moment edit.")))

    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", inject)
    with pytest.raises(StaleProposalError, match="stale"):
        confirm_proposal(
            workspace,
            "DELTA-TOCTOU",
            actor=owner,
            confirmed_at=datetime(2026, 7, 25, tzinfo=UTC),
        )
    assert json.loads(target.read_text(encoding="utf-8"))["decision"] == (
        "External last-moment edit."
    )
