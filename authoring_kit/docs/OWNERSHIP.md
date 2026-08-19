# Ownership map

| Boundary | Accountable owner | Review owner | Forbidden coupling |
|---|---|---|---|
| `ontowiz_spec` contracts and schemas | Contract owner | Integrator | No authoring/evaluator imports |
| Workspace, proposals, validation, explorer | Authoring owner | Contract owner | No protected vault access |
| Archive envelopes | Portable-format owner | Security reviewer | No adapter-specific fields |
| Codex adapter | Codex adapter owner | Authoring owner | No direct canonical writes |
| Claude adapter | Claude adapter owner | Codex adapter owner | No divergent command semantics |
| Vault, run plan, receipts | Evaluation custodian | Independent security reviewer | No drafting-worker access |
| Examples and acceptance evidence | Slice owner | Adversarial reviewer | No protected cases |

One person may fill more than one implementation role in a pilot, but the
platform approver must be a different principal from the candidate author and a
real held-out custodian must be outside the drafting principal.

