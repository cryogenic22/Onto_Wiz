# ADR-010: Ticket Estimation Scale (S/M/L/XL)

**Date:** 2026-01-31
**Status:** SETTLED
**Deciders:** Tech Lead
**Source:** DEC-010

## Context

AI agents don't estimate time reliably. Absolute time estimates ("this will take 2 hours") are meaningless in an agent context. Relative complexity is more useful for sequencing work and assessing risk.

## Decision

Use relative sizing, not time estimates:

| Size | Scope | Mini-Spec Gate |
|------|-------|----------------|
| S | 1-2 functions | Standard |
| M | 3-5 functions | Standard |
| L | Full feature (multiple files) | Standard |
| XL | Subsystem (architectural change) | HIGH complexity gate |

XL tickets should be broken down before execution. L and above auto-trigger the HIGH complexity mini-spec gate (more detailed spec, explicit risk assessment).

## Consequences

**Positive:**
- Estimation is for prioritization and risk assessment, not scheduling
- XL tickets are flagged for decomposition before they start
- Relative sizing is consistent across agents (unlike time estimates)

**Negative:**
- No time-based forecasting (can't say "Sprint 7 will ship by date X")
- S vs M distinction is sometimes subjective

**Neutral:**
- Sizes are assigned by the Tech Lead in `BOARD.md` and `Lead2Dev.md`
