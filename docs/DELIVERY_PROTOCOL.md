# Delivery Protocol — how Onto_Wiz work gets built

This is the loop every epic/phase runs through. It is borrowed from the
discipline already in this repo (Cathedral Keeper, Quality Gate, Slop Checker,
the ADRs) and the market_zero harness pattern, and it is non-negotiable: we do
not lower the Definition of Done to move faster.

## The loop (per epic / phase)

```
1. MINI-SPEC      (ADR-008)  short written spec: goal, scope, success criteria,
                             reversibility tag. No code before the spec.
2. REUSE-FIRST    (slop)     search existing code (SpecOmagic / market_zero /
                             src / packages) — port and reuse, never re-create.
3. TDD: RED                  write failing tests that encode the success criteria.
4. TDD: GREEN                implement the minimum to pass; functions <= 50 lines
                             (ADR-004); respect the tier boundary (ADR-012).
5. GATES                     `bash scripts/verify-audit.sh` is the gate of record.
                             Its six OWNED (blocking) gates:
                               - pytest over packages/ + coverage >= 85%
                               - ruff on our five packages
                               - mypy on Tier A source
                               - A -> B boundary clean (tools/check_boundaries.py)
                               - Cathedral Keeper: zero NEW findings on packages/
                                 (named INHERITED_DEBT baseline excluded)
                               - legacy src/ suite green
                             ADVISORY, not blocking (demoted by F0.1 = R3):
                               - Quality Gate PRS >= 85   (continue-on-error in CI)
                               - Slop Checker             (continue-on-error in CI)
                             Frontend units additionally run the ADR-017 FE gate
                             (vitest >=85% + tsc + eslint + next build); it is run
                             and recorded beside verify-audit, not folded into it.
6. PROOF                     an executable artifact (test/smoke) demonstrating it
                             works, plus honest status: done / stubbed / deferred.
7. STOP AT PHASE BOUNDARY    report; await review. Do not run ahead.
```

**Builder never self-verifies (R14).** The builder submits one immutable review SHA
on `build/<unit-id>` plus the six-part evidence bundle (§14 of
`docs/specs/DOMAIN_PACK_PLATFORM_BUILD_INSTRUCTION_SET_2026-07.md`); a read-only REV
reviews that SHA; **INT alone** records `VERIFIED`. "Written" / "committed" / "gates
green" are all still short of done.

## Definition of Done (held firm)

A unit of work is DONE only when **all** of:
- [ ] Tests written first, now green; coverage on new code >= 85%.
- [ ] `ruff check` and `mypy` clean on the changed packages.
- [ ] `tools/check_boundaries.py` green (Tier A imports no Tier B).
- [ ] Cathedral Keeper reports zero NEW findings on `packages/` (baseline excluded).
- [ ] No reused-logic re-implemented (slop check); provenance noted when ported.
- [ ] An executable proof exists and is referenced in the status report.
- [ ] Status reported faithfully — stubs and deferrals named, not hidden.
- [ ] Evidence recorded in `docs/PROJECT_STATUS.md`, and the unit submitted as an
      immutable review SHA — **the builder does not set `VERIFIED`.**

If any box is unchecked, the task stays `in_progress`. We never mark done on a
partial implementation or a failing gate.

## Commands

```
make test-packages     # pytest over packages/ with coverage on our new code
make boundaries        # A -> B tier boundary check
make lint              # ruff + mypy (src + packages)
make ck                # Cathedral Keeper full analysis
make quality           # Quality Gate (PRS >= 85) — ADVISORY since F0.1
```

Pre-commit runs the fast subset (ruff, boundary, pytest-fast, slop, quality
gate, Cathedral Keeper diff) on every commit. `slop` and `quality` are advisory
there too — they inform, they do not block.

## Tiers (ADR-012) — the rule that protects the IP

```
Tier A (ships): ontowiz-spec, ontowiz-ctx, ontowiz-runtime, ontowiz-serve
Tier B (secret): ontowiz-core, ontowiz-factory
Rule: Tier A may import Tier A only. Tier A -> Tier B is a build failure.
```

## Phase map

| Phase | Epic | Gate it must clear |
|---|---|---|
| F0  | scaffold + vendor CTX + contracts seam | DONE — smoke green |
| 0   | harden harness for packages/ | this document + the gates wired |
| F1  | unify artifact model + re-home core + Delta bridge | TDD + gates |
| F2  | pack compiler + registry + runtime store | TDD + gates |
| F3  | headless serve + first consumer agent-lift benchmark | TDD + gates |
| F4+ | port the five loops (mining→steward→forge→eval→feedback) | TDD + gates |

UX phases (UX-1..4) pair with F1..F4 per the UX spec.

**This phase map is historical (F0–F4 shipped 2026-06).** The live plan is the
Domain Pack Platform build: `docs/specs/DELIVERY_LOOPS_BACKLOG_2026-07.md` v2.0 is
the **card inventory of record** (Gates G0–G4, Loops 0–8, F0.x/E-x/D-x cards);
`docs/specs/VDP_GAP_CLOSURE_LOOPS_2026-07.md` sequences it against the verified gap
register. New unit IDs are minted **only** after reconciling against that backlog
plus the B0–B12 / GM0–GM7 / Slice A–J instruction sets — no renumbering, no parallel
paths. Per-unit truth lives in `docs/PROJECT_STATUS.md`.
