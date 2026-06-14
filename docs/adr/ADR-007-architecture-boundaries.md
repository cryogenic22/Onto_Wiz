# ADR-007: Architecture Boundaries Enforced by Cathedral Keeper

**Date:** 2026-01-31
**Status:** SETTLED (Cathedral Keeper will block violations)
**Deciders:** Tech Lead
**Source:** DEC-007

## Context

Clean architecture requires that dependencies point inward: the API layer depends on core, but core must never depend on the API layer. This ensures core logic is invocable without the web server, enabling testing, reuse, and eventual microservice extraction.

## Decision

`src/core/` and `src/reasoning/` must never import from `src/api/`. This is enforced by the Cathedral Keeper (CK) policy tool.

**Allowed dependency direction:**
```
src/api/ --> src/core/
src/api/ --> src/reasoning/
src/core/ --> (stdlib, pydantic only)
src/reasoning/ --> src/core/
```

**Forbidden:**
```
src/core/ -X-> src/api/
src/reasoning/ -X-> src/api/
```

## Consequences

**Positive:**
- Core logic is testable without FastAPI or HTTP infrastructure
- Clear module boundaries prevent spaghetti imports
- Enables future extraction of core as a standalone library or microservice
- SEN-003 architecture review confirmed 0 boundary violations

**Negative:**
- Sometimes requires passing callbacks or interfaces rather than direct imports
- New developers must understand the layering to avoid CK rejections

**Neutral:**
- The boundary is checked automatically by `cathedral-keeper/ck.py` in CI and pre-commit
