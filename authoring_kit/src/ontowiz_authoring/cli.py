"""Technical-author and CI entry point for the adapter-neutral core."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from ontowiz_spec import SourceProfile

from .workspace import (
    WorkspaceConflictError,
    WorkspaceError,
    WorkspaceValidationError,
    initialize_workspace,
    validate_workspace,
    workspace_status,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="owak")
    commands = parser.add_subparsers(dest="command", required=True)
    workspace = commands.add_parser("workspace", help="manage an authoring workspace")
    workspace_commands = workspace.add_subparsers(dest="workspace_command", required=True)

    initialize = workspace_commands.add_parser("init", help="initialize a workspace")
    initialize.add_argument("path", type=Path)
    initialize.add_argument("--workspace-id", required=True)
    initialize.add_argument("--owner-role", action="append", required=True)
    initialize.add_argument("--archetype", action="append", required=True)
    initialize.add_argument(
        "--source-profile",
        choices=[profile.value for profile in SourceProfile],
        default=SourceProfile.REFERENCED.value,
    )
    initialize.add_argument("--allow-existing-empty", action="store_true")

    status = workspace_commands.add_parser("status", help="show validated workspace status")
    status.add_argument("path", type=Path)

    validate = workspace_commands.add_parser("validate", help="validate a workspace")
    validate.add_argument("path", type=Path)
    return parser


def _emit(value: object, *, stream: TextIO | None = None) -> None:
    print(
        json.dumps(
            value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ),
        file=sys.stdout if stream is None else stream,
    )


def _run(arguments: argparse.Namespace) -> dict[str, object]:
    if arguments.workspace_command == "init":
        workspace = initialize_workspace(
            arguments.path,
            workspace_id=arguments.workspace_id,
            owner_roles=arguments.owner_role,
            archetypes=arguments.archetype,
            source_profile=SourceProfile(arguments.source_profile),
            allow_existing_empty=arguments.allow_existing_empty,
        )
        return {"ok": True, "status": workspace.status().model_dump(mode="json")}
    if arguments.workspace_command == "status":
        return {"ok": True, "status": workspace_status(arguments.path).model_dump(mode="json")}
    if arguments.workspace_command == "validate":
        validate_workspace(arguments.path)
        return {"ok": True, "validated": str(arguments.path.absolute())}
    raise AssertionError("unreachable workspace command")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        _emit(_run(arguments))
    except WorkspaceConflictError as exc:
        _emit(
            {"ok": False, "error": {"code": "E_WORKSPACE_CONFLICT", "message": str(exc)}},
            stream=sys.stderr,
        )
        return 3
    except WorkspaceValidationError as exc:
        _emit(
            {"ok": False, "error": {"code": "E_WORKSPACE_INVALID", "message": str(exc)}},
            stream=sys.stderr,
        )
        return 4
    except WorkspaceError as exc:
        _emit(
            {"ok": False, "error": {"code": "E_WORKSPACE_IO", "message": str(exc)}},
            stream=sys.stderr,
        )
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
