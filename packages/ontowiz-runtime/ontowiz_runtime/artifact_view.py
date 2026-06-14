"""Single-artifact detail view (Tier A, read-only) — the catalog drawer's data.

Given a loaded pack and an artifact id, surface everything the catalog drawer
shows: the knowledge (summary, content fields, anti-patterns, trigger signals),
the relevance tags (function + therapy overlay), the provenance (sources + the
governed lifecycle history with delta ids), eval coverage, and the raw YAML.
Pure derived data — no factory, no network.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml
from ontowiz_spec import (
    SERVABLE_STATES,
    ArtifactBase,
    ArtifactKind,
    EvalCase,
    TagDimension,
)

from .registry import LoadedPack

# Governance/meta fields shared by every artifact — everything else is knowledge.
_META_FIELDS = set(ArtifactBase.model_fields)


@dataclass
class ArtifactView:
    """The full detail of one artifact, for the catalog drawer."""

    id: str
    kind: str
    name: str
    lifecycle: str
    served: bool
    confidence: float
    function: str | None
    therapy: str | None
    summary: str
    content: dict[str, object]
    anti_patterns: list[dict[str, str]]
    trigger_signals: list[dict[str, object]]
    sources: list[str]
    governance: list[dict[str, object]]
    has_eval: bool
    yaml: str = ""
    tags: list[dict[str, str]] = field(default_factory=list)


def _tag_value(artifact: ArtifactBase, dimension: TagDimension) -> str | None:
    for t in artifact.tags:
        if t.dimension == dimension:
            return t.value
    return None


def _eval_covered_ids(artifacts: list[ArtifactBase]) -> set[str]:
    covered: set[str] = set()
    for a in artifacts:
        if a.kind == ArtifactKind.EVAL_CASE and isinstance(a, EvalCase):
            covered.update(a.validates)
    return covered


def artifact_view(loaded: LoadedPack, artifact_id: str) -> ArtifactView:
    """Build the detail view for one artifact in a pack. Raises KeyError if absent."""
    artifact = next((a for a in loaded.artifacts if a.id == artifact_id), None)
    if artifact is None:
        raise KeyError(artifact_id)

    data = artifact.model_dump(mode="json")
    content = {
        k: v for k, v in data.items()
        if k not in _META_FIELDS and v not in (None, "", [], {})
    }
    anti = [
        {"wrong_conclusion": str(ap.get("wrong_conclusion", "")),
         "why_wrong": str(ap.get("why_wrong", ""))}
        for ap in data.get("anti_patterns", []) or []
    ]
    governance: list[dict[str, object]] = []
    for t in artifact.lifecycle_history:
        governance.append({
            "from_state": t.from_state.value if t.from_state else None,
            "to_state": t.to_state.value,
            "changed_by": t.changed_by,
            "delta_id": t.delta_id,
            "at": t.at,
        })
    return ArtifactView(
        id=artifact.id,
        kind=artifact.kind.value,
        name=artifact.name,
        lifecycle=artifact.lifecycle.value,
        served=artifact.lifecycle in SERVABLE_STATES,
        confidence=artifact.confidence,
        function=_tag_value(artifact, TagDimension.FUNCTION),
        therapy=_tag_value(artifact, TagDimension.THERAPY_AREA),
        summary=artifact.to_prompt_text(),
        content=content,
        anti_patterns=anti,
        trigger_signals=list(data.get("trigger_signals", []) or []),
        sources=list(artifact.source_document_ids),
        governance=governance,
        has_eval=artifact.id in _eval_covered_ids(loaded.artifacts),
        yaml=yaml.safe_dump(data, sort_keys=False),
        tags=[{"dimension": t.dimension.value, "value": t.value} for t in artifact.tags],
    )
