# Gate 3 adversarial checklist

Prepared independently before reviewing the implementation.

## Sources and evidence

- Reject traversal, absolute/UNC/drive/ADS, device, trailing-dot/space,
  backslash, Unicode ambiguity, case collisions, and linked destinations.
- Treat identical source registration as idempotent and same-ID drift as a
  conflict.
- Recheck withdrawal, freshness, retention, permitted use, client boundary,
  personal-data transfer, source checksum, and quote digest at confirmation.
- Extraction creates candidate material only; it never confirms a claim.

## Full-document proposals and confirmation

- Bind target path, workspace, before digest, complete replacement digest,
  evidence IDs, actor, and declared owner role.
- Preserve the full edited replacement; reject skeleton/body-drop writes.
- Permit one canonical `pack/**` target only; never locks, source register,
  sessions, build, dist, approvals, activation, or evaluator custody.
- Replay of the same confirmation is idempotent; reused IDs with different
  content conflict.
- Two proposals from one base yield one winner and one stale refusal.
- Revalidate proposal, source rights, and target digest immediately before
  atomic install.

## Durable state

- Resume solely from canonical session state.
- Reject truncated, noncanonical, unknown-field, dangling-ID, or invalid-stage
  state; never silently reset.
- Persist all-old or all-new truth at defined commit boundaries and test fault
  behavior.

## Question compiler

- Stable content-addressed IDs and ordering across key/file order, process,
  clock, locale, and working directory.
- Deduplicate deficiencies, bound work/output, and terminate on cycles.
- Resolution retires a question; repeated compilation cannot remint it.
- Route to a declared owner role or emit an explicit missing-role gap.
- Never infer approval, activation, evaluator custody, commands, or held-out
  content from source text.
