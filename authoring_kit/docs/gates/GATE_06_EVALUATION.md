# Gate 6 — external evaluation firebreak

Status: **PASS** — independent adversarial review found no remaining P0, P1, or P2.

## Contract

This repository contains evaluation boundary contracts and a fail-closed
coordinator. It does **not** contain a vault, held-out scenarios, oracles,
hidden rubrics, arm mappings, provider credentials, signing keys, a local
receipt store, or protected receipts.

Real evaluation remains unauthorized while the reviewed experiment
pre-registration is draft. A production caller must supply external protocol
implementations for:

1. approved pre-registration and signature verification;
2. vault list/read denial proofs for both drafting and worker principals;
3. signed suite freeze/current-lock verification;
4. approved run-plan and blind-token verification;
5. one-at-a-time public scenario projection and private scoring;
6. a fresh worker runtime per envelope with a separately verified isolation
   attestation; and
7. atomic compare-and-append storage for the full private receipt plus public
   attestation.

The coordinator has no raw vault-path input. The adapter worker receives one
`WorkerEnvelope` containing a public scenario, opaque candidate/suite
commitments, an opaque blind-arm token, repetition number, and fixed execution
digests. It receives no oracle, hidden rubric, critical-failure mapping, actual
arm identity, vault credential, or protected path.

## Acceptance evidence

The Gate 6 test suite covers:

- approved paired/repeated execution and redacted public output;
- draft or unresolved pre-registration;
- absent, false, or same-principal vault isolation;
- invalid lock/run-plan verification and suite/run-plan/candidate drift;
- incomplete or duplicate scenario, repetition, trace, score, and receipt
  inventories;
- duplicate or unverified blind-arm tokens;
- unresolved scorer disagreement and invalid adjudication;
- top-severity critical failures forcing a failed immutable receipt;
- append-store exceptions and wrong commitment digests;
- candidate mutation before receipt finalization;
- public scenario protected-field rejection;
- strict revalidation of every external return value and literal verifier result;
- public error redaction, including malformed provider objects;
- fresh runtime identity and opaque-token dispatch order;
- retention of full private output, citation, retrieval, and tool traces;
- atomic append request/commitment matching with no test-store write on mismatch;
  and
- absence of evaluator-custodian commands from Codex and Claude authoring
  adapters.

Infrastructure refusal writes no quality score receipt. A completed quality
run with a critical failure writes an immutable private failed receipt and a
redacted public failed attestation. Evaluation never edits `.owpack`.

## Release hold

This gate does not authorize a real held-out run. Release additionally requires
a separately approved and signed pre-registration, independently administered
external provider implementations, proven list/read denial for the drafting
and worker principals, and a separately reviewed evaluator deployment.
