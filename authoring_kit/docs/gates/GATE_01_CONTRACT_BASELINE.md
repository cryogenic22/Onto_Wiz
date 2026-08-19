# Gate 1 — contract and provenance baseline

Status: **PASS**

Closed on: 2026-07-25

## Scope

- Revision 2 source specification and associated review notes locked by SHA-256.
- Source repository access declared read-only for phase one.
- Existing `ontowiz-spec` v0.1 models vendored byte-for-byte under
  `ontowiz_spec.pinned_v0_1`.
- Additive `vNext-min` candidate, workspace, evidence, source, evaluation, and
  archive contracts implemented and exported as JSON Schema.
- Candidate lifecycle limited to `draft|review`; approval and activation are
  structurally unavailable.
- `.owworkspace` and `.owpack` security fields and portable path constraints
  fixed before implementation slices.

## Automated evidence

- `python -m pytest tests/contract -q` — 48 passed.
- `python -m ruff check src tests/contract tools` — passed.
- Strict `mypy` over authored contract/provenance code — passed.
- `python tools/verify_vendor_lock.py` — `vendor-lock-ok`.
- Source-origin verifier — `origin-lock-ok`.

## Adversarial findings resolved

1. JSON Schema `null` bypasses for source withdrawal, personal-data consent,
   and quoted evidence were closed and independently tested.
2. Generic payload compatibility was replaced with a canonical, digested,
   exact pinned-artifact snapshot validated through the original typed model.
3. Archive paths now reject traversal, absolute paths, Windows device names,
   trailing-dot/space components, non-ASCII/non-NFC ambiguity, and unsafe
   separators.
4. High/critical-risk `decision_heuristic` records now require owned
   exceptions.
5. All 15 duplicated legacy base fields are compared after JSON
   normalization; per-field tamper tests prevent conflicting authorities.

## Independent verdicts

- Contract reviewer: **PASS**.
- Portability/adapter reviewer: **PASS**.

Gate 2 was not opened until both verdicts were received.
