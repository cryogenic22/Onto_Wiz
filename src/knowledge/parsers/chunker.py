"""
Token-aware text chunker.

Splits ParsedDocument sections into token-bounded chunks for LLM extraction.
Preserves heading context in each chunk.

Adapted from AgentFuel's MarkdownChunker heading-context-preservation approach.
"""

import logging
import re
from typing import List

from .models import ParsedDocument, DocumentSection, Chunk

logger = logging.getLogger(__name__)


class TextChunker:
    """Split documents into token-bounded chunks preserving heading context."""

    def __init__(self, max_tokens: int = 1500, overlap_tokens: int = 100) -> None:
        if max_tokens < 100:
            raise ValueError("max_tokens must be >= 100")
        self._max_tokens = max_tokens
        self._overlap_tokens = min(overlap_tokens, max_tokens // 4)

    def chunk_document(self, doc: ParsedDocument) -> List[Chunk]:
        """Split a parsed document into chunks."""
        chunks: List[Chunk] = []

        for section in doc.sections:
            heading_ctx = section.heading or ""
            section_chunks = self._chunk_section(section, heading_ctx)
            chunks.extend(section_chunks)

        # Also chunk tables as text
        for table in doc.tables:
            table_text = table.to_text()
            if table_text.strip():
                table_chunks = self._split_text(
                    table_text,
                    heading_context=f"Table: {table.caption}" if table.caption else "Table",
                    source_section="table",
                )
                chunks.extend(table_chunks)

        # Number the chunks
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.total_chunks = total

        return chunks

    def _chunk_section(
        self, section: DocumentSection, heading_context: str
    ) -> List[Chunk]:
        """Recursively chunk a section and its subsections."""
        chunks: List[Chunk] = []

        if section.content.strip():
            section_chunks = self._split_text(
                section.content,
                heading_context=heading_context,
                source_section=section.heading or "untitled",
            )
            chunks.extend(section_chunks)

        # Recurse into subsections
        for sub in section.subsections:
            sub_ctx = f"{heading_context} > {sub.heading}" if heading_context else sub.heading
            chunks.extend(self._chunk_section(sub, sub_ctx))

        return chunks

    def _split_text(
        self, text: str, heading_context: str, source_section: str
    ) -> List[Chunk]:
        """Split text into token-bounded chunks."""
        text = text.strip()
        if not text:
            return []

        # Reserve tokens for heading context
        context_tokens = self._estimate_tokens(heading_context) + 10
        available_tokens = self._max_tokens - context_tokens

        if available_tokens <= 50:
            available_tokens = self._max_tokens

        text_tokens = self._estimate_tokens(text)
        if text_tokens <= available_tokens:
            return [
                Chunk(
                    text=text,
                    heading_context=heading_context,
                    source_section=source_section,
                    estimated_tokens=text_tokens + context_tokens,
                )
            ]

        # Split on paragraph boundaries first
        paragraphs = re.split(r"\n\s*\n", text)
        if len(paragraphs) <= 1:
            # Fall back to sentence splitting
            paragraphs = self._split_sentences(text)

        chunks: List[Chunk] = []
        current_parts: List[str] = []
        current_tokens = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_tokens = self._estimate_tokens(para)

            if para_tokens > available_tokens:
                # Paragraph itself is too large — split by sentences
                if current_parts:
                    chunks.append(self._make_chunk(
                        current_parts, heading_context, source_section, current_tokens + context_tokens
                    ))
                    current_parts = []
                    current_tokens = 0

                sentences = self._split_sentences(para)
                for sent in sentences:
                    sent_tokens = self._estimate_tokens(sent)
                    if current_tokens + sent_tokens > available_tokens and current_parts:
                        chunks.append(self._make_chunk(
                            current_parts, heading_context, source_section, current_tokens + context_tokens
                        ))
                        # Overlap: keep last part
                        overlap_parts = self._get_overlap(current_parts)
                        current_parts = overlap_parts
                        current_tokens = sum(self._estimate_tokens(p) for p in current_parts)
                    current_parts.append(sent)
                    current_tokens += sent_tokens
            elif current_tokens + para_tokens > available_tokens:
                # Flush current chunk
                chunks.append(self._make_chunk(
                    current_parts, heading_context, source_section, current_tokens + context_tokens
                ))
                # Overlap
                overlap_parts = self._get_overlap(current_parts)
                current_parts = overlap_parts + [para]
                current_tokens = sum(self._estimate_tokens(p) for p in current_parts)
            else:
                current_parts.append(para)
                current_tokens += para_tokens

        if current_parts:
            chunks.append(self._make_chunk(
                current_parts, heading_context, source_section, current_tokens + context_tokens
            ))

        return chunks

    def _make_chunk(
        self,
        parts: List[str],
        heading_context: str,
        source_section: str,
        estimated_tokens: int,
    ) -> Chunk:
        return Chunk(
            text="\n\n".join(parts),
            heading_context=heading_context,
            source_section=source_section,
            estimated_tokens=estimated_tokens,
        )

    def _get_overlap(self, parts: List[str]) -> List[str]:
        """Get trailing parts for overlap."""
        if not parts or self._overlap_tokens <= 0:
            return []
        overlap: List[str] = []
        tokens = 0
        for part in reversed(parts):
            t = self._estimate_tokens(part)
            if tokens + t > self._overlap_tokens:
                break
            overlap.insert(0, part)
            tokens += t
        return overlap

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on period/question/exclamation followed by space
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count: ~4 chars per token."""
        return len(text) // 4
