"""
PDF parser with fallback chain.

Primary: unstructured (if available)
Fallback: pypdf (lightweight)

Ported from Transmax PDFService fallback pattern.
"""

import logging
from pathlib import Path
from typing import Optional

from .models import ParsedDocument, DocumentSection, TableData, ParseError

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 100


class PDFParser:
    """Parse PDF documents with unstructured -> pypdf fallback chain."""

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a PDF file into a ParsedDocument.

        Raises ParseError for corrupted or oversized files.
        """
        if not file_path.exists():
            raise ParseError(f"File not found: {file_path}")

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ParseError(
                f"File too large: {file_size_mb:.1f}MB exceeds {MAX_FILE_SIZE_MB}MB limit"
            )

        # Try unstructured first
        doc = self._try_unstructured(file_path)
        if doc is not None:
            return doc

        # Fallback to pypdf
        doc = self._try_pypdf(file_path)
        if doc is not None:
            return doc

        raise ParseError(f"All parsers failed for: {file_path}")

    def _try_unstructured(self, file_path: Path) -> Optional[ParsedDocument]:
        """Try parsing with unstructured library."""
        try:
            from unstructured.partition.pdf import partition_pdf

            elements = partition_pdf(str(file_path))
            if not elements:
                return None

            sections = []
            current_section = DocumentSection(heading="", level=0, content="")
            tables = []

            for element in elements:
                el_type = type(element).__name__
                text = str(element)

                if el_type == "Title":
                    if current_section.content or current_section.heading:
                        sections.append(current_section)
                    current_section = DocumentSection(heading=text, level=1, content="")
                elif el_type == "Table":
                    # Basic table extraction
                    tables.append(TableData(caption="", rows=[[text]]))
                else:
                    if current_section.content:
                        current_section.content += "\n" + text
                    else:
                        current_section.content = text

            if current_section.content or current_section.heading:
                sections.append(current_section)

            if not sections:
                return None

            doc = ParsedDocument(
                source_path=str(file_path),
                title=sections[0].heading if sections[0].heading else file_path.stem,
                sections=sections,
                tables=tables,
                metadata={"parser": "unstructured"},
            )
            doc.compute_hash()
            logger.info("Parsed %s with unstructured (%d sections)", file_path.name, len(sections))
            return doc

        except ImportError:
            logger.debug("unstructured not available, falling back")
            return None
        except Exception as exc:
            logger.warning("unstructured failed for %s: %s", file_path.name, exc)
            return None

    def _try_pypdf(self, file_path: Path) -> Optional[ParsedDocument]:
        """Fallback parsing with pypdf."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            sections = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    sections.append(
                        DocumentSection(
                            heading=f"Page {i + 1}",
                            level=1,
                            content=text.strip(),
                        )
                    )

            if not sections:
                # Scanned PDF — no extractable text
                logger.warning(
                    "No extractable text in %s (possibly scanned)", file_path.name
                )
                sections.append(
                    DocumentSection(
                        heading="[Scanned Document]",
                        level=1,
                        content="",
                    )
                )

            title = file_path.stem
            pdf_meta = reader.metadata
            if pdf_meta and pdf_meta.title:
                title = pdf_meta.title

            doc = ParsedDocument(
                source_path=str(file_path),
                title=title,
                sections=sections,
                metadata={
                    "parser": "pypdf",
                    "page_count": len(reader.pages),
                },
            )
            doc.compute_hash()
            logger.info("Parsed %s with pypdf (%d pages)", file_path.name, len(reader.pages))
            return doc

        except ImportError:
            logger.warning("pypdf not available")
            return None
        except Exception as exc:
            logger.warning("pypdf failed for %s: %s", file_path.name, exc)
            return None
