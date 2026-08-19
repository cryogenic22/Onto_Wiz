# vNext-min additive compatibility map

The source lock pins Onto_Wiz `ontowiz-spec` 0.1.0. vNext-min preserves the
following base fields without renaming or changing meaning:

`id`, `kind`, `name`, `version`, `lifecycle`, `lifecycle_history`,
`created_by`, `reviewed_by`, `approved_at`, `tags`, `layer`,
`source_document_ids`, `confidence`, `created_at`, and `updated_at`.

The original closed catalogue is preserved exactly:

`instruction_set`, `taxonomy`, `jargon_map`, `entity_registry`,
`fewshot_library`, `override_rule`, `prompt_template`, `decision_heuristic`,
`data_quirk`, `process_playbook`, `judgment_pattern`, `guardrail`,
`action_template`, `eval_case`, `metric_definition`, `source_contract`,
`question_playbook`, `anti_pattern`, and `exception_rule`.

vNext-min adds four explicit kinds required by both experiments:
`evidence_contract`, `applicability_contract`, `decision_contract`, and
`tool_contract`. These are additions, not replacements.

Candidate records narrow lifecycle to `draft|review` and add provenance,
evidence references, applicability, owner, abstention, standardized definition,
and semantic rule fields. Every original-kind candidate carries a
`pinned_artifact` snapshot validated by the byte-pinned v0.1 model for that
kind. The snapshot is canonical JSON plus its SHA-256 digest, so all
type-specific fields round-trip losslessly and cannot drift independently of
the candidate base fields. Additive vNext-only kinds cannot carry this
snapshot.

The phase-one platform importer is deliberately absent; a later governed
importer must map a validated candidate record to proposed Deltas and must
never activate directly.
