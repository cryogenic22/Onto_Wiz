from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, cast

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ontowiz_authoring.adapters import (
    AdapterRequest,
    AdapterSession,
    ConfirmCommand,
    PackageCommand,
    ProposeCommand,
    RecordEvidenceCommand,
    RegisterSourceCommand,
    ResumeCommand,
    UpdateSessionCommand,
    ValidateCommand,
    WithdrawSourceCommand,
)
from ontowiz_authoring.workspace import Workspace

from ._support import (
    ExternalTestProvider,
    canonical,
    canonical_tree,
    create_workspace,
    digest,
    evidence_record,
    public_eval,
    source_record,
)


class _PreparedIntent(Protocol):
    format: str
    format_version: int
    operation: str
    workspace_id: str
    expected_revision: int
    request: dict[str, object]
    intent_digest: str


def _request(
    request_id: str,
    workspace_id: str,
    expected_revision: int | None,
    command: object,
) -> AdapterRequest:
    return AdapterRequest.model_validate(
        {
            "format": "ontowiz-adapter-request",
            "format_version": 1,
            "request_id": request_id,
            "workspace_id": workspace_id,
            "expected_revision": expected_revision,
            "command": command,
        }
    )


def _assert_exact_intent(
    prepared: object,
    *,
    operation: str,
    workspace_id: str,
    expected_revision: int,
    request: dict[str, object],
) -> _PreparedIntent:
    intent = cast(_PreparedIntent, prepared)
    assert intent.__class__.__name__ == "AuthoringIntent"
    assert intent.format == "ontowiz-authoring-intent"
    assert intent.format_version == 1
    assert intent.operation == operation
    assert intent.workspace_id == workspace_id
    assert intent.expected_revision == expected_revision
    assert intent.request == request
    assert intent.intent_digest == digest(
        canonical(
            {
                "format": intent.format,
                "format_version": intent.format_version,
                "operation": intent.operation,
                "workspace_id": intent.workspace_id,
                "expected_revision": intent.expected_revision,
                "request": intent.request,
            }
        )
    )
    return intent


def _execute_prepared(
    session: AdapterSession,
    workspace: Workspace,
    provider: ExternalTestProvider,
    request: AdapterRequest,
    *,
    principal_id: str,
    operation: str,
    normalized_request: dict[str, object],
) -> _PreparedIntent:
    prepared = session.prepare_intent(request)
    assert prepared is not None
    intent = _assert_exact_intent(
        prepared,
        operation=operation,
        workspace_id=session.workspace_id,
        expected_revision=cast(int, request.expected_revision),
        request=normalized_request,
    )
    response = session.execute(
        request,
        trust=provider.context(principal_id, intent.intent_digest),
    )
    assert response.status == "ok"
    assert response.session is not None
    assert response.session.workspace_revision in {
        cast(int, request.expected_revision),
        cast(int, request.expected_revision) + 1,
    }
    assert workspace.manifest.workspace_id == session.workspace_id
    return intent


@pytest.mark.contract
def test_read_only_commands_do_not_prepare_operation_credentials(tmp_path: Path) -> None:
    workspace, provider = create_workspace(
        tmp_path / "workspace",
        authority_key=Ed25519PrivateKey.generate(),
    )
    session = AdapterSession(
        workspace,
        provider,
        output_directory=tmp_path / "output",
    )
    for request_id, expected_revision, command in (
        ("REQ-RESUME", None, ResumeCommand(operation="resume")),
        ("REQ-VALIDATE", 1, ValidateCommand(operation="validate")),
        ("REQ-PACKAGE", 1, PackageCommand(operation="package")),
    ):
        request = _request(
            request_id,
            session.workspace_id,
            expected_revision,
            command,
        )
        before = canonical_tree(workspace)
        assert session.prepare_intent(request) is None
        assert canonical_tree(workspace) == before


