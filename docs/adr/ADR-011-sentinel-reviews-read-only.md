# ADR-011: SENTINEL Reviews Are Read-Only

**Date:** 2026-02-01
**Status:** SETTLED
**Deciders:** Tech Lead
**Source:** DEC-011

## Context

Architecture reviews that also fix issues conflate auditing with implementation. If the reviewer is also the fixer, the review loses objectivity — findings may be downplayed to avoid creating work, or fixes may be applied without proper review from the owning team.

## Decision

SENTINEL review tickets (SEN-003, SEN-004, SEN-005, SEN-006, SEN-007, etc.) must NOT modify source code. They produce reports in `docs/reviews/` and recommend tickets. Only the Tech Lead creates actual backlog items from recommendations.

**SENTINEL can:**
- Read all source code
- Run quality tools (slop checker, quality gate, cathedral keeper)
- Create files in `docs/reviews/`, `docs/adr/`, `quality/`, `tests/perf/`
- Create benchmark/test infrastructure (non-source)

**SENTINEL cannot:**
- Modify files in `src/`
- Modify files in `frontend/src/`
- Modify files in `ontology/`
- Create backlog tickets directly

## Consequences

**Positive:**
- Separation of concerns: SENTINEL identifies problems, CORTEX/LENS/ATLAS fix them
- Review reports are objective (no incentive to minimize findings)
- Audit trail is clean: reviews are timestamped documents, fixes are separate tickets

**Negative:**
- Findings cannot be immediately fixed — requires a round-trip through the Tech Lead
- Small fixes (e.g., a typo in a docstring found during review) still require a separate ticket

**Neutral:**
- This mirrors real-world audit practice (auditor != implementer)
- SENTINEL's test infrastructure (benchmark scripts, quality configs) is explicitly permitted as it's tooling, not application code
