# CLAUDE.md — operating contract for Onto_Wiz

Build discipline is **loop-driven with an anti-overstatement harness** (ADR-015,
adopted from Content_medical_hub ADR-0001). Read `docs/PROJECT_STATUS.md` for
current truth and `docs/DELIVERY_PROTOCOL.md` for the full loop.

## The loop (one unit at a time)

```
mini-spec (ADR-008) → reuse-first → TDD red → build (green) → gates → fix → verify → record
```
Stop at unit boundaries and report. Do not run ahead.

## Three gates (non-negotiable)

1. **Anti-bloat gate.** Before writing new code, search for what exists and
   reuse it (SpecOmagic / market_zero / `src` / `packages`). The Slop Checker
   enforces this. Porting > re-creating; note provenance when you port.
2. **Reproduce-the-failure gate.** Write the failing test FIRST (TDD red) that
   encodes the success criteria. No implementation before a red test.
3. **Completion gate.** A unit is DONE only when `bash scripts/verify-audit.sh`
   passes AND the evidence is recorded in `docs/PROJECT_STATUS.md`.
   **"Written" / "committed" ≠ "done."** Never mark a Task complete on a partial
   implementation or a red gate.

## Definition of Done

- [ ] Failing test written first, now green; coverage ≥ 85% on new code.
- [ ] `ruff` + `mypy` clean on changed packages.
- [ ] `scripts/verify-audit.sh` passes (all 6 owned gates green).
- [ ] No reused logic re-implemented (Slop Checker); provenance noted on ports.
- [ ] `docs/PROJECT_STATUS.md` updated with the evidence.

## Persistence check

After edits, confirm they persisted (the harness emits file-modification
notices; re-read on doubt). Guards the silent linter-revert failure mode.

## Status lives in one place

`docs/PROJECT_STATUS.md` — NOT in chat or memory. Memory may point to it; it must
not hold the status itself.

## Tier boundary (ADR-012) — protects the IP

```
Tier A (ships):  ontowiz-spec · ontowiz-ctx · ontowiz-runtime · ontowiz-serve
Tier B (secret): ontowiz-core · ontowiz-factory
Rule: Tier A imports Tier A only. Tier A → Tier B is a build failure.
```
Enforced by `tools/check_boundaries.py` (pytest + pre-commit) and ADR-007's
Cathedral Keeper.

## Verify

```bash
bash scripts/verify-audit.sh   # the independent gate that makes "done" falsifiable
```
