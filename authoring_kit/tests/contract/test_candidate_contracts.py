from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import date

import pytest
from pydantic import ValidationError

from ontowiz_spec import (
    PINNED_ARTIFACT_KINDS,
    Applicability,
    ArchiveTransferAuthorization,
    CandidateArtifact,
    CandidateLifecycle,
    CandidatePackManifest,
    DecisionContract,
    EvidenceRef,
    HeldoutReference,
    PinnedArtifactDocument,
    PortableCandidateClaim,
    Provenance,
    PublicEvalCase,
    SourceRecord,
    WorkspaceManifest,
)
from ontowiz_spec.pinned_v0_1 import (
    DecisionHeuristic,
    Guardrail,
    MetricDefinition,
    TagDimension,
    Taxonomy,
    TaxonomyNode,
)
from ontowiz_spec.pinned_v0_1 import (
    Lifecycle as PinnedLifecycle,
)
from ontowiz_spec.pinned_v0_1 import (
    Tag as PinnedTag,
)


def _base_kwargs() -> dict[str, object]:
    return {
        "version": 1,
        "lifecycle": PinnedLifecycle.DRAFT,
        "created_by": "brand_sme",
        "tags": [PinnedTag(dimension=TagDimension.FUNCTION, value="brand")],
        "layer": "base",
        "source_document_ids": ["SRC-001"],
        "confidence": 0.8,
        "created_at": "2026-07-25T12:00:00Z",
    }


def _bind_pinned(data: dict[str, object], artifact: object) -> None:
    snapshot = PinnedArtifactDocument.from_artifact(artifact)  # type: ignore[arg-type]
    dumped = artifact.model_dump(mode="json")  # type: ignore[attr-defined]
    for field in (
        "id",
        "kind",
        "name",
        "version",
        "lifecycle",
        "lifecycle_history",
        "created_by",
        "reviewed_by",
        "approved_at",
        "tags",
        "layer",
        "source_document_ids",
        "confidence",
        "created_at",
        "updated_at",
    ):
        data[field] = dumped[field]
    data["pinned_artifact"] = snapshot.model_dump(mode="json")


def valid_artifact_data() -> dict[str, object]:
    pinned = Taxonomy(
        id="concept_nbrx_variance",
        name="NBRx variance",
        tree=[TaxonomyNode(name="NBRx variance")],
        **_base_kwargs(),
    )
    data: dict[str, object] = {
        "definition": "Difference between actual and planned NBRx.",
        "evidence_refs": ["EV-001"],
        "applicability": {
            "markets": ["GB"],
            "lifecycle_stages": ["launch"],
            "effective_from": "2026-01-01",
        },
        "provenance": {
            "mode": "sme_authored",
            "supplied_by": "brand_sme",
            "confidence": 0.8,
        },
        "owner_role": "brand_owner",
        "abstention_conditions": ["Required weekly data is missing."],
    }
    _bind_pinned(data, pinned)
    return data


def valid_manifest_data() -> dict[str, object]:
    return {
        "format": "ontowiz-candidate-pack",
        "format_version": 1,
        "package_kind": "candidate",
        "schema_target": "ontowiz-spec/vNext-min",
        "schema_revision": 1,
        "pack_id": "brand-variance",
        "pack_version": "0.1.0",
        "production_eligible": False,
        "releasable": False,
        "contains_protected_evaluations": False,
        "artifact_digests": [
            {
                "artifact_id": "concept_nbrx_variance",
                "digest": "sha256:" + "a" * 64,
            }
        ],
        "public_evaluation_suites": ["dev", "regression"],
    }


def valid_eval_data() -> dict[str, object]:
    return {
        "id": "EVAL-001",
        "decision_id": "DEC-001",
        "suite": "dev",
        "status": "candidate",
        "protected": False,
        "applicability": {
            "markets": ["GB"],
            "lifecycle_stages": ["launch"],
            "effective_from": "2026-01-01",
        },
        "scenario": [
            {"name": "actual_nbrx", "value": "80"},
            {"name": "plan_nbrx", "value": "100"},
        ],
        "required_behaviours": ["Quantify the variance."],
        "prohibited_behaviours": ["Claim access is causal without evidence."],
        "required_context": ["metric_nbrx_variance"],
        "evidence_expectations": ["Cite the metric receipt."],
        "scoring": {
            "decision_quality": 4,
            "method": 2,
            "evidence": 3,
            "uncertainty": 2,
            "human_boundary": 2,
        },
        "critical_failures": ["Invent a metric value."],
        "provenance": {
            "mode": "sme_authored",
            "supplied_by": "brand_sme",
            "confidence": 0.9,
        },
    }


