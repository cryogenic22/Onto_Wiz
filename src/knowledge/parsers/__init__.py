"""Knowledge module — document parsers."""

from .models import ParsedDocument, DocumentSection, TableData, Chunk, DocumentType, ParseError
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .chunker import TextChunker
from .type_detector import DocumentTypeDetector

__all__ = [
    "ParsedDocument",
    "DocumentSection",
    "TableData",
    "Chunk",
    "DocumentType",
    "ParseError",
    "PDFParser",
    "DocxParser",
    "TextChunker",
    "DocumentTypeDetector",
]
