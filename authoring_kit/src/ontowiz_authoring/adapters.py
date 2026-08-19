"""Strict provider-neutral protocol for candidate authoring adapters."""

from __future__ import annotations

import json
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, NoReturn, TypeAlias

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    ValidationError,
    model_validator,
)

from ontowiz_spec import EvidenceRef, SourceRecord

from .archive import ArchiveError, build_candidate_pack
from .authoring import (
    AuthoringConflictError,
    AuthoringError,
    AuthoringIntent,
    AuthoringOperation,
    AuthoringTrustContext,
    AuthoringTrustProvider,
    AuthoringValidationError,
    AuthorizationError,
    StaleProposalError,
    compile_questions,
    confirm_proposal,
    get_workspace_revision,
    load_session_state,
    prepare_authoring_intent,
    prepare_confirmation_intent,
    propose_replacement,
    record_evidence,
    register_source,
    update_session_state,
    validate_authoring,
    withdraw_source,
)
from .authority_errors import AuthorityClientError
from .workspace import Workspace, WorkspaceError, load_workspace

_MAX_REQUEST_BYTES = 1_048_576
_SAFE_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$"
_PACK_ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,62}$"
_SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"


def _reject_reserved_id(value: str) -> str:
    if value.casefold() in {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{index}" for index in range(1, 10)),
        *(f"lpt{index}" for index in range(1, 10)),
    }:
        raise ValueError("reserved identifier")
    return value


SafeId = Annotated[
    str,
    StringConstraints(pattern=_SAFE_ID_PATTERN),
    AfterValidator(_reject_reserved_id),
]
PackId = Annotated[
    str,
    StringConstraints(pattern=_PACK_ID_PATTERN),
    AfterValidator(_reject_reserved_id),
]
Sha256 = Annotated[str, StringConstraints(pattern=_SHA256_PATTERN)]
Stage: TypeAlias = Literal["discover", "scenario", "challenge", "ratify"]
AdapterOperation: TypeAlias = Literal[
    "resume",
    "register_source",
    "record_evidence",
    "propose",
    "confirm",
    "update_session",
    "withdraw_source",
    "validate",
    "package",
]
AdapterErrorCode: TypeAlias = Literal[
    "E_REQUEST_INVALID",
    "E_WORKSPACE_MISMATCH",
    "E_AUTHORIZATION",
    "E_AUTHORITY_UNAVAILABLE",
    "E_STALE",
    "E_CONFLICT",
    "E_VALIDATION",
    "E_OPERATION_FAILED",
]


class _ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ResumeCommand(_ProtocolModel):
    operation: Literal["resume"]


class RegisterSourceCommand(_ProtocolModel):
    operation: Literal["register_source"]
    source: SourceRecord
    material_path: str | None = None


class RecordEvidenceCommand(_ProtocolModel):
    operation: Literal["record_evidence"]
    evidence: EvidenceRef
    quote_payload: str | None = None


class ProposeCommand(_ProtocolModel):
    operation: Literal["propose"]
    delta_id: SafeId
    target_owner_role: SafeId
    allowed_confirmer_roles: tuple[SafeId, ...] = Field(min_length=1)
    target_path: str
    expected_target_digest: Sha256 | None
    replacement_body: dict[str, JsonValue]
    evidence_ids: tuple[SafeId, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=16_384)


class ConfirmCommand(_ProtocolModel):
    operation: Literal["confirm"]
    delta_id: SafeId
    confirmed_at: datetime


class UpdateSessionCommand(_ProtocolModel):
    operation: Literal["update_session"]
    stage: Stage
    last_delta_id: SafeId | None = None
    open_question_ids: tuple[SafeId, ...] = ()
    next_mission: Stage


class WithdrawSourceCommand(_ProtocolModel):
    operation: Literal["withdraw_source"]
    source_id: SafeId
    withdrawn_at: datetime


class ValidateCommand(_ProtocolModel):
    operation: Literal["validate"]


class PackageCommand(_ProtocolModel):
    operation: Literal["package"]


