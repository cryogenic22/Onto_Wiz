"""
Knowledge module domain models.

FewShotExample: Curated input/output examples for agent prompts.
ContextPackage: Wire format returned to agents with assembled context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4
import json

from src.core.models import ArtifactStatus


@dataclass
class FewShotExample:
    """A curated input/output example for agent prompts."""

    id: str = field(default_factory=lambda: str(uuid4()))
    task_type: str = ""  # "driver_attribution", "signal_interpretation", etc.
    input_text: str = ""
    output_text: str = ""
    tags: Dict[str, List[str]] = field(default_factory=dict)
    quality_score: float = 0.8
    status: ArtifactStatus = ArtifactStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for YAML storage."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FewShotExample":
        """Deserialize from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        status_val = data.get("status", "draft")
        if isinstance(status_val, str):
            status_val = ArtifactStatus(status_val)

        return cls(
            id=data.get("id", str(uuid4())),
            task_type=data.get("task_type", ""),
            input_text=data.get("input_text", ""),
            output_text=data.get("output_text", ""),
            tags=data.get("tags", {}),
            quality_score=float(data.get("quality_score", 0.8)),
            status=status_val,
            created_at=created_at,
            version=data.get("version", "1.0.0"),
        )


@dataclass
class ContextPackage:
    """
    Wire format returned to agents containing assembled context.

    Bundles patterns, guardrails, few-shots, jargon, and entity context
    within a token budget.
    """

    query: str = ""
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    guardrails: List[Dict[str, Any]] = field(default_factory=list)
    few_shots: List[Dict[str, Any]] = field(default_factory=list)
    jargon_context: Dict[str, str] = field(default_factory=dict)
    entity_context: Dict[str, Any] = field(default_factory=dict)
    tags_matched: Dict[str, List[str]] = field(default_factory=dict)
    token_estimate: int = 0
    max_tokens: int = 4000
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "query": self.query,
            "patterns": self.patterns,
            "guardrails": self.guardrails,
            "few_shots": self.few_shots,
            "jargon_context": self.jargon_context,
            "entity_context": self.entity_context,
            "tags_matched": self.tags_matched,
            "token_estimate": self.token_estimate,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
        }

    def estimate_tokens(self) -> int:
        """Estimate token count via len(json.dumps(self)) // 4."""
        return len(json.dumps(self.to_dict())) // 4
