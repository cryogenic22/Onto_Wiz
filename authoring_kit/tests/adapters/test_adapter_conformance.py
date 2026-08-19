from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from adapters.claude import ClaudeAdapterSession
from adapters.codex import CodexAdapterSession
from ontowiz_authoring.adapters import (
    AdapterRequest,
    AdapterResponse,
    AdapterSession,
    ConfirmCommand,
    PackageCommand,
    ProposeCommand,
    RecordEvidenceCommand,
    RegisterSourceCommand,
    ResumeCommand,
    UpdateSessionCommand,
    ValidateCommand,
)

from ._support import (
    canonical,
    canonical_tree,
    create_workspace,
    digest,
    evidence_record,
    public_eval,
    source_record,
    trust_for,
)


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


def _authorized_transcript(workspace_id: str) -> tuple[tuple[AdapterRequest, str | None], ...]:
    confirmed_at = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)
    return (
        (
            _request("REQ-RESUME", workspace_id, None, ResumeCommand(operation="resume")),
            None,
        ),
        (
            _request(
                "REQ-SOURCE",
                workspace_id,
                1,
                RegisterSourceCommand(
                    operation="register_source",
                    source=source_record(),
                ),
            ),
            "draft-agent",
        ),
        (
            _request(
                "REQ-EVIDENCE",
                workspace_id,
                2,
                RecordEvidenceCommand(
                    operation="record_evidence",
                    evidence=evidence_record(),
                ),
            ),
            "draft-agent",
        ),
        (
            _request(
                "REQ-DEV-PROPOSAL",
                workspace_id,
                3,
                ProposeCommand(
                    operation="propose",
                    delta_id="DELTA-EVAL-DEV",
                    target_owner_role="brand_owner",
                    allowed_confirmer_roles=("brand_owner",),
                    target_path="pack/evaluations/EVAL-DEV.yaml",
                    expected_target_digest=None,
                    replacement_body=public_eval("EVAL-DEV", "dev"),
                    evidence_ids=("EV-001",),
                    rationale="Add a public development case for the bounded decision.",
                ),
            ),
            "draft-agent",
        ),
        (
            _request(
                "REQ-DEV-CONFIRM",
                workspace_id,
                4,
                ConfirmCommand(
                    operation="confirm",
                    delta_id="DELTA-EVAL-DEV",
                    confirmed_at=confirmed_at,
                ),
            ),
            "brand-1",
        ),
        (
            _request(
                "REQ-REG-PROPOSAL",
                workspace_id,
                5,
                ProposeCommand(
                    operation="propose",
                    delta_id="DELTA-EVAL-REG",
                    target_owner_role="brand_owner",
                    allowed_confirmer_roles=("brand_owner",),
                    target_path="pack/evaluations/EVAL-REG.yaml",
                    expected_target_digest=None,
                    replacement_body=public_eval("EVAL-REG", "regression"),
                    evidence_ids=("EV-001",),
                    rationale="Add a public regression case for the bounded decision.",
                ),
            ),
            "draft-agent",
        ),
        (
            _request(
                "REQ-REG-CONFIRM",
                workspace_id,
                6,
                ConfirmCommand(
                    operation="confirm",
                    delta_id="DELTA-EVAL-REG",
                    confirmed_at=confirmed_at,
                ),
            ),
            "brand-1",
        ),
        (
            _request(
                "REQ-SESSION",
                workspace_id,
                7,
                UpdateSessionCommand(
                    operation="update_session",
                    stage="ratify",
                    last_delta_id="DELTA-EVAL-REG",
                    open_question_ids=(),
                    next_mission="ratify",
                ),
            ),
            "draft-agent",
        ),
        (
            _request("REQ-VALIDATE", workspace_id, 8, ValidateCommand(operation="validate")),
            None,
        ),
        (
            _request("REQ-PACKAGE", workspace_id, 8, PackageCommand(operation="package")),
            None,
        ),
    )


@pytest.mark.contract
def test_codex_and_claude_are_aliases_of_one_protocol() -> None:
    assert CodexAdapterSession is AdapterSession
    assert ClaudeAdapterSession is AdapterSession


