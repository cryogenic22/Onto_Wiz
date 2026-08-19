# Gate 3 adversarial review — attempt 3

Status: **BLOCKED**  
Automated evidence at review: 45 focused tests passed; 71 authoring tests passed
with two platform skips; lint and production strict typing passed.

The reviewer confirmed that attempt-two journal paths, stage bindings, generic
mutation recovery, session anchoring, cooperative target CAS, blocking
authority questions, and bounded iterative JSON traversal were materially
fixed. Three trust-boundary findings remained:

1. **P1 — local trust and impersonable actor snapshots.** The public API could
   reconstruct a capability for a caller-selected principal. The public key and
   authority high-water state lived only in the writable workspace, permitting
   anchor replacement or rollback to an older valid signed authority.
2. **P1 — unauthenticated recovery intent.** Journals were path-safe and
   digest-consistent but not externally signed. Recovery validated staged models
   without replaying every operation-specific transition, so a forged
   self-consistent journal could resurrect a withdrawn source or roll authority
   backward.
3. **P1 — pre-validation lock write.** The lock file was created before the
   workspace scanner rejected a replaced `locks` junction/reparse point,
   permitting creation and deletion outside the workspace.

No runtime import, activation, release, or platform-approval authority was
found.

Required disposition: make a trusted host/adapter provider—not a workspace
file—the source of the authority key, monotonic high-water state, actor
authentication/proof of possession, and journal authentication; re-run
operation-specific transition invariants during recovery; acquire the lock
through a verified no-follow directory handle before any write. Gate 4 remains
unauthorized.
