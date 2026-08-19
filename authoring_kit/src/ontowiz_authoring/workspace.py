"""Strict local workspace initialization and loading."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ontowiz_spec import (
    SCHEMA_REVISION,
    SCHEMA_TARGET,
    ArchiveEntry,
    CandidatePackManifest,
    PublicSuite,
    SourceProfile,
    SourceRecord,
    WorkspaceManifest,
)

_MANIFEST_PATH: Literal["workspace.yaml"] = "workspace.yaml"
_SOURCE_REGISTER_PATH: Literal["sources/source-register.yaml"] = "sources/source-register.yaml"
_SESSION_STATE_PATH: Literal["authoring/session-state.yaml"] = "authoring/session-state.yaml"
_PACK_MANIFEST_PATH: Literal["pack/pack.yaml"] = "pack/pack.yaml"
_INVENTORY_PATH = "locks/workspace-inventory.json"
_CONTROLLED_DIRECTORIES = tuple(
    sorted(
        {
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
    )
)
_CONTROLLED_FILES = tuple(
    sorted(
        {
            _MANIFEST_PATH,
            _SOURCE_REGISTER_PATH,
            _SESSION_STATE_PATH,
            _PACK_MANIFEST_PATH,
            _INVENTORY_PATH,
        }
    )
)
_SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"
_MAX_CONTROL_FILE_BYTES = 1_048_576
_DYNAMIC_DIRECTORY_PATTERNS = (
    r"^authoring/sessions/[A-Za-z0-9][A-Za-z0-9_-]*$",
    r"^locks/transactions$",
)
_DYNAMIC_FILE_PATTERNS = (
    r"^sources/inbox/[A-Za-z0-9][A-Za-z0-9._-]*$",
    r"^sources/extracted/[A-Za-z0-9][A-Za-z0-9_-]{0,127}\.json$",
    r"^sources/candidate-claims/[A-Za-z0-9][A-Za-z0-9_-]{0,127}\.yaml$",
    r"^authoring/sessions/[A-Za-z0-9][A-Za-z0-9_-]*/(?:session|questions|responses|receipt)\.yaml$",
    r"^authoring/proposals/DELTA-[A-Za-z0-9][A-Za-z0-9_-]*\.yaml$",
    r"^authoring/decisions/DDR-[A-Za-z0-9][A-Za-z0-9_-]*\.yaml$",
    r"^pack/(?:scope|ontology|metrics|methods|policies|retrieval|workflows|tools|evaluations|governance)/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:yaml|json|md)$",
    r"^reports/(?:validation|semantic-findings|readiness)\.json$",
    r"^build/(?:context-model\.json|explorer\.html)$",
    r"^dist/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:owworkspace|owpack)$",
    r"^locks/authoring\.lock$",
    r"^locks/authoring-authority\.json$",
    r"^locks/authoring-revision\.json$",
    r"^locks/source-material-bindings\.json$",
    r"^locks/transactions/(?:DELTA-[A-Za-z0-9][A-Za-z0-9_-]*|TX-[0-9a-f]{32})(?:\.journal|-[0-9]{2}\.(?:stage|before))$",
)


class WorkspaceError(RuntimeError):
    """Base error for the local authoring workspace boundary."""


class WorkspaceConflictError(WorkspaceError):
    """Raised when initialization would overwrite existing state."""


class WorkspaceValidationError(WorkspaceError):
    """Raised when workspace state is incomplete, unsupported, or inconsistent."""


class WorkspaceStatus(BaseModel):
    """Validated summary suitable for adapter display."""

    workspace_id: str
    source_profile: str
    owner_roles: tuple[str, ...]
    archetypes: tuple[str, ...]
    controlled_file_count: int = Field(ge=0)
    directory_count: int = Field(ge=0)
    manifest_sha256: str = Field(pattern=_SHA256_PATTERN)

    model_config = ConfigDict(extra="forbid", frozen=True)


class _WorkspaceInventory(BaseModel):
    inventory_version: Literal[1]
    manifest_path: Literal["workspace.yaml"]
    manifest_bytes: int = Field(ge=1, le=_MAX_CONTROL_FILE_BYTES)
    manifest_sha256: str = Field(pattern=_SHA256_PATTERN)
    directories: tuple[str, ...]
    files: tuple[str, ...]

    model_config = ConfigDict(extra="forbid", frozen=True)


class _SourceRegister(BaseModel):
    format: Literal["ontowiz-source-register"]
    format_version: Literal[1]
    sources: tuple[SourceRecord, ...] = ()

    model_config = ConfigDict(extra="forbid", frozen=True)


class _SessionState(BaseModel):
    format: Literal["ontowiz-authoring-session-state"]
    format_version: Literal[1]
    stage: Literal["discover", "scenario", "challenge", "ratify"]
    last_delta_id: str | None = None
    open_question_ids: tuple[str, ...] = ()
    next_mission: Literal["discover", "scenario", "challenge", "ratify"]

    model_config = ConfigDict(extra="forbid", frozen=True)


_ModelT = TypeVar("_ModelT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class Workspace:
    """A fully validated authoring workspace."""

    root: Path
    manifest: WorkspaceManifest
    _manifest_sha256: str

    @classmethod
    def initialize(
        cls,
        root: str | Path,
        *,
        workspace_id: str,
        owner_roles: Sequence[str],
        archetypes: Sequence[str],
        source_profile: SourceProfile = SourceProfile.REFERENCED,
        allow_existing_empty: bool = False,
    ) -> Workspace:
        """Create a workspace transactionally or return an identical valid workspace."""
        target = Path(root).absolute()
        manifest = _build_manifest(
            workspace_id=workspace_id,
            owner_roles=owner_roles,
            archetypes=archetypes,
            source_profile=source_profile,
        )
        target_exists = os.path.lexists(target)
        replace_empty = False

        if target_exists:
            if _is_plain_empty_directory(target):
                if not allow_existing_empty:
                    raise WorkspaceConflictError(
                        f"existing empty target requires allow_existing_empty=True: {target}"
                    )
                replace_empty = True
            else:
                try:
                    existing = cls.open(target)
                except WorkspaceValidationError as exc:
                    raise WorkspaceConflictError(
                        f"target contains non-workspace or invalid state: {target}"
                    ) from exc
                if existing.manifest == manifest:
                    return existing
                raise WorkspaceConflictError(
                    f"target contains a workspace with a different manifest: {target}"
                )

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise WorkspaceConflictError(
                f"cannot create workspace parent: {target.parent}"
            ) from exc

        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.owak-", dir=target.parent))
        try:
            _populate_staging(staging, manifest)
            cls.open(staging)
            if replace_empty:
                try:
                    target.rmdir()
                except OSError as exc:
                    raise WorkspaceConflictError(
                        f"existing target is no longer safely empty: {target}"
                    ) from exc
            try:
                os.replace(staging, target)
            except OSError as exc:
                raise WorkspaceConflictError(
                    f"cannot install workspace atomically: {target}"
                ) from exc
        finally:
            if staging.exists():
                shutil.rmtree(staging)

        return cls.open(target)

    @classmethod
    def open(cls, root: str | Path) -> Workspace:
        """Load a workspace only after validating its exact controlled state."""
        target = Path(root).absolute()
        directories, files = _scan_workspace(target)
        _validate_workspace_inventory(directories, files)

        inventory_bytes = _read_control_file(target / _INVENTORY_PATH)
        try:
            inventory = _WorkspaceInventory.model_validate_json(inventory_bytes)
        except (ValidationError, ValueError) as exc:
            raise WorkspaceValidationError("invalid declared inventory") from exc
        if _canonical_json(inventory.model_dump(mode="json")) != inventory_bytes:
            raise WorkspaceValidationError("inventory is not canonical JSON")
        if inventory.directories != _CONTROLLED_DIRECTORIES or inventory.files != _CONTROLLED_FILES:
            raise WorkspaceValidationError("declared inventory does not match workspace contract")

        manifest_bytes = _read_control_file(target / inventory.manifest_path)
        manifest_digest = _sha256(manifest_bytes)
        if (
            len(manifest_bytes) != inventory.manifest_bytes
            or manifest_digest != inventory.manifest_sha256
        ):
            raise WorkspaceValidationError("workspace manifest drift")
        try:
            manifest = WorkspaceManifest.model_validate_json(manifest_bytes)
        except (ValidationError, ValueError) as exc:
            raise WorkspaceValidationError("invalid workspace manifest") from exc
        if _canonical_json(manifest.model_dump(mode="json")) != manifest_bytes:
            raise WorkspaceValidationError("workspace manifest is not canonical JSON")
        if manifest.contains_protected_evaluations:
            raise WorkspaceValidationError("protected evaluations are forbidden")

        _load_canonical_model(target / _SOURCE_REGISTER_PATH, _SourceRegister)
        _load_canonical_model(target / _SESSION_STATE_PATH, _SessionState)
        pack_manifest = _load_canonical_model(
            target / _PACK_MANIFEST_PATH,
            CandidatePackManifest,
        )
        if pack_manifest.pack_id != manifest.workspace_id:
            raise WorkspaceValidationError("candidate pack id differs from workspace id")

        return cls(root=target, manifest=manifest, _manifest_sha256=manifest_digest)

    def status(self) -> WorkspaceStatus:
        """Return a deterministic summary of already validated state."""
        return WorkspaceStatus(
            workspace_id=self.manifest.workspace_id,
            source_profile=self.manifest.source_profile.value,
            owner_roles=self.manifest.owner_roles,
            archetypes=self.manifest.archetypes,
            controlled_file_count=len(_CONTROLLED_FILES),
            directory_count=len(_CONTROLLED_DIRECTORIES),
            manifest_sha256=self._manifest_sha256,
        )


def _load_canonical_model(path: Path, model_type: type[_ModelT]) -> _ModelT:
    payload = _read_control_file(path)
    try:
        model = model_type.model_validate_json(payload)
    except (ValidationError, ValueError) as exc:
        raise WorkspaceValidationError(f"invalid controlled file: {path.name}") from exc
    if _canonical_json(model.model_dump(mode="json")) != payload:
        raise WorkspaceValidationError(f"controlled file is not canonical JSON: {path.name}")
    return model


def _build_manifest(
    *,
    workspace_id: str,
    owner_roles: Sequence[str],
    archetypes: Sequence[str],
    source_profile: SourceProfile,
) -> WorkspaceManifest:
    if isinstance(owner_roles, str) or isinstance(archetypes, str):
        raise WorkspaceValidationError("owner_roles and archetypes must be sequences, not strings")
    try:
        return WorkspaceManifest(
            format="ontowiz-authoring-workspace",
            format_version=1,
            schema_target=cast(Literal["ontowiz-spec/vNext-min"], SCHEMA_TARGET),
            schema_revision=cast(Literal[1], SCHEMA_REVISION),
            workspace_id=workspace_id,
            owner_roles=tuple(owner_roles),
            archetypes=tuple(archetypes),
            source_profile=source_profile,
            adapter_neutral=True,
            contains_protected_evaluations=False,
        )
    except ValidationError as exc:
        raise WorkspaceValidationError("invalid workspace initialization request") from exc


def _populate_staging(staging: Path, manifest: WorkspaceManifest) -> None:
    for relative in _CONTROLLED_DIRECTORIES:
        (staging / relative).mkdir(parents=True, exist_ok=True)

    manifest_bytes = _canonical_json(manifest.model_dump(mode="json"))
    source_register = _SourceRegister(
        format="ontowiz-source-register",
        format_version=1,
    )
    session_state = _SessionState(
        format="ontowiz-authoring-session-state",
        format_version=1,
        stage="discover",
        next_mission="discover",
    )
    pack_manifest = CandidatePackManifest(
        format="ontowiz-candidate-pack",
        format_version=1,
        package_kind="candidate",
        schema_target="ontowiz-spec/vNext-min",
        schema_revision=1,
        pack_id=manifest.workspace_id,
        pack_version="0.1.0",
        production_eligible=False,
        releasable=False,
        contains_protected_evaluations=False,
        artifact_digests=(),
        public_evaluation_suites=(PublicSuite.DEV, PublicSuite.REGRESSION),
    )
    inventory = _WorkspaceInventory(
        inventory_version=1,
        manifest_path=_MANIFEST_PATH,
        manifest_bytes=len(manifest_bytes),
        manifest_sha256=_sha256(manifest_bytes),
        directories=_CONTROLLED_DIRECTORIES,
        files=_CONTROLLED_FILES,
    )
    controlled_payloads = {
        _MANIFEST_PATH: manifest_bytes,
        _SOURCE_REGISTER_PATH: _canonical_json(source_register.model_dump(mode="json")),
        _SESSION_STATE_PATH: _canonical_json(session_state.model_dump(mode="json")),
        _PACK_MANIFEST_PATH: _canonical_json(pack_manifest.model_dump(mode="json")),
        _INVENTORY_PATH: _canonical_json(inventory.model_dump(mode="json")),
    }
    for relative_path in sorted(controlled_payloads):
        _atomic_write(staging / relative_path, controlled_payloads[relative_path])


def initialize_workspace(
    root: str | Path,
    *,
    workspace_id: str,
    owner_roles: Sequence[str],
    archetypes: Sequence[str],
    source_profile: SourceProfile = SourceProfile.REFERENCED,
    allow_existing_empty: bool = False,
) -> Workspace:
    return Workspace.initialize(
        root,
        workspace_id=workspace_id,
        owner_roles=owner_roles,
        archetypes=archetypes,
        source_profile=source_profile,
        allow_existing_empty=allow_existing_empty,
    )


def load_workspace(root: str | Path) -> Workspace:
    return Workspace.open(root)


def validate_workspace(root: str | Path) -> None:
    Workspace.open(root)


def workspace_status(root: str | Path) -> WorkspaceStatus:
    return Workspace.open(root).status()


def _canonical_json(value: object) -> bytes:
    serialized = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{os.urandom(16).hex()}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise WorkspaceError(f"cannot persist controlled file: {path.name}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if os.path.lexists(temporary):
            temporary.unlink()


def _read_control_file(path: Path) -> bytes:
    _ensure_plain_file(path)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise WorkspaceValidationError(f"cannot read controlled file: {path.name}") from exc
    if not payload or len(payload) > _MAX_CONTROL_FILE_BYTES:
        raise WorkspaceValidationError(f"controlled file has invalid size: {path.name}")
    return payload


def _scan_workspace(root: Path) -> tuple[set[str], set[str]]:
    _ensure_plain_directory(root, label="workspace root")
    directories: set[str] = set()
    files: set[str] = set()
    casefolded_paths: dict[str, str] = {}
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name)
        except OSError as exc:
            raise WorkspaceValidationError(
                f"cannot inspect workspace directory: {current}"
            ) from exc
        for entry in entries:
            relative = Path(entry.path).relative_to(root).as_posix()
            folded = relative.casefold()
            previous = casefolded_paths.get(folded)
            if previous is not None and previous != relative:
                raise WorkspaceValidationError(
                    f"case-insensitive workspace path collision: {previous}, {relative}"
                )
            casefolded_paths[folded] = relative
            try:
                entry_stat = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise WorkspaceValidationError(
                    f"cannot inspect workspace entry: {relative}"
                ) from exc
            if entry.is_symlink() or _is_reparse(entry_stat):
                raise WorkspaceValidationError(f"unsupported linked entry: {relative}")
            if stat.S_ISDIR(entry_stat.st_mode):
                directories.add(relative)
                pending.append(Path(entry.path))
            elif stat.S_ISREG(entry_stat.st_mode):
                files.add(relative)
            else:
                raise WorkspaceValidationError(f"unsupported workspace entry: {relative}")
    return directories, files


def _validate_workspace_inventory(directories: set[str], files: set[str]) -> None:
    required_directories = set(_CONTROLLED_DIRECTORIES)
    required_files = set(_CONTROLLED_FILES)
    if not required_directories.issubset(directories) or not required_files.issubset(files):
        raise WorkspaceValidationError("workspace filesystem inventory mismatch")

    for relative in sorted(directories - required_directories):
        if not _matches_any(relative, _DYNAMIC_DIRECTORY_PATTERNS):
            raise WorkspaceValidationError(f"unsupported workspace directory: {relative}")
        _validate_portable_path(f"{relative}/placeholder")

    for relative in sorted(files - required_files):
        if not _matches_any(relative, _DYNAMIC_FILE_PATTERNS):
            raise WorkspaceValidationError(f"unsupported workspace file: {relative}")
        _validate_portable_path(relative)


def _matches_any(relative: str, patterns: tuple[str, ...]) -> bool:
    return any(re.fullmatch(pattern, relative) is not None for pattern in patterns)


def _validate_portable_path(relative: str) -> None:
    try:
        ArchiveEntry(
            path=relative,
            role="workspace-content",
            media_type="application/octet-stream",
            byte_count=0,
            sha256="sha256:" + "0" * 64,
        )
    except ValidationError as exc:
        raise WorkspaceValidationError(f"non-portable workspace path: {relative}") from exc


def _is_plain_empty_directory(path: Path) -> bool:
    try:
        _ensure_plain_directory(path, label="existing target")
        with os.scandir(path) as entries:
            return next(entries, None) is None
    except WorkspaceValidationError as exc:
        raise WorkspaceConflictError(str(exc)) from exc
    except OSError as exc:
        raise WorkspaceConflictError(f"cannot inspect existing target: {path}") from exc


def _ensure_plain_directory(path: Path, *, label: str) -> None:
    try:
        path_stat = os.lstat(path)
    except OSError as exc:
        raise WorkspaceValidationError(f"{label} is missing or unreadable: {path}") from exc
    if stat.S_ISLNK(path_stat.st_mode) or _is_reparse(path_stat):
        raise WorkspaceValidationError(f"{label} cannot be a symlink or reparse point: {path}")
    if not stat.S_ISDIR(path_stat.st_mode):
        raise WorkspaceValidationError(f"{label} is not a directory: {path}")


def _ensure_plain_file(path: Path) -> None:
    try:
        path_stat = os.lstat(path)
    except OSError as exc:
        raise WorkspaceValidationError(f"controlled file is missing: {path.name}") from exc
    if (
        stat.S_ISLNK(path_stat.st_mode)
        or _is_reparse(path_stat)
        or not stat.S_ISREG(path_stat.st_mode)
    ):
        raise WorkspaceValidationError(f"controlled file is unsupported: {path.name}")


def _is_reparse(path_stat: os.stat_result) -> bool:
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(path_stat, "st_file_attributes", 0)
    return bool(reparse_flag and file_attributes & reparse_flag)