@pytest.mark.integration
def test_codex_and_claude_authorized_transcripts_are_byte_identical(tmp_path: Path) -> None:
    authority_key = Ed25519PrivateKey.generate()
    codex_workspace, codex_provider = create_workspace(
        tmp_path / "codex-workspace",
        authority_key=authority_key,
    )
    claude_workspace, claude_provider = create_workspace(
        tmp_path / "claude-workspace",
        authority_key=authority_key,
    )
    codex = CodexAdapterSession(
        codex_workspace,
        codex_provider,
        output_directory=tmp_path / "codex-output",
    )
    claude = ClaudeAdapterSession(
        claude_workspace,
        claude_provider,
        output_directory=tmp_path / "claude-output",
    )

    for request, principal_id in _authorized_transcript(codex.workspace_id):
        codex_trust = (
            trust_for(codex_provider, codex_workspace, request, principal_id=principal_id)
            if principal_id is not None
            else None
        )
        claude_trust = (
            trust_for(claude_provider, claude_workspace, request, principal_id=principal_id)
            if principal_id is not None
            else None
        )
        codex_response = codex.execute(request, trust=codex_trust)
        claude_response = claude.execute(request, trust=claude_trust)
        assert codex_response == claude_response
        assert codex_response.status == "ok"

    assert canonical_tree(codex_workspace) == canonical_tree(claude_workspace)
    assert codex.package_path.read_bytes() == claude.package_path.read_bytes()
    package_response = AdapterResponse.model_validate_json(
        codex.execute_json(
            json.dumps(
                {
                    "format": "ontowiz-adapter-request",
                    "format_version": 1,
                    "request_id": "REQ-PACKAGE-AGAIN",
                    "workspace_id": codex.workspace_id,
                    "expected_revision": 8,
                    "command": {"operation": "package"},
                }
            )
        )
    )
    assert package_response.status == "ok"
    assert package_response.outcome is not None
    assert package_response.outcome.entity_status == "candidate"
    assert package_response.outcome.artifact_name == "brand-variance.owpack"
    assert b"codex" not in codex.package_path.read_bytes().lower()
    assert b"claude" not in codex.package_path.read_bytes().lower()


@pytest.mark.integration
def test_resume_uses_verified_disk_and_provider_high_water(tmp_path: Path) -> None:
    workspace, provider = create_workspace(
        tmp_path / "workspace",
        authority_key=Ed25519PrivateKey.generate(),
    )
    codex = CodexAdapterSession(
        workspace,
        provider,
        output_directory=tmp_path / "codex-output",
    )
    register = _request(
        "REQ-SOURCE",
        codex.workspace_id,
        1,
        RegisterSourceCommand(operation="register_source", source=source_record()),
    )
    assert codex.execute(register, trust=trust_for(provider, workspace, register)).status == "ok"

    fresh_claude = ClaudeAdapterSession(
        workspace.root,
        provider,
        output_directory=tmp_path / "claude-output",
    )
    resumed = fresh_claude.execute(
        _request("REQ-RESUME", fresh_claude.workspace_id, None, ResumeCommand(operation="resume"))
    )
    assert resumed.status == "ok"
    assert resumed.session is not None
    assert resumed.session.workspace_revision == 2
    assert resumed.session.validation.source_count == 1
    assert resumed.session.questions == tuple(
        sorted(resumed.session.questions, key=lambda question: question.id)
    )

    stale = _request(
        "REQ-STALE",
        fresh_claude.workspace_id,
        1,
        RecordEvidenceCommand(operation="record_evidence", evidence=evidence_record()),
    )
    before = canonical_tree(workspace)
    response = fresh_claude.execute(stale, trust=trust_for(provider, workspace, stale))
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "E_STALE"
    assert canonical_tree(workspace) == before


