# Authoring authority boundary

The authoring kernel verifies authority; it does not authenticate people or
hold signing keys.

- An external identity/approval system owns the Ed25519 private key and
  authenticates principals before issuing statements or capabilities.
- The workspace stores only a public trust anchor, signed statements, and
  digest commitments. Private keys, signing callbacks, passwords, tokens, and
  OS credential material are forbidden from workspaces and portable archives.
- The trust-anchor digest must be pinned by the launching adapter or other
  protected configuration outside the writable workspace. A workspace-provided
  key is not self-authenticating.
- Bootstrap is one-time. Rotation or grant changes require a signed
  administrator statement, an exact previous authority revision/digest, and a
  monotonic next revision.
- Actor capabilities bind the workspace, principal, roles, client boundary,
  authority revision/digest, validity interval, unique capability identifier,
  and signer key ID. Confirmation verifies the signature, trust anchor,
  workspace, time, current authority, principal grant, owner role, and client
  boundary.
- A capability copied to another workspace, replayed after authority rotation,
  modified, expired, or signed by another key fails closed.

The bundled Codex and Claude adapters must obtain signed capability material
from their configured external authority provider. They must not expose
signing, grant mutation, trust-anchor replacement, or administrator bootstrap as
ordinary drafting commands.

Tests may use deterministic synthetic private keys held only in test memory.
Those keys and resulting test fixtures are not production credentials and must
never be copied into examples, `.owworkspace`, or `.owpack` artifacts.
