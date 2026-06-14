import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from src.knowledge.parsers.models import ParsedDocument, ParseError
from src.knowledge.parsers.pdf_parser import PDFParser
from src.knowledge.parsers.docx_parser import DocxParser
from src.knowledge.parsers.chunker import TextChunker
from src.knowledge.parsers.type_detector import DocumentTypeDetector

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    entity_type: str
    name: str
    attributes: Dict[str, Any]
    confidence: float


@dataclass
class FieldInsight:
    topic: str
    content: str
    source_file: str
    entities: List[ExtractedEntity]


# Parser dispatch by file extension
_PARSERS = {
    ".pdf": PDFParser,
    ".docx": DocxParser,
}


class DarkDataRefinery:
    """
    Refines unstructured 'Dark Data' (PDFs, DOCX, Notes) into Structured Ontology Nodes.

    Now uses real parsers from src/knowledge/parsers/ instead of stubs.
    """

    def __init__(self) -> None:
        self._chunker = TextChunker(max_tokens=1500, overlap_tokens=100)
        self._type_detector = DocumentTypeDetector()

    def ingest_document(self, file_path: str) -> List[FieldInsight]:
        """
        Main pipeline entry point.
        1. Parse document (PDF/DOCX dispatch by extension)
        2. Detect document type
        3. Chunk text
        4. Extract entities (placeholder — will be replaced by Phase 3 LLM extraction)
        """
        path = Path(file_path)
        logger.info("Ingesting: %s", path.name)

        # 1. Parse
        parsed_doc = self._parse_document(path)

        # 2. Detect type
        doc_type, confidence = self._type_detector.detect(parsed_doc)
        logger.info(
            "Detected type: %s (confidence: %.2f)", doc_type.value, confidence
        )

        # 3. Chunk
        chunks = self._chunker.chunk_document(parsed_doc)
        logger.info("Generated %d chunks from %s", len(chunks), path.name)

        # 4. Extract insights from chunks
        insights = []
        for chunk in chunks:
            insight = self._extract_semantics(chunk.text, file_path)
            if insight:
                insights.append(insight)

        return insights

    def parse_only(self, file_path: str) -> ParsedDocument:
        """Parse a document without extraction. Useful for inspection."""
        return self._parse_document(Path(file_path))

    def _parse_document(self, path: Path) -> ParsedDocument:
        """Dispatch to the appropriate parser based on file extension."""
        ext = path.suffix.lower()
        parser_cls = _PARSERS.get(ext)

        if parser_cls is None:
            # Fallback: treat as plain text
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="replace")
                from src.knowledge.parsers.models import DocumentSection

                doc = ParsedDocument(
                    source_path=str(path),
                    title=path.stem,
                    sections=[DocumentSection(content=text)],
                    metadata={"parser": "plaintext"},
                )
                doc.compute_hash()
                return doc
            raise ParseError(f"Unsupported file format: {ext}")

        parser = parser_cls()
        return parser.parse(path)

    def _extract_semantics(self, chunk_text: str, source: str) -> FieldInsight:
        """
        Extract semantic meaning from a chunk.

        Currently uses heuristic placeholder. Will be replaced by
        Phase 3 LLM-powered extraction pipeline.
        """
        if not chunk_text.strip():
            return None  # type: ignore[return-value]

        return FieldInsight(
            topic="Extracted Content",
            content=chunk_text[:500],
            source_file=source,
            entities=[],
        )


if __name__ == "__main__":
    refinery = DarkDataRefinery()
    results = refinery.ingest_document("field_notes_germany_q3.pdf")
    print("Extracted Insights:", results)
