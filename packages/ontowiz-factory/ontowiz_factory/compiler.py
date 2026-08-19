"""Pack compiler — governed artifacts → a compiled Domain Pack.

Turns ACTIVE artifacts into a CompiledPack: a CTX L2 context layer (one section
per artifact), a hydration directory (the agent's map, via CTX's LLM-as-router
protocol), and a PackManifest. Only ACTIVE artifacts enter a pack — governance
is enforced at compile time, before anything can be served.

S1.1 makes the candidate **deterministic, digest-addressed, and exactly
inventoried** (spec ``docs/specs/S1-1_DETERMINISTIC_COMPILE.md`` @ ``f8a79a3``):
a candidate is byte-identical regardless of input order, working directory, or
wall-clock time; ``candidate_digest`` is a reproducible content id over an
explicit allowlist that reads payload digests out of ``output_inventory`` (no
self-reference); output paths are injective. The on-disk persistence half (fresh
staging, atomic promote, conflict, verification) lives in ``writer.py`` and is
re-exported from this module for backward compatibility.

Tier B (factory): may import Tier A (ontowiz_spec, ontowiz_ctx).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

import yaml
from ontowiz_ctx.core.hydration_protocol import build_system_prompt
from ontowiz_ctx.core.model import CTXDocument, Header, KeyValue, Layer, Section
from ontowiz_ctx.core.serializer import serialize
from ontowiz_spec import (
    ArtifactBase,
    InventoryEntry,
    Lifecycle,
    OutputFile,
    PackManifest,
)

# The manifest version every fresh candidate carries (v1 == unmarked/compat).
CANDIDATE_MANIFEST_VERSION = 2

# Control files that live in a candidate dir but are never payload / inventoried.
_CONTROL_FILES = frozenset({"pack.yaml", "pack.sig"})


# ── typed errors (all fatal; raised before any promote) ──────────────────────


class CompileError(Exception):
    """Base for deterministic-compile failures."""


class DuplicateArtifactIdentityError(CompileError):
    """Two inputs share the same (kind, id) logical identity."""


class DuplicateOutputPathError(CompileError):
    """Two payload files normalize to the same (case-folded) output path."""


class UnsafePackNameError(CompileError):
    """A pack name that could escape or corrupt the destination path."""


class UnsafePackVersionError(CompileError):
    """A pack version that is not a safe semver path component."""


class UnsafeCandidatePathError(CompileError):
    """The resolved candidate path escapes the destination root (reparse/symlink)."""


class StagedCandidateInvalidError(CompileError):
    """A staged candidate failed its own verification before promotion."""


class CandidateDigestConflictError(CompileError):
    """The target version already exists with a different candidate_digest."""


class CorruptCandidateError(CompileError):
    """An existing target matches the digest but fails verification (missing/tampered)."""


# ── canonicalization primitives (NFC + canonical JSON + sha256) ──────────────


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _nfc_obj(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc_obj(v) for v in value]
    if isinstance(value, dict):
        return {_nfc_obj(k): _nfc_obj(v) for k, v in value.items()}
    return value


def canonical_json(obj: object) -> bytes:
    """Deterministic JSON bytes: NFC-normalized, key-sorted, tight separators."""
    return json.dumps(
        _nfc_obj(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _content_digest(artifact: ArtifactBase) -> str:
    return _sha256_hex(canonical_json(artifact.model_dump(mode="json")))


# ── name / version safety (path components) ──────────────────────────────────

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
_RESERVED = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)}
)


def _validate_name(name: str) -> None:
    if not _NAME_RE.match(name) or name.lower() in _RESERVED:
        raise UnsafePackNameError(f"unsafe pack name {name!r}")


def _validate_version(version: str) -> None:
    if not _VERSION_RE.match(version) or version.lower() in _RESERVED:
        raise UnsafePackVersionError(f"unsafe pack version {version!r}")


@dataclass
class CompiledPack:
    """The output of the compiler — ready to write to disk or load into a runtime."""

    manifest: PackManifest
    l2_doc: CTXDocument
    l3_directory: str
    artifacts: list[ArtifactBase] = field(default_factory=list)

    def l2_text(self) -> str:
        """Serialize the L2 context layer to .ctx text."""
        return serialize(self.l2_doc)


def _section_name(artifact: ArtifactBase) -> str:
    """CTX section name — must match [A-Z][A-Z0-9_-]* (uppercase directory key).

    The original (case-preserving) id is kept in the section's ID field.
    """
    raw = re.sub(r"[^A-Z0-9_-]", "-", f"{artifact.kind.value}-{artifact.id}".upper())
    return raw if raw[:1].isalpha() else f"A-{raw}"


# The governance/meta fields every artifact shares — everything else is the
# kind-specific *knowledge* an agent actually needs.
_META_FIELDS = set(ArtifactBase.model_fields)


def _safe_inline(value: str) -> str:
    """Collapse a value to a single CTX-safe line.

    Three CTX control constructs must be neutralised so a field value cannot
    corrupt the document on re-parse: a newline (forges a section), an *unbalanced*
    bracket (the parser continues a value across lines until brackets balance — an
    unclosed ``[`` in a regex/array index would silently swallow the next
    section), and a backtick (opens a quoted block). We collapse whitespace and
    map ``[]`` → ``()`` and `` ` `` → ``'``.
    """
    s = re.sub(r"\s+", " ", str(value)).strip()
    return s.replace("[", "(").replace("]", ")").replace("`", "'")


def _one_line(value: str) -> str:
    return _safe_inline(value)


def _render_value(value: object) -> str:
    """Render a content value as readable text (no Python repr brackets/quotes)."""
    if isinstance(value, list):
        return ", ".join(_render_value(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}={_render_value(v)}" for k, v in value.items())
    return str(value)


def _knowledge_body(artifact: ArtifactBase) -> str:
    """The artifact's content fields rendered to one safe line (the actual knowledge)."""
    data = artifact.model_dump(mode="json")
    parts = [
        f"{k}={_render_value(data[k])}"
        for k in data
        if k not in _META_FIELDS and data[k] not in (None, "", [], {})
    ]
    return _safe_inline("; ".join(parts)) or _safe_inline(artifact.to_prompt_text())


def _artifact_section(artifact: ArtifactBase) -> Section:
    """One CTX section per artifact — the hydratable unit of knowledge.

    Carries the artifact's kind-specific content as a BODY field, not just
    metadata, so an agent that hydrates this section receives the domain content.
    """
    return Section(
        name=_section_name(artifact),
        children=(
            KeyValue(key="ID", value=_one_line(artifact.id)),
            KeyValue(key="NAME", value=_one_line(artifact.name)),
            KeyValue(key="KIND", value=artifact.kind.value),
            KeyValue(key="LIFECYCLE", value=artifact.lifecycle.value),
            KeyValue(key="CONFIDENCE", value=f"{artifact.confidence:.2f}"),
            KeyValue(key="BODY", value=_knowledge_body(artifact)),
        ),
    )


# ── deterministic identity, injective paths, reproducible digest ─────────────


def _reject_duplicate_identity(active: list[ArtifactBase]) -> None:
    counts = Counter((a.kind.value, a.id) for a in active)
    dupes = sorted(k for k, c in counts.items() if c > 1)
    if dupes:
        raise DuplicateArtifactIdentityError(f"duplicate (kind, id) identities: {dupes}")


def _safe_id(raw: str) -> str:
    """Map an artifact id to a filesystem-safe token (case preserved)."""
    return re.sub(r"[^A-Za-z0-9._-]", "-", raw)


def _output_path(artifact: ArtifactBase) -> str:
    """Injective-by-construction payload path: ``artifacts/<kind>__<id>.yaml``.

    Kind-prefixing keeps same-``id``/different-``kind`` artifacts on distinct
    paths; the case-folded guard in ``_assert_injective_paths`` is the backstop.
    """
    return f"artifacts/{artifact.kind.value}__{_safe_id(artifact.id)}.yaml"


def _assert_injective_paths(paths: list[str]) -> None:
    """Reject any two payload paths that collide under case-folding (before staging)."""
    seen: dict[str, str] = {}
    for p in paths:
        key = p.casefold()
        if key in seen:
            raise DuplicateOutputPathError(
                f"output paths {seen[key]!r} and {p!r} collide under case-folding"
            )
        seen[key] = p


def _render_payload(pack: CompiledPack) -> list[tuple[str, bytes]]:
    """Deterministic payload bytes: ``[(pack-relative-path, bytes), ...]``.

    Pure function of the CompiledPack — same pack ⇒ identical bytes. All text is
    NFC-normalized, LF, UTF-8. Guards output-path injectivity before returning.
    """
    items: list[tuple[str, bytes]] = []
    for a in pack.artifacts:
        text = yaml.safe_dump(a.model_dump(mode="json"), sort_keys=False, allow_unicode=True)
        items.append((_output_path(a), _nfc(text).encode("utf-8")))
    items.append(("context.ctx", _nfc(pack.l2_text()).encode("utf-8")))
    items.append(("index.l3.ctx", _nfc(pack.l3_directory).encode("utf-8")))
    _assert_injective_paths([p for p, _ in items])
    return items


def _candidate_digest(m: PackManifest) -> str:
    """Reproducible content id over an explicit allowlist (no self-reference).

    Reads each payload file's digest out of ``output_inventory`` rather than
    re-hashing files, and excludes ``candidate_digest`` itself — so it is
    well-defined and independent of time, order, and working directory.
    """
    core = {
        "manifest_version": CANDIDATE_MANIFEST_VERSION,
        "name": m.name,
        "version": m.version,
        "domain": m.domain,
        "author": m.author,
        "description": m.description,
        "layers": [layer.model_dump(mode="json") for layer in m.layers],
        "depends_on": list(m.depends_on),
        "input_inventory": [e.model_dump(mode="json") for e in m.input_inventory],
        "output_inventory": [o.model_dump(mode="json") for o in m.output_inventory],
        "releasable": m.releasable,
        "candidate_status": m.candidate_status,
    }
    return _sha256_hex(canonical_json(core))


# ── compile ──────────────────────────────────────────────────────────────────


def _build_context(
    active: list[ArtifactBase], *, name: str, version: str, domain: str
) -> tuple[CTXDocument, str]:
    """Build the L2 doc (one section per artifact) + L3 directory; reject collisions."""
    sections = [_artifact_section(a) for a in active]
    seen: dict[str, str] = {}
    for a, sec in zip(active, sections, strict=True):
        if sec.name in seen:
            raise ValueError(
                f"section-name collision {sec.name!r}: artifacts {seen[sec.name]!r} "
                f"and {a.id!r} would overwrite each other in the pack"
            )
        seen[sec.name] = a.id
    header = Header(
        magic="§CTX",
        version="1.0",
        layer=Layer.L2,
        status_fields=(KeyValue(key="DOMAIN", value=domain or name),),
        metadata=(KeyValue(key="PACK", value=name), KeyValue(key="VERSION", value=version)),
    )
    l2_doc = CTXDocument(header=header, body=tuple(sections))
    return l2_doc, build_system_prompt(l2_doc)


def _build_manifest(
    active: list[ArtifactBase],
    *,
    name: str,
    version: str,
    description: str,
    domain: str,
    author: str,
) -> PackManifest:
    """Manifest with exact input inventory; empty pack ⇒ non-releasable diagnostic."""
    return PackManifest(
        manifest_version=CANDIDATE_MANIFEST_VERSION,
        name=name,
        version=version,
        description=description,
        domain=domain or name,
        author=author,
        artifact_count=len(active),
        artifact_kinds=dict(Counter(a.kind.value for a in active)),
        input_inventory=[
            InventoryEntry(id=a.id, kind=a.kind.value, content_digest=_content_digest(a))
            for a in active  # already sorted by (kind, id)
        ],
        releasable=bool(active),
        candidate_status="candidate" if active else "diagnostic",
    )


def _finalize_inventory(pack: CompiledPack) -> None:
    """Set output_inventory + candidate_digest from the in-memory payload (pure)."""
    payload = _render_payload(pack)
    pack.manifest.output_inventory = sorted(
        (OutputFile(path=p, byte_count=len(b), sha256=_sha256_hex(b)) for p, b in payload),
        key=lambda o: o.path,
    )
    pack.manifest.candidate_digest = _candidate_digest(pack.manifest)


def compile_pack(
    artifacts: list[ArtifactBase],
    *,
    name: str,
    version: str,
    description: str = "",
    domain: str = "",
    author: str = "ontowiz",
) -> CompiledPack:
    """Compile ACTIVE artifacts into a deterministic, digest-addressed Domain Pack."""
    _validate_name(name)
    _validate_version(version)
    active = [a for a in artifacts if a.lifecycle == Lifecycle.ACTIVE]
    _reject_duplicate_identity(active)
    active.sort(key=lambda a: (a.kind.value, a.id))  # stable order → byte-identical
    l2_doc, l3_directory = _build_context(active, name=name, version=version, domain=domain)
    manifest = _build_manifest(
        active, name=name, version=version, description=description, domain=domain, author=author
    )
    pack = CompiledPack(
        manifest=manifest, l2_doc=l2_doc, l3_directory=l3_directory, artifacts=active
    )
    _finalize_inventory(pack)
    return pack


# Persistence API (fresh staging, atomic promote, conflict, verification) lives
# in writer.py; imported at the bottom to break the module cycle and re-exported
# so ``from ontowiz_factory.compiler import write_pack`` keeps working.
from .writer import (  # noqa: E402
    reseal_pack,
    verify_candidate_dir,
    verify_pack,
    write_pack,
)

__all__ = [
    "CompiledPack",
    "compile_pack",
    "write_pack",
    "verify_pack",
    "verify_candidate_dir",
    "reseal_pack",
    "canonical_json",
    "CompileError",
    "DuplicateArtifactIdentityError",
    "DuplicateOutputPathError",
    "UnsafePackNameError",
    "UnsafePackVersionError",
    "UnsafeCandidatePathError",
    "StagedCandidateInvalidError",
    "CandidateDigestConflictError",
    "CorruptCandidateError",
]
