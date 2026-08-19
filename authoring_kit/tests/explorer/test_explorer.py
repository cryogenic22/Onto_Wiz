from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Sequence

import pytest

from ontowiz_authoring.explorer import (
    CandidateExplorerContext,
    CandidateExplorerSourceDocument,
    ExplorerContentError,
    build_candidate_explorer_context,
    candidate_explorer_context_bytes,
    render_candidate_explorer,
)
from ontowiz_spec import (
    CandidateArtifact,
    CandidatePackManifest,
    DecisionContract,
    PublicEvalCase,
)


def _canonical_json_value(value: object) -> bytes:
    text = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", text) + "\n").encode("utf-8")


def _canonical_model(model: object) -> bytes:
    dumped = model.model_dump(mode="json")  # type: ignore[attr-defined]
    return _canonical_json_value(dumped)


def _artifact(definition: str = "A bounded synthetic candidate concept.") -> CandidateArtifact:
    return CandidateArtifact.model_validate(
        {
            "abstention_conditions": ["Required synthetic evidence is missing."],
            "applicability": {
                "effective_from": "2026-01-01",
                "lifecycle_stages": ["launch"],
                "markets": ["GB"],
            },
            "definition": definition,
            "evidence_refs": ["EVID-PUBLIC-001"],
            "id": "ART-001",
            "kind": "evidence_contract",
            "name": "Synthetic evidence boundary",
            "owner_role": "analyst",
            "provenance": {
                "confidence": 1.0,
                "mode": "sme_authored",
                "supplied_by": "public-example",
            },
            "source_document_ids": ["SRC-PUBLIC-001"],
        }
    )


def _decision() -> DecisionContract:
    return DecisionContract.model_validate(
        {
            "action_mode": "advise",
            "applicability": {
                "effective_from": "2026-01-01",
                "lifecycle_stages": ["launch"],
                "markets": ["GB"],
            },
            "decision": "Explain the synthetic variance without claiming causality.",
            "human_owned_actions": ["Approve any operational response."],
            "id": "DEC-001",
            "materially_unsafe_answers": ["Invent missing values."],
            "out_of_scope": ["Production activation."],
            "owner_role": "analyst",
        }
    )


def _evaluation() -> PublicEvalCase:
    return PublicEvalCase.model_validate(
        {
            "applicability": {
                "effective_from": "2026-01-01",
                "lifecycle_stages": ["launch"],
                "markets": ["GB"],
            },
            "critical_failures": ["Claims a cause from variance alone."],
            "decision_id": "DEC-001",
            "evidence_expectations": ["Cite only public synthetic identifiers."],
            "id": "EVAL-001",
            "protected": False,
            "provenance": {
                "confidence": 1.0,
                "mode": "sme_authored",
                "supplied_by": "public-example",
            },
            "required_behaviours": ["State the bounded result."],
            "required_context": ["ART-001", "DEC-001"],
            "scenario": [{"name": "case_class", "value": "normal"}],
            "scoring": {
                "decision_quality": 1,
                "evidence": 1,
                "human_boundary": 1,
                "method": 1,
                "uncertainty": 1,
            },
            "status": "candidate",
            "suite": "dev",
        }
    )


def _manifest(
    artifacts: Sequence[CandidateArtifact],
    decisions: Sequence[DecisionContract],
    *,
    document_payloads: dict[str, bytes] | None = None,
    suites: Sequence[str] = ("dev",),
) -> CandidatePackManifest:
    documents = [*artifacts, *decisions]
    inventory = [
        {
            "artifact_id": document.id,
            "digest": "sha256:"
            + hashlib.sha256(
                document_payloads[document.id]
                if document_payloads is not None
                else _canonical_model(document)
            ).hexdigest(),
        }
        for document in sorted(documents, key=lambda item: item.id)
    ]
    return CandidatePackManifest.model_validate(
        {
            "artifact_digests": inventory,
            "contains_protected_evaluations": False,
            "format": "ontowiz-candidate-pack",
            "format_version": 1,
            "pack_id": "explorer-contract",
            "pack_version": "0.1.0",
            "package_kind": "candidate",
            "production_eligible": False,
            "public_evaluation_suites": list(suites),
            "releasable": False,
            "schema_revision": 1,
            "schema_target": "ontowiz-spec/vNext-min",
        }
    )


def _candidate_payloads(
    manifest: CandidatePackManifest,
    artifacts: Sequence[CandidateArtifact],
    decisions: Sequence[DecisionContract],
    evaluations: Sequence[PublicEvalCase],
    *,
    artifact_payloads: dict[str, bytes] | None = None,
) -> dict[str, bytes]:
    payloads = {"pack/pack.yaml": _canonical_model(manifest)}
    payloads.update(
        {
            f"pack/governance/{artifact.id}.json": (
                artifact_payloads[artifact.id]
                if artifact_payloads is not None
                else _canonical_model(artifact)
            )
            for artifact in artifacts
        }
    )
    payloads.update(
        {f"pack/scope/{decision.id}.json": _canonical_model(decision) for decision in decisions}
    )
    payloads.update(
        {
            f"pack/evaluations/{evaluation.id}.json": _canonical_model(evaluation)
            for evaluation in evaluations
        }
    )
    return payloads


