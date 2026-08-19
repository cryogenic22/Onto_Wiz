# Adapter protocol

Create an `AdapterRequest` with:

- `format: "ontowiz-adapter-request"`
- `format_version: 1`
- a safe `request_id`
- the exact `workspace_id`
- `expected_revision` for every command except discovery-style `resume`
- one discriminated `command`

Supported commands are `resume`, `register_source`, `record_evidence`,
`propose`, `confirm`, `update_session`, `withdraw_source`, `validate`, and
`package`. There are deliberately no authority, approval, activation, release,
or evaluator-custodian commands.

The `command` object is discriminated by `operation`:

- `resume`, `validate`, `package`: only `{"operation":"..."}`.
- `register_source`: `source` is one full `SourceRecord`; `material_path` is a
  governed relative path or null.
- `record_evidence`: `evidence` is one full `EvidenceRef`; `quote_payload` is
  the authorized quote text or null.
- `propose`: include `delta_id`, `target_owner_role`,
  `allowed_confirmer_roles`, `target_path`, `expected_target_digest`,
  `replacement_body`, `evidence_ids`, and `rationale`. The replacement is the
  complete target document, never a patch.
- `confirm`: include `delta_id` and timezone-aware `confirmed_at`.
- `update_session`: include `stage`, `last_delta_id`, `open_question_ids`, and
  `next_mission`.
- `withdraw_source`: include `source_id` and timezone-aware `withdrawn_at`.

Construct these objects with the exported Pydantic command models. Do not
invent omitted fields, silently coerce malformed input, or copy credentials
into the envelope.

Call `AdapterSession.prepare_intent(request)` before each mutation and give its
public `AuthoringIntent` to the external trust host. It returns `None` for
read-only commands. Supply the resulting credential only out-of-band as a fresh
`AuthoringTrustContext`, then call `execute(request, trust=...)`. Use
`execute_json` for strict duplicate-key rejecting JSON. Responses contain only
a safe outcome and a verified session/question/validation snapshot.

On `E_STALE`, `E_CONFLICT`, or interruption, discard conversational assumptions
and send `resume`. On authorization or validation errors, do not retry with
broader authority or weaker data.
