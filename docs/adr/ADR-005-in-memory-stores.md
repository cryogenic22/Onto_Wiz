# ADR-005: In-Memory Stores Until Phase 6

**Date:** 2026-01-31
**Status:** SETTLED (do not add database dependencies before Phase 6)
**Deciders:** Tech Lead
**Source:** DEC-005

## Context

The system needs data persistence for deltas, patterns, guardrails, sessions, and the knowledge graph. Introducing a database (Postgres, Neo4j) early adds ORM complexity, migration tooling, connection management, and Docker dependencies — all before the domain model is stable.

## Decision

All stores remain in-memory (Python dicts/lists) until Phase 6 introduces Postgres/Neo4j. The store interfaces are abstracted so swapping in a database later requires implementing the same interface.

## Consequences

**Positive:**
- Zero infrastructure dependencies for development
- Sub-millisecond store operations (SEN-005 baseline confirms all ops < 0.2ms)
- Domain model can evolve rapidly without migration overhead
- Testing is trivial (no database setup/teardown)

**Negative:**
- All data is lost on restart
- No concurrent access safety (single-process only)
- Memory-bound: projected ~115 MB at 100K deltas, viable up to ~500K on a 512MB server
- Performance characteristics will change dramatically when persistence is added (10-50x latency increase expected)

**Neutral:**
- Store interfaces (`DeltaStore`, `JudgmentStore`, `GraphStore`, `EvidenceStore`) define the contract; implementations are swappable
- SEN-005 performance baseline provides the reference for regression detection after Phase 6 migration