def valid_source_data() -> dict[str, object]:
    return {
        "id": "SRC-001",
        "title": "Weekly brand data dictionary",
        "owner_role": "data_steward",
        "checksum": "sha256:" + "b" * 64,
        "source_date": "2026-01-01",
        "fresh_until": "2026-12-31",
        "scope": ["GB", "Brand A"],
        "client_boundary": "client-a",
        "confidentiality": "internal",
        "permitted_uses": ["authoring-workspace-transfer", "candidate-derivation"],
        "quotation_allowed": True,
        "redistribution_allowed": True,
        "raw_transfer_allowed": True,
        "retention_until": "2026-12-31",
        "contains_personal_data": False,
        "personal_data_transfer_allowed": False,
        "consent_basis": None,
        "status": "current",
        "withdrawn_at": None,
    }


@pytest.mark.contract
def test_original_19_artifact_kinds_are_preserved_exactly() -> None:
    assert {kind.value for kind in PINNED_ARTIFACT_KINDS} == {
        "instruction_set",
        "taxonomy",
        "jargon_map",
        "entity_registry",
        "fewshot_library",
        "override_rule",
        "prompt_template",
        "decision_heuristic",
        "data_quirk",
        "process_playbook",
        "judgment_pattern",
        "guardrail",
        "action_template",
        "eval_case",
        "metric_definition",
        "source_contract",
        "question_playbook",
        "anti_pattern",
        "exception_rule",
    }


@pytest.mark.contract
def test_candidate_manifest_security_fields_are_required_and_serialized() -> None:
    manifest = CandidatePackManifest.model_validate(valid_manifest_data())
    serialized = manifest.model_dump(mode="json")
    assert serialized["package_kind"] == "candidate"
    assert serialized["production_eligible"] is False
    assert serialized["releasable"] is False
    assert serialized["contains_protected_evaluations"] is False

    for field in (
        "format",
        "schema_target",
        "package_kind",
        "production_eligible",
        "releasable",
        "contains_protected_evaluations",
    ):
        incomplete = valid_manifest_data()
        incomplete.pop(field)
        with pytest.raises(ValidationError):
            CandidatePackManifest.model_validate(incomplete)


@pytest.mark.contract
def test_candidate_is_immutable_and_round_trips_platform_base_fields() -> None:
    artifact = CandidateArtifact.model_validate(valid_artifact_data())
    restored = CandidateArtifact.model_validate_json(artifact.model_dump_json())
    assert restored == artifact
    assert restored.version == 1
    assert restored.created_by == "brand_sme"
    assert restored.tags[0].dimension == "function"
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        artifact.source_document_ids += ("SRC-002",)
    with pytest.raises((AttributeError, TypeError, ValidationError)):
        artifact.pinned_artifact.canonical_json = "changed"  # type: ignore[union-attr,misc]


@pytest.mark.contract
def test_governed_lifecycle_and_platform_approval_are_impossible() -> None:
    for lifecycle in ("verified", "active"):
        data = valid_artifact_data()
        data["lifecycle"] = lifecycle
        with pytest.raises(ValidationError):
            CandidateArtifact.model_validate(data)

    for field, value in (("reviewed_by", "same-author"), ("approved_at", "2026-07-25T12:00:00Z")):
        data = valid_artifact_data()
        data[field] = value
        with pytest.raises(ValidationError):
            CandidateArtifact.model_validate(data)


@pytest.mark.contract
def test_lifecycle_history_must_be_contiguous_and_match_current_state() -> None:
    data = valid_artifact_data()
    snapshot = PinnedArtifactDocument.model_validate(data["pinned_artifact"])
    reviewed = snapshot.to_artifact().transition(
        PinnedLifecycle.REVIEW,
        changed_by="brand_sme",
        reason="confirmed proposal",
    )
    _bind_pinned(data, reviewed)
    artifact = CandidateArtifact.model_validate(data)
    assert artifact.lifecycle is CandidateLifecycle.REVIEW

    broken = dict(data)
    broken["lifecycle"] = "draft"
    with pytest.raises(ValidationError):
        CandidateArtifact.model_validate(broken)


@pytest.mark.contract
@pytest.mark.parametrize(
    ("field", "empty"),
    [
        ("source_document_ids", []),
        ("evidence_refs", []),
        ("abstention_conditions", []),
        ("owner_role", " "),
        ("definition", ""),
    ],
)
def test_required_semantics_reject_empty_and_blank(field: str, empty: object) -> None:
    data = valid_artifact_data()
    data[field] = empty
    with pytest.raises(ValidationError):
        CandidateArtifact.model_validate(data)

    blank_list = valid_artifact_data()
    blank_list["evidence_refs"] = [" "]
    with pytest.raises(ValidationError):
        CandidateArtifact.model_validate(blank_list)


