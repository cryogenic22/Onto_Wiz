"""
Document type classification via keyword heuristics.

Classifies documents as: clinical_study, label, field_note, formulary,
competitive_intel, guideline, or general.

Adapted from Content Medical Hub's DocumentTypeRegistry patterns.
"""

import re
from typing import Dict, List, Tuple

from .models import DocumentType, ParsedDocument

# Keyword patterns for each document type (case-insensitive)
_TYPE_KEYWORDS: Dict[DocumentType, List[str]] = {
    DocumentType.CLINICAL_STUDY: [
        "clinical trial",
        "phase [123i]+",
        "randomized",
        "double-blind",
        "placebo-controlled",
        "primary endpoint",
        "secondary endpoint",
        "overall survival",
        "progression-free survival",
        "hazard ratio",
        "p-value",
        "intention-to-treat",
        "per-protocol",
        "inclusion criteria",
        "exclusion criteria",
        "informed consent",
        "IRB",
        "DSMB",
        "ClinicalTrials.gov",
        "NCT\\d+",
    ],
    DocumentType.LABEL: [
        "prescribing information",
        "indications and usage",
        "dosage and administration",
        "contraindications",
        "warnings and precautions",
        "adverse reactions",
        "drug interactions",
        "boxed warning",
        "black box warning",
        "medication guide",
        "FDA-approved",
        "package insert",
    ],
    DocumentType.FIELD_NOTE: [
        "field report",
        "call note",
        "account visit",
        "territory review",
        "rep feedback",
        "MSL report",
        "KOL meeting",
        "medical education",
        "speaker program",
        "lunch and learn",
        "in-service",
        "advisory board",
    ],
    DocumentType.FORMULARY: [
        "formulary",
        "prior authorization",
        "step therapy",
        "step edit",
        "tier [1-4]",
        "preferred status",
        "non-preferred",
        "pharmacy benefit",
        "medical benefit",
        "copay",
        "coinsurance",
        "payer",
        "coverage determination",
        "utilization management",
    ],
    DocumentType.COMPETITIVE_INTEL: [
        "competitive landscape",
        "market share",
        "competitor",
        "market analysis",
        "SWOT",
        "biosimilar",
        "patent expiry",
        "pipeline",
        "launch readiness",
        "competitive threat",
        "win rate",
        "share of voice",
    ],
    DocumentType.GUIDELINE: [
        "clinical guideline",
        "treatment guideline",
        "NCCN",
        "ASCO",
        "practice guideline",
        "standard of care",
        "evidence-based",
        "recommendation grade",
        "level of evidence",
        "consensus statement",
        "expert panel",
        "treatment algorithm",
    ],
}


class DocumentTypeDetector:
    """Classify document type using keyword heuristics."""

    def detect(self, doc: ParsedDocument) -> Tuple[DocumentType, float]:
        """
        Detect document type from content.

        Returns (DocumentType, confidence) where confidence is 0.0-1.0.
        """
        text = doc.full_text.lower()
        title = doc.title.lower()

        scores: Dict[DocumentType, float] = {}

        for doc_type, keywords in _TYPE_KEYWORDS.items():
            match_count = 0
            for kw in keywords:
                pattern = re.compile(kw, re.IGNORECASE)
                matches = pattern.findall(text)
                match_count += len(matches)
                # Title matches count double
                title_matches = pattern.findall(title)
                match_count += len(title_matches) * 2

            if match_count > 0:
                # Normalize: more matches = higher confidence, saturating at 1.0
                keyword_count = len(keywords)
                scores[doc_type] = min(1.0, match_count / (keyword_count * 0.5))

        if not scores:
            return DocumentType.GENERAL, 0.5

        # Return highest scoring type
        best_type = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best_type]

        # Scale confidence: raw score * 0.9 (never fully certain from heuristics)
        confidence = min(0.95, best_score * 0.9)

        return best_type, round(confidence, 2)
