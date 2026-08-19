"""On-disk candidate persistence — fresh staging, atomic promote, verification.

The write/verify half of S1.1 (the compile half is ``compiler.py``). A candidate
is staged into a unique sibling dir, its staged bytes are verified, then it is
promoted by atomic create-or-fail rename; a same-version different-digest target
conflicts rather than being overwritten. ``verify_candidate_dir`` is the exact
inventory + seal checker reused by S1.2 at load time.

Public API is re-exported from ``compiler`` for backward compatibility.

Tier B (factory): may import Tier A (ontowiz_spec, ontowiz_ctx).
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path

import yaml
from ontowiz_spec import PackManifest

from .compiler import (
    _CONTROL_FILES,
    CANDIDATE_MANIFEST_VERSION,
    CandidateDigestConflictError,
    CompiledPack,
    CorruptCandidateError,
    StagedCandidateInvalidError,
    UnsafeCandidatePathError,
    _candidate_digest,
    _nfc,
    _render_payload,
    _sha256_hex,
    _validate_name,
    _validate_version,
)

# The exact payload-path grammar the verifier trusts. A declared inventory path
# is either one of the two fixed CTX files or a single-level artifacts/*.yaml —
# no directory traversal, absolute path, drive, or control file can match.
_FIXED_PAYLOAD = frozenset({"context.ctx", "index.l3.ctx"})
_PAYLOAD_RE = re.compile(r"^artifacts/[A-Za-z0-9._-]+\.yaml$")


def _valid_payload_path(path: str) -> bool:
    return path in _FIXED_PAYLOAD or bool(_PAYLOAD_RE.match(path))


def _paths_are_safe(output_inventory: list) -> bool:
    """Every declared path matches the payload grammar and is unique (case-folded).

    Validated **before** any filesystem access, so a malicious manifest cannot
    steer ``verify_candidate_dir`` into hashing files outside the candidate, nor
    declare a control file, traversal, absolute path, or duplicate.
    """
    seen: set[str] = set()
    for o in output_inventory:
        key = o.path.casefold()
        if not _valid_payload_path(o.path) or key in seen:
            return False
        seen.add(key)
    return True


def _pack_digest(pack_dir: Path) -> str:
    """SHA-256 integrity seal over the pack's files (payload + manifest).

    A tamper-evident *byte-integrity* seal — it detects any post-write edit of a
    pack file, including ``pack.yaml`` (whose ``candidate_digest`` field it
    covers). Distinct job from ``candidate_digest`` (portable content identity):
    ``pack.sig`` is *byte integrity as-written*. Now reproducible, because the
    candidate carries no volatile value. Excludes ``pack.sig`` itself.
    """
    h = hashlib.sha256()
    files = sorted((pack_dir / "artifacts").glob("*.yaml"))
    files += [pack_dir / "context.ctx", pack_dir / "index.l3.ctx", pack_dir / "pack.yaml"]
    for f in files:
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def _serialize_candidate_manifest(m: PackManifest) -> str:
    """Serialize ``pack.yaml`` from an explicit allowlist.

    The candidate carries only {digest core} ∪ {candidate_digest} ∪ {fixed
    deterministic fields}. Mutable/clock fields (evals, coverage, freshness_days,
    compiled_at) and roadmap placeholders (encrypted, license_id) are **omitted**,
    so nothing a caller mutates can change candidate bytes under a fixed digest.
    Every retained non-core field is a constant or is derived from the digest core.
    """
    doc = {
        "manifest_version": CANDIDATE_MANIFEST_VERSION,
        "name": m.name,
        "version": m.version,
        "description": m.description,
        "domain": m.domain,
        "author": m.author,
        "compiler_version": m.compiler_version,   # fixed build constant
        "signed": True,                           # fixed: a written candidate is sealed
        "layers": [layer.model_dump(mode="json") for layer in m.layers],
        "depends_on": list(m.depends_on),
        "artifact_count": m.artifact_count,       # derived from input_inventory
        "artifact_kinds": dict(m.artifact_kinds),  # derived from input_inventory
        "candidate_digest": m.candidate_digest,
        "input_inventory": [e.model_dump(mode="json") for e in m.input_inventory],
        "output_inventory": [o.model_dump(mode="json") for o in m.output_inventory],
        "releasable": m.releasable,
        "candidate_status": m.candidate_status,
        "ctx_l2_path": m.ctx_l2_path,             # fixed pointer (also in output_inventory)
        "ctx_l3_path": m.ctx_l3_path,
    }
    return _nfc(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))


def _read_manifest(pack_dir: Path) -> PackManifest:
    data = yaml.safe_load((pack_dir / "pack.yaml").read_text(encoding="utf-8"))
    return PackManifest.model_validate(data if isinstance(data, dict) else {})


def _no_symlinks_and_only_declared(pack_dir: Path, declared: set[str]) -> bool:
    """No symlink/reparse entry anywhere, and every real file is control or declared."""
    for p in pack_dir.rglob("*"):
        if p.is_symlink():                    # reject before it can point outside
            return False
        if p.is_file():
            rel = p.relative_to(pack_dir).as_posix()
            if rel not in _CONTROL_FILES and rel not in declared:
                return False
    return True


def _within(root_real: str, fp: Path) -> bool:
    try:
        return os.path.commonpath([root_real, os.path.realpath(fp)]) == root_real
    except ValueError:                        # different drive/UNC on Windows
        return False


def _declared_files_match(pack_dir: Path, output_inventory: list) -> bool:
    """Every declared payload file is present, a contained non-symlink, and byte-exact."""
    root_real = os.path.realpath(pack_dir)
    for o in output_inventory:
        fp = pack_dir / o.path
        if fp.is_symlink() or not fp.is_file() or not _within(root_real, fp):
            return False
        data = fp.read_bytes()
        if len(data) != o.byte_count or _sha256_hex(data) != o.sha256:
            return False
    return True


def verify_candidate_dir(pack_dir: str | Path) -> bool:
    """True iff the directory is an exactly-inventoried, untampered v2 candidate.

    Fixed order: parse manifest → reject undeclared/unexpected file → require every
    declared payload present & matching → recompute candidate_digest → recompute
    the ``pack.sig`` seal. Reused by S1.1 at staging-verify time and by S1.2 at load.
    """
    pack_dir = Path(pack_dir)
    sig_path = pack_dir / "pack.sig"
    if not (pack_dir / "pack.yaml").is_file() or not sig_path.is_file():
        return False
    try:
        m = _read_manifest(pack_dir)
    except Exception:
        return False
    if m.manifest_version != CANDIDATE_MANIFEST_VERSION:
        return False
    if not _paths_are_safe(m.output_inventory):   # grammar + uniqueness, BEFORE fs access
        return False
    declared = {o.path for o in m.output_inventory}
    if not _no_symlinks_and_only_declared(pack_dir, declared):
        return False
    if not _declared_files_match(pack_dir, m.output_inventory):
        return False
    if _candidate_digest(m) != m.candidate_digest:
        return False
    return sig_path.read_text(encoding="utf-8").strip() == _pack_digest(pack_dir)


def _assert_within_root(dest_root: Path, target: Path) -> None:
    """Refuse a candidate path that escapes the root via symlink/junction/traversal."""
    root_real = Path(os.path.realpath(dest_root))
    node = target
    while not node.exists():
        node = node.parent
    node_real = Path(os.path.realpath(node))
    if node_real != root_real and root_real not in node_real.parents:
        raise UnsafeCandidatePathError(
            f"candidate path {target} escapes destination root {dest_root}"
        )


def _materialize(pack: CompiledPack, staging: Path) -> None:
    (staging / "artifacts").mkdir(parents=True, exist_ok=True)
    for rel, data in _render_payload(pack):
        fp = staging / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_bytes(data)
    (staging / "pack.yaml").write_text(
        _serialize_candidate_manifest(pack.manifest), encoding="utf-8"
    )
    # Seal last, over the frozen payload + manifest (never over pack.sig itself).
    (staging / "pack.sig").write_text(_pack_digest(staging), encoding="utf-8")


def write_pack(pack: CompiledPack, dest_root: str | Path) -> Path:
    """Write a CompiledPack to ``dest_root/<name>/<version>/``, fresh + atomic.

    Stages into a unique sibling dir, verifies the staged bytes, then promotes by
    atomic create-or-fail rename. A pre-existing target with the **same**
    candidate_digest is idempotent success; a **different** digest (including a v1
    target, whose digest is ``""``) raises ``CandidateDigestConflictError`` —
    ``write_pack`` never overwrites or migrates in place. Returns the pack dir.
    """
    m = pack.manifest
    _validate_name(m.name)
    _validate_version(m.version)
    dest_root = Path(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    parent = dest_root / m.name
    target = parent / m.version
    _assert_within_root(dest_root, target)
    parent.mkdir(parents=True, exist_ok=True)

    staging = Path(tempfile.mkdtemp(prefix=f".staging-{m.version}-", dir=parent))
    try:
        _materialize(pack, staging)
        if not verify_candidate_dir(staging):
            raise StagedCandidateInvalidError(
                f"staged candidate failed verification: {m.name}@{m.version}"
            )
        try:
            os.rename(staging, target)          # atomic; fails if target exists
        except OSError:
            if not target.exists():
                raise                            # a real error, not a promote race
            existing = _read_manifest(target)
            if existing.candidate_digest and existing.candidate_digest == m.candidate_digest:
                # Same-digest target — only idempotent if it is actually intact on
                # disk. A missing/tampered/bad-seal target must not report success.
                if not verify_candidate_dir(target):
                    raise CorruptCandidateError(
                        f"existing {m.name}@{m.version} has candidate_digest "
                        f"{m.candidate_digest} but failed verification "
                        f"(missing, tampered, or bad seal)"
                    ) from None
                return target                    # idempotent: same version, verified bytes
            raise CandidateDigestConflictError(
                f"{m.name}@{m.version} already present with a different candidate_digest "
                f"(existing={existing.candidate_digest!r}, new={m.candidate_digest!r}); "
                f"bump the version"
            ) from None
        return target
    finally:
        shutil.rmtree(staging, ignore_errors=True)


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
    (S1.3 removes the eval-mutation path this exists for; retained here unchanged.)
    """
    pack_dir = Path(pack_dir)
    digest = _pack_digest(pack_dir)
    (pack_dir / "pack.sig").write_text(digest, encoding="utf-8")
    return digest
