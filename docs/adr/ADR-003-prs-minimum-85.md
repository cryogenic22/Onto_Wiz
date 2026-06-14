# ADR-003: Quality Gate PRS Minimum 85

**Date:** 2026-01-31
**Status:** SETTLED
**Deciders:** Tech Lead
**Source:** DEC-003

## Context

Code quality varies when multiple autonomous agents contribute code. A measurable, enforceable quality threshold prevents gradual degradation. The Production Readiness Score (PRS) combines function size, complexity, import hygiene, and code organization into a single 0-100 metric.

At the time of this decision, 2 existing files scored below 85 (`delta_generator.py`, `semantic_store.py`). These are acknowledged technical debt, not precedent.

## Decision

All new code must score PRS >= 85. Existing debt is addressed incrementally.

PRS 85 means at most 1 error and 7 warnings per file. This is strict enough to catch real problems (overly complex functions, dead imports, commented-out code) without blocking velocity on minor style issues.

## Consequences

**Positive:**
- Objective, automated quality enforcement
- Prevents "broken windows" — new code cannot introduce quality debt
- PRS is measurable in CI (SEN-001 quality gate)

**Negative:**
- Existing files below 85 create a "legacy exception" that could confuse new contributors
- Agents occasionally need to refactor to meet the threshold, adding implementation time

**Neutral:**
- PRS is enforced by `quality_gate.py` in CI and pre-commit hooks
