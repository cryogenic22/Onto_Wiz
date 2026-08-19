# Gate 4 archive red-team checklist

Status: prepared; Gate 4 implementation is not authorized until Gate 3 passes.

An independent reviewer must block the archive gate unless every item below has
both a positive round-trip test and a negative can-fail test where applicable.

## Deterministic envelope

- Two builds from identical semantic input are byte-for-byte identical.
- Input enumeration order, host path, clock, locale, and permitted text EOL
  variation cannot change the archive or semantic digest.
- ZIP members are stored, sorted, fixed-time, regular mode `0644`, and have no
  comment or extra field.
- The control-file digest covers the exact canonical manifest bytes.
- Declared and actual inventories, byte counts, media types, roles, and SHA-256
  digests agree exactly.

## Hostile input and extraction

- Reject absolute, drive, URI, UNC, traversal, dot, empty, backslash, NUL,
  trailing-dot/space, non-NFC, Windows device-name, duplicate, and case-fold
  colliding paths.
- Reject directories, symlinks, hard links, junctions/reparse-like modes,
  unsupported compression, data descriptors that defeat limits, archive
  comments, unexpected control files, and undeclared payloads.
- Enforce the declared entry, per-entry, and total-uncompressed ceilings before
  extraction and while streaming.
- Extract only to a new staging directory without link following. Existing
  destinations are idempotent only for the same verified semantic digest;
  conflicting destinations are never overwritten.
- A failed import leaves no partial destination.

## `.owworkspace`

- Preserve all portable canonical authoring state needed for crash/resume.
- Exclude build, reports, dist, VCS, adapter state, secrets, and any held-out or
  evaluator-private material.
- Referenced profile omits source bytes while retaining governed records,
  checksums, and explicit omission reasons.
- Embedded profile includes a source only when the current source record,
  permitted-use, confidentiality, quotation, redistribution, transfer,
  retention, client-boundary, and personal-data rules all permit the transfer.
  Any uncertainty refuses the build.
- Import revalidates source rights and authoring cross-references.

## Candidate-only `.owpack`

- Permit only the documented schema, pack, public evaluation, public provenance,
  and redacted public-receipt roots.
- Reject draft-control state, proposals, sessions, locks, raw/extracted sources,
  runtime context, explorer output, protected cases/oracles/rubrics, evaluator
  mappings, private receipts, secrets, and evaluation summaries.
- Strictly validate every pack document and require candidate lifecycle,
  candidate package kind, null approvals, and false
  production/release/protected-evaluation flags.
- Packaging does not compile, import, activate, approve, or mutate the source
  workspace. Evaluation receipts bind the unchanged package digest externally.

## Gate evidence

The reviewer must report PASS or concrete P0/P1 findings with file and line
evidence. A passing unit suite alone is not sufficient. Gate 5 adapter work may
begin only after deterministic rebuilds, hostile archives, rights failures,
candidate-state mutations, and import conflicts have all been exercised.
