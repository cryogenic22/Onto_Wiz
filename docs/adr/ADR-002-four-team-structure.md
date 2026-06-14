# ADR-002: Four-Team Structure — LENS + CORTEX + ATLAS + SENTINEL

**Date:** 2026-02-01 (revised from 2-team to 4-team)
**Status:** SETTLED (revisit only when codebase exceeds 15,000 lines)
**Deciders:** Tech Lead
**Source:** DEC-002

## Context

As the codebase grew to ~6,500 lines with ontology content and quality tooling, the original 2-team structure (LENS + CORTEX) could not scale. Domain knowledge work (ontology YAML, gold sets, scenarios) and quality enforcement (CI, reviews, audits) needed dedicated ownership separate from feature delivery teams.

## Decision

Four teams with clean file ownership:

| Team | Code | Owns | Focus |
|------|------|------|-------|
| LENS | LENS | `src/api/`, `frontend/`, API tests | UI + API surface |
| CORTEX | CTX | `src/core/`, `src/reasoning/`, core tests | Core engine |
| ATLAS | ATL | `ontology/`, `tests/gold_set/` | Domain content + ontology |
| SENTINEL | SEN | `quality/`, `.github/workflows/`, `docs/reviews/` | Quality infrastructure |

## Consequences

**Positive:**
- ATLAS decouples ontology design (YAML, gold sets, scenarios) from Python engineering
- SENTINEL decouples CI/CD, quality audits, and architecture reviews from feature velocity
- Both can operate in parallel without blocking LENS or CORTEX
- Clean file ownership prevents merge conflicts

**Negative:**
- More coordination overhead (4 teams vs 2)
- Cross-team dependencies require explicit tracking in BOARD.md
- WIP limit of 1 per team means max 4 concurrent tickets

**Neutral:**
- Team structure maps directly to ticket prefixes (LENS-NNN, CTX-NNN, ATL-NNN, SEN-NNN)
