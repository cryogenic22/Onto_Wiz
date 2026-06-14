"""
Onto_Wiz Semantic Capture

Captures synonyms, aliases, taxonomy, and linguistic patterns from SME games.
This is the knowledge layer that helps AI agents understand context.

During SME games, experts use varied terminology:
- "PA" = "Prior Auth" = "Prior Authorization"
- "NBRx" = "New to Brand" = "New Prescriptions"
- "KOL" = "Key Opinion Leader" = "Thought Leader"

This module captures:
1. Synonyms - Different terms for the same concept
2. Aliases - Abbreviations, acronyms, shorthand
3. Taxonomy - Hierarchical relationships (HCP -> Prescriber -> Oncologist)
4. Context-dependent meanings - "Access" means different things in different TAs
5. Anti-patterns - Terms that SHOULD NOT be treated as synonyms

The semantic layer is domain-aware - Commercial synonyms may differ from Clinical.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# =============================================================================
# FUNCTIONAL DOMAINS (Modular & Extensible)
# =============================================================================

class FunctionalDomain(str, Enum):
    """
    High-level functional domains.
    Each domain has its own ontology, patterns, and semantic conventions.
    The architecture is modular - new domains can be added without breaking existing ones.
    """
    # Core Commercial
    COMMERCIAL = "commercial"
    MARKET_ACCESS = "market_access"
    FIELD_OPERATIONS = "field_operations"
    MARKETING = "marketing"
    ANALYTICS = "analytics"

    # Supply Chain
    SUPPLY_CHAIN = "supply_chain"
    MANUFACTURING = "manufacturing"
    DISTRIBUTION = "distribution"
    INVENTORY = "inventory"

    # Clinical & Medical
    CLINICAL = "clinical"
    MEDICAL_AFFAIRS = "medical_affairs"
    PHARMACOVIGILANCE = "pharmacovigilance"
    REGULATORY = "regulatory"

    # R&D
    RESEARCH = "research"
    DEVELOPMENT = "development"

    # Corporate
    FINANCE = "finance"
    HR = "human_resources"
    LEGAL = "legal"

    # Cross-functional
    CROSS_FUNCTIONAL = "cross_functional"


class SemanticRelationType(str, Enum):
    """Types of semantic relationships between terms."""
    SYNONYM = "synonym"               # Same meaning (PA = Prior Authorization)
    ALIAS = "alias"                   # Abbreviation/shorthand (NBRx)
    BROADER = "broader"               # Taxonomy parent (HCP -> Prescriber)
    NARROWER = "narrower"             # Taxonomy child (Prescriber -> Oncologist)
    RELATED = "related"               # Associated but not equivalent
    CONTEXT_DEPENDENT = "context_dependent"  # Meaning varies by context
    NOT_SYNONYM = "not_synonym"       # Explicitly NOT the same (guardrail)


# =============================================================================
# SEMANTIC ITEMS
# =============================================================================

@dataclass
class CanonicalTerm:
    """
    The canonical (preferred) term for a concept.
    All synonyms and aliases map back to this.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    term: str = ""

    # Domain scope - which domains use this term
    domains: list[FunctionalDomain] = field(default_factory=list)

    # Definition
    definition: str = ""
    definition_source: str = ""

    # Taxonomy position
    parent_term_id: str | None = None  # For hierarchies

    # Governance
    status: str = "active"  # active, deprecated, draft
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "term": self.term,
            "domains": [d.value for d in self.domains],
            "definition": self.definition,
            "parent_term_id": self.parent_term_id,
            "status": self.status,
        }


@dataclass
class SemanticRelation:
    """
    A relationship between two terms.
    Captures synonyms, aliases, taxonomy, and anti-patterns.
    """
    id: str = field(default_factory=lambda: str(uuid4()))

    # The relationship
    source_term: str = ""             # The term used by SME
    target_term_id: str = ""          # The canonical term ID
    relation_type: SemanticRelationType = SemanticRelationType.SYNONYM

    # Context - relationship may only hold in certain contexts
    domains: list[FunctionalDomain] = field(default_factory=list)
    therapeutic_areas: list[str] = field(default_factory=list)

    # Confidence and provenance
    confidence: float = 0.8
    source_event_id: str | None = None  # Which SME game captured this
    captured_from: str = ""  # e.g., "sme_game", "document", "manual"

    # For context-dependent meanings
    context_note: str | None = None  # e.g., "In oncology, means X"

    # Governance
    status: str = "proposed"  # proposed, approved, rejected
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_term": self.source_term,
            "target_term_id": self.target_term_id,
            "relation_type": self.relation_type.value,
            "domains": [d.value for d in self.domains],
            "therapeutic_areas": self.therapeutic_areas,
            "confidence": self.confidence,
            "context_note": self.context_note,
            "status": self.status,
        }


