"""Deterministic JSON Schema export for checked-in contract artifacts."""

from __future__ import annotations

from pydantic import BaseModel

from .vnext import (
    ArchiveManifest,
    CandidateArtifact,
    CandidatePackManifest,
    DecisionContract,
    EvidenceRef,
    HeldoutReference,
    PortableCandidateClaim,
    PortableDecisionRecord,
    PortableSessionQuestions,
    PortableSessionReceipt,
    PortableSessionRecord,
    PortableSessionResponses,
    PublicEvalCase,
    SourceRecord,
    WorkspaceManifest,
)

_SCHEMAS: dict[str, type[BaseModel]] = {
    "archive-manifest.schema.json": ArchiveManifest,
    "candidate-artifact.schema.json": CandidateArtifact,
    "candidate-pack-manifest.schema.json": CandidatePackManifest,
    "decision-contract.schema.json": DecisionContract,
    "evidence-ref.schema.json": EvidenceRef,
    "heldout-reference.schema.json": HeldoutReference,
    "portable-candidate-claim.schema.json": PortableCandidateClaim,
    "portable-decision-record.schema.json": PortableDecisionRecord,
    "portable-session-questions.schema.json": PortableSessionQuestions,
    "portable-session-receipt.schema.json": PortableSessionReceipt,
    "portable-session-record.schema.json": PortableSessionRecord,
    "portable-session-responses.schema.json": PortableSessionResponses,
    "public-eval-case.schema.json": PublicEvalCase,
    "source-record.schema.json": SourceRecord,
    "workspace-manifest.schema.json": WorkspaceManifest,
}


def schema_documents() -> dict[str, dict[str, object]]:
    return {
        filename: model.model_json_schema(mode="validation")
        for filename, model in sorted(_SCHEMAS.items())
    }
