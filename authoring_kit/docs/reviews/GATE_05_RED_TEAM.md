# Gate 5 adapter and worked-slice red-team checklist

Status: prepared; Gate 5 implementation is not authorized until Gate 4 passes.

## Thin adapter equivalence

- Codex and Claude adapters call the same public authoring/archive kernel. They
  do not reimplement validation, canonicalization, authority, recovery, or
  packaging.
- The same scripted authority context, source/evidence inputs, confirmations,
  and questions produce identical canonical workspace state, semantic digest,
  and byte-identical `.owpack`.
- Provider-specific transcript, cache, prompt, or tool metadata never enters
  canonical state.
- Resume uses verified disk state and external provider high-water, not chat
  memory.

## Authority and evaluation separation

- Adapters receive operation credentials from a configured external
  `AuthoringTrustProvider`; they never hold or persist private signing keys.
- No drafting command can bootstrap/replace trust, mutate provider high-water,
  issue another principal's credential, sign a journal, provision a protected
  vault, freeze held-out cases, read an oracle, score a held-out run, or publish
  a private receipt.
- Credential, token, secret, protected path, and private provider state are
  excluded from logs, workspaces, examples, transcripts, and packages.

## Interaction and question discipline

- Both adapters expose the same finite, deterministic, content-addressed
  question set, authority routing, answer schema, and work/resource bounds.
- Malformed, duplicate, stale, cross-workspace, expired ordinary, or
  intent-mismatched credentials fail closed without changing state.
- User edits are represented as full-document proposals with exact before/after
  digests and evidence; no adapter applies line patches to canonical documents.

## Archetypes and worked slices

- Every archetype maps inputs into the shared normalized context shape and
  declares decisions, metrics, evidence, owners, exceptions, abstention, and
  evaluation needs without adding schema variants.
- The Business Analyst worked slice includes 15–20 synthetic/public
  behavior-based cases covering normal, boundary, exception, conflict, missing,
  stale, abstain, tool failure, and adversarial classes.
- Medical Representative material remains candidate-only and contains no
  patient data, diagnosis/prescribing authority, protected evaluation, or
  production claim.

## Explorer

- Explorer output is generated from validated canonical context, not hand-edited
  truth.
- It is static/self-contained, contains no raw confidential source, credential,
  secret, protected case, oracle, private receipt, or runtime authority.
- Regeneration from identical canonical input is deterministic; stale explorer
  output is excluded from portable archives and packages.

## Gate evidence

The reviewer must run scripted Codex/Claude parity tests, resume tests, malformed
credential/transcript tests, package-digest comparison, protected-content scans,
and the full worked behavior suite. PASS requires no P0/P1 finding and no
adapter-owned canonical or security logic.
