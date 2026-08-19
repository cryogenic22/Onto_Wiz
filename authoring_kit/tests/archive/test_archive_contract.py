from __future__ import annotations

import hashlib
import json
import struct
import threading
import time
import zipfile
from datetime import date
from pathlib import Path

import pytest

import ontowiz_authoring.archive as archive_module
from ontowiz_authoring import Workspace
from ontowiz_authoring.archive import (
    ArchiveBuildError,
    ArchiveConflictError,
    ArchiveImportError,
    ArchiveVerificationError,
    build_candidate_pack,
    build_workspace_archive,
    import_workspace_archive,
    verify_archive,
)
from ontowiz_authoring.authoring import (
    AuthoringProviderState,
    AuthorityHighWater,
    _authoring_lock,
)
from ontowiz_authoring.explorer import (
    CandidateExplorerContext,
    candidate_explorer_context_bytes,
    render_candidate_explorer,
)


@pytest.fixture(autouse=True)
def _fixed_archive_effective_date(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        archive_module,
        "_trusted_effective_date",
        lambda: date(2026, 7, 26),
    )


class _ArchiveTrustProvider:
    def __init__(self, workspace_id: str, *, revision: int = 0) -> None:
        key = bytes(32)
        key_digest = "sha256:" + hashlib.sha256(key).hexdigest()
        self._authority = AuthorityHighWater(
            format="ontowiz-authority-high-water",
            format_version=1,
            workspace_id=workspace_id,
            trust_key_id=key_digest,
            authority_public_key=key.hex(),
            authority_revision=0,
            authority_digest=None,
        )
        self._state = AuthoringProviderState(
            format="ontowiz-provider-state",
            format_version=1,
            workspace_id=workspace_id,
            authoring_revision=revision,
            pending=None,
            last_finalized_transaction_id=None,
            last_finalized_transaction_digest=None,
        )

    def authority_high_water(self, workspace_id: str) -> AuthorityHighWater:
        assert workspace_id == self._authority.workspace_id
        return self._authority

    def authoring_state(self, workspace_id: str) -> AuthoringProviderState:
        assert workspace_id == self._state.workspace_id
        return self._state


def _trust(workspace: Workspace, *, revision: int = 0) -> _ArchiveTrustProvider:
    return _ArchiveTrustProvider(workspace.manifest.workspace_id, revision=revision)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


class _Utf8Info(zipfile.ZipInfo):
    def _encodeFilenameFlags(self) -> tuple[bytes, int]:  # noqa: N802
        return self.filename.encode("utf-8"), self.flag_bits | 0x800


