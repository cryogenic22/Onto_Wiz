from __future__ import annotations

import json
from pathlib import Path

from ontowiz_authoring.cli import main


def test_workspace_cli_init_status_and_validate(tmp_path: Path, capsys: object) -> None:
    root = tmp_path / "workspace"
    assert (
        main(
            [
                "workspace",
                "init",
                str(root),
                "--workspace-id",
                "brand-variance",
                "--owner-role",
                "steward",
                "--owner-role",
                "brand_owner",
                "--archetype",
                "enterprise_core",
                "--archetype",
                "brand_analytics",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    initialized = json.loads(captured.out)
    assert initialized["ok"] is True
    assert initialized["status"]["workspace_id"] == "brand-variance"

    assert main(["workspace", "status", str(root)]) == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert json.loads(captured.out)["status"]["controlled_file_count"] == 5

    assert main(["workspace", "validate", str(root)]) == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert json.loads(captured.out)["ok"] is True


def test_workspace_cli_refuses_invalid_state(tmp_path: Path, capsys: object) -> None:
    missing = tmp_path / "missing"
    assert main(["workspace", "validate", str(missing)]) == 4
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    error = json.loads(captured.err)
    assert error["ok"] is False
    assert error["error"]["code"] == "E_WORKSPACE_INVALID"
