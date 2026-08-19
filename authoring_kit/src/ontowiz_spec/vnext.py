"""Additive vNext-min contracts preserving the existing OntoWiz artifact spine."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, Self, cast

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    WithJsonSchema,
    model_validator,
)

from .pinned_v0_1 import (
    ARTIFACT_MODELS as PINNED_MODELS,
)
from .pinned_v0_1 import (
    ArtifactBase as PinnedArtifactBase,
)
from .pinned_v0_1 import (
    ArtifactKind as PinnedArtifactKind,
)

SCHEMA_TARGET = "ontowiz-spec/vNext-min"
SCHEMA_REVISION = 1

_ID_JSON_PATTERN = (
    r"^(?![Cc][Oo][Nn]$|[Pp][Rr][Nn]$|[Aa][Uu][Xx]$|[Nn][Uu][Ll]$|"
    r"[Cc][Oo][Mm][1-9]$|[Ll][Pp][Tt][1-9]$)[A-Za-z0-9][A-Za-z0-9_-]{0,127}$"
)
_PACK_ID_JSON_PATTERN = r"^(?!con$|prn$|aux$|nul$|com[1-9]$|lpt[1-9]$)[a-z0-9][a-z0-9_-]{0,62}$"
_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$"
_PACK_ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,62}$"
_SEMVER_PATTERN = r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$"
_SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"
_PATH_JSON_PATTERN = (
    r"^(?!/)(?!.*(?:^|/)\.\.?(?:/|$))"
    r"(?!.*(?:^|/)(?:[Cc][Oo][Nn]|[Pp][Rr][Nn]|[Aa][Uu][Xx]|[Nn][Uu][Ll]"
    r"|[Cc][Oo][Mm][1-9]|[Ll][Pp][Tt][1-9])(?:\.[A-Za-z0-9._-]*)?(?:/|$))"
    r"(?!.*[. ](?:/|$))[A-Za-z0-9][A-Za-z0-9._/-]*$"
)

NonBlank = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, pattern=r".*\S.*"),
]


def _reject_reserved_id(value: str) -> str:
    if re.fullmatch(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])", value):
        raise ValueError("Windows reserved device name")
    return value


def _safe_archive_path(value: str) -> str:
    parts = value.split("/")
    reserved = re.compile(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?")
    if (
        not value.isascii()
        or unicodedata.normalize("NFC", value) != value
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or any(part in {"", ".", ".."} or part.endswith((".", " ")) for part in parts)
        or any(reserved.fullmatch(part) for part in parts)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value)
    ):
        raise ValueError("unsafe archive path")
    return value


SafeId = Annotated[
    str,
    StringConstraints(pattern=_ID_PATTERN),
    AfterValidator(_reject_reserved_id),
    WithJsonSchema({"type": "string", "pattern": _ID_JSON_PATTERN}),
]
PackId = Annotated[
    str,
    StringConstraints(pattern=_PACK_ID_PATTERN),
    AfterValidator(_reject_reserved_id),
    WithJsonSchema({"type": "string", "pattern": _PACK_ID_JSON_PATTERN}),
]
SemVer = Annotated[str, StringConstraints(pattern=_SEMVER_PATTERN)]
Sha256 = Annotated[str, StringConstraints(pattern=_SHA256_PATTERN)]
RelativeArchivePath = Annotated[
    str,
    AfterValidator(_safe_archive_path),
    WithJsonSchema({"type": "string", "pattern": _PATH_JSON_PATTERN}),
]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Lifecycle(str, Enum):
    """Exact lifecycle catalogue from the pinned 0.1.0 platform contract."""

    DRAFT = "draft"
    REVIEW = "review"
    VERIFIED = "verified"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class CandidateLifecycle(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"


class ArtifactKind(str, Enum):
    """The existing 19 kinds plus four additive vNext-min contract kinds."""

    INSTRUCTION_SET = "instruction_set"
    TAXONOMY = "taxonomy"
    JARGON_MAP = "jargon_map"
    ENTITY_REGISTRY = "entity_registry"
    FEWSHOT_LIBRARY = "fewshot_library"
    OVERRIDE_RULE = "override_rule"
    PROMPT_TEMPLATE = "prompt_template"
    DECISION_HEURISTIC = "decision_heuristic"
    DATA_QUIRK = "data_quirk"
    PROCESS_PLAYBOOK = "process_playbook"
    JUDGMENT_PATTERN = "judgment_pattern"
    GUARDRAIL = "guardrail"
    ACTION_TEMPLATE = "action_template"
    EVAL_CASE = "eval_case"
    METRIC_DEFINITION = "metric_definition"
    SOURCE_CONTRACT = "source_contract"
    QUESTION_PLAYBOOK = "question_playbook"
    ANTI_PATTERN = "anti_pattern"
    EXCEPTION_RULE = "exception_rule"
    EVIDENCE_CONTRACT = "evidence_contract"
    APPLICABILITY_CONTRACT = "applicability_contract"
    DECISION_CONTRACT = "decision_contract"
    TOOL_CONTRACT = "tool_contract"


PINNED_ARTIFACT_KINDS = frozenset(
    {
        ArtifactKind.INSTRUCTION_SET,
        ArtifactKind.TAXONOMY,
        ArtifactKind.JARGON_MAP,
        ArtifactKind.ENTITY_REGISTRY,
        ArtifactKind.FEWSHOT_LIBRARY,
        ArtifactKind.OVERRIDE_RULE,
        ArtifactKind.PROMPT_TEMPLATE,
        ArtifactKind.DECISION_HEURISTIC,
        ArtifactKind.DATA_QUIRK,
        ArtifactKind.PROCESS_PLAYBOOK,
        ArtifactKind.JUDGMENT_PATTERN,
        ArtifactKind.GUARDRAIL,
        ArtifactKind.ACTION_TEMPLATE,
        ArtifactKind.EVAL_CASE,
        ArtifactKind.METRIC_DEFINITION,
        ArtifactKind.SOURCE_CONTRACT,
        ArtifactKind.QUESTION_PLAYBOOK,
        ArtifactKind.ANTI_PATTERN,
        ArtifactKind.EXCEPTION_RULE,
    }
)


class ProvenanceMode(str, Enum):
    EXTRACTED = "extracted"
    SME_AUTHORED = "sme_authored"
    AI_INFERRED = "ai_inferred"


class ClaimType(str, Enum):
    OBSERVATION = "observation"
    INTERPRETATION = "interpretation"
    CAUSAL_HYPOTHESIS = "causal_hypothesis"
    NORMATIVE = "normative"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PublicSuite(str, Enum):
    DEV = "dev"
    REGRESSION = "regression"
    CHALLENGE = "challenge"


class SourceProfile(str, Enum):
    REFERENCED = "referenced"
    EMBEDDED = "embedded"


class SourceStatus(str, Enum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class Confidentiality(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class EvidenceMode(str, Enum):
    OBSERVED = "observed"
    INTERPRETATION = "interpretation"


class Applicability(ContractModel):
    markets: tuple[NonBlank, ...] = Field(min_length=1)
    lifecycle_stages: tuple[NonBlank, ...] = Field(min_length=1)
    products: tuple[NonBlank, ...] = ()
    audiences: tuple[NonBlank, ...] = ()
    effective_from: date


class Provenance(ContractModel):
    mode: ProvenanceMode
    supplied_by: NonBlank
    confidence: float = Field(ge=0.0, le=1.0)
    open_questions: tuple[NonBlank, ...] = ()


class Tag(ContractModel):
    dimension: NonBlank
    value: NonBlank
    parent: NonBlank | None = None


class CandidateLifecycleTransition(ContractModel):
    from_state: Literal["draft"]
    to_state: Literal["review"]
    changed_by: NonBlank
    reason: NonBlank
    delta_id: SafeId | None = None
    at: datetime | None = None


def _canonical_pinned_json(artifact: PinnedArtifactBase) -> str:
    raw = json.dumps(
        artifact.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return unicodedata.normalize("NFC", raw)


class PinnedArtifactDocument(ContractModel):
    kind: PinnedArtifactKind
    canonical_json: NonBlank
    sha256: Sha256

    @classmethod
    def from_artifact(cls, artifact: PinnedArtifactBase) -> PinnedArtifactDocument:
        canonical = _canonical_pinned_json(artifact)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return cls(kind=artifact.kind, canonical_json=canonical, sha256=f"sha256:{digest}")

    @model_validator(mode="after")
    def validates_exact_pinned_model(self) -> PinnedArtifactDocument:
        try:
            document = json.loads(self.canonical_json)
            model_type = PINNED_MODELS[self.kind]
            artifact = model_type.model_validate(document)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("invalid pinned artifact document") from exc
        canonical = _canonical_pinned_json(artifact)
        digest = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if canonical != self.canonical_json or digest != self.sha256:
            raise ValueError("pinned artifact bytes or digest are not canonical")
        return self

    def to_artifact(self) -> PinnedArtifactBase:
        model_type = PINNED_MODELS[self.kind]
        return model_type.model_validate(json.loads(self.canonical_json))


class CandidateArtifact(ContractModel):
    """Candidate projection retaining every field from the platform ArtifactBase."""

    id: SafeId
    kind: ArtifactKind
    name: NonBlank
    version: int = Field(default=1, ge=1)
    lifecycle: CandidateLifecycle = CandidateLifecycle.DRAFT
    lifecycle_history: tuple[CandidateLifecycleTransition, ...] = ()
    created_by: NonBlank = "system"
    reviewed_by: None = None
    approved_at: None = None
    tags: tuple[Tag, ...] = ()
    layer: NonBlank = "base"
    source_document_ids: tuple[SafeId, ...] = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    provenance: Provenance
    evidence_refs: tuple[SafeId, ...] = Field(min_length=1)
    applicability: Applicability
    owner_role: NonBlank
    abstention_conditions: tuple[NonBlank, ...] = Field(min_length=1)
    definition: NonBlank
    pinned_artifact: PinnedArtifactDocument | None = None

    claim_type: ClaimType = ClaimType.OBSERVATION
    alternatives: tuple[NonBlank, ...] = ()
    disconfirming_conditions: tuple[NonBlank, ...] = ()
    formula: NonBlank | None = None
    formula_inputs: tuple[NonBlank, ...] = ()
    unit: NonBlank | None = None
    grain: NonBlank | None = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    exception_ids: tuple[SafeId, ...] = ()

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"lifecycle": {"const": "draft"}}},
                    "then": {"properties": {"lifecycle_history": {"maxItems": 0}}},
                },
                {
                    "if": {"properties": {"lifecycle": {"const": "review"}}},
                    "then": {"properties": {"lifecycle_history": {"minItems": 1, "maxItems": 1}}},
                },
                {
                    "if": {
                        "properties": {
                            "kind": {
                                "enum": cast(
                                    list[JsonValue],
                                    sorted(kind.value for kind in PINNED_ARTIFACT_KINDS),
                                )
                            }
                        },
                        "required": ["kind"],
                    },
                    "then": {
                        "required": ["pinned_artifact"],
                        "properties": {"pinned_artifact": {"type": "object"}},
                    },
                },
                {
                    "if": {"properties": {"kind": {"const": "metric_definition"}}},
                    "then": {
                        "required": ["formula", "formula_inputs", "unit", "grain"],
                        "properties": {
                            "formula_inputs": {"minItems": 1},
                            "formula": {"minLength": 1, "pattern": r".*\S.*"},
                            "unit": {"minLength": 1, "pattern": r".*\S.*"},
                            "grain": {"minLength": 1, "pattern": r".*\S.*"},
                        },
                    },
                },
                {
                    "if": {
                        "properties": {"claim_type": {"const": "causal_hypothesis"}},
                        "required": ["claim_type"],
                    },
                    "then": {
                        "required": ["alternatives", "disconfirming_conditions"],
                        "properties": {
                            "alternatives": {"minItems": 1},
                            "disconfirming_conditions": {"minItems": 1},
                        },
                    },
                },
                {
                    "if": {
                        "properties": {
                            "kind": {"enum": ["override_rule", "guardrail", "decision_heuristic"]},
                            "risk_level": {"enum": ["high", "critical"]},
                        },
                        "required": ["kind", "risk_level"],
                    },
                    "then": {
                        "required": ["exception_ids"],
                        "properties": {"exception_ids": {"minItems": 1}},
                    },
                },
            ]
        },
    )

    @model_validator(mode="after")
    def semantic_rules(self) -> CandidateArtifact:
        if self.lifecycle is CandidateLifecycle.DRAFT and self.lifecycle_history:
            raise ValueError("draft artifact cannot carry review history")
        if self.lifecycle is CandidateLifecycle.REVIEW and len(self.lifecycle_history) != 1:
            raise ValueError("review artifact requires exactly one draft-to-review transition")
        if self.kind in PINNED_ARTIFACT_KINDS:
            if self.pinned_artifact is None or self.pinned_artifact.kind.value != self.kind.value:
                raise ValueError("pinned artifact snapshot is required and must match kind")
            pinned = self.pinned_artifact.to_artifact().model_dump(mode="json")
            candidate = self.model_dump(mode="json")
            duplicated_base_fields = (
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
            )
            if any(pinned.get(field) != candidate[field] for field in duplicated_base_fields):
                raise ValueError("candidate base fields differ from pinned artifact snapshot")
        elif self.pinned_artifact is not None:
            raise ValueError("additive vNext kinds cannot masquerade as pinned artifacts")
        if self.kind is ArtifactKind.METRIC_DEFINITION and (
            self.formula is None
            or not self.formula_inputs
            or self.unit is None
            or self.grain is None
        ):
            raise ValueError("metric definition requires formula, inputs, unit, and grain")
        if self.claim_type is ClaimType.CAUSAL_HYPOTHESIS and (
            not self.alternatives or not self.disconfirming_conditions
        ):
            raise ValueError("causal hypotheses require alternatives and disconfirming conditions")
        if (
            self.kind
            in {
                ArtifactKind.OVERRIDE_RULE,
                ArtifactKind.GUARDRAIL,
                ArtifactKind.DECISION_HEURISTIC,
            }
            and self.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
            and not self.exception_ids
        ):
            raise ValueError("high-risk rules require owned exceptions")
        return self


class SourceRecord(ContractModel):
    id: SafeId
    title: NonBlank
    owner_role: NonBlank
    checksum: Sha256
    source_date: date
    fresh_until: date | None
    scope: tuple[NonBlank, ...] = Field(min_length=1)
    client_boundary: NonBlank
    confidentiality: Confidentiality
    permitted_uses: tuple[NonBlank, ...] = Field(min_length=1)
    quotation_allowed: bool
    redistribution_allowed: bool
    raw_transfer_allowed: bool
    retention_until: date | None
    contains_personal_data: bool
    personal_data_transfer_allowed: bool = False
    consent_basis: NonBlank | None = None
    status: SourceStatus = SourceStatus.CURRENT
    withdrawn_at: datetime | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"lifecycle": {"const": "draft"}}},
                    "then": {"properties": {"lifecycle_history": {"maxItems": 0}}},
                },
                {
                    "if": {"properties": {"lifecycle": {"const": "review"}}},
                    "then": {"properties": {"lifecycle_history": {"minItems": 1, "maxItems": 1}}},
                },
                {
                    "if": {"properties": {"status": {"const": "withdrawn"}}},
                    "then": {
                        "required": ["withdrawn_at"],
                        "properties": {"withdrawn_at": {"type": "string", "format": "date-time"}},
                    },
                },
                {
                    "if": {"properties": {"contains_personal_data": {"const": True}}},
                    "then": {
                        "required": ["consent_basis"],
                        "properties": {
                            "consent_basis": {
                                "type": "string",
                                "minLength": 1,
                                "pattern": r".*\S.*",
                            }
                        },
                    },
                },
            ]
        },
    )

    @model_validator(mode="after")
    def governed_source_state(self) -> SourceRecord:
        if self.status is SourceStatus.WITHDRAWN and self.withdrawn_at is None:
            raise ValueError("withdrawn sources require withdrawn_at")
        if self.contains_personal_data and self.consent_basis is None:
            raise ValueError("personal data requires a consent_basis")
        return self

    def permits_embedding(self, *, as_of: date) -> bool:
        return (
            self.status is SourceStatus.CURRENT
            and (self.retention_until is None or self.retention_until >= as_of)
            and self.redistribution_allowed
            and self.raw_transfer_allowed
            and self.quotation_allowed
            and (
                not self.contains_personal_data
                or (self.personal_data_transfer_allowed and self.consent_basis is not None)
            )
            and self.confidentiality in {Confidentiality.PUBLIC, Confidentiality.INTERNAL}
            and "authoring-workspace-transfer" in self.permitted_uses
        )


class EvidenceRef(ContractModel):
    id: SafeId
    source_id: SafeId
    source_checksum: Sha256
    claim: NonBlank
    locator_type: Literal["page", "slide", "paragraph", "timestamp", "row", "cell", "section"]
    locator: NonBlank
    mode: EvidenceMode
    permitted_use: NonBlank
    quoted: bool
    quote_digest: Sha256 | None = None
    valid_as_of: date
    extracted_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "if": {"properties": {"quoted": {"const": True}}},
            "then": {
                "required": ["quote_digest"],
                "properties": {"quote_digest": {"type": "string", "pattern": _SHA256_PATTERN}},
            },
        },
    )

    @model_validator(mode="after")
    def quoted_evidence_has_digest(self) -> EvidenceRef:
        if self.quoted and self.quote_digest is None:
            raise ValueError("quoted evidence requires quote_digest")
        return self


def _portable_record_digest(value: dict[str, object]) -> str:
    serialized = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload = (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _is_unique_and_ordered(values: tuple[str, ...]) -> bool:
    return values == tuple(sorted(set(values)))


class _CandidatePortableRecord(ContractModel):
    workspace_id: PackId
    workspace_revision: int = Field(ge=0)
    session_id: SafeId
    session_sequence: int = Field(ge=0)
    status: Literal["candidate"]
    record_digest: Sha256

    @model_validator(mode="after")
    def record_digest_is_exact(self) -> Self:
        body = self.model_dump(mode="json", exclude={"record_digest"})
        if _portable_record_digest(body) != self.record_digest:
            raise ValueError("portable record digest mismatch")
        return self


class PortableSourceBinding(ContractModel):
    source_id: SafeId
    registered_checksum: Sha256
    source_record_digest: Sha256


class PortableEvidenceBinding(ContractModel):
    evidence_id: SafeId
    evidence_item_digest: Sha256
    source_id: SafeId
    source_checksum: Sha256


class PortableCandidateArtifactBinding(ContractModel):
    artifact_id: SafeId
    payload_digest: Sha256


class PortableDeltaBinding(ContractModel):
    delta_id: SafeId
    proposal_digest: Sha256


class PortableRecordDigestBinding(ContractModel):
    record_id: SafeId
    record_digest: Sha256


def _validate_content_binding_inventory(
    source_bindings: tuple[PortableSourceBinding, ...],
    evidence_bindings: tuple[PortableEvidenceBinding, ...],
    candidate_artifact_bindings: tuple[PortableCandidateArtifactBinding, ...],
) -> None:
    inventories = (
        tuple(item.source_id for item in source_bindings),
        tuple(item.evidence_id for item in evidence_bindings),
        tuple(item.artifact_id for item in candidate_artifact_bindings),
    )
    if any(not _is_unique_and_ordered(values) for values in inventories):
        raise ValueError("portable content bindings must be unique and ordered")
    source_checksums = {
        item.source_id: item.registered_checksum for item in source_bindings
    }
    if any(
        source_checksums.get(item.source_id) != item.source_checksum
        for item in evidence_bindings
    ):
        raise ValueError("portable evidence binding lacks its exact source binding")


class _ReferencedPortableRecord(_CandidatePortableRecord):
    source_bindings: tuple[PortableSourceBinding, ...] = Field(min_length=1)
    evidence_bindings: tuple[PortableEvidenceBinding, ...] = Field(min_length=1)
    candidate_artifact_bindings: tuple[PortableCandidateArtifactBinding, ...] = Field(
        min_length=1
    )
    pack_manifest_digest: Sha256

    @model_validator(mode="after")
    def bindings_are_unique_ordered_and_connected(self) -> Self:
        _validate_content_binding_inventory(
            self.source_bindings,
            self.evidence_bindings,
            self.candidate_artifact_bindings,
        )
        return self


class PortableCandidateClaim(_ReferencedPortableRecord):
    format: Literal["ontowiz-candidate-claim-record"]
    format_version: Literal[1]
    claim_record_id: SafeId
    claim: NonBlank


class PortableGapQuestion(ContractModel):
    id: SafeId
    gap_kind: Literal[
        "source",
        "evidence",
        "decision",
        "evaluation",
        "rule_evaluation",
        "authority",
    ]
    owner_role: SafeId | None
    blocking: bool
    prompt: NonBlank
    resolves: tuple[NonBlank, ...] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def resolutions_are_unique_and_ordered(self) -> Self:
        if not _is_unique_and_ordered(self.resolves):
            raise ValueError("question resolutions must be unique and ordered")
        return self


class PortableSessionResponse(ContractModel):
    id: SafeId
    question_id: SafeId
    response: NonBlank
    source_bindings: tuple[PortableSourceBinding, ...] = ()
    evidence_bindings: tuple[PortableEvidenceBinding, ...] = ()
    candidate_artifact_bindings: tuple[PortableCandidateArtifactBinding, ...] = ()
    pack_manifest_digest: Sha256

    @model_validator(mode="after")
    def bindings_are_unique_ordered_and_connected(self) -> Self:
        _validate_content_binding_inventory(
            self.source_bindings,
            self.evidence_bindings,
            self.candidate_artifact_bindings,
        )
        return self


class PortableSessionRecord(_CandidatePortableRecord):
    format: Literal["ontowiz-candidate-session-record"]
    format_version: Literal[1]
    canonical_state_digest: Sha256
    pack_manifest_digest: Sha256
    delta_bindings: tuple[PortableDeltaBinding, ...] = ()
    question_ids: tuple[SafeId, ...] = ()

    @model_validator(mode="after")
    def contents_are_unique_and_ordered(self) -> Self:
        delta_ids = tuple(item.delta_id for item in self.delta_bindings)
        if not _is_unique_and_ordered(delta_ids) or not _is_unique_and_ordered(
            self.question_ids
        ):
            raise ValueError("session references must be unique and ordered")
        return self


class PortableSessionQuestions(_CandidatePortableRecord):
    format: Literal["ontowiz-candidate-session-questions"]
    format_version: Literal[1]
    session_record_digest: Sha256
    questions: tuple[PortableGapQuestion, ...] = ()

    @model_validator(mode="after")
    def questions_are_unique_and_ordered(self) -> Self:
        ids = tuple(question.id for question in self.questions)
        if not _is_unique_and_ordered(ids):
            raise ValueError("session questions must be unique and ordered")
        return self


class PortableSessionResponses(_CandidatePortableRecord):
    format: Literal["ontowiz-candidate-session-responses"]
    format_version: Literal[1]
    session_record_digest: Sha256
    responses: tuple[PortableSessionResponse, ...] = ()

    @model_validator(mode="after")
    def responses_are_unique_and_ordered(self) -> Self:
        response_ids = tuple(response.id for response in self.responses)
        question_ids = tuple(response.question_id for response in self.responses)
        if not _is_unique_and_ordered(response_ids) or len(question_ids) != len(
            set(question_ids)
        ):
            raise ValueError("session responses must be unique and ordered")
        return self


class PortableSessionReceipt(_CandidatePortableRecord):
    format: Literal["ontowiz-candidate-session-receipt"]
    format_version: Literal[1]
    session_record_digest: Sha256
    questions_record_digest: Sha256
    responses_record_digest: Sha256
    pack_manifest_digest: Sha256
    question_ids: tuple[SafeId, ...] = ()
    response_ids: tuple[SafeId, ...] = ()
    source_bindings: tuple[PortableSourceBinding, ...] = ()
    evidence_bindings: tuple[PortableEvidenceBinding, ...] = ()
    candidate_artifact_bindings: tuple[PortableCandidateArtifactBinding, ...] = ()
    delta_bindings: tuple[PortableDeltaBinding, ...] = ()
    claim_record_bindings: tuple[PortableRecordDigestBinding, ...] = ()
    decision_record_bindings: tuple[PortableRecordDigestBinding, ...] = ()

    @model_validator(mode="after")
    def inventory_is_unique_and_ordered(self) -> Self:
        _validate_content_binding_inventory(
            self.source_bindings,
            self.evidence_bindings,
            self.candidate_artifact_bindings,
        )
        inventories = (
            self.question_ids,
            self.response_ids,
            tuple(item.delta_id for item in self.delta_bindings),
            tuple(item.record_id for item in self.claim_record_bindings),
            tuple(item.record_id for item in self.decision_record_bindings),
        )
        if any(not _is_unique_and_ordered(values) for values in inventories):
            raise ValueError("session receipt inventory must be unique and ordered")
        return self


class PortableDecisionRecord(_ReferencedPortableRecord):
    format: Literal["ontowiz-candidate-decision-record"]
    format_version: Literal[1]
    decision_record_id: SafeId
    decision: NonBlank
    rationale: NonBlank


class DecisionContract(ContractModel):
    id: SafeId
    decision: NonBlank
    action_mode: Literal["advise", "calculate", "recommend"]
    human_owned_actions: tuple[NonBlank, ...] = Field(min_length=1)
    out_of_scope: tuple[NonBlank, ...] = Field(min_length=1)
    materially_unsafe_answers: tuple[NonBlank, ...] = Field(min_length=1)
    applicability: Applicability
    owner_role: NonBlank


class ScoringWeights(ContractModel):
    decision_quality: float = Field(gt=0)
    method: float = Field(gt=0)
    evidence: float = Field(gt=0)
    uncertainty: float = Field(gt=0)
    human_boundary: float = Field(gt=0)


class ScenarioField(ContractModel):
    name: NonBlank
    value: NonBlank


class PublicEvalCase(ContractModel):
    id: SafeId
    decision_id: SafeId
    suite: PublicSuite
    status: Literal["candidate"]
    protected: Literal[False]
    applicability: Applicability
    scenario: tuple[ScenarioField, ...] = Field(min_length=1)
    deliberately_missing: tuple[NonBlank, ...] = ()
    required_behaviours: tuple[NonBlank, ...] = ()
    prohibited_behaviours: tuple[NonBlank, ...] = ()
    required_context: tuple[SafeId, ...] = Field(min_length=1)
    evidence_expectations: tuple[NonBlank, ...] = Field(min_length=1)
    scoring: ScoringWeights
    critical_failures: tuple[NonBlank, ...] = Field(min_length=1)
    provenance: Provenance

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "anyOf": [
                {
                    "required": ["required_behaviours"],
                    "properties": {"required_behaviours": {"minItems": 1}},
                },
                {
                    "required": ["prohibited_behaviours"],
                    "properties": {"prohibited_behaviours": {"minItems": 1}},
                },
            ]
        },
    )

    @model_validator(mode="after")
    def behaviours_are_non_vacuous(self) -> PublicEvalCase:
        if not self.required_behaviours and not self.prohibited_behaviours:
            raise ValueError("an evaluation must require or prohibit behavior")
        return self


class ArtifactDigest(ContractModel):
    artifact_id: SafeId
    digest: Sha256


class CandidatePackManifest(ContractModel):
    format: Literal["ontowiz-candidate-pack"]
    format_version: Literal[1]
    package_kind: Literal["candidate"]
    schema_target: Literal["ontowiz-spec/vNext-min"]
    schema_revision: Literal[1]
    pack_id: PackId
    pack_version: SemVer
    production_eligible: Literal[False]
    releasable: Literal[False]
    contains_protected_evaluations: Literal[False]
    artifact_digests: tuple[ArtifactDigest, ...]
    public_evaluation_suites: tuple[PublicSuite, ...]


class WorkspaceManifest(ContractModel):
    format: Literal["ontowiz-authoring-workspace"]
    format_version: Literal[1]
    schema_target: Literal["ontowiz-spec/vNext-min"]
    schema_revision: Literal[1]
    workspace_id: PackId
    owner_roles: tuple[NonBlank, ...] = Field(min_length=1)
    archetypes: tuple[NonBlank, ...] = Field(min_length=1)
    source_profile: SourceProfile
    adapter_neutral: Literal[True]
    contains_protected_evaluations: Literal[False]


class HeldoutReference(ContractModel):
    suite_id: SafeId
    suite_version: SemVer
    suite_schema: NonBlank
    suite_digest: Sha256
    evaluator_key_id: SafeId


class ArchiveEntry(ContractModel):
    path: RelativeArchivePath
    role: NonBlank
    media_type: NonBlank
    byte_count: int = Field(ge=0)
    sha256: Sha256


class ArchiveTransferAuthorization(ContractModel):
    source_profile: SourceProfile
    effective_date: date
    target_client_boundary: NonBlank | None = None

    @model_validator(mode="after")
    def transfer_scope_is_explicit(self) -> ArchiveTransferAuthorization:
        if (self.source_profile is SourceProfile.EMBEDDED) != (
            self.target_client_boundary is not None
        ):
            raise ValueError(
                "embedded transfer requires exactly one target client boundary"
            )
        return self


class ArchiveManifest(ContractModel):
    envelope_version: Literal[1]
    format: Literal["ontowiz-authoring-workspace", "ontowiz-candidate-pack"]
    format_version: Literal[1]
    schema_target: Literal["ontowiz-spec/vNext-min"]
    schema_revision: Literal[1]
    zip_compression: Literal["stored"]
    canonical_json: Literal["RFC8785-subset:UTF-8,NFC,sorted-keys,no-whitespace"]
    fixed_timestamp: Literal["1980-01-01T00:00:00Z"]
    max_entries: Literal[10000]
    max_entry_bytes: Literal[67108864]
    max_total_bytes: Literal[536870912]
    entries: tuple[ArchiveEntry, ...]
    transfer_authorization: ArchiveTransferAuthorization | None
    semantic_digest: Sha256

    @model_validator(mode="after")
    def transfer_matches_archive_format(self) -> ArchiveManifest:
        requires_transfer = self.format == "ontowiz-authoring-workspace"
        if requires_transfer != (self.transfer_authorization is not None):
            raise ValueError("archive transfer identity differs from archive format")
        return self
