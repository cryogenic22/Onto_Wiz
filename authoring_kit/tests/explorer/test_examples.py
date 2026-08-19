from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.generate import WorkedSlice, build_brand_slice, build_mr_slice, slice_files
from ontowiz_spec import (
    CandidateArtifact,
    CandidatePackManifest,
    DecisionContract,
    PublicEvalCase,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_BRAND_CLASSES = {
    "abstain",
    "adversarial",
    "boundary",
    "conflict",
    "exception",
    "missing",
    "normal",
    "stale",
    "tool-failure",
}
FORBIDDEN_PUBLIC_MARKERS = (
    b"api_key",
    b"bearer ",
    b"diagnose the patient",
    b"heldout",
    b"oracle answer",
    b"patient_id",
    b"private receipt",
    b"production_eligible\":true",
    b"releasable\":true",
    b"runtime authority",
    b"signing key",
)


@pytest.fixture(params=("brand-nbrx-variance", "mr-barriers-to-initiation"))
def worked_slice(request: pytest.FixtureRequest) -> WorkedSlice:
    if request.param == "brand-nbrx-variance":
        return build_brand_slice()
    return build_mr_slice()


def _scenario_value(case: PublicEvalCase, name: str) -> str:
    return next(field.value for field in case.scenario if field.name == name)


def _assert_shared_contract_round_trip(worked: WorkedSlice) -> None:
    CandidatePackManifest.model_validate_json(worked.manifest.model_dump_json())
    for artifact in worked.artifacts:
        CandidateArtifact.model_validate_json(artifact.model_dump_json())
    for decision in worked.decisions:
        DecisionContract.model_validate_json(decision.model_dump_json())
    for evaluation in worked.evaluations:
        PublicEvalCase.model_validate_json(evaluation.model_dump_json())


def test_worked_examples_are_exact_generated_goldens(worked_slice: WorkedSlice) -> None:
    expected = slice_files(worked_slice)
    root = REPO_ROOT / "examples" / worked_slice.slug
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert actual_paths == set(expected)
    for relative_path, expected_bytes in expected.items():
        assert (root / relative_path).read_bytes() == expected_bytes


def test_worked_examples_use_only_shared_candidate_contracts(
    worked_slice: WorkedSlice,
) -> None:
    _assert_shared_contract_round_trip(worked_slice)
    assert worked_slice.manifest.package_kind == "candidate"
    assert worked_slice.manifest.production_eligible is False
    assert worked_slice.manifest.releasable is False
    assert worked_slice.manifest.contains_protected_evaluations is False
    assert all(case.protected is False for case in worked_slice.evaluations)
    assert all(case.status == "candidate" for case in worked_slice.evaluations)


def test_brand_slice_covers_all_required_public_case_classes() -> None:
    worked = build_brand_slice()
    classes = {_scenario_value(case, "case_class") for case in worked.evaluations}
    assert len(worked.evaluations) == 18
    assert classes == REQUIRED_BRAND_CLASSES
    assert {case.suite.value for case in worked.evaluations} == {
        "challenge",
        "dev",
        "regression",
    }


def test_mr_slice_is_aggregate_non_clinical_and_candidate_only() -> None:
    worked = build_mr_slice()
    combined = b"".join(slice_files(worked).values()).lower()
    assert b"aggregate synthetic" in combined
    assert b"no diagnosis" in combined
    assert b"no prescribing" in combined
    assert b"patient-level" not in combined
    assert b"production claim" not in combined


def test_public_examples_pass_content_scan(worked_slice: WorkedSlice) -> None:
    files = slice_files(worked_slice)
    combined = b"".join(
        payload for path, payload in files.items() if path != "explorer.html"
    ).lower()
    for marker in FORBIDDEN_PUBLIC_MARKERS:
        assert marker not in combined
    assert b"http://" not in files["explorer.html"].lower()
    assert b"https://" not in files["explorer.html"].lower()
    assert b"<script" not in files["explorer.html"].lower()

    manifest = json.loads(files["pack/pack.yaml"])
    assert manifest["package_kind"] == "candidate"
    assert manifest["contains_protected_evaluations"] is False
