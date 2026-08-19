from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ontowiz_authoring.adapters import (
    AdapterRequest,
    AdapterSession,
    PackageCommand,
    RegisterSourceCommand,
)

from ._support import canonical_tree, create_workspace, source_record, trust_for


def _request(
    request_id: str,
    workspace_id: str,
    revision: int,
    command: object,
) -> AdapterRequest:
    return AdapterRequest.model_validate(
        {
            "format": "ontowiz-adapter-request",
            "format_version": 1,
            "request_id": request_id,
            "workspace_id": workspace_id,
            "expected_revision": revision,
            "command": command,
        }
    )


@pytest.mark.adversarial
def test_provider_credentials_and_attestations_never_persist(tmp_path: Path) -> None:
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
    response = session.execute(register, trust=trust_for(provider, workspace, register))
    package = _request(
        "REQ-PACKAGE",
        session.workspace_id,
        2,
        PackageCommand(operation="package"),
    )
    package_response = session.execute(package)

    assert response.status == "ok"
    assert package_response.status == "ok"
    persisted = b"".join(canonical_tree(workspace).values())
    assert b"a" * 128 not in persisted
    assert b"external-test-host" not in persisted
    assert b"a" * 128 not in session.package_path.read_bytes()
    assert b"external-test-host" not in session.package_path.read_bytes()
    assert str(session.package_path).encode() not in package_response.model_dump_json().encode()
