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
5. GATES                     all must pass before "done":
                               - pytest green + coverage >= 85% on new code
                               - ruff + mypy clean
                               - A -> B boundary clean (tools/check_boundaries.py)
                               - Cathedral Keeper clean (no high findings)
                               - Quality Gate PRS >= 85
6. PROOF                     an executable artifact (test/smoke) demonstrating it
                             works, plus honest status: done / stubbed / deferred.
7. STOP AT PHASE BOUNDARY    report; await review. Do not run ahead.
```

## Definition of Done (held firm)

A unit of work is DONE only when **all** of:
- [ ] Tests written first, now green; coverage on new code >= 85%.
- [ ] `ruff check` and `mypy` clean on the changed packages.
- [ ] `tools/check_boundaries.py` green (Tier A imports no Tier B).
- [ ] Cathedral Keeper reports no high-severity findings on the change.
- [ ] No reused-logic re-implemented (slop check); provenance noted when ported.
- [ ] An executable proof exists and is referenced in the status report.
- [ ] Status reported faithfully — stubs and deferrals named, not hidden.

If any box is unchecked, the task stays `in_progress`. We never mark done on a
partial implementation or a failing gate.

## Commands

```
make test-packages     # pytest over packages/ with coverage on our new code
make boundaries        # A -> B tier boundary check
make lint              # ruff + mypy (src + packages)
make ck                # Cathedral Keeper full analysis
make quality           # Quality Gate (PRS >= 85)
```

Pre-commit runs the fast subset (ruff, boundary, pytest-fast, slop, quality
gate, Cathedral Keeper diff) on every commit.

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
