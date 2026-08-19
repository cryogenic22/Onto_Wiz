from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from pydantic import JsonValue

from examples.generate import WorkedSlice, build_brand_slice, build_mr_slice
from ontowiz_authoring import (
    Workspace,
    build_candidate_pack,
    confirm_proposal,
    get_workspace_revision,
    prepare_authoring_intent,
    prepare_confirmation_intent,
    propose_replacement,
    record_evidence,
    register_source,
    verify_archive,
)
from tests.authoring.test_authoring_flow import (
    _evidence,
    _provider,
    _source,
    _TestTrustProvider,
    _workspace,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIRMED_AT = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _register_worked_evidence(
    workspace: Workspace,
    provider: _TestTrustProvider,
    worked: WorkedSlice,
) -> tuple[str, ...]:
    source_ids = {
        source_id
        for artifact in worked.artifacts
        for source_id in artifact.source_document_ids
    }
    evidence_ids = {
        evidence_id
        for artifact in worked.artifacts
        for evidence_id in artifact.evidence_refs
    }
    assert len(source_ids) == len(evidence_ids) == 1
    source_id = next(iter(source_ids))
    evidence_id = next(iter(evidence_ids))
    actor = provider.actor("draft-agent")

    source = _source(id=source_id)
    source_revision = get_workspace_revision(workspace, provider)
    source_intent = prepare_authoring_intent(
        "register_source",
        workspace.manifest.workspace_id,
        source_revision,
        {"source": source.model_dump(mode="json"), "material_path": None},
    )
    register_source(
        workspace,
        source,
        trust=provider.context(actor, source_intent.intent_digest),
        material_path=None,
        expected_revision=source_revision,
    )

    evidence = _evidence(id=evidence_id, source_id=source_id)
    evidence_revision = get_workspace_revision(workspace, provider)
    evidence_intent = prepare_authoring_intent(
        "record_evidence",
        workspace.manifest.workspace_id,
        evidence_revision,
        {
            "evidence": evidence.model_dump(mode="json"),
            "quote_payload": None,
        },
    )
    record_evidence(
        workspace,
        evidence,
        trust=provider.context(actor, evidence_intent.intent_digest),
        quote_payload=None,
        expected_revision=evidence_revision,
    )
    return (evidence_id,)


def _governed_replace(
    workspace: Workspace,
    provider: _TestTrustProvider,
    *,
    delta_id: str,
    target_path: str,
    payload: bytes,
    evidence_ids: Sequence[str],
) -> None:
    target = workspace.root / target_path
    expected_target_digest = _digest(target.read_bytes()) if target.exists() else None
    replacement = cast(Mapping[str, JsonValue], json.loads(payload))
    expected_revision = get_workspace_revision(workspace, provider)
    request = {
        "delta_id": delta_id,
        "target_owner_role": "steward",
        "allowed_confirmer_roles": ["steward"],
        "target_path": target_path,
        "expected_target_digest": expected_target_digest,
        "replacement_body": dict(replacement),
        "evidence_ids": list(evidence_ids),
        "rationale": "Materialize the checked-in public worked example through governance.",
    }
    intent = prepare_authoring_intent(
        "propose",
        workspace.manifest.workspace_id,
        expected_revision,
        request,
    )
    actor = provider.actor("draft-agent")
    propose_replacement(
        workspace,
        trust=provider.context(actor, intent.intent_digest),
        delta_id=delta_id,
        target_owner_role="steward",
        allowed_confirmer_roles=("steward",),
        target_path=target_path,
        expected_target_digest=expected_target_digest,
        replacement_body=replacement,
        evidence_ids=tuple(evidence_ids),
        rationale="Materialize the checked-in public worked example through governance.",
        expected_revision=expected_revision,
    )
    confirmation_revision = get_workspace_revision(workspace, provider)
    confirmation_intent = prepare_confirmation_intent(
        workspace,
        provider,
        delta_id=delta_id,
        confirmed_at=CONFIRMED_AT,
        expected_revision=confirmation_revision,
    )
    confirm_proposal(
        workspace,
        delta_id,
        trust=provider.context(
            actor,
            confirmation_intent.intent_digest,
        ),
        confirmed_at=CONFIRMED_AT,
        expected_revision=confirmation_revision,
    )


@pytest.mark.parametrize("builder", (build_brand_slice, build_mr_slice))
def test_checked_example_materializes_through_governed_public_apis_and_builds(
    builder: Callable[[], WorkedSlice],
    tmp_path: Path,
) -> None:
    worked = builder()
    checked_in_root = REPO_ROOT / "examples" / worked.slug
    pack_payloads = {
        path.relative_to(checked_in_root).as_posix(): path.read_bytes()
        for path in sorted((checked_in_root / "pack").rglob("*"))
        if path.is_file()
    }
    workspace = _workspace(
        tmp_path,
        name=worked.slug,
        workspace_id=worked.manifest.pack_id,
    )
    provider = _provider(workspace)
    evidence_ids = _register_worked_evidence(workspace, provider, worked)
    ordered_paths = [
        *sorted(path for path in pack_payloads if path != "pack/pack.yaml"),
        "pack/pack.yaml",
    ]
    for index, path in enumerate(ordered_paths, start=1):
        _governed_replace(
            workspace,
            provider,
            delta_id=f"DELTA-EXAMPLE-{index:03d}",
            target_path=path,
            payload=pack_payloads[path],
            evidence_ids=evidence_ids,
        )

    output = tmp_path / f"{worked.slug}.owpack"
    built = build_candidate_pack(
        workspace,
        output,
        trust_provider=provider,
    )
    verified = verify_archive(output, expected_format="ontowiz-candidate-pack")

    assert built.archive_sha256 == verified.archive_sha256
    assert {entry.path for entry in verified.manifest.entries} == set(pack_payloads)
    with zipfile.ZipFile(output, "r") as archive:
        for path, payload in pack_payloads.items():
            assert archive.read(path) == payload
