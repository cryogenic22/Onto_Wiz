"""Deterministic, fail-closed portable OntoWiz archive formats."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import struct
import tempfile
import unicodedata
import zipfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Final, Literal, TypeAlias, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ontowiz_spec import (
    ArchiveEntry,
    ArchiveManifest,
    ArchiveTransferAuthorization,
    CandidateArtifact,
    CandidatePackManifest,
    DecisionContract,
    PortableCandidateArtifactBinding,
    PortableCandidateClaim,
    PortableDecisionRecord,
    PortableDeltaBinding,
    PortableEvidenceBinding,
    PortableRecordDigestBinding,
    PortableSessionQuestions,
    PortableSessionReceipt,
    PortableSessionRecord,
    PortableSessionResponse,
    PortableSessionResponses,
    PortableSourceBinding,
    PublicEvalCase,
    SourceRecord,
    WorkspaceManifest,
)

from .authoring import (
    AuthoringError,
    AuthoringTrustProvider,
    locked_authoring_archive_snapshot,
)
from .explorer import (
    CandidateExplorerContext,
    ExplorerContentError,
    build_candidate_explorer_context,
    candidate_explorer_context_bytes,
    render_candidate_explorer,
)
from .workspace import Workspace, WorkspaceError

ArchiveFormat: TypeAlias = Literal[
    "ontowiz-authoring-workspace",
    "ontowiz-candidate-pack",
]
SourceProfile: TypeAlias = Literal["referenced", "embedded"]
WorkspaceRef: TypeAlias = Workspace | str | Path

_CONTROL_MANIFEST = "META-INF/manifest.json"
_CONTROL_DIGEST = "META-INF/manifest.sha256"
_CONTROLS = (_CONTROL_MANIFEST, _CONTROL_DIGEST)
_MAX_ENTRIES: Final[Literal[10_000]] = 10_000
_MAX_ENTRY_BYTES: Final[Literal[67_108_864]] = 67_108_864
_MAX_TOTAL_BYTES: Final[Literal[536_870_912]] = 536_870_912
_FIXED_TIME = (1980, 1, 1, 0, 0, 0)
_UTF8_FLAG = 0x800
_DATA_DESCRIPTOR_FLAG = 0x08
_REGULAR_MODE = stat.S_IFREG | 0o644
_WINDOWS_DEVICES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
_PORTABLE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_FORBIDDEN_WORKSPACE_ROOTS = {
    ".git",
    ".hg",
    ".svn",
    "adapters",
    "build",
    "dist",
    "heldout",
    "reports",
    "runtime",
    "secrets",
    "vault",
}
_REQUIRED_WORKSPACE_FILES = {
    "workspace.yaml",
    "locks/workspace-inventory.json",
    "sources/source-register.yaml",
    "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml",
    "authoring/session-state.yaml",
    "pack/pack.yaml",
}
_WORKSPACE_ALLOWED_ROOTS = {"workspace.yaml", "locks", "sources", "authoring", "pack"}
_PACK_ALLOWED_ROOTS = {"pack"}
_PRIVATE_TOKENS = {
    "heldout",
    "oracle",
    "oracles",
    "private",
    "rubric",
    "rubrics",
    "mapping",
    "mappings",
    "secret",
    "secrets",
}
_TEXT_SUFFIXES = {".json", ".yaml", ".yml", ".md", ".txt", ".csv"}


class ArchiveError(RuntimeError):
    """Base error for portable archive operations."""


class ArchiveBuildError(ArchiveError):
    """The source workspace cannot be safely packaged."""


class ArchiveVerificationError(ArchiveError):
    """The archive envelope or semantic content is invalid."""


class ArchiveImportError(ArchiveError):
    """A verified archive cannot be safely imported."""


class ArchiveConflictError(ArchiveImportError):
    """The import destination contains different content."""


@dataclass(frozen=True, slots=True)
class VerifiedArchive:
    """Immutable verification result; no payload has been extracted."""

    path: Path
    manifest: ArchiveManifest
    manifest_bytes: bytes
    archive_sha256: str

    @property
    def semantic_digest(self) -> str:
        return self.manifest.semantic_digest

    @property
    def format(self) -> ArchiveFormat:
        return cast(ArchiveFormat, self.manifest.format)


class _CanonicalSessionControl(BaseModel):
    format: Literal["ontowiz-authoring-session-state"]
    format_version: Literal[1]
    last_delta_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
    next_mission: Literal["discover", "scenario", "challenge", "ratify"]
    open_question_ids: tuple[str, ...] = ()
    stage: Literal["discover", "scenario", "challenge", "ratify"]

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def question_ids_are_unique_and_ordered(self) -> _CanonicalSessionControl:
        if self.open_question_ids != tuple(sorted(set(self.open_question_ids))):
            raise ValueError("canonical open question ids must be unique and ordered")
        if any(
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", item) is None
            for item in self.open_question_ids
        ):
            raise ValueError("canonical open question id is invalid")
        return self


_PortableModelT = TypeVar("_PortableModelT", bound=BaseModel)
_PortableBoundRecord: TypeAlias = (
    PortableCandidateClaim
    | PortableDecisionRecord
    | PortableSessionQuestions
    | PortableSessionReceipt
    | PortableSessionRecord
    | PortableSessionResponses
)
_ContentBoundPortableRecord: TypeAlias = (
    PortableCandidateClaim | PortableDecisionRecord | PortableSessionResponse
)


class _Utf8ZipInfo(zipfile.ZipInfo):
    def _encodeFilenameFlags(self) -> tuple[bytes, int]:  # noqa: N802
        return self.filename.encode("utf-8"), self.flag_bits | _UTF8_FLAG


def _canonical_json(value: object) -> bytes:
    try:
        serialized = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ArchiveBuildError("value is not canonical JSON") from exc
    return (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _archive_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise ArchiveVerificationError("cannot read archive file") from exc
    return "sha256:" + digest.hexdigest()


def _semantic_digest(manifest: ArchiveManifest) -> str:
    core = manifest.model_dump(mode="json", exclude={"semantic_digest"})
    return _sha256(_canonical_json(core))


def _portable_path(path: str) -> str:
    if (
        not path
        or "\x00" in path
        or "\\" in path
        or unicodedata.normalize("NFC", path) != path
        or path.startswith(("/", "//"))
        or re.match(r"^[A-Za-z]:", path)
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path)
    ):
        raise ArchiveVerificationError(f"unsafe archive path: {path!r}")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ArchiveVerificationError(f"unsafe archive path segment: {path!r}")
    for part in parts:
        if (
            part.endswith((".", " "))
            or not _PORTABLE_COMPONENT.fullmatch(part)
            or part.split(".", 1)[0].upper() in _WINDOWS_DEVICES
        ):
            raise ArchiveVerificationError(f"non-portable archive path: {path!r}")
    normalized = PurePosixPath(*parts).as_posix()
    if normalized != path:
        raise ArchiveVerificationError(f"non-canonical archive path: {path!r}")
    return path


def _safe_source_relative(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ArchiveBuildError("source path escapes workspace") from exc
    try:
        return _portable_path(relative)
    except ArchiveVerificationError as exc:
        raise ArchiveBuildError(str(exc)) from exc


def _plain_file(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ArchiveBuildError(f"cannot inspect workspace path: {path.name}") from exc
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(info, "st_file_attributes", 0)
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or (reparse and attributes & reparse)
        or info.st_nlink != 1
    ):
        raise ArchiveBuildError(f"workspace payload is linked or non-regular: {path.name}")


def _stat_signature(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_nlink,
    )


def _read_pinned_file(path: Path) -> bytes:
    try:
        before = path.lstat()
        _plain_file(path)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
    except (ArchiveBuildError, OSError) as exc:
        raise ArchiveBuildError(f"cannot pin workspace payload: {path.name}") from exc
    try:
        opened_before = os.fstat(descriptor)
        if _stat_signature(opened_before) != _stat_signature(before):
            raise ArchiveBuildError("workspace payload identity changed before read")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        opened_after = os.fstat(descriptor)
        after = path.lstat()
        if _stat_signature(opened_after) != _stat_signature(opened_before) or _stat_signature(
            after
        ) != _stat_signature(opened_before):
            raise ArchiveBuildError("workspace payload changed during pinned read")
        return b"".join(chunks)
    except OSError as exc:
        raise ArchiveBuildError(f"cannot read pinned workspace payload: {path.name}") from exc
    finally:
        os.close(descriptor)


def _normalize_payload(path: str, payload: bytes) -> bytes:
    suffix = PurePosixPath(path).suffix.lower()
    if suffix not in _TEXT_SUFFIXES:
        return payload
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArchiveBuildError(f"declared text payload is not UTF-8: {path}") from exc
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    if suffix in {".json", ".yaml", ".yml"}:
        try:
            value = json.loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ArchiveBuildError(
                f"structured payload is not canonical JSON-compatible: {path}"
            ) from exc
        return _canonical_json(value)
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def _media_type(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    return {
        ".json": "application/json",
        ".yaml": "application/json",
        ".yml": "application/json",
        ".md": "text/markdown; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".csv": "text/csv; charset=utf-8",
        ".html": "text/html; charset=utf-8",
    }.get(suffix, "application/octet-stream")


def _metadata(format_name: ArchiveFormat, path: str) -> tuple[str, str]:
    root = path.split("/", 1)[0]
    if format_name == "ontowiz-authoring-workspace":
        role = {
            "workspace.yaml": "workspace-manifest",
            "locks": "portable-lock-state",
            "sources": "governed-source-state",
            "authoring": "authoring-state",
            "pack": "candidate-pack-state",
        }[root]
    else:
        role = {
            "schema": "public-schema",
            "pack": "candidate-pack",
            "evaluations": "public-evaluation",
            "provenance": "public-provenance",
            "receipts": "public-receipt",
        }[root]
    return role, _media_type(path)


def _base_manifest(
    format_name: ArchiveFormat,
    entries: tuple[ArchiveEntry, ...],
    transfer_authorization: ArchiveTransferAuthorization | None,
) -> ArchiveManifest:
    draft = ArchiveManifest(
        envelope_version=1,
        format=format_name,
        format_version=1,
        schema_target="ontowiz-spec/vNext-min",
        schema_revision=1,
        zip_compression="stored",
        canonical_json="RFC8785-subset:UTF-8,NFC,sorted-keys,no-whitespace",
        fixed_timestamp="1980-01-01T00:00:00Z",
        max_entries=_MAX_ENTRIES,
        max_entry_bytes=_MAX_ENTRY_BYTES,
        max_total_bytes=_MAX_TOTAL_BYTES,
        entries=entries,
        transfer_authorization=transfer_authorization,
        semantic_digest="sha256:" + "0" * 64,
    )
    return draft.model_copy(update={"semantic_digest": _semantic_digest(draft)})


def _entry(path: str, payload: bytes, format_name: ArchiveFormat) -> ArchiveEntry:
    role, media_type = _metadata(format_name, path)
    return ArchiveEntry(
        path=path,
        role=role,
        media_type=media_type,
        byte_count=len(payload),
        sha256=_sha256(payload),
    )


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = _Utf8ZipInfo(name, _FIXED_TIME)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = _REGULAR_MODE << 16
    info.internal_attr = 0
    info.flag_bits = _UTF8_FLAG
    info.extra = b""
    info.comment = b""
    return info


def _write_archive(
    out: Path,
    manifest: ArchiveManifest,
    payloads: Mapping[str, bytes],
) -> VerifiedArchive:
    manifest_bytes = _canonical_json(manifest.model_dump(mode="json"))
    digest_bytes = (hashlib.sha256(manifest_bytes).hexdigest() + "\n").encode("ascii")
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_name(f".{out.name}.{os.urandom(16).hex()}.tmp")
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_STORED,
            allowZip64=True,
        ) as archive:
            archive.comment = b""
            archive.writestr(_zip_info(_CONTROL_MANIFEST), manifest_bytes)
            archive.writestr(_zip_info(_CONTROL_DIGEST), digest_bytes)
            for name in sorted(payloads):
                archive.writestr(_zip_info(name), payloads[name])
        os.replace(temporary, out)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ArchiveBuildError("cannot write deterministic archive") from exc
    finally:
        if os.path.lexists(temporary):
            temporary.unlink()
    return verify_archive(out, expected_format=cast(ArchiveFormat, manifest.format))


def _workspace_root(workspace: WorkspaceRef) -> tuple[Workspace, Path]:
    try:
        current = workspace if isinstance(workspace, Workspace) else Workspace.open(workspace)
    except WorkspaceError as exc:
        raise ArchiveBuildError("workspace validation failed") from exc
    return current, current.root.absolute()


def _scan_files(root: Path) -> Iterator[tuple[str, Path]]:
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            children = sorted(current.iterdir(), key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise ArchiveBuildError("cannot enumerate workspace") from exc
        for child in children:
            try:
                info = child.lstat()
            except OSError as exc:
                raise ArchiveBuildError("cannot inspect workspace entry") from exc
            if stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode):
                pending.append(child)
            elif stat.S_ISREG(info.st_mode):
                _plain_file(child)
                yield _safe_source_relative(child, root), child
            else:
                raise ArchiveBuildError(f"linked or special workspace path: {child.name}")


def _load_sources(root: Path) -> dict[str, SourceRecord]:
    path = root / "sources" / "source-register.yaml"
    try:
        data = json.loads(_read_pinned_file(path))
        records = {
            record.id: record
            for record in (SourceRecord.model_validate(item) for item in data["sources"])
        }
    except (OSError, KeyError, TypeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        raise ArchiveBuildError("source register is invalid") from exc
    if len(records) != len(data["sources"]):
        raise ArchiveBuildError("source register contains duplicate ids")
    return records


def _load_bindings(root: Path) -> dict[str, tuple[str, str]]:
    path = root / "locks" / "source-material-bindings.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(_read_pinned_file(path))
        bindings = {
            str(item["source_id"]): (
                str(item["relative_path"]),
                str(item["checksum"]),
            )
            for item in data["bindings"]
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ArchiveBuildError("source material bindings are invalid") from exc
    if len(bindings) != len(data["bindings"]):
        raise ArchiveBuildError("source material bindings contain duplicate ids")
    return bindings


def _canonical_payload_document(path: str, payload: bytes) -> dict[str, object]:
    try:
        body = json.loads(payload)
        if not isinstance(body, dict) or _canonical_json(body) != payload:
            raise ValueError("record is not canonical JSON")
        return body
    except ArchiveBuildError:
        raise
    except (
        RecursionError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise ArchiveBuildError(f"portable record is invalid: {path}") from exc


def _load_canonical_portable_model(
    path: str,
    payload: bytes,
    model_type: type[_PortableModelT],
) -> _PortableModelT:
    try:
        return model_type.model_validate(_canonical_payload_document(path, payload))
    except (TypeError, ValueError, ValidationError) as exc:
        raise ArchiveBuildError(f"portable record is invalid: {path}") from exc


def _portable_payload_index(root: Path) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for relative, path in _scan_files(root):
        if relative.startswith("sources/inbox/") or relative == "locks/authoring.lock":
            continue
        payloads[relative] = _read_pinned_file(path)
    return payloads


def _assert_portable_record_anchor(
    record: _PortableBoundRecord,
    *,
    workspace_id: str,
    workspace_revision: int,
    session_id: str,
    session_sequence: int,
) -> None:
    if (
        record.workspace_id != workspace_id
        or record.workspace_revision != workspace_revision
        or record.session_id != session_id
        or record.session_sequence != session_sequence
    ):
        raise ArchiveBuildError("portable record anchor is stale or belongs elsewhere")


def _assert_content_binding_references(
    *,
    source_bindings: tuple[PortableSourceBinding, ...],
    evidence_bindings: tuple[PortableEvidenceBinding, ...],
    candidate_artifact_bindings: tuple[PortableCandidateArtifactBinding, ...],
    pack_manifest_digest: str,
    expected_pack_manifest_digest: str,
    require_current: bool,
    current_sources: Mapping[str, PortableSourceBinding],
    current_evidence: Mapping[str, PortableEvidenceBinding],
    current_artifacts: Mapping[str, PortableCandidateArtifactBinding],
    artifact_provenance: Mapping[str, tuple[frozenset[str], frozenset[str]]],
) -> None:
    if pack_manifest_digest != expected_pack_manifest_digest:
        raise ArchiveBuildError("portable record pack binding is inconsistent")
    if not require_current:
        return
    cited_sources = frozenset(item.source_id for item in source_bindings)
    cited_evidence = frozenset(item.evidence_id for item in evidence_bindings)
    cited_artifacts = frozenset(item.artifact_id for item in candidate_artifact_bindings)
    if (
        any(current_sources.get(item.source_id) != item for item in source_bindings)
        or any(current_evidence.get(item.evidence_id) != item for item in evidence_bindings)
        or any(
            current_artifacts.get(item.artifact_id) != item for item in candidate_artifact_bindings
        )
        or not cited_artifacts.issubset(artifact_provenance)
        or any(
            artifact_provenance[artifact_id] != (cited_sources, cited_evidence)
            for artifact_id in cited_artifacts
        )
    ):
        raise ArchiveBuildError("current portable content bindings are inconsistent")


def _validate_portable_record_graph(payloads: Mapping[str, bytes]) -> None:
    from .authoring import Proposal, SessionState, _EvidenceDocument, _RevisionState

    try:
        for path in payloads:
            if (
                path.startswith("authoring/sessions/")
                and re.fullmatch(
                    r"authoring/sessions/[A-Za-z0-9][A-Za-z0-9_-]*/"
                    r"(?:session|questions|responses|receipt)\.yaml",
                    path,
                )
                is None
            ):
                raise ArchiveBuildError("unknown portable session record")
            if (
                path.startswith("authoring/decisions/")
                and re.fullmatch(
                    r"authoring/decisions/DDR-[A-Za-z0-9][A-Za-z0-9_-]*\.yaml",
                    path,
                )
                is None
            ):
                raise ArchiveBuildError("unknown portable decision record")
            if (
                path.startswith("sources/candidate-claims/")
                and path != "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml"
                and re.fullmatch(
                    r"sources/candidate-claims/SRC-[A-Za-z0-9][A-Za-z0-9_-]*\.yaml",
                    path,
                )
                is None
            ):
                raise ArchiveBuildError("unknown portable candidate claim")
        workspace_manifest = WorkspaceManifest.model_validate(
            _canonical_payload_document("workspace.yaml", payloads["workspace.yaml"])
        )
        workspace_id = workspace_manifest.workspace_id
        source_body = _canonical_payload_document(
            "sources/source-register.yaml",
            payloads["sources/source-register.yaml"],
        )
        source_items = source_body.get("sources")
        if not isinstance(source_items, list):
            raise ArchiveBuildError("source register is invalid")
        sources: dict[str, SourceRecord] = {}
        current_source_bindings: dict[str, PortableSourceBinding] = {}
        for item in source_items:
            source = SourceRecord.model_validate(item)
            if source.id in sources:
                raise ArchiveBuildError("source register contains duplicate ids")
            sources[source.id] = source
            current_source_bindings[source.id] = PortableSourceBinding(
                source_id=source.id,
                registered_checksum=source.checksum,
                source_record_digest=_sha256(_canonical_json(item)),
            )

        evidence_sources: dict[str, str] = {}
        current_evidence_bindings: dict[str, PortableEvidenceBinding] = {}
        extracted_source_ids: set[str] = set()
        for path in sorted(
            item
            for item in payloads
            if re.fullmatch(r"sources/extracted/SRC-[A-Za-z0-9][A-Za-z0-9_-]*\.json", item)
        ):
            evidence_body = _canonical_payload_document(path, payloads[path])
            document = _EvidenceDocument.model_validate(evidence_body)
            raw_evidence = evidence_body.get("evidence")
            evidence_source = sources.get(document.source_id)
            if (
                evidence_source is None
                or not isinstance(raw_evidence, list)
                or len(raw_evidence) != len(document.evidence)
                or PurePosixPath(path).stem != document.source_id
                or document.source_id in extracted_source_ids
            ):
                raise ArchiveBuildError("extracted evidence source binding is invalid")
            extracted_source_ids.add(document.source_id)
            for evidence, raw_item in zip(document.evidence, raw_evidence, strict=True):
                if (
                    evidence.id in evidence_sources
                    or evidence.source_id != document.source_id
                    or evidence.source_checksum != evidence_source.checksum
                ):
                    raise ArchiveBuildError("extracted evidence cross-reference is invalid")
                evidence_sources[evidence.id] = evidence.source_id
                current_evidence_bindings[evidence.id] = PortableEvidenceBinding(
                    evidence_id=evidence.id,
                    evidence_item_digest=_sha256(_canonical_json(raw_item)),
                    source_id=evidence.source_id,
                    source_checksum=evidence.source_checksum,
                )

        proposals: dict[str, Proposal] = {}
        current_delta_bindings: dict[str, PortableDeltaBinding] = {}
        for path in sorted(
            item
            for item in payloads
            if re.fullmatch(r"authoring/proposals/DELTA-[A-Za-z0-9][A-Za-z0-9_-]*\.yaml", item)
        ):
            proposal = Proposal.model_validate(_canonical_payload_document(path, payloads[path]))
            if (
                proposal.workspace_id != workspace_id
                or PurePosixPath(path).stem != proposal.delta_id
                or proposal.delta_id in proposals
                or not set(proposal.evidence_ids).issubset(evidence_sources)
            ):
                raise ArchiveBuildError("proposal cross-reference is invalid")
            proposals[proposal.delta_id] = proposal
            current_delta_bindings[proposal.delta_id] = PortableDeltaBinding(
                delta_id=proposal.delta_id,
                proposal_digest=_sha256(payloads[path]),
            )
            _validate_candidate_document(
                proposal.target_path,
                _canonical_json(proposal.replacement_body),
            )
            if proposal.status == "confirmed":
                target_payload = payloads.get(proposal.target_path)
                if (
                    proposal.applied_to_digest is None
                    or target_payload is None
                    or _sha256(target_payload) != proposal.applied_to_digest
                ):
                    raise ArchiveBuildError("confirmed proposal target is not exact")

        pack_items = [
            (path, payloads[path]) for path in sorted(payloads) if path.startswith("pack/")
        ]
        artifact_provenance: dict[str, tuple[frozenset[str], frozenset[str]]] = {}
        current_artifact_bindings: dict[str, PortableCandidateArtifactBinding] = {}
        for path, payload in pack_items:
            body = _canonical_payload_document(path, payload)
            pack_document = _validate_candidate_document(path, payload)
            for key, value in _walk_json(body):
                if key not in {"evidence_refs", "source_document_ids"}:
                    continue
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    raise ArchiveBuildError("candidate reference list is invalid")
                known = evidence_sources if key == "evidence_refs" else set(sources)
                if not set(value).issubset(known):
                    raise ArchiveBuildError("candidate document has a dangling reference")
            if isinstance(pack_document, CandidateArtifact):
                artifact_sources = frozenset(pack_document.source_document_ids)
                artifact_evidence = frozenset(pack_document.evidence_refs)
                if pack_document.id in artifact_provenance or any(
                    evidence_sources[evidence_id] not in artifact_sources
                    for evidence_id in artifact_evidence
                ):
                    raise ArchiveBuildError("candidate artifact provenance edges are invalid")
                artifact_provenance[pack_document.id] = (
                    artifact_sources,
                    artifact_evidence,
                )
                current_artifact_bindings[pack_document.id] = PortableCandidateArtifactBinding(
                    artifact_id=pack_document.id,
                    payload_digest=_sha256(payload),
                )
        _validate_candidate_inventory_items(iter(pack_items))
        pack_manifest = CandidatePackManifest.model_validate(
            _canonical_payload_document("pack/pack.yaml", payloads["pack/pack.yaml"])
        )
        current_pack_manifest_digest = _sha256(payloads["pack/pack.yaml"])
        declared_artifact_ids = {item.artifact_id for item in pack_manifest.artifact_digests}
        if not set(artifact_provenance).issubset(declared_artifact_ids):
            raise ArchiveBuildError("candidate artifact provenance is undeclared")

        state_payload = payloads["authoring/session-state.yaml"]
        canonical_state = _load_canonical_portable_model(
            "authoring/session-state.yaml",
            state_payload,
            _CanonicalSessionControl,
        )
        if canonical_state.last_delta_id is not None:
            last_proposal = proposals.get(canonical_state.last_delta_id)
            if last_proposal is None or last_proposal.delta_id != canonical_state.last_delta_id:
                raise ArchiveBuildError("canonical session delta is missing or inexact")

        revision_payload = payloads.get("locks/authoring-revision.json")
        revision = (
            _load_canonical_portable_model(
                "locks/authoring-revision.json",
                revision_payload,
                _RevisionState,
            )
            if revision_payload is not None
            else None
        )
        if revision is not None:
            if revision.workspace_id != workspace_id:
                raise ArchiveBuildError("authoring revision belongs to another workspace")
            workspace_revision = revision.revision
            session_sequence = revision.session_sequence
        else:
            workspace_revision = 0
            session_sequence = 0

        session_paths: dict[str, dict[str, str]] = {}
        for path in payloads:
            match = re.fullmatch(
                r"authoring/sessions/([A-Za-z0-9][A-Za-z0-9_-]*)/"
                r"(session|questions|responses|receipt)\.yaml",
                path,
            )
            if match is not None:
                session_paths.setdefault(match.group(1), {})[match.group(2)] = path

        sessions: dict[str, PortableSessionRecord] = {}
        session_responses: dict[str, PortableSessionResponses] = {}
        session_receipts: dict[str, PortableSessionReceipt] = {}
        all_questions: set[str] = set()
        all_response_ids: set[str] = set()
        session_delta_ids: set[str] = set()
        required_records = {"session", "questions", "responses", "receipt"}
        for session_id, records in sorted(session_paths.items()):
            if session_id == "current":
                if set(records) != {"session"} or revision is None:
                    raise ArchiveBuildError("live current session record set is invalid")
                session_path = records["session"]
                live_session = _load_canonical_portable_model(
                    session_path,
                    payloads[session_path],
                    SessionState,
                )
                if (
                    live_session.workspace_id != workspace_id
                    or live_session.revision != workspace_revision
                    or live_session.sequence != session_sequence
                    or revision.session_digest != _sha256(payloads[session_path])
                    or (
                        live_session.last_delta_id is not None
                        and live_session.last_delta_id not in proposals
                    )
                ):
                    raise ArchiveBuildError("live current session anchor is invalid")
                continue
            if set(records) != required_records:
                raise ArchiveBuildError("portable session record set is incomplete or unknown")
            session_path = records["session"]
            questions_path = records["questions"]
            responses_path = records["responses"]
            receipt_path = records["receipt"]
            session = _load_canonical_portable_model(
                session_path,
                payloads[session_path],
                PortableSessionRecord,
            )
            questions = _load_canonical_portable_model(
                questions_path,
                payloads[questions_path],
                PortableSessionQuestions,
            )
            responses = _load_canonical_portable_model(
                responses_path,
                payloads[responses_path],
                PortableSessionResponses,
            )
            receipt = _load_canonical_portable_model(
                receipt_path,
                payloads[receipt_path],
                PortableSessionReceipt,
            )
            if session_id in sessions:
                raise ArchiveBuildError("portable session id is duplicated")
            sessions[session_id] = session
            session_responses[session_id] = responses
            session_receipts[session_id] = receipt
            bound_records: tuple[_PortableBoundRecord, ...] = (
                session,
                questions,
                responses,
                receipt,
            )
            for record in bound_records:
                _assert_portable_record_anchor(
                    record,
                    workspace_id=workspace_id,
                    workspace_revision=session.workspace_revision,
                    session_id=session_id,
                    session_sequence=session.session_sequence,
                )
            if (
                session.workspace_revision > workspace_revision
                or session.session_sequence > session_sequence
            ):
                raise ArchiveBuildError("portable session checkpoint exceeds high-water")
            current_checkpoint = (
                session.workspace_revision == workspace_revision
                and session.session_sequence == session_sequence
            )
            if current_checkpoint and (
                session.canonical_state_digest != _sha256(state_payload)
                or session.pack_manifest_digest != current_pack_manifest_digest
                or any(
                    current_delta_bindings.get(binding.delta_id) != binding
                    for binding in session.delta_bindings
                )
            ):
                raise ArchiveBuildError("current portable session content binding is invalid")
            if (
                questions.session_record_digest != session.record_digest
                or responses.session_record_digest != session.record_digest
                or receipt.session_record_digest != session.record_digest
                or receipt.questions_record_digest != questions.record_digest
                or receipt.responses_record_digest != responses.record_digest
                or receipt.pack_manifest_digest != session.pack_manifest_digest
            ):
                raise ArchiveBuildError("portable session digest chain is invalid")
            question_ids = tuple(question.id for question in questions.questions)
            response_ids = tuple(response.id for response in responses.responses)
            if (
                session.question_ids != question_ids
                or receipt.question_ids != question_ids
                or receipt.response_ids != response_ids
                or receipt.delta_bindings != session.delta_bindings
            ):
                raise ArchiveBuildError("portable session inventory is not exact")
            known_question_ids = set(question_ids)
            for question_id in question_ids:
                if question_id in all_questions:
                    raise ArchiveBuildError("portable question id is duplicated")
                all_questions.add(question_id)
            for response in responses.responses:
                if response.id in all_response_ids:
                    raise ArchiveBuildError("portable response id is duplicated")
                all_response_ids.add(response.id)
                if response.question_id not in known_question_ids:
                    raise ArchiveBuildError("portable response references an unknown question")
                _assert_content_binding_references(
                    source_bindings=response.source_bindings,
                    evidence_bindings=response.evidence_bindings,
                    candidate_artifact_bindings=response.candidate_artifact_bindings,
                    pack_manifest_digest=response.pack_manifest_digest,
                    expected_pack_manifest_digest=session.pack_manifest_digest,
                    require_current=current_checkpoint,
                    current_sources=current_source_bindings,
                    current_evidence=current_evidence_bindings,
                    current_artifacts=current_artifact_bindings,
                    artifact_provenance=artifact_provenance,
                )
            session_delta_ids.update(binding.delta_id for binding in session.delta_bindings)

        previous_revision = -1
        previous_sequence = -1
        for checkpoint in sorted(
            sessions.values(),
            key=lambda item: item.session_sequence,
        ):
            if (
                checkpoint.workspace_revision <= previous_revision
                or checkpoint.session_sequence <= previous_sequence
            ):
                raise ArchiveBuildError(
                    "portable session checkpoints are duplicated or non-monotonic"
                )
            previous_revision = checkpoint.workspace_revision
            previous_sequence = checkpoint.session_sequence

        for question_id in canonical_state.open_question_ids:
            if question_id not in all_questions:
                raise ArchiveBuildError(
                    "canonical open question lacks exactly one portable question"
                )
        if (
            canonical_state.last_delta_id is not None
            and canonical_state.last_delta_id not in session_delta_ids
        ):
            raise ArchiveBuildError("canonical session delta lacks a portable receipt")

        known_session_ids = set(sessions)
        claims_by_session: dict[str, dict[str, PortableCandidateClaim]] = {}
        claim_ids: set[str] = set()
        omission_path = "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml"
        for path in sorted(
            item
            for item in payloads
            if re.fullmatch(r"sources/candidate-claims/SRC-[A-Za-z0-9][A-Za-z0-9_-]*\.yaml", item)
            and item != omission_path
        ):
            claim = _load_canonical_portable_model(
                path,
                payloads[path],
                PortableCandidateClaim,
            )
            if (
                claim.claim_record_id != PurePosixPath(path).stem
                or claim.claim_record_id in claim_ids
                or claim.session_id not in known_session_ids
            ):
                raise ArchiveBuildError("candidate claim identity binding is invalid")
            claim_ids.add(claim.claim_record_id)
            claim_session = sessions[claim.session_id]
            claims_by_session.setdefault(claim.session_id, {})[claim.claim_record_id] = claim
            _assert_portable_record_anchor(
                claim,
                workspace_id=workspace_id,
                workspace_revision=claim_session.workspace_revision,
                session_id=claim.session_id,
                session_sequence=claim_session.session_sequence,
            )
            _assert_content_binding_references(
                source_bindings=claim.source_bindings,
                evidence_bindings=claim.evidence_bindings,
                candidate_artifact_bindings=claim.candidate_artifact_bindings,
                pack_manifest_digest=claim.pack_manifest_digest,
                expected_pack_manifest_digest=claim_session.pack_manifest_digest,
                require_current=(
                    claim_session.workspace_revision == workspace_revision
                    and claim_session.session_sequence == session_sequence
                ),
                current_sources=current_source_bindings,
                current_evidence=current_evidence_bindings,
                current_artifacts=current_artifact_bindings,
                artifact_provenance=artifact_provenance,
            )

        decisions_by_session: dict[str, dict[str, PortableDecisionRecord]] = {}
        decision_ids: set[str] = set()
        for path in sorted(
            item
            for item in payloads
            if re.fullmatch(r"authoring/decisions/DDR-[A-Za-z0-9][A-Za-z0-9_-]*\.yaml", item)
        ):
            decision = _load_canonical_portable_model(
                path,
                payloads[path],
                PortableDecisionRecord,
            )
            if (
                decision.decision_record_id != PurePosixPath(path).stem
                or decision.decision_record_id in decision_ids
                or decision.session_id not in known_session_ids
            ):
                raise ArchiveBuildError("decision record identity binding is invalid")
            decision_ids.add(decision.decision_record_id)
            decision_session = sessions[decision.session_id]
            decisions_by_session.setdefault(decision.session_id, {})[
                decision.decision_record_id
            ] = decision
            _assert_portable_record_anchor(
                decision,
                workspace_id=workspace_id,
                workspace_revision=decision_session.workspace_revision,
                session_id=decision.session_id,
                session_sequence=decision_session.session_sequence,
            )
            _assert_content_binding_references(
                source_bindings=decision.source_bindings,
                evidence_bindings=decision.evidence_bindings,
                candidate_artifact_bindings=decision.candidate_artifact_bindings,
                pack_manifest_digest=decision.pack_manifest_digest,
                expected_pack_manifest_digest=decision_session.pack_manifest_digest,
                require_current=(
                    decision_session.workspace_revision == workspace_revision
                    and decision_session.session_sequence == session_sequence
                ),
                current_sources=current_source_bindings,
                current_evidence=current_evidence_bindings,
                current_artifacts=current_artifact_bindings,
                artifact_provenance=artifact_provenance,
            )

        for session_id, session in sessions.items():
            receipt = session_receipts[session_id]
            claims = claims_by_session.get(session_id, {})
            decisions = decisions_by_session.get(session_id, {})
            content_records: list[_ContentBoundPortableRecord] = list(
                session_responses[session_id].responses
            )
            content_records.extend(claims.values())
            content_records.extend(decisions.values())
            source_inventory: dict[str, PortableSourceBinding] = {}
            evidence_inventory: dict[str, PortableEvidenceBinding] = {}
            artifact_inventory: dict[str, PortableCandidateArtifactBinding] = {}
            for content_record in content_records:
                for source_binding in content_record.source_bindings:
                    existing_source = source_inventory.get(source_binding.source_id)
                    if existing_source is not None and existing_source != source_binding:
                        raise ArchiveBuildError("portable receipt has conflicting source bindings")
                    source_inventory[source_binding.source_id] = source_binding
                for evidence_binding in content_record.evidence_bindings:
                    existing_evidence = evidence_inventory.get(evidence_binding.evidence_id)
                    if existing_evidence is not None and existing_evidence != evidence_binding:
                        raise ArchiveBuildError(
                            "portable receipt has conflicting evidence bindings"
                        )
                    evidence_inventory[evidence_binding.evidence_id] = evidence_binding
                for artifact_binding in content_record.candidate_artifact_bindings:
                    existing_artifact = artifact_inventory.get(artifact_binding.artifact_id)
                    if existing_artifact is not None and existing_artifact != artifact_binding:
                        raise ArchiveBuildError(
                            "portable receipt has conflicting artifact bindings"
                        )
                    artifact_inventory[artifact_binding.artifact_id] = artifact_binding
            expected_claim_bindings = tuple(
                PortableRecordDigestBinding(
                    record_id=record_id,
                    record_digest=claims[record_id].record_digest,
                )
                for record_id in sorted(claims)
            )
            expected_decision_bindings = tuple(
                PortableRecordDigestBinding(
                    record_id=record_id,
                    record_digest=decisions[record_id].record_digest,
                )
                for record_id in sorted(decisions)
            )
            if (
                receipt.pack_manifest_digest != session.pack_manifest_digest
                or receipt.delta_bindings != session.delta_bindings
                or receipt.source_bindings
                != tuple(source_inventory[key] for key in sorted(source_inventory))
                or receipt.evidence_bindings
                != tuple(evidence_inventory[key] for key in sorted(evidence_inventory))
                or receipt.candidate_artifact_bindings
                != tuple(artifact_inventory[key] for key in sorted(artifact_inventory))
                or receipt.claim_record_bindings != expected_claim_bindings
                or receipt.decision_record_bindings != expected_decision_bindings
            ):
                raise ArchiveBuildError("portable receipt digest inventory is not exact")
    except ArchiveBuildError:
        raise
    except (
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        ValidationError,
        json.JSONDecodeError,
    ) as exc:
        raise ArchiveBuildError("portable record graph validation failed") from exc


def _validate_authoring_cross_references(root: Path, _workspace: Workspace) -> None:
    _validate_portable_record_graph(_portable_payload_index(root))


def _source_payload_policy(
    root: Path,
    *,
    profile: SourceProfile,
    as_of: date,
    target_client_boundary: str | None,
) -> tuple[set[str], bytes]:
    sources = _load_sources(root)
    bindings = _load_bindings(root)
    inbox = {relative for relative, _ in _scan_files(root) if relative.startswith("sources/inbox/")}
    bound_paths: set[str] = set()
    omissions: list[dict[str, object]] = []
    for source_id, (relative, checksum) in sorted(bindings.items()):
        try:
            relative = _portable_path(relative)
        except ArchiveVerificationError as exc:
            raise ArchiveBuildError("material binding path is unsafe") from exc
        if not relative.startswith("sources/inbox/"):
            raise ArchiveBuildError("material binding does not target governed inbox")
        source = sources.get(source_id)
        if source is None or source.checksum != checksum:
            raise ArchiveBuildError("material binding lacks exact source/checksum")
        material = root / Path(*relative.split("/"))
        _plain_file(material)
        payload = _read_pinned_file(material)
        if _sha256(payload) != checksum:
            raise ArchiveBuildError("governed source bytes differ from registered checksum")
        bound_paths.add(relative)
        if profile == "embedded":
            if (
                target_client_boundary is None
                or source.retention_until is None
                or source.client_boundary != target_client_boundary
                or not source.permits_embedding(as_of=as_of)
            ):
                raise ArchiveBuildError(
                    f"source rights do not permit this embedded transfer: {source_id}"
                )
        else:
            omissions.append(
                {
                    "path": relative,
                    "reason": "referenced-profile-governed-source-omission",
                    "sha256": checksum,
                    "source_id": source_id,
                }
            )
    if inbox != bound_paths:
        raise ArchiveBuildError("inbox contains unbound or missing governed source bytes")
    record = _canonical_json(
        {
            "as_of": as_of.isoformat(),
            "format": "ontowiz-source-omissions",
            "format_version": 1,
            "omitted": omissions,
            "source_profile": profile,
            "target_client_boundary": target_client_boundary,
        }
    )
    return bound_paths, record


def _assert_no_pending_transaction(root: Path) -> None:
    transaction_dir = root / "locks" / "transactions"
    if transaction_dir.exists() and any(transaction_dir.iterdir()):
        raise ArchiveBuildError("workspace has a pending authoring transaction")


def _workspace_payloads(
    workspace: WorkspaceRef,
    *,
    source_profile: SourceProfile,
    as_of: date,
    target_client_boundary: str | None,
) -> tuple[Path, dict[str, bytes]]:
    current, root = _workspace_root(workspace)
    _assert_no_pending_transaction(root)
    try:
        _validate_supported_portable_state_paths(root)
    except ArchiveImportError as exc:
        raise ArchiveBuildError(str(exc)) from exc
    _validate_authoring_cross_references(root, current)
    bound_paths, omission = _source_payload_policy(
        root,
        profile=source_profile,
        as_of=as_of,
        target_client_boundary=target_client_boundary,
    )
    payloads: dict[str, bytes] = {}
    omission_path = "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml"
    for relative, file_path in _scan_files(root):
        if relative == omission_path:
            continue
        root_name = relative.split("/", 1)[0]
        if root_name in _FORBIDDEN_WORKSPACE_ROOTS:
            continue
        if root_name not in _WORKSPACE_ALLOWED_ROOTS:
            raise ArchiveBuildError(f"unexpected workspace payload root: {root_name}")
        lowered = relative.casefold()
        if (
            relative == "locks/authoring.lock"
            or "trust-provider" in lowered
            or "private-key" in lowered
            or lowered.endswith((".key", ".pem", ".p12", ".pfx"))
        ):
            continue
        if relative.startswith("sources/inbox/") and source_profile == "referenced":
            continue
        if relative.startswith("sources/inbox/") and relative not in bound_paths:
            raise ArchiveBuildError("embedded source is not governed")
        try:
            payload = _read_pinned_file(file_path)
        except OSError as exc:
            raise ArchiveBuildError(f"cannot read workspace payload: {relative}") from exc
        payloads[relative] = (
            payload
            if relative.startswith("sources/inbox/")
            else _normalize_payload(relative, payload)
        )
    payloads[omission_path] = omission
    if not _REQUIRED_WORKSPACE_FILES.issubset(payloads):
        raise ArchiveBuildError("workspace archive lacks required portable state")
    return root, payloads


def _walk_json(value: object) -> Iterator[tuple[str, object]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _validate_candidate_document(
    path: str,
    payload: bytes,
) -> CandidatePackManifest | PublicEvalCase | DecisionContract | CandidateArtifact:
    if PurePosixPath(path).suffix.lower() not in {".json", ".yaml"}:
        raise ArchiveBuildError(f"untyped candidate payload is forbidden: {path}")
    try:
        body = json.loads(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ArchiveBuildError(f"candidate document is invalid JSON: {path}") from exc
    if not isinstance(body, dict):
        raise ArchiveBuildError(f"candidate document must be an object: {path}")
    try:
        if path == "pack/pack.yaml":
            document: (
                CandidatePackManifest | PublicEvalCase | DecisionContract | CandidateArtifact
            ) = CandidatePackManifest.model_validate(body)
        elif re.fullmatch(
            r"pack/evaluations/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)",
            path,
        ):
            document = PublicEvalCase.model_validate(body)
        elif re.fullmatch(
            r"pack/scope/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)",
            path,
        ) and {"decision", "action_mode"}.issubset(body):
            document = DecisionContract.model_validate(body)
        elif re.fullmatch(
            r"pack/(?:scope|ontology|metrics|methods|policies|retrieval|"
            r"workflows|tools|governance)/"
            r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)",
            path,
        ):
            document = CandidateArtifact.model_validate(body)
        else:
            raise ArchiveBuildError(f"candidate path has no exact schema: {path}")
    except ValidationError as exc:
        raise ArchiveBuildError(f"candidate document schema is invalid: {path}") from exc

    for key, value in _walk_json(body):
        lowered = key.casefold()
        if lowered == "lifecycle" and value not in {"draft", "review"}:
            raise ArchiveBuildError(f"candidate lifecycle exceeds review: {path}")
        if lowered == "lifecycle_history" and (
            not isinstance(value, list)
            or any(
                not isinstance(item, dict)
                or item.get("to_state", item.get("to_lifecycle")) not in {"draft", "review"}
                for item in value
            )
        ):
            raise ArchiveBuildError(f"candidate lifecycle history exceeds review: {path}")
        if lowered in {
            "reviewed_by",
            "approved_at",
            "approved_by",
            "approval",
            "approvals",
        } and value not in (None, (), []):
            raise ArchiveBuildError(f"candidate review or approval field is not null: {path}")
        if (
            lowered
            in {
                "active",
                "production",
                "production_eligible",
                "releasable",
                "protected",
                "contains_protected_evaluations",
            }
            and value is not False
        ):
            raise ArchiveBuildError(f"candidate safety flag is not false: {path}")
        if lowered == "package_kind" and value != "candidate":
            raise ArchiveBuildError(f"package kind is not candidate: {path}")
    return document


def _candidate_path_allowed(path: str) -> bool:
    parts = path.split("/")
    if parts[0] != "pack":
        return False
    stems = {part.casefold().split(".", 1)[0] for part in parts}
    path_tokens = {token for stem in stems for token in re.split(r"[^a-z0-9]+", stem) if token}
    if path_tokens & _PRIVATE_TOKENS or any(
        marker in stem for stem in stems for marker in ("heldout", "oracle", "rubric", "secret")
    ):
        return False
    lowered = path.casefold()
    if any(
        token in lowered
        for token in (
            "evaluation-summary",
            "explorer",
            "context-model",
            "runtime-ctx",
            "source-register",
        )
    ):
        return False
    return (
        path == "pack/pack.yaml"
        or re.fullmatch(
            r"pack/(?:scope|ontology|metrics|methods|policies|retrieval|"
            r"workflows|tools|evaluations|governance)/"
            r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)",
            path,
        )
        is not None
    )


def _validate_candidate_inventory_items(
    items: Iterator[tuple[str, bytes]],
) -> None:
    manifest: CandidatePackManifest | None = None
    artifacts: dict[str, str] = {}
    suites: set[str] = set()
    evaluation_ids: set[str] = set()
    artifact_ids: set[str] = set()
    evaluations: list[PublicEvalCase] = []
    for path, payload in items:
        document = _validate_candidate_document(path, payload)
        if isinstance(document, CandidatePackManifest):
            if manifest is not None:
                raise ArchiveBuildError("candidate pack manifest is duplicated")
            manifest = document
        elif isinstance(document, PublicEvalCase):
            if document.id in evaluation_ids:
                raise ArchiveBuildError("candidate evaluation id is duplicated")
            evaluation_ids.add(document.id)
            suites.add(document.suite.value)
            evaluations.append(document)
        else:
            if document.id in artifact_ids:
                raise ArchiveBuildError("candidate artifact id is duplicated")
            artifact_ids.add(document.id)
            artifacts[document.id] = _sha256(payload)
    if manifest is None:
        raise ArchiveBuildError("candidate archive lacks pack/pack.yaml")
    declared_artifacts = tuple(
        (entry.artifact_id, entry.digest) for entry in manifest.artifact_digests
    )
    actual_artifacts = tuple(sorted(artifacts.items()))
    if declared_artifacts != actual_artifacts:
        raise ArchiveBuildError("candidate pack artifact digest inventory is not exact")
    # Candidate-completeness gap: this is a draft-suite allowlist, not proof that
    # every declared suite contains cases. Candidate manifests remain non-releasable.
    declared_suites = tuple(suite.value for suite in manifest.public_evaluation_suites)
    if tuple(sorted(set(declared_suites))) != declared_suites or not suites.issubset(
        set(declared_suites)
    ):
        raise ArchiveBuildError("candidate pack public evaluation suite declaration is not exact")
    for evaluation in evaluations:
        if not set(evaluation.required_context).issubset(artifact_ids):
            raise ArchiveBuildError("public evaluation references an undeclared candidate artifact")


def _validate_candidate_inventory(payloads: Mapping[str, bytes]) -> None:
    _validate_candidate_inventory_items(iter((path, payloads[path]) for path in sorted(payloads)))


def _candidate_payloads(workspace: WorkspaceRef) -> tuple[Path, dict[str, bytes]]:
    _, root = _workspace_root(workspace)
    _assert_no_pending_transaction(root)
    payloads: dict[str, bytes] = {}
    for relative, file_path in _scan_files(root):
        if not _candidate_path_allowed(relative):
            if relative.split("/", 1)[0] in _PACK_ALLOWED_ROOTS:
                raise ArchiveBuildError(f"forbidden candidate payload: {relative}")
            continue
        payload = _normalize_payload(relative, _read_pinned_file(file_path))
        _validate_candidate_document(relative, payload)
        payloads[relative] = payload
    if "pack/pack.yaml" not in payloads:
        raise ArchiveBuildError("candidate archive lacks pack/pack.yaml")
    return root, payloads


def _build(
    format_name: ArchiveFormat,
    out: str | Path,
    root: Path,
    payloads: dict[str, bytes],
    transfer_authorization: ArchiveTransferAuthorization | None = None,
) -> VerifiedArchive:
    output = Path(out).absolute()
    expected_suffix = ".owworkspace" if format_name == "ontowiz-authoring-workspace" else ".owpack"
    if output.suffix.casefold() != expected_suffix:
        raise ArchiveBuildError(f"archive output must use {expected_suffix}")
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ArchiveBuildError("archive output cannot mutate its source workspace")
    if len(payloads) > _MAX_ENTRIES:
        raise ArchiveBuildError("archive payload entry limit exceeded")
    total = sum(len(payload) for payload in payloads.values())
    if total > _MAX_TOTAL_BYTES or any(
        len(payload) > _MAX_ENTRY_BYTES for payload in payloads.values()
    ):
        raise ArchiveBuildError("archive payload byte limit exceeded")
    ordered = sorted(payloads)
    _assert_no_namespace_collisions(ordered, ArchiveBuildError)
    if len({name.casefold() for name in ordered}) != len(ordered):
        raise ArchiveBuildError("archive payload paths collide under case-folding")
    entries = tuple(_entry(name, payloads[name], format_name) for name in ordered)
    manifest = _base_manifest(format_name, entries, transfer_authorization)
    return _write_archive(output, manifest, payloads)


def _trusted_effective_date() -> date:
    return date.today()


def build_workspace_archive(
    workspace: WorkspaceRef,
    out: str | Path,
    *,
    source_profile: SourceProfile,
    as_of: date,
    target_client_boundary: str | None = None,
    trust_provider: AuthoringTrustProvider | None = None,
) -> VerifiedArchive:
    """Build one locked, provider-converged portable authoring snapshot."""

    if source_profile not in {"referenced", "embedded"}:
        raise ArchiveBuildError("unsupported source profile")
    if not isinstance(as_of, date) or as_of != _trusted_effective_date():
        raise ArchiveBuildError("as_of must equal the trusted current effective date")
    try:
        transfer = ArchiveTransferAuthorization.model_validate(
            {
                "source_profile": source_profile,
                "effective_date": as_of,
                "target_client_boundary": target_client_boundary,
            }
        )
        with locked_authoring_archive_snapshot(
            workspace,
            trust_provider,
        ) as snapshot:
            root, payloads = _workspace_payloads(
                snapshot.workspace,
                source_profile=source_profile,
                as_of=as_of,
                target_client_boundary=target_client_boundary,
            )
            output = Path(out).absolute()
            temporary = output.with_name(f".{output.name}.{os.urandom(16).hex()}{output.suffix}")
            try:
                _build(
                    "ontowiz-authoring-workspace",
                    temporary,
                    root,
                    payloads,
                    transfer,
                )
                _, final_payloads = _workspace_payloads(
                    snapshot.workspace,
                    source_profile=source_profile,
                    as_of=as_of,
                    target_client_boundary=target_client_boundary,
                )
                if final_payloads != payloads:
                    raise ArchiveBuildError("workspace changed during archive publication")
                os.replace(temporary, output)
                return verify_archive(
                    output,
                    expected_format="ontowiz-authoring-workspace",
                )
            finally:
                if temporary.exists():
                    temporary.unlink()
    except ValidationError as exc:
        raise ArchiveBuildError("workspace transfer authorization is invalid") from exc
    except (AuthoringError, WorkspaceError) as exc:
        raise ArchiveBuildError("authoring snapshot is not converged") from exc


def build_candidate_pack(
    workspace: WorkspaceRef,
    out: str | Path,
    *,
    trust_provider: AuthoringTrustProvider | None = None,
) -> VerifiedArchive:
    """Build one locked, provider-converged candidate-only package."""

    try:
        with locked_authoring_archive_snapshot(
            workspace,
            trust_provider,
        ) as snapshot:
            root, payloads = _candidate_payloads(snapshot.workspace)
            _validate_candidate_inventory(payloads)
            output = Path(out).absolute()
            temporary = output.with_name(f".{output.name}.{os.urandom(16).hex()}{output.suffix}")
            try:
                _build(
                    "ontowiz-candidate-pack",
                    temporary,
                    root,
                    payloads,
                )
                _, final_payloads = _candidate_payloads(snapshot.workspace)
                _validate_candidate_inventory(final_payloads)
                if final_payloads != payloads:
                    raise ArchiveBuildError("candidate state changed during archive publication")
                os.replace(temporary, output)
                return verify_archive(
                    output,
                    expected_format="ontowiz-candidate-pack",
                )
            finally:
                if temporary.exists():
                    temporary.unlink()
    except (AuthoringError, WorkspaceError) as exc:
        raise ArchiveBuildError("authoring snapshot is not converged") from exc


def _assert_no_namespace_collisions(
    paths: Iterator[str] | list[str] | tuple[str, ...] | set[str],
    error_type: type[ArchiveError],
) -> None:
    seen: set[str] = set()
    for path in sorted(value.casefold() for value in paths):
        components = path.split("/")
        if any("/".join(components[:index]) in seen for index in range(1, len(components))):
            raise error_type("archive file/ancestor namespace collision")
        seen.add(path)


def _dos_datetime(info: zipfile.ZipInfo) -> tuple[int, int]:
    year, month, day, hour, minute, second = info.date_time
    dos_date = ((year - 1980) << 9) | (month << 5) | day
    dos_time = (hour << 11) | (minute << 5) | (second // 2)
    return dos_time, dos_date


def _verify_raw_zip_layout(
    archive_path: Path,
    archive: zipfile.ZipFile,
    infos: list[zipfile.ZipInfo],
) -> None:
    local_struct = struct.Struct("<4s5H3I2H")
    central_struct = struct.Struct("<4s6H3I5H2I")
    eocd_struct = struct.Struct("<4s4H2IH")
    try:
        file_size = archive_path.stat().st_size
        with archive_path.open("rb") as raw:
            cursor = 0
            local_records: list[tuple[int, tuple[int, ...], bytes]] = []
            for info in infos:
                if info.header_offset != cursor:
                    raise ArchiveVerificationError(
                        "ZIP local records are prefixed, gapped, or reordered"
                    )
                raw.seek(cursor)
                header = raw.read(local_struct.size)
                if len(header) != local_struct.size:
                    raise ArchiveVerificationError("truncated ZIP local header")
                (
                    signature,
                    extract_version,
                    flags,
                    method,
                    modified_time,
                    modified_date,
                    crc,
                    compressed_size,
                    uncompressed_size,
                    name_length,
                    extra_length,
                ) = local_struct.unpack(header)
                if signature != b"PK\x03\x04" or extra_length != 0:
                    raise ArchiveVerificationError(
                        "ZIP local header or local extra field is non-canonical"
                    )
                name_bytes = raw.read(name_length)
                if len(name_bytes) != name_length:
                    raise ArchiveVerificationError("truncated ZIP local filename")
                try:
                    decoded_name = name_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ArchiveVerificationError("ZIP local filename is not UTF-8") from exc
                dos_time, dos_date = _dos_datetime(info)
                if (
                    decoded_name != info.filename
                    or flags != info.flag_bits
                    or method != info.compress_type
                    or modified_time != dos_time
                    or modified_date != dos_date
                    or crc != info.CRC
                    or compressed_size != info.compress_size
                    or uncompressed_size != info.file_size
                    or extract_version != info.extract_version
                ):
                    raise ArchiveVerificationError("ZIP local and central metadata differ")
                local_records.append(
                    (
                        cursor,
                        (
                            extract_version,
                            flags,
                            method,
                            modified_time,
                            modified_date,
                            crc,
                            compressed_size,
                            uncompressed_size,
                        ),
                        name_bytes,
                    )
                )
                cursor += local_struct.size + name_length + extra_length + compressed_size
            if cursor != archive.start_dir:
                raise ArchiveVerificationError(
                    "ZIP bytes exist between local records and central directory"
                )
            central_start = cursor
            for info, (local_offset, local_values, local_name_bytes) in zip(
                infos,
                local_records,
                strict=True,
            ):
                raw.seek(cursor)
                header = raw.read(central_struct.size)
                if len(header) != central_struct.size:
                    raise ArchiveVerificationError("truncated ZIP central header")
                (
                    signature,
                    create_version,
                    extract_version,
                    flags,
                    method,
                    modified_time,
                    modified_date,
                    crc,
                    compressed_size,
                    uncompressed_size,
                    name_length,
                    extra_length,
                    comment_length,
                    disk_number,
                    internal_attr,
                    external_attr,
                    header_offset,
                ) = central_struct.unpack(header)
                name_bytes = raw.read(name_length)
                extra = raw.read(extra_length)
                comment = raw.read(comment_length)
                if (
                    signature != b"PK\x01\x02"
                    or name_bytes != local_name_bytes
                    or extra
                    or comment
                    or disk_number != 0
                    or internal_attr != info.internal_attr
                    or external_attr != info.external_attr
                    or header_offset != local_offset
                    or create_version != ((info.create_system << 8) | info.create_version)
                    or (
                        extract_version,
                        flags,
                        method,
                        modified_time,
                        modified_date,
                        crc,
                        compressed_size,
                        uncompressed_size,
                    )
                    != local_values
                ):
                    raise ArchiveVerificationError(
                        "ZIP central directory is not an exact canonical mirror"
                    )
                cursor += central_struct.size + name_length + extra_length + comment_length
            central_size = cursor - central_start
            raw.seek(cursor)
            eocd = raw.read(eocd_struct.size)
            if len(eocd) != eocd_struct.size:
                raise ArchiveVerificationError("truncated ZIP end record")
            (
                signature,
                disk_number,
                central_disk,
                disk_entries,
                total_entries,
                declared_central_size,
                declared_central_offset,
                comment_length,
            ) = eocd_struct.unpack(eocd)
            cursor += eocd_struct.size
            if (
                signature != b"PK\x05\x06"
                or disk_number != 0
                or central_disk != 0
                or disk_entries != len(infos)
                or total_entries != len(infos)
                or declared_central_size != central_size
                or declared_central_offset != central_start
                or comment_length != 0
                or cursor != file_size
                or raw.read(1)
            ):
                raise ArchiveVerificationError("ZIP end record does not exactly consume the file")
    except ArchiveVerificationError:
        raise
    except (OSError, ValueError, struct.error) as exc:
        raise ArchiveVerificationError("invalid physical ZIP layout") from exc


def _validate_zip_member(info: zipfile.ZipInfo) -> str:
    name = _portable_path(info.filename)
    if (
        info.compress_type != zipfile.ZIP_STORED
        or info.flag_bits & ~_UTF8_FLAG
        or not info.flag_bits & _UTF8_FLAG
        or info.date_time != _FIXED_TIME
        or info.create_system != 3
        or info.extra
        or info.comment
        or info.is_dir()
    ):
        raise ArchiveVerificationError(f"non-canonical ZIP member: {name}")
    unix_mode = info.external_attr >> 16
    dos_attributes = info.external_attr & 0xFFFF
    if unix_mode != _REGULAR_MODE or not stat.S_ISREG(unix_mode) or dos_attributes & 0x410:
        raise ArchiveVerificationError(f"linked or non-regular ZIP member: {name}")
    if info.file_size < 0 or info.file_size > _MAX_ENTRY_BYTES:
        raise ArchiveVerificationError(f"ZIP member exceeds byte limit: {name}")
    return name


def _read_limited(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    *,
    expected_size: int | None = None,
) -> bytes:
    limit = _MAX_ENTRY_BYTES if expected_size is None else min(_MAX_ENTRY_BYTES, expected_size)
    chunks: list[bytes] = []
    count = 0
    try:
        with archive.open(info, "r") as stream:
            while chunk := stream.read(min(1024 * 1024, limit + 1 - count)):
                count += len(chunk)
                if count > limit:
                    raise ArchiveVerificationError(
                        f"member exceeds streamed byte limit: {info.filename}"
                    )
                chunks.append(chunk)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise ArchiveVerificationError(f"cannot stream ZIP member: {info.filename}") from exc
    if expected_size is not None and count != expected_size:
        raise ArchiveVerificationError(f"member byte count mismatch: {info.filename}")
    return b"".join(chunks)


def _strict_manifest(payload: bytes) -> ArchiveManifest:
    try:
        data = json.loads(payload)
        manifest = ArchiveManifest.model_validate(data)
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise ArchiveVerificationError("archive manifest schema is invalid") from exc
    try:
        canonical = _canonical_json(manifest.model_dump(mode="json"))
    except ArchiveBuildError as exc:
        raise ArchiveVerificationError("archive manifest is not canonical") from exc
    if canonical != payload:
        raise ArchiveVerificationError("archive manifest bytes are not canonical")
    if manifest.semantic_digest != _semantic_digest(manifest):
        raise ArchiveVerificationError("archive semantic digest mismatch")
    paths = tuple(entry.path for entry in manifest.entries)
    if paths != tuple(sorted(paths)) or len(set(paths)) != len(paths):
        raise ArchiveVerificationError("manifest entries are not unique and sorted")
    if len({path.casefold() for path in paths}) != len(paths):
        raise ArchiveVerificationError("manifest paths collide under case-folding")
    _assert_no_namespace_collisions(paths, ArchiveVerificationError)
    if len(paths) > _MAX_ENTRIES:
        raise ArchiveVerificationError("manifest entry limit exceeded")
    total = 0
    for entry in manifest.entries:
        _portable_path(entry.path)
        if entry.byte_count > _MAX_ENTRY_BYTES:
            raise ArchiveVerificationError("manifest per-entry limit exceeded")
        total += entry.byte_count
        if total > _MAX_TOTAL_BYTES:
            raise ArchiveVerificationError("manifest total byte limit exceeded")
        role, media = _metadata(cast(ArchiveFormat, manifest.format), entry.path)
        if entry.role != role or entry.media_type != media:
            raise ArchiveVerificationError(f"manifest role/media mismatch: {entry.path}")
    _validate_format_inventory(manifest)
    return manifest


def _validate_format_inventory(manifest: ArchiveManifest) -> None:
    paths = {entry.path for entry in manifest.entries}
    format_name = cast(ArchiveFormat, manifest.format)
    if format_name == "ontowiz-authoring-workspace":
        if not _REQUIRED_WORKSPACE_FILES.issubset(paths):
            raise ArchiveVerificationError("workspace archive lacks required state")
        for path in paths:
            if path.split("/", 1)[0] not in _WORKSPACE_ALLOWED_ROOTS:
                raise ArchiveVerificationError(f"forbidden workspace archive root: {path}")
            lowered = path.casefold()
            if (
                path == "locks/authoring.lock"
                or any(f"/{root}/" in f"/{lowered}/" for root in _FORBIDDEN_WORKSPACE_ROOTS)
                or "heldout" in lowered
                or "secret" in lowered
                or "trust-provider" in lowered
            ):
                raise ArchiveVerificationError(f"private workspace payload: {path}")
    else:
        if "pack/pack.yaml" not in paths:
            raise ArchiveVerificationError("candidate archive lacks pack manifest")
        for path in paths:
            if not _candidate_path_allowed(path):
                raise ArchiveVerificationError(f"forbidden candidate payload: {path}")


def _parse_governance_payloads(
    source_payload: bytes,
    binding_payload: bytes | None,
    omission_payload: bytes,
) -> tuple[
    dict[str, SourceRecord],
    dict[str, tuple[str, str]],
    SourceProfile,
    date,
    list[dict[str, object]],
    str | None,
]:
    try:
        source_data = json.loads(source_payload)
        if set(source_data) != {"format", "format_version", "sources"}:
            raise ValueError
        if (
            source_data["format"] != "ontowiz-source-register"
            or source_data["format_version"] != 1
            or not isinstance(source_data["sources"], list)
        ):
            raise ValueError
        sources = {
            source.id: source
            for source in (SourceRecord.model_validate(item) for item in source_data["sources"])
        }
        if len(sources) != len(source_data["sources"]):
            raise ValueError

        bindings: dict[str, tuple[str, str]] = {}
        if binding_payload is not None:
            binding_data = json.loads(binding_payload)
            if set(binding_data) != {
                "format",
                "format_version",
                "workspace_id",
                "bindings",
            }:
                raise ValueError
            if (
                binding_data["format"] != "ontowiz-source-material-bindings"
                or binding_data["format_version"] != 1
                or not isinstance(binding_data["bindings"], list)
            ):
                raise ValueError
            for item in binding_data["bindings"]:
                if set(item) != {"source_id", "relative_path", "checksum"}:
                    raise ValueError
                source_id = str(item["source_id"])
                if source_id in bindings:
                    raise ValueError
                relative = _portable_path(str(item["relative_path"]))
                checksum = str(item["checksum"])
                if not relative.startswith("sources/inbox/") or not re.fullmatch(
                    r"sha256:[0-9a-f]{64}", checksum
                ):
                    raise ValueError
                bindings[source_id] = (relative, checksum)

        omission_data = json.loads(omission_payload)
        if set(omission_data) != {
            "as_of",
            "format",
            "format_version",
            "omitted",
            "source_profile",
            "target_client_boundary",
        }:
            raise ValueError
        if (
            omission_data["format"] != "ontowiz-source-omissions"
            or omission_data["format_version"] != 1
            or omission_data["source_profile"] not in {"referenced", "embedded"}
            or not isinstance(omission_data["omitted"], list)
        ):
            raise ValueError
        as_of = date.fromisoformat(str(omission_data["as_of"]))
        omitted: list[dict[str, object]] = []
        for item in omission_data["omitted"]:
            if not isinstance(item, dict) or set(item) != {
                "path",
                "reason",
                "sha256",
                "source_id",
            }:
                raise ValueError
            _portable_path(str(item["path"]))
            if item["reason"] != "referenced-profile-governed-source-omission" or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", str(item["sha256"])
            ):
                raise ValueError
            omitted.append(item)
    except (
        ArchiveVerificationError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        ValidationError,
    ) as exc:
        raise ArchiveVerificationError("workspace source governance is invalid") from exc
    return (
        sources,
        bindings,
        cast(SourceProfile, omission_data["source_profile"]),
        as_of,
        omitted,
        (
            str(omission_data["target_client_boundary"])
            if omission_data["target_client_boundary"] is not None
            else None
        ),
    )


def _source_permits_archive_transfer(
    source: SourceRecord,
    *,
    effective_date: date,
    target_client_boundary: str,
) -> bool:
    return (
        source.retention_until is not None
        and source.retention_until >= effective_date
        and source.client_boundary == target_client_boundary
        and source.permits_embedding(as_of=effective_date)
    )


def _verify_workspace_governance(
    archive: zipfile.ZipFile,
    by_name: Mapping[str, zipfile.ZipInfo],
    manifest: ArchiveManifest,
) -> None:
    entries = {entry.path: entry for entry in manifest.entries}
    source_payload = _read_limited(
        archive,
        by_name["sources/source-register.yaml"],
        expected_size=entries["sources/source-register.yaml"].byte_count,
    )
    omission_path = "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml"
    omission_payload = _read_limited(
        archive,
        by_name[omission_path],
        expected_size=entries[omission_path].byte_count,
    )
    binding_path = "locks/source-material-bindings.json"
    binding_payload = (
        _read_limited(
            archive,
            by_name[binding_path],
            expected_size=entries[binding_path].byte_count,
        )
        if binding_path in entries
        else None
    )
    (
        sources,
        bindings,
        profile,
        as_of,
        omitted,
        target_client_boundary,
    ) = _parse_governance_payloads(
        source_payload,
        binding_payload,
        omission_payload,
    )
    transfer = manifest.transfer_authorization
    if (
        transfer is None
        or transfer.source_profile.value != profile
        or transfer.effective_date != as_of
        or transfer.target_client_boundary != target_client_boundary
    ):
        raise ArchiveVerificationError(
            "workspace transfer authorization differs from governed source record"
        )
    inbox = {path for path in entries if path.startswith("sources/inbox/")}
    bound_paths = {relative for relative, _ in bindings.values()}
    if len(bound_paths) != len(bindings):
        raise ArchiveVerificationError("multiple sources bind the same material")
    expected_omissions: list[dict[str, object]] = []
    for source_id, (relative, checksum) in sorted(bindings.items()):
        source = sources.get(source_id)
        if source is None or source.checksum != checksum:
            raise ArchiveVerificationError("material binding lacks exact source/checksum")
        if profile == "embedded":
            entry = entries.get(relative)
            if (
                entry is None
                or entry.sha256 != checksum
                or target_client_boundary is None
                or not _source_permits_archive_transfer(
                    source,
                    effective_date=as_of,
                    target_client_boundary=target_client_boundary,
                )
            ):
                raise ArchiveVerificationError(
                    f"embedded source is absent or unauthorized: {source_id}"
                )
        else:
            if relative in entries:
                raise ArchiveVerificationError("referenced archive embeds source bytes")
            expected_omissions.append(
                {
                    "path": relative,
                    "reason": "referenced-profile-governed-source-omission",
                    "sha256": checksum,
                    "source_id": source_id,
                }
            )
    if profile == "embedded":
        if inbox != bound_paths or omitted:
            raise ArchiveVerificationError("embedded source inventory is not exact")
    elif inbox or omitted != expected_omissions:
        raise ArchiveVerificationError("referenced source omissions are not exact")


def verify_archive(
    path: str | Path,
    expected_format: ArchiveFormat | None = None,
) -> VerifiedArchive:
    """Verify an archive independently without extracting any payload."""

    archive_path = Path(path).absolute()
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            if archive.comment:
                raise ArchiveVerificationError("archive comment is forbidden")
            infos = archive.infolist()
            _verify_raw_zip_layout(archive_path, archive, infos)
            if len(infos) < 2 or len(infos) > _MAX_ENTRIES + 2:
                raise ArchiveVerificationError("archive entry count is invalid")
            names: list[str] = []
            total_declared = 0
            for info in infos:
                name = _validate_zip_member(info)
                names.append(name)
                total_declared += info.file_size
                if total_declared > _MAX_TOTAL_BYTES + 2 * _MAX_ENTRY_BYTES:
                    raise ArchiveVerificationError("archive declared total size exceeded")
            if len(set(names)) != len(names) or len({name.casefold() for name in names}) != len(
                names
            ):
                raise ArchiveVerificationError("archive contains duplicate or colliding names")
            if names[:2] != list(_CONTROLS):
                raise ArchiveVerificationError("archive control files are missing or reordered")
            if any(name.startswith("META-INF/") for name in names[2:]):
                raise ArchiveVerificationError("archive contains unexpected control files")
            by_name = {info.filename: info for info in infos}
            manifest_bytes = _read_limited(archive, by_name[_CONTROL_MANIFEST])
            digest_bytes = _read_limited(archive, by_name[_CONTROL_DIGEST], expected_size=65)
            expected_digest_bytes = (hashlib.sha256(manifest_bytes).hexdigest() + "\n").encode(
                "ascii"
            )
            if digest_bytes != expected_digest_bytes:
                raise ArchiveVerificationError("manifest control digest mismatch")
            manifest = _strict_manifest(manifest_bytes)
            if expected_format is not None and manifest.format != expected_format:
                raise ArchiveVerificationError("archive format differs from expected format")
            declared_names = tuple(entry.path for entry in manifest.entries)
            if tuple(names[2:]) != declared_names:
                raise ArchiveVerificationError("archive inventory differs from manifest")
            total_streamed = 0
            portable_payloads: dict[str, bytes] = {}
            for entry in manifest.entries:
                info = by_name[entry.path]
                if info.file_size != entry.byte_count:
                    raise ArchiveVerificationError(f"declared byte count mismatch: {entry.path}")
                payload = _read_limited(archive, info, expected_size=entry.byte_count)
                total_streamed += len(payload)
                if total_streamed > _MAX_TOTAL_BYTES:
                    raise ArchiveVerificationError("streamed archive total exceeded")
                if _sha256(payload) != entry.sha256:
                    raise ArchiveVerificationError(f"payload digest mismatch: {entry.path}")
                _verify_payload_semantics(
                    cast(ArchiveFormat, manifest.format),
                    entry.path,
                    payload,
                )
                if manifest.format == "ontowiz-authoring-workspace" and not entry.path.startswith(
                    "sources/inbox/"
                ):
                    portable_payloads[entry.path] = payload
            if manifest.format == "ontowiz-authoring-workspace":
                _verify_workspace_governance(archive, by_name, manifest)
                try:
                    _validate_portable_record_graph(portable_payloads)
                except ArchiveBuildError as exc:
                    raise ArchiveVerificationError(str(exc)) from exc
            else:
                try:
                    _validate_candidate_inventory_items(
                        iter(
                            (
                                entry.path,
                                _read_limited(
                                    archive,
                                    by_name[entry.path],
                                    expected_size=entry.byte_count,
                                ),
                            )
                            for entry in manifest.entries
                        )
                    )
                except ArchiveBuildError as exc:
                    raise ArchiveVerificationError(str(exc)) from exc
    except ArchiveVerificationError:
        raise
    except (OSError, KeyError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise ArchiveVerificationError("invalid ZIP archive") from exc
    return VerifiedArchive(
        path=archive_path,
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        archive_sha256=_archive_file_sha256(archive_path),
    )


def _verify_payload_semantics(
    format_name: ArchiveFormat,
    path: str,
    payload: bytes,
) -> None:
    if format_name == "ontowiz-candidate-pack":
        try:
            _validate_candidate_document(path, payload)
        except ArchiveBuildError as exc:
            raise ArchiveVerificationError(str(exc)) from exc
    elif path == "workspace.yaml":
        try:
            data = json.loads(payload)
            if (
                data.get("format") != "ontowiz-authoring-workspace"
                or data.get("contains_protected_evaluations") is not False
                or data.get("adapter_neutral") is not True
            ):
                raise ValueError
        except (json.JSONDecodeError, AttributeError, ValueError) as exc:
            raise ArchiveVerificationError("workspace manifest payload is invalid") from exc
    elif path.endswith((".json", ".yaml", ".yml")):
        try:
            if _canonical_json(json.loads(payload)) != payload:
                raise ArchiveVerificationError(f"structured payload is not canonical: {path}")
        except (json.JSONDecodeError, ArchiveBuildError) as exc:
            raise ArchiveVerificationError(f"structured payload is invalid: {path}") from exc


def _write_extracted_file(root: Path, relative: str, payload: bytes) -> None:
    target = root.joinpath(*relative.split("/"))
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ArchiveImportError("extraction path escapes staging") from exc
    current = root
    for component in relative.split("/")[:-1]:
        current = current / component
        try:
            current.mkdir(mode=0o755)
        except FileExistsError:
            info = current.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ArchiveImportError("extraction parent is linked") from None
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(target, flags, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(target, 0o644)
    except OSError as exc:
        raise ArchiveImportError(f"cannot extract payload: {relative}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _same_destination(
    destination: Path,
    verified: VerifiedArchive,
) -> bool:
    try:
        Workspace.open(destination)
    except WorkspaceError:
        return False
    expected = {entry.path: entry for entry in verified.manifest.entries}
    for path, entry in expected.items():
        target = destination.joinpath(*path.split("/"))
        try:
            _plain_file(target)
            payload = _read_pinned_file(target)
        except (ArchiveBuildError, OSError):
            return False
        if len(payload) != entry.byte_count or _sha256(payload) != entry.sha256:
            return False
    actual = {
        relative
        for relative, _ in _scan_files(destination)
        if relative.split("/", 1)[0] in _WORKSPACE_ALLOWED_ROOTS
        and relative != "locks/authoring.lock"
    }
    return actual == set(expected)


def _restore_workspace_directories(root: Path) -> None:
    inventory_path = root / "locks" / "workspace-inventory.json"
    try:
        inventory = json.loads(_read_pinned_file(inventory_path))
        directories = inventory["directories"]
        if not isinstance(directories, list) or len(set(directories)) != len(directories):
            raise ValueError
        for relative_value in directories:
            relative = _portable_path(str(relative_value))
            target = root.joinpath(*relative.split("/"))
            target.mkdir(mode=0o755, parents=True, exist_ok=True)
            info = target.lstat()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ValueError
    except (
        ArchiveVerificationError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise ArchiveImportError("imported directory inventory is invalid") from exc


def _validate_supported_portable_state_paths(root: Path) -> None:
    for relative, _path in _scan_files(root):
        if (
            relative.startswith("pack/")
            and relative != "pack/pack.yaml"
            and PurePosixPath(relative).suffix.lower() not in {".json", ".yaml"}
        ):
            raise ArchiveImportError(f"pack document has no portable schema: {relative}")


def _derived_outputs(
    root: Path,
    workspace: Workspace,
) -> dict[str, bytes]:
    revision_path = root / "locks" / "authoring-revision.json"
    revision = 0
    if revision_path.exists():
        revision_data = json.loads(_read_pinned_file(revision_path))
        revision = int(revision_data["revision"])
    validation = _canonical_json(
        {
            "format": "ontowiz-validation-report",
            "format_version": 1,
            "revision": revision,
            "valid": True,
            "workspace_id": workspace.manifest.workspace_id,
        }
    )
    semantic = _canonical_json(
        {
            "findings": [],
            "format": "ontowiz-semantic-findings",
            "format_version": 1,
            "workspace_id": workspace.manifest.workspace_id,
        }
    )
    readiness = _canonical_json(
        {
            "candidate_only": True,
            "format": "ontowiz-readiness-report",
            "format_version": 1,
            "production_eligible": False,
            "releasable": False,
            "revision": revision,
            "workspace_id": workspace.manifest.workspace_id,
        }
    )
    try:
        _, candidate_payloads = _candidate_payloads(workspace)
        _validate_candidate_inventory(candidate_payloads)
        candidate_documents = tuple(
            (
                path,
                _validate_candidate_document(path, candidate_payloads[path]),
                candidate_payloads[path],
            )
            for path in sorted(candidate_payloads)
        )
        context_model = build_candidate_explorer_context(
            workspace_id=workspace.manifest.workspace_id,
            revision=revision,
            documents=candidate_documents,
        )
        context = candidate_explorer_context_bytes(context_model)
        validated_context = CandidateExplorerContext.model_validate_json(context)
        if candidate_explorer_context_bytes(validated_context) != context:
            raise ExplorerContentError("context model serialization is not canonical")
        explorer = render_candidate_explorer(validated_context)
    except (ArchiveBuildError, ExplorerContentError, ValidationError) as exc:
        raise ArchiveImportError(
            "validated candidate context could not regenerate its explorer"
        ) from exc
    return {
        "reports/validation.json": validation,
        "reports/semantic-findings.json": semantic,
        "reports/readiness.json": readiness,
        "build/context-model.json": context,
        "build/explorer.html": explorer,
    }


def _regenerate_and_validate_derived_outputs(
    root: Path,
    workspace: Workspace,
) -> None:
    expected = _derived_outputs(root, workspace)
    for relative, payload in expected.items():
        _write_extracted_file(root, relative, payload)
    for relative, payload in expected.items():
        actual = _read_pinned_file(root.joinpath(*relative.split("/")))
        if actual != payload:
            raise ArchiveImportError(f"regenerated derived output failed validation: {relative}")


def _validate_import_trust_context(
    manifest: ArchiveManifest,
    *,
    effective_date: date,
    target_client_boundary: str | None,
) -> None:
    if not isinstance(effective_date, date):
        raise ArchiveImportError("trusted import effective date is invalid")
    transfer = manifest.transfer_authorization
    if transfer is None or transfer.effective_date > effective_date:
        raise ArchiveImportError("archive transfer effective date is not trustworthy")
    if transfer.source_profile == "embedded":
        if (
            target_client_boundary is None
            or transfer.target_client_boundary != target_client_boundary
        ):
            raise ArchiveImportError(
                "embedded transfer target does not match the trusted destination boundary"
            )
    elif target_client_boundary is not None:
        raise ArchiveImportError(
            "referenced transfer must not receive a destination client boundary"
        )


def _reauthorize_workspace_transfer(
    archive: zipfile.ZipFile,
    by_name: Mapping[str, zipfile.ZipInfo],
    manifest: ArchiveManifest,
    *,
    effective_date: date,
    target_client_boundary: str | None,
) -> None:
    entries = {entry.path: entry for entry in manifest.entries}
    omission_path = "sources/candidate-claims/SRC-ARCHIVE-OMISSIONS.yaml"
    binding_path = "locks/source-material-bindings.json"
    (
        sources,
        bindings,
        profile,
        _build_date,
        _omitted,
        archive_target_client_boundary,
    ) = _parse_governance_payloads(
        _read_limited(
            archive,
            by_name["sources/source-register.yaml"],
            expected_size=entries["sources/source-register.yaml"].byte_count,
        ),
        (
            _read_limited(
                archive,
                by_name[binding_path],
                expected_size=entries[binding_path].byte_count,
            )
            if binding_path in entries
            else None
        ),
        _read_limited(
            archive,
            by_name[omission_path],
            expected_size=entries[omission_path].byte_count,
        ),
    )
    _validate_import_trust_context(
        manifest,
        effective_date=effective_date,
        target_client_boundary=target_client_boundary,
    )
    if profile == "embedded":
        if (
            not isinstance(target_client_boundary, str)
            or archive_target_client_boundary != target_client_boundary
        ):
            raise ArchiveImportError(
                "archive governance target does not match the trusted destination boundary"
            )
        for source_id, (_relative, checksum) in bindings.items():
            source = sources.get(source_id)
            if (
                source is None
                or source.checksum != checksum
                or not _source_permits_archive_transfer(
                    source,
                    effective_date=effective_date,
                    target_client_boundary=target_client_boundary,
                )
            ):
                raise ArchiveImportError("embedded source transfer is no longer authorized")


def _validate_derived_outputs(root: Path, workspace: Workspace) -> None:
    for relative, payload in _derived_outputs(root, workspace).items():
        path = root.joinpath(*relative.split("/"))
        if not path.is_file() or _read_pinned_file(path) != payload:
            raise ArchiveImportError(f"derived output is absent or stale: {relative}")


def _validate_imported_workspace(
    root: Path,
    trust_provider: AuthoringTrustProvider | None,
    *,
    effective_date: date,
    target_client_boundary: str | None,
) -> Workspace:
    try:
        _validate_supported_portable_state_paths(root)
        with locked_authoring_archive_snapshot(root, trust_provider) as snapshot:
            workspace = snapshot.workspace
            _validate_authoring_cross_references(root, workspace)
            sources = _load_sources(root)
            bindings = _load_bindings(root)
            omission_path = root / "sources" / "candidate-claims" / "SRC-ARCHIVE-OMISSIONS.yaml"
            omission = json.loads(_read_pinned_file(omission_path))
            profile = omission.get("source_profile")
            archive_target_client_boundary = omission.get("target_client_boundary")
            if profile not in {"referenced", "embedded"}:
                raise ArchiveImportError("imported source profile is invalid")
            if profile == "embedded":
                if (
                    target_client_boundary is None
                    or archive_target_client_boundary != target_client_boundary
                ):
                    raise ArchiveImportError(
                        "imported governance target does not match the trusted destination boundary"
                    )
            elif target_client_boundary is not None:
                raise ArchiveImportError(
                    "referenced import must not receive a destination client boundary"
                )
            for source_id, (relative, checksum) in bindings.items():
                source = sources.get(source_id)
                if source is None or source.checksum != checksum:
                    raise ArchiveImportError("imported material binding is invalid")
                material = root.joinpath(*relative.split("/"))
                if profile == "embedded":
                    if (
                        not isinstance(target_client_boundary, str)
                        or not material.is_file()
                        or _sha256(_read_pinned_file(material)) != checksum
                        or not _source_permits_archive_transfer(
                            source,
                            effective_date=effective_date,
                            target_client_boundary=target_client_boundary,
                        )
                    ):
                        raise ArchiveImportError(
                            "imported source rights or checksum are no longer valid"
                        )
                elif material.exists():
                    raise ArchiveImportError("referenced import unexpectedly contains source bytes")
            return workspace
    except ArchiveImportError:
        raise
    except (
        AuthoringError,
        WorkspaceError,
        ArchiveBuildError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise ArchiveImportError("imported workspace validation failed") from exc


def import_workspace_archive(
    path: str | Path,
    destination: str | Path,
    *,
    effective_date: date,
    target_client_boundary: str | None = None,
    trust_provider: AuthoringTrustProvider | None = None,
) -> Workspace:
    """Import using caller-trusted date and destination boundary context."""

    verified = verify_archive(
        path,
        expected_format="ontowiz-authoring-workspace",
    )
    _validate_import_trust_context(
        verified.manifest,
        effective_date=effective_date,
        target_client_boundary=target_client_boundary,
    )
    target = Path(destination).absolute()
    if os.path.lexists(target):
        if target.is_dir() and _same_destination(target, verified):
            current = _validate_imported_workspace(
                target,
                trust_provider,
                effective_date=effective_date,
                target_client_boundary=target_client_boundary,
            )
            _validate_derived_outputs(target, current)
            return current
        raise ArchiveConflictError("destination exists with a different semantic archive")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.owimport-", dir=target.parent))
    try:
        if _archive_file_sha256(verified.path) != verified.archive_sha256:
            raise ArchiveImportError("archive changed after verification")
        with zipfile.ZipFile(verified.path, "r") as archive:
            by_name = {info.filename: info for info in archive.infolist()}
            _reauthorize_workspace_transfer(
                archive,
                by_name,
                verified.manifest,
                effective_date=effective_date,
                target_client_boundary=target_client_boundary,
            )
            for entry in verified.manifest.entries:
                payload = _read_limited(
                    archive,
                    by_name[entry.path],
                    expected_size=entry.byte_count,
                )
                if _sha256(payload) != entry.sha256:
                    raise ArchiveImportError("archive changed during extraction")
                _write_extracted_file(staging, entry.path, payload)
        _restore_workspace_directories(staging)
        imported = _validate_imported_workspace(
            staging,
            trust_provider,
            effective_date=effective_date,
            target_client_boundary=target_client_boundary,
        )
        _regenerate_and_validate_derived_outputs(staging, imported)
        Workspace.open(staging)
        try:
            os.rename(staging, target)
        except OSError as exc:
            if (
                os.path.lexists(target)
                and target.is_dir()
                and _same_destination(
                    target,
                    verified,
                )
            ):
                current = _validate_imported_workspace(
                    target,
                    trust_provider,
                    effective_date=effective_date,
                    target_client_boundary=target_client_boundary,
                )
                _validate_derived_outputs(target, current)
                return current
            raise ArchiveConflictError("destination appeared during atomic import") from exc
        return Workspace.open(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