@dataclass
class TermUsage:
    """
    Records how a term is used in context.
    Helps understand meaning through usage patterns.
    """
    term: str
    context: str                      # The sentence/context where used
    domain: FunctionalDomain = FunctionalDomain.COMMERCIAL
    therapeutic_area: str | None = None
    source_event_id: str | None = None
    captured_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# SEMANTIC STORE
# =============================================================================

class SemanticStore:
    """
    Store for semantic knowledge - synonyms, aliases, taxonomy.

    This is the "language layer" that helps AI agents understand
    that "PA", "Prior Auth", and "Prior Authorization" mean the same thing.

    The store is domain-aware - Commercial synonyms may differ from Clinical.
    """

    def __init__(self):
        self._canonical_terms: dict[str, CanonicalTerm] = {}
        self._relations: dict[str, SemanticRelation] = {}
        self._by_term: dict[str, set[str]] = {}  # term -> relation IDs
        self._by_canonical: dict[str, set[str]] = {}  # canonical ID -> relation IDs
        self._usage_log: list[TermUsage] = []

        # Anti-synonyms (terms that should NOT be treated as equivalent)
        self._anti_synonyms: set[tuple[str, str]] = set()

    # -------------------------------------------------------------------------
    # Canonical Terms
    # -------------------------------------------------------------------------

    def add_canonical_term(self, term: CanonicalTerm) -> CanonicalTerm:
        """Add a canonical (preferred) term."""
        self._canonical_terms[term.id] = term
        return term

    def get_canonical_term(self, term_id: str) -> CanonicalTerm | None:
        """Get canonical term by ID."""
        return self._canonical_terms.get(term_id)

    def find_canonical_by_name(self, name: str) -> CanonicalTerm | None:
        """Find canonical term by name."""
        for term in self._canonical_terms.values():
            if term.term.lower() == name.lower():
                return term
        return None

    # -------------------------------------------------------------------------
    # Semantic Relations
    # -------------------------------------------------------------------------

    def add_relation(self, relation: SemanticRelation) -> SemanticRelation:
        """Add a semantic relation (synonym, alias, etc.)."""
        # Check for anti-synonym
        source_lower = relation.source_term.lower()
        target_term = self._canonical_terms.get(relation.target_term_id)
        if target_term:
            target_lower = target_term.term.lower()
            if (source_lower, target_lower) in self._anti_synonyms:
                raise ValueError(f"'{relation.source_term}' is explicitly NOT a synonym of '{target_term.term}'")

        self._relations[relation.id] = relation

        # Index by source term
        if relation.source_term not in self._by_term:
            self._by_term[relation.source_term] = set()
        self._by_term[relation.source_term].add(relation.id)

        # Index by canonical
        if relation.target_term_id not in self._by_canonical:
            self._by_canonical[relation.target_term_id] = set()
        self._by_canonical[relation.target_term_id].add(relation.id)

        return relation

    def add_synonym(
        self,
        synonym: str,
        canonical_term_id: str,
        domains: list[FunctionalDomain] = None,
        confidence: float = 0.8,
        source_event_id: str | None = None
    ) -> SemanticRelation:
        """Convenience method to add a synonym."""
        relation = SemanticRelation(
            source_term=synonym,
            target_term_id=canonical_term_id,
            relation_type=SemanticRelationType.SYNONYM,
            domains=domains or [FunctionalDomain.COMMERCIAL],
            confidence=confidence,
            source_event_id=source_event_id,
            captured_from="sme_game" if source_event_id else "manual",
        )
        return self.add_relation(relation)

    def add_alias(
        self,
        alias: str,
        canonical_term_id: str,
        domains: list[FunctionalDomain] = None
    ) -> SemanticRelation:
        """Add an abbreviation/alias (e.g., PA for Prior Authorization)."""
        relation = SemanticRelation(
            source_term=alias,
            target_term_id=canonical_term_id,
            relation_type=SemanticRelationType.ALIAS,
            domains=domains or [FunctionalDomain.COMMERCIAL],
            confidence=1.0,  # Aliases are definitional
            captured_from="manual",
        )
        return self.add_relation(relation)

    def add_anti_synonym(self, term1: str, term2: str):
        """
        Mark two terms as explicitly NOT synonyms.
        This prevents AI from incorrectly conflating them.
        """
        self._anti_synonyms.add((term1.lower(), term2.lower()))
        self._anti_synonyms.add((term2.lower(), term1.lower()))

    # -------------------------------------------------------------------------
    # Lookups
    # -------------------------------------------------------------------------

    def resolve_to_canonical(
        self,
        term: str,
        domain: FunctionalDomain | None = None
    ) -> CanonicalTerm | None:
        """
        Resolve any term (synonym, alias, etc.) to its canonical form.
        This is the main lookup for AI agents.
        """
        # Check if it's already canonical
        canonical = self.find_canonical_by_name(term)
        if canonical:
            return canonical

        # Look up in relations
        term_lower = term.lower()
        for relation in self._relations.values():
            if relation.source_term.lower() == term_lower:
                # Check domain filter
                if domain and domain not in relation.domains:
                    continue
                return self._canonical_terms.get(relation.target_term_id)

        return None

    def get_all_variants(
        self,
        canonical_term_id: str,
        include_aliases: bool = True
    ) -> list[str]:
        """
        Get all synonyms and aliases for a canonical term.
        Useful for search expansion and understanding.
        """
        variants = []

        relation_ids = self._by_canonical.get(canonical_term_id, set())
        for rid in relation_ids:
            relation = self._relations.get(rid)
            if relation and (
                include_aliases or relation.relation_type != SemanticRelationType.ALIAS
            ):
                variants.append(relation.source_term)

        return variants

    def get_taxonomy_children(self, parent_term_id: str) -> list[CanonicalTerm]:
        """Get all children in taxonomy hierarchy."""
        children = []
        for term in self._canonical_terms.values():
            if term.parent_term_id == parent_term_id:
                children.append(term)
        return children

    def get_taxonomy_path(self, term_id: str) -> list[CanonicalTerm]:
        """Get path from term up to root of taxonomy."""
        path = []
        current_id = term_id

        while current_id:
            term = self._canonical_terms.get(current_id)
            if not term:
                break
            path.append(term)
            current_id = term.parent_term_id

        return path

    # -------------------------------------------------------------------------
    # Term Usage & Learning
    # -------------------------------------------------------------------------

    def log_usage(self, usage: TermUsage):
        """Log how a term was used in context."""
        self._usage_log.append(usage)

    def get_usage_patterns(self, term: str, limit: int = 10) -> list[TermUsage]:
        """Get recent usage patterns for a term."""
        matching = [u for u in self._usage_log if u.term.lower() == term.lower()]
        return matching[-limit:]

    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        return {
            "canonical_terms": len(self._canonical_terms),
            "relations": len(self._relations),
            "unique_terms_indexed": len(self._by_term),
            "anti_synonyms": len(self._anti_synonyms) // 2,
            "usage_logs": len(self._usage_log),
        }

    # -------------------------------------------------------------------------
    # Seed with Common Commercial Synonyms
    # -------------------------------------------------------------------------

    def seed_commercial_synonyms(self):
        """
        Seed the store with common commercial pharma synonyms.
        These are the terms SMEs will use interchangeably.
        """
        # Prior Authorization
        pa = self.add_canonical_term(CanonicalTerm(
            term="Prior_Authorization",
            domains=[FunctionalDomain.COMMERCIAL, FunctionalDomain.MARKET_ACCESS],
            definition="Requirement for payer approval before medication coverage",
        ))
        self.add_alias("PA", pa.id)
        self.add_synonym("Prior Auth", pa.id)
        self.add_synonym("Prior Approval", pa.id)

        # New to Brand Rx
        nbrx = self.add_canonical_term(CanonicalTerm(
            term="New_to_Brand_Rx",
            domains=[FunctionalDomain.COMMERCIAL, FunctionalDomain.ANALYTICS],
            definition="Prescriptions from patients new to the brand",
        ))
        self.add_alias("NBRx", nbrx.id)
        self.add_synonym("New Prescriptions", nbrx.id)
        self.add_synonym("New Starts", nbrx.id)

        # Total Rx
        trx = self.add_canonical_term(CanonicalTerm(
            term="Total_Rx",
            domains=[FunctionalDomain.COMMERCIAL, FunctionalDomain.ANALYTICS],
            definition="Total prescriptions across all patients",
        ))
        self.add_alias("TRx", trx.id)
        self.add_synonym("Total Prescriptions", trx.id)

        # Key Opinion Leader
        kol = self.add_canonical_term(CanonicalTerm(
            term="Key_Opinion_Leader",
            domains=[FunctionalDomain.COMMERCIAL, FunctionalDomain.MEDICAL_AFFAIRS],
            definition="Influential HCP who shapes treatment practices",
        ))
        self.add_alias("KOL", kol.id)
        self.add_synonym("Thought Leader", kol.id)
        self.add_synonym("Key Influencer", kol.id)

        # Health Care Professional
        hcp = self.add_canonical_term(CanonicalTerm(
            term="Health_Care_Professional",
            domains=[FunctionalDomain.COMMERCIAL],
            definition="Any licensed healthcare provider",
        ))
        self.add_alias("HCP", hcp.id)
        self.add_synonym("Provider", hcp.id)
        self.add_synonym("Physician", hcp.id)
        self.add_synonym("Doctor", hcp.id)

        # Add taxonomy: HCP -> Prescriber -> Specialist
        prescriber = self.add_canonical_term(CanonicalTerm(
            term="Prescriber",
            domains=[FunctionalDomain.COMMERCIAL],
            definition="HCP with prescribing authority",
            parent_term_id=hcp.id,
        ))

        self.add_canonical_term(CanonicalTerm(
            term="Oncologist",
            domains=[FunctionalDomain.COMMERCIAL],
            definition="Physician specializing in cancer treatment",
            parent_term_id=prescriber.id,
        ))

        # Access-related
        access_friction = self.add_canonical_term(CanonicalTerm(
            term="Access_Friction",
            domains=[FunctionalDomain.COMMERCIAL, FunctionalDomain.MARKET_ACCESS],
            definition="Barriers to patient medication access (PA, step edits, etc.)",
        ))
        self.add_synonym("Access Issues", access_friction.id)
        self.add_synonym("Access Barriers", access_friction.id)
        self.add_synonym("Payer Friction", access_friction.id)

        # Anti-synonyms (terms that should NOT be conflated)
        self.add_anti_synonym("Access_Friction", "Demand_Erosion")
        self.add_anti_synonym("NBRx", "TRx")

        print(f"Seeded {self.stats()['canonical_terms']} canonical terms with synonyms")


