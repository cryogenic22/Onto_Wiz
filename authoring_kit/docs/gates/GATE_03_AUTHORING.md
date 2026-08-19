# Gate 3 — governed authoring

Status: **PASS**  
Independent decision: adversarial review attempt 7  
Gate 4 authorization: granted

## Delivered

- External-only authoring trust-provider protocol; no production local provider
  or workspace-held private signing material.
- Operation-bound proof-of-possession credentials, signed authority cache, and
  external authority plus authoring-revision high-water.
- Provider-reserved, attested, recoverable, finalized transaction lifecycle
  with finalized-replay rejection.
- Derived, contained journal/stage paths; digest-bound before/after state;
  operation-specific live semantic revalidation before recovery writes.
- Idempotent journal-first finalized cleanup and exact recovery authentication
  that survives credential expiry without permitting ordinary replay.
- Full-document evidence-backed proposals with target-owner confirmation,
  current source/rights/material/quotation checks, and candidate-only guards.
- Canonical session state with workspace/revision/sequence/digest anchoring,
  lag-safe recovery, deletion/replay detection, and exact confirmation session
  transformation.
- Deterministic, schema-valid, bounded, content-addressed, deduplicated gap
  questions, including explicit blocking authority gaps.
- Cross-platform cooperative writer lock: POSIX no-follow relative directory
  operations and Windows handle-relative `NtCreateFile`; a synchronized
  successful directory-swap attack produced zero outside writes/deletions.
- No runtime compile, platform import, activation, release, or approval
  authority.

## Can-fail evidence

- Forged/cross-workspace/stale/wrong-role/wrong-key actor and authority data.
- Source withdrawal, rights, freshness, retention, personal-data, client
  boundary, source-byte, and quote drift.
- Concurrent lost update and confirmation races.
- Crash windows across reserve, journal, apply, provider finalize, cleanup, and
  each cleanup unlink.
- Forged, substituted, replayed, finalized, stale, and partially cleaned
  journals.
- Candidate activation/approval injection, unauthorized confirmation, stale
  target, dangling session delta/questions, session deletion/replay, future
  prior-session state, and legitimate lagging-session recovery.
- Unbounded/malformed/deep compiler inputs, duplicate gaps, missing authority,
  path traversal, symlink/junction/reparse, and synchronized Windows ancestor
  swap.

## Validation at close

- Full authoring suite: 83 passed, 2 pre-existing symlink-capability skips.
- Dedicated final lag/future recovery tests: 2 passed.
- Ruff: clean.
- Strict mypy: clean across 14 source files.
- Compileall: clean.
- Independent attempt-7 spot-check: 2 passed; no P0/P1 or material lower-risk
  finding.

Reviews 1–6 remain in `docs/reviews/` as the can-fail audit trail. Gate 3 closed
only after every reported P0/P1 was remediated and independently re-reviewed.
