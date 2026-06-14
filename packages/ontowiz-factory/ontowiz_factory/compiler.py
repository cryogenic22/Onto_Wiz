"""Pack compiler — governed artifacts → a compiled Domain Pack.

Turns ACTIVE artifacts into a CompiledPack: a CTX L2 context layer (one section
per artifact), a hydration directory (the agent's map, via CTX's LLM-as-router
protocol), and a PackManifest. Only ACTIVE artifacts enter a pack — governance
is enforced at compile time, before anything can be served.

Tier B (factory): may import Tier A (ontowiz_spec, ontowiz_ctx).
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from ontowiz_ctx.core.hydration_protocol import build_system_prompt
from ontowiz_ctx.core.model import CTXDocument, Header, KeyValue, Layer, Section
from ontowiz_ctx.core.serializer import serialize
from ontowiz_spec import ArtifactBase, Lifecycle, PackManifest


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


def compile_pack(
    artifacts: list[ArtifactBase],
    *,
    name: str,
    version: str,
    description: str = "",
    domain: str = "",
    author: str = "ontowiz",
) -> CompiledPack:
    """Compile ACTIVE artifacts into a Domain Pack (manifest + CTX layer)."""
    active = [a for a in artifacts if a.lifecycle == Lifecycle.ACTIVE]

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
    l3_directory = build_system_prompt(l2_doc)

    kinds = Counter(a.kind.value for a in active)
    manifest = PackManifest(
        name=name,
        version=version,
        description=description,
        domain=domain or name,
        author=author,
        artifact_count=len(active),
        artifact_kinds=dict(kinds),
    )
    return CompiledPack(manifest=manifest, l2_doc=l2_doc, l3_directory=l3_directory, artifacts=active)


def _pack_digest(pack_dir: Path) -> str:
    """SHA-256 over the pack's content files (artifacts + ctx + l3 + manifest).

    A tamper-evident *integrity seal* — it detects any post-compile edit of a pack
    file. (It is a content digest, not a PKI signature: it proves the bytes are
    unchanged since write, not authorship. Cryptographic authorship signing is
    roadmap; see PROJECT_STATUS.)
    """
    h = hashlib.sha256()
    files = sorted((pack_dir / "artifacts").glob("*.yaml"))
    files += [pack_dir / "context.ctx", pack_dir / "index.l3.ctx", pack_dir / "pack.yaml"]
    for f in files:
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def write_pack(pack: CompiledPack, dest_root: str | Path) -> Path:
    """Write a CompiledPack to ``dest_root/<name>/<version>/``. Returns the pack dir.

    Layout (the on-disk contract, see PackManifest): artifacts/*.yaml + the
    compiled .ctx context layer + the L3 directory + pack.yaml manifest + a
    ``pack.sig`` integrity seal (SHA-256 over the above).
    """
    pack_dir = Path(dest_root) / pack.manifest.name / pack.manifest.version
    (pack_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    for artifact in pack.artifacts:
        (pack_dir / "artifacts" / f"{artifact.id}.yaml").write_text(
            yaml.safe_dump(artifact.model_dump(mode="json"), sort_keys=False), encoding="utf-8"
        )
    (pack_dir / pack.manifest.ctx_l2_path).write_text(pack.l2_text(), encoding="utf-8")
    (pack_dir / pack.manifest.ctx_l3_path).write_text(pack.l3_directory, encoding="utf-8")
    pack.manifest.signed = True
    (pack_dir / "pack.yaml").write_text(
        yaml.safe_dump(pack.manifest.model_dump(mode="json"), sort_keys=False), encoding="utf-8"
    )
    (pack_dir / "pack.sig").write_text(_pack_digest(pack_dir), encoding="utf-8")
    return pack_dir


def verify_pack(pack_dir: str | Path) -> bool:
    """True if the pack's ``pack.sig`` matches a freshly-computed digest (untampered)."""
    pack_dir = Path(pack_dir)
    sig_file = pack_dir / "pack.sig"
    if not sig_file.is_file():
        return False
    return sig_file.read_text(encoding="utf-8").strip() == _pack_digest(pack_dir)


def reseal_pack(pack_dir: str | Path) -> str:
    """Recompute and rewrite ``pack.sig`` for an in-place edited pack.

    A governed post-compile edit (e.g. writing eval results into the manifest)
    changes the pack's bytes and would otherwise leave the integrity seal stale.
    Re-sealing keeps ``verify_pack`` honest after such an authorised change.
    """
    pack_dir = Path(pack_dir)
    digest = _pack_digest(pack_dir)
    (pack_dir / "pack.sig").write_text(digest, encoding="utf-8")
    return digest
