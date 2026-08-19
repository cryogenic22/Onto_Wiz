# Held-out and package threat model

Protected assets include held-out scenarios, oracles, hidden rubric predicates,
failure mappings, arm mappings, full traces, private receipts, signing keys, and
provider credentials.

Assume the drafting agent can read and write its repository and authoring
workspace, and that source text may be prompt-injected. Defend against
filesystem/environment/tool/network exfiltration, adaptive overfitting, log and
error leakage, archive traversal and bombs, case-fold collisions, reparse
points, suite/run-plan/candidate drift, evaluator downgrade, and scorer
de-blinding.

The boundary is:

1. Draft zone: this repository, workspaces, `.owworkspace`, `.owpack`.
2. Submission broker: accepts only verified digests and an approved run plan.
3. Evaluator coordinator: external or a distinct service identity with
   evaluator-only, read-only vault access.
4. Ephemeral adapter worker: receives one scenario but never its oracle, hidden
   rubric, critical predicates, arm map, vault mount, or evaluator secrets.
5. Private scorer and append-only receipt store.

If the custodian process cannot prove the drafting principal is denied list/read
access, evaluation refuses with `E_VAULT_ISOLATION_UNPROVEN`.

