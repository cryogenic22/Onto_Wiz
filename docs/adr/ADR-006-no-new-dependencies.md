# ADR-006: No New Dependencies Without Lead Approval

**Date:** 2026-01-31
**Status:** SETTLED
**Deciders:** Tech Lead
**Source:** DEC-006

## Context

Dependency creep is a major quality risk ("slop vector") in AI-assisted development. Each new package is an attack surface, a compatibility risk, a licensing concern, and a context burden for agents. The current stack covers all Phase 2-5 requirements.

## Decision

Agents cannot add pip/npm packages without explicit Lead approval in `Lead2Dev.md`.

**Approved stack:**
- **Python:** FastAPI, Pydantic, PyYAML, pytest (+ uvicorn, httpx for testing)
- **Frontend:** Next.js, React, ReactFlow, Tailwind CSS
- **Quality:** ruff, mypy (dev only)

## Consequences

**Positive:**
- Controlled attack surface (SEN-006 security review benefits from known, small dependency set)
- No surprise version conflicts or breaking changes from transitive dependencies
- Agents learn to solve problems with stdlib + approved libraries

**Negative:**
- Some tasks require more code than a library would (e.g., `time.perf_counter()` + `statistics` instead of `pytest-benchmark`)
- EPIC-007 (Document Ingestion) and EPIC-008 (Agentic AI) will require new dependencies — gated by future DEC-012

**Neutral:**
- The approval gate is in `Lead2Dev.md`, making it visible and auditable
