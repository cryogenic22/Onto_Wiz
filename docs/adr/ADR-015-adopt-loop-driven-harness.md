# ADR-015: Adopt the loop-driven build + anti-overstatement harness

**Date:** 2026-06-10
**Status:** SETTLED
**Deciders:** Founder + Tech Lead
**Reversibility:** two-way door (process; can be relaxed)
**Source:** Content_medical_hub ADR-0001 (`docs/adr/0001-adopt-loop-driven-harness.md`),
the `loop-driven-dev` skill discipline. Adapted to Onto_Wiz's existing gates.

## Context

We are building a multi-package factory across consolidated codebases. The
failure mode this guards against (per the source ADR): "committed" treated as
"done", status drifting in chat/memory, and silent linter-reverts unwiring work.
Onto_Wiz already has strong automated gates (Cathedral Keeper, Quality Gate,
Slop Checker, the A↛B boundary, coverage) but, until now, status lived in chat
and memory — the exact anti-pattern the source ADR forbids.

## Decision

Adopt the source ADR's **discipline** (not the autonomous daemon/scheduler):

1. **Gates in `CLAUDE.md`** — anti-bloat (reuse-first / slop), reproduce-the-failure
   (TDD red before green), completion (DoD below).
2. **Definition of Done** — a task is DONE only when `scripts/verify-audit.sh`
   passes and the evidence is recorded. "Written" / "committed" ≠ "done".
3. **Single source of truth** — `docs/PROJECT_STATUS.md`. Status does NOT live in
   chat or memory; memory may *point* to it but not hold it.
4. **The loop** — spec (mini-spec, ADR-008) → TDD → build → gates → fix → verify
   → record. One unit per loop. Tracked via the Task tool + `PROJECT_STATUS.md`.
   Detailed in `docs/DELIVERY_PROTOCOL.md`.
5. **Persistence check** — after edits, confirm they persisted (the harness emits
   file-modification notices; re-read on doubt). Guards the linter-revert mode.

**Mapping to Onto_Wiz's existing gates** (we reuse, not reinvent):

| Source ADR mechanism | Onto_Wiz realization |
|---|---|
| anti-bloat 5-test | Slop Checker + reuse-first (port from SpecOmagic/market_zero/src) |
| reproduce-the-failure | TDD red-first (pytest) |
| `verify-audit.sh` | `scripts/verify-audit.sh` — 6 owned gates |
| `PROJECT_STATUS.md` | `docs/PROJECT_STATUS.md` |
| quality gate | Cathedral Keeper + Quality Gate (PRS ≥ 85) + coverage ≥ 85% on new code |

We **skip** (as the source ADR did): the scheduler, the feedback daemon,
`promote.sh`, CODEOWNERS — they are parallel infrastructure for a hands-on loop.

## Consequences

- Positive: claims become falsifiable (one command); status has one home; drift
  and app-breakage are caught by `verify-audit.sh`.
- Negative: each loop is slower (verification overhead) — accepted as the cost of
  trust, per the source ADR.

## Verification

`docs/PROJECT_STATUS.md` rows flip to ✅ VERIFIED only with evidence; the first
`scripts/verify-audit.sh` run (2026-06-10) confirmed all 6 owned gates fire
(50 package + 308 legacy tests green, 0 CK findings on `packages/`).
