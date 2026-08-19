from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError
from test_candidate_contracts import (
    _base_kwargs,
    valid_artifact_data,
    valid_source_data,
)

from ontowiz_spec import ArchiveEntry, PinnedArtifactDocument
from ontowiz_spec.pinned_v0_1 import EvalCase, MetricDefinition

SCHEMA_ROOT = Path(__file__).parents[2] / "schemas"


def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.mark.contract
def test_source_and_evidence_schemas_reject_null_bypasses() -> None:
    source_check = validator("source-record.schema.json")
    withdrawn = valid_source_data()
    withdrawn.update({"status": "withdrawn", "withdrawn_at": None})
    with pytest.raises(JsonSchemaValidationError):
        source_check.validate(withdrawn)

    personal = valid_source_data()
    personal.update({"contains_personal_data": True, "consent_basis": None})
    with pytest.raises(JsonSchemaValidationError):
        source_check.validate(personal)

    evidence_check = validator("evidence-ref.schema.json")
    quoted = {
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
    with pytest.raises(JsonSchemaValidationError):
        evidence_check.validate(quoted)


@pytest.mark.contract
def test_candidate_schema_requires_pinned_snapshot_and_exact_review_transition() -> None:
    check = validator("candidate-artifact.schema.json")
    valid = valid_artifact_data()
    check.validate(valid)

    missing_snapshot = deepcopy(valid)
    missing_snapshot["pinned_artifact"] = None
    with pytest.raises(JsonSchemaValidationError):
        check.validate(missing_snapshot)

    bad_review = deepcopy(valid)
    bad_review["lifecycle"] = "review"
    bad_review["lifecycle_history"] = []
    with pytest.raises(JsonSchemaValidationError):
        check.validate(bad_review)

    high_risk_heuristic = deepcopy(valid)
    high_risk_heuristic.update(
        {
            "kind": "decision_heuristic",
            "risk_level": "high",
            "exception_ids": [],
        }
    )
    with pytest.raises(JsonSchemaValidationError):
        check.validate(high_risk_heuristic)


@pytest.mark.contract
@pytest.mark.parametrize(
    "path",
    [
        "pack/CON.txt",
        "pack/nul",
        "pack/name.",
        "pack/name ",
        "pack/../escape.json",
        "pack/café.json",
    ],
)
def test_archive_paths_reject_platform_unsafe_or_non_ascii_names(path: str) -> None:
    data = {
        "path": path,
        "role": "candidate-artifact",
        "media_type": "application/json",
        "byte_count": 1,
        "sha256": "sha256:" + "a" * 64,
    }
    with pytest.raises(ValidationError):
        ArchiveEntry.model_validate(data)
    with pytest.raises(JsonSchemaValidationError):
        validator("archive-manifest.schema.json").validate(
            {
                "envelope_version": 1,
                "format": "ontowiz-candidate-pack",
                "format_version": 1,
                "schema_target": "ontowiz-spec/vNext-min",
                "schema_revision": 1,
                "zip_compression": "stored",
                "canonical_json": "RFC8785-subset:UTF-8,NFC,sorted-keys,no-whitespace",
                "fixed_timestamp": "1980-01-01T00:00:00Z",
                "max_entries": 10000,
                "max_entry_bytes": 67108864,
                "max_total_bytes": 536870912,
                "entries": [data],
                "semantic_digest": "sha256:" + "b" * 64,
            }
        )


@pytest.mark.contract
def test_vendored_subtype_round_trip_preserves_lists_mappings_booleans_and_numbers() -> None:
    eval_case = EvalCase(
        id="eval_roundtrip",
        name="Pinned evaluation",
        question="What changed?",
        must_contain=["variance", "uncertainty"],
        must_not_contain=["guaranteed"],
        gold_answer="Explain variance with uncertainty.",
        validates=["metric_roundtrip"],
        rubric={"decision_quality": 0.5, "evidence": 0.5},
        **_base_kwargs(),
    )
    metric = MetricDefinition(
        id="metric_roundtrip",
        name="Pinned metric",
        formula="actual - plan",
        unit="prescriptions",
        grain="weekly/brand/market",
        synonyms=["NBRx delta"],
        caveats=["Plan version must match."],
        trusted_sources=["SRC-001"],
        **_base_kwargs(),
    )

    for original in (eval_case, metric):
        snapshot = PinnedArtifactDocument.from_artifact(original)
        restored = snapshot.to_artifact()
        assert type(restored) is type(original)
        assert restored.model_dump(mode="json") == original.model_dump(mode="json")

        tampered = snapshot.model_dump(mode="json")
        tampered["canonical_json"] = snapshot.canonical_json.replace(original.name, "changed", 1)
        with pytest.raises(ValidationError):
            PinnedArtifactDocument.model_validate(tampered)