AdapterCommand: TypeAlias = Annotated[
    ResumeCommand
    | RegisterSourceCommand
    | RecordEvidenceCommand
    | ProposeCommand
    | ConfirmCommand
    | UpdateSessionCommand
    | WithdrawSourceCommand
    | ValidateCommand
    | PackageCommand,
    Field(discriminator="operation"),
]


class AdapterRequest(_ProtocolModel):
    """One content-bounded command; credentials are deliberately out-of-band."""

    format: Literal["ontowiz-adapter-request"]
    format_version: Literal[1]
    request_id: SafeId
    workspace_id: PackId
    expected_revision: int | None = Field(default=None, ge=0)
    command: AdapterCommand

    @model_validator(mode="after")
    def mutation_and_checkpoint_commands_use_cas(self) -> AdapterRequest:
        if self.command.operation != "resume" and self.expected_revision is None:
            raise ValueError("non-resume adapter requests require expected_revision")
        return self


class AdapterQuestion(_ProtocolModel):
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
    prompt: str
    resolves: tuple[str, ...]


class AdapterValidationSnapshot(_ProtocolModel):
    source_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    proposal_count: int = Field(ge=0)
    confirmed_proposals: int = Field(ge=0)
    pack_document_count: int = Field(ge=0)


class AdapterSessionSnapshot(_ProtocolModel):
    """Verified disk/provider state returned after each successful command."""

    workspace_id: PackId
    workspace_revision: int = Field(ge=0)
    session_revision: int = Field(ge=0)
    session_sequence: int = Field(ge=0)
    stage: Stage
    last_delta_id: SafeId | None
    open_question_ids: tuple[SafeId, ...]
    next_mission: Stage
    questions: tuple[AdapterQuestion, ...]
    validation: AdapterValidationSnapshot


class AdapterOutcome(_ProtocolModel):
    operation: AdapterOperation
    entity_id: SafeId | None = None
    entity_status: (
        Literal["candidate", "current", "withdrawn", "proposed", "confirmed"] | None
    ) = None
    target_path: str | None = None
    artifact_name: str | None = None
    semantic_digest: Sha256 | None = None
    archive_sha256: Sha256 | None = None


class AdapterError(_ProtocolModel):
    code: AdapterErrorCode
    message: str


class AdapterResponse(_ProtocolModel):
    format: Literal["ontowiz-adapter-response"]
    format_version: Literal[1]
    request_id: SafeId
    workspace_id: PackId
    status: Literal["ok", "error"]
    session: AdapterSessionSnapshot | None = None
    outcome: AdapterOutcome | None = None
    error: AdapterError | None = None

    @model_validator(mode="after")
    def success_or_error_is_exact(self) -> AdapterResponse:
        success = self.session is not None and self.outcome is not None and self.error is None
        failure = self.session is None and self.outcome is None and self.error is not None
        if (self.status == "ok" and not success) or (self.status == "error" and not failure):
            raise ValueError("adapter response success/error payload is incoherent")
        return self


class _AdapterStaleError(RuntimeError):
    pass


class _AdapterWorkspaceMismatchError(RuntimeError):
    pass


class _AdapterTrustError(RuntimeError):
    pass


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _load_request(payload: bytes | str) -> AdapterRequest:
    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    if not raw or len(raw) > _MAX_REQUEST_BYTES:
        raise ValueError("adapter request size is invalid")
    text = raw.decode("utf-8")
    parsed = json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_json_constant,
    )
    return AdapterRequest.model_validate(parsed)


