"""Pack version diff (Tier A, read-only) — the catalog's "how it evolves" view.

Compares two loaded pack versions and reports what changed: artifacts added,
removed, or changed in content, plus the per-function slice deltas. Pure derived
data over two LoadedPacks — no factory, no network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ontowiz_spec import ArtifactBase

from .catalog import function_counts
from .registry import LoadedPack

# Governance/meta fields change with every transition; compare only the knowledge.
_META_FIELDS = set(ArtifactBase.model_fields)


@dataclass
class DiffResult:
    """What changed between two pack versions."""

    name: str
    from_version: str
    to_version: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    function_deltas: dict[str, dict[str, int]] = field(default_factory=dict)


def _content_sig(artifact: ArtifactBase) -> str:
    """A stable signature of an artifact's *knowledge* (meta/governance excluded)."""
    data = artifact.model_dump(mode="json")
    knowledge = {k: v for k, v in data.items() if k not in _META_FIELDS}
    return json.dumps(knowledge, sort_keys=True)


def pack_diff(a: LoadedPack, b: LoadedPack) -> DiffResult:
    """Diff pack ``a`` (from) against pack ``b`` (to)."""
    a_by = {art.id: art for art in a.artifacts}
    b_by = {art.id: art for art in b.artifacts}
    a_ids, b_ids = set(a_by), set(b_by)

    added = sorted(b_ids - a_ids)
    removed = sorted(a_ids - b_ids)
    changed = sorted(
        i for i in (a_ids & b_ids) if _content_sig(a_by[i]) != _content_sig(b_by[i])
    )

    fa, fb = function_counts(a.artifacts), function_counts(b.artifacts)
    deltas: dict[str, dict[str, int]] = {}
    for fn in sorted(set(fa) | set(fb)):
        before, after = fa.get(fn, 0), fb.get(fn, 0)
        if before != after:
            deltas[fn] = {"from": before, "to": after, "delta": after - before}

    return DiffResult(
        name=b.manifest.name,
        from_version=a.manifest.version,
        to_version=b.manifest.version,
        added=added, removed=removed, changed=changed, function_deltas=deltas,
    )
