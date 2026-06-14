# Architecture Decision Records (ADR)

> **Owner:** Team SENTINEL
> **Created:** SEN-007 (2026-02-01)
> **Source:** `docs/DECISION_LOG.md` (DEC-001 through DEC-011)
> **Template:** Michael Nygard (Title, Date, Status, Context, Decision, Consequences)

---

## Index

| ADR | Title | Status | Date | Source |
|-----|-------|--------|------|--------|
| [ADR-001](ADR-001-delta-model.md) | Delta Model — Everything is a Proposal | SETTLED | 2026-01-31 | DEC-001 |
| [ADR-002](ADR-002-four-team-structure.md) | Four-Team Structure — LENS + CORTEX + ATLAS + SENTINEL | SETTLED | 2026-02-01 | DEC-002 |
| [ADR-003](ADR-003-prs-minimum-85.md) | Quality Gate PRS Minimum 85 | SETTLED | 2026-01-31 | DEC-003 |
| [ADR-004](ADR-004-function-size-max-50.md) | Function Size Max 50 Lines | SETTLED | 2026-01-31 | DEC-004 |
| [ADR-005](ADR-005-in-memory-stores.md) | In-Memory Stores Until Phase 6 | SETTLED | 2026-01-31 | DEC-005 |
| [ADR-006](ADR-006-no-new-dependencies.md) | No New Dependencies Without Lead Approval | SETTLED | 2026-01-31 | DEC-006 |
| [ADR-007](ADR-007-architecture-boundaries.md) | Architecture Boundaries Enforced by Cathedral Keeper | SETTLED | 2026-01-31 | DEC-007 |
| [ADR-008](ADR-008-mini-spec-before-impl.md) | Mini-Spec Required Before Implementation | SETTLED | 2026-01-31 | DEC-008 |
| [ADR-009](ADR-009-agile-board.md) | Agile Board for Cross-Team Visibility | SETTLED | 2026-01-31 | DEC-009 |
| [ADR-010](ADR-010-estimation-scale.md) | Ticket Estimation Scale (S/M/L/XL) | SETTLED | 2026-01-31 | DEC-010 |
| [ADR-011](ADR-011-sentinel-reviews-read-only.md) | SENTINEL Reviews Are Read-Only | SETTLED | 2026-02-01 | DEC-011 |

---

## Status Legend

| Status | Meaning |
|--------|---------|
| SETTLED | Decision is final. Do not propose alternatives without Lead approval. |
| PROPOSED | Under discussion. Not yet binding. |
| SUPERSEDED | Replaced by a newer ADR. |
| DEPRECATED | No longer applicable. |

All 11 current ADRs are **SETTLED**.

---

## How to Add a New ADR

1. Only the Tech Lead or Human can create new decisions (add to `DECISION_LOG.md` first)
2. SENTINEL formalizes decisions into ADR format during review sprints
3. File naming: `ADR-NNN-short-title.md`
4. Follow the template: Title, Date, Status, Deciders, Source, Context, Decision, Consequences

---

## Categories

**Governance:** ADR-001 (Delta Model), ADR-008 (Mini-Spec), ADR-011 (Read-Only Reviews)
**Quality:** ADR-003 (PRS 85), ADR-004 (50-Line Max), ADR-006 (No New Deps)
**Architecture:** ADR-005 (In-Memory), ADR-007 (Boundaries)
**Process:** ADR-002 (4 Teams), ADR-009 (Agile Board), ADR-010 (Estimation)