# =============================================================================
# SEMANTIC CAPTURE FROM SME GAMES
# =============================================================================

def extract_semantic_captures(
    sme_text: str,
    domain: FunctionalDomain = FunctionalDomain.COMMERCIAL,
    event_id: str | None = None
) -> list[SemanticRelation]:
    """
    Extract potential synonyms/aliases from SME free-text responses.

    Looks for patterns like:
    - "PA (Prior Authorization)"
    - "NBRx, also called new starts"
    - "the KOL, or thought leader"

    Returns proposed relations for review, not auto-approved.
    """
    # Simple pattern matching - in production, use NLP
    proposed = []

    # Pattern: "X (Y)" or "X [Y]" - parenthetical definitions
    import re
    paren_pattern = r'(\w+)\s*[\(\[]([^\)\]]+)[\)\]]'
    for match in re.finditer(paren_pattern, sme_text):
        alias = match.group(1).strip()
        match.group(2).strip()

        proposed.append(SemanticRelation(
            source_term=alias,
            target_term_id="",  # Needs resolution
            relation_type=SemanticRelationType.ALIAS,
            domains=[domain],
            confidence=0.6,  # Lower confidence for auto-extracted
            source_event_id=event_id,
            captured_from="sme_game_nlp",
            context_note=f"Extracted from: {sme_text[:50]}...",
            status="proposed",
        ))

    # Pattern: "X, also called Y" or "X, or Y"
    also_pattern = r'(\w+(?:\s+\w+)?),?\s+(?:also called|also known as|or)\s+(\w+(?:\s+\w+)?)'
    for match in re.finditer(also_pattern, sme_text, re.IGNORECASE):
        term1 = match.group(1).strip()
        term2 = match.group(2).strip()

        proposed.append(SemanticRelation(
            source_term=term2,
            target_term_id="",  # Needs resolution to canonical
            relation_type=SemanticRelationType.SYNONYM,
            domains=[domain],
            confidence=0.5,
            source_event_id=event_id,
            captured_from="sme_game_nlp",
            context_note=f"'{term1}' and '{term2}' used interchangeably",
            status="proposed",
        ))

    return proposed
