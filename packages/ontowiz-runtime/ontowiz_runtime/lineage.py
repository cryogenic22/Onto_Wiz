"""Knowledge Workbench lineage (Loop 5 / UX-3) — Tier A, read-only.

"Explain this definition": given a concept, trace it to the governed artifacts
behind it and surface each one's provenance — source documents, confidence,
whether an agent actually sees it (served), eval coverage, and how many governed
transitions it has survived. The Workbench renders this as the lineage story.
"""

from __future__ import annotations

from dataclasses import dataclass

from ontowiz_spec import SERVABLE_STATES, ArtifactBase, ArtifactKind, EvalCase

from .registry import LoadedPack


@dataclass
class LineageEntry:
    """One artifact in a concept's lineage, with its provenance."""

    artifact_id: str
    kind: str
    name: str
    lifecycle: str
    served: bool
    confidence: float
    sources: list[str]  # source_document_ids
    has_eval: bool
    governance_steps: int  # length of the governed lifecycle history


def _matches(artifact: ArtifactBase, needle: str) -> bool:
    haystack = f"{artifact.name}\n{artifact.to_prompt_text()}".lower()
    return needle in haystack


def explain_concept(loaded: LoadedPack, concept: str) -> list[LineageEntry]:
    """Trace ``concept`` to the governed artifacts behind it, served first."""
    needle = concept.strip().lower()
    if not needle:
        return []
    covered: set[str] = set()
    for a in loaded.artifacts:
        if a.kind == ArtifactKind.EVAL_CASE and isinstance(a, EvalCase):
            covered.update(a.validates)

    entries: list[LineageEntry] = []
    for a in loaded.artifacts:
        # eval cases are the proof, not the belief — don't list them as lineage
        if a.kind == ArtifactKind.EVAL_CASE or not _matches(a, needle):
            continue
        entries.append(
            LineageEntry(
                artifact_id=a.id,
                kind=a.kind.value,
                name=a.name,
                lifecycle=a.lifecycle.value,
                served=a.lifecycle in SERVABLE_STATES,
                confidence=a.confidence,
                sources=list(a.source_document_ids),
                has_eval=a.id in covered,
                governance_steps=len(a.lifecycle_history),
            )
        )
    entries.sort(key=lambda e: (e.served, e.confidence), reverse=True)
    return entries
