"""Mining loop (Loop 1 of the 5) — extract candidate artifacts from text → Deltas.

A pattern-based MVP: finds if/then decision rules and data-lag caveats and emits
them as low-confidence DRAFT candidates, pushed into governance as PROPOSED
Deltas via the bridge. Nothing is served until an SME governs it.

Tier B (factory): may import ontowiz_core (bridge) + ontowiz_spec.
"""

from __future__ import annotations

import re

from ontowiz_core.bridge import propose_artifact
from ontowiz_core.models import Delta
from ontowiz_spec import ArtifactBase, DataQuirk, DecisionHeuristic, Tag, TagDimension

_IF_THEN = re.compile(r"\bif\s+(.+?)[,]?\s+(?:then\s+|=>\s*)(.+?)(?:\.|;|\n|$)", re.IGNORECASE)
_LAG = re.compile(
    r"\b([A-Z][\w ]{2,30}?)\s+(?:data\s+)?lags?\s+(?:by\s+)?(\d+\s*(?:days?|weeks?|months?))",
    re.IGNORECASE,
)


def mine_text(text: str, *, source_id: str = "", domain: str = "commercial") -> list[ArtifactBase]:
    """Extract candidate DRAFT artifacts from free text."""
    tag = Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value=domain)
    src = [source_id] if source_id else []
    out: list[ArtifactBase] = []

    for i, m in enumerate(_IF_THEN.finditer(text), start=1):
        cond, action = m.group(1).strip(), m.group(2).strip()
        out.append(
            DecisionHeuristic(
                id=f"mined-dh-{source_id or 'x'}-{i}",
                name=f"Mined heuristic {i}",
                decision_logic=f"if {cond} => {action}",
                confidence=0.4,
                source_document_ids=src,
                tags=[tag],
            )
        )

    for j, m in enumerate(_LAG.finditer(text), start=1):
        source, lag = m.group(1).strip(), m.group(2).strip()
        out.append(
            DataQuirk(
                id=f"mined-dq-{source_id or 'x'}-{j}",
                name=f"{source} lag",
                data_source=source,
                quirk_description=f"{source} lags {lag}",
                confidence=0.4,
                source_document_ids=src,
                tags=[tag],
            )
        )
    return out


def mine_to_deltas(
    text: str, *, source_id: str = "", proposed_by: str = "miner", domain: str = "commercial"
) -> list[Delta]:
    """Mine text and push each candidate into governance as a PROPOSED Delta."""
    return [
        propose_artifact(a, proposed_by=proposed_by, confidence=a.confidence)
        for a in mine_text(text, source_id=source_id, domain=domain)
    ]
