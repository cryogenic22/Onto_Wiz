# Design Document: Semantic Store

## Overview

The SemanticStore captures synonyms, aliases, taxonomy, and linguistic patterns from SME games. This is the knowledge layer that helps AI agents understand that "PA", "Prior Auth", and "Prior Authorization" mean the same thing.

## Problem Statement

SMEs use varied terminology:
- "PA" = "Prior Auth" = "Prior Authorization"
- "NBRx" = "New to Brand" = "New Prescriptions"
- "KOL" = "Key Opinion Leader" = "Thought Leader"

Without semantic capture:
1. AI agents miss synonyms in queries
2. Pattern matching fails on terminology variations
3. Ontology becomes brittle and hard to maintain

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SemanticStore                               │
├─────────────────────────────────────────────────────────────────┤
│  Canonical Terms                                                │
│   - Preferred term for each concept                             │
│   - Domain scope (Commercial, Clinical, etc.)                   │
│   - Taxonomy parent (for hierarchies)                           │
├─────────────────────────────────────────────────────────────────┤
│  Semantic Relations                                             │
│   - SYNONYM: Same meaning                                       │
│   - ALIAS: Abbreviation                                         │
│   - BROADER: Taxonomy parent                                    │
│   - NARROWER: Taxonomy child                                    │
│   - CONTEXT_DEPENDENT: Meaning varies                           │
│   - NOT_SYNONYM: Anti-pattern                                   │
├─────────────────────────────────────────────────────────────────┤
│  Functional Domains                                             │
│   - Commercial                                                  │
│   - Market Access                                               │
│   - Clinical                                                    │
│   - Supply Chain                                                │
│   - Medical Affairs                                             │
│   - (extensible)                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Data Model

### CanonicalTerm

```python
@dataclass
class CanonicalTerm:
    id: str
    term: str  # "Prior_Authorization"
    domains: List[FunctionalDomain]
    definition: str
    parent_term_id: Optional[str]  # Taxonomy
    status: str  # active, deprecated, draft
```

### SemanticRelation

```python
@dataclass
class SemanticRelation:
    source_term: str  # "PA"
    target_term_id: str  # ID of Prior_Authorization
    relation_type: SemanticRelationType  # ALIAS
    domains: List[FunctionalDomain]
    confidence: float
    source_event_id: Optional[str]  # SME game
    context_note: Optional[str]  # "In oncology..."
```

## Functional Domains

The system is modular - domains can be added without breaking existing ones:

```python
class FunctionalDomain(str, Enum):
    COMMERCIAL = "commercial"
    MARKET_ACCESS = "market_access"
    CLINICAL = "clinical"
    SUPPLY_CHAIN = "supply_chain"
    MEDICAL_AFFAIRS = "medical_affairs"
    REGULATORY = "regulatory"
    # ... extensible
```

## Core Operations

### Resolve to Canonical

```python
# AI agent sees "PA" in user query
canonical = store.resolve_to_canonical("PA")
# Returns: CanonicalTerm(term="Prior_Authorization", ...)
```

### Get All Variants

```python
# For search expansion
variants = store.get_all_variants(pa_id)
# Returns: ["PA", "Prior Auth", "Prior Approval"]
```

### Taxonomy Navigation

```python
# Get all children of HCP
children = store.get_taxonomy_children(hcp_id)
# Returns: [Prescriber, ...]

# Get path to root
path = store.get_taxonomy_path(oncologist_id)
# Returns: [Oncologist, Prescriber, HCP]
```

### Anti-Synonyms

```python
# Mark terms as NOT equivalent
store.add_anti_synonym("Access_Friction", "Demand_Erosion")

# This prevents AI from conflating these terms
```

## Auto-Extraction from SME Games

```python
# SME says: "the KOL (Key Opinion Leader) mentioned..."
captures = extract_semantic_captures(sme_text)
# Returns proposed relations for review
```

Patterns detected:
- "X (Y)" - Parenthetical definitions
- "X, also called Y" - Explicit synonyms
- "X, or Y" - Alternative names

## Seeding

Pre-populated with common commercial pharma terms:

| Canonical | Aliases/Synonyms |
|:---|:---|
| Prior_Authorization | PA, Prior Auth, Prior Approval |
| New_to_Brand_Rx | NBRx, New Prescriptions, New Starts |
| Total_Rx | TRx, Total Prescriptions |
| Key_Opinion_Leader | KOL, Thought Leader |
| Health_Care_Professional | HCP, Provider, Physician, Doctor |
| Access_Friction | Access Issues, Access Barriers |

## Integration Points

### With Pattern Matching

```python
# Pattern defines: applies_when_signals = ["PA_reject"]
# User query mentions: "Prior Auth rejects"
# SemanticStore resolves both to Prior_Authorization
# → Pattern matches
```

### With Query Expansion

```python
# User: "Why are PA edits causing issues?"
# Expanded: "Prior_Authorization" + synonyms
# Graph search includes all variants
```

### With Delta Generator

```python
# DeltaGenerator uses SemanticStore to:
# 1. Normalize SME terms to canonical IDs
# 2. Capture new synonyms from free-text
# 3. Propose semantic relation deltas
```

## Implementation Status

| Component | Status |
|:---|:---|
| FunctionalDomain enum | ✅ Done |
| CanonicalTerm | ✅ Done |
| SemanticRelation | ✅ Done |
| SemanticStore | ✅ Done |
| Commercial seeding | ✅ Done |
| Auto-extraction | ✅ Basic |
| Integration tests | 🔲 Pending |

## File Location

`src/core/semantic_store.py` - ~500 lines

## Example Usage

```python
from src.core import SemanticStore, FunctionalDomain

# Create and seed
store = SemanticStore()
store.seed_commercial_synonyms()

# Resolve term
canonical = store.resolve_to_canonical("PA")
print(f"PA = {canonical.term}")
# Output: PA = Prior_Authorization

# Get variants for search
variants = store.get_all_variants(canonical.id)
print(variants)
# Output: ['PA', 'Prior Auth', 'Prior Approval']

# Check taxonomy
hcp = store.find_canonical_by_name("Health_Care_Professional")
children = store.get_taxonomy_children(hcp.id)
print([c.term for c in children])
# Output: ['Prescriber']
```
