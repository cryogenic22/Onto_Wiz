# ADR-001: Delta Model — Everything is a Proposal

**Date:** 2026-01-31
**Status:** SETTLED
**Deciders:** Tech Lead
**Source:** DEC-001

## Context

The Onto_Wiz system manages a knowledge graph for enterprise pharma commercial intelligence. Mutations to this graph (new entities, edges, patterns, guardrails) must be auditable, reversible, and governed. Enterprise pharma clients require full audit trails for regulatory compliance.

Direct writes to the knowledge graph would bypass governance, making it impossible to trace who changed what, when, and why.

## Decision

All mutations to the knowledge graph go through Deltas. No direct writes are permitted.

A Delta is a proposal: it is created, reviewed (automatically or by a human), and only then promoted to the live graph. Every Delta has a status lifecycle (`proposed` -> `approved`/`rejected` -> `merged`), a confidence score, a blast radius, evidence pointers, and full audit metadata.

## Consequences

**Positive:**
- Full audit trail for every change to the knowledge graph
- Reversibility: any merged delta can be traced and its effects understood
- Governance: human-in-the-loop review is native to the model
- Self-healing: the system can propose corrections as new deltas

**Negative:**
- Higher write latency (proposal -> review -> promotion vs. direct write)
- More complex store layer (DeltaStore + status indexes + promotion pipeline)
- All agents must learn the delta protocol rather than writing directly

**Neutral:**
- The Delta model is the foundation for CTX-005 (classification), CTX-006 (routing), and the entire HITL governance chain
