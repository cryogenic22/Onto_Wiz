from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from test_candidate_contracts import (
    valid_artifact_data,
    valid_eval_data,
    valid_manifest_data,
    valid_source_data,
)

SCHEMA_ROOT = Path(__file__).parents[2] / "schemas"


def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.contract
def test_candidate_schema_rejects_lifecycle_and_semantic_bypasses() -> None:
    check = validator("candidate-artifact.schema.json")
    valid = valid_artifact_data()
    check.validate(valid)

    invalid_documents: list[dict[str, object]] = []
    active = deepcopy(valid)
    active["lifecycle"] = "active"
    invalid_documents.append(active)

    blank = deepcopy(valid)
    blank["evidence_refs"] = [" "]
    invalid_documents.append(blank)

    metric = deepcopy(valid)
    metric["kind"] = "metric_definition"
    invalid_documents.append(metric)

    causal = deepcopy(valid)
    causal["claim_type"] = "causal_hypothesis"
    invalid_documents.append(causal)

    high_risk = deepcopy(valid)
    high_risk.update({"kind": "guardrail", "risk_level": "critical"})
    invalid_documents.append(high_risk)

    for document in invalid_documents:
        with pytest.raises(ValidationError):
            check.validate(document)


@pytest.mark.contract
def test_manifest_schema_requires_candidate_security_constants() -> None:
    check = validator("candidate-pack-manifest.schema.json")
    valid = valid_manifest_data()
    check.validate(valid)
    for field in (
        "format",
        "schema_target",
        "package_kind",
        "production_eligible",
        "releasable",
        "contains_protected_evaluations",
    ):
        incomplete = deepcopy(valid)
        incomplete.pop(field)
        with pytest.raises(ValidationError):
            check.validate(incomplete)


@pytest.mark.contract
def test_eval_and_source_schema_rules_are_independently_enforced() -> None:
    eval_check = validator("public-eval-case.schema.json")
    valid_eval = valid_eval_data()
    eval_check.validate(valid_eval)
    vacuous = deepcopy(valid_eval)
    vacuous["required_behaviours"] = []
    vacuous["prohibited_behaviours"] = []
    with pytest.raises(ValidationError):
        eval_check.validate(vacuous)

    source_check = validator("source-record.schema.json")
    valid_source = valid_source_data()
    source_check.validate(valid_source)
    withdrawn = deepcopy(valid_source)
    withdrawn["status"] = "withdrawn"
    withdrawn.pop("withdrawn_at")
    with pytest.raises(ValidationError):
        source_check.validate(withdrawn)

    personal = deepcopy(valid_source)
    personal["contains_personal_data"] = True
    personal.pop("consent_basis")
    with pytest.raises(ValidationError):
        source_check.validate(personal)
