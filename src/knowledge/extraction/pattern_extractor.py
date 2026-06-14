"""
Pattern extractor — extracts "if signal X then driver Y" rules from chunks.

Creates Delta(PROPOSED_PATTERN) proposals that flow through existing governance.
"""

import logging
from typing import Dict, List, Optional, Any

from src.core.models import Delta, DeltaType, BlastRadius
from src.core.stores import JudgmentStore
from src.core.semantic_store import SemanticStore
from src.knowledge.parsers.models import Chunk

logger = logging.getLogger(__name__)

PATTERN_EXTRACTION_PROMPT = """Analyze the following text and extract any signal-to-driver patterns.

A pattern describes: "When signal X is observed, driver Y is likely the cause."

Text:
{text}

Context: {heading_context}
Document type: {doc_type}

Return a JSON object with this structure:
{{
  "patterns": [
    {{
      "signals": ["signal_name_1", "signal_name_2"],
      "context": ["context_keyword_1"],
      "drivers": [
        {{"driver": "driver_name", "confidence": 0.7}}
      ],
      "disallowed_drivers": [],
      "reasoning": "why this pattern holds"
    }}
  ]
}}

Only extract patterns that are clearly stated or strongly implied.
Use standard signal names: TRx_Drop, NBRx_Drop, PA_Edit_Increase, Market_Share_Loss, etc.
Use standard driver names: Access_Friction, Field_Execution_Gap, Competitor_Displacement, etc.
If no patterns found, return {{"patterns": []}}.
"""


class PatternExtractor:
    """Extract judgment patterns from document chunks via LLM."""

    def __init__(
        self,
        llm_service: Any,
        judgment_store: Optional[JudgmentStore] = None,
        semantic_store: Optional[SemanticStore] = None,
    ) -> None:
        self._llm = llm_service
        self._judgment_store = judgment_store
        self._semantic_store = semantic_store

    def extract_patterns(
        self,
        chunks: List[Chunk],
        doc_metadata: Dict[str, Any],
    ) -> List[Delta]:
        """Extract patterns from chunks and return as Delta proposals."""
        all_deltas: List[Delta] = []
        doc_type = doc_metadata.get("doc_type", "general")

        for chunk in chunks:
            try:
                deltas = self._extract_from_chunk(chunk, doc_type, doc_metadata)
                all_deltas.extend(deltas)
            except Exception as exc:
                logger.warning(
                    "Pattern extraction failed for chunk %d: %s",
                    chunk.chunk_index,
                    exc,
                )

        # Dedup against existing patterns
        if self._judgment_store:
            all_deltas = self._dedup_against_existing(all_deltas)

        return all_deltas

    def _extract_from_chunk(
        self,
        chunk: Chunk,
        doc_type: str,
        doc_metadata: Dict[str, Any],
    ) -> List[Delta]:
        """Extract patterns from a single chunk."""
        prompt = PATTERN_EXTRACTION_PROMPT.format(
            text=chunk.text,
            heading_context=chunk.heading_context,
            doc_type=doc_type,
        )

        result = self._llm.complete_json(
            prompt=prompt,
            system="You are a pharma commercial intelligence analyst. Extract signal-to-driver patterns.",
        )

        patterns = result.get("patterns", [])
        deltas = []

        for pat_data in patterns:
            if not isinstance(pat_data, dict):
                continue

            drivers = pat_data.get("drivers", [])
            if not drivers:
                continue

            # Filter low-confidence patterns
            max_conf = max(d.get("confidence", 0) for d in drivers)
            if max_conf < 0.3:
                continue

            # Resolve terms via SemanticStore
            signals = self._resolve_terms(pat_data.get("signals", []))
            context = pat_data.get("context", [])

            delta = Delta(
                type=DeltaType.PROPOSED_PATTERN,
                content={
                    "applies_when_signals": signals,
                    "applies_when_context": context,
                    "typical_drivers": drivers,
                    "disallowed_drivers": pat_data.get("disallowed_drivers", []),
                    "reasoning": pat_data.get("reasoning", ""),
                    "source_chunk": chunk.chunk_index,
                    "source_heading": chunk.heading_context,
                },
                confidence=max_conf,
                blast_radius=BlastRadius.MEDIUM,
                source_type="document_extraction",
                source_id=doc_metadata.get("source_path", ""),
            )
            deltas.append(delta)

        return deltas

    def _resolve_terms(self, terms: List[str]) -> List[str]:
        """Resolve terms to canonical form via SemanticStore."""
        if not self._semantic_store:
            return terms

        resolved = []
        for term in terms:
            canonical = self._semantic_store.resolve_to_canonical(term)
            if canonical:
                resolved.append(canonical.term)
            else:
                resolved.append(term)
        return resolved

    def _dedup_against_existing(self, deltas: List[Delta]) -> List[Delta]:
        """Remove deltas that duplicate existing patterns."""
        if not self._judgment_store:
            return deltas

        unique = []
        existing_patterns = list(self._judgment_store._patterns.values())

        for delta in deltas:
            signals = set(delta.content.get("applies_when_signals", []))
            is_dup = False
            for existing in existing_patterns:
                existing_signals = set(existing.applies_when_signals)
                overlap = len(signals & existing_signals)
                union = len(signals | existing_signals)
                if union > 0 and overlap / union > 0.8:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(delta)

        if len(deltas) != len(unique):
            logger.info(
                "Deduped %d patterns (kept %d)",
                len(deltas) - len(unique),
                len(unique),
            )

        return unique
