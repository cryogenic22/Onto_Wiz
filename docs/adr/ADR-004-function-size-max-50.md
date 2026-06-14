# ADR-004: Function Size Max 50 Lines

**Date:** 2026-01-31
**Status:** SETTLED
**Deciders:** Tech Lead
**Source:** DEC-004

## Context

Long functions have high cyclomatic complexity, are hard to test in isolation, and attract "slop" (dead code, commented-out blocks, catch-all error handling). Six existing functions exceed 50 lines — these are technical debt, not precedent.

## Decision

No function may exceed 50 lines. This is enforced by the quality gate and slop checker.

## Consequences

**Positive:**
- Forces decomposition into small, testable units
- Reduces cyclomatic complexity (fewer branches per function)
- Makes code reviews faster (each function fits on one screen)
- Slop checker (SEN-002) enforces this automatically

**Negative:**
- Some naturally sequential operations (e.g., building a complex response) require decomposition that may feel forced
- Helper function proliferation if not managed carefully

**Neutral:**
- 50 lines is generous for most operations; the typical well-written function is 15-30 lines
- Benchmark scripts and test fixtures sometimes need creative decomposition to comply
