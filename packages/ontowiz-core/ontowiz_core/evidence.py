"""
Onto_Wiz Evidence Model

First-class evidence with reliability classification, provenance, and permissions.
This is the foundation of credible reasoning - without structured evidence,
approvals and confidence are arbitrary.

Evidence Types:
- METRIC: Quantitative data from systems (TRx, NBRx, etc.)
- DOCUMENT: Unstructured text (field notes, MSL reports)
- FEEDBACK: HCP/account feedback from CRM
- EXTERNAL: Third-party data (IQVIA, Symphony, etc.)
- DERIVED: Computed/aggregated from other evidence

Reliability Classes:
- HARD: System-verified, auditable (e.g., claims data)
- SOFT: Human-reported, plausible (e.g., field notes)
- RUMOR: Unverified, requires validation (e.g., competitive intel)
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# =============================================================================
# EVIDENCE ENUMS
# =============================================================================

class EvidenceType(str, Enum):
    """Types of evidence that can be collected."""
    METRIC = "metric"           # Quantitative data (TRx, NBRx, share)
    DOCUMENT = "document"       # Unstructured text
    FEEDBACK = "feedback"       # HCP/account feedback
    EXTERNAL = "external"       # Third-party data
    DERIVED = "derived"         # Computed from other evidence
    OBSERVATION = "observation" # Direct observation (field visit)
    CLAIM = "claim"             # Extracted claim from documents


class ReliabilityClass(str, Enum):
    """
    Reliability of evidence - determines weight in confidence calculation.

    HARD: System-verified, auditable, high trust
    SOFT: Human-reported, plausible but not verified
    RUMOR: Unverified hearsay, requires validation
    """
    HARD = "hard"   # Weight: 1.0
    SOFT = "soft"   # Weight: 0.6
    RUMOR = "rumor" # Weight: 0.2


class SourceSystem(str, Enum):
    """Source systems for evidence."""
    CRM = "crm"                   # Salesforce, Veeva
    CLAIMS = "claims"             # Claims/Rx data
    FIELD_NOTES = "field_notes"   # Rep notes
    MSL_REPORT = "msl_report"     # MSL interactions
    MARKET_RESEARCH = "market_research"
    COMPETITOR_INTEL = "competitor_intel"
    SOCIAL_LISTENING = "social_listening"
    INTERNAL_ANALYTICS = "internal_analytics"
    EXTERNAL_VENDOR = "external_vendor"
    SME_GAME = "sme_game"         # Captured from Semantic Harvester
    MANUAL_ENTRY = "manual"


# =============================================================================
# EVIDENCE POINTER (Structured, not string)
# =============================================================================

@dataclass
class EvidencePointer:
    """
    Structured reference to a specific piece of evidence.

    NOT a free string - includes evidence ID, optional span, and claim ID.
    This enables proper citation and audit trails.
    """
    evidence_id: str
    claim_id: str | None = None  # Specific claim within evidence
    span: str | None = None       # Text span or range
    confidence: float = 1.0          # Confidence in this citation

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim_id": self.claim_id,
            "span": self.span,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidencePointer":
        return cls(
            evidence_id=data["evidence_id"],
            claim_id=data.get("claim_id"),
            span=data.get("span"),
            confidence=data.get("confidence", 1.0),
        )


@dataclass
class ExtractedClaim:
    """A claim extracted from evidence."""
    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    claim_type: str = "assertion"  # assertion, observation, inference
    confidence: float = 0.8
    extracted_by: str = "manual"   # manual, nlp, llm
    span_start: int | None = None
    span_end: int | None = None


# =============================================================================
# EVIDENCE ITEM
# =============================================================================

@dataclass
class EvidenceItem:
    """
    A first-class piece of evidence.

    This is NOT a free string - it has:
    - Type and reliability classification
    - Source system and provenance
    - Entity and metric references
    - Permission tags for access control
    - Extracted claims for citation
    - Content hash for deduplication
    """
    id: str = field(default_factory=lambda: str(uuid4()))

    # Classification
    type: EvidenceType = EvidenceType.DOCUMENT
    reliability: ReliabilityClass = ReliabilityClass.SOFT

    # Source and provenance
    source_system: SourceSystem = SourceSystem.MANUAL_ENTRY
    source_uri: str = ""           # Original location/URL
    source_id: str | None = None  # ID in source system
    collected_at: datetime = field(default_factory=datetime.utcnow)
    collected_by: str = ""         # Who/what collected it

    # Content
    title: str = ""
    content: str = ""              # Raw content/text
    content_hash: str = ""         # SHA256 for deduplication

    # References
    entity_refs: list[str] = field(default_factory=list)  # Entities mentioned
    metric_refs: list[str] = field(default_factory=list)  # Metrics referenced

    # Extracted claims
    claims: list[ExtractedClaim] = field(default_factory=list)

    # Access control
    permission_tags: list[str] = field(default_factory=list)
    client_id: str | None = None  # For multi-tenancy

    # Scope
    geography: str | None = None
    brand: str | None = None
    time_period: str | None = None  # e.g., "2026-Q1"

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Compute content hash if not provided."""
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]

    def reliability_weight(self) -> float:
        """Get numeric weight for reliability class."""
        weights = {
            ReliabilityClass.HARD: 1.0,
            ReliabilityClass.SOFT: 0.6,
            ReliabilityClass.RUMOR: 0.2,
        }
        return weights.get(self.reliability, 0.5)

    def add_claim(
        self,
        text: str,
        claim_type: str = "assertion",
        confidence: float = 0.8,
        span_start: int | None = None,
        span_end: int | None = None
    ) -> ExtractedClaim:
        """Add an extracted claim to this evidence."""
        claim = ExtractedClaim(
            text=text,
            claim_type=claim_type,
            confidence=confidence,
            span_start=span_start,
            span_end=span_end,
        )
        self.claims.append(claim)
        return claim

    def get_pointer(self, claim_id: str | None = None, span: str | None = None) -> EvidencePointer:
        """Create a pointer to this evidence."""
        return EvidencePointer(
            evidence_id=self.id,
            claim_id=claim_id,
            span=span,
            confidence=self.reliability_weight(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "reliability": self.reliability.value,
            "source_system": self.source_system.value,
            "source_uri": self.source_uri,
            "source_id": self.source_id,
            "collected_at": self.collected_at.isoformat(),
            "collected_by": self.collected_by,
            "title": self.title,
            "content": self.content,
            "content_hash": self.content_hash,
            "entity_refs": self.entity_refs,
            "metric_refs": self.metric_refs,
            "claims": [{"id": c.id, "text": c.text, "type": c.claim_type, "confidence": c.confidence} for c in self.claims],
            "permission_tags": self.permission_tags,
            "client_id": self.client_id,
            "geography": self.geography,
            "brand": self.brand,
            "time_period": self.time_period,
        }


# =============================================================================
# EVIDENCE STORE
# =============================================================================

class EvidenceStore:
    """
    Store for all evidence items.

    Features:
    - CRUD operations
    - Reliability classification
    - Deduplication via content hash
    - Permission-aware retrieval
    - Scope-based filtering
    """

    def __init__(self):
        self._evidence: dict[str, EvidenceItem] = {}
        self._by_type: dict[EvidenceType, set[str]] = {t: set() for t in EvidenceType}
        self._by_reliability: dict[ReliabilityClass, set[str]] = {r: set() for r in ReliabilityClass}
        self._by_hash: dict[str, str] = {}  # content_hash -> id (for dedup)
        self._by_entity: dict[str, set[str]] = {}  # entity_ref -> evidence_ids
        self._by_source: dict[SourceSystem, set[str]] = {s: set() for s in SourceSystem}

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def add(self, evidence: EvidenceItem) -> EvidenceItem:
        """
        Add evidence to the store.

        Returns existing evidence if content hash matches (deduplication).
        """
        # Check for duplicate
        if evidence.content_hash and evidence.content_hash in self._by_hash:
            existing_id = self._by_hash[evidence.content_hash]
            return self._evidence[existing_id]

        # Store evidence
        self._evidence[evidence.id] = evidence
        self._by_type[evidence.type].add(evidence.id)
        self._by_reliability[evidence.reliability].add(evidence.id)
        self._by_source[evidence.source_system].add(evidence.id)

        if evidence.content_hash:
            self._by_hash[evidence.content_hash] = evidence.id

        # Index by entity refs
        for entity in evidence.entity_refs:
            if entity not in self._by_entity:
                self._by_entity[entity] = set()
            self._by_entity[entity].add(evidence.id)

        return evidence

    def get(self, evidence_id: str) -> EvidenceItem | None:
        """Get evidence by ID."""
        return self._evidence.get(evidence_id)

    def get_by_pointer(self, pointer: EvidencePointer) -> EvidenceItem | None:
        """Get evidence by pointer."""
        return self._evidence.get(pointer.evidence_id)

    def update(self, evidence_id: str, **kwargs) -> EvidenceItem | None:
        """Update evidence properties."""
        evidence = self._evidence.get(evidence_id)
        if not evidence:
            return None

        for key, value in kwargs.items():
            if hasattr(evidence, key):
                setattr(evidence, key, value)

        evidence.updated_at = datetime.utcnow()
        return evidence

    def remove(self, evidence_id: str) -> bool:
        """Remove evidence from store."""
        evidence = self._evidence.get(evidence_id)
        if not evidence:
            return False

        # Remove from indexes
        self._by_type[evidence.type].discard(evidence_id)
        self._by_reliability[evidence.reliability].discard(evidence_id)
        self._by_source[evidence.source_system].discard(evidence_id)

        if evidence.content_hash in self._by_hash:
            del self._by_hash[evidence.content_hash]

        for entity in evidence.entity_refs:
            if entity in self._by_entity:
                self._by_entity[entity].discard(evidence_id)

        del self._evidence[evidence_id]
        return True

    # -------------------------------------------------------------------------
    # Query Operations
    # -------------------------------------------------------------------------

    def find_by_type(self, evidence_type: EvidenceType) -> list[EvidenceItem]:
        """Get all evidence of a specific type."""
        return [self._evidence[eid] for eid in self._by_type.get(evidence_type, set())]

    def find_by_reliability(self, reliability: ReliabilityClass) -> list[EvidenceItem]:
        """Get all evidence of a specific reliability class."""
        return [self._evidence[eid] for eid in self._by_reliability.get(reliability, set())]

    def find_by_entity(self, entity_ref: str) -> list[EvidenceItem]:
        """Get all evidence mentioning an entity."""
        return [self._evidence[eid] for eid in self._by_entity.get(entity_ref, set())]

    def find_by_source(self, source: SourceSystem) -> list[EvidenceItem]:
        """Get all evidence from a source system."""
        return [self._evidence[eid] for eid in self._by_source.get(source, set())]

    def find_hard_evidence(self) -> list[EvidenceItem]:
        """Get all HARD (system-verified) evidence."""
        return self.find_by_reliability(ReliabilityClass.HARD)

    def find_for_hypothesis(
        self,
        hypothesis_label: str,
        min_reliability: ReliabilityClass = ReliabilityClass.RUMOR
    ) -> list[EvidenceItem]:
        """
        Find evidence relevant to a hypothesis.

        Currently uses entity/metric refs. Will be enhanced with
        semantic search when vector store is added.
        """
        results = []
        reliability_order = [ReliabilityClass.HARD, ReliabilityClass.SOFT, ReliabilityClass.RUMOR]
        min_index = reliability_order.index(min_reliability)

        for evidence in self._evidence.values():
            # Check reliability threshold
            evidence_index = reliability_order.index(evidence.reliability)
            if evidence_index > min_index:
                continue

            # Check if hypothesis is mentioned in entity refs or claims
            if hypothesis_label in evidence.entity_refs or any(hypothesis_label.lower() in c.text.lower() for c in evidence.claims):
                results.append(evidence)

        # Sort by reliability (HARD first)
        return sorted(results, key=lambda e: reliability_order.index(e.reliability))

    # -------------------------------------------------------------------------
    # Permission-Aware Retrieval
    # -------------------------------------------------------------------------

    def find_with_permissions(
        self,
        required_tags: list[str],
        client_id: str | None = None
    ) -> list[EvidenceItem]:
        """Get evidence that the user has permission to access."""
        results = []
        for evidence in self._evidence.values():
            # Check client_id if multi-tenant
            if client_id and evidence.client_id and evidence.client_id != client_id:
                continue

            # Check permission tags
            if evidence.permission_tags and not any(
                tag in required_tags for tag in evidence.permission_tags
            ):
                continue

            results.append(evidence)

        return results

    # -------------------------------------------------------------------------
    # Semantic Search (CTX-019)
    # -------------------------------------------------------------------------

    def search_by_text(
        self, query: str, fields: list[str] | None = None,
    ) -> list[EvidenceItem]:
        """Case-insensitive substring search across evidence fields."""
        search_fields = fields or ["title", "content"]
        query_lower = query.lower()
        results: list[EvidenceItem] = []
        for evidence in self._evidence.values():
            for f in search_fields:
                val = getattr(evidence, f, "")
                if val and query_lower in val.lower():
                    results.append(evidence)
                    break
            else:
                # Also search claim text
                if "claims" not in search_fields:
                    continue
                if any(query_lower in c.text.lower() for c in evidence.claims):
                    results.append(evidence)
        return results

    def semantic_find_evidence(
        self,
        query: str,
        semantic_store,
        min_reliability: "ReliabilityClass" = None,
    ) -> list[EvidenceItem]:
        """Expand query through SemanticStore, then search entity_refs + text."""
        if min_reliability is None:
            min_reliability = ReliabilityClass.RUMOR
        # Build expanded term set
        terms: set = {query}
        canonical = semantic_store.resolve_to_canonical(query)
        if canonical:
            terms.add(canonical.term)
            terms.update(semantic_store.get_all_variants(canonical.id))

        # Search entity_refs, title, content, and claims
        reliability_order = [ReliabilityClass.HARD, ReliabilityClass.SOFT, ReliabilityClass.RUMOR]
        min_index = reliability_order.index(min_reliability)
        seen: set[str] = set()
        results: list[EvidenceItem] = []
        for term in terms:
            for evidence in self._evidence.values():
                if evidence.id in seen:
                    continue
                if reliability_order.index(evidence.reliability) > min_index:
                    continue
                if term in evidence.entity_refs or term.lower() in evidence.title.lower() or term.lower() in evidence.content.lower():
                    results.append(evidence)
                    seen.add(evidence.id)
        return sorted(results, key=lambda e: reliability_order.index(e.reliability))

    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Get store statistics."""
        return {
            "total": len(self._evidence),
            "by_type": {t.value: len(ids) for t, ids in self._by_type.items()},
            "by_reliability": {r.value: len(ids) for r, ids in self._by_reliability.items()},
            "by_source": {s.value: len(ids) for s, ids in self._by_source.items() if ids},
            "entities_indexed": len(self._by_entity),
        }

    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------

    def add_metric_evidence(
        self,
        metric: str,
        value: Any,
        time_period: str,
        entity_refs: list[str],
        source: SourceSystem = SourceSystem.CLAIMS
    ) -> EvidenceItem:
        """Helper to add metric-type evidence."""
        evidence = EvidenceItem(
            type=EvidenceType.METRIC,
            reliability=ReliabilityClass.HARD,  # Metrics are typically HARD
            source_system=source,
            title=f"{metric} for {time_period}",
            content=str(value),
            metric_refs=[metric],
            entity_refs=entity_refs,
            time_period=time_period,
        )
        return self.add(evidence)

    def add_field_note(
        self,
        content: str,
        collected_by: str,
        entity_refs: list[str],
        brand: str | None = None,
        geography: str | None = None
    ) -> EvidenceItem:
        """Helper to add field note evidence."""
        evidence = EvidenceItem(
            type=EvidenceType.DOCUMENT,
            reliability=ReliabilityClass.SOFT,
            source_system=SourceSystem.FIELD_NOTES,
            title=f"Field Note - {datetime.utcnow().strftime('%Y-%m-%d')}",
            content=content,
            collected_by=collected_by,
            entity_refs=entity_refs,
            brand=brand,
            geography=geography,
        )
        return self.add(evidence)

    def add_competitor_intel(
        self,
        content: str,
        source_uri: str = "",
        entity_refs: list[str] = None
    ) -> EvidenceItem:
        """Helper to add competitor intel (RUMOR reliability)."""
        evidence = EvidenceItem(
            type=EvidenceType.DOCUMENT,
            reliability=ReliabilityClass.RUMOR,  # Rumor until verified
            source_system=SourceSystem.COMPETITOR_INTEL,
            title="Competitor Intelligence",
            content=content,
            source_uri=source_uri,
            entity_refs=entity_refs or [],
        )
        return self.add(evidence)
