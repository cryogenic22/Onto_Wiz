# ADR-008: Mini-Spec Required Before Implementation

**Date:** 2026-01-31
**Status:** SETTLED (sprints without mini-specs will be rejected at review)
**Deciders:** Tech Lead
**Source:** DEC-008

## Context

Autonomous AI agents that start coding without a plan produce scope creep and hallucinated abstractions. They add unnecessary features, create parallel implementations of existing functionality, and introduce architectural inconsistencies.

## Decision

Every sprint ticket requires a written mini-spec in `docs/Dev2Lead.md` before any implementation code is written. The mini-spec must include:
- Objective (what and why)
- Files to be modified
- Complexity assessment
- What is explicitly out of scope

The status progression is: `IN_PROGRESS:SPEC` -> `IN_PROGRESS:IMPL` -> `DONE`.

## Consequences

**Positive:**
- Forces agents to read existing code before writing new code
- Identifies reuse opportunities (existing functions, stores, patterns)
- Declares slop risks upfront
- Prevents 80% of rework by catching misunderstandings before implementation
- Creates a reviewable record of design decisions per ticket

**Negative:**
- Adds overhead for trivial tickets (S-sized, 1-2 function changes)
- Mini-spec quality varies — bad specs don't prevent bad implementations

**Neutral:**
- The spec is written in `Dev2Lead.md`, making it visible to the Tech Lead for review before implementation proceeds
