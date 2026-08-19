# Implementation plan

Status: phase-one contract freeze. The source Onto_Wiz repository is read-only.

## Micro-spec

- Files in scope: this repository only.
- Primary risks: schema fork, accidental runtime/approval behavior, vacuous
  validation, non-deterministic archives, adapter-owned state, and a fake
  held-out boundary under the drafting principal.
- Complexity: high. Portable authoring truth, candidate distribution, and
  protected evaluation are three separate trust envelopes.

## Gated vertical slices

1. **Contract freeze** — source-origin lock, vNext-min models and generated
   schemas, format specs, ownership, threat model, legacy negative fixture.
2. **Archive codecs** — deterministic `.owworkspace` and `.owpack` build,
   verification, safe extraction, and byte-identical round trips.
3. **Brand-analytics candidate** — one variance decision, 5–10 concepts, two
   metrics, one method, challenge rules, and 15–20 public dev/regression cases.
4. **Authoring engine + Codex** — archetype merge, source registration,
   candidate claims, proposals, full replacement deltas, DDRs, adaptive
   questions, resume, checkpoint, validation, explorer, and packaging.
5. **Rights and withdrawal** — transfer policy, evidence invalidation, and
   candidate-package refusal after source withdrawal.
6. **Evaluation firebreak** — approved-preregistration gate, deterministic
   synthetic freeze/verify, worker-envelope separation, drift refusal, and
   immutable/redacted receipts. Real protected data stays outside this repo.
7. **MR + Claude** — observed/inferred separation, verbatim/rights rules,
   withdrawal scenario, and adapter-conformance parity.

Each slice starts with a failing acceptance test. A later slice cannot weaken a
previous gate.

