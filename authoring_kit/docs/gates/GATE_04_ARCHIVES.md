# Gate 4 — portable archives

Status: **PASS**  
Independent decision: adversarial review attempt 5  
Gate 5 authorization: granted

## Delivered

- Deterministic `.owworkspace` and candidate-only `.owpack` formats.
- Byte-complete canonical `ZIP_STORED` layout, exact manifest/inventory,
  semantic digest, fixed metadata, resource ceilings, portable paths, and
  component-prefix/case-fold collision refusal.
- Referenced raw-source omission by default; embedded transfer only with
  explicit non-expired retention, exact client boundary, bound effective date,
  and immediate import-time reauthorization.
- Authoring snapshot under the existing identity-safe Gate 3 lock with exact
  provider/revision convergence and no-follow identity-pinned reads.
- Exact candidate schema/path allowlist, artifact/evaluation digest
  reconciliation, draft/review-only lifecycle, null approvals, and no
  runtime/release/production authority.
- Full portable resume graph: claims, decisions, proposals, named session
  questions/responses/receipts, canonical resume pointers, and distinct
  live-current state.
- Content-bound historical source, evidence, artifact, proposal, and pack
  identity with immutable exact receipt inventories.
- Standalone verification, staged import, semantic regeneration, idempotency,
  conflict refusal, and no partial destination.
- Explicit integrity/authenticity boundary: deterministic unkeyed digests do
  not claim origin authentication.

## Can-fail evidence

- Physical ZIP overlays, metadata disagreement, unsafe/colliding namespaces,
  compressed or resource-excessive members, inventory and semantic drift.
- Unknown/untyped candidate content, private/protected data, active/release
  semantics, artifact/evaluation digest mismatch.
- Transaction/revision/provider drift, manually edited revision-zero controls,
  lock/link/file-swap races, mixed snapshots, source workspace mutation.
- Missing/expired/cross-client rights, stale archive-controlled dates, changed
  governed bytes, forged omission records.
- Missing/duplicate/dangling sessions, questions, responses, proposals, claims,
  decisions, receipts, and resume anchors.
- Non-monotonic history, rewritten earlier receipts, mismatched provenance
  edges, same-ID later revisions, substituted historical digests, and
  live-current content mismatch.

## Validation at close

- Focused content-binding cases: 13 passed.
- Archive suite: 55 passed.
- Schema/candidate contract suite: 26 passed.
- Ruff: clean.
- Strict mypy: clean across 15 source files.
- Full regression: 190 passed, 2 platform-capability skips.
- Independent attempt-5 checks: archive 55/55, schema/fail-closed 14/14, full
  ordinary suite green with 2 skips; no P0/P1.

Attempts 1–4 remain in `docs/reviews/` as the can-fail audit trail.

