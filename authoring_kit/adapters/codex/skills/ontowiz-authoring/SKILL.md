---
name: ontowiz-authoring
description: Resume, question, propose, validate, and package an existing OntoWiz candidate workspace through the governed adapter protocol. Use for folder-aware Codex authoring of `.owworkspace` projects and candidate-only `.owpack` output; never use it for approval, activation, release, protected evaluation, or trust administration.
---

# OntoWiz Authoring

Use `ontowiz_authoring.adapters.AdapterSession`. Treat the workspace and its
external trust provider as authoritative; treat chat memory as untrusted.

## Workflow

1. Send `resume` before interpreting or changing the workspace. Present its
   deterministic questions and authority routing.
2. Call `AdapterSession.prepare_intent(request)`, then send only that public
   intent to the configured external trust host for authorization. Keep the
   returned credential in a fresh out-of-band `AuthoringTrustContext`. Never put
   credentials, tokens, keys, provider state, or protected paths in adapter JSON,
   prompts, logs, or files.
3. Turn an accepted edit into one complete replacement document with its exact
   target precondition, evidence IDs, owner role, confirmer roles, and rationale.
   Send `propose`; never write canonical files or apply line patches.
4. Show the proposal and require an explicit authorized confirmation. Send
   `confirm` with a fresh operation-bound trust context.
5. Resume again after conflicts, stale state, interruption, or tool failure.
   Continue only from verified disk/provider high-water.
6. Run `validate`, then `package`. Deliver only the candidate `.owpack` produced
   by the kernel.

## Hard boundaries

- Keep all output candidate-only.
- Do not install or replace authority, mint credentials, hold private keys,
  attest journals, approve, activate, release, or serve.
- Do not provision/read held-out vaults, freeze protected cases, score held-out
  runs, or publish private receipts.
- Do not reimplement validation, recovery, canonicalization, or packaging.

Read [references/protocol.md](references/protocol.md) only when constructing or
diagnosing adapter messages.
