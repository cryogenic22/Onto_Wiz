"""Pack Registry detail view (Loop 5 / UX-2) — Tier A, read-only.

Turns a LoadedPack into the data behind the Registry UI: an artifact explorer
(each row flagged served / eval-covered) plus the gaps list (served artifacts
with no eval) that the Forge auto-converts into curation missions. Pure derived
data — no factory, no governance, no network.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ontowiz_spec import SERVABLE_STATES, ArtifactBase, ArtifactKind, EvalCase

from .registry import LoadedPack


@dataclass
class ArtifactRow:
    """One row in the artifact explorer."""

    id: str
    kind: str
    name: str
    lifecycle: str
    confidence: float
    served: bool  # lifecycle in SERVABLE_STATES → reaches agents
    has_eval: bool  # validated by some EvalCase in the pack


@dataclass
class PackDetail:
    """The registry detail payload for one pack."""

    name: str
    version: str
    description: str
    artifact_count: int
    artifact_kinds: dict[str, int]
    evals: dict[str, object]
    coverage: float
    artifacts: list[ArtifactRow] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)  # served artifact ids missing eval


def _eval_covered_ids(artifacts: list[ArtifactBase]) -> set[str]:
    covered: set[str] = set()
    for a in artifacts:
        if a.kind == ArtifactKind.EVAL_CASE and isinstance(a, EvalCase):
            covered.update(a.validates)
    return covered


def pack_detail(loaded: LoadedPack) -> PackDetail:
    """Derive the registry detail view (artifact explorer + gaps) from a pack."""
    covered = _eval_covered_ids(loaded.artifacts)
    rows: list[ArtifactRow] = []
    gaps: list[str] = []
    for a in loaded.artifacts:
        served = a.lifecycle in SERVABLE_STATES
        has_eval = a.id in covered
        rows.append(
            ArtifactRow(
                id=a.id,
                kind=a.kind.value,
                name=a.name,
                lifecycle=a.lifecycle.value,
                confidence=a.confidence,
                served=served,
                has_eval=has_eval,
            )
        )
        # A gap is something agents see (served) that no eval proves — exclude
        # eval cases themselves, which are never "served" knowledge.
        if served and not has_eval and a.kind != ArtifactKind.EVAL_CASE:
            gaps.append(a.id)

    m = loaded.manifest
    return PackDetail(
        name=m.name,
        version=m.version,
        description=m.description,
        artifact_count=m.artifact_count or len(loaded.artifacts),
        artifact_kinds=dict(m.artifact_kinds),
        evals=m.evals.model_dump(mode="json"),
        coverage=m.coverage,
        artifacts=rows,
        gaps=gaps,
    )
