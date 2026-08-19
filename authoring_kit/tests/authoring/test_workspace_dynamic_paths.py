from __future__ import annotations

from pathlib import Path

import pytest

from ontowiz_authoring import Workspace, WorkspaceValidationError


def _workspace(root: Path) -> Workspace:
    return Workspace.initialize(
        root,
        workspace_id="brand-variance",
        owner_roles=("steward", "brand_owner", "approver"),
        archetypes=("enterprise_core", "brand_analytics"),
    )


@pytest.mark.contract
def test_revision_two_dynamic_content_remains_openable_and_resumable(tmp_path: Path) -> None:
    root = _workspace(tmp_path / "workspace").root
    session = root / "authoring" / "sessions" / "20260725-A"
    session.mkdir()

    dynamic_files = {
        "sources/inbox/source.pdf": b"synthetic source bytes",
        "sources/extracted/SRC-001.json": b"{}\n",
        "sources/candidate-claims/SRC-001.yaml": b"{}\n",
        "authoring/sessions/20260725-A/session.yaml": b"{}\n",
        "authoring/sessions/20260725-A/questions.yaml": b"[]\n",
        "authoring/sessions/20260725-A/responses.yaml": b"[]\n",
        "authoring/sessions/20260725-A/receipt.yaml": b"{}\n",
        "authoring/proposals/DELTA-001.yaml": b"{}\n",
        "authoring/decisions/DDR-001.yaml": b"{}\n",
        "pack/ontology/concepts.yaml": b"[]\n",
        "pack/metrics/metrics.json": b"[]\n",
        "pack/policies/no-causal-leap.md": b"# Candidate policy\n",
        "pack/evaluations/dev.json": b"[]\n",
        "reports/validation.json": b"{}\n",
        "reports/semantic-findings.json": b"[]\n",
        "reports/readiness.json": b"{}\n",
        "build/context-model.json": b"{}\n",
        "build/explorer.html": b"<!doctype html>\n",
        "dist/brand-variance.owworkspace": b"synthetic archive",
        "dist/brand-variance.owpack": b"synthetic archive",
    }
    for relative_path, payload in dynamic_files.items():
        (root / relative_path).write_bytes(payload)

    reopened = Workspace.open(root)
    assert reopened.manifest.workspace_id == "brand-variance"
    assert reopened.status().controlled_file_count == 5


@pytest.mark.contract
@pytest.mark.parametrize(
    "relative_path",
    [
        "authoring/sessions/20260725-A/unexpected.yaml",
        "authoring/proposals/not-a-delta.yaml",
        "pack/ontology/café.json",
        "pack/ontology/concepts.exe",
        "sources/extracted/not.a.source.json",
        "dist/candidate.zip",
    ],
)
def test_unrecognized_or_nonportable_dynamic_file_is_rejected(
    tmp_path: Path,
    relative_path: str,
) -> None:
    root = _workspace(tmp_path / "workspace").root
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"content")

    with pytest.raises(WorkspaceValidationError, match="unsupported workspace"):
        Workspace.open(root)


@pytest.mark.contract
def test_unknown_dynamic_directory_is_rejected(tmp_path: Path) -> None:
    root = _workspace(tmp_path / "workspace").root
    (root / "pack" / "ontology" / "nested").mkdir()

    with pytest.raises(WorkspaceValidationError, match="unsupported workspace directory"):
        Workspace.open(root)