@pytest.mark.integration
def test_external_host_can_authorize_every_mutation_from_public_prepared_intents(
    tmp_path: Path,
) -> None:
    workspace, provider = create_workspace(
        tmp_path / "workspace",
        authority_key=Ed25519PrivateKey.generate(),
    )
    session = AdapterSession(
        workspace,
        provider,
        output_directory=tmp_path / "output",
    )

    primary_source = source_record()
    register_primary = _request(
        "REQ-SOURCE-PRIMARY",
        session.workspace_id,
        1,
        RegisterSourceCommand(
            operation="register_source",
            source=primary_source,
        ),
    )
    _execute_prepared(
        session,
        workspace,
        provider,
        register_primary,
        principal_id="draft-agent",
        operation="register_source",
        normalized_request={
            "source": primary_source.model_dump(mode="json"),
            "material_path": None,
        },
    )

    auxiliary_source = primary_source.model_copy(
        update={
            "id": "SRC-WITHDRAW",
            "title": "Synthetic source reserved for withdrawal coverage",
            "checksum": digest(b"withdrawal-source"),
        }
    )
    register_auxiliary = _request(
        "REQ-SOURCE-AUXILIARY",
        session.workspace_id,
        2,
        RegisterSourceCommand(
            operation="register_source",
            source=auxiliary_source,
        ),
    )
    _execute_prepared(
        session,
        workspace,
        provider,
        register_auxiliary,
        principal_id="draft-agent",
        operation="register_source",
        normalized_request={
            "source": auxiliary_source.model_dump(mode="json"),
            "material_path": None,
        },
    )

    first_evidence = evidence_record()
    record_first = _request(
        "REQ-EVIDENCE-001",
        session.workspace_id,
        3,
        RecordEvidenceCommand(
            operation="record_evidence",
            evidence=first_evidence,
        ),
    )
    _execute_prepared(
        session,
        workspace,
        provider,
        record_first,
        principal_id="draft-agent",
        operation="record_evidence",
        normalized_request={
            "evidence": first_evidence.model_dump(mode="json"),
            "quote_payload": None,
        },
    )

    second_evidence = first_evidence.model_copy(
        update={
            "id": "EV-002",
            "claim": "A second public synthetic observation supports the candidate.",
        }
    )
    record_second = _request(
        "REQ-EVIDENCE-002",
        session.workspace_id,
        4,
        RecordEvidenceCommand(
            operation="record_evidence",
            evidence=second_evidence,
        ),
    )
    _execute_prepared(
        session,
        workspace,
        provider,
        record_second,
        principal_id="draft-agent",
        operation="record_evidence",
        normalized_request={
            "evidence": second_evidence.model_dump(mode="json"),
            "quote_payload": None,
        },
    )

    replacement = public_eval("EVAL-DEV", "dev")
    propose = _request(
        "REQ-PROPOSE",
        session.workspace_id,
        5,
        ProposeCommand(
            operation="propose",
            delta_id="DELTA-PUBLIC-INTENT",
            target_owner_role="brand_owner",
            allowed_confirmer_roles=("steward", "brand_owner"),
            target_path="pack/evaluations/EVAL-DEV.yaml",
            expected_target_digest=None,
            replacement_body=replacement,
            evidence_ids=("EV-002", "EV-001"),
            rationale="Prove public intent preparation for a full replacement.",
        ),
    )
    _execute_prepared(
        session,
        workspace,
        provider,
        propose,
        principal_id="draft-agent",
        operation="propose",
        normalized_request={
            "delta_id": "DELTA-PUBLIC-INTENT",
            "target_owner_role": "brand_owner",
            "allowed_confirmer_roles": ["brand_owner", "steward"],
            "target_path": "pack/evaluations/EVAL-DEV.yaml",
            "expected_target_digest": None,
            "replacement_body": replacement,
            "evidence_ids": ["EV-001", "EV-002"],
            "rationale": "Prove public intent preparation for a full replacement.",
        },
    )

    confirmed_at = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)
    confirm = _request(
        "REQ-CONFIRM",
        session.workspace_id,
        6,
        ConfirmCommand(
            operation="confirm",
            delta_id="DELTA-PUBLIC-INTENT",
            confirmed_at=confirmed_at,
        ),
    )
    confirm_prepared = session.prepare_intent(confirm)
    assert confirm_prepared is not None
    confirm_intent = cast(_PreparedIntent, confirm_prepared)
    assert confirm_intent.request.keys() == {"delta_id", "confirmed_at", "session"}
    advanced_session = cast(dict[str, object], confirm_intent.request["session"])
    assert advanced_session == {
        "format": "ontowiz-authoring-session",
        "format_version": 2,
        "workspace_id": session.workspace_id,
        "revision": 7,
        "sequence": 1,
        "stage": "discover",
        "last_delta_id": "DELTA-PUBLIC-INTENT",
        "open_question_ids": [],
        "next_mission": "discover",
    }
    _assert_exact_intent(
        confirm_intent,
        operation="confirm",
        workspace_id=session.workspace_id,
        expected_revision=6,
        request={
            "delta_id": "DELTA-PUBLIC-INTENT",
            "confirmed_at": confirmed_at.isoformat(),
            "session": advanced_session,
        },
    )
    confirmation_response = session.execute(
        confirm,
        trust=provider.context("brand-1", confirm_intent.intent_digest),
    )
    assert confirmation_response.status == "ok"

    update = _request(
        "REQ-UPDATE-SESSION",
        session.workspace_id,
        7,
        UpdateSessionCommand(
            operation="update_session",
            stage="challenge",
            last_delta_id="DELTA-PUBLIC-INTENT",
            open_question_ids=(),
            next_mission="challenge",
        ),
    )
    _execute_prepared(
        session,
        workspace,
        provider,
        update,
        principal_id="draft-agent",
        operation="update_session",
        normalized_request={
            "stage": "challenge",
            "last_delta_id": "DELTA-PUBLIC-INTENT",
            "open_question_ids": [],
            "next_mission": "challenge",
        },
    )

    withdrawn_at = datetime(2026, 7, 26, 13, 0, tzinfo=UTC)
    withdraw = _request(
        "REQ-WITHDRAW",
        session.workspace_id,
        8,
        WithdrawSourceCommand(
            operation="withdraw_source",
            source_id="SRC-WITHDRAW",
            withdrawn_at=withdrawn_at,
        ),
    )
    _execute_prepared(
        session,
        workspace,
        provider,
        withdraw,
        principal_id="draft-agent",
        operation="withdraw_source",
        normalized_request={
            "source_id": "SRC-WITHDRAW",
            "withdrawn_at": withdrawn_at.isoformat(),
        },
    )


@pytest.mark.adversarial
def test_intent_preparation_rejects_stale_and_cross_workspace_requests(
    tmp_path: Path,
) -> None:
    workspace, provider = create_workspace(
        tmp_path / "workspace",
        authority_key=Ed25519PrivateKey.generate(),
    )
    session = AdapterSession(
        workspace,
        provider,
        output_directory=tmp_path / "output",
    )
    stale = _request(
        "REQ-STALE",
        session.workspace_id,
        0,
        RegisterSourceCommand(operation="register_source", source=source_record()),
    )
    cross_workspace = _request(
        "REQ-CROSS-WORKSPACE",
        "other-workspace",
        1,
        RegisterSourceCommand(operation="register_source", source=source_record()),
    )
    before = canonical_tree(workspace)

    with pytest.raises(RuntimeError):
        session.prepare_intent(stale)
    with pytest.raises(RuntimeError):
        session.prepare_intent(cross_workspace)

    assert canonical_tree(workspace) == before
