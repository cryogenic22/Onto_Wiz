# OntoWiz candidate authoring

Use `ontowiz_authoring.adapters.AdapterSession`, exposed here as
`ClaudeAdapterSession`. The shared request, response, session, validation, and
packaging behavior is identical to Codex.

Resume from verified disk/provider high-water before acting. Call
`prepare_intent` for each mutation, have the external trust host authorize that
exact public intent, and keep the returned credential out-of-band. Present
deterministic questions, propose only complete replacement documents, require
explicit authorized confirmation, validate, and package only candidate
`.owpack` output.

Never write canonical files directly; implement trust, validation, recovery, or
packaging; hold keys; administer authority; approve, activate, release, or
serve; or access/freeze/score protected held-out evaluations and private
receipts.
