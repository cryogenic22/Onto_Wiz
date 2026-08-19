# Evaluation firebreak decision

Status: architecture accepted; real held-out execution is **not authorized**.

The reviewed experiment pre-registration is a draft with unresolved owners,
thresholds, models, run counts, scoring, and adjudication decisions. Therefore
every real freeze or run must refuse with `E_PREREG_UNAPPROVED`. Phase one may
implement contracts, synthetic public fixtures, isolation checks, and refusal
behavior only.

## Trust boundaries

1. The draft zone contains this repository, authoring workspaces, portable
   `.owworkspace` files, and candidate-only `.owpack` files. It contains no
   protected prompt, oracle, hidden rubric, arm mapping, evaluator secret, or
   private receipt.
2. A submission broker accepts a verified candidate digest and approved,
   signed run-plan reference. It never returns protected cases.
3. An evaluator coordinator runs under a distinct principal or in an external
   private runner with read-only vault access.
4. An ephemeral adapter worker receives one scenario envelope and has no vault
   mount, evaluator secret, oracle, hidden predicate, or arm mapping.
5. A private scorer loads the oracle only after the worker returns. Full
   receipts remain in protected append-only storage; a publisher emits only a
   signed redacted attestation.

A folder outside the repository but readable by the same Windows principal is
not a firebreak. If the draft principal's inability to list and read the vault
cannot be proved, execution refuses with `E_VAULT_ISOLATION_UNPROVEN`.

## Required refusal codes

- `E_PREREG_UNAPPROVED`
- `E_VAULT_ISOLATION_UNPROVEN`
- `E_LOCK_SIGNATURE_INVALID`
- `E_SUITE_DRIFT`
- `E_RUNPLAN_DRIFT`
- `E_CANDIDATE_DRIFT`
- `E_ADAPTER_ISOLATION`
- `E_RUN_INCOMPLETE`
- `E_BLINDING_COMPROMISED`

Public errors must not disclose protected paths, case identifiers, oracle
content, rubric predicates, or expected hashes.

## Freeze and receipt invariants

- A suite lock binds an approved pre-registration digest, exact canonical
  inventory, suite digest, version, signer key ID, and signature.
- A suite version is create-once: the same digest is idempotent and a changed
  digest is a fatal conflict.
- Signature, exact bytes, inventory, ACL policy, run plan, candidate digest,
  and adapter build are verified before execution and again before receipt
  finalization.
- Drift or invalid infrastructure produces no score receipt.
- A completed quality failure does receive an immutable failed receipt.
- A top-severity critical failure always forces `gate_passed: false`, regardless
  of any mean score.
- Evaluation never changes `.owpack` bytes. Receipts are external and bind the
  unchanged package digest.
- Public receipts contain approved aggregates and digest commitments only;
  scenarios, answers, oracles, private case IDs, hidden rubrics, mappings, raw
  sources, secrets, and protected paths are forbidden.

## Release gate

Real evaluation requires a separately approved and signed pre-registration,
proven vault denial for the draft principal and adapter worker, an independently
reviewed signed evaluator build, and all isolation, drift, blinding,
critical-failure, completeness, immutable-receipt, and redaction tests passing.
The current repository intentionally cannot satisfy the authorization
precondition and must demonstrate refusal instead.