def _context(
    manifest: CandidatePackManifest,
    artifacts: Sequence[CandidateArtifact],
    decisions: Sequence[DecisionContract],
    evaluations: Sequence[PublicEvalCase],
    *,
    payloads: dict[str, bytes] | None = None,
) -> CandidateExplorerContext:
    candidate_payloads = (
        payloads
        if payloads is not None
        else _candidate_payloads(manifest, artifacts, decisions, evaluations)
    )
    documents: list[CandidateExplorerSourceDocument] = [
        ("pack/pack.yaml", manifest, candidate_payloads["pack/pack.yaml"]),
        *(
            (
                f"pack/governance/{artifact.id}.json",
                artifact,
                candidate_payloads[f"pack/governance/{artifact.id}.json"],
            )
            for artifact in artifacts
        ),
        *(
            (
                f"pack/scope/{decision.id}.json",
                decision,
                candidate_payloads[f"pack/scope/{decision.id}.json"],
            )
            for decision in decisions
        ),
        *(
            (
                f"pack/evaluations/{evaluation.id}.json",
                evaluation,
                candidate_payloads[f"pack/evaluations/{evaluation.id}.json"],
            )
            for evaluation in evaluations
        ),
    ]
    assert {path for path, _, _ in documents} == set(candidate_payloads)
    return build_candidate_explorer_context(
        workspace_id="explorer-contract",
        revision=3,
        documents=documents,
    )


def test_explorer_is_deterministic_static_and_self_contained() -> None:
    artifact = _artifact("A <script>alert('escaped')</script> synthetic definition.")
    decision = _decision()
    evaluation = _evaluation()
    manifest = _manifest([artifact], [decision])
    first = render_candidate_explorer(_context(manifest, [artifact], [decision], [evaluation]))
    second = render_candidate_explorer(
        _context(
            manifest,
            tuple(reversed([artifact])),
            tuple(reversed([decision])),
            tuple(reversed([evaluation])),
        )
    )
    assert first == second
    assert first.startswith(b"<!doctype html>\n")
    assert b"candidate-only" in first
    assert b"&lt;script&gt;" in first
    lowered = first.lower()
    assert b"<script" not in lowered
    assert b"http://" not in lowered
    assert b"https://" not in lowered
    assert b" src=" not in lowered
    assert b" href=" not in lowered


def test_explorer_rejects_manifest_drift_and_sensitive_content() -> None:
    artifact = _artifact()
    decision = _decision()
    evaluation = _evaluation()
    manifest = _manifest([artifact], [decision])
    changed = artifact.model_copy(update={"definition": "Changed after digesting."})
    with pytest.raises(ExplorerContentError, match="digest inventory"):
        _context(
            manifest=manifest,
            artifacts=[changed],
            decisions=[decision],
            evaluations=[evaluation],
        )

    sensitive = _artifact("api_key=demo-secret must never render")
    sensitive_manifest = _manifest([sensitive], [decision])
    with pytest.raises(ExplorerContentError, match="forbidden content"):
        _context(
            manifest=sensitive_manifest,
            artifacts=[sensitive],
            decisions=[decision],
            evaluations=[evaluation],
        )


def test_context_model_is_the_validated_renderer_input_and_binds_raw_documents() -> None:
    artifact = _artifact()
    decision = _decision()
    evaluation = _evaluation()
    raw_artifact = _canonical_json_value(artifact.model_dump(mode="json", exclude_defaults=True))
    manifest = _manifest(
        [artifact],
        [decision],
        document_payloads={
            artifact.id: raw_artifact,
            decision.id: _canonical_model(decision),
        },
    )
    payloads = _candidate_payloads(
        manifest,
        [artifact],
        [decision],
        [evaluation],
        artifact_payloads={artifact.id: raw_artifact},
    )

    context = _context(
        manifest,
        [artifact],
        [decision],
        [evaluation],
        payloads=payloads,
    )
    serialized = candidate_explorer_context_bytes(context)
    validated = CandidateExplorerContext.model_validate_json(serialized)
    artifact_binding = next(
        binding for binding in validated.documents if binding.document_id == artifact.id
    )

    assert artifact_binding.sha256 == ("sha256:" + hashlib.sha256(raw_artifact).hexdigest())
    assert artifact_binding.sha256 != (
        "sha256:" + hashlib.sha256(_canonical_model(artifact)).hexdigest()
    )
    assert render_candidate_explorer(context) == render_candidate_explorer(validated)


@pytest.mark.parametrize("with_artifact", (False, True))
def test_context_model_supports_empty_and_partial_candidates(
    with_artifact: bool,
) -> None:
    artifacts = [_artifact()] if with_artifact else []
    manifest = _manifest(artifacts, [], suites=())
    context = _context(manifest, artifacts, [], [])
    serialized = candidate_explorer_context_bytes(context)

    validated = CandidateExplorerContext.model_validate_json(serialized)

    assert validated.artifacts == tuple(artifacts)
    assert validated.decisions == ()
    assert validated.evaluations == ()
    assert render_candidate_explorer(validated).startswith(b"<!doctype html>\n")
