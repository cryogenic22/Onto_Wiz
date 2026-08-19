from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from ontowiz_authoring import (
    Workspace,
    WorkspaceConflictError,
    WorkspaceValidationError,
)


def _initialize(target: Path, *, workspace_id: str = "brand-variance") -> Workspace:
    return Workspace.initialize(
        target,
        workspace_id=workspace_id,
        owner_roles=("steward", "brand_owner", "approver"),
        archetypes=("enterprise_core", "brand_analytics"),
    )


def _tree_digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _inventory_path(root: Path) -> Path:
    return root / "locks" / "workspace-inventory.json"


@pytest.mark.contract
def test_workspace_round_trip_and_status(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    created = _initialize(root)
    opened = Workspace.open(root)

    assert opened.manifest == created.manifest
    assert opened.root == root
    assert opened.status().model_dump(mode="json") == {
        "workspace_id": "brand-variance",
        "source_profile": "referenced",
        "owner_roles": ["steward", "brand_owner", "approver"],
        "archetypes": ["enterprise_core", "brand_analytics"],
        "controlled_file_count": 5,
        "directory_count": 23,
        "manifest_sha256": created.status().manifest_sha256,
    }


@pytest.mark.contract
def test_initialization_is_deterministic_and_same_request_is_idempotent(tmp_path: Path) -> None:
    first = _initialize(tmp_path / "first")
    second = _initialize(tmp_path / "second")
    repeated = _initialize(first.root)

    assert (first.root / "workspace.yaml").read_bytes() == (
        second.root / "workspace.yaml"
    ).read_bytes()
    assert _inventory_path(first.root).read_bytes() == _inventory_path(second.root).read_bytes()
    assert repeated.manifest == first.manifest


@pytest.mark.contract
def test_existing_empty_target_requires_explicit_permission(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    with pytest.raises(WorkspaceConflictError, match="existing empty"):
        _initialize(root)

    created = Workspace.initialize(
        root,
        workspace_id="brand-variance",
        owner_roles=("steward",),
        archetypes=("enterprise_core",),
        allow_existing_empty=True,
    )
    assert created.root == root


@pytest.mark.contract
def test_nonempty_target_or_different_manifest_is_never_overwritten(tmp_path: Path) -> None:
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    sentinel = occupied / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(WorkspaceConflictError):
        _initialize(occupied)
    assert sentinel.read_text(encoding="utf-8") == "keep"

    root = tmp_path / "workspace"
    _initialize(root)
    with pytest.raises(WorkspaceConflictError, match="different manifest"):
        _initialize(root, workspace_id="other-workspace")


@pytest.mark.contract
@pytest.mark.parametrize(
    "relative_path",
    (
        "pack/ontology",
        "workspace.yaml",
        "authoring/proposals",
    ),
)
def test_missing_controlled_entry_is_rejected(tmp_path: Path, relative_path: str) -> None:
    root = tmp_path / "workspace"
    _initialize(root)
    target = root / relative_path
    if target.is_dir():
        target.rmdir()
    else:
        target.unlink()

    with pytest.raises(WorkspaceValidationError, match="inventory mismatch"):
        Workspace.open(root)


@pytest.mark.contract
def test_extra_file_and_traversal_inventory_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    _initialize(root)
    extra = root / "rogue.txt"
    extra.write_text("unexpected", encoding="utf-8")

    with pytest.raises(WorkspaceValidationError, match="unsupported workspace file"):
        Workspace.open(root)

    extra.unlink()
    inventory = json.loads(_inventory_path(root).read_text(encoding="utf-8"))
    inventory["files"].append("../outside.json")
    _inventory_path(root).write_text(
        json.dumps(inventory, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(WorkspaceValidationError, match="declared inventory"):
        Workspace.open(root)


@pytest.mark.contract
def test_manifest_tamper_invalid_json_and_protected_declaration_are_rejected(
    tmp_path: Path,
) -> None:
    drifted = tmp_path / "drifted"
    _initialize(drifted)
    manifest_path = drifted / "workspace.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["workspace_id"] = "tampered"
    manifest_path.write_text(
        json.dumps(manifest, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(WorkspaceValidationError, match="manifest drift"):
        Workspace.open(drifted)

    invalid = tmp_path / "invalid"
    _initialize(invalid)
    (invalid / "workspace.yaml").write_text("{", encoding="utf-8")
    with pytest.raises(WorkspaceValidationError, match="manifest drift"):
        Workspace.open(invalid)

    protected = tmp_path / "protected"
    _initialize(protected)
    manifest_path = protected / "workspace.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["contains_protected_evaluations"] = True
    payload = (json.dumps(manifest, separators=(",", ":"), sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(payload)
    inventory = json.loads(_inventory_path(protected).read_text(encoding="utf-8"))
    inventory["manifest_bytes"] = len(payload)
    inventory["manifest_sha256"] = "sha256:" + hashlib.sha256(payload).hexdigest()
    _inventory_path(protected).write_text(
        json.dumps(inventory, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(WorkspaceValidationError, match="invalid workspace manifest"):
        Workspace.open(protected)


@pytest.mark.contract
def test_symlink_or_reparse_like_entry_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    _initialize(root)
    link = root / "pack" / "linked"
    try:
        link.symlink_to(root / "sources", target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(WorkspaceValidationError, match="unsupported linked entry"):
        Workspace.open(root)


@pytest.mark.contract
def test_workspace_creation_never_touches_source_tree(tmp_path: Path) -> None:
    source = tmp_path / "read-only-source"
    source.mkdir()
    sentinel = source / "contract.py"
    sentinel.write_bytes(b"pinned-contract\n")
    before = _tree_digest(source)
    before_stat = sentinel.stat()

    workspace = _initialize(tmp_path / "workspaces" / "brand")

    assert _tree_digest(source) == before
    assert sentinel.stat().st_mtime_ns == before_stat.st_mtime_ns
    assert source not in workspace.root.parents
    assert workspace.root != source


@pytest.mark.contract
def test_noncanonical_control_files_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    _initialize(root)
    inventory = json.loads(_inventory_path(root).read_text(encoding="utf-8"))
    _inventory_path(root).write_text(
        json.dumps(inventory, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(WorkspaceValidationError, match="canonical JSON"):
        Workspace.open(root)


@pytest.mark.contract
def test_root_symlink_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    _initialize(real)
    link = tmp_path / "workspace-link"
    try:
        os.symlink(real, link, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(WorkspaceValidationError, match="workspace root"):
        Workspace.open(link)