def _archive_info(name: str) -> zipfile.ZipInfo:
    info = _Utf8Info(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    info.extra = b""
    info.comment = b""
    return info


def _forge_payload(
    archive_path: Path,
    relative: str,
    payload: bytes,
    *,
    refresh_manifest: bool,
) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        names = [info.filename for info in archive.infolist()]
        payloads = {name: archive.read(name) for name in names}
    payloads[relative] = payload
    if refresh_manifest:
        manifest = json.loads(payloads["META-INF/manifest.json"])
        for entry in manifest["entries"]:
            if entry["path"] == relative:
                entry["byte_count"] = len(payload)
                entry["sha256"] = "sha256:" + hashlib.sha256(payload).hexdigest()
                break
        else:
            raise AssertionError(f"missing test payload: {relative}")
        core = dict(manifest)
        core.pop("semantic_digest")
        manifest["semantic_digest"] = "sha256:" + hashlib.sha256(_canonical(core)).hexdigest()
        payloads["META-INF/manifest.json"] = _canonical(manifest)
        payloads["META-INF/manifest.sha256"] = (
            hashlib.sha256(payloads["META-INF/manifest.json"]).hexdigest() + "\n"
        ).encode("ascii")
    temporary = archive_path.with_suffix(archive_path.suffix + ".forged")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in names:
            archive.writestr(_archive_info(name), payloads[name])
    temporary.replace(archive_path)


def _insert_zip_bytes(
    archive_path: Path,
    offset: int,
    overlay: bytes,
    *,
    local_extra_length: int | None = None,
) -> None:
    data = bytearray(archive_path.read_bytes())
    eocd = len(data) - 22
    assert data[eocd : eocd + 4] == b"PK\x05\x06"
    entry_count = struct.unpack_from("<H", data, eocd + 10)[0]
    central_offset = struct.unpack_from("<I", data, eocd + 16)[0]
    if local_extra_length is not None:
        struct.pack_into("<H", data, 28, local_extra_length)
    data[offset:offset] = overlay
    shifted_central = central_offset + (len(overlay) if offset <= central_offset else 0)
    cursor = shifted_central
    for _ in range(entry_count):
        assert data[cursor : cursor + 4] == b"PK\x01\x02"
        name_length, extra_length, comment_length = struct.unpack_from(
            "<3H",
            data,
            cursor + 28,
        )
        local_offset = struct.unpack_from("<I", data, cursor + 42)[0]
        if local_offset >= offset:
            struct.pack_into("<I", data, cursor + 42, local_offset + len(overlay))
        cursor += 46 + name_length + extra_length + comment_length
    shifted_eocd = eocd + len(overlay)
    struct.pack_into("<I", data, shifted_eocd + 16, shifted_central)
    archive_path.write_bytes(data)


def _first_local_record_end(archive_path: Path) -> int:
    data = archive_path.read_bytes()
    compressed_size = struct.unpack_from("<I", data, 18)[0]
    name_length, extra_length = struct.unpack_from("<2H", data, 26)
    return 30 + name_length + extra_length + compressed_size


def _forge_add_payloads(
    archive_path: Path,
    additions: dict[str, tuple[bytes, str, str]],
) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        payloads = {info.filename: archive.read(info.filename) for info in archive.infolist()}
    manifest = json.loads(payloads["META-INF/manifest.json"])
    for path, (payload, role, media_type) in additions.items():
        payloads[path] = payload
        manifest["entries"].append(
            {
                "byte_count": len(payload),
                "media_type": media_type,
                "path": path,
                "role": role,
                "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest["entries"].sort(key=lambda entry: entry["path"])
    core = dict(manifest)
    core.pop("semantic_digest")
    manifest["semantic_digest"] = "sha256:" + hashlib.sha256(_canonical(core)).hexdigest()
    payloads["META-INF/manifest.json"] = _canonical(manifest)
    payloads["META-INF/manifest.sha256"] = (
        hashlib.sha256(payloads["META-INF/manifest.json"]).hexdigest() + "\n"
    ).encode("ascii")
    names = [
        "META-INF/manifest.json",
        "META-INF/manifest.sha256",
        *(entry["path"] for entry in manifest["entries"]),
    ]
    temporary = archive_path.with_suffix(archive_path.suffix + ".forged")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in names:
            archive.writestr(_archive_info(name), payloads[name])
    temporary.replace(archive_path)


def _workspace(root: Path) -> Workspace:
    return Workspace.initialize(
        root,
        workspace_id="archive-contract",
        owner_roles=("steward", "approver"),
        archetypes=("enterprise_core",),
    )


def _tree_digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _govern_source(
    workspace: Workspace,
    *,
    transferable: bool,
    retention_until: str | None = "2027-12-31",
    client_boundary: str = "archive-contract",
) -> tuple[str, bytes]:
    payload = b"governed source bytes\r\n"
    checksum = "sha256:" + hashlib.sha256(payload).hexdigest()
    source = {
        "checksum": checksum,
        "client_boundary": client_boundary,
        "confidentiality": "internal",
        "consent_basis": None,
        "contains_personal_data": False,
        "fresh_until": "2027-12-31",
        "id": "SRC-transfer",
        "owner_role": "steward",
        "permitted_uses": ["authoring-workspace-transfer"],
        "personal_data_transfer_allowed": False,
        "quotation_allowed": True,
        "raw_transfer_allowed": transferable,
        "redistribution_allowed": True,
        "retention_until": retention_until,
        "scope": ["archive contract"],
        "source_date": "2026-01-01",
        "status": "current",
        "title": "Transfer source",
        "withdrawn_at": None,
    }
    register = {
        "format": "ontowiz-source-register",
        "format_version": 1,
        "sources": [source],
    }
    binding = {
        "bindings": [
            {
                "checksum": checksum,
                "relative_path": "sources/inbox/source.bin",
                "source_id": "SRC-transfer",
            }
        ],
        "format": "ontowiz-source-material-bindings",
        "format_version": 1,
        "workspace_id": workspace.manifest.workspace_id,
    }
    (workspace.root / "sources/inbox/source.bin").write_bytes(payload)
    (workspace.root / "sources/source-register.yaml").write_bytes(_canonical(register))
    (workspace.root / "locks/source-material-bindings.json").write_bytes(_canonical(binding))
    return checksum, payload


def _portable_record(body: dict[str, object]) -> dict[str, object]:
    record = dict(body)
    assert "record_digest" not in record
    record["record_digest"] = "sha256:" + hashlib.sha256(_canonical(record)).hexdigest()
    return record


def _write_portable_record(path: Path, body: dict[str, object]) -> None:
    path.write_bytes(_canonical(_portable_record(body)))


def _install_portable_record_graph(workspace: Workspace) -> dict[str, Path]:
    checksum, _ = _govern_source(workspace, transferable=False)
    source_register = json.loads((workspace.root / "sources/source-register.yaml").read_bytes())
    source_record = next(
        item for item in source_register["sources"] if item["id"] == "SRC-transfer"
    )
    source_binding = {
        "registered_checksum": checksum,
        "source_id": "SRC-transfer",
        "source_record_digest": "sha256:" + hashlib.sha256(_canonical(source_record)).hexdigest(),
    }
    evidence = {
        "claim": "Synthetic governed evidence.",
        "confidence": 0.9,
        "extracted_at": "2026-07-26T12:00:00Z",
        "id": "EVID-001",
        "locator": "paragraph 1",
        "locator_type": "paragraph",
        "mode": "observed",
        "permitted_use": "authoring-workspace-transfer",
        "quote_digest": None,
        "quoted": False,
        "source_checksum": checksum,
        "source_id": "SRC-transfer",
        "valid_as_of": "2026-07-26",
    }
    evidence_binding = {
        "evidence_id": "EVID-001",
        "evidence_item_digest": "sha256:" + hashlib.sha256(_canonical(evidence)).hexdigest(),
        "source_checksum": checksum,
        "source_id": "SRC-transfer",
    }
    evidence_document = {
        "evidence": [evidence],
        "format": "ontowiz-extracted-evidence",
        "format_version": 2,
        "quotes": [],
        "source_id": "SRC-transfer",
    }
    (workspace.root / "sources/extracted/SRC-transfer.json").write_bytes(
        _canonical(evidence_document)
    )

    artifact = {
        "abstention_conditions": ["The governed evidence is unavailable."],
        "applicability": {
            "audiences": [],
            "effective_from": "2026-01-01",
            "lifecycle_stages": ["launch"],
            "markets": ["GB"],
            "products": [],
        },
        "definition": "A candidate-only human approval boundary.",
        "evidence_refs": ["EVID-001"],
        "id": "ART-001",
        "kind": "decision_contract",
        "name": "Human approval boundary",
        "owner_role": "steward",
        "provenance": {
            "confidence": 0.9,
            "mode": "sme_authored",
            "open_questions": [],
            "supplied_by": "steward",
        },
        "source_document_ids": ["SRC-transfer"],
    }
    artifact_payload = _canonical(artifact)
    artifact_binding = {
        "artifact_id": "ART-001",
        "payload_digest": "sha256:" + hashlib.sha256(artifact_payload).hexdigest(),
    }
    artifact_path = workspace.root / "pack/scope/ART-001.yaml"
    artifact_path.write_bytes(artifact_payload)
    pack_path = workspace.root / "pack/pack.yaml"
    pack = json.loads(pack_path.read_bytes())
    pack["artifact_digests"] = [
        {"artifact_id": "ART-001", "digest": artifact_binding["payload_digest"]}
    ]
    pack_payload = _canonical(pack)
    pack_path.write_bytes(pack_payload)
    pack_manifest_digest = "sha256:" + hashlib.sha256(pack_payload).hexdigest()

    state = {
        "format": "ontowiz-authoring-session-state",
        "format_version": 1,
        "last_delta_id": None,
        "next_mission": "challenge",
        "open_question_ids": ["Q-001"],
        "stage": "challenge",
    }
    state_payload = _canonical(state)
    (workspace.root / "authoring/session-state.yaml").write_bytes(state_payload)

    session_id = "SESSION-001"
    common = {
        "session_id": session_id,
        "session_sequence": 0,
        "status": "candidate",
        "workspace_id": workspace.manifest.workspace_id,
        "workspace_revision": 0,
    }
    content_bindings = {
        "candidate_artifact_bindings": [artifact_binding],
        "evidence_bindings": [evidence_binding],
        "pack_manifest_digest": pack_manifest_digest,
        "source_bindings": [source_binding],
    }
    session = _portable_record(
        {
            **common,
            "canonical_state_digest": "sha256:" + hashlib.sha256(state_payload).hexdigest(),
            "delta_bindings": [],
            "format": "ontowiz-candidate-session-record",
            "format_version": 1,
            "pack_manifest_digest": pack_manifest_digest,
            "question_ids": ["Q-001"],
        }
    )
    question = {
        "blocking": True,
        "gap_kind": "decision",
        "id": "Q-001",
        "owner_role": "steward",
        "prompt": "Which bounded action should remain human-owned?",
        "resolves": ["decision boundary"],
    }
    questions = _portable_record(
        {
            **common,
            "format": "ontowiz-candidate-session-questions",
            "format_version": 1,
            "questions": [question],
            "session_record_digest": session["record_digest"],
        }
    )
    response = {
        **content_bindings,
        "id": "RESP-001",
        "question_id": "Q-001",
        "response": "The steward retains final approval.",
    }
    responses = _portable_record(
        {
            **common,
            "format": "ontowiz-candidate-session-responses",
            "format_version": 1,
            "responses": [response],
            "session_record_digest": session["record_digest"],
        }
    )
    claim = _portable_record(
        {
            **common,
            **content_bindings,
            "claim": "The source supports the candidate decision boundary.",
            "claim_record_id": "SRC-CLAIM-001",
            "format": "ontowiz-candidate-claim-record",
            "format_version": 1,
        }
    )
    decision = _portable_record(
        {
            **common,
            **content_bindings,
            "decision": "Retain human approval.",
            "decision_record_id": "DDR-001",
            "format": "ontowiz-candidate-decision-record",
            "format_version": 1,
            "rationale": "The governed evidence does not authorize autonomous action.",
        }
    )
    receipt = _portable_record(
        {
            **common,
            "candidate_artifact_bindings": [artifact_binding],
            "claim_record_bindings": [
                {
                    "record_digest": claim["record_digest"],
                    "record_id": "SRC-CLAIM-001",
                }
            ],
            "decision_record_bindings": [
                {
                    "record_digest": decision["record_digest"],
                    "record_id": "DDR-001",
                }
            ],
            "delta_bindings": [],
            "evidence_bindings": [evidence_binding],
            "format": "ontowiz-candidate-session-receipt",
            "format_version": 1,
            "pack_manifest_digest": pack_manifest_digest,
            "question_ids": ["Q-001"],
            "questions_record_digest": questions["record_digest"],
            "response_ids": ["RESP-001"],
            "responses_record_digest": responses["record_digest"],
            "session_record_digest": session["record_digest"],
            "source_bindings": [source_binding],
        }
    )
    session_dir = workspace.root / "authoring/sessions" / session_id
    session_dir.mkdir()
    records = {
        "session": session_dir / "session.yaml",
        "questions": session_dir / "questions.yaml",
        "responses": session_dir / "responses.yaml",
        "receipt": session_dir / "receipt.yaml",
        "claim": workspace.root / "sources/candidate-claims/SRC-CLAIM-001.yaml",
        "decision": workspace.root / "authoring/decisions/DDR-001.yaml",
    }
    for key, value in (
        ("session", session),
        ("questions", questions),
        ("responses", responses),
        ("receipt", receipt),
        ("claim", claim),
        ("decision", decision),
    ):
        records[key].write_bytes(_canonical(value))
    return records


def _mutate_portable_record(path: Path, **changes: object) -> None:
    record = json.loads(path.read_bytes())
    record.pop("record_digest")
    record.update(changes)
    path.write_bytes(_canonical(_portable_record(record)))


def _append_portable_session_bundle(
    workspace: Workspace,
    *,
    session_id: str,
    workspace_revision: int,
    session_sequence: int,
    state_payload: bytes,
    question_id: str,
) -> dict[str, Path]:
    common = {
        "session_id": session_id,
        "session_sequence": session_sequence,
        "status": "candidate",
        "workspace_id": workspace.manifest.workspace_id,
        "workspace_revision": workspace_revision,
    }
    pack_payload = (workspace.root / "pack/pack.yaml").read_bytes()
    pack_manifest_digest = "sha256:" + hashlib.sha256(pack_payload).hexdigest()
    session = _portable_record(
        {
            **common,
            "canonical_state_digest": "sha256:" + hashlib.sha256(state_payload).hexdigest(),
            "delta_bindings": [],
            "format": "ontowiz-candidate-session-record",
            "format_version": 1,
            "pack_manifest_digest": pack_manifest_digest,
            "question_ids": [question_id],
        }
    )
    questions = _portable_record(
        {
            **common,
            "format": "ontowiz-candidate-session-questions",
            "format_version": 1,
            "questions": [
                {
                    "blocking": True,
                    "gap_kind": "decision",
                    "id": question_id,
                    "owner_role": "steward",
                    "prompt": f"Resolve historical checkpoint {question_id}.",
                    "resolves": [f"checkpoint {question_id}"],
                }
            ],
            "session_record_digest": session["record_digest"],
        }
    )
    responses = _portable_record(
        {
            **common,
            "format": "ontowiz-candidate-session-responses",
            "format_version": 1,
            "responses": [],
            "session_record_digest": session["record_digest"],
        }
    )
    receipt = _portable_record(
        {
            **common,
            "candidate_artifact_bindings": [],
            "claim_record_bindings": [],
            "decision_record_bindings": [],
            "delta_bindings": [],
            "evidence_bindings": [],
            "format": "ontowiz-candidate-session-receipt",
            "format_version": 1,
            "pack_manifest_digest": pack_manifest_digest,
            "question_ids": [question_id],
            "questions_record_digest": questions["record_digest"],
            "response_ids": [],
            "responses_record_digest": responses["record_digest"],
            "session_record_digest": session["record_digest"],
            "source_bindings": [],
        }
    )
    directory = workspace.root / "authoring/sessions" / session_id
    directory.mkdir()
    paths = {
        "session": directory / "session.yaml",
        "questions": directory / "questions.yaml",
        "responses": directory / "responses.yaml",
        "receipt": directory / "receipt.yaml",
    }
    for name, record in (
        ("session", session),
        ("questions", questions),
        ("responses", responses),
        ("receipt", receipt),
    ):
        paths[name].write_bytes(_canonical(record))
    return paths


def _install_second_provenance_chain(workspace: Workspace) -> None:
    register_path = workspace.root / "sources/source-register.yaml"
    register = json.loads(register_path.read_bytes())
    second_checksum = "sha256:" + hashlib.sha256(b"second governed source").hexdigest()
    second_source = dict(register["sources"][0])
    second_source.update(
        {
            "checksum": second_checksum,
            "id": "SRC-other",
            "title": "Other governed source",
        }
    )
    register["sources"].append(second_source)
    register["sources"].sort(key=lambda item: item["id"])
    register_path.write_bytes(_canonical(register))

    evidence = {
        "claim": "Other synthetic governed evidence.",
        "confidence": 0.9,
        "extracted_at": "2026-07-26T12:00:00Z",
        "id": "EVID-002",
        "locator": "paragraph 2",
        "locator_type": "paragraph",
        "mode": "observed",
        "permitted_use": "authoring-workspace-transfer",
        "quote_digest": None,
        "quoted": False,
        "source_checksum": second_checksum,
        "source_id": "SRC-other",
        "valid_as_of": "2026-07-26",
    }
    (workspace.root / "sources/extracted/SRC-other.json").write_bytes(
        _canonical(
            {
                "evidence": [evidence],
                "format": "ontowiz-extracted-evidence",
                "format_version": 2,
                "quotes": [],
                "source_id": "SRC-other",
            }
        )
    )

    first_artifact_path = workspace.root / "pack/scope/ART-001.yaml"
    second_artifact = json.loads(first_artifact_path.read_bytes())
    second_artifact.update(
        {
            "evidence_refs": ["EVID-002"],
            "id": "ART-002",
            "name": "Other human approval boundary",
            "source_document_ids": ["SRC-other"],
        }
    )
    second_payload = _canonical(second_artifact)
    (workspace.root / "pack/scope/ART-002.yaml").write_bytes(second_payload)
    pack_path = workspace.root / "pack/pack.yaml"
    pack = json.loads(pack_path.read_bytes())
    pack["artifact_digests"].append(
        {
            "artifact_id": "ART-002",
            "digest": "sha256:" + hashlib.sha256(second_payload).hexdigest(),
        }
    )
    pack["artifact_digests"].sort(key=lambda item: item["artifact_id"])
    pack_path.write_bytes(_canonical(pack))


@pytest.mark.contract
def _advance_content_bound_history(workspace: Workspace) -> tuple[bytes, bytes]:
    _install_second_provenance_chain(workspace)
    artifact_path = workspace.root / "pack/scope/ART-001.yaml"
    artifact = json.loads(artifact_path.read_bytes())
    artifact.update(
        {
            "definition": "A later candidate boundary with revised provenance.",
            "evidence_refs": ["EVID-002"],
            "source_document_ids": ["SRC-other"],
        }
    )
    artifact_payload = _canonical(artifact)
    artifact_path.write_bytes(artifact_payload)
    artifact_digest = "sha256:" + hashlib.sha256(artifact_payload).hexdigest()
    pack_path = workspace.root / "pack/pack.yaml"
    pack = json.loads(pack_path.read_bytes())
    for item in pack["artifact_digests"]:
        if item["artifact_id"] == "ART-001":
            item["digest"] = artifact_digest
    pack_payload = _canonical(pack)
    pack_path.write_bytes(pack_payload)

    state = {
        "format": "ontowiz-authoring-session-state",
        "format_version": 1,
        "last_delta_id": None,
        "next_mission": "ratify",
        "open_question_ids": ["Q-002"],
        "stage": "ratify",
    }
    state_payload = _canonical(state)
    (workspace.root / "authoring/session-state.yaml").write_bytes(state_payload)
    _append_portable_session_bundle(
        workspace,
        session_id="SESSION-002",
        workspace_revision=2,
        session_sequence=2,
        state_payload=state_payload,
        question_id="Q-002",
    )
    revision = {
        "format": "ontowiz-authoring-revision",
        "format_version": 2,
        "revision": 2,
        "session_digest": None,
        "session_sequence": 2,
        "workspace_id": workspace.manifest.workspace_id,
    }
    (workspace.root / "locks/authoring-revision.json").write_bytes(_canonical(revision))
    return artifact_payload, pack_payload


def test_workspace_archive_is_byte_deterministic_and_source_immutable(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    before = _tree_digest(workspace.root)

    first = build_workspace_archive(
        workspace,
        tmp_path / "first.owworkspace",
        source_profile="referenced",
        as_of=date(2026, 7, 26),
    )
    second = build_workspace_archive(
        workspace.root,
        tmp_path / "second.owworkspace",
        source_profile="referenced",
        as_of=date(2026, 7, 26),
    )

    assert first.path.read_bytes() == second.path.read_bytes()
    assert first.semantic_digest == second.semantic_digest
    assert _tree_digest(workspace.root) == before
    with zipfile.ZipFile(first.path) as archive:
        infos = archive.infolist()
        assert [info.filename for info in infos[:2]] == [
            "META-INF/manifest.json",
            "META-INF/manifest.sha256",
        ]
        assert [info.filename for info in infos[2:]] == sorted(info.filename for info in infos[2:])
        for info in infos:
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 3
            assert info.flag_bits == 0x800
            assert info.extra == b""
            assert info.comment == b""
            assert (info.external_attr >> 16) == 0o100644


@pytest.mark.contract
def test_referenced_profile_omits_governed_bytes_with_exact_record(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    checksum, _ = _govern_source(workspace, transferable=False)

    verified = build_workspace_archive(
        workspace,
        tmp_path / "portable.owworkspace",
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace),
    )

    paths = {entry.path for entry in verified.manifest.entries}
    assert "sources/inbox/source.bin" not in paths
    omission = "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml"
    assert omission in paths
    with zipfile.ZipFile(verified.path) as archive:
        record = json.loads(archive.read(omission))
    assert record["source_profile"] == "referenced"
    assert record["omitted"] == [
        {
            "path": "sources/inbox/source.bin",
            "reason": "referenced-profile-governed-source-omission",
            "sha256": checksum,
            "source_id": "SRC-transfer",
        }
    ]


@pytest.mark.contract
def test_embedded_profile_requires_all_transfer_rights(tmp_path: Path) -> None:
    permitted = _workspace(tmp_path / "permitted")
    checksum, payload = _govern_source(permitted, transferable=True)

    verified = build_workspace_archive(
        permitted,
        tmp_path / "embedded.owworkspace",
        source_profile="embedded",
        as_of=date(2026, 7, 26),
        target_client_boundary="archive-contract",
        trust_provider=_trust(permitted),
    )
    entries = {entry.path: entry for entry in verified.manifest.entries}
    assert entries["sources/inbox/source.bin"].sha256 == checksum
    with zipfile.ZipFile(verified.path) as archive:
        assert archive.read("sources/inbox/source.bin") == payload

    denied = _workspace(tmp_path / "denied")
    _govern_source(denied, transferable=False)
    with pytest.raises(ArchiveBuildError, match="rights do not permit"):
        build_workspace_archive(
            denied,
            tmp_path / "denied.owworkspace",
            source_profile="embedded",
            as_of=date(2026, 7, 26),
            target_client_boundary="archive-contract",
            trust_provider=_trust(denied),
        )


@pytest.mark.contract
def test_candidate_pack_is_deterministic_candidate_only_and_non_mutating(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    (workspace.root / "reports/validation.json").write_bytes(b'{"private":"report"}\n')
    before = _tree_digest(workspace.root)

    first = build_candidate_pack(workspace, tmp_path / "first.owpack")
    second = build_candidate_pack(workspace.root, tmp_path / "second.owpack")

    assert first.path.read_bytes() == second.path.read_bytes()
    assert _tree_digest(workspace.root) == before
    paths = {entry.path for entry in first.manifest.entries}
    assert paths == {"pack/pack.yaml"}


@pytest.mark.contract
@pytest.mark.parametrize(
    ("relative", "payload"),
    [
        ("pack/evaluations/heldout.json", b'{"protected":true}\n'),
        (
            "pack/ontology/release.json",
            b'{"kind":"ontology","lifecycle":"released"}\n',
        ),
        (
            "pack/governance/approved.json",
            b'{"approval":"yes","name":"unsafe"}\n',
        ),
        (
            "pack/ontology/opaque.json",
            b'{"name":"untyped candidate payload"}\n',
        ),
    ],
)
def test_candidate_pack_rejects_private_or_release_semantics(
    tmp_path: Path,
    relative: str,
    payload: bytes,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    target = workspace.root.joinpath(*relative.split("/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)

    with pytest.raises(ArchiveBuildError):
        build_candidate_pack(
            workspace,
            tmp_path / "unsafe.owpack",
            trust_provider=_trust(workspace),
        )


@pytest.mark.contract
@pytest.mark.parametrize(
    ("builder", "name"),
    [
        ("workspace", "wrong.zip"),
        ("candidate", "wrong.zip"),
    ],
)
def test_archive_build_requires_portable_format_extension(
    tmp_path: Path,
    builder: str,
    name: str,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    with pytest.raises(ArchiveBuildError, match="must use"):
        if builder == "workspace":
            build_workspace_archive(
                workspace,
                tmp_path / name,
                source_profile="referenced",
                as_of=date(2026, 7, 26),
            )
        else:
            build_candidate_pack(workspace, tmp_path / name)


@pytest.mark.contract
def test_verify_rejects_hostile_paths_before_extraction(tmp_path: Path) -> None:
    hostile = tmp_path / "hostile.owworkspace"
    with zipfile.ZipFile(hostile, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("../escape", b"x")
        archive.writestr("META-INF/manifest.json", b"{}\n")

    before = set(tmp_path.iterdir())
    with pytest.raises(ArchiveVerificationError, match="unsafe archive path"):
        verify_archive(hostile)
    assert set(tmp_path.iterdir()) == before
    assert not (tmp_path.parent / "escape").exists()


@pytest.mark.contract
def test_verify_rejects_compression_and_noncanonical_metadata(tmp_path: Path) -> None:
    archive_path = tmp_path / "compressed.owpack"
    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr("META-INF/manifest.json", b"{}\n")
        archive.writestr("META-INF/manifest.sha256", b"0" * 64 + b"\n")

    with pytest.raises(ArchiveVerificationError, match="non-canonical ZIP member"):
        verify_archive(archive_path)


@pytest.mark.contract
def test_import_round_trip_is_staged_idempotent_and_conflict_safe(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "portable.owworkspace"
    verified = build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
    )
    original_archive = archive_path.read_bytes()
    destination = tmp_path / "imported"

    imported = import_workspace_archive(archive_path, destination, effective_date=date(2026, 7, 26))
    repeated = import_workspace_archive(archive_path, destination, effective_date=date(2026, 7, 26))

    assert imported.root == destination
    assert repeated.root == destination
    assert archive_path.read_bytes() == original_archive
    rebuilt = build_workspace_archive(
        imported,
        tmp_path / "rebuilt.owworkspace",
        source_profile="referenced",
        as_of=date(2026, 7, 26),
    )
    assert rebuilt.semantic_digest == verified.semantic_digest

    conflict = tmp_path / "conflict"
    conflict.mkdir()
    sentinel = conflict / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    with pytest.raises(ArchiveConflictError):
        import_workspace_archive(archive_path, conflict, effective_date=date(2026, 7, 26))
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not list(tmp_path.glob(".conflict.owimport-*"))


@pytest.mark.contract
def test_output_inside_source_workspace_is_refused(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")

    with pytest.raises(ArchiveBuildError, match="cannot mutate"):
        build_candidate_pack(workspace, workspace.root / "dist/candidate.owpack")
    assert not (workspace.root / "dist/candidate.owpack").exists()


@pytest.mark.contract
def test_verifier_does_not_mutate_archive_bytes(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "candidate.owpack"
    build_candidate_pack(workspace, archive_path)
    before = archive_path.read_bytes()

    verified = verify_archive(
        archive_path,
        expected_format="ontowiz-candidate-pack",
    )

    assert verified.archive_sha256 == "sha256:" + hashlib.sha256(before).hexdigest()
    assert archive_path.read_bytes() == before


@pytest.mark.contract
def test_verifier_rejects_payload_digest_drift_and_import_leaves_no_partial_tree(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "candidate.owpack"
    build_candidate_pack(workspace, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        manifest = json.loads(archive.read("pack/pack.yaml"))
    manifest["pack_version"] = "0.0.1"
    _forge_payload(
        archive_path,
        "pack/pack.yaml",
        _canonical(manifest),
        refresh_manifest=False,
    )
    before = archive_path.read_bytes()

    with pytest.raises(ArchiveVerificationError, match="payload digest mismatch"):
        verify_archive(archive_path)
    destination = tmp_path / "must-not-exist"
    with pytest.raises(ArchiveVerificationError):
        import_workspace_archive(archive_path, destination, effective_date=date(2026, 7, 26))
    assert not destination.exists()
    assert not list(tmp_path.glob(".must-not-exist.owimport-*"))
    assert archive_path.read_bytes() == before


@pytest.mark.contract
def test_verifier_independently_rejects_forged_source_omission_semantics(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _govern_source(workspace, transferable=True)
    archive_path = tmp_path / "referenced.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace),
    )
    omission_path = "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml"
    with zipfile.ZipFile(archive_path) as archive:
        omission = json.loads(archive.read(omission_path))
    omission["omitted"] = []
    _forge_payload(
        archive_path,
        omission_path,
        _canonical(omission),
        refresh_manifest=True,
    )

    with pytest.raises(
        ArchiveVerificationError,
        match="referenced source omissions are not exact",
    ):
        verify_archive(archive_path)


@pytest.mark.contract
def test_verifier_rejects_stale_semantic_digest_even_with_new_control_digest(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "candidate.owpack"
    build_candidate_pack(workspace, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        names = [info.filename for info in archive.infolist()]
        payloads = {name: archive.read(name) for name in names}
    manifest = json.loads(payloads["META-INF/manifest.json"])
    manifest["entries"][0]["role"] = "candidate-artifact"
    payloads["META-INF/manifest.json"] = _canonical(manifest)
    payloads["META-INF/manifest.sha256"] = (
        hashlib.sha256(payloads["META-INF/manifest.json"]).hexdigest() + "\n"
    ).encode("ascii")
    temporary = archive_path.with_suffix(".semantic-forged")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in names:
            archive.writestr(_archive_info(name), payloads[name])
    temporary.replace(archive_path)

    with pytest.raises(ArchiveVerificationError, match="semantic digest mismatch"):
        verify_archive(archive_path)


@pytest.mark.contract
@pytest.mark.parametrize("attack", ("prefix", "gap", "local-extra", "trailing"))
def test_verifier_rejects_uninventoried_physical_zip_bytes(
    tmp_path: Path,
    attack: str,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / f"{attack}.owpack"
    build_candidate_pack(workspace, archive_path)
    sentinel = b"PROTECTED-OVERLAY-SENTINEL"
    if attack == "prefix":
        _insert_zip_bytes(archive_path, 0, sentinel)
    elif attack == "gap":
        _insert_zip_bytes(
            archive_path,
            _first_local_record_end(archive_path),
            sentinel,
        )
    elif attack == "local-extra":
        data = archive_path.read_bytes()
        name_length = struct.unpack_from("<H", data, 26)[0]
        _insert_zip_bytes(
            archive_path,
            30 + name_length,
            sentinel,
            local_extra_length=len(sentinel),
        )
    else:
        archive_path.write_bytes(archive_path.read_bytes() + sentinel)

    with zipfile.ZipFile(archive_path) as permissive_reader:
        assert permissive_reader.namelist()
    with pytest.raises(ArchiveVerificationError):
        verify_archive(archive_path)


@pytest.mark.contract
def test_candidate_refuses_untyped_text_and_manifest_digest_drift(
    tmp_path: Path,
) -> None:
    text_workspace = _workspace(tmp_path / "text")
    (text_workspace.root / "pack/policies/private-notes.md").write_text(
        "reviewed_by: approver\nlifecycle_history: active\n",
        encoding="utf-8",
    )
    with pytest.raises(ArchiveBuildError):
        build_candidate_pack(
            text_workspace,
            tmp_path / "text.owpack",
            trust_provider=_trust(text_workspace),
        )

    drifted = _workspace(tmp_path / "drifted")
    manifest_path = drifted.root / "pack/pack.yaml"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["artifact_digests"] = [
        {
            "artifact_id": "missing-artifact",
            "digest": "sha256:" + "a" * 64,
        }
    ]
    manifest_path.write_bytes(_canonical(manifest))
    with pytest.raises(ArchiveBuildError, match="digest inventory"):
        build_candidate_pack(
            drifted,
            tmp_path / "drifted.owpack",
            trust_provider=_trust(drifted),
        )


@pytest.mark.contract
def test_provider_free_revision_zero_requires_exact_pristine_controls(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    manifest_path = workspace.root / "pack/pack.yaml"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["pack_version"] = "0.1.1"
    manifest_path.write_bytes(_canonical(manifest))

    with pytest.raises(ArchiveBuildError, match="not converged"):
        build_candidate_pack(workspace, tmp_path / "candidate.owpack")


@pytest.mark.contract
def test_provider_revision_divergence_refuses_snapshot(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")

    with pytest.raises(ArchiveBuildError, match="not converged"):
        build_candidate_pack(
            workspace,
            tmp_path / "candidate.owpack",
            trust_provider=_trust(workspace, revision=1),
        )


@pytest.mark.contract
def test_workspace_refuses_malformed_dynamic_delta(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    proposal = workspace.root / "authoring/proposals/DELTA-bad.yaml"
    proposal.write_bytes(b"{}\n")

    with pytest.raises(ArchiveBuildError):
        build_workspace_archive(
            workspace,
            tmp_path / "bad.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )


@pytest.mark.contract
def test_import_refuses_forged_delta_and_leaves_no_partial_tree(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "forged.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
    )
    _forge_add_payloads(
        archive_path,
        {
            "authoring/proposals/DELTA-forged.yaml": (
                b"{}\n",
                "authoring-state",
                "application/json",
            )
        },
    )
    with pytest.raises(ArchiveVerificationError):
        verify_archive(archive_path)
    destination = tmp_path / "destination"

    with pytest.raises(ArchiveVerificationError):
        import_workspace_archive(
            archive_path,
            destination,
            effective_date=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )
    assert not destination.exists()
    assert not list(tmp_path.glob(".destination.owimport-*"))


@pytest.mark.contract
def test_import_regenerates_and_validates_derived_outputs(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "portable.owworkspace"
    effective_date = archive_module._trusted_effective_date()
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=effective_date,
    )

    imported = import_workspace_archive(
        archive_path,
        tmp_path / "imported",
        effective_date=effective_date,
    )

    for relative in (
        "reports/validation.json",
        "reports/semantic-findings.json",
        "reports/readiness.json",
        "build/context-model.json",
        "build/explorer.html",
    ):
        assert (imported.root / relative).is_file()

    context_payload = (imported.root / "build/context-model.json").read_bytes()
    context = CandidateExplorerContext.model_validate_json(context_payload)
    assert candidate_explorer_context_bytes(context) == context_payload
    assert (
        render_candidate_explorer(context) == (imported.root / "build/explorer.html").read_bytes()
    )
    assert context.workspace_id == imported.manifest.workspace_id
    assert tuple(binding.path for binding in context.documents) == ("pack/pack.yaml",)
    pack_payload = (imported.root / "pack/pack.yaml").read_bytes()
    assert context.documents[0].sha256 == ("sha256:" + hashlib.sha256(pack_payload).hexdigest())


@pytest.mark.contract
@pytest.mark.parametrize(
    ("retention_until", "source_boundary", "target_boundary"),
    [
        (None, "archive-contract", "archive-contract"),
        ("2027-12-31", "client-a", "client-b"),
    ],
)
def test_embedded_transfer_refuses_unknown_retention_or_cross_client(
    tmp_path: Path,
    retention_until: str | None,
    source_boundary: str,
    target_boundary: str,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _govern_source(
        workspace,
        transferable=True,
        retention_until=retention_until,
        client_boundary=source_boundary,
    )

    with pytest.raises(ArchiveBuildError):
        build_workspace_archive(
            workspace,
            tmp_path / "embedded.owworkspace",
            source_profile="embedded",
            as_of=date(2026, 7, 26),
            target_client_boundary=target_boundary,
            trust_provider=_trust(workspace),
        )


@pytest.mark.contract
def test_import_reauthorizes_rights_immediately_before_extraction(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _govern_source(
        workspace,
        transferable=True,
        retention_until="2026-07-26",
    )
    archive_path = tmp_path / "embedded.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="embedded",
        as_of=date(2026, 7, 26),
        target_client_boundary="archive-contract",
        trust_provider=_trust(workspace),
    )
    destination = tmp_path / "expired"

    with pytest.raises(ArchiveImportError, match="no longer authorized"):
        import_workspace_archive(
            archive_path,
            destination,
            effective_date=date(2026, 7, 27),
            target_client_boundary="archive-contract",
            trust_provider=_trust(workspace),
        )
    assert not destination.exists()


@pytest.mark.contract
def test_referenced_import_rejects_destination_boundary(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "referenced.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
    )
    destination = tmp_path / "must-not-exist"

    with pytest.raises(ArchiveImportError, match="must not receive"):
        import_workspace_archive(
            archive_path,
            destination,
            effective_date=date(2026, 7, 26),
            target_client_boundary="client-a",
        )
    assert not destination.exists()


@pytest.mark.contract
@pytest.mark.parametrize("trusted_boundary", [None, "another-client"])
def test_import_requires_exact_trusted_destination_boundary(
    tmp_path: Path,
    trusted_boundary: str | None,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _govern_source(workspace, transferable=True)
    archive_path = tmp_path / "embedded.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="embedded",
        as_of=date(2026, 7, 26),
        target_client_boundary="archive-contract",
        trust_provider=_trust(workspace),
    )
    destination = tmp_path / "must-not-exist"

    with pytest.raises(ArchiveImportError, match="trusted destination boundary"):
        import_workspace_archive(
            archive_path,
            destination,
            effective_date=date(2026, 7, 26),
            target_client_boundary=trusted_boundary,
            trust_provider=_trust(workspace),
        )
    assert not destination.exists()
    assert not list(tmp_path.glob(".must-not-exist.owimport-*"))


@pytest.mark.contract
def test_component_prefix_namespace_collision_is_rejected(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    archive_path = tmp_path / "collision.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
    )
    _forge_add_payloads(
        archive_path,
        {
            "pack/Foo": (
                b"x",
                "candidate-pack-state",
                "application/octet-stream",
            ),
            "pack/foo/bar.json": (
                b"{}\n",
                "candidate-pack-state",
                "application/json",
            ),
        },
    )

    with pytest.raises(ArchiveVerificationError, match="namespace collision"):
        verify_archive(archive_path)


@pytest.mark.contract
def test_builder_waits_for_cooperative_authoring_lock(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    held = threading.Event()
    release = threading.Event()
    errors: list[BaseException] = []
    output = tmp_path / "candidate.owpack"

    def hold_lock() -> None:
        with _authoring_lock(workspace.root):
            held.set()
            assert release.wait(timeout=5)

    def build() -> None:
        try:
            build_candidate_pack(workspace, output)
        except BaseException as exc:  # pragma: no cover - assertion reports details
            errors.append(exc)

    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert held.wait(timeout=5)
    builder = threading.Thread(target=build)
    builder.start()
    time.sleep(0.05)
    assert builder.is_alive()
    assert not output.exists()
    release.set()
    holder.join(timeout=5)
    builder.join(timeout=5)

    assert not holder.is_alive()
    assert not builder.is_alive()
    assert errors == []
    assert output.is_file()


@pytest.mark.contract
def test_pinned_read_rejects_distinct_file_swap_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    target = workspace.root / "pack/pack.yaml"
    backup = tmp_path / "pack.backup"
    original_open = archive_module.os.open
    swapped = False

    def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        nonlocal swapped
        candidate = Path(path) if isinstance(path, str | Path) else None
        if candidate == target and not swapped:
            swapped = True
            target.replace(backup)
            target.write_bytes(backup.read_bytes())
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(archive_module.os, "open", racing_open)
    try:
        with pytest.raises(ArchiveBuildError, match="identity changed"):
            build_candidate_pack(workspace, tmp_path / "candidate.owpack")
    finally:
        if target.exists():
            target.unlink()
        if backup.exists():
            backup.replace(target)


@pytest.mark.contract
@pytest.mark.parametrize(
    "record_case",
    ["claim", "session", "questions", "responses", "receipt", "decision"],
)
def test_portable_record_classes_fail_closed(
    tmp_path: Path,
    record_case: str,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    records = _install_portable_record_graph(workspace)
    if record_case == "claim":
        _mutate_portable_record(records[record_case], approved_at="2026-07-26T12:00:00Z")
    elif record_case == "session":
        _mutate_portable_record(records[record_case], workspace_revision=1)
    elif record_case == "questions":
        body = json.loads(records[record_case].read_bytes())
        _mutate_portable_record(records[record_case], questions=body["questions"] * 2)
    elif record_case == "responses":
        body = json.loads(records[record_case].read_bytes())
        response = dict(body["responses"][0])
        response["question_id"] = "Q-UNKNOWN"
        _mutate_portable_record(records[record_case], responses=[response])
    elif record_case == "receipt":
        _mutate_portable_record(records[record_case], response_ids=[])
    else:
        body = json.loads(records[record_case].read_bytes())
        artifact_binding = dict(body["candidate_artifact_bindings"][0])
        artifact_binding["artifact_id"] = "ART-UNKNOWN"
        _mutate_portable_record(
            records[record_case],
            candidate_artifact_bindings=[artifact_binding],
        )

    with pytest.raises(ArchiveBuildError):
        build_workspace_archive(
            workspace,
            tmp_path / "invalid.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )


@pytest.mark.contract
def test_portable_session_missing_record_refuses(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    records = _install_portable_record_graph(workspace)
    records["receipt"].unlink()

    with pytest.raises(ArchiveBuildError, match="record set is incomplete"):
        build_workspace_archive(
            workspace,
            tmp_path / "missing.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )


@pytest.mark.contract
def test_canonical_session_last_delta_must_resolve_exactly(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _install_portable_record_graph(workspace)
    state_path = workspace.root / "authoring/session-state.yaml"
    state = json.loads(state_path.read_bytes())
    state["last_delta_id"] = "DELTA-MISSING"
    state_path.write_bytes(_canonical(state))

    with pytest.raises(ArchiveBuildError, match="session delta is missing"):
        build_workspace_archive(
            workspace,
            tmp_path / "dangling.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )


@pytest.mark.contract
def test_complete_portable_record_graph_round_trips(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    records = _install_portable_record_graph(workspace)
    archive_path = tmp_path / "portable.owworkspace"
    built = build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace),
    )

    imported = import_workspace_archive(
        archive_path,
        tmp_path / "imported",
        effective_date=date(2026, 7, 26),
        trust_provider=_trust(workspace),
    )
    for path in records.values():
        relative = path.relative_to(workspace.root)
        assert (imported.root / relative).read_bytes() == path.read_bytes()
    assert verify_archive(archive_path).semantic_digest == built.semantic_digest


@pytest.mark.contract
def test_verifier_rejects_rehashed_dangling_portable_graph(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _install_portable_record_graph(workspace)
    archive_path = tmp_path / "portable.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace),
    )
    state = json.loads((workspace.root / "authoring/session-state.yaml").read_bytes())
    state["last_delta_id"] = "DELTA-MISSING"
    _forge_payload(
        archive_path,
        "authoring/session-state.yaml",
        _canonical(state),
        refresh_manifest=True,
    )
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None

    with pytest.raises(ArchiveVerificationError, match="session delta is missing"):
        verify_archive(archive_path)


@pytest.mark.contract
def test_gate3_live_current_session_is_not_reinterpreted_as_bundle(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    session = {
        "format": "ontowiz-authoring-session",
        "format_version": 2,
        "last_delta_id": None,
        "next_mission": "discover",
        "open_question_ids": [],
        "revision": 1,
        "sequence": 1,
        "stage": "discover",
        "workspace_id": workspace.manifest.workspace_id,
    }
    session_payload = _canonical(session)
    session_dir = workspace.root / "authoring/sessions/current"
    session_dir.mkdir()
    (session_dir / "session.yaml").write_bytes(session_payload)
    revision = {
        "format": "ontowiz-authoring-revision",
        "format_version": 2,
        "revision": 1,
        "session_digest": "sha256:" + hashlib.sha256(session_payload).hexdigest(),
        "session_sequence": 1,
        "workspace_id": workspace.manifest.workspace_id,
    }
    (workspace.root / "locks/authoring-revision.json").write_bytes(_canonical(revision))

    verified = build_workspace_archive(
        workspace,
        tmp_path / "live.owworkspace",
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace, revision=1),
    )
    assert verify_archive(verified.path).semantic_digest == verified.semantic_digest


@pytest.mark.contract
def test_historical_session_receipt_survives_later_revision_unchanged(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    first_records = _install_portable_record_graph(workspace)
    first_receipt = first_records["receipt"].read_bytes()
    first_receipt_digest = hashlib.sha256(first_receipt).hexdigest()

    later_state = {
        "format": "ontowiz-authoring-session-state",
        "format_version": 1,
        "last_delta_id": None,
        "next_mission": "ratify",
        "open_question_ids": ["Q-002"],
        "stage": "ratify",
    }
    later_state_payload = _canonical(later_state)
    (workspace.root / "authoring/session-state.yaml").write_bytes(later_state_payload)
    _append_portable_session_bundle(
        workspace,
        session_id="SESSION-002",
        workspace_revision=2,
        session_sequence=2,
        state_payload=later_state_payload,
        question_id="Q-002",
    )
    revision = {
        "format": "ontowiz-authoring-revision",
        "format_version": 2,
        "revision": 2,
        "session_digest": None,
        "session_sequence": 2,
        "workspace_id": workspace.manifest.workspace_id,
    }
    (workspace.root / "locks/authoring-revision.json").write_bytes(_canonical(revision))
    archive_path = tmp_path / "historical.owworkspace"

    built = build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace, revision=2),
    )
    assert first_records["receipt"].read_bytes() == first_receipt
    assert hashlib.sha256(first_receipt).hexdigest() == first_receipt_digest
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.read("authoring/sessions/SESSION-001/receipt.yaml") == first_receipt
    assert verify_archive(archive_path).semantic_digest == built.semantic_digest

    imported = import_workspace_archive(
        archive_path,
        tmp_path / "imported",
        effective_date=date(2026, 7, 26),
        trust_provider=_trust(workspace, revision=2),
    )
    imported_receipt = (imported.root / "authoring/sessions/SESSION-001/receipt.yaml").read_bytes()
    assert imported_receipt == first_receipt
    assert hashlib.sha256(imported_receipt).hexdigest() == first_receipt_digest


@pytest.mark.contract
def test_session_checkpoints_must_be_unique_and_monotonic(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _install_portable_record_graph(workspace)
    state_payload = (workspace.root / "authoring/session-state.yaml").read_bytes()
    _append_portable_session_bundle(
        workspace,
        session_id="SESSION-002",
        workspace_revision=0,
        session_sequence=2,
        state_payload=state_payload,
        question_id="Q-002",
    )
    revision = {
        "format": "ontowiz-authoring-revision",
        "format_version": 2,
        "revision": 2,
        "session_digest": None,
        "session_sequence": 2,
        "workspace_id": workspace.manifest.workspace_id,
    }
    (workspace.root / "locks/authoring-revision.json").write_bytes(_canonical(revision))

    with pytest.raises(ArchiveBuildError, match="duplicated or non-monotonic"):
        build_workspace_archive(
            workspace,
            tmp_path / "non-monotonic.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace, revision=2),
        )


@pytest.mark.contract
@pytest.mark.parametrize("mismatch", ["evidence-source", "artifact-provenance"])
def test_provenance_mismatch_refuses_build_verify_and_import(
    tmp_path: Path,
    mismatch: str,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    records = _install_portable_record_graph(workspace)
    archive_path = tmp_path / "valid.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace),
    )
    claim = json.loads(records["claim"].read_bytes())
    if mismatch == "evidence-source":
        evidence_binding = dict(claim["evidence_bindings"][0])
        evidence_binding["source_checksum"] = "sha256:" + "9" * 64
        _mutate_portable_record(
            records["claim"],
            evidence_bindings=[evidence_binding],
        )
    else:
        artifact_binding = dict(claim["candidate_artifact_bindings"][0])
        artifact_binding["artifact_id"] = "ART-UNKNOWN"
        _mutate_portable_record(
            records["claim"],
            candidate_artifact_bindings=[artifact_binding],
        )
    forged_claim = records["claim"].read_bytes()

    with pytest.raises(ArchiveBuildError):
        build_workspace_archive(
            workspace,
            tmp_path / "invalid.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )
    _forge_payload(
        archive_path,
        "sources/candidate-claims/SRC-CLAIM-001.yaml",
        forged_claim,
        refresh_manifest=True,
    )
    with pytest.raises(ArchiveVerificationError):
        verify_archive(archive_path)
    destination = tmp_path / "must-not-exist"
    with pytest.raises(ArchiveVerificationError):
        import_workspace_archive(
            archive_path,
            destination,
            effective_date=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )
    assert not destination.exists()


@pytest.mark.contract
def test_historical_content_bindings_survive_same_id_artifact_revision(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    records = _install_portable_record_graph(workspace)
    historical_bytes = {
        name: path.read_bytes()
        for name, path in records.items()
        if name in {"session", "responses", "receipt", "claim", "decision"}
    }
    historical_claim = json.loads(historical_bytes["claim"])
    historical_artifact_digest = historical_claim["candidate_artifact_bindings"][0][
        "payload_digest"
    ]
    artifact_payload, _ = _advance_content_bound_history(workspace)
    current_artifact_digest = "sha256:" + hashlib.sha256(artifact_payload).hexdigest()
    assert historical_artifact_digest != current_artifact_digest

    archive_path = tmp_path / "retained-history.owworkspace"
    built = build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace, revision=2),
    )
    for name, payload in historical_bytes.items():
        assert records[name].read_bytes() == payload
    assert verify_archive(archive_path).semantic_digest == built.semantic_digest

    imported = import_workspace_archive(
        archive_path,
        tmp_path / "imported-history",
        effective_date=date(2026, 7, 26),
        trust_provider=_trust(workspace, revision=2),
    )
    for name, payload in historical_bytes.items():
        relative = records[name].relative_to(workspace.root)
        assert (imported.root / relative).read_bytes() == payload


@pytest.mark.contract
def test_historical_digest_substitution_refuses_build_verify_and_import(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    records = _install_portable_record_graph(workspace)
    _advance_content_bound_history(workspace)
    archive_path = tmp_path / "valid-history.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace, revision=2),
    )

    claim = json.loads(records["claim"].read_bytes())
    artifact_binding = dict(claim["candidate_artifact_bindings"][0])
    artifact_binding["payload_digest"] = "sha256:" + "f" * 64
    _mutate_portable_record(
        records["claim"],
        candidate_artifact_bindings=[artifact_binding],
    )
    substituted_claim = records["claim"].read_bytes()
    with pytest.raises(ArchiveBuildError, match="portable receipt"):
        build_workspace_archive(
            workspace,
            tmp_path / "substituted.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace, revision=2),
        )

    _forge_payload(
        archive_path,
        "sources/candidate-claims/SRC-CLAIM-001.yaml",
        substituted_claim,
        refresh_manifest=True,
    )
    with pytest.raises(ArchiveVerificationError, match="portable receipt"):
        verify_archive(archive_path)
    destination = tmp_path / "substitution-must-not-exist"
    with pytest.raises(ArchiveVerificationError, match="portable receipt"):
        import_workspace_archive(
            archive_path,
            destination,
            effective_date=date(2026, 7, 26),
            trust_provider=_trust(workspace, revision=2),
        )
    assert not destination.exists()


@pytest.mark.contract
def test_current_same_id_artifact_mismatch_refuses_build_verify_and_import(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path / "workspace")
    _install_portable_record_graph(workspace)
    archive_path = tmp_path / "valid-current.owworkspace"
    build_workspace_archive(
        workspace,
        archive_path,
        source_profile="referenced",
        as_of=date(2026, 7, 26),
        trust_provider=_trust(workspace),
    )

    artifact_path = workspace.root / "pack/scope/ART-001.yaml"
    artifact = json.loads(artifact_path.read_bytes())
    artifact["definition"] = "A current same-ID rewrite not bound by the live record."
    artifact_payload = _canonical(artifact)
    artifact_path.write_bytes(artifact_payload)
    pack_path = workspace.root / "pack/pack.yaml"
    pack = json.loads(pack_path.read_bytes())
    pack["artifact_digests"][0]["digest"] = "sha256:" + hashlib.sha256(artifact_payload).hexdigest()
    pack_payload = _canonical(pack)
    pack_path.write_bytes(pack_payload)

    with pytest.raises(ArchiveBuildError, match="current portable session content binding"):
        build_workspace_archive(
            workspace,
            tmp_path / "current-mismatch.owworkspace",
            source_profile="referenced",
            as_of=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )
    _forge_payload(
        archive_path,
        "pack/scope/ART-001.yaml",
        artifact_payload,
        refresh_manifest=True,
    )
    _forge_payload(
        archive_path,
        "pack/pack.yaml",
        pack_payload,
        refresh_manifest=True,
    )
    with pytest.raises(
        ArchiveVerificationError,
        match="current portable session content binding",
    ):
        verify_archive(archive_path)
    destination = tmp_path / "current-mismatch-must-not-exist"
    with pytest.raises(
        ArchiveVerificationError,
        match="current portable session content binding",
    ):
        import_workspace_archive(
            archive_path,
            destination,
            effective_date=date(2026, 7, 26),
            trust_provider=_trust(workspace),
        )
    assert not destination.exists()
