from __future__ import annotations

import json
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
def test_revision_two_scaffold_and_typed_seed_files(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path / "workspace")
    root = workspace.root

    expected_directories = {
        "authoring",
        "authoring/decisions",
        "authoring/proposals",
        "authoring/sessions",
        "build",
        "dist",
        "locks",
        "pack",
        "pack/evaluations",
        "pack/governance",
        "pack/methods",
        "pack/metrics",
        "pack/ontology",
        "pack/policies",
        "pack/retrieval",
        "pack/scope",
        "pack/tools",
        "pack/workflows",
        "reports",
        "sources",
        "sources/candidate-claims",
        "sources/extracted",
        "sources/inbox",
    }
    actual_directories = {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir()
    }
    assert actual_directories == expected_directories

    source_register = json.loads(
        (root / "sources" / "source-register.yaml").read_text(encoding="utf-8")
    )
    assert source_register == {
        "format": "ontowiz-source-register",
        "format_version": 1,
        "sources": [],
    }

    session_state = json.loads(
        (root / "authoring" / "session-state.yaml").read_text(encoding="utf-8")
    )
    assert session_state == {
        "format": "ontowiz-authoring-session-state",
        "format_version": 1,
        "last_delta_id": None,
        "next_mission": "discover",
        "open_question_ids": [],
        "stage": "discover",
    }

    pack_manifest = json.loads((root / "pack" / "pack.yaml").read_text(encoding="utf-8"))
    assert pack_manifest["package_kind"] == "candidate"
    assert pack_manifest["pack_id"] == "brand-variance"
    assert pack_manifest["production_eligible"] is False
    assert pack_manifest["releasable"] is False
    assert pack_manifest["contains_protected_evaluations"] is False


@pytest.mark.contract
@pytest.mark.parametrize(
    ("relative_path", "mutation"),
    [
        (
            "sources/source-register.yaml",
            {"format": "ontowiz-source-register", "format_version": 1, "sources": "bad"},
        ),
        (
            "authoring/session-state.yaml",
            {
                "format": "ontowiz-authoring-session-state",
                "format_version": 1,
                "last_delta_id": None,
                "next_mission": "unknown",
                "open_question_ids": [],
                "stage": "discover",
            },
        ),
        (
            "pack/pack.yaml",
            {
                "format": "ontowiz-candidate-pack",
                "format_version": 1,
                "package_kind": "release",
            },
        ),
    ],
)
def test_typed_seed_file_tamper_fails_closed(
    tmp_path: Path,
    relative_path: str,
    mutation: object,
) -> None:
    root = _workspace(tmp_path / "workspace").root
    (root / relative_path).write_text(
        json.dumps(mutation, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(WorkspaceValidationError, match="invalid controlled file"):
        Workspace.open(root)


@pytest.mark.contract
def test_pack_and_workspace_identity_cannot_drift(tmp_path: Path) -> None:
    root = _workspace(tmp_path / "workspace").root
    pack_path = root / "pack" / "pack.yaml"
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    pack["pack_id"] = "other-pack"
    pack_path.write_text(
        json.dumps(pack, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(WorkspaceValidationError, match="pack id differs"):
        Workspace.open(root)
