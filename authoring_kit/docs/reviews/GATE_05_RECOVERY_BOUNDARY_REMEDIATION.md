# Gate 5 Recovery Boundary Remediation

Status: design approved for implementation; Gate 5 remains closed.

## Finding

An interrupted authoring mutation left a durable transaction journal inside the
workspace. Revision 4 of that journal serialized the complete operation credential
and provider attestation. That made proof material and provider-private identity
readable to any drafting process that could read the workspace.

## Contract decision

Revision 5 transaction journals are public recovery envelopes, not trust stores.
They may contain only:

- the workspace and transaction identifiers;
- the operation and public intent digest;
- public authority revision/digest anchors already represented by signed workspace
  governance;
- before/after semantic content digests, staging digests, and mutation revisions;
- confirmation-specific public content bindings; and
- an opaque digest of the externally reserved transaction.

They must not contain an operation credential, proof signature, actor or principal
identity, credential nonce, trust-key identity, provider identity, provider key
identity, or provider attestation.

The external provider retains the complete `AuthoringTransactionIdentity` for both
the pending transaction and the last finalized transaction. Recovery obtains that
identity out of band, proves that the complete public projection of the local
journal is identical to the provider-reserved transaction, obtains an exact
recovery authorization, and asks the provider to reconstruct the authenticated
actor from provider-held state. The core then rechecks the actor against the
external identity and the current signed authority before applying staged bytes.

Any absent, ambiguous, substituted, stale, or mismatched external identity closes
recovery without changing canonical workspace content.

## Required evidence

1. A kill-point test stops immediately after durable journal creation.
2. The test scans every workspace file before cleanup and finds none of the
   forbidden credential or provider-private values.
3. The same residue recovers successfully through the external provider.
4. Journal-field, staged-byte, external-identity, recovery-actor, and finalized
   cleanup substitutions remain fail closed.
5. Focused, full, lint, type, source-lock, and vendor-lock checks remain green.

