"""
Document parsing models.

ParsedDocument, DocumentSection, TableData, Chunk — output types for all parsers.
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


class DocumentType(str, Enum):
    """Classification of document type for extraction routing."""

    CLINICAL_STUDY = "clinical_study"
    LABEL = "label"
    FIELD_NOTE = "field_note"
    FORMULARY = "formulary"
    COMPETITIVE_INTEL = "competitive_intel"
    GUIDELINE = "guideline"
    GENERAL = "general"


@dataclass
class DocumentSection:
    """A section within a parsed document, preserving heading hierarchy."""

    heading: str = ""
    level: int = 0  # 0 = no heading, 1-6 = heading level
    content: str = ""
    subsections: List["DocumentSection"] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Return all text including subsections."""
        parts = []
        if self.heading:
            parts.append(self.heading)
        if self.content:
            parts.append(self.content)
        for sub in self.subsections:
            parts.append(sub.full_text)
        return "\n".join(parts)


@dataclass
class TableData:
    """A table extracted from a document."""

    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    caption: str = ""

    def to_text(self) -> str:
        """Render table as pipe-delimited text."""
        lines = []
        if self.caption:
            lines.append(f"Table: {self.caption}")
        if self.headers:
            lines.append(" | ".join(self.headers))
            lines.append(" | ".join("---" for _ in self.headers))
        for row in self.rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)


@dataclass
class ParsedDocument:
    """Output of any document parser — normalized representation."""

    source_path: str = ""
    title: str = ""
    sections: List[DocumentSection] = field(default_factory=list)
    tables: List[TableData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""  # SHA256 for dedup

    def compute_hash(self) -> str:
        """Compute SHA256 hash of all text content for deduplication."""
        full_text = "\n".join(s.full_text for s in self.sections)
        full_text += "\n".join(t.to_text() for t in self.tables)
        self.content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]
        return self.content_hash

    @property
    def full_text(self) -> str:
        """Return concatenated text from all sections."""
        return "\n\n".join(s.full_text for s in self.sections)

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())


@dataclass
class Chunk:
    """A token-bounded chunk of text for LLM extraction."""

    text: str = ""
    heading_context: str = ""  # Ancestor headings for context
    chunk_index: int = 0
    total_chunks: int = 0
    source_section: str = ""  # Which section this came from
    estimated_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ParseError(Exception):
    """Raised when document parsing fails."""

    pass
