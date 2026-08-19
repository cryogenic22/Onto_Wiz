# `.owpack` candidate version 1

Format name: `ontowiz-candidate-pack`; schema target:
`ontowiz-spec/vNext-min`; archive compression: stored.

Candidate contents use an exact path-to-schema allowlist. Unknown structured
documents and untyped text are refused. Artifact identifiers/digests and public
evaluation identifiers/suites are reconciled exactly with `pack/pack.yaml`.
Public provenance or receipt paths are excluded until a typed, redacted public
contract exists.

Only public dev/regression/challenge evaluation contracts may appear.
Dev/regression suite declarations are a draft allowlist: zero cases remain an
explicit candidate-completeness gap and never establish validation success,
approval, release eligibility, or production fitness.

Every lifecycle stays at `draft` or `review`, approvals and reviewers remain
null/empty, lifecycle history may not reach active/released states, and all
production/releasable/protected flags are false. The package is never a runtime
compilation.

The format excludes raw sources, protected cases/oracles/rubrics/mappings,
private locks/receipts, runtime CTX, explorer output, source registers,
evaluation summaries, and any unmanifested physical ZIP bytes. Evaluation
produces an external immutable receipt over the unchanged package digest.

