# Gate 3 adversarial review — attempt 2

Status: **BLOCKED**  
Automated evidence at review: 25 focused tests passed; full contract/authoring
suite passed with two platform skips; authoring lint and strict typing passed.

The first review's six findings were materially addressed, but the reviewer
identified the following remaining bypasses:

1. **P0 — recovery path injection.** A journal-controlled proposal path could
   escape the workspace and be written during automatic recovery. Journal stage
   paths and bytes were not all independently digest-bound.
2. **P1 — self-asserted authority.** Local callers could reconfigure grants or
   request another principal's capability. Unkeyed record digests did not
   establish an authentication boundary.
3. **P1 — partial non-confirmation mutations.** Source, evidence, proposal,
   authority, and session payload writes could complete before their revision
   update, leaving crash-incoherent state.
4. **P1 — session replay/reset.** Older still-valid session state and deletion
   were not anchored to the revision state, and confirmation did not always
   create/advance a canonical session.
5. **P1 — final target check/use window.** A writer could change the target
   after the last digest read but before replacement.
6. **P1 — missing authority gap.** Question compilation aborted if no preferred
   role existed instead of emitting deterministic resumable gap state.

Lower risk: deeply nested JSON measurement was recursive and could raise an
untranslated recursion error before the explicit node bound.

No runtime import, activation, release, or platform-approval authority was
found.

Required disposition: derive and contain all journal paths; bind every recovery
stage and invariant; use an external signed authority/capability boundary;
journal every payload-plus-revision mutation; anchor session sequence/digest;
close the in-kit target CAS window; emit typed authority gaps; replace recursive
measurement. Gate 4 remains unauthorized.
