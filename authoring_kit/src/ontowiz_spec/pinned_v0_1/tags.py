"""Tag dimensions and tag queries — the relevance vocabulary.

Tags are how the runtime decides *which* artifacts are eligible for a query
before CTX hydration ever happens. Nine dimensions, ported from SpecOmagic.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TagDimension(str, Enum):
    THERAPY_AREA = "therapy_area"
    DRUG = "drug"
    INDICATION = "indication"
    DATA_SOURCE = "data_source"
    ANALYTICS_DOMAIN = "analytics_domain"
    TASK_TYPE = "task_type"
    GEOGRAPHY = "geography"
    FUNCTION = "function"
    CLIENT = "client"


class Tag(BaseModel):
    """A single (dimension, value) label. Hierarchical via ``parent``."""

    dimension: TagDimension
    value: str
    parent: str | None = None  # value of the parent tag in the same dimension

    def key(self) -> str:
        return f"{self.dimension.value}:{self.value}"


class TagQuery(BaseModel):
    """A request for artifacts matching some tags, with a match threshold."""

    tags: list[Tag] = Field(default_factory=list)
    # Fraction of query tags an artifact must carry to be considered a match.
    min_match_ratio: float = 0.3
    # Restrict to these pack layers (e.g. only client overlay). Empty = all.
    layers: list[str] = Field(default_factory=list)
