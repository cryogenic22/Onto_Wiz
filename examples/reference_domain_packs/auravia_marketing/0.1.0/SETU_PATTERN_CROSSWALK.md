# Setu Pattern Crosswalk

The Setu Hindi domain pack is a useful implementation precedent for modular curation and typed compilation. It is not a suitable pharma schema to copy directly.

## Patterns adopted

| Setu pattern | Pharma marketing translation |
|---|---|
| `grammar.yaml` controlled feature values | Controlled claim, purpose, applicability, metric, and decision vocabularies |
| `lexicon.yaml` plus deterministic shards | Preferred brand terms, governed variants, prohibited expressions, and semantic modules |
| Stable lexeme ID separate from concept | Stable concept or claim ID separate from textual realization |
| One learner default plus alternatives | One preferred market-specific term or claim variant plus governed alternatives |
| `nominals.yaml` | Entity, metric, table, grain, and relationship semantics |
| `romanisation.yaml` | Rendering, abbreviation, controlled-language, and channel-style rules |
| `error_taxonomy.yaml` | Named MLR, grounding, applicability, data, causal, privacy, and release failures |
| Typed `DomainPack` loader | One Onto_Wiz compiler boundary producing immutable typed artifacts and projections |
| Seed-to-reviewed curation | Proposed to SME-endorsed to ratified to released lifecycle |

Specific useful Setu behavior includes:

- `domain/hindi/lexicon.yaml` declares shards instead of discovering them implicitly.
- The loader composes shards deterministically and fails when the manifest and files disagree.
- Cross-module checks reject duplicate IDs, broken references, and inconsistent controlled features.
- The error taxonomy associates named failures with checks and can-fail tests.

## Extensions required for Onto_Wiz

Setu does not provide the complete contract required here. Onto_Wiz adds:

- Pack-level releases, compatibility, digests, diffs, rollback, and attestations.
- Source-instance identity separated from immutable content identity.
- Exact multi-span provenance and evidence relationships.
- Typed relationship instances with cardinality and evidence requirements.
- Client, market, audience, purpose, channel, indication, and temporal applicability.
- Human review decisions and authority.
- Semantic metrics, governed tables, temporal joins, and query receipts.
- Rebuildable graph, lexical, vector, catalog, and agent-contract projections.
- Critical evaluation gates and candidate-versus-released states.
- Tenant isolation and access-aware retrieval.

## Pattern to avoid

Do not duplicate one fact across modules and rely on tests to keep the copies synchronized. A canonical artifact may be extended by another module, but the extension must reference the canonical ID and must not redefine its authority. Generated inventories and documentation should be compiled from the pack to prevent count and version drift.

