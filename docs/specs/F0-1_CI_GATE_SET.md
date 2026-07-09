# Mini-spec — F0.1: CI gate set = R3 exactly

**Epic:** F0 (Foundry build, Loop 0) · **Rule anchors:** R3 (the gate set), R2 (unit loop)
**Provenance:** `docs/specs/BUILD_INSTRUCTION_SET_2026-07.md` §F0.1 + §R3;
`docs/specs/DELIVERY_LOOPS_BACKLOG_2026-07.md`.

## Problem

The CI blocking path does not yet equal the R3 gate set:

- **Frontend Vitest is not wired into CI at all.** `.github/workflows/ci.yml`
  `frontend-build` runs `npm run build` + `npm run lint` only. The ADR-017 Vitest
  suite (25 tests, ≥85% catalog coverage) is run/recorded beside `verify-audit`,
  never as a blocking CI job.
- **quality-gate is still blocking.** `ci.yml` `python-checks` runs
  `python quality-gate/quality_gate.py --root .` with no `continue-on-error`.
  R3 removes quality-gate from the blocking path (advisory only).
- **slop_checker** is already advisory (`continue-on-error: true`) — confirm + comment.

## Success criteria (what "done" means)

1. `ci.yml` runs the **frontend Vitest suite as a blocking step** — `npm run test:cov`
   (enforces the ADR-017 ≥85% catalog thresholds), no `continue-on-error`.
2. The **Quality Gate** step in `python-checks` is **advisory** (`continue-on-error: true`).
3. The **Slop Checker** step remains **advisory** (`continue-on-error: true`).
4. A **governance test** (`tests/test_ci_gate_set.py`) parses `ci.yml` and asserts 1–3,
   so the gate set is machine-checked, not eyeballed. It fails before the edit (TDD red)
   and passes after (green).
5. `bash scripts/verify-audit.sh` → PASS (the new test runs inside gate 6, `pytest tests/`).

## Out of scope (flagged, not smuggled in)

- **`.env` history purge — no-op.** Verified `.env` was **never committed** (empty
  exact-path `git log`; only `.env.example` blob exists; `.env` is git-ignored,
  working-tree only). A destructive history rewrite would be gratuitous → **skipped**,
  verification recorded as evidence.
- **ANTHROPIC_API_KEY rotation — user's Anthropic-console action.** Never git-leaked
  (see above); cannot be done from the repo.
- **ctx-core (`ontowiz-ctx`) under the ≥85% coverage gate.** R3 says "no exemptions,"
  but `ontowiz-ctx` has substantial source and only a smoke test; verify-audit's
  coverage gate omits it today. Closing this is a **separate unit** (writing ctx tests),
  not part of F0.1. Tracked as an R3 follow-up.

## Approach (reuse-first)

- No new CI job: **add a step** to the existing `frontend-build` job (it already does
  Node 20 setup + `npm ci`) — anti-bloat, don't duplicate the toolchain in a new job.
- Governance test lands in `tests/` (collected by verify-audit gate 6 already) — no
  `verify-audit.sh` change needed. Parses YAML with the already-present `pyyaml`.

## Test plan (TDD red → green)

`tests/test_ci_gate_set.py`:
- `test_frontend_vitest_is_a_blocking_ci_step` — a step invokes vitest/`test:cov`
  in a frontend context and is **not** `continue-on-error`.
- `test_quality_gate_is_advisory` — the Quality Gate step is `continue-on-error: true`.
- `test_slop_checker_is_advisory` — the Slop Checker step is `continue-on-error: true`.

## Evidence to record (Completion gate)

`docs/PROJECT_STATUS.md`: F0.1 row with the three governance assertions green,
`verify-audit` PASS line, and the `.env`/key hygiene verification note.
