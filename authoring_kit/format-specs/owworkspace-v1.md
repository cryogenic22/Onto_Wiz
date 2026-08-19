# `.owworkspace` version 1

Format name: `ontowiz-authoring-workspace`; schema target:
`ontowiz-spec/vNext-min`; archive compression: stored.

Required payload roots are `workspace.yaml`, `locks/`, `sources/`,
`authoring/`, and `pack/`. `build/`, `reports/`, `dist/`, VCS data, adapter
state, vault/held-out material, secrets, local trust-provider state, and
absolute paths are forbidden.

Archive creation holds the Gate 3 identity-safe authoring lock through final
publication, uses identity-pinned no-follow reads, refuses pending/divergent
provider state, and proves the same local/provider revision before and after
publication. Only an exact initialized revision-zero baseline may be archived
without an external trust provider.

Source profile `referenced` preserves register/checksum/omission governance and
omits governed `sources/inbox` bytes. Profile `embedded` preserves governed
bytes exactly and requires explicit non-expired retention, permitted use,
confidentiality, redistribution permission, and an exact source/target client
boundary match. The profile, effective date, and target boundary are bound into
the archive semantic identity.

Import never trusts the archive to authorize itself. The caller supplies the
trusted effective date and destination client boundary. Import checks those
values before staging, immediately before extracting embedded bytes, and after
portable-state validation, including idempotent and racing-destination paths.

Every dynamic proposal, decision, evidence record, candidate claim, session,
delta, question, pack artifact, evaluation, source/material binding, revision,
and cross-reference is validated offline before publish. Derived reports,
context model, and explorer output are regenerated and validated in staging;
they are never accepted as portable authority from the archive.

Historical completed session bundles retain their original revision and sequence.
Their records and receipt inventories bind source-record/checksum, evidence-item,
candidate-artifact, proposal, and pack-manifest digests, so a later same-ID
revision cannot reinterpret earlier history. Only the live-current checkpoint
must match current bytes. These unkeyed bindings prove deterministic content
identity and internal integrity, not origin authenticity; an externally pinned
signed checkpoint is a separate future extension.
