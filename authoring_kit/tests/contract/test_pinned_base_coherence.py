from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError
from test_candidate_contracts import _bind_pinned, valid_artifact_data

from ontowiz_spec import CandidateArtifact, PinnedArtifactDocument
from ontowiz_spec.pinned_v0_1 import Lifecycle as PinnedLifecycle


@pytest.mark.contract
@pytest.mark.parametrize(
    ("field", "tampered_value"),
    [
        ("id", "different_id"),
        ("name", "Different name"),
        ("version", 2),
        ("created_by", "different_author"),
        ("tags", [{"dimension": "function", "value": "different"}]),
        ("layer", "client"),
        ("source_document_ids", ["SRC-002"]),
        ("confidence", 0.7),
        ("created_at", "2026-07-26T12:00:00Z"),
        ("updated_at", "2026-07-26T13:00:00Z"),
    ],
)
def test_pinned_snapshot_rejects_duplicated_base_field_drift(
    field: str,
    tampered_value: object,
) -> None:
    data = valid_artifact_data()
    data[field] = tampered_value

    with pytest.raises(ValidationError, match="base fields differ"):
        CandidateArtifact.model_validate(data)


@pytest.mark.contract
def test_pinned_snapshot_rejects_lifecycle_drift() -> None:
    data = valid_artifact_data()
    snapshot = PinnedArtifactDocument.model_validate(data["pinned_artifact"])
    reviewed = snapshot.to_artifact().transition(
        PinnedLifecycle.REVIEW,
        changed_by="brand_sme",
        reason="confirmed proposal",
    )
    reviewed_dump = reviewed.model_dump(mode="json")
    data["lifecycle"] = reviewed_dump["lifecycle"]
    data["lifecycle_history"] = reviewed_dump["lifecycle_history"]

    with pytest.raises(ValidationError, match="base fields differ"):
        CandidateArtifact.model_validate(data)


@pytest.mark.contract
def test_pinned_snapshot_rejects_lifecycle_history_drift() -> None:
    data = valid_artifact_data()
    snapshot = PinnedArtifactDocument.model_validate(data["pinned_artifact"])
    reviewed = snapshot.to_artifact().transition(
        PinnedLifecycle.REVIEW,
        changed_by="brand_sme",
        reason="confirmed proposal",
    )
    _bind_pinned(data, reviewed)

    tampered_history = deepcopy(data["lifecycle_history"])
    assert isinstance(tampered_history, list)
    assert isinstance(tampered_history[0], dict)
    tampered_history[0]["reason"] = "different reason"
    data["lifecycle_history"] = tampered_history

    with pytest.raises(ValidationError, match="base fields differ"):
        CandidateArtifact.model_validate(data)


@pytest.mark.contract
def test_pinned_snapshot_kind_must_match_candidate_kind() -> None:
    data = valid_artifact_data()
    data["kind"] = "prompt_template"

    with pytest.raises(ValidationError, match="snapshot is required and must match kind"):
        CandidateArtifact.model_validate(data)
