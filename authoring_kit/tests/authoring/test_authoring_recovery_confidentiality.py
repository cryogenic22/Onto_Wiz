from __future__ import annotations

from pathlib import Path

import pytest
from test_authoring_flow import (
    _canonical,
    _intent,
    _provider,
    _source,
    _workspace,
    get_workspace_revision,
)
from test_authoring_gate3_hardening import _InjectedExitError, _kill_after

import ontowiz_authoring.authoring as authoring_module
from ontowiz_authoring.authoring import JournalAttestation


def _workspace_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.mark.adversarial
def test_durable_recovery_residue_contains_no_external_trust_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    source = _source(id="SRC-RECOVERY-CONFIDENTIALITY")
    revision_before = get_workspace_revision(workspace)
    baseline = _workspace_files(workspace.root)
    intent = _intent(
        "register_source",
        workspace,
        None,
        {"material_path": None, "source": source.model_dump(mode="json")},
    )
    trust = provider.context(provider.actor("draft-agent"), intent)
    attestations: list[JournalAttestation] = []
    original_attest = provider.attest_journal

    def capture_attestation(identity: bytes) -> JournalAttestation:
        attestation = original_attest(identity)
        attestations.append(attestation)
        return attestation

    monkeypatch.setattr(provider, "attest_journal", capture_attestation)
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-register_source-journal"),
    )
    with pytest.raises(_InjectedExitError):
        authoring_module.register_source(
            workspace,
            source,
            trust=trust,
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)

    transaction_dir = workspace.root / "locks" / "transactions"
    assert tuple(transaction_dir.glob("*.journal"))
    assert tuple(transaction_dir.glob("*.stage"))
    during_recovery = _workspace_files(workspace.root)
    credential = trust.credential
    credential_payload = _canonical(credential.model_dump(mode="json"))
    serialized_credential = credential_payload.rstrip(b"\n")
    forbidden = {
        "actor principal": credential.principal_id.encode(),
        "credential nonce": credential.nonce.encode(),
        "credential proof signature": credential.proof_signature.encode(),
        "credential trust-key binding": credential.trust_key_id.encode(),
        "credential actor-key binding": credential.actor_key_id.encode(),
        "provider id": b"test-provider",
        "provider key": provider._journal_key_id.encode(),
        "provider attestation field": b'"attestation":',
        "provider attestation type": b'"format":"ontowiz-journal-attestation"',
        "serialized OperationCredential": serialized_credential,
        "OperationCredential type marker": b'"format":"ontowiz-operation-credential"',
        "credential digest": authoring_module._digest(credential_payload).encode(),
    }
    forbidden.update(
        {
            f"provider attestation value {index}": attestation.value.encode()
            for index, attestation in enumerate(attestations)
        }
    )
    leaks = {
        label: tuple(
            path
            for path, payload in during_recovery.items()
            if payload.count(marker) > baseline.get(path, b"").count(marker)
        )
        for label, marker in forbidden.items()
    }
    leaks = {label: paths for label, paths in leaks.items() if paths}

    assert get_workspace_revision(workspace) == revision_before + 1
    persisted = authoring_module._unique_sources(
        authoring_module._load_source_register(workspace)
    )
    assert persisted[source.id] == source
    assert not tuple(transaction_dir.glob("*.journal"))
    assert not tuple(transaction_dir.glob("*.stage"))
    assert not tuple(transaction_dir.glob("*.before"))
    assert not leaks, f"workspace persisted external trust material: {leaks}"
