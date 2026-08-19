from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ontowiz_authoring.adapters import AdapterResponse, AdapterSession

from ._support import canonical_tree, create_workspace


@pytest.mark.adversarial
def test_invalid_unicode_is_redacted_and_cannot_change_state(tmp_path: Path) -> None:
    workspace, provider = create_workspace(
        tmp_path / "workspace",
        authority_key=Ed25519PrivateKey.generate(),
    )
    session = AdapterSession(
        workspace,
        provider,
        output_directory=tmp_path / "output",
    )
    before = canonical_tree(workspace)

    payload = session.execute_json("\ud800PRIVATE-PROVIDER-STATE")
    response = AdapterResponse.model_validate_json(payload)

    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "E_REQUEST_INVALID"
    assert b"PRIVATE-PROVIDER-STATE" not in payload
    assert canonical_tree(workspace) == before
