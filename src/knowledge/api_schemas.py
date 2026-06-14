"""
Pydantic request/response models for knowledge API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class ContextRequest(BaseModel):
    """Request to assemble a context package."""

    query: str = Field(..., min_length=1)
    agent_type: str = "general"
    max_tokens: int = Field(default=4000, ge=100, le=128000)


class ContextResponse(BaseModel):
    """Response containing assembled context package."""

    query: str
    patterns: List[Dict[str, Any]]
    guardrails: List[Dict[str, Any]]
    few_shots: List[Dict[str, Any]]
    jargon_context: Dict[str, str]
    entity_context: Dict[str, Any]
    tags_matched: Dict[str, List[str]]
    token_estimate: int
    max_tokens: int
    metadata: Dict[str, Any]


class ArtifactListResponse(BaseModel):
    """Response listing knowledge artifacts."""

    artifacts: List[Dict[str, Any]]
    total: int
    artifact_type: Optional[str] = None


class ArtifactDetailResponse(BaseModel):
    """Response containing a single artifact's details."""

    id: str
    artifact_type: str
    data: Dict[str, Any]
