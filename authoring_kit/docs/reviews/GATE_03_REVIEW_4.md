# Gate 3 adversarial review — attempt 4

Status: **BLOCKED**  
Automated evidence at review: complete contract/authoring behavior passed with
two pre-existing symlink-capability skips; repository lint, strict authoring
typing, source lock, and vendor lock passed.

The reviewer confirmed that the external-only authority provider, authority
high-water cache, proof-of-possession credentials, nonce/expiry/intent checks,
provider-attested journals, operation-specific source/authority recovery, and
pre-existing-junction rejection were materially fixed. Three deeper invariants
remained:

1. **P1 — authentic transaction replay.** The provider attested journal
   identities but had no pending/finalized transaction lifecycle or monotonic
   authoring-revision high-water. A captured valid journal plus a restored local
   before-state could therefore be replayed.
2. **P1 — incomplete proposal/session recovery semantics.** Recovery checked
   model and transition shape but did not re-run every live-path actor,
   authority, boundary, role, evidence, target, candidate-only, document, and
   session-reference invariant before writing.
3. **P1 — Windows ancestor-swap race.** The `locks` directory handle was pinned,
   but `authoring.lock` was created through a full string path rather than
   relative to that handle. A synchronized ancestor swap could redirect creation
   and delete-on-close outside the workspace.

No runtime import, activation, release, or platform-approval authority was
found.

Required disposition: add provider-side reserve/authorize/finalize transaction
CAS and authoring-revision high-water; bind the complete transaction identity
and permit recovery only for the one pending transaction; replay full live-path
proposal/confirmation/session semantics under current authority; use relative
handle lock creation on Windows (for example `NtCreateFile` with
`RootDirectory`) and execute a synchronized swap-race test. Gate 4 remains
unauthorized.
