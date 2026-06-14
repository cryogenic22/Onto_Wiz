"""
Knowledge API endpoints.

POST /knowledge/context    -> ContextResponse
GET  /knowledge/artifacts  -> ArtifactListResponse
GET  /knowledge/artifacts/{id} -> ArtifactDetailResponse
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from .api_schemas import (
    ContextRequest,
    ContextResponse,
    ArtifactListResponse,
    ArtifactDetailResponse,
)
from .assembler import ContextAssembler
from .few_shot_store import FewShotStore

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

# These will be set during server startup via init_knowledge_routes()
_assembler: Optional[ContextAssembler] = None
_few_shot_store: Optional[FewShotStore] = None
_judgment_store = None


def init_knowledge_routes(
    assembler: ContextAssembler,
    few_shot_store: FewShotStore,
    judgment_store: object,
) -> None:
    """Wire dependencies into routes. Called during server startup."""
    global _assembler, _few_shot_store, _judgment_store
    _assembler = assembler
    _few_shot_store = few_shot_store
    _judgment_store = judgment_store


@router.post("/context", response_model=ContextResponse)
def assemble_context(request: ContextRequest) -> ContextResponse:
    """Assemble a context package for an agent query."""
    if _assembler is None:
        raise HTTPException(status_code=503, detail="Knowledge module not initialized")

    package = _assembler.assemble(
        query=request.query,
        agent_type=request.agent_type,
        max_tokens=request.max_tokens,
    )
    return ContextResponse(**package.to_dict())


@router.get("/artifacts", response_model=ArtifactListResponse)
def list_artifacts(
    type: Optional[str] = Query(
        default=None, description="Filter: pattern, guardrail, few_shot"
    ),
    tag: Optional[str] = Query(default=None, description="Filter by tag value"),
) -> ArtifactListResponse:
    """List knowledge artifacts with optional type/tag filtering."""
    if _judgment_store is None or _few_shot_store is None:
        raise HTTPException(status_code=503, detail="Knowledge module not initialized")

    artifacts = []

    if type is None or type == "pattern":
        for p in _judgment_store._patterns.values():
            item = {
                "id": p.id,
                "artifact_type": "pattern",
                "signals": p.applies_when_signals,
                "context": p.applies_when_context,
                "status": p.status.value,
            }
            if tag is None or _tag_in(tag, p.applies_when_signals + p.applies_when_context):
                artifacts.append(item)

    if type is None or type == "guardrail":
        for g in _judgment_store._guardrails.values():
            item = {
                "id": g.id,
                "artifact_type": "guardrail",
                "blocks_drivers": g.blocks_drivers,
                "blocks_action_types": g.blocks_action_types,
                "status": g.status.value,
            }
            if tag is None or _tag_in(tag, g.blocks_drivers + g.blocks_action_types):
                artifacts.append(item)

    if type is None or type == "few_shot":
        for ex in _few_shot_store.get_all():
            all_tag_values = []
            for vals in ex.tags.values():
                all_tag_values.extend(vals)
            item = {
                "id": ex.id,
                "artifact_type": "few_shot",
                "task_type": ex.task_type,
                "tags": ex.tags,
                "quality_score": ex.quality_score,
                "status": ex.status.value,
            }
            if tag is None or _tag_in(tag, all_tag_values + [ex.task_type]):
                artifacts.append(item)

    return ArtifactListResponse(
        artifacts=artifacts,
        total=len(artifacts),
        artifact_type=type,
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetailResponse)
def get_artifact(artifact_id: str) -> ArtifactDetailResponse:
    """Get a single artifact by ID."""
    if _judgment_store is None or _few_shot_store is None:
        raise HTTPException(status_code=503, detail="Knowledge module not initialized")

    # Check patterns
    pattern = _judgment_store._patterns.get(artifact_id)
    if pattern:
        return ArtifactDetailResponse(
            id=pattern.id,
            artifact_type="pattern",
            data={
                "signals": pattern.applies_when_signals,
                "context": pattern.applies_when_context,
                "drivers": [
                    {"driver": d.driver, "confidence": d.prior_confidence}
                    for d in pattern.typical_drivers
                ],
                "disallowed_drivers": pattern.disallowed_drivers,
                "status": pattern.status.value,
                "is_active": pattern.is_active(),
            },
        )

    # Check guardrails
    guardrail = _judgment_store._guardrails.get(artifact_id)
    if guardrail:
        return ArtifactDetailResponse(
            id=guardrail.id,
            artifact_type="guardrail",
            data={
                "blocks_action_types": guardrail.blocks_action_types,
                "blocks_drivers": guardrail.blocks_drivers,
                "unless_evidence": guardrail.unless_evidence,
                "applies_to_personas": guardrail.applies_to_personas,
                "status": guardrail.status.value,
            },
        )

    # Check few-shots
    example = _few_shot_store.get(artifact_id)
    if example:
        return ArtifactDetailResponse(
            id=example.id,
            artifact_type="few_shot",
            data=example.to_dict(),
        )

    raise HTTPException(status_code=404, detail="Artifact not found")


def _tag_in(tag: str, values: list) -> bool:
    """Case-insensitive check if tag appears in any value."""
    tag_lower = tag.lower()
    return any(tag_lower in v.lower() for v in values if isinstance(v, str))