def adapter_response_bytes(response: AdapterResponse) -> bytes:
    """Return deterministic, newline-terminated JSON with no provider credentials."""

    serialized = json.dumps(
        response.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")


class AdapterSession:
    """Thin dispatcher over the public candidate authoring and archive kernel."""

    def __init__(
        self,
        workspace: Workspace | str | Path,
        trust_provider: AuthoringTrustProvider,
        *,
        output_directory: str | Path,
    ) -> None:
        self._workspace = (
            workspace if isinstance(workspace, Workspace) else load_workspace(workspace)
        )
        self._trust_provider = trust_provider
        self._output_directory = Path(output_directory).absolute()

    @property
    def workspace_id(self) -> str:
        return self._workspace.manifest.workspace_id

    @property
    def package_path(self) -> Path:
        return self._output_directory / f"{self.workspace_id}.owpack"

    def _snapshot(self) -> AdapterSessionSnapshot:
        revision_before = get_workspace_revision(self._workspace, self._trust_provider)
        state = load_session_state(self._workspace, self._trust_provider)
        questions = compile_questions(self._workspace, self._trust_provider)
        report = validate_authoring(self._workspace, self._trust_provider)
        revision_after = get_workspace_revision(self._workspace, self._trust_provider)
        if revision_before != revision_after or state.revision > revision_after:
            raise _AdapterStaleError("workspace changed while producing adapter snapshot")
        return AdapterSessionSnapshot(
            workspace_id=self.workspace_id,
            workspace_revision=revision_after,
            session_revision=state.revision,
            session_sequence=state.sequence,
            stage=state.stage,
            last_delta_id=state.last_delta_id,
            open_question_ids=state.open_question_ids,
            next_mission=state.next_mission,
            questions=tuple(
                AdapterQuestion(
                    id=question.id,
                    gap_kind=question.gap_kind,
                    owner_role=question.owner_role,
                    blocking=question.blocking,
                    prompt=question.prompt,
                    resolves=question.resolves,
                )
                for question in questions
            ),
            validation=AdapterValidationSnapshot.model_validate(report.model_dump(mode="json")),
        )

    def prepare_intent(self, request: AdapterRequest) -> AuthoringIntent | None:
        """Prepare the exact public identity for external credential issuance."""

        self._check_request_anchor(request)
        command = request.command
        if isinstance(command, ResumeCommand | ValidateCommand | PackageCommand):
            return None
        expected_revision = request.expected_revision
        if expected_revision is None:
            raise _AdapterStaleError("mutation request lacks expected revision")
        if isinstance(command, ConfirmCommand):
            return prepare_confirmation_intent(
                self._workspace,
                self._trust_provider,
                delta_id=command.delta_id,
                confirmed_at=command.confirmed_at,
                expected_revision=expected_revision,
            )
        if isinstance(command, RegisterSourceCommand):
            operation: AuthoringOperation = "register_source"
            normalized: dict[str, object] = {
                "source": command.source.model_dump(mode="json"),
                "material_path": command.material_path,
            }
        elif isinstance(command, RecordEvidenceCommand):
            operation = "record_evidence"
            normalized = {
                "evidence": command.evidence.model_dump(mode="json"),
                "quote_payload": command.quote_payload,
            }
        elif isinstance(command, ProposeCommand):
            allowed = tuple(sorted(set(command.allowed_confirmer_roles)))
            evidence_ids = tuple(sorted(set(command.evidence_ids)))
            if (
                len(allowed) != len(command.allowed_confirmer_roles)
                or len(evidence_ids) != len(command.evidence_ids)
            ):
                raise AuthoringValidationError(
                    "proposal intent contains duplicate roles or evidence ids"
                )
            operation = "propose"
            normalized = {
                "delta_id": command.delta_id,
                "target_owner_role": command.target_owner_role,
                "allowed_confirmer_roles": list(allowed),
                "target_path": command.target_path,
                "expected_target_digest": command.expected_target_digest,
                "replacement_body": dict(command.replacement_body),
                "evidence_ids": list(evidence_ids),
                "rationale": command.rationale,
            }
        elif isinstance(command, UpdateSessionCommand):
            question_ids = tuple(sorted(set(command.open_question_ids)))
            if len(question_ids) != len(command.open_question_ids):
                raise AuthoringValidationError(
                    "session intent contains duplicate question ids"
                )
            operation = "update_session"
            normalized = {
                "stage": command.stage,
                "last_delta_id": command.last_delta_id,
                "open_question_ids": list(question_ids),
                "next_mission": command.next_mission,
            }
        elif isinstance(command, WithdrawSourceCommand):
            operation = "withdraw_source"
            normalized = {
                "source_id": command.source_id,
                "withdrawn_at": command.withdrawn_at.isoformat(),
            }
        else:
            raise AssertionError("unreachable adapter intent command")
        return prepare_authoring_intent(
            operation,
            self.workspace_id,
            expected_revision,
            normalized,
        )

    def _trusted_mutation(
        self,
        trust: AuthoringTrustContext | None,
    ) -> AuthoringTrustContext:
        if trust is None or trust.provider is not self._trust_provider:
            raise _AdapterTrustError("an external trust context is required")
        return trust

    def _check_request_anchor(self, request: AdapterRequest) -> int:
        if request.workspace_id != self.workspace_id:
            raise _AdapterWorkspaceMismatchError("request belongs to another workspace")
        current_revision = get_workspace_revision(self._workspace, self._trust_provider)
        if (
            request.expected_revision is not None
            and request.expected_revision != current_revision
        ):
            raise _AdapterStaleError("adapter request revision is stale")
        return current_revision

    def _dispatch(
        self,
        request: AdapterRequest,
        trust: AuthoringTrustContext | None,
    ) -> AdapterOutcome:
        command = request.command
        expected_revision = request.expected_revision
        if isinstance(command, ResumeCommand):
            return AdapterOutcome(operation="resume", entity_status="candidate")
        if isinstance(command, ValidateCommand):
            return AdapterOutcome(operation="validate", entity_status="candidate")
        if isinstance(command, PackageCommand):
            self._output_directory.mkdir(parents=True, exist_ok=True)
            archive = build_candidate_pack(
                self._workspace,
                self.package_path,
                trust_provider=self._trust_provider,
            )
            return AdapterOutcome(
                operation="package",
                entity_status="candidate",
                artifact_name=self.package_path.name,
                semantic_digest=archive.semantic_digest,
                archive_sha256=archive.archive_sha256,
            )
        if expected_revision is None:
            raise _AdapterStaleError("mutation request lacks expected revision")
        mutation_trust = self._trusted_mutation(trust)
        if isinstance(command, RegisterSourceCommand):
            source = register_source(
                self._workspace,
                command.source,
                trust=mutation_trust,
                material_path=command.material_path,
                expected_revision=expected_revision,
            )
            return AdapterOutcome(
                operation="register_source",
                entity_id=source.id,
                entity_status="current",
            )
        if isinstance(command, RecordEvidenceCommand):
            evidence = record_evidence(
                self._workspace,
                command.evidence,
                trust=mutation_trust,
                quote_payload=command.quote_payload,
                expected_revision=expected_revision,
            )
            return AdapterOutcome(
                operation="record_evidence",
                entity_id=evidence.id,
                entity_status="candidate",
            )
        if isinstance(command, ProposeCommand):
            proposal = propose_replacement(
                self._workspace,
                trust=mutation_trust,
                delta_id=command.delta_id,
                target_owner_role=command.target_owner_role,
                allowed_confirmer_roles=command.allowed_confirmer_roles,
                target_path=command.target_path,
                expected_target_digest=command.expected_target_digest,
                replacement_body=command.replacement_body,
                evidence_ids=command.evidence_ids,
                rationale=command.rationale,
                expected_revision=expected_revision,
            )
            return AdapterOutcome(
                operation="propose",
                entity_id=proposal.delta_id,
                entity_status=proposal.status,
                target_path=proposal.target_path,
            )
        if isinstance(command, ConfirmCommand):
            proposal = confirm_proposal(
                self._workspace,
                command.delta_id,
                trust=mutation_trust,
                confirmed_at=command.confirmed_at,
                expected_revision=expected_revision,
            )
            return AdapterOutcome(
                operation="confirm",
                entity_id=proposal.delta_id,
                entity_status=proposal.status,
                target_path=proposal.target_path,
            )
        if isinstance(command, UpdateSessionCommand):
            state = update_session_state(
                self._workspace,
                trust=mutation_trust,
                stage=command.stage,
                last_delta_id=command.last_delta_id,
                open_question_ids=command.open_question_ids,
                next_mission=command.next_mission,
                expected_revision=expected_revision,
            )
            return AdapterOutcome(
                operation="update_session",
                entity_id=state.last_delta_id,
                entity_status="candidate",
            )
        if isinstance(command, WithdrawSourceCommand):
            source = withdraw_source(
                self._workspace,
                command.source_id,
                trust=mutation_trust,
                withdrawn_at=command.withdrawn_at,
                expected_revision=expected_revision,
            )
            return AdapterOutcome(
                operation="withdraw_source",
                entity_id=source.id,
                entity_status="withdrawn",
            )
        raise AssertionError("unreachable adapter command")

    def execute(
        self,
        request: AdapterRequest,
        *,
        trust: AuthoringTrustContext | None = None,
    ) -> AdapterResponse:
        """Execute one validated request and return a redacted structured response."""

        try:
            self._check_request_anchor(request)
            outcome = self._dispatch(request, trust)
            session = self._snapshot()
            return AdapterResponse(
                format="ontowiz-adapter-response",
                format_version=1,
                request_id=request.request_id,
                workspace_id=self.workspace_id,
                status="ok",
                session=session,
                outcome=outcome,
            )
        except AuthorityClientError:
            # A transport/config/protocol failure from the keyless authority client.
            # It survives the kernel's provider-call wrapping points (distinct type +
            # narrow pass-throughs) and maps to the stable, redacted code here — never
            # collapsed into E_AUTHORIZATION (reachable host refused) or E_VALIDATION.
            return self._error(
                request.request_id,
                "E_AUTHORITY_UNAVAILABLE",
                "The authority host is unprovisioned or unreachable.",
            )
        except _AdapterWorkspaceMismatchError:
            return self._error(
                request.request_id,
                "E_WORKSPACE_MISMATCH",
                "The request workspace does not match the open session.",
            )
        except _AdapterStaleError:
            return self._error(
                request.request_id,
                "E_STALE",
                "The request is stale; resume from verified disk state.",
            )
        except (_AdapterTrustError, AuthorizationError):
            return self._error(
                request.request_id,
                "E_AUTHORIZATION",
                "External authorization was missing, invalid, stale, or mismatched.",
            )
        except (StaleProposalError, AuthoringConflictError):
            return self._error(
                request.request_id,
                "E_CONFLICT",
                "The requested candidate change conflicts with current state.",
            )
        except (AuthoringError, WorkspaceError, ArchiveError, ValidationError):
            return self._error(
                request.request_id,
                "E_VALIDATION",
                "The candidate operation failed closed validation.",
            )
        except OSError:
            return self._error(
                request.request_id,
                "E_OPERATION_FAILED",
                "The adapter operation could not be completed safely.",
            )

    def execute_json(
        self,
        payload: bytes | str,
        *,
        trust: AuthoringTrustContext | None = None,
    ) -> bytes:
        """Parse strict JSON, execute it, and serialize only the redacted response."""

        try:
            request = _load_request(payload)
        except (UnicodeError, ValueError, TypeError, ValidationError, json.JSONDecodeError):
            return adapter_response_bytes(
                self._error(
                    "invalid",
                    "E_REQUEST_INVALID",
                    "The adapter request is malformed or unsupported.",
                )
            )
        return adapter_response_bytes(self.execute(request, trust=trust))

    def _error(
        self,
        request_id: str,
        code: AdapterErrorCode,
        message: str,
    ) -> AdapterResponse:
        return AdapterResponse(
            format="ontowiz-adapter-response",
            format_version=1,
            request_id=request_id,
            workspace_id=self.workspace_id,
            status="error",
            error=AdapterError(code=code, message=message),
        )


__all__ = [
    "AdapterCommand",
    "AdapterError",
    "AdapterErrorCode",
    "AdapterOperation",
    "AdapterOutcome",
    "AdapterQuestion",
    "AdapterRequest",
    "AdapterResponse",
    "AdapterSession",
    "AdapterSessionSnapshot",
    "AdapterValidationSnapshot",
    "ConfirmCommand",
    "PackageCommand",
    "ProposeCommand",
    "RecordEvidenceCommand",
    "RegisterSourceCommand",
    "ResumeCommand",
    "UpdateSessionCommand",
    "ValidateCommand",
    "WithdrawSourceCommand",
    "adapter_response_bytes",
]