@pytest.mark.adversarial
def test_malformed_cross_workspace_and_secret_inputs_fail_closed(tmp_path: Path) -> None:
    workspace, provider = create_workspace(
        tmp_path / "workspace",
        authority_key=Ed25519PrivateKey.generate(),
    )
    session = AdapterSession(
        workspace,
        provider,
        output_directory=tmp_path / "output",
    )
    secret_marker = "DO-NOT-ECHO-PRIVATE-CREDENTIAL"
    malformed = json.dumps(
        {
            "format": "ontowiz-adapter-request",
            "format_version": 1,
            "request_id": "REQ-MALFORMED",
            "workspace_id": session.workspace_id,
            "expected_revision": 1,
            "command": {
                "operation": "register_source",
                "source": source_record().model_dump(mode="json"),
                "private_provider_state": secret_marker,
            },
        }
    )
    before = canonical_tree(workspace)
    malformed_response = AdapterResponse.model_validate_json(session.execute_json(malformed))
    assert malformed_response.status == "error"
    assert malformed_response.error is not None
    assert malformed_response.error.code == "E_REQUEST_INVALID"
    assert secret_marker.encode() not in session.execute_json(malformed)
    assert canonical_tree(workspace) == before

    duplicate_key = (
        '{"format":"ontowiz-adapter-request","format_version":1,'
        '"request_id":"REQ-DUPLICATE","request_id":"DO-NOT-ECHO-DUPLICATE",'
        f'"workspace_id":"{session.workspace_id}","expected_revision":null,'
        '"command":{"operation":"resume"}}'
    )
    duplicate_response = AdapterResponse.model_validate_json(
        session.execute_json(duplicate_key)
    )
    assert duplicate_response.status == "error"
    assert duplicate_response.error is not None
    assert duplicate_response.error.code == "E_REQUEST_INVALID"
    assert b"DO-NOT-ECHO-DUPLICATE" not in session.execute_json(duplicate_key)
    assert canonical_tree(workspace) == before

    cross_workspace = _request(
        "REQ-CROSS",
        "other-workspace",
        None,
        ResumeCommand(operation="resume"),
    )
    cross_response = session.execute(cross_workspace)
    assert cross_response.status == "error"
    assert cross_response.error is not None
    assert cross_response.error.code == "E_WORKSPACE_MISMATCH"
    assert canonical_tree(workspace) == before


@pytest.mark.adversarial
@pytest.mark.parametrize("malformation", ["expired", "workspace", "intent"])
def test_malformed_external_credentials_fail_closed(
    tmp_path: Path,
    malformation: str,
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
    request = _request(
        "REQ-SOURCE",
        session.workspace_id,
        1,
        RegisterSourceCommand(operation="register_source", source=source_record()),
    )
    kwargs: dict[str, object] = {}
    if malformation == "expired":
        kwargs["expired"] = True
    elif malformation == "workspace":
        kwargs["credential_workspace_id"] = "other-workspace"
    else:
        kwargs["credential_intent_digest"] = "sha256:" + "f" * 64
    trust = trust_for(provider, workspace, request, **kwargs)
    before = canonical_tree(workspace)

    response = session.execute(request, trust=trust)

    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "E_AUTHORIZATION"
    assert "a" * 128 not in response.model_dump_json()
    assert canonical_tree(workspace) == before


@pytest.mark.adversarial
def test_stale_full_document_precondition_refuses_confirmation(tmp_path: Path) -> None:
    workspace, provider = create_workspace(
        tmp_path / "workspace",
        authority_key=Ed25519PrivateKey.generate(),
    )
    session = AdapterSession(
        workspace,
        provider,
        output_directory=tmp_path / "output",
    )
    register = _request(
        "REQ-SOURCE",
        session.workspace_id,
        1,
        RegisterSourceCommand(operation="register_source", source=source_record()),
    )
    evidence = _request(
        "REQ-EVIDENCE",
        session.workspace_id,
        2,
        RecordEvidenceCommand(operation="record_evidence", evidence=evidence_record()),
    )
    assert session.execute(register, trust=trust_for(provider, workspace, register)).status == "ok"
    assert session.execute(evidence, trust=trust_for(provider, workspace, evidence)).status == "ok"

    target = workspace.root / "pack/scope/DEC-001.yaml"
    replacement = json.loads(target.read_bytes())
    proposal = _request(
        "REQ-PROPOSE",
        session.workspace_id,
        3,
        ProposeCommand(
            operation="propose",
            delta_id="DELTA-STALE-TARGET",
            target_owner_role="brand_owner",
            allowed_confirmer_roles=("brand_owner",),
            target_path="pack/scope/DEC-001.yaml",
            expected_target_digest=digest(target.read_bytes()),
            replacement_body=replacement,
            evidence_ids=("EV-001",),
            rationale="Bind an exact full-document candidate precondition.",
        ),
    )
    assert session.execute(proposal, trust=trust_for(provider, workspace, proposal)).status == "ok"
    replacement["decision"] = "An out-of-band rewrite makes the proposal stale."
    target.write_bytes(canonical(replacement))
    before_confirmation = canonical_tree(workspace)
    confirmation = _request(
        "REQ-CONFIRM",
        session.workspace_id,
        4,
        ConfirmCommand(
            operation="confirm",
            delta_id="DELTA-STALE-TARGET",
            confirmed_at=datetime(2026, 7, 26, 12, 0, tzinfo=UTC),
        ),
    )

    response = session.execute(
        confirmation,
        trust=trust_for(
            provider,
            workspace,
            confirmation,
            principal_id="brand-1",
        ),
    )

    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "E_CONFLICT"
    assert canonical_tree(workspace) == before_confirmation
