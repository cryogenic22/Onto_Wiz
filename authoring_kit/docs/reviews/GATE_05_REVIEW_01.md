# Gate 5 independent review — attempt 1

Decision: **FAIL**

Reviewer: independent evaluation/firebreak owner  
Scope: Codex/Claude adapters, explorer, worked examples, packaging integration,
and drafting-workspace isolation.

## Blocking finding

### P1 — recoverable journals persisted external trust material

Journal revision 4 serialized the full `OperationCredential` and provider
attestation beneath `locks/transactions/`. A crash after the durable journal
write therefore left the actor principal, credential nonce and proof signature,
trust/actor-key bindings, provider identity/key/attestation, and complete
credential readable to any process that could read the drafting workspace.

The existing isolation test inspected only the successful post-cleanup state and
could not detect this residue.

Required closure:

1. remove all credential and provider-private material from durable journals;
2. retain tamper-evident, fail-closed recovery through external provider state;
3. add a kill-point test that inspects the whole workspace before cleanup; and
4. prove recovery convergence and residue cleanup after that inspection.

## Non-blocking findings

1. Worked-example `.owpack` evidence called private archive helpers instead of
   proving publication through the governed public workflow.
2. `context-model.json` was a minimal identity sidecar rather than the complete
   normalized input consumed by `explorer.html`.
3. `pyproject.toml` advertised `owak-eval` before an evaluator package existed.

## Evidence observed

- 29 focused adapter/explorer/archive tests passed.
- Codex and Claude used the same public `AdapterSession`.
- Public intent preparation existed for all mutations and did not mint
  credentials.
- The forward Codex skill probe refused to treat a candidate pack as an
  authoritative workspace and used the documented strict command wire shape.
- The worked slices covered the required public synthetic cases, but the P1
  boundary violation required Gate 5 to remain closed.