@pytest.mark.contract
def test_metric_causal_and_high_risk_rules_fail_closed() -> None:
    metric = valid_artifact_data()
    metric.update(
        {
            "id": "metric_nbrx_variance",
            "kind": "metric_definition",
            "formula": "actual_nbrx - planned_nbrx",
            "formula_inputs": ["actual_nbrx", "planned_nbrx"],
            "unit": "prescriptions",
            "grain": "weekly/brand/market",
        }
    )
    _bind_pinned(
        metric,
        MetricDefinition(
            id="metric_nbrx_variance",
            name="NBRx variance",
            formula="actual_nbrx - planned_nbrx",
            unit="prescriptions",
            grain="weekly/brand/market",
            trusted_sources=["SRC-001"],
            **_base_kwargs(),
        ),
    )
    CandidateArtifact.model_validate(metric)
    for field, empty in (
        ("formula", None),
        ("formula_inputs", []),
        ("unit", None),
        ("grain", None),
    ):
        incomplete = dict(metric)
        incomplete[field] = empty
        with pytest.raises(ValidationError):
            CandidateArtifact.model_validate(incomplete)

    causal = valid_artifact_data()
    causal.update(
        {
            "id": "rule_access_driver",
            "kind": "decision_heuristic",
            "claim_type": "causal_hypothesis",
            "alternatives": ["awareness decline"],
            "disconfirming_conditions": ["Access is stable."],
        }
    )
    _bind_pinned(
        causal,
        DecisionHeuristic(
            id="rule_access_driver",
            name="NBRx variance",
            decision_logic="Treat access as a hypothesis, not a conclusion.",
            **_base_kwargs(),
        ),
    )
    CandidateArtifact.model_validate(causal)
    for field in ("alternatives", "disconfirming_conditions"):
        incomplete = dict(causal)
        incomplete[field] = []
        with pytest.raises(ValidationError):
            CandidateArtifact.model_validate(incomplete)

    guardrail = valid_artifact_data()
    guardrail.update({"id": "rule_no_causal_leap", "kind": "guardrail", "risk_level": "high"})
    _bind_pinned(
        guardrail,
        Guardrail(
            id="rule_no_causal_leap",
            name="NBRx variance",
            blocks_drivers=["unsupported causal attribution"],
            **_base_kwargs(),
        ),
    )
    with pytest.raises(ValidationError):
        CandidateArtifact.model_validate(guardrail)


@pytest.mark.contract
@pytest.mark.parametrize("unsafe_id", ["CON", "nul", "COM1", "lpt9"])
def test_windows_device_names_are_rejected(unsafe_id: str) -> None:
    data = valid_artifact_data()
    data["id"] = unsafe_id
    with pytest.raises(ValidationError):
        CandidateArtifact.model_validate(data)


@pytest.mark.contract
def test_public_eval_is_behavior_based_and_never_held_out() -> None:
    PublicEvalCase.model_validate(valid_eval_data())
    with pytest.raises(ValidationError):
        PublicEvalCase.model_validate({**valid_eval_data(), "suite": "heldout"})
    with pytest.raises(ValidationError):
        PublicEvalCase.model_validate(
            {
                **valid_eval_data(),
                "required_behaviours": [],
                "prohibited_behaviours": [],
            }
        )


@pytest.mark.contract
def test_source_embedding_refuses_expiry_and_personal_data_without_transfer_rights() -> None:
    source = SourceRecord.model_validate(valid_source_data())
    assert source.permits_embedding(as_of=date(2026, 7, 25))
    assert not source.permits_embedding(as_of=date(2027, 1, 1))

    personal = valid_source_data()
    personal.update(
        {
            "contains_personal_data": True,
            "consent_basis": "explicit research consent",
            "personal_data_transfer_allowed": False,
        }
    )
    assert not SourceRecord.model_validate(personal).permits_embedding(as_of=date(2026, 7, 25))


@pytest.mark.contract
def test_withdrawal_and_quoted_evidence_are_explicit() -> None:
    withdrawn = valid_source_data()
    withdrawn.update({"status": "withdrawn", "withdrawn_at": None})
    with pytest.raises(ValidationError):
        SourceRecord.model_validate(withdrawn)

    evidence = {
        "id": "EV-001",
        "source_id": "SRC-001",
        "source_checksum": "sha256:" + "b" * 64,
        "claim": "NBRx is below plan.",
        "locator_type": "page",
        "locator": "12",
        "mode": "observed",
        "permitted_use": "candidate-derivation",
        "quoted": True,
        "quote_digest": None,
        "valid_as_of": "2026-07-25",
        "extracted_at": "2026-07-25T12:00:00Z",
        "confidence": 0.9,
    }
    with pytest.raises(ValidationError):
        EvidenceRef.model_validate(evidence)


