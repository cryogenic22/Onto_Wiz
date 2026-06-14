"""Catalog index + search (Tier A, read-only) — the data behind the catalog grid.

Turns a PackRegistry into one rich entry per pack (grouped across versions): its
domain, every version (latest first), artifact count, the function slices it
sub-divides into, and the eval/lift summary from the latest manifest. Pure
derived data over the registry — no factory, no network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ontowiz_spec import (
    SERVABLE_STATES,
    ArtifactBase,
    ArtifactKind,
    EvalCase,
    PackManifest,
    TagDimension,
)

from .context import context_for_function, context_for_pack
from .registry import LoadedPack, PackRegistry


@dataclass
class CatalogEntry:
    """One pack in the catalog, summarised across its versions."""

    name: str
    domain: str
    description: str
    latest_version: str
    versions: list[str]                              # descending semver order
    artifact_count: int
    functions: dict[str, int]                        # function tag → artifact count
    signed: bool
    eval_cases: int
    pass_rate: float
    agent_lift: float | None
    coverage: float


@dataclass
class FunctionSlice:
    """One function the pack sub-divides into, with coverage + token leanness."""

    function: str
    count: int
    served_count: int
    eval_count: int
    slice_tokens: int    # directory size when only this slice is served
    full_tokens: int     # directory size for the whole pack (the baseline)


def _eval_covered_ids(artifacts: list[ArtifactBase]) -> set[str]:
    covered: set[str] = set()
    for a in artifacts:
        if a.kind == ArtifactKind.EVAL_CASE and isinstance(a, EvalCase):
            covered.update(a.validates)
    return covered


def pack_functions(loaded: LoadedPack) -> list[FunctionSlice]:
    """Per-function slice view of a pack: counts, eval coverage, token leanness.

    ``slice_tokens`` vs ``full_tokens`` quantifies the functionalization payoff —
    serving one function ships a smaller L3 directory than the whole pack. Both
    reuse the real serving path (``context_for_function`` / ``context_for_pack``).
    """
    covered = _eval_covered_ids(loaded.artifacts)
    full_tokens = context_for_pack("", loaded).tokens_estimate
    slices: list[FunctionSlice] = []
    for function in function_counts(loaded.artifacts):
        members = [
            a for a in loaded.artifacts
            if any(t.dimension == TagDimension.FUNCTION and t.value == function for t in a.tags)
        ]
        slices.append(
            FunctionSlice(
                function=function,
                count=len(members),
                served_count=sum(1 for a in members if a.lifecycle in SERVABLE_STATES),
                eval_count=sum(1 for a in members if a.id in covered),
                slice_tokens=context_for_function("", loaded, function).tokens_estimate,
                full_tokens=full_tokens,
            )
        )
    return slices


def _ver_key(version: str) -> tuple[int, ...]:
    """Semver-ish sort key — numeric components so 0.10.0 > 0.9.0."""
    parts: list[int] = []
    for piece in version.split("."):
        digits = "".join(c for c in piece if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def function_counts(artifacts: list[ArtifactBase]) -> dict[str, int]:
    """Count artifacts per FUNCTION tag value — the pack's function slices."""
    counts: dict[str, int] = {}
    for a in artifacts:
        for t in a.tags:
            if t.dimension == TagDimension.FUNCTION:
                counts[t.value] = counts.get(t.value, 0) + 1
    return dict(sorted(counts.items()))


def _entry_for(name: str, manifests: list[PackManifest], loaded: LoadedPack) -> CatalogEntry:
    versions = [m.version for m in sorted(manifests, key=lambda m: _ver_key(m.version), reverse=True)]
    m = loaded.manifest
    return CatalogEntry(
        name=name,
        domain=m.domain or name,
        description=m.description,
        latest_version=m.version,
        versions=versions,
        artifact_count=m.artifact_count or len(loaded.artifacts),
        functions=function_counts(loaded.artifacts),
        signed=m.signed,
        eval_cases=m.evals.eval_cases,
        pass_rate=m.evals.pass_rate,
        agent_lift=m.evals.agent_lift,
        coverage=m.coverage,
    )


@dataclass
class SearchHit:
    """A pack that matched a catalog search, with the artifacts that matched."""

    name: str
    domain: str
    latest_version: str
    score: int
    functions: dict[str, int]
    matched_artifacts: list[dict[str, str]] = field(default_factory=list)


def _terms(query: str) -> set[str]:
    return {t for t in re.findall(r"\w+", query.lower()) if len(t) > 2}


def catalog_search(
    registry: PackRegistry,
    query: str,
    *,
    function: str | None = None,
    domain: str | None = None,
) -> list[SearchHit]:
    """Rank packs by lexical overlap with ``query`` (name/desc/domain + artifacts).

    Empty query lists every pack (honouring the filters). ``function``/``domain``
    narrow the set the way the catalog's filter chips do. Matching artifacts are
    surfaced so the UI can deep-link straight to the relevant heuristic.
    """
    terms = _terms(query)
    hits: list[SearchHit] = []
    for entry in catalog_index(registry):
        if function and function not in entry.functions:
            continue
        if domain and entry.domain != domain:
            continue
        loaded = registry.load(entry.name, entry.latest_version)
        pack_text = f"{entry.name} {entry.description} {entry.domain}".lower()
        score = sum(1 for t in terms if t in pack_text)
        matched: list[dict[str, str]] = []
        for a in loaded.artifacts:
            text = f"{a.name} {a.to_prompt_text()}".lower()
            if terms and any(t in text for t in terms):
                matched.append({"id": a.id, "name": a.name})
                score += 1
        if terms and score == 0:
            continue  # a real query that matched nothing is not a hit
        hits.append(
            SearchHit(
                name=entry.name, domain=entry.domain, latest_version=entry.latest_version,
                score=score, functions=entry.functions, matched_artifacts=matched,
            )
        )
    return sorted(hits, key=lambda h: (-h.score, h.name))


def catalog_index(registry: PackRegistry) -> list[CatalogEntry]:
    """One CatalogEntry per pack name, using the latest version for the details."""
    by_name: dict[str, list[PackManifest]] = {}
    for m in registry.list_manifests():
        by_name.setdefault(m.name, []).append(m)

    entries: list[CatalogEntry] = []
    for name, manifests in by_name.items():
        latest = max(manifests, key=lambda m: _ver_key(m.version))
        loaded = registry.load(name, latest.version)
        entries.append(_entry_for(name, manifests, loaded))
    return sorted(entries, key=lambda e: e.name)