@pytest.mark.contract
def test_workspace_decision_and_heldout_reference_are_narrow() -> None:
    workspace = WorkspaceManifest(
        format="ontowiz-authoring-workspace",
        format_version=1,
        schema_target="ontowiz-spec/vNext-min",
        schema_revision=1,
        workspace_id="brand-variance",
        owner_roles=("steward", "brand_owner", "approver"),
        archetypes=("enterprise_core", "brand_analytics"),
        source_profile="referenced",
        adapter_neutral=True,
        contains_protected_evaluations=False,
    )
    assert workspace.source_profile.value == "referenced"

    decision = DecisionContract(
        id="DEC-001",
        decision="Recommend the next action for NBRx variance.",
        action_mode="recommend",
        human_owned_actions=("Approve commercial action.",),
        out_of_scope=("Patient-level targeting.",),
        materially_unsafe_answers=("Unsupported causal attribution.",),
        applicability=Applicability(
            markets=("GB",),
            lifecycle_stages=("launch",),
            effective_from=date(2026, 1, 1),
        ),
        owner_role="brand_owner",
    )
    assert decision.action_mode != "approve"

    reference = HeldoutReference(
        suite_id="BA-HO-001",
        suite_version="1.0.0",
        suite_schema="ow-eval/1",
        suite_digest="sha256:" + "c" * 64,
        evaluator_key_id="eval-key-1",
    )
    assert set(reference.model_dump()) == {
        "suite_id",
        "suite_version",
        "suite_schema",
        "suite_digest",
        "evaluator_key_id",
    }


@pytest.mark.contract
def test_supporting_models_reject_empty_scope_and_unbounded_confidence() -> None:
    with pytest.raises(ValidationError):
        Applicability(markets=(), lifecycle_stages=(), effective_from="2026-01-01")
    with pytest.raises(ValidationError):
        Provenance(mode="ai_inferred", supplied_by="draft-agent", confidence=1.1)

@pytest.mark.contract
@pytest.mark.parametrize(
    ("source_profile", "target_client_boundary"),
    [
        ("referenced", "client-a"),
        ("embedded", None),
    ],
)
def test_archive_transfer_authorization_binds_profile_to_target_boundary(
    source_profile: str,
    target_client_boundary: str | None,
) -> None:
    with pytest.raises(ValidationError):
        ArchiveTransferAuthorization.model_validate(
            {
                "source_profile": source_profile,
                "effective_date": "2026-07-26",
                "target_client_boundary": target_client_boundary,
            }
        )


@pytest.mark.contract
def test_archive_transfer_authorization_round_trips_exact_context() -> None:
    authorization = ArchiveTransferAuthorization(
        source_profile="embedded",
        effective_date=date(2026, 7, 26),
        target_client_boundary="client-a",
    )

    assert ArchiveTransferAuthorization.model_validate_json(
        authorization.model_dump_json()
    ) == authorization

@pytest.mark.contract
def test_portable_claim_requires_ordered_content_bindings() -> None:
    body: dict[str, object] = {
        "candidate_artifact_bindings": [
            {"artifact_id": "ART-001", "payload_digest": "sha256:" + "d" * 64}
        ],
        "claim": "Content-bound candidate claim.",
        "claim_record_id": "SRC-CLAIM-001",
        "evidence_bindings": [
            {
                "evidence_id": "EVID-001",
                "evidence_item_digest": "sha256:" + "c" * 64,
                "source_checksum": "sha256:" + "a" * 64,
                "source_id": "SRC-001",
            }
        ],
        "format": "ontowiz-candidate-claim-record",
        "format_version": 1,
        "pack_manifest_digest": "sha256:" + "e" * 64,
        "session_id": "SESSION-001",
        "session_sequence": 0,
        "source_bindings": [
            {
                "registered_checksum": "sha256:" + "a" * 64,
                "source_id": "SRC-001",
                "source_record_digest": "sha256:" + "b" * 64,
            }
        ],
        "status": "candidate",
        "workspace_id": "brand-variance",
        "workspace_revision": 0,
    }
    serialized = json.dumps(
        body,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload = (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")
    body["record_digest"] = "sha256:" + hashlib.sha256(payload).hexdigest()
    claim = PortableCandidateClaim.model_validate(body)
    assert claim.source_bindings[0].registered_checksum == "sha256:" + "a" * 64

