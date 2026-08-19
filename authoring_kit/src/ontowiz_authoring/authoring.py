"""Evidence-anchored candidate authoring state transitions."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import stat
import time
import unicodedata
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal, Protocol, TypeAlias, overload

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from ontowiz_spec import (
    ArchiveEntry,
    CandidateArtifact,
    CandidatePackManifest,
    DecisionContract,
    EvidenceRef,
    PublicEvalCase,
    PublicSuite,
    SourceRecord,
    SourceStatus,
)

from .authority_errors import AuthorityClientError
from .workspace import (
    Workspace,
    WorkspaceError,
    _atomic_write,
    _canonical_json,
    _load_canonical_model,
    _read_control_file,
    _SourceRegister,
)

_SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"
_SAFE_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$"
_PACK_ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,62}$"
_DELTA_PATTERN = r"^DELTA-[A-Za-z0-9][A-Za-z0-9_-]{0,121}$"
_TARGET_PATTERN = (
    r"^pack/(?:pack\.yaml|(?:scope|ontology|metrics|methods|policies|retrieval|"
    r"workflows|tools|evaluations|governance)/"
    r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:yaml|json))$"
)
_MATERIAL_PATH_PATTERN = r"^sources/inbox/[A-Za-z0-9][A-Za-z0-9._-]*$"
_RULE_KINDS = frozenset({"decision_heuristic", "override_rule", "guardrail"})
_MAX_PACK_DOCUMENTS = 256
_MAX_TOTAL_INPUT_BYTES = 4_194_304
_MAX_DOCUMENT_NODES = 20_000
_MAX_TEXT_CHARS = 262_144
_MAX_QUESTIONS = 64
_MAX_PROMPT_CHARS = 2_000
_LOCK_TIMEOUT_SECONDS = 5.0


def _reject_reserved_id(value: str) -> str:
    if re.fullmatch(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])", value):
        raise ValueError("reserved identifier")
    return value


NonBlank = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=16_384),
]
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
Mission: TypeAlias = Literal["discover", "scenario", "challenge", "ratify"]
WorkspaceRef: TypeAlias = Workspace | str | Path
AuthoringOperation: TypeAlias = Literal[
    "install_authority",
    "register_source",
    "update_source",
    "withdraw_source",
    "record_evidence",
    "propose",
    "confirm",
    "update_session",
]


class AuthoringError(RuntimeError):
    """Base error for candidate authoring operations."""


class AuthoringConflictError(AuthoringError):
    """Raised when optimistic state or an idempotency key conflicts."""


class AuthoringValidationError(AuthoringError):
    """Raised when rights, evidence, or candidate contracts are invalid."""


class AuthorizationError(AuthoringError):
    """Raised when a principal lacks a governed workspace capability."""


class StaleProposalError(AuthoringError):
    """Raised when optimistic target state no longer matches a proposal."""


class AuthoringAtomicError(AuthoringError):
    """Raised when durable authoring state cannot be completed."""


class PrincipalGrant(BaseModel):
    """One principal-to-role binding in the local authority record."""

    principal_id: SafeId
    roles: tuple[SafeId, ...] = Field(min_length=1)
    client_boundary: NonBlank

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def roles_are_unique_and_ordered(self) -> PrincipalGrant:
        if self.roles != tuple(sorted(set(self.roles))):
            raise ValueError("principal roles must be unique and ordered")
        return self


class AuthorityStatement(BaseModel):
    """Externally signed principal-to-role authority statement."""

    format: Literal["ontowiz-authority-statement"]
    format_version: Literal[1]
    workspace_id: PackId
    authority_revision: int = Field(ge=1)
    issued_at: datetime
    grants: tuple[PrincipalGrant, ...] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def grants_are_coherent(self) -> AuthorityStatement:
        if not _is_aware(self.issued_at):
            raise ValueError("authority issue time must be timezone-aware")
        if tuple(grant.principal_id for grant in self.grants) != tuple(
            sorted(grant.principal_id for grant in self.grants)
        ):
            raise ValueError("authority grants must be ordered by principal")
        if len({grant.principal_id for grant in self.grants}) != len(self.grants):
            raise ValueError("authority grants contain duplicate principals")
        return self


class SignedAuthority(BaseModel):
    """Authority statement and detached Ed25519 signature."""

    statement: AuthorityStatement
    statement_digest: Sha256
    signature: str = Field(pattern=r"^[0-9a-f]{128}$")
    trust_key_id: Sha256

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def statement_digest_matches(self) -> SignedAuthority:
        if _digest(_authority_bytes(self.statement)) != self.statement_digest:
            raise ValueError("authority statement digest mismatch")
        return self


class AuthorityHighWater(BaseModel):
    """Externally protected authority key and monotonic state."""

    format: Literal["ontowiz-authority-high-water"]
    format_version: Literal[1]
    workspace_id: PackId
    trust_key_id: Sha256
    authority_public_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    authority_revision: int = Field(ge=0)
    authority_digest: Sha256 | None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def key_and_revision_are_coherent(self) -> AuthorityHighWater:
        if _digest(bytes.fromhex(self.authority_public_key)) != self.trust_key_id:
            raise ValueError("authority high-water key digest mismatch")
        if (self.authority_revision == 0) != (self.authority_digest is None):
            raise ValueError("authority high-water revision/digest mismatch")
        return self


class OperationCredential(BaseModel):
    """Operation-bound actor credential issued by a trusted host."""

    format: Literal["ontowiz-operation-credential"]
    format_version: Literal[1]
    workspace_id: PackId
    principal_id: SafeId
    roles: tuple[SafeId, ...] = Field(min_length=1)
    client_boundary: NonBlank
    authority_revision: int = Field(ge=0)
    authority_digest: Sha256 | None
    trust_key_id: Sha256
    intent_digest: Sha256
    nonce: SafeId
    issued_at: datetime
    expires_at: datetime
    actor_key_id: Sha256
    proof_signature: str = Field(pattern=r"^[0-9a-f]{128}$")

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def credential_is_coherent(self) -> OperationCredential:
        if self.roles != tuple(sorted(set(self.roles))):
            raise ValueError("credential roles must be unique and ordered")
        if not _is_aware(self.issued_at) or not _is_aware(self.expires_at):
            raise ValueError("credential times must be timezone-aware")
        if self.expires_at <= self.issued_at:
            raise ValueError("credential expiry must follow issuance")
        if (self.authority_revision == 0) != (self.authority_digest is None):
            raise ValueError("credential authority revision/digest mismatch")
        return self


class AuthoringIntent(BaseModel):
    """Exact public operation identity an external host may authorize."""

    format: Literal["ontowiz-authoring-intent"]
    format_version: Literal[1]
    operation: AuthoringOperation
    workspace_id: PackId
    expected_revision: int | None = Field(ge=0)
    request: dict[str, JsonValue]
    intent_digest: Sha256

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def digest_is_exact(self) -> AuthoringIntent:
        body = self.model_dump(mode="json", exclude={"intent_digest"})
        if _digest(_canonical_json(body)) != self.intent_digest:
            raise ValueError("authoring intent digest mismatch")
        return self


class ActorCapability(BaseModel):
    """Authenticated actor result returned only by the trusted provider."""

    format: Literal["ontowiz-authenticated-actor"]
    format_version: Literal[1]
    workspace_id: PackId
    principal_id: SafeId
    roles: tuple[SafeId, ...] = Field(min_length=1)
    client_boundary: NonBlank
    authority_revision: int = Field(ge=0)
    authority_digest: Sha256 | None
    trust_key_id: Sha256
    intent_digest: Sha256
    credential_nonce: SafeId

    model_config = ConfigDict(extra="forbid", frozen=True)


class JournalAttestation(BaseModel):
    """Opaque provider signature or MAC over a canonical journal identity."""

    format: Literal["ontowiz-journal-attestation"]
    format_version: Literal[1]
    provider_id: SafeId
    key_id: Sha256
    value: str = Field(pattern=r"^[0-9a-f]{64,512}$")

    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthoringTransactionChange(BaseModel):
    """One sorted before/after digest binding in provider transaction state."""

    kind: Literal[
        "authority",
        "source_register",
        "material_bindings",
        "evidence",
        "proposal",
        "session",
        "target",
        "revision",
    ]
    entity_id: SafeId | None = None
    before_digest: Sha256 | None
    after_digest: Sha256

    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthoringTransactionIdentity(BaseModel):
    """Canonical identity reserved atomically outside the authoring workspace."""

    format: Literal["ontowiz-provider-transaction"]
    format_version: Literal[1]
    workspace_id: PackId
    transaction_id: SafeId
    operation: AuthoringOperation
    revision_before: int = Field(ge=0)
    revision_after: int = Field(ge=1)
    actor_principal: SafeId
    intent_digest: Sha256
    credential_nonce: SafeId
    credential_digest: Sha256
    trust_key_id: Sha256
    authority_revision: int = Field(ge=0)
    authority_digest: Sha256 | None
    delta_id: SafeId | None = None
    target_path: str | None = None
    changes: tuple[AuthoringTransactionChange, ...] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def transaction_is_coherent(self) -> AuthoringTransactionIdentity:
        if self.revision_after != self.revision_before + 1:
            raise ValueError("provider transaction revision must advance by one")
        if (self.authority_revision == 0) != (self.authority_digest is None):
            raise ValueError("provider transaction authority binding mismatch")
        order = tuple((change.kind, change.entity_id or "") for change in self.changes)
        if order != tuple(sorted(order)) or len(set(order)) != len(order):
            raise ValueError("provider transaction changes must be unique and sorted")
        return self


class AuthoringProviderState(BaseModel):
    """Externally protected authoring revision and pending transaction state."""

    format: Literal["ontowiz-provider-state"]
    format_version: Literal[1]
    workspace_id: PackId
    authoring_revision: int = Field(ge=0)
    pending: AuthoringTransactionIdentity | None = None
    last_finalized: AuthoringTransactionIdentity | None = None
    last_finalized_transaction_id: SafeId | None = None
    last_finalized_transaction_digest: Sha256 | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def state_is_coherent(self) -> AuthoringProviderState:
        if (
            (self.last_finalized is None)
            != (self.last_finalized_transaction_id is None)
            or (self.last_finalized is None)
            != (self.last_finalized_transaction_digest is None)
        ):
            raise ValueError("provider finalized transaction binding mismatch")
        if self.last_finalized is not None and (
            self.last_finalized.workspace_id != self.workspace_id
            or self.last_finalized.revision_after != self.authoring_revision
            or self.last_finalized.transaction_id != self.last_finalized_transaction_id
            or authoring_transaction_digest(self.last_finalized)
            != self.last_finalized_transaction_digest
        ):
            raise ValueError("provider finalized transaction identity mismatch")
        if self.pending is not None and (
            self.pending.workspace_id != self.workspace_id
            or self.pending.revision_before != self.authoring_revision
        ):
            raise ValueError("provider pending transaction high-water mismatch")
        return self


class RecoveryAuthorization(BaseModel):
    """Provider authorization for one exact pending or finalized transaction."""

    format: Literal["ontowiz-recovery-authorization"]
    format_version: Literal[1]
    workspace_id: PackId
    transaction_digest: Sha256
    status: Literal["pending", "finalized"]
    authoring_revision: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthoringTrustProvider(Protocol):
    """Trusted host boundary; implementations and secrets remain outside the workspace."""

    def authority_high_water(self, workspace_id: str) -> AuthorityHighWater:
        """Return externally protected pinned authority state."""

    def authoring_state(self, workspace_id: str) -> AuthoringProviderState:
        """Return finalized authoring revision and at most one pending transaction."""

    def authenticate_actor(
        self,
        credential: OperationCredential,
        *,
        expected_intent_digest: str,
        now: datetime,
    ) -> ActorCapability:
        """Authenticate actor and verify proof-of-possession, freshness, and nonce."""

    def authenticate_recovery(
        self,
        identity: AuthoringTransactionIdentity,
        authorization: RecoveryAuthorization,
    ) -> ActorCapability:
        """Recover the original actor from provider-held transaction state."""

    def reserve_transaction(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> None:
        """Atomically reserve the exact next authoring transaction."""

    def authorize_recovery(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> RecoveryAuthorization:
        """Authorize only the exact pending transaction or its cleanup after finalize."""

    def finalize_transaction(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> None:
        """Atomically finalize the exact pending transaction, idempotently."""

    def abort_reserved_transaction(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> None:
        """Abort only a reserved transaction proven locally unapplied and unjournaled."""

    def advance_authority(
        self,
        *,
        expected: AuthorityHighWater,
        replacement: AuthorityHighWater,
    ) -> None:
        """Atomically compare-and-advance monotonic external authority state."""


@dataclass(frozen=True, slots=True)
class AuthoringTrustContext:
    """Trusted provider plus one caller-supplied operation credential."""

    provider: AuthoringTrustProvider
    credential: OperationCredential


class Proposal(BaseModel):
    """A full-document replacement awaiting an authorized confirmation."""

    format: Literal["ontowiz-full-document-proposal"]
    format_version: Literal[2]
    workspace_id: PackId
    workspace_revision: int = Field(ge=0)
    delta_id: str = Field(pattern=_DELTA_PATTERN)
    proposer_principal: SafeId
    proposer_authority_digest: Sha256
    client_boundary: NonBlank
    target_owner_role: SafeId
    allowed_confirmer_roles: tuple[SafeId, ...] = Field(min_length=1)
    target_path: str
    expected_target_digest: Sha256 | None
    replacement_body: dict[str, JsonValue]
    replacement_digest: Sha256
    evidence_ids: tuple[SafeId, ...] = Field(min_length=1)
    rationale: NonBlank
    status: Literal["proposed", "confirmed"]
    confirmer_principal: SafeId | None = None
    confirmer_role: SafeId | None = None
    confirmed_at: datetime | None = None
    applied_from_digest: Sha256 | None = None
    applied_to_digest: Sha256 | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("target_path")
    @classmethod
    def target_is_canonical_pack_path(cls, value: str) -> str:
        if re.fullmatch(_TARGET_PATTERN, value) is None:
            raise ValueError("proposal target is not a canonical pack document")
        try:
            ArchiveEntry(
                path=value,
                role="candidate-document",
                media_type="application/json",
                byte_count=0,
                sha256="sha256:" + "0" * 64,
            )
        except ValidationError as exc:
            raise ValueError("proposal target is not portable") from exc
        return value

    @model_validator(mode="after")
    def body_and_status_are_coherent(self) -> Proposal:
        if self.allowed_confirmer_roles != tuple(sorted(set(self.allowed_confirmer_roles))):
            raise ValueError("allowed confirmer roles must be unique and ordered")
        if _digest(_canonical_json(self.replacement_body)) != self.replacement_digest:
            raise ValueError("replacement body digest mismatch")
        confirmation = (
            self.confirmer_principal,
            self.confirmer_role,
            self.confirmed_at,
            self.applied_from_digest,
            self.applied_to_digest,
        )
        if self.status == "proposed" and any(value is not None for value in confirmation):
            raise ValueError("proposed replacement cannot contain confirmation fields")
        if self.status == "confirmed":
            required = (
                self.confirmer_principal,
                self.confirmer_role,
                self.confirmed_at,
                self.applied_to_digest,
            )
            if any(value is None for value in required):
                raise ValueError("confirmed replacement requires complete confirmation fields")
            if not _is_aware(self.confirmed_at):
                raise ValueError("confirmation time must be timezone-aware")
            if self.confirmer_role not in self.allowed_confirmer_roles:
                raise ValueError("recorded confirmer role was not allowed")
            if self.applied_to_digest != self.replacement_digest:
                raise ValueError("confirmed replacement digest differs from applied digest")
            if self.expected_target_digest is None:
                if self.applied_from_digest is not None:
                    raise ValueError("created target cannot claim a prior digest")
            elif self.applied_from_digest != self.expected_target_digest:
                raise ValueError("replacement prior digest differs from expected digest")
        return self


class SessionState(BaseModel):
    """Explicit resumable state bound to one workspace revision."""

    format: Literal["ontowiz-authoring-session"]
    format_version: Literal[2]
    workspace_id: PackId
    revision: int = Field(ge=0)
    sequence: int = Field(ge=0)
    stage: Stage
    last_delta_id: SafeId | None = None
    open_question_ids: tuple[SafeId, ...] = ()
    next_mission: Mission

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def questions_are_unique_and_ordered(self) -> SessionState:
        if self.open_question_ids != tuple(sorted(set(self.open_question_ids))):
            raise ValueError("open question ids must be unique and ordered")
        return self


class GapQuestion(BaseModel):
    """One deterministic owned gap emitted from validated bounded state."""

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
    prompt: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=_MAX_PROMPT_CHARS,
        ),
    ]
    resolves: tuple[NonBlank, ...] = Field(min_length=1, max_length=16)

    model_config = ConfigDict(extra="forbid", frozen=True)


class AuthoringValidationReport(BaseModel):
    source_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    proposal_count: int = Field(ge=0)
    confirmed_proposals: int = Field(ge=0)
    pack_document_count: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid", frozen=True)


class _QuotePayload(BaseModel):
    evidence_id: SafeId
    payload: NonBlank
    digest: Sha256

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def digest_matches_payload(self) -> _QuotePayload:
        if _quote_digest(self.payload) != self.digest:
            raise ValueError("quote payload digest mismatch")
        return self


class _EvidenceDocument(BaseModel):
    format: Literal["ontowiz-extracted-evidence"]
    format_version: Literal[2]
    source_id: SafeId
    evidence: tuple[EvidenceRef, ...] = ()
    quotes: tuple[_QuotePayload, ...] = ()

    model_config = ConfigDict(extra="forbid", frozen=True)


class _RevisionState(BaseModel):
    format: Literal["ontowiz-authoring-revision"]
    format_version: Literal[2]
    workspace_id: PackId
    revision: int = Field(ge=0)
    session_sequence: int = Field(ge=0)
    session_digest: Sha256 | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)


class _MaterialBinding(BaseModel):
    source_id: SafeId
    relative_path: str = Field(pattern=_MATERIAL_PATH_PATTERN)
    checksum: Sha256

    model_config = ConfigDict(extra="forbid", frozen=True)


class _MaterialBindings(BaseModel):
    format: Literal["ontowiz-source-material-bindings"]
    format_version: Literal[1]
    workspace_id: PackId
    bindings: tuple[_MaterialBinding, ...] = ()

    model_config = ConfigDict(extra="forbid", frozen=True)


_ChangeKind: TypeAlias = Literal[
    "authority",
    "source_register",
    "material_bindings",
    "evidence",
    "proposal",
    "session",
    "target",
    "revision",
]


class _JournalChange(BaseModel):
    kind: _ChangeKind
    entity_id: SafeId | None = None
    before_digest: Sha256 | None
    before_stage_digest: Sha256 | None
    after_digest: Sha256
    stage_digest: Sha256

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def identity_is_coherent(self) -> _JournalChange:
        needs_id = self.kind in {"source_register", "evidence", "proposal"}
        if needs_id != (self.entity_id is not None):
            raise ValueError("journal change identity mismatch")
        if self.before_digest != self.before_stage_digest:
            raise ValueError("journal before-stage digest mismatch")
        if self.after_digest != self.stage_digest:
            raise ValueError("journal stage digest differs from after digest")
        return self


class _TransactionJournal(BaseModel):
    format: Literal["ontowiz-authoring-transaction"]
    format_version: Literal[5]
    operation: AuthoringOperation
    transaction_id: SafeId
    workspace_id: PackId
    intent_digest: Sha256
    provider_transaction_digest: Sha256 | None
    authority_before_revision: int = Field(ge=0)
    authority_before_digest: Sha256 | None
    authority_after_revision: int = Field(ge=0)
    authority_after_digest: Sha256 | None
    delta_id: SafeId | None = None
    target_path: str | None = None
    expected_target_digest: Sha256 | None = None
    installed_target_digest: Sha256 | None = None
    proposal_before_digest: Sha256 | None = None
    proposal_after_digest: Sha256 | None = None
    session_before_digest: Sha256 | None = None
    session_after_digest: Sha256 | None = None
    revision_before: int = Field(ge=0)
    revision_after: int = Field(ge=1)
    changes: tuple[_JournalChange, ...] = Field(min_length=1)
    phase: Literal["prepared", "applying", "committed"]

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def bindings_are_coherent(self) -> _TransactionJournal:
        if self.revision_after != self.revision_before + 1:
            raise ValueError("journal revision sequence mismatch")
        if len({(item.kind, item.entity_id) for item in self.changes}) != len(self.changes):
            raise ValueError("journal contains duplicate semantic changes")
        if (self.authority_before_revision == 0) != (self.authority_before_digest is None):
            raise ValueError("journal authority-before binding mismatch")
        if (self.authority_after_revision == 0) != (self.authority_after_digest is None):
            raise ValueError("journal authority-after binding mismatch")
        if self.operation == "install_authority":
            if self.authority_after_revision != self.authority_before_revision + 1:
                raise ValueError("authority journal must advance by one")
        elif (
            self.authority_after_revision != self.authority_before_revision
            or self.authority_after_digest != self.authority_before_digest
        ):
            raise ValueError("non-authority journal cannot advance authority")
        revision = next(
            (item for item in self.changes if item.kind == "revision"),
            None,
        )
        if revision is None:
            raise ValueError("journal does not stage a revision")
        if self.operation == "confirm":
            if (
                self.delta_id is None
                or self.target_path is None
                or self.installed_target_digest is None
                or self.proposal_after_digest is None
                or self.session_after_digest is None
            ):
                raise ValueError("confirmation journal bindings are incomplete")
            if re.fullmatch(_TARGET_PATTERN, self.target_path) is None:
                raise ValueError("confirmation target path is invalid")
            kinds = {item.kind for item in self.changes}
            if kinds != {"target", "proposal", "session", "revision"}:
                raise ValueError("confirmation journal has unexpected changes")
            proposal = next(item for item in self.changes if item.kind == "proposal")
            session = next(item for item in self.changes if item.kind == "session")
            target = next(item for item in self.changes if item.kind == "target")
            if proposal.entity_id != self.delta_id:
                raise ValueError("confirmation proposal id mismatch")
            if (
                proposal.before_digest != self.proposal_before_digest
                or proposal.after_digest != self.proposal_after_digest
                or session.before_digest != self.session_before_digest
                or session.after_digest != self.session_after_digest
                or target.before_digest != self.expected_target_digest
                or target.after_digest != self.installed_target_digest
            ):
                raise ValueError("confirmation journal digest binding mismatch")
        elif self.target_path is not None or self.installed_target_digest is not None:
            raise ValueError("non-confirmation journal cannot bind a target")
        return self


_TEST_KILL_POINT: Callable[[str], None] | None = None


def install_signed_authority(
    workspace: WorkspaceRef,
    *,
    trust: AuthoringTrustContext,
    authority: SignedAuthority,
    expected_revision: int,
) -> SignedAuthority:
    """Install a signed authority cache after an external monotonic advance."""
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        intent = _mutation_intent(
            "install_authority",
            current.manifest.workspace_id,
            expected_revision,
            {"authority": authority.model_dump(mode="json")},
        )
        actor, high_water = _authenticate_mutation(
            current,
            trust,
            intent,
            authority_optional=True,
        )
        _verify_signed_authority(current, high_water, authority)
        statement = authority.statement
        if statement.authority_revision != high_water.authority_revision + 1:
            raise AuthorizationError("authority revision must advance external high-water by one")
        declared_roles = set(current.manifest.owner_roles)
        for grant in statement.grants:
            if not set(grant.roles).issubset(declared_roles):
                raise AuthorizationError(
                    f"principal has role outside workspace authority: {grant.principal_id}"
                )
        existing = _load_authority(current, trust.provider, required=False)
        if high_water.authority_revision == 0:
            if existing is not None:
                raise AuthorizationError("authority cache exists before external authority")
        elif (
            existing is None
            or existing.statement_digest != high_water.authority_digest
            or existing.statement.authority_revision != high_water.authority_revision
        ):
            raise AuthorizationError("authority cache does not equal external high-water")
        replacement_high_water = high_water.model_copy(
            update={
                "authority_revision": statement.authority_revision,
                "authority_digest": authority.statement_digest,
            }
        )
        _commit_mutation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            authority_after=replacement_high_water,
            operation="install_authority",
            revision=revision,
            next_revision=_advance_revision(revision),
            payloads=(
                (
                    "authority",
                    None,
                    _canonical_json(authority.model_dump(mode="json")),
                ),
            ),
        )
        return authority


def get_workspace_revision(
    workspace: WorkspaceRef,
    trust_provider: AuthoringTrustProvider,
) -> int:
    """Return the recovered authoring revision."""
    with _locked_workspace(workspace, trust_provider) as current:
        return _load_revision(current).revision


def register_source(
    workspace: WorkspaceRef,
    source: SourceRecord,
    *,
    trust: AuthoringTrustContext,
    material_path: str | None = None,
    expected_revision: int | None = None,
) -> SourceRecord:
    """Register source metadata and optionally bind governed local bytes."""
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        intent = _mutation_intent(
            "register_source",
            current.manifest.workspace_id,
            expected_revision,
            {
                "source": source.model_dump(mode="json"),
                "material_path": material_path,
            },
        )
        actor, high_water = _authenticate_mutation(current, trust, intent)
        if source.status is not SourceStatus.CURRENT:
            raise AuthoringValidationError("newly registered source must be current")
        sources = _unique_sources(_load_source_register(current))
        bindings = _load_material_bindings(current)
        existing = sources.get(source.id)
        requested_binding = (
            _validate_material_for_registration(current, source, material_path)
            if material_path is not None
            else None
        )
        current_binding = bindings.get(source.id)
        if existing is not None:
            if existing == source and current_binding == requested_binding:
                return existing
            raise AuthoringConflictError(
                f"source id already has different content or binding: {source.id}"
            )
        if current_binding is not None:
            raise AuthoringConflictError(f"orphan source material binding: {source.id}")
        sources[source.id] = source
        if requested_binding is not None:
            bindings[source.id] = requested_binding
        register = _SourceRegister(
            format="ontowiz-source-register",
            format_version=1,
            sources=tuple(sources[key] for key in sorted(sources)),
        )
        payloads: list[tuple[_ChangeKind, str | None, bytes]] = [
            (
                "source_register",
                source.id,
                _canonical_json(register.model_dump(mode="json")),
            )
        ]
        if bindings or (current.root / "locks" / "source-material-bindings.json").exists():
            binding_record = _MaterialBindings(
                format="ontowiz-source-material-bindings",
                format_version=1,
                workspace_id=current.manifest.workspace_id,
                bindings=tuple(bindings[key] for key in sorted(bindings)),
            )
            payloads.append(
                (
                    "material_bindings",
                    None,
                    _canonical_json(binding_record.model_dump(mode="json")),
                )
            )
        _commit_mutation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            operation="register_source",
            revision=revision,
            next_revision=_advance_revision(revision),
            payloads=tuple(payloads),
        )
        return source


def update_source(
    workspace: WorkspaceRef,
    source: SourceRecord,
    *,
    trust: AuthoringTrustContext,
    expected_revision: int | None = None,
) -> SourceRecord:
    """Apply only an explicit full-record transition into withdrawn state."""
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        intent = _mutation_intent(
            "update_source",
            current.manifest.workspace_id,
            expected_revision,
            {"source": source.model_dump(mode="json")},
        )
        actor, high_water = _authenticate_mutation(current, trust, intent)
        sources = _unique_sources(_load_source_register(current))
        existing = sources.get(source.id)
        if existing is None:
            raise AuthoringValidationError(f"missing source: {source.id}")
        if existing == source:
            return existing
        if (
            source.status is not SourceStatus.WITHDRAWN
            or existing.status is SourceStatus.WITHDRAWN
            or _source_without_status(existing) != _source_without_status(source)
        ):
            raise AuthoringConflictError(
                "same-id source update is forbidden unless it is an explicit withdrawal"
            )
        sources[source.id] = source
        register = _SourceRegister(
            format="ontowiz-source-register",
            format_version=1,
            sources=tuple(sources[key] for key in sorted(sources)),
        )
        _commit_mutation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            operation="update_source",
            revision=revision,
            next_revision=_advance_revision(revision),
            payloads=(
                (
                    "source_register",
                    source.id,
                    _canonical_json(register.model_dump(mode="json")),
                ),
            ),
        )
        return source


def withdraw_source(
    workspace: WorkspaceRef,
    source_id: str,
    *,
    trust: AuthoringTrustContext,
    withdrawn_at: datetime,
    expected_revision: int | None = None,
) -> SourceRecord:
    """Withdraw a registered source without rewriting rights or identity."""
    if not _is_aware(withdrawn_at):
        raise AuthoringValidationError("withdrawal time must be timezone-aware")
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        intent = _mutation_intent(
            "withdraw_source",
            current.manifest.workspace_id,
            expected_revision,
            {
                "source_id": source_id,
                "withdrawn_at": withdrawn_at.isoformat(),
            },
        )
        actor, high_water = _authenticate_mutation(current, trust, intent)
        sources = _unique_sources(_load_source_register(current))
        existing = sources.get(source_id)
        if existing is None:
            raise AuthoringValidationError(f"missing source: {source_id}")
        if existing.status is SourceStatus.WITHDRAWN:
            if existing.withdrawn_at == withdrawn_at:
                return existing
            raise AuthoringConflictError(
                f"source already withdrawn at a different time: {source_id}"
            )
        data = existing.model_dump(mode="json")
        data.update({"status": "withdrawn", "withdrawn_at": withdrawn_at.isoformat()})
        withdrawn = SourceRecord.model_validate(data)
        sources[source_id] = withdrawn
        register = _SourceRegister(
            format="ontowiz-source-register",
            format_version=1,
            sources=tuple(sources[key] for key in sorted(sources)),
        )
        _commit_mutation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            operation="withdraw_source",
            revision=revision,
            next_revision=_advance_revision(revision),
            payloads=(
                (
                    "source_register",
                    source_id,
                    _canonical_json(register.model_dump(mode="json")),
                ),
            ),
        )
        return withdrawn


def record_evidence(
    workspace: WorkspaceRef,
    evidence: EvidenceRef,
    *,
    trust: AuthoringTrustContext,
    quote_payload: str | None = None,
    expected_revision: int | None = None,
) -> EvidenceRef:
    """Persist evidence only when its source, quote, and rights are valid."""
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        intent = _mutation_intent(
            "record_evidence",
            current.manifest.workspace_id,
            expected_revision,
            {
                "evidence": evidence.model_dump(mode="json"),
                "quote_payload": quote_payload,
            },
        )
        actor, high_water = _authenticate_mutation(current, trust, intent)
        sources = _unique_sources(_load_source_register(current))
        _validate_evidence(evidence, sources)
        quote = _validate_quote_payload(evidence, quote_payload)
        all_evidence, all_quotes = _load_all_evidence(current, sources)
        existing = all_evidence.get(evidence.id)
        if existing is not None:
            if existing == evidence and all_quotes.get(evidence.id) == quote:
                return existing
            raise AuthoringConflictError(
                f"evidence id already has different content: {evidence.id}"
            )
        path = _evidence_path(current, evidence.source_id)
        if path.exists():
            document = _load_evidence_document(path)
            if document.source_id != evidence.source_id:
                raise AuthoringValidationError("evidence document source id mismatch")
            records = {record.id: record for record in document.evidence}
            quotes = {item.evidence_id: item for item in document.quotes}
        else:
            records = {}
            quotes = {}
        records[evidence.id] = evidence
        if quote is not None:
            quotes[evidence.id] = quote
        updated = _EvidenceDocument(
            format="ontowiz-extracted-evidence",
            format_version=2,
            source_id=evidence.source_id,
            evidence=tuple(records[key] for key in sorted(records)),
            quotes=tuple(quotes[key] for key in sorted(quotes)),
        )
        _commit_mutation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            operation="record_evidence",
            revision=revision,
            next_revision=_advance_revision(revision),
            payloads=(
                (
                    "evidence",
                    evidence.source_id,
                    _canonical_json(updated.model_dump(mode="json")),
                ),
            ),
        )
        return evidence


def propose_replacement(
    workspace: WorkspaceRef,
    *,
    trust: AuthoringTrustContext,
    delta_id: str,
    target_owner_role: str,
    allowed_confirmer_roles: Sequence[str],
    target_path: str,
    expected_target_digest: str | None,
    replacement_body: Mapping[str, JsonValue],
    evidence_ids: Sequence[str],
    rationale: str,
    expected_revision: int | None = None,
) -> Proposal:
    """Persist a complete candidate replacement without changing its target."""
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        allowed = tuple(sorted(set(allowed_confirmer_roles)))
        evidence_id_tuple = tuple(sorted(set(evidence_ids)))
        if len(allowed) != len(allowed_confirmer_roles):
            raise AuthoringValidationError("allowed confirmer roles contain duplicates")
        if len(evidence_id_tuple) != len(evidence_ids):
            raise AuthoringValidationError("proposal contains duplicate evidence ids")
        intent = _mutation_intent(
            "propose",
            current.manifest.workspace_id,
            expected_revision,
            {
                "delta_id": delta_id,
                "target_owner_role": target_owner_role,
                "allowed_confirmer_roles": list(allowed),
                "target_path": target_path,
                "expected_target_digest": expected_target_digest,
                "replacement_body": dict(replacement_body),
                "evidence_ids": list(evidence_id_tuple),
                "rationale": rationale,
            },
        )
        actor, high_water = _authenticate_mutation(current, trust, intent)
        if actor.authority_digest is None:
            raise AuthorizationError("proposal actor has no installed authority")
        owner_roles = set(current.manifest.owner_roles)
        if target_owner_role not in owner_roles:
            raise AuthorizationError("target owner role is not declared by the workspace")
        if not allowed or not set(allowed).issubset(owner_roles):
            raise AuthorizationError("allowed confirmer roles exceed workspace authority")
        if target_owner_role not in allowed:
            raise AuthorizationError("target owner role must be an allowed confirmer role")
        body = dict(replacement_body)
        _assert_candidate_only(body)
        _validate_target_document(target_path, body)
        _validate_evidence_ids(
            current,
            evidence_id_tuple,
            client_boundary=actor.client_boundary,
        )
        _assert_target_precondition(
            current.root / target_path,
            expected_target_digest,
            target_path,
        )
        replacement_bytes = _canonical_json(body)
        path = _proposal_path(current, delta_id)
        existing = _load_proposal_path(current, path) if path.exists() else None
        proposal = Proposal(
            format="ontowiz-full-document-proposal",
            format_version=2,
            workspace_id=current.manifest.workspace_id,
            workspace_revision=(
                existing.workspace_revision if existing is not None else revision.revision
            ),
            delta_id=delta_id,
            proposer_principal=actor.principal_id,
            proposer_authority_digest=actor.authority_digest,
            client_boundary=actor.client_boundary,
            target_owner_role=target_owner_role,
            allowed_confirmer_roles=allowed,
            target_path=target_path,
            expected_target_digest=expected_target_digest,
            replacement_body=body,
            replacement_digest=_digest(replacement_bytes),
            evidence_ids=evidence_id_tuple,
            rationale=rationale,
            status="proposed",
        )
        if existing is not None:
            if existing == proposal:
                return existing
            raise AuthoringConflictError(
                f"proposal id already has different content: {proposal.delta_id}"
            )
        _commit_mutation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            operation="propose",
            revision=revision,
            next_revision=_advance_revision(revision),
            payloads=(
                (
                    "proposal",
                    proposal.delta_id,
                    _canonical_json(proposal.model_dump(mode="json")),
                ),
            ),
            delta_id=proposal.delta_id,
            proposal_after_digest=_digest(_canonical_json(proposal.model_dump(mode="json"))),
        )
        return proposal


def load_proposal(
    workspace: WorkspaceRef,
    delta_id: str,
    trust_provider: AuthoringTrustProvider,
) -> Proposal:
    with _locked_workspace(workspace, trust_provider) as current:
        return _load_proposal_path(current, _proposal_path(current, delta_id))


def _confirmation_session_after(
    workspace: Workspace,
    revision: _RevisionState,
    delta_id: str,
) -> SessionState:
    session = _load_session_optional(workspace)
    if session is None:
        session = SessionState(
            format="ontowiz-authoring-session",
            format_version=2,
            workspace_id=workspace.manifest.workspace_id,
            revision=revision.revision,
            sequence=revision.session_sequence,
            stage="discover",
            next_mission="discover",
        )
    else:
        _validate_session(workspace, session, revision)
    return SessionState(
        format="ontowiz-authoring-session",
        format_version=2,
        workspace_id=workspace.manifest.workspace_id,
        revision=revision.revision + 1,
        sequence=revision.session_sequence + 1,
        stage=session.stage,
        last_delta_id=delta_id,
        open_question_ids=(),
        next_mission=session.next_mission,
    )


def _confirmation_plan(
    current: Workspace,
    revision: _RevisionState,
    delta_id: str,
    confirmed_at: datetime,
    expected_revision: int | None,
) -> tuple[Proposal, SessionState | None, AuthoringIntent]:
    proposal = _load_proposal_path(current, _proposal_path(current, delta_id))
    advanced_session = (
        _confirmation_session_after(current, revision, delta_id)
        if proposal.status == "proposed"
        else None
    )
    request: dict[str, object] = {
        "delta_id": delta_id,
        "confirmed_at": confirmed_at.isoformat(),
    }
    if advanced_session is not None:
        request["session"] = advanced_session.model_dump(mode="json")
    intent = prepare_authoring_intent(
        "confirm",
        current.manifest.workspace_id,
        expected_revision,
        request,
    )
    return proposal, advanced_session, intent


def prepare_confirmation_intent(
    workspace: WorkspaceRef,
    trust_provider: AuthoringTrustProvider,
    *,
    delta_id: str,
    confirmed_at: datetime,
    expected_revision: int | None,
) -> AuthoringIntent:
    """Prepare the exact confirmation identity from verified disk/provider state."""

    if not _is_aware(confirmed_at):
        raise AuthoringValidationError("confirmation time must be timezone-aware")
    with _locked_workspace(workspace, trust_provider) as current:
        revision = _check_revision(current, expected_revision)
        _, _, intent = _confirmation_plan(
            current,
            revision,
            delta_id,
            confirmed_at,
            expected_revision,
        )
        return intent


def confirm_proposal(
    workspace: WorkspaceRef,
    delta_id: str,
    *,
    trust: AuthoringTrustContext,
    confirmed_at: datetime,
    expected_revision: int | None = None,
) -> Proposal:
    """Confirm through a recoverable full-document transaction."""
    if not _is_aware(confirmed_at):
        raise AuthoringValidationError("confirmation time must be timezone-aware")
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        proposal, advanced_session, prepared_intent = _confirmation_plan(
            current,
            revision,
            delta_id,
            confirmed_at,
            expected_revision,
        )
        actor, high_water = _authenticate_mutation(
            current,
            trust,
            prepared_intent.intent_digest,
        )
        _validate_confirmation_actor(proposal, actor)
        target = current.root / proposal.target_path
        if proposal.status == "confirmed":
            target_bytes, target_body = _load_target(target)
            if (
                proposal.confirmer_principal == actor.principal_id
                and proposal.confirmed_at == confirmed_at
                and _digest(target_bytes) == proposal.replacement_digest
                and target_body == proposal.replacement_body
            ):
                return proposal
            raise AuthoringConflictError(
                "proposal was already confirmed with different confirmation"
            )
        if advanced_session is None:
            raise AuthoringAtomicError("confirmation session plan is missing")
        authority = _load_authority(current, trust.provider)
        if proposal.proposer_authority_digest != authority.statement_digest:
            raise AuthorizationError("proposal proposer authority is no longer current")
        _validate_evidence_ids(
            current,
            proposal.evidence_ids,
            client_boundary=proposal.client_boundary,
            confirmed_at=confirmed_at,
        )
        _assert_target_precondition(
            target,
            proposal.expected_target_digest,
            proposal.target_path,
        )
        replacement_bytes = _canonical_json(proposal.replacement_body)
        if _digest(replacement_bytes) != proposal.replacement_digest:
            raise AuthoringValidationError("proposal replacement digest drift")
        _assert_candidate_only(proposal.replacement_body)
        _validate_target_document(
            proposal.target_path,
            proposal.replacement_body,
        )
        confirmed_data = proposal.model_dump(mode="json")
        confirmed_data.update(
            {
                "status": "confirmed",
                "confirmer_principal": actor.principal_id,
                "confirmer_role": proposal.target_owner_role,
                "confirmed_at": confirmed_at.isoformat(),
                "applied_from_digest": proposal.expected_target_digest,
                "applied_to_digest": proposal.replacement_digest,
            }
        )
        confirmed = Proposal.model_validate(confirmed_data)
        _commit_confirmation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            proposal=proposal,
            confirmed=confirmed,
            replacement_bytes=replacement_bytes,
            revision=revision,
            session=advanced_session,
        )
        return confirmed


def load_session_state(
    workspace: WorkspaceRef,
    trust_provider: AuthoringTrustProvider,
) -> SessionState:
    with _locked_workspace(workspace, trust_provider) as current:
        revision = _load_revision(current)
        state = _load_session_optional(current)
        if state is None:
            if revision.session_digest is not None or revision.session_sequence != 0:
                raise AuthoringValidationError("revision anchor detects deleted session state")
            return SessionState(
                format="ontowiz-authoring-session",
                format_version=2,
                workspace_id=current.manifest.workspace_id,
                revision=revision.revision,
                sequence=revision.session_sequence,
                stage="discover",
                next_mission="discover",
            )
        _validate_session(current, state, revision)
        return state


def update_session_state(
    workspace: WorkspaceRef,
    *,
    trust: AuthoringTrustContext,
    stage: Stage,
    last_delta_id: str | None,
    open_question_ids: Sequence[str],
    next_mission: Mission,
    expected_revision: int,
) -> SessionState:
    """Persist bounded resume state under mandatory revision CAS."""
    with _locked_workspace(workspace, trust.provider) as current:
        revision = _check_revision(current, expected_revision)
        question_ids = tuple(sorted(set(open_question_ids)))
        if len(question_ids) != len(open_question_ids):
            raise AuthoringValidationError("session contains duplicate question ids")
        intent = _mutation_intent(
            "update_session",
            current.manifest.workspace_id,
            expected_revision,
            {
                "stage": stage,
                "last_delta_id": last_delta_id,
                "open_question_ids": list(question_ids),
                "next_mission": next_mission,
            },
        )
        actor, high_water = _authenticate_mutation(current, trust, intent)
        if last_delta_id is not None:
            proposal = _load_proposal_path(
                current,
                _proposal_path(current, last_delta_id),
            )
            if proposal.workspace_id != current.manifest.workspace_id:
                raise AuthoringValidationError("session delta belongs to another workspace")
        current_ids = {question.id for question in _compile_questions_under_lock(current)}
        stale = set(question_ids) - current_ids
        if stale:
            raise AuthoringValidationError(
                f"session references non-current questions: " f"{', '.join(sorted(stale))}"
            )
        state = SessionState(
            format="ontowiz-authoring-session",
            format_version=2,
            workspace_id=current.manifest.workspace_id,
            revision=revision.revision + 1,
            sequence=revision.session_sequence + 1,
            stage=stage,
            last_delta_id=last_delta_id,
            open_question_ids=question_ids,
            next_mission=next_mission,
        )
        session_payload = _canonical_json(state.model_dump(mode="json"))
        next_revision = _RevisionState(
            format="ontowiz-authoring-revision",
            format_version=2,
            workspace_id=current.manifest.workspace_id,
            revision=revision.revision + 1,
            session_sequence=state.sequence,
            session_digest=_digest(session_payload),
        )
        _commit_mutation(
            current,
            trust=trust,
            actor=actor,
            high_water=high_water,
            operation="update_session",
            revision=revision,
            next_revision=next_revision,
            payloads=(("session", None, session_payload),),
            session_before_digest=_existing_digest(_session_path(current)),
            session_after_digest=_digest(session_payload),
        )
        return state


def compile_questions(
    workspace: WorkspaceRef,
    trust_provider: AuthoringTrustProvider,
) -> tuple[GapQuestion, ...]:
    """Compile a bounded, schema-valid, stable question set."""
    with _locked_workspace(workspace, trust_provider) as current:
        return _compile_questions_under_lock(current)


def _validate_authoring_locked(current: Workspace) -> AuthoringValidationReport:
    sources = _unique_sources(_load_source_register(current))
    evidence, _ = _load_all_evidence(current, sources)
    proposals = [
        _load_proposal_path(current, path)
        for path in sorted((current.root / "authoring" / "proposals").glob("DELTA-*.yaml"))
    ]
    confirmed = 0
    for proposal in proposals:
        _validate_evidence_ids(
            current,
            proposal.evidence_ids,
            client_boundary=proposal.client_boundary,
            confirmed_at=proposal.confirmed_at,
        )
        target = current.root / proposal.target_path
        if proposal.status == "proposed" and proposal.expected_target_digest is None:
            if target.exists():
                raise StaleProposalError(
                    f"new proposal target already exists: {proposal.target_path}"
                )
            continue
        target_bytes, target_body = _load_target(target)
        expected = (
            proposal.replacement_digest
            if proposal.status == "confirmed"
            else proposal.expected_target_digest
        )
        if _digest(target_bytes) != expected:
            raise StaleProposalError(f"proposal target is stale: {proposal.target_path}")
        if proposal.status == "confirmed":
            if target_body != proposal.replacement_body:
                raise AuthoringValidationError(
                    "confirmed target differs from replacement body"
                )
            confirmed += 1
    documents = _load_pack_documents(current)
    for _relative, body in documents.items():
        for source_id in _collect_string_references(
            body,
            {"source_ids", "source_document_ids"},
        ):
            source = sources.get(source_id)
            if source is None:
                raise AuthoringValidationError(
                    f"pack references missing source: {source_id}"
                )
            if source.status is SourceStatus.WITHDRAWN:
                raise AuthoringValidationError(
                    f"pack references withdrawn source: {source_id}"
                )
        for evidence_id in _collect_string_references(body, {"evidence_refs"}):
            if evidence_id not in evidence:
                raise AuthoringValidationError(
                    f"pack references missing evidence: {evidence_id}"
                )
    session = _load_session_optional(current)
    if session is not None:
        _validate_session(current, session, _load_revision(current))
    return AuthoringValidationReport(
        source_count=len(sources),
        evidence_count=len(evidence),
        proposal_count=len(proposals),
        confirmed_proposals=confirmed,
        pack_document_count=len(documents),
    )


def _provider_free_archive_baseline_is_clean(current: Workspace) -> bool:
    root = current.root
    forbidden_files = (
        root / "locks" / "authoring-authority.json",
        root / "locks" / "authoring-revision.json",
        root / "locks" / "source-material-bindings.json",
    )
    if any(path.exists() for path in forbidden_files):
        return False
    register = _load_source_register(current)
    if register.sources:
        return False
    expected_session = _canonical_json(
        {
            "format": "ontowiz-authoring-session-state",
            "format_version": 1,
            "last_delta_id": None,
            "next_mission": "discover",
            "open_question_ids": [],
            "stage": "discover",
        }
    )
    expected_pack = _canonical_json(
        CandidatePackManifest(
            format="ontowiz-candidate-pack",
            format_version=1,
            package_kind="candidate",
            schema_target="ontowiz-spec/vNext-min",
            schema_revision=1,
            pack_id=current.manifest.workspace_id,
            pack_version="0.1.0",
            production_eligible=False,
            releasable=False,
            contains_protected_evaluations=False,
            artifact_digests=(),
            public_evaluation_suites=(
                PublicSuite.DEV,
                PublicSuite.REGRESSION,
            ),
        ).model_dump(mode="json")
    )
    if (
        _read_control_file(root / "authoring" / "session-state.yaml")
        != expected_session
        or _read_control_file(root / "pack" / "pack.yaml") != expected_pack
    ):
        return False
    portable_dynamic_roots = (
        root / "sources" / "extracted",
        root / "authoring" / "proposals",
        root / "authoring" / "decisions",
    )
    if any(any(path.iterdir()) for path in portable_dynamic_roots):
        return False
    claims = tuple((root / "sources" / "candidate-claims").iterdir())
    for claim in claims:
        if claim.name != "SRC-ARCHIVE-OMISSIONS.yaml":
            return False
        try:
            omission_bytes = _read_control_file(claim)
            omission = json.loads(omission_bytes)
            if (
                _canonical_json(omission) != omission_bytes
                or set(omission)
                != {
                    "as_of",
                    "format",
                    "format_version",
                    "omitted",
                    "source_profile",
                    "target_client_boundary",
                }
                or omission["format"] != "ontowiz-source-omissions"
                or omission["format_version"] != 1
                or omission["omitted"] != []
                or omission["source_profile"] not in {"referenced", "embedded"}
                or (
                    omission["source_profile"] == "embedded"
                )
                != (omission["target_client_boundary"] is not None)
            ):
                return False
        except (WorkspaceError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False
    if any((root / "authoring" / "sessions").iterdir()):
        return False
    return not any(
        path.is_file() and path.name != "pack.yaml"
        for path in (root / "pack").rglob("*")
    )


@dataclass(frozen=True, slots=True)
class AuthoringArchiveSnapshot:
    workspace: Workspace
    revision: int
    provider_revision: int | None
    validation: AuthoringValidationReport


@contextmanager
def locked_authoring_archive_snapshot(
    workspace: WorkspaceRef,
    trust_provider: AuthoringTrustProvider | None = None,
) -> Iterator[AuthoringArchiveSnapshot]:
    """Hold the Gate 3 lock through one provider-converged archive publication."""

    root = _workspace_root(workspace)
    _validate_workspace_and_locks(root)
    with _authoring_lock(root):
        current = _validate_workspace_and_locks(root)
        transaction_dir = current.root / "locks" / "transactions"
        has_transaction_state = transaction_dir.exists() and any(
            transaction_dir.iterdir()
        )
        if has_transaction_state:
            if trust_provider is None:
                raise AuthoringAtomicError(
                    "archive snapshot cannot recover without a trust provider"
                )
            _recover_transactions(current, trust_provider)
            current = _validate_workspace_and_locks(root)
        revision = _load_revision(current)
        provider_revision: int | None = None
        if trust_provider is None:
            if (
                revision.revision != 0
                or not _provider_free_archive_baseline_is_clean(current)
            ):
                raise AuthoringAtomicError(
                    "authored archive snapshot requires a trust provider"
                )
        else:
            _load_authority(current, trust_provider, required=False)
            provider_state = _provider_authoring_state(
                trust_provider,
                current.manifest.workspace_id,
            )
            if (
                provider_state.pending is not None
                or provider_state.authoring_revision != revision.revision
            ):
                raise AuthoringAtomicError(
                    "local and provider authoring revisions are not converged"
                )
            provider_revision = provider_state.authoring_revision
        validation = _validate_authoring_locked(current)
        snapshot = AuthoringArchiveSnapshot(
            workspace=current,
            revision=revision.revision,
            provider_revision=provider_revision,
            validation=validation,
        )
        try:
            yield snapshot
        finally:
            after = _validate_workspace_and_locks(root)
            after_revision = _load_revision(after)
            if (
                after_revision != revision
                or (
                    transaction_dir.exists()
                    and any(transaction_dir.iterdir())
                )
            ):
                raise AuthoringAtomicError(
                    "authoring state changed during archive publication"
                )
            if trust_provider is not None:
                after_provider = _provider_authoring_state(
                    trust_provider,
                    after.manifest.workspace_id,
                )
                if (
                    after_provider.pending is not None
                    or after_provider.authoring_revision != revision.revision
                ):
                    raise AuthoringAtomicError(
                        "provider state changed during archive publication"
                    )


def validate_authoring(
    workspace: WorkspaceRef,
    trust_provider: AuthoringTrustProvider,
) -> AuthoringValidationReport:
    """Validate recovered source, evidence, proposal, session, and pack state."""

    with _locked_workspace(workspace, trust_provider) as current:
        return _validate_authoring_locked(current)

def _compile_questions_under_lock(workspace: Workspace) -> tuple[GapQuestion, ...]:
    sources = _unique_sources(_load_source_register(workspace))
    current_sources = {
        source_id: source
        for source_id, source in sources.items()
        if source.status is SourceStatus.CURRENT
    }
    evidence, _ = _load_all_evidence(workspace, sources)
    documents = _load_pack_documents(workspace)
    evaluations = [
        body for relative, body in documents.items() if relative.startswith("pack/evaluations/")
    ]
    decisions = [
        body
        for relative, body in documents.items()
        if relative.startswith("pack/scope/") and "decision" in body and "action_mode" in body
    ]
    suites = {str(body.get("suite")) for body in evaluations}
    questions: dict[str, GapQuestion] = {}

    def add(question: GapQuestion) -> None:
        existing = questions.get(question.id)
        if existing is not None and existing != question:
            raise AuthoringValidationError("question digest collision")
        questions[question.id] = question
        if len(questions) > _MAX_QUESTIONS:
            raise AuthoringValidationError("question compiler output exceeds limit")

    if not current_sources:
        add(
            _question(
                workspace,
                gap_kind="source",
                preferred_roles=("steward", "rights_owner"),
                prompt="Register a current governed source for this workspace.",
                resolves=("current-source",),
            )
        )
    if not evidence:
        add(
            _question(
                workspace,
                gap_kind="evidence",
                preferred_roles=("steward", "brand_owner"),
                prompt="Record evidence anchored to a current registered source.",
                resolves=("registered-evidence",),
            )
        )
    if not decisions:
        add(
            _question(
                workspace,
                gap_kind="decision",
                preferred_roles=("brand_owner", "steward"),
                prompt=("Define the decision, applicability, human boundary, and unsafe answers."),
                resolves=("decision-contract",),
            )
        )
    for suite in ("dev", "regression"):
        if suite not in suites:
            add(
                _question(
                    workspace,
                    gap_kind="evaluation",
                    preferred_roles=("brand_owner", "steward"),
                    prompt=f"Add a candidate behavior-based {suite} evaluation.",
                    resolves=(f"{suite}-evaluation",),
                )
            )

    eval_context: set[str] = set()
    for body in evaluations:
        required_context = body.get("required_context")
        if isinstance(required_context, list):
            eval_context.update(
                reference for reference in required_context if isinstance(reference, str)
            )
    for body in documents.values():
        rule_id = body.get("id")
        if body.get("kind") not in _RULE_KINDS or not isinstance(rule_id, str):
            continue
        declared_owner = body.get("owner_role")
        if not isinstance(declared_owner, str):
            raise AuthoringValidationError(f"rule is missing owner role: {rule_id}")
        if declared_owner not in workspace.manifest.owner_roles:
            add(
                _question(
                    workspace,
                    gap_kind="authority",
                    preferred_roles=("steward",),
                    prompt=(f"Assign rule {rule_id} to an owner role declared by this workspace."),
                    resolves=(f"authority:{rule_id}",),
                )
            )
            continue
        if rule_id not in eval_context:
            add(
                _question(
                    workspace,
                    gap_kind="rule_evaluation",
                    preferred_roles=(declared_owner,),
                    prompt=f"Pair rule {rule_id} with a positive or exception evaluation.",
                    resolves=(f"rule-evaluation:{rule_id}",),
                )
            )
    return tuple(questions[key] for key in sorted(questions))


def _question(
    workspace: Workspace,
    *,
    gap_kind: Literal[
        "source",
        "evidence",
        "decision",
        "evaluation",
        "rule_evaluation",
        "authority",
    ],
    preferred_roles: Sequence[str],
    prompt: str,
    resolves: Sequence[str],
) -> GapQuestion:
    role = next(
        (candidate for candidate in preferred_roles if candidate in workspace.manifest.owner_roles),
        None,
    )
    blocking = role is None
    seed = {
        "gap_kind": gap_kind,
        "owner_role": role,
        "blocking": blocking,
        "prompt": prompt,
        "resolves": list(resolves),
    }
    suffix = hashlib.sha256(_canonical_json(seed)).hexdigest()[:16]
    question_id = f"Q-{gap_kind.upper().replace('_', '-')}-{suffix}"
    return GapQuestion(
        id=question_id,
        gap_kind=gap_kind,
        owner_role=role,
        blocking=blocking,
        prompt=prompt,
        resolves=tuple(resolves),
    )


def _load_pack_documents(workspace: Workspace) -> dict[str, dict[str, JsonValue]]:
    candidates = [
        path
        for path in sorted((workspace.root / "pack").rglob("*"))
        if path.is_file()
        and path != workspace.root / "pack" / "pack.yaml"
        and path.suffix in {".json", ".yaml"}
    ]
    if len(candidates) > _MAX_PACK_DOCUMENTS:
        raise AuthoringValidationError("pack document count exceeds compiler limit")
    documents: dict[str, dict[str, JsonValue]] = {}
    document_ids: dict[str, str] = {}
    total_bytes = 0
    total_nodes = 0
    total_text = 0
    for path in candidates:
        relative = path.relative_to(workspace.root).as_posix()
        try:
            payload, document = _load_target(path)
            total_bytes += len(payload)
            nodes, text = _measure_json(document)
        except (RecursionError, ValueError) as exc:
            raise AuthoringValidationError(
                f"pack document exceeds structural limits: {relative}"
            ) from exc
        total_nodes += nodes
        total_text += text
        if (
            total_bytes > _MAX_TOTAL_INPUT_BYTES
            or total_nodes > _MAX_DOCUMENT_NODES
            or total_text > _MAX_TEXT_CHARS
        ):
            raise AuthoringValidationError("pack input exceeds compiler work limits")
        _assert_candidate_only(document)
        _validate_target_document(relative, document)
        document_id = document.get("id")
        if not isinstance(document_id, str):
            raise AuthoringValidationError(f"pack document is missing id: {relative}")
        previous = document_ids.get(document_id)
        if previous is not None:
            raise AuthoringValidationError(
                f"duplicate pack document id: {document_id} ({previous}, {relative})"
            )
        document_ids[document_id] = relative
        documents[relative] = document
    return documents


def _measure_json(value: JsonValue) -> tuple[int, int]:
    nodes = 0
    text_chars = 0
    pending: list[JsonValue] = [value]
    while pending:
        current = pending.pop()
        nodes += 1
        if nodes > _MAX_DOCUMENT_NODES:
            raise AuthoringValidationError("pack input exceeds compiler node limit")
        if isinstance(current, dict):
            for key, child in current.items():
                text_chars += len(key)
                pending.append(child)
        elif isinstance(current, list):
            pending.extend(current)
        elif isinstance(current, str):
            text_chars += len(current)
        if text_chars > _MAX_TEXT_CHARS:
            raise AuthoringValidationError("pack input exceeds compiler text limit")
    return nodes, text_chars


def prepare_authoring_intent(
    operation: AuthoringOperation,
    workspace_id: str,
    expected_revision: int | None,
    request: Mapping[str, object],
) -> AuthoringIntent:
    """Return the exact public identity an external host must authorize."""

    body: dict[str, object] = {
        "format": "ontowiz-authoring-intent",
        "format_version": 1,
        "operation": operation,
        "workspace_id": workspace_id,
        "expected_revision": expected_revision,
        "request": dict(request),
    }
    return AuthoringIntent.model_validate(
        {**body, "intent_digest": _digest(_canonical_json(body))}
    )


def _mutation_intent(
    operation: AuthoringOperation,
    workspace_id: str,
    expected_revision: int | None,
    request: Mapping[str, object],
) -> str:
    return prepare_authoring_intent(
        operation,
        workspace_id,
        expected_revision,
        request,
    ).intent_digest


def operation_credential_bytes(credential: OperationCredential) -> bytes:
    """Return the canonical proof-of-possession payload for a credential."""
    return _canonical_json(credential.model_dump(mode="json", exclude={"proof_signature"}))


def _provider_high_water(
    provider: AuthoringTrustProvider,
    workspace_id: str,
) -> AuthorityHighWater:
    try:
        high_water = AuthorityHighWater.model_validate(provider.authority_high_water(workspace_id))
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthorizationError("trusted authority provider is unavailable") from exc
    if high_water.workspace_id != workspace_id:
        raise AuthorizationError("provider authority belongs to another workspace")
    return high_water


def _authenticate_mutation(
    workspace: Workspace,
    trust: AuthoringTrustContext,
    expected_intent_digest: str,
    *,
    authority_optional: bool = False,
) -> tuple[ActorCapability, AuthorityHighWater]:
    try:
        credential = OperationCredential.model_validate(trust.credential)
    except (ValidationError, ValueError) as exc:
        raise AuthorizationError("operation credential is invalid") from exc
    high_water = _provider_high_water(
        trust.provider,
        workspace.manifest.workspace_id,
    )
    now = datetime.now(UTC)
    if credential.workspace_id != workspace.manifest.workspace_id:
        raise AuthorizationError("operation credential belongs to another workspace")
    if credential.intent_digest != expected_intent_digest:
        raise AuthorizationError("operation credential is bound to another intent")
    if credential.trust_key_id != high_water.trust_key_id:
        raise AuthorizationError("operation credential uses another trust key")
    if (
        credential.authority_revision != high_water.authority_revision
        or credential.authority_digest != high_water.authority_digest
    ):
        raise AuthorizationError("operation credential authority is stale")
    if credential.issued_at > now or credential.expires_at <= now:
        raise AuthorizationError("operation credential is not currently valid")
    try:
        actor = ActorCapability.model_validate(
            trust.provider.authenticate_actor(
                credential,
                expected_intent_digest=expected_intent_digest,
                now=now,
            )
        )
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthorizationError("trusted provider rejected actor proof-of-possession") from exc
    expected_actor = {
        "workspace_id": credential.workspace_id,
        "principal_id": credential.principal_id,
        "roles": credential.roles,
        "client_boundary": credential.client_boundary,
        "authority_revision": credential.authority_revision,
        "authority_digest": credential.authority_digest,
        "trust_key_id": credential.trust_key_id,
        "intent_digest": credential.intent_digest,
        "credential_nonce": credential.nonce,
    }
    for field, expected in expected_actor.items():
        if getattr(actor, field) != expected:
            raise AuthorizationError("provider actor result does not match credential")
    if high_water.authority_revision == 0:
        if not authority_optional:
            raise AuthorizationError("external authority has not been installed")
        if not set(actor.roles).issubset(set(workspace.manifest.owner_roles)):
            raise AuthorizationError("bootstrap actor roles exceed workspace authority")
        return actor, high_water
    authority = _load_authority(workspace, trust.provider)
    grant = next(
        (item for item in authority.statement.grants if item.principal_id == actor.principal_id),
        None,
    )
    if grant is None:
        raise AuthorizationError("actor principal is not in current authority")
    if actor.roles != grant.roles or actor.client_boundary != grant.client_boundary:
        raise AuthorizationError("actor credential does not match current authority")
    return actor, high_water


def _validate_confirmation_actor(
    proposal: Proposal,
    actor: ActorCapability,
) -> None:
    if actor.workspace_id != proposal.workspace_id:
        raise AuthorizationError("confirmation actor belongs to another workspace")
    if actor.client_boundary != proposal.client_boundary:
        raise AuthorizationError("confirmation crosses the proposal client boundary")
    if proposal.target_owner_role not in actor.roles:
        raise AuthorizationError("confirmation actor is not the target owner")
    if not set(actor.roles).intersection(proposal.allowed_confirmer_roles):
        raise AuthorizationError("confirmation actor has no allowed confirmer role")


@overload
def _load_authority(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    *,
    required: Literal[True] = True,
) -> SignedAuthority: ...


@overload
def _load_authority(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    *,
    required: Literal[False],
) -> SignedAuthority | None: ...


def _load_authority(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    *,
    required: bool = True,
) -> SignedAuthority | None:
    high_water = _provider_high_water(provider, workspace.manifest.workspace_id)
    path = _authority_path(workspace)
    if not path.exists():
        if high_water.authority_revision != 0:
            raise AuthorizationError("authority cache is missing below external high-water")
        if required:
            raise AuthorizationError("external authority has not been installed")
        return None
    try:
        record = _load_canonical_model(path, SignedAuthority)
    except (WorkspaceError, ValidationError) as exc:
        raise AuthorizationError("signed authority cache is invalid") from exc
    _verify_signed_authority(workspace, high_water, record)
    if (
        record.statement.authority_revision != high_water.authority_revision
        or record.statement_digest != high_water.authority_digest
    ):
        raise AuthorizationError(
            "authority cache rollback or external anchor substitution detected"
        )
    return record


def _authority_path(workspace: Workspace) -> Path:
    return workspace.root / "locks" / "authoring-authority.json"


def _verify_signed_authority(
    workspace: Workspace,
    high_water: AuthorityHighWater,
    authority: SignedAuthority,
) -> None:
    if authority.statement.workspace_id != workspace.manifest.workspace_id:
        raise AuthorizationError("signed authority belongs to another workspace")
    if authority.trust_key_id != high_water.trust_key_id:
        raise AuthorizationError("signed authority uses the wrong trust key")
    try:
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(high_water.authority_public_key))
        key.verify(
            bytes.fromhex(authority.signature),
            _authority_bytes(authority.statement),
        )
    except (InvalidSignature, ValueError) as exc:
        raise AuthorizationError("signed authority signature is invalid") from exc


def _authority_bytes(statement: AuthorityStatement) -> bytes:
    return _canonical_json(statement.model_dump(mode="json"))


def _load_revision(workspace: Workspace) -> _RevisionState:
    path = workspace.root / "locks" / "authoring-revision.json"
    if not path.exists():
        return _RevisionState(
            format="ontowiz-authoring-revision",
            format_version=2,
            workspace_id=workspace.manifest.workspace_id,
            revision=0,
            session_sequence=0,
            session_digest=None,
        )
    state = _load_canonical_model(path, _RevisionState)
    if state.workspace_id != workspace.manifest.workspace_id:
        raise AuthoringValidationError("authoring revision belongs to another workspace")
    return state


def _check_revision(
    workspace: Workspace,
    expected_revision: int | None,
) -> _RevisionState:
    revision = _load_revision(workspace)
    if expected_revision is not None and expected_revision != revision.revision:
        raise AuthoringConflictError(
            f"stale workspace revision: expected {expected_revision}, " f"found {revision.revision}"
        )
    return revision


def _advance_revision(revision: _RevisionState) -> _RevisionState:
    return _RevisionState(
        format="ontowiz-authoring-revision",
        format_version=2,
        workspace_id=revision.workspace_id,
        revision=revision.revision + 1,
        session_sequence=revision.session_sequence,
        session_digest=revision.session_digest,
    )


def _load_source_register(workspace: Workspace) -> _SourceRegister:
    return _load_canonical_model(
        workspace.root / "sources" / "source-register.yaml",
        _SourceRegister,
    )


def _unique_sources(register: _SourceRegister) -> dict[str, SourceRecord]:
    sources: dict[str, SourceRecord] = {}
    for source in register.sources:
        if source.id in sources:
            raise AuthoringValidationError(f"duplicate source id: {source.id}")
        sources[source.id] = source
    if tuple(sources) != tuple(sorted(sources)):
        raise AuthoringValidationError("source register is not ordered by id")
    return sources


def _source_without_status(source: SourceRecord) -> dict[str, JsonValue]:
    data = source.model_dump(mode="json")
    data.pop("status")
    data.pop("withdrawn_at")
    return data


def _validate_material_for_registration(
    workspace: Workspace,
    source: SourceRecord,
    material_path: str,
) -> _MaterialBinding:
    if re.fullmatch(_MATERIAL_PATH_PATTERN, material_path) is None:
        raise AuthoringValidationError("source material must be a portable sources/inbox file")
    if not source.raw_transfer_allowed:
        raise AuthoringValidationError("source rights prohibit local raw material")
    path = workspace.root / material_path
    payload = _read_control_file(path)
    checksum = _digest(payload)
    if checksum != source.checksum:
        raise AuthoringValidationError("source material checksum mismatch")
    return _MaterialBinding(
        source_id=source.id,
        relative_path=material_path,
        checksum=checksum,
    )


def _load_material_bindings(workspace: Workspace) -> dict[str, _MaterialBinding]:
    path = workspace.root / "locks" / "source-material-bindings.json"
    if not path.exists():
        return {}
    record = _load_canonical_model(path, _MaterialBindings)
    if record.workspace_id != workspace.manifest.workspace_id:
        raise AuthoringValidationError("source bindings belong to another workspace")
    bindings: dict[str, _MaterialBinding] = {}
    for binding in record.bindings:
        if binding.source_id in bindings:
            raise AuthoringValidationError("duplicate source material binding")
        bindings[binding.source_id] = binding
    if tuple(bindings) != tuple(sorted(bindings)):
        raise AuthoringValidationError("source material bindings are not ordered")
    return bindings


def _rehash_material(
    workspace: Workspace,
    source: SourceRecord,
    bindings: Mapping[str, _MaterialBinding],
) -> None:
    binding = bindings.get(source.id)
    if binding is None:
        return
    if not source.raw_transfer_allowed:
        raise AuthoringValidationError("source rights no longer permit local raw material")
    payload = _read_control_file(workspace.root / binding.relative_path)
    checksum = _digest(payload)
    if checksum != binding.checksum or checksum != source.checksum:
        raise AuthoringValidationError("source material byte drift")


def _evidence_path(workspace: Workspace, source_id: str) -> Path:
    return workspace.root / "sources" / "extracted" / f"{source_id}.json"


def _load_evidence_document(path: Path) -> _EvidenceDocument:
    return _load_canonical_model(path, _EvidenceDocument)


def _load_all_evidence(
    workspace: Workspace,
    sources: Mapping[str, SourceRecord],
) -> tuple[dict[str, EvidenceRef], dict[str, _QuotePayload]]:
    evidence: dict[str, EvidenceRef] = {}
    quotes: dict[str, _QuotePayload] = {}
    for path in sorted((workspace.root / "sources" / "extracted").glob("*.json")):
        document = _load_evidence_document(path)
        if path.stem != document.source_id:
            raise AuthoringValidationError("evidence filename and source id differ")
        document_quotes = {quote.evidence_id: quote for quote in document.quotes}
        if len(document_quotes) != len(document.quotes):
            raise AuthoringValidationError("duplicate quote payload id")
        for record in document.evidence:
            if record.id in evidence:
                raise AuthoringValidationError(f"duplicate evidence id: {record.id}")
            _validate_evidence(record, sources)
            quote = document_quotes.get(record.id)
            _validate_persisted_quote(record, quote)
            evidence[record.id] = record
            if quote is not None:
                quotes[record.id] = quote
        if set(document_quotes) - {record.id for record in document.evidence}:
            raise AuthoringValidationError("orphan quote payload")
    return evidence, quotes


def _validate_evidence(
    evidence: EvidenceRef,
    sources: Mapping[str, SourceRecord],
) -> None:
    source = sources.get(evidence.source_id)
    if source is None:
        raise AuthoringValidationError(f"evidence references missing source: {evidence.source_id}")
    if source.status is not SourceStatus.CURRENT:
        raise AuthoringValidationError(
            f"evidence references withdrawn source: {evidence.source_id}"
        )
    if evidence.source_checksum != source.checksum:
        raise AuthoringValidationError("evidence source checksum mismatch")
    if evidence.permitted_use not in source.permitted_uses:
        raise AuthoringValidationError("evidence permitted use is not registered")
    if evidence.quoted and not source.quotation_allowed:
        raise AuthoringValidationError("source rights prohibit quoted evidence")
    if evidence.valid_as_of < source.source_date:
        raise AuthoringValidationError("evidence predates its registered source")
    if source.fresh_until is not None and evidence.valid_as_of > source.fresh_until:
        raise AuthoringValidationError("evidence exceeds source freshness")
    if source.retention_until is not None and evidence.valid_as_of > source.retention_until:
        raise AuthoringValidationError("evidence exceeds source retention")


def _validate_quote_payload(
    evidence: EvidenceRef,
    quote_payload: str | None,
) -> _QuotePayload | None:
    if not evidence.quoted:
        if quote_payload is not None or evidence.quote_digest is not None:
            raise AuthoringValidationError("unquoted evidence cannot carry quote material")
        return None
    if quote_payload is None or evidence.quote_digest is None:
        raise AuthoringValidationError("quoted evidence requires explicit quote payload")
    try:
        quote = _QuotePayload(
            evidence_id=evidence.id,
            payload=quote_payload,
            digest=evidence.quote_digest,
        )
    except (ValidationError, RecursionError, ValueError) as exc:
        raise AuthoringValidationError("quote payload digest mismatch") from exc
    return quote


def _validate_persisted_quote(
    evidence: EvidenceRef,
    quote: _QuotePayload | None,
) -> None:
    if evidence.quoted:
        if (
            quote is None
            or evidence.quote_digest is None
            or quote.digest != evidence.quote_digest
            or _quote_digest(quote.payload) != evidence.quote_digest
        ):
            raise AuthoringValidationError("quoted evidence payload drift")
    elif quote is not None or evidence.quote_digest is not None:
        raise AuthoringValidationError("unquoted evidence carries quote material")


def _validate_evidence_ids(
    workspace: Workspace,
    evidence_ids: Sequence[str],
    *,
    client_boundary: str,
    confirmed_at: datetime | None = None,
) -> None:
    if not evidence_ids:
        raise AuthoringValidationError("proposal requires evidence ids")
    if len(set(evidence_ids)) != len(evidence_ids):
        raise AuthoringValidationError("proposal contains duplicate evidence ids")
    sources = _unique_sources(_load_source_register(workspace))
    evidence, quotes = _load_all_evidence(workspace, sources)
    bindings = _load_material_bindings(workspace)
    confirmation_date = None
    if confirmed_at is not None:
        if not _is_aware(confirmed_at):
            raise AuthoringValidationError("confirmation time must be timezone-aware")
        confirmation_date = confirmed_at.astimezone(UTC).date()
    for evidence_id in evidence_ids:
        record = evidence.get(evidence_id)
        if record is None:
            raise AuthoringValidationError(f"proposal references missing evidence: {evidence_id}")
        source = sources[record.source_id]
        if source.client_boundary != client_boundary:
            raise AuthoringValidationError("evidence crosses the actor client boundary")
        if source.contains_personal_data and not source.personal_data_transfer_allowed:
            raise AuthoringValidationError(
                "source rights prohibit personal-data transfer for authoring"
            )
        if record.quoted:
            if not source.quotation_allowed:
                raise AuthoringValidationError("source rights prohibit quotation")
            _validate_persisted_quote(record, quotes.get(record.id))
        _rehash_material(workspace, source, bindings)
        if confirmation_date is not None:
            if confirmation_date < source.source_date:
                raise AuthoringValidationError("confirmation predates governed source")
            if source.fresh_until is not None and confirmation_date > source.fresh_until:
                raise AuthoringValidationError("source freshness expired before confirmation")
            if source.retention_until is not None and confirmation_date > source.retention_until:
                raise AuthoringValidationError("source retention expired before confirmation")


def _proposal_path(workspace: Workspace, delta_id: str) -> Path:
    if re.fullmatch(_DELTA_PATTERN, delta_id) is None:
        raise AuthoringValidationError("invalid delta id")
    return workspace.root / "authoring" / "proposals" / f"{delta_id}.yaml"


def _load_proposal_path(workspace: Workspace, path: Path) -> Proposal:
    proposal = _load_canonical_model(path, Proposal)
    if proposal.workspace_id != workspace.manifest.workspace_id:
        raise AuthoringValidationError("proposal belongs to another workspace")
    return proposal


def _load_target(path: Path) -> tuple[bytes, dict[str, JsonValue]]:
    if not path.exists():
        raise StaleProposalError(f"proposal target is missing: {path.as_posix()}")
    try:
        payload = _read_control_file(path)
        document = json.loads(payload)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise AuthoringValidationError(f"target is not canonical JSON: {path.name}") from exc
    if not isinstance(document, dict):
        raise AuthoringValidationError("canonical target must be a JSON object")
    try:
        canonical = _canonical_json(document)
    except (RecursionError, ValueError) as exc:
        raise AuthoringValidationError(f"target exceeds structural limits: {path.name}") from exc
    if canonical != payload:
        raise AuthoringValidationError(f"target is not canonical JSON: {path.name}")
    return payload, document


def _assert_target_precondition(
    target: Path,
    expected_digest: str | None,
    relative: str,
) -> None:
    if expected_digest is None:
        if target.exists():
            raise StaleProposalError(f"new proposal target already exists: {relative}")
        return
    payload, _ = _load_target(target)
    if _digest(payload) != expected_digest:
        raise StaleProposalError(f"proposal target is stale: {relative}")


def _validate_target_document(
    relative: str,
    body: Mapping[str, JsonValue],
) -> None:
    try:
        if relative == "pack/pack.yaml":
            CandidatePackManifest.model_validate(body)
        elif relative.startswith("pack/evaluations/"):
            PublicEvalCase.model_validate(body)
        elif relative.startswith("pack/scope/") and "decision" in body:
            DecisionContract.model_validate(body)
        else:
            CandidateArtifact.model_validate(body)
    except (ValidationError, RecursionError, ValueError) as exc:
        raise AuthoringValidationError(f"invalid canonical pack document: {relative}") from exc


def _assert_candidate_only(
    value: JsonValue | Mapping[str, JsonValue],
) -> None:
    pending: list[JsonValue | Mapping[str, JsonValue]] = [value]
    visited = 0
    while pending:
        current = pending.pop()
        visited += 1
        if visited > _MAX_DOCUMENT_NODES:
            raise AuthoringValidationError("candidate content exceeds structural limits")
        if isinstance(current, Mapping):
            lifecycle = current.get("lifecycle")
            if lifecycle is not None and lifecycle not in {"draft", "review"}:
                raise AuthoringValidationError("candidate-only content cannot activate or verify")
            if current.get("reviewed_by") is not None or current.get("approved_at") is not None:
                raise AuthoringValidationError(
                    "candidate-only content cannot record platform approval"
                )
            if current.get("production_eligible") is True or current.get("releasable") is True:
                raise AuthoringValidationError("candidate-only content cannot become releasable")
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)


def _collect_string_references(
    value: JsonValue,
    keys: set[str],
) -> set[str]:
    found: set[str] = set()
    pending: list[JsonValue] = [value]
    visited = 0
    while pending:
        current = pending.pop()
        visited += 1
        if visited > _MAX_DOCUMENT_NODES:
            raise AuthoringValidationError("candidate references exceed structural limits")
        if isinstance(current, dict):
            for key, child in current.items():
                if key in keys and isinstance(child, list):
                    found.update(item for item in child if isinstance(item, str))
                pending.append(child)
        elif isinstance(current, list):
            pending.extend(current)
    return found


def _session_path(workspace: Workspace) -> Path:
    directory = workspace.root / "authoring" / "sessions" / "current"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "session.yaml"


def _load_session_optional(workspace: Workspace) -> SessionState | None:
    path = workspace.root / "authoring" / "sessions" / "current" / "session.yaml"
    if not path.exists():
        return None
    state = _load_canonical_model(path, SessionState)
    if state.workspace_id != workspace.manifest.workspace_id:
        raise AuthoringValidationError("session belongs to another workspace")
    return state


def _validate_session(
    workspace: Workspace,
    state: SessionState,
    revision: _RevisionState,
) -> None:
    if state.workspace_id != workspace.manifest.workspace_id:
        raise AuthoringValidationError("session belongs to another workspace")
    if state.revision > revision.revision:
        raise AuthoringValidationError("session revision is ahead of workspace revision")
    if state.sequence != revision.session_sequence:
        raise AuthoringValidationError("session sequence replay or gap detected")
    state_digest = _digest(_canonical_json(state.model_dump(mode="json")))
    if revision.session_digest is None or state_digest != revision.session_digest:
        raise AuthoringValidationError("session digest does not match revision anchor")
    if state.last_delta_id is not None:
        proposal = _load_proposal_path(
            workspace,
            _proposal_path(workspace, state.last_delta_id),
        )
        if proposal.workspace_id != state.workspace_id:
            raise AuthoringValidationError("session delta belongs to another workspace")
    current_ids = {question.id for question in _compile_questions_under_lock(workspace)}
    stale = set(state.open_question_ids) - current_ids
    if stale:
        raise AuthoringValidationError("session contains stale question ids")


def _commit_confirmation(
    workspace: Workspace,
    *,
    trust: AuthoringTrustContext,
    actor: ActorCapability,
    high_water: AuthorityHighWater,
    proposal: Proposal,
    confirmed: Proposal,
    replacement_bytes: bytes,
    revision: _RevisionState,
    session: SessionState,
) -> None:
    proposal_path = _proposal_path(workspace, proposal.delta_id)
    session_path = _session_path(workspace)
    proposal_before = _existing_digest(proposal_path)
    session_before = _existing_digest(session_path)
    session_payload = _canonical_json(session.model_dump(mode="json"))
    next_revision = _RevisionState(
        format="ontowiz-authoring-revision",
        format_version=2,
        workspace_id=workspace.manifest.workspace_id,
        revision=revision.revision + 1,
        session_sequence=session.sequence,
        session_digest=_digest(session_payload),
    )
    _commit_mutation(
        workspace,
        trust=trust,
        actor=actor,
        high_water=high_water,
        operation="confirm",
        revision=revision,
        next_revision=next_revision,
        payloads=(
            ("target", None, replacement_bytes),
            (
                "proposal",
                proposal.delta_id,
                _canonical_json(confirmed.model_dump(mode="json")),
            ),
            ("session", None, session_payload),
        ),
        delta_id=proposal.delta_id,
        target_path=proposal.target_path,
        expected_target_digest=proposal.expected_target_digest,
        installed_target_digest=proposal.replacement_digest,
        proposal_before_digest=proposal_before,
        proposal_after_digest=_digest(_canonical_json(confirmed.model_dump(mode="json"))),
        session_before_digest=session_before,
        session_after_digest=_digest(session_payload),
    )


def authoring_transaction_identity_bytes(
    identity: AuthoringTransactionIdentity,
) -> bytes:
    """Return the canonical provider transaction identity payload."""
    return _canonical_json(identity.model_dump(mode="json"))


def authoring_transaction_digest(
    identity: AuthoringTransactionIdentity,
) -> str:
    """Return the canonical digest reserved by the external provider."""
    return _digest(authoring_transaction_identity_bytes(identity))


def _transaction_identity(
    journal: _TransactionJournal,
    *,
    actor: ActorCapability,
    credential: OperationCredential,
) -> AuthoringTransactionIdentity:
    if (
        actor.workspace_id != credential.workspace_id
        or actor.principal_id != credential.principal_id
        or actor.roles != credential.roles
        or actor.client_boundary != credential.client_boundary
        or actor.authority_revision != credential.authority_revision
        or actor.authority_digest != credential.authority_digest
        or actor.trust_key_id != credential.trust_key_id
        or actor.intent_digest != credential.intent_digest
        or actor.credential_nonce != credential.nonce
    ):
        raise AuthoringAtomicError("authenticated actor differs from operation credential")
    changes = tuple(
        sorted(
            (
                AuthoringTransactionChange(
                    kind=change.kind,
                    entity_id=change.entity_id,
                    before_digest=change.before_digest,
                    after_digest=change.after_digest,
                )
                for change in journal.changes
            ),
            key=lambda change: (change.kind, change.entity_id or ""),
        )
    )
    return AuthoringTransactionIdentity(
        format="ontowiz-provider-transaction",
        format_version=1,
        workspace_id=journal.workspace_id,
        transaction_id=journal.transaction_id,
        operation=journal.operation,
        revision_before=journal.revision_before,
        revision_after=journal.revision_after,
        actor_principal=actor.principal_id,
        intent_digest=journal.intent_digest,
        credential_nonce=actor.credential_nonce,
        credential_digest=_digest(_canonical_json(credential.model_dump(mode="json"))),
        trust_key_id=actor.trust_key_id,
        authority_revision=journal.authority_before_revision,
        authority_digest=journal.authority_before_digest,
        delta_id=journal.delta_id,
        target_path=journal.target_path,
        changes=changes,
    )


def _assert_journal_matches_external_identity(
    journal: _TransactionJournal,
    identity: AuthoringTransactionIdentity,
) -> None:
    changes = tuple(
        sorted(
            (
                AuthoringTransactionChange(
                    kind=change.kind,
                    entity_id=change.entity_id,
                    before_digest=change.before_digest,
                    after_digest=change.after_digest,
                )
                for change in journal.changes
            ),
            key=lambda change: (change.kind, change.entity_id or ""),
        )
    )
    public_binding = (
        identity.workspace_id,
        identity.transaction_id,
        identity.operation,
        identity.revision_before,
        identity.revision_after,
        identity.intent_digest,
        identity.authority_revision,
        identity.authority_digest,
        identity.delta_id,
        identity.target_path,
        identity.changes,
    )
    journal_binding = (
        journal.workspace_id,
        journal.transaction_id,
        journal.operation,
        journal.revision_before,
        journal.revision_after,
        journal.intent_digest,
        journal.authority_before_revision,
        journal.authority_before_digest,
        journal.delta_id,
        journal.target_path,
        changes,
    )
    if public_binding != journal_binding:
        raise AuthoringAtomicError("journal differs from external transaction identity")
    if journal.provider_transaction_digest != authoring_transaction_digest(identity):
        raise AuthoringAtomicError("journal provider transaction digest mismatch")


def _journal_identity(journal: _TransactionJournal) -> bytes:
    return _canonical_json(journal.model_dump(mode="json", exclude={"phase"}))


def _provider_authoring_state(
    provider: AuthoringTrustProvider,
    workspace_id: str,
) -> AuthoringProviderState:
    try:
        state = AuthoringProviderState.model_validate(provider.authoring_state(workspace_id))
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthoringAtomicError("external authoring state is unavailable") from exc
    if state.workspace_id != workspace_id:
        raise AuthoringAtomicError("external authoring state belongs to another workspace")
    return state


def _verify_journal_trust(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    journal: _TransactionJournal,
) -> tuple[
    AuthorityHighWater,
    AuthoringTransactionIdentity,
    RecoveryAuthorization,
]:
    state = _provider_authoring_state(provider, workspace.manifest.workspace_id)
    identities = tuple(
        identity
        for identity in (state.pending, state.last_finalized)
        if identity is not None
    )
    identity = next(
        (
            candidate
            for candidate in identities
            if candidate.transaction_id == journal.transaction_id
            and authoring_transaction_digest(candidate)
            == journal.provider_transaction_digest
        ),
        None,
    )
    if identity is None:
        raise AuthoringAtomicError("external transaction identity is unavailable")
    _assert_journal_matches_external_identity(journal, identity)
    identity_digest = authoring_transaction_digest(identity)
    high_water = _provider_high_water(provider, workspace.manifest.workspace_id)
    if identity.trust_key_id != high_water.trust_key_id:
        raise AuthoringAtomicError("external transaction trust key differs from high-water")
    current = (high_water.authority_revision, high_water.authority_digest)
    before = (
        journal.authority_before_revision,
        journal.authority_before_digest,
    )
    after = (
        journal.authority_after_revision,
        journal.authority_after_digest,
    )
    allowed = {before, after} if journal.operation == "install_authority" else {before}
    if current not in allowed:
        raise AuthoringAtomicError("transaction authority binding differs from external high-water")
    try:
        authorization = RecoveryAuthorization.model_validate(provider.authorize_recovery(identity))
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthoringAtomicError("external provider rejected transaction recovery") from exc
    if (
        authorization.workspace_id != journal.workspace_id
        or authorization.transaction_digest != identity_digest
        or authorization.authoring_revision not in {journal.revision_before, journal.revision_after}
        or (
            authorization.status == "pending"
            and authorization.authoring_revision != journal.revision_before
        )
        or (
            authorization.status == "finalized"
            and authorization.authoring_revision != journal.revision_after
        )
    ):
        raise AuthoringAtomicError("provider recovery authorization is incoherent")
    return high_water, identity, authorization


def _commit_mutation(
    workspace: Workspace,
    *,
    trust: AuthoringTrustContext,
    actor: ActorCapability,
    high_water: AuthorityHighWater,
    operation: AuthoringOperation,
    revision: _RevisionState,
    next_revision: _RevisionState,
    payloads: Sequence[tuple[_ChangeKind, str | None, bytes]],
    authority_after: AuthorityHighWater | None = None,
    delta_id: str | None = None,
    target_path: str | None = None,
    expected_target_digest: str | None = None,
    installed_target_digest: str | None = None,
    proposal_before_digest: str | None = None,
    proposal_after_digest: str | None = None,
    session_before_digest: str | None = None,
    session_after_digest: str | None = None,
) -> None:
    if next_revision.revision != revision.revision + 1:
        raise AuthoringAtomicError("mutation revision does not advance by one")
    if actor.intent_digest != trust.credential.intent_digest:
        raise AuthoringAtomicError("mutation actor intent binding drift")
    final_authority = authority_after or high_water
    transaction_id = (
        delta_id
        if operation == "confirm" and delta_id is not None
        else f"TX-{os.urandom(16).hex()}"
    )
    all_payloads = tuple(payloads) + (
        (
            "revision",
            None,
            _canonical_json(next_revision.model_dump(mode="json")),
        ),
    )
    changes: list[_JournalChange] = []
    before_payloads: list[bytes | None] = []
    for kind, entity_id, payload in all_payloads:
        target = _semantic_path(
            workspace,
            kind=kind,
            entity_id=entity_id,
            target_path=target_path,
        )
        before_payload = _read_safe_file(workspace, target) if target.exists() else None
        before_digest = _digest(before_payload) if before_payload is not None else None
        digest = _digest(payload)
        before_payloads.append(before_payload)
        changes.append(
            _JournalChange(
                kind=kind,
                entity_id=entity_id,
                before_digest=before_digest,
                before_stage_digest=before_digest,
                after_digest=digest,
                stage_digest=digest,
            )
        )
    journal = _TransactionJournal(
        format="ontowiz-authoring-transaction",
        format_version=5,
        operation=operation,
        transaction_id=transaction_id,
        workspace_id=workspace.manifest.workspace_id,
        intent_digest=actor.intent_digest,
        provider_transaction_digest=None,
        authority_before_revision=high_water.authority_revision,
        authority_before_digest=high_water.authority_digest,
        authority_after_revision=final_authority.authority_revision,
        authority_after_digest=final_authority.authority_digest,
        delta_id=delta_id,
        target_path=target_path,
        expected_target_digest=expected_target_digest,
        installed_target_digest=installed_target_digest,
        proposal_before_digest=proposal_before_digest,
        proposal_after_digest=proposal_after_digest,
        session_before_digest=session_before_digest,
        session_after_digest=session_after_digest,
        revision_before=revision.revision,
        revision_after=next_revision.revision,
        changes=tuple(changes),
        phase="prepared",
    )
    identity = _transaction_identity(
        journal,
        actor=actor,
        credential=trust.credential,
    )
    journal = journal.model_copy(
        update={"provider_transaction_digest": authoring_transaction_digest(identity)}
    )
    transaction_dir = workspace.root / "locks" / "transactions"
    journal_path = _journal_path(workspace, journal)
    _inject_kill(f"before-{operation}-reserve")
    try:
        trust.provider.reserve_transaction(identity)
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthoringAtomicError("external transaction reservation failed") from exc
    _inject_kill(f"after-{operation}-reserve")
    journal_written = False
    try:
        transaction_dir.mkdir(parents=True, exist_ok=True)
        for index, ((_, _, payload), before_payload) in enumerate(
            zip(all_payloads, before_payloads, strict=True)
        ):
            if before_payload is not None:
                _durable_write(
                    _before_stage_path(workspace, journal, index),
                    before_payload,
                )
            stage_path = _stage_path(workspace, journal, index)
            _durable_write(stage_path, payload)
            _inject_kill(f"after-{operation}-stage-{index}")
        _write_journal(journal_path, journal)
        journal_written = True
        _inject_kill(f"after-{operation}-journal")
        _finish_transaction(
            workspace,
            trust.provider,
            journal_path,
            journal,
            inject=True,
        )
    except (WorkspaceError, OSError) as exc:
        if not journal_written and not journal_path.exists():
            _abort_unjournaled_reservation(workspace, trust.provider, identity)
        raise AuthoringAtomicError(f"{operation} transaction is staged for recovery") from exc


def _transaction_local_before_state(
    workspace: Workspace,
    identity: AuthoringTransactionIdentity,
) -> bool:
    if _load_revision(workspace).revision != identity.revision_before:
        return False
    for change in identity.changes:
        target = _semantic_path(
            workspace,
            kind=change.kind,
            entity_id=change.entity_id,
            target_path=identity.target_path,
        )
        if _existing_digest(target) != change.before_digest:
            return False
    return True


def _clean_transaction_stages(
    workspace: Workspace,
    *,
    inject: bool = False,
) -> None:
    transaction_dir = workspace.root / "locks" / "transactions"
    if not transaction_dir.exists():
        return
    paths = (*transaction_dir.glob("*.stage"), *transaction_dir.glob("*.before"))
    for index, stage_path in enumerate(sorted(paths)):
        match = re.fullmatch(r"(.+)-(\d{2})\.(stage|before)", stage_path.name)
        if match is None or re.fullmatch(_SAFE_ID_PATTERN, match.group(1)) is None:
            raise AuthoringAtomicError("orphan transaction stage filename is invalid")
        _ensure_safe_plain_file(workspace, stage_path)
        stage_path.unlink()
        _sync_directory(transaction_dir)
        if inject:
            _inject_kill(f"after-orphan-cleanup-unlink-{index}")


def _abort_unjournaled_reservation(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    identity: AuthoringTransactionIdentity,
) -> None:
    if not _transaction_local_before_state(workspace, identity):
        raise AuthoringAtomicError(
            "cannot abort external reservation without proven local before-state"
        )
    try:
        provider.abort_reserved_transaction(identity)
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthoringAtomicError("external transaction abort failed") from exc
    state = _provider_authoring_state(provider, identity.workspace_id)
    if state.pending is not None or state.authoring_revision != identity.revision_before:
        raise AuthoringAtomicError("external transaction abort did not converge")
    _clean_transaction_stages(workspace)


def _recover_transactions(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
) -> None:
    transaction_dir = workspace.root / "locks" / "transactions"
    journals = sorted(transaction_dir.glob("*.journal")) if transaction_dir.exists() else []
    if len(journals) > 1:
        raise AuthoringAtomicError("multiple authoring transactions require recovery")
    state = _provider_authoring_state(provider, workspace.manifest.workspace_id)
    if not journals:
        if state.pending is not None:
            _abort_unjournaled_reservation(workspace, provider, state.pending)
            state = _provider_authoring_state(provider, workspace.manifest.workspace_id)
        elif transaction_dir.exists():
            _clean_transaction_stages(workspace)
        if _load_revision(workspace).revision != state.authoring_revision:
            raise AuthoringAtomicError(
                "local authoring revision differs from external finalized high-water"
            )
        return
    journal_path = journals[0]
    try:
        journal = _load_canonical_model(journal_path, _TransactionJournal)
    except WorkspaceError as exc:
        raise AuthoringAtomicError(
            "transaction journal attestation or structure is invalid"
        ) from exc
    if journal.workspace_id != workspace.manifest.workspace_id:
        raise AuthoringAtomicError("transaction journal belongs to another workspace")
    expected_path = _journal_path(workspace, journal)
    if journal_path != expected_path:
        raise AuthoringAtomicError("transaction journal filename substitution")
    _finish_transaction(
        workspace,
        provider,
        journal_path,
        journal,
        inject=False,
    )
    state = _provider_authoring_state(provider, workspace.manifest.workspace_id)
    if state.pending is not None or _load_revision(workspace).revision != state.authoring_revision:
        raise AuthoringAtomicError(
            "authoring transaction recovery did not converge with external high-water"
        )
    _clean_transaction_stages(workspace)


def _load_staged_transaction(
    workspace: Workspace,
    journal: _TransactionJournal,
) -> list[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]]:
    staged: list[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]] = []
    for index, change in enumerate(journal.changes):
        before_path = (
            _before_stage_path(workspace, journal, index)
            if change.before_digest is not None
            else None
        )
        before_payload = (
            _read_safe_file(workspace, before_path) if before_path is not None else None
        )
        if before_payload is not None and _digest(before_payload) != change.before_stage_digest:
            raise AuthoringAtomicError("transaction before-stage digest mismatch")
        stage_path = _stage_path(workspace, journal, index)
        payload = _read_safe_file(workspace, stage_path)
        if _digest(payload) != change.stage_digest:
            raise AuthoringAtomicError("transaction stage digest mismatch")
        target = _semantic_path(
            workspace,
            kind=change.kind,
            entity_id=change.entity_id,
            target_path=journal.target_path,
        )
        actual = _existing_digest(target)
        if actual not in {change.before_digest, change.after_digest}:
            raise AuthoringAtomicError("transaction before-state digest mismatch")
        if change.kind == "revision":
            current_revision = _load_revision(workspace)
            expected_number = (
                journal.revision_after if actual == change.after_digest else journal.revision_before
            )
            if current_revision.revision != expected_number:
                raise AuthoringAtomicError("transaction revision number mismatch")
        staged.append(
            (
                change,
                before_path,
                stage_path,
                target,
                before_payload,
                payload,
            )
        )
    return staged


def _advance_transaction_authority(
    provider: AuthoringTrustProvider,
    journal: _TransactionJournal,
    high_water: AuthorityHighWater,
    *,
    inject: bool,
) -> AuthorityHighWater:
    if journal.operation != "install_authority":
        return high_water
    current = (high_water.authority_revision, high_water.authority_digest)
    before = (
        journal.authority_before_revision,
        journal.authority_before_digest,
    )
    if current == before:
        replacement = high_water.model_copy(
            update={
                "authority_revision": journal.authority_after_revision,
                "authority_digest": journal.authority_after_digest,
            }
        )
        try:
            provider.advance_authority(
                expected=high_water,
                replacement=replacement,
            )
        except AuthorityClientError:
            raise
        except Exception as exc:
            raise AuthoringAtomicError("external authority high-water advance failed") from exc
        high_water = _provider_high_water(provider, journal.workspace_id)
        if (
            high_water.authority_revision != journal.authority_after_revision
            or high_water.authority_digest != journal.authority_after_digest
        ):
            raise AuthoringAtomicError("external authority high-water did not converge")
        if inject:
            _inject_kill("after-install_authority-high-water")
    return high_water


def _validate_finalized_after_payload(
    workspace: Workspace,
    journal: _TransactionJournal,
    change: _JournalChange,
    payload: bytes,
) -> None:
    try:
        if change.kind == "authority":
            authority = SignedAuthority.model_validate_json(payload)
            if (
                authority.statement.authority_revision != journal.authority_after_revision
                or authority.statement_digest != journal.authority_after_digest
            ):
                raise ValueError("authority after binding mismatch")
        elif change.kind == "source_register":
            _SourceRegister.model_validate_json(payload)
        elif change.kind == "material_bindings":
            bindings = _MaterialBindings.model_validate_json(payload)
            if bindings.workspace_id != journal.workspace_id:
                raise ValueError("material binding workspace mismatch")
        elif change.kind == "evidence":
            _EvidenceDocument.model_validate_json(payload)
        elif change.kind == "proposal":
            proposal = Proposal.model_validate_json(payload)
            if proposal.workspace_id != journal.workspace_id:
                raise ValueError("proposal workspace mismatch")
        elif change.kind == "session":
            session = SessionState.model_validate_json(payload)
            if (
                session.workspace_id != journal.workspace_id
                or session.revision != journal.revision_after
            ):
                raise ValueError("session finalized binding mismatch")
        elif change.kind == "revision":
            revision = _RevisionState.model_validate_json(payload)
            if (
                revision.workspace_id != journal.workspace_id
                or revision.revision != journal.revision_after
            ):
                raise ValueError("revision finalized binding mismatch")
        else:
            body = json.loads(payload)
            if not isinstance(body, dict) or journal.target_path is None:
                raise ValueError("target finalized body is invalid")
            _assert_candidate_only(body)
            _validate_target_document(journal.target_path, body)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise AuthoringAtomicError("finalized transaction semantic after-state is invalid") from exc


def _verify_finalized_local_after_state(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    journal: _TransactionJournal,
) -> None:
    state = _provider_authoring_state(provider, journal.workspace_id)
    if (
        state.pending is not None
        or state.authoring_revision != journal.revision_after
        or state.last_finalized_transaction_id != journal.transaction_id
        or state.last_finalized_transaction_digest != journal.provider_transaction_digest
    ):
        raise AuthoringAtomicError("provider finalized transaction state is incoherent")
    for change in journal.changes:
        target = _semantic_path(
            workspace,
            kind=change.kind,
            entity_id=change.entity_id,
            target_path=journal.target_path,
        )
        payload = _read_safe_file(workspace, target)
        if _digest(payload) != change.after_digest:
            raise AuthoringAtomicError("finalized transaction local state was restored or replayed")
        _validate_finalized_after_payload(workspace, journal, change, payload)


def _cleanup_transaction(
    workspace: Workspace,
    journal_path: Path,
    journal: _TransactionJournal,
    *,
    inject: bool,
) -> None:
    transaction_dir = journal_path.parent
    if journal_path.exists():
        _ensure_safe_plain_file(workspace, journal_path)
        journal_path.unlink()
        _sync_directory(transaction_dir)
        if inject:
            _inject_kill(f"after-{journal.operation}-cleanup-unlink-journal")
    for index in range(len(journal.changes)):
        before_path = _before_stage_path(workspace, journal, index)
        stage_path = _stage_path(workspace, journal, index)
        for label, candidate in (("before", before_path), ("stage", stage_path)):
            if not candidate.exists():
                continue
            _ensure_safe_plain_file(workspace, candidate)
            candidate.unlink()
            _sync_directory(transaction_dir)
            if inject:
                _inject_kill(f"after-{journal.operation}-cleanup-unlink-" f"{index}-{label}")


def _finish_transaction(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    journal_path: Path,
    journal: _TransactionJournal,
    *,
    inject: bool,
) -> None:
    high_water, identity, authorization = _verify_journal_trust(
        workspace,
        provider,
        journal,
    )
    _validate_operation_changes(journal)
    if authorization.status == "finalized":
        _verify_finalized_local_after_state(workspace, provider, journal)
        _cleanup_transaction(
            workspace,
            journal_path,
            journal,
            inject=inject,
        )
        if inject:
            _inject_kill(f"after-{journal.operation}-cleanup")
        return
    staged = _load_staged_transaction(workspace, journal)
    actor = _reauthenticate_journal(
        workspace,
        provider,
        journal,
        identity,
        authorization,
        high_water,
        staged,
    )
    _validate_transaction_semantics(
        workspace,
        provider,
        actor,
        high_water,
        journal,
        staged,
    )
    high_water = _advance_transaction_authority(
        provider,
        journal,
        high_water,
        inject=inject,
    )
    current_journal = journal
    if current_journal.phase == "prepared":
        current_journal = current_journal.model_copy(update={"phase": "applying"})
        _write_journal(journal_path, current_journal)
    for index, (change, _, _, target, _, payload) in enumerate(staged):
        if _existing_digest(target) == change.after_digest:
            continue
        if change.kind == "target":
            if inject:
                _inject_kill("before-target-replace")
            if _existing_digest(target) != change.before_digest:
                raise StaleProposalError("target is stale before final replace check")
            if inject:
                _inject_kill("after-final-target-read")
            if _existing_digest(target) != change.before_digest:
                raise StaleProposalError("target is stale inside final replace boundary")
        _durable_write(target, payload)
        if _existing_digest(target) != change.after_digest:
            raise AuthoringAtomicError("transaction installed digest mismatch")
        if inject:
            _inject_kill(f"after-{journal.operation}-file-{index}")
    for change, _, _, target, _, _ in staged:
        if _existing_digest(target) != change.after_digest:
            raise AuthoringAtomicError("transaction did not converge to after state")
    if inject:
        _inject_kill(f"after-{journal.operation}-apply")
    current_journal = current_journal.model_copy(update={"phase": "committed"})
    _write_journal(journal_path, current_journal)
    if inject:
        _inject_kill(f"after-{journal.operation}-commit")
    try:
        provider.finalize_transaction(identity)
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthoringAtomicError("external transaction finalize failed") from exc
    final_state = _provider_authoring_state(provider, journal.workspace_id)
    if (
        final_state.pending is not None
        or final_state.authoring_revision != journal.revision_after
        or final_state.last_finalized_transaction_id != journal.transaction_id
        or final_state.last_finalized_transaction_digest != journal.provider_transaction_digest
    ):
        raise AuthoringAtomicError("external transaction finalize did not converge")
    if inject:
        _inject_kill(f"after-{journal.operation}-finalize")
    _cleanup_transaction(
        workspace,
        journal_path,
        journal,
        inject=inject,
    )
    if inject:
        _inject_kill(f"after-{journal.operation}-cleanup")


def _validate_operation_changes(journal: _TransactionJournal) -> None:
    expected: dict[str, set[str]] = {
        "install_authority": {"authority", "revision"},
        "register_source": {"source_register", "material_bindings", "revision"},
        "update_source": {"source_register", "revision"},
        "withdraw_source": {"source_register", "revision"},
        "record_evidence": {"evidence", "revision"},
        "propose": {"proposal", "revision"},
        "confirm": {"target", "proposal", "session", "revision"},
        "update_session": {"session", "revision"},
    }
    actual = {change.kind for change in journal.changes}
    allowed = expected[journal.operation]
    if actual != allowed and not (
        journal.operation == "register_source" and actual == {"source_register", "revision"}
    ):
        raise AuthoringAtomicError("transaction semantic change set mismatch")
    if journal.operation in {"register_source", "update_source", "withdraw_source"}:
        source_change = next(
            change for change in journal.changes if change.kind == "source_register"
        )
        if source_change.entity_id is None:
            raise AuthoringAtomicError("source journal lacks subject identity")
    if journal.operation == "propose":
        proposal = next(change for change in journal.changes if change.kind == "proposal")
        if (
            journal.delta_id != proposal.entity_id
            or journal.proposal_before_digest != proposal.before_digest
            or journal.proposal_after_digest != proposal.after_digest
        ):
            raise AuthoringAtomicError("proposal journal digest binding mismatch")
    if journal.operation == "update_session":
        session = next(change for change in journal.changes if change.kind == "session")
        if (
            journal.session_before_digest != session.before_digest
            or journal.session_after_digest != session.after_digest
        ):
            raise AuthoringAtomicError("session journal digest binding mismatch")


def _staged_change(
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
    kind: _ChangeKind,
) -> tuple[_JournalChange, bytes | None, bytes]:
    matches = [
        (change, before_payload, payload)
        for change, _, _, _, before_payload, payload in staged
        if change.kind == kind
    ]
    if len(matches) != 1:
        raise AuthoringAtomicError(f"transaction lacks unique {kind} transition")
    return matches[0]


def _revision_transition(
    journal: _TransactionJournal,
    before_payload: bytes | None,
    after_payload: bytes,
) -> tuple[_RevisionState, _RevisionState]:
    try:
        before = (
            _RevisionState.model_validate_json(before_payload)
            if before_payload is not None
            else _RevisionState(
                format="ontowiz-authoring-revision",
                format_version=2,
                workspace_id=journal.workspace_id,
                revision=0,
                session_sequence=0,
            )
        )
        after = _RevisionState.model_validate_json(after_payload)
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid staged revision transition") from exc
    if (
        before.workspace_id != journal.workspace_id
        or after.workspace_id != journal.workspace_id
        or before.revision != journal.revision_before
        or after.revision != journal.revision_after
    ):
        raise AuthoringAtomicError("revision transition binding mismatch")
    return before, after


def _source_map(payload: bytes | None) -> dict[str, SourceRecord]:
    if payload is None:
        return {}
    try:
        return _unique_sources(_SourceRegister.model_validate_json(payload))
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid source register transition") from exc


def _binding_map(
    payload: bytes | None,
    workspace_id: str,
) -> dict[str, _MaterialBinding]:
    if payload is None:
        return {}
    try:
        record = _MaterialBindings.model_validate_json(payload)
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid material binding transition") from exc
    if record.workspace_id != workspace_id:
        raise AuthoringAtomicError("material bindings belong to another workspace")
    return {item.source_id: item for item in record.bindings}


def _validate_source_transition(
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    change, before_payload, after_payload = _staged_change(staged, "source_register")
    if change.entity_id is None:
        raise AuthoringAtomicError("source transition lacks subject")
    before = _source_map(before_payload)
    after = _source_map(after_payload)
    subject = change.entity_id
    if journal.operation == "register_source":
        if set(after) - set(before) != {subject} or set(before) - set(after):
            raise AuthoringAtomicError("source registration is not an only-add transition")
        if any(after[key] != value for key, value in before.items()):
            raise AuthoringAtomicError("source registration rewrites an existing source")
        if after[subject].status is not SourceStatus.CURRENT:
            raise AuthoringAtomicError("source registration adds non-current source")
        binding_changes = [item for item in staged if item[0].kind == "material_bindings"]
        if binding_changes:
            _, _, _, _, binding_before_payload, binding_after_payload = binding_changes[0]
            bindings_before = _binding_map(
                binding_before_payload,
                journal.workspace_id,
            )
            bindings_after = _binding_map(
                binding_after_payload,
                journal.workspace_id,
            )
            added = set(bindings_after) - set(bindings_before)
            if added not in (set(), {subject}) or set(bindings_before) - set(bindings_after):
                raise AuthoringAtomicError("source binding transition is not only-add")
            if any(bindings_after[key] != value for key, value in bindings_before.items()):
                raise AuthoringAtomicError("source binding rewrites existing identity")
            if added and bindings_after[subject].checksum != after[subject].checksum:
                raise AuthoringAtomicError("source binding checksum differs from source")
        return
    if set(before) != set(after) or subject not in before:
        raise AuthoringAtomicError("source withdrawal changes register identity set")
    changed = {key for key in before if before[key] != after[key]}
    if changed != {subject}:
        raise AuthoringAtomicError("source withdrawal changes an unexpected source")
    prior = before[subject]
    replacement = after[subject]
    if (
        prior.status is not SourceStatus.CURRENT
        or replacement.status is not SourceStatus.WITHDRAWN
        or _source_without_status(prior) != _source_without_status(replacement)
    ):
        raise AuthoringAtomicError(
            "source update resurrects or rewrites immutable rights/checksum/identity"
        )


def _validate_evidence_transition(
    workspace: Workspace,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    change, before_payload, after_payload = _staged_change(staged, "evidence")
    if change.entity_id is None:
        raise AuthoringAtomicError("evidence transition lacks source identity")
    try:
        before = (
            _EvidenceDocument.model_validate_json(before_payload)
            if before_payload is not None
            else _EvidenceDocument(
                format="ontowiz-extracted-evidence",
                format_version=2,
                source_id=change.entity_id,
            )
        )
        after = _EvidenceDocument.model_validate_json(after_payload)
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid evidence transition") from exc
    if before.source_id != change.entity_id or after.source_id != change.entity_id:
        raise AuthoringAtomicError("evidence source identity changed")
    before_evidence = {item.id: item for item in before.evidence}
    after_evidence = {item.id: item for item in after.evidence}
    added = set(after_evidence) - set(before_evidence)
    if len(added) != 1 or set(before_evidence) - set(after_evidence):
        raise AuthoringAtomicError("evidence transition is not exactly one addition")
    if any(after_evidence[key] != value for key, value in before_evidence.items()):
        raise AuthoringAtomicError("evidence transition rewrites existing evidence")
    before_quotes = {item.evidence_id: item for item in before.quotes}
    after_quotes = {item.evidence_id: item for item in after.quotes}
    if set(before_quotes) - set(after_quotes) or any(
        after_quotes[key] != value for key, value in before_quotes.items()
    ):
        raise AuthoringAtomicError("evidence transition rewrites existing quotes")
    if set(after_quotes) - set(before_quotes) not in (set(), added):
        raise AuthoringAtomicError("evidence quote addition does not match new evidence")
    sources = _unique_sources(_load_source_register(workspace))
    evidence_id = next(iter(added))
    _validate_evidence(after_evidence[evidence_id], sources)
    quote = after_quotes.get(evidence_id)
    _validate_persisted_quote(after_evidence[evidence_id], quote)


def _validate_proposal_transition(
    journal: _TransactionJournal,
    actor: ActorCapability,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    change, before_payload, after_payload = _staged_change(staged, "proposal")
    try:
        after = Proposal.model_validate_json(after_payload)
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid proposal transition") from exc
    if after.workspace_id != journal.workspace_id or after.delta_id != change.entity_id:
        raise AuthoringAtomicError("proposal identity binding mismatch")
    if journal.operation == "propose":
        if before_payload is not None or after.status != "proposed":
            raise AuthoringAtomicError("proposal operation is not a fresh proposal")
        if after.workspace_revision != journal.revision_before:
            raise AuthoringAtomicError("proposal workspace revision binding mismatch")
        return
    if before_payload is None:
        raise AuthoringAtomicError("confirmation lacks proposed before-state")
    try:
        before = Proposal.model_validate_json(before_payload)
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid confirmation proposal before-state") from exc
    if before.status != "proposed" or after.status != "confirmed":
        raise AuthoringAtomicError("confirmation proposal status transition is invalid")
    confirmation_fields = {
        "status",
        "confirmer_principal",
        "confirmer_role",
        "confirmed_at",
        "applied_from_digest",
        "applied_to_digest",
    }
    prior = before.model_dump(mode="json", exclude=confirmation_fields)
    final = after.model_dump(mode="json", exclude=confirmation_fields)
    if prior != final:
        raise AuthoringAtomicError("confirmation rewrites immutable proposal fields")
    if (
        after.confirmer_principal != actor.principal_id
        or after.target_path != journal.target_path
        or after.replacement_digest != journal.installed_target_digest
    ):
        raise AuthoringAtomicError("confirmation actor or target binding mismatch")


def _validate_session_transition(
    journal: _TransactionJournal,
    revision_before: _RevisionState,
    revision_after: _RevisionState,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, before_payload, after_payload = _staged_change(staged, "session")
    try:
        before = (
            SessionState.model_validate_json(before_payload) if before_payload is not None else None
        )
        after = SessionState.model_validate_json(after_payload)
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid session transition") from exc
    if after.workspace_id != journal.workspace_id:
        raise AuthoringAtomicError("session belongs to another workspace")
    if (
        after.revision != journal.revision_after
        or after.sequence != revision_before.session_sequence + 1
        or revision_after.session_sequence != after.sequence
        or revision_after.session_digest != _digest(after_payload)
    ):
        raise AuthoringAtomicError("session revision/sequence/digest transition mismatch")
    if before is not None:
        if before_payload is None:
            raise AuthoringAtomicError("session before-state snapshot is missing")
        if (
            before.sequence != revision_before.session_sequence
            or _digest(before_payload) != revision_before.session_digest
        ):
            raise AuthoringAtomicError("session before-state differs from revision anchor")


def _validate_authority_transition(
    workspace: Workspace,
    high_water: AuthorityHighWater,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, before_payload, after_payload = _staged_change(staged, "authority")
    try:
        before = (
            SignedAuthority.model_validate_json(before_payload)
            if before_payload is not None
            else None
        )
        after = SignedAuthority.model_validate_json(after_payload)
    except (ValidationError, ValueError) as exc:
        raise AuthoringAtomicError("invalid authority transition") from exc
    _verify_signed_authority(workspace, high_water, after)
    if (
        after.statement.authority_revision != journal.authority_after_revision
        or after.statement_digest != journal.authority_after_digest
    ):
        raise AuthoringAtomicError("authority after-state differs from journal high-water")
    if journal.authority_before_revision == 0:
        if before is not None:
            raise AuthoringAtomicError("first authority transition has a prior cache")
    elif (
        before is None
        or before.statement.authority_revision != journal.authority_before_revision
        or before.statement_digest != journal.authority_before_digest
        or before.trust_key_id != high_water.trust_key_id
    ):
        raise AuthoringAtomicError("authority before-state differs from external high-water")


def _journal_before_authority(
    workspace: Workspace,
    journal: _TransactionJournal,
    high_water: AuthorityHighWater,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> SignedAuthority | None:
    if journal.authority_before_revision == 0:
        return None
    before_anchor = high_water.model_copy(
        update={
            "authority_revision": journal.authority_before_revision,
            "authority_digest": journal.authority_before_digest,
        }
    )
    if journal.operation == "install_authority":
        _, before_payload, _ = _staged_change(staged, "authority")
        if before_payload is None:
            raise AuthorizationError("prior authority snapshot is missing")
        authority = SignedAuthority.model_validate_json(before_payload)
        _verify_signed_authority(workspace, before_anchor, authority)
        if (
            authority.statement.authority_revision != journal.authority_before_revision
            or authority.statement_digest != journal.authority_before_digest
        ):
            raise AuthorizationError("prior authority snapshot differs from provider binding")
        return authority
    path = _authority_path(workspace)
    if not path.exists():
        raise AuthorizationError("recovery authority cache is missing")
    authority = _load_canonical_model(path, SignedAuthority)
    _verify_signed_authority(workspace, before_anchor, authority)
    if (
        authority.statement.authority_revision != journal.authority_before_revision
        or authority.statement_digest != journal.authority_before_digest
    ):
        raise AuthorizationError("recovery authority cache differs from provider binding")
    return authority


def _reauthenticate_journal(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    journal: _TransactionJournal,
    identity: AuthoringTransactionIdentity,
    authorization: RecoveryAuthorization,
    high_water: AuthorityHighWater,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> ActorCapability:
    if (
        identity.workspace_id != workspace.manifest.workspace_id
        or identity.intent_digest != journal.intent_digest
        or identity.authority_revision != journal.authority_before_revision
        or identity.authority_digest != journal.authority_before_digest
        or authorization.transaction_digest != authoring_transaction_digest(identity)
    ):
        raise AuthorizationError("recovery identity binding mismatch")
    try:
        actor = ActorCapability.model_validate(
            provider.authenticate_recovery(
                identity,
                authorization,
            )
        )
    except AuthorityClientError:
        raise
    except Exception as exc:
        raise AuthorizationError("trusted provider rejected recovery authorization") from exc
    expected_actor = {
        "workspace_id": identity.workspace_id,
        "principal_id": identity.actor_principal,
        "authority_revision": identity.authority_revision,
        "authority_digest": identity.authority_digest,
        "trust_key_id": identity.trust_key_id,
        "intent_digest": identity.intent_digest,
        "credential_nonce": identity.credential_nonce,
    }
    if any(getattr(actor, field) != expected for field, expected in expected_actor.items()):
        raise AuthorizationError(
            "provider recovery actor differs from external transaction identity"
        )
    authority = _journal_before_authority(
        workspace,
        journal,
        high_water,
        staged,
    )
    if authority is None:
        if not set(actor.roles).issubset(set(workspace.manifest.owner_roles)):
            raise AuthorizationError("bootstrap recovery roles exceed workspace authority")
        return actor
    grant = next(
        (item for item in authority.statement.grants if item.principal_id == actor.principal_id),
        None,
    )
    if grant is None:
        raise AuthorizationError("recovery actor is absent from current authority")
    if actor.roles != grant.roles or actor.client_boundary != grant.client_boundary:
        raise AuthorizationError("recovery actor no longer matches current authority")
    return actor


def _assert_reconstructed_intent(
    journal: _TransactionJournal,
    request: Mapping[str, object],
    *,
    mandatory_revision: bool,
) -> None:
    revisions: tuple[int | None, ...] = (
        (journal.revision_before,) if mandatory_revision else (None, journal.revision_before)
    )
    possible = {
        _mutation_intent(
            journal.operation,
            journal.workspace_id,
            expected_revision,
            request,
        )
        for expected_revision in revisions
    }
    if journal.intent_digest not in possible:
        raise AuthoringAtomicError(
            "transaction intent cannot be reconstructed from staged semantics"
        )


def _validate_live_authority(
    workspace: Workspace,
    high_water: AuthorityHighWater,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, _, payload = _staged_change(staged, "authority")
    authority = SignedAuthority.model_validate_json(payload)
    before_anchor = high_water.model_copy(
        update={
            "authority_revision": journal.authority_before_revision,
            "authority_digest": journal.authority_before_digest,
        }
    )
    _verify_signed_authority(workspace, before_anchor, authority)
    if authority.statement.authority_revision != journal.authority_before_revision + 1:
        raise AuthorizationError("recovered authority does not advance by one")
    owner_roles = set(workspace.manifest.owner_roles)
    if any(not set(grant.roles).issubset(owner_roles) for grant in authority.statement.grants):
        raise AuthorizationError("recovered authority grants undeclared roles")
    _assert_reconstructed_intent(
        journal,
        {"authority": authority.model_dump(mode="json")},
        mandatory_revision=True,
    )


def _validate_live_source(
    workspace: Workspace,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    change, before_payload, after_payload = _staged_change(staged, "source_register")
    if change.entity_id is None:
        raise AuthoringAtomicError("source transaction has no source id")
    before = _source_map(before_payload) if before_payload is not None else {}
    after = _source_map(after_payload)
    source = after.get(change.entity_id)
    if source is None:
        raise AuthoringAtomicError("source transaction omits its declared source")
    if journal.operation == "register_source":
        if change.entity_id in before or source.status is not SourceStatus.CURRENT:
            raise AuthoringAtomicError("recovered source registration is not a new source")
        binding_change = next(
            (item for item in staged if item[0].kind == "material_bindings"),
            None,
        )
        material_path: str | None = None
        if binding_change is not None:
            binding_before_payload = binding_change[4]
            binding_after_payload = binding_change[5]
            old_bindings = (
                _binding_map(binding_before_payload, workspace.manifest.workspace_id)
                if binding_before_payload is not None
                else {}
            )
            new_bindings = _binding_map(
                binding_after_payload,
                workspace.manifest.workspace_id,
            )
            binding = new_bindings.get(source.id)
            if source.id in old_bindings:
                raise AuthoringAtomicError("source registration rewrites a material binding")
            if binding is not None:
                material_path = binding.relative_path
                if (
                    _validate_material_for_registration(
                        workspace,
                        source,
                        material_path,
                    )
                    != binding
                ):
                    raise AuthoringValidationError(
                        "recovered source material binding is no longer valid"
                    )
        request: Mapping[str, object] = {
            "source": source.model_dump(mode="json"),
            "material_path": material_path,
        }
    elif journal.operation == "update_source":
        request = {"source": source.model_dump(mode="json")}
    else:
        if source.withdrawn_at is None or not _is_aware(source.withdrawn_at):
            raise AuthoringAtomicError("recovered withdrawal lacks an aware timestamp")
        request = {
            "source_id": source.id,
            "withdrawn_at": source.withdrawn_at.isoformat(),
        }
    _assert_reconstructed_intent(
        journal,
        request,
        mandatory_revision=False,
    )


def _validate_live_evidence(
    workspace: Workspace,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, before_payload, after_payload = _staged_change(staged, "evidence")
    before = (
        _EvidenceDocument.model_validate_json(before_payload)
        if before_payload is not None
        else None
    )
    after = _EvidenceDocument.model_validate_json(after_payload)
    before_records = {record.id: record for record in before.evidence} if before is not None else {}
    added = [record for record in after.evidence if record.id not in before_records]
    if len(added) != 1:
        raise AuthoringAtomicError("recovered evidence transaction is not one addition")
    evidence = added[0]
    quotes = {quote.evidence_id: quote for quote in after.quotes}
    quote = quotes.get(evidence.id)
    sources = _unique_sources(_load_source_register(workspace))
    _validate_evidence(evidence, sources)
    _validate_persisted_quote(evidence, quote)
    _rehash_material(workspace, sources[evidence.source_id], _load_material_bindings(workspace))
    _assert_reconstructed_intent(
        journal,
        {
            "evidence": evidence.model_dump(mode="json"),
            "quote_payload": quote.payload if quote is not None else None,
        },
        mandatory_revision=False,
    )


def _validate_live_proposal(
    workspace: Workspace,
    actor: ActorCapability,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, _, proposal_payload = _staged_change(staged, "proposal")
    proposal = Proposal.model_validate_json(proposal_payload)
    if (
        proposal.status != "proposed"
        or proposal.workspace_revision != journal.revision_before
        or proposal.proposer_principal != actor.principal_id
        or proposal.proposer_authority_digest != actor.authority_digest
        or proposal.client_boundary != actor.client_boundary
    ):
        raise AuthorizationError("recovered proposal actor or lifecycle binding is invalid")
    owner_roles = set(workspace.manifest.owner_roles)
    if (
        proposal.target_owner_role not in owner_roles
        or not set(proposal.allowed_confirmer_roles).issubset(owner_roles)
        or proposal.target_owner_role not in proposal.allowed_confirmer_roles
    ):
        raise AuthorizationError("recovered proposal ownership is invalid")
    _assert_candidate_only(proposal.replacement_body)
    _validate_target_document(proposal.target_path, proposal.replacement_body)
    _validate_evidence_ids(
        workspace,
        proposal.evidence_ids,
        client_boundary=actor.client_boundary,
    )
    _assert_target_precondition(
        workspace.root / proposal.target_path,
        proposal.expected_target_digest,
        proposal.target_path,
    )
    _assert_reconstructed_intent(
        journal,
        {
            "delta_id": proposal.delta_id,
            "target_owner_role": proposal.target_owner_role,
            "allowed_confirmer_roles": list(proposal.allowed_confirmer_roles),
            "target_path": proposal.target_path,
            "expected_target_digest": proposal.expected_target_digest,
            "replacement_body": proposal.replacement_body,
            "evidence_ids": list(proposal.evidence_ids),
            "rationale": proposal.rationale,
        },
        mandatory_revision=False,
    )


def _validate_live_confirmation_session(
    workspace: Workspace,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
    confirmed: Proposal,
) -> SessionState:
    _, revision_before_payload, revision_after_payload = _staged_change(
        staged,
        "revision",
    )
    revision_before, revision_after = _revision_transition(
        journal,
        revision_before_payload,
        revision_after_payload,
    )
    _, session_before_payload, session_after_payload = _staged_change(
        staged,
        "session",
    )
    before = (
        SessionState.model_validate_json(session_before_payload)
        if session_before_payload is not None
        else SessionState(
            format="ontowiz-authoring-session",
            format_version=2,
            workspace_id=journal.workspace_id,
            revision=journal.revision_before,
            sequence=revision_before.session_sequence,
            stage="discover",
            next_mission="discover",
        )
    )
    after = SessionState.model_validate_json(session_after_payload)
    if (
        before.workspace_id != journal.workspace_id
        or before.revision > journal.revision_before
        or before.sequence != revision_before.session_sequence
        or (session_before_payload is None and revision_before.session_digest is not None)
        or (
            session_before_payload is not None
            and _digest(session_before_payload) != revision_before.session_digest
        )
    ):
        raise AuthoringAtomicError("confirmation session before-state is not canonical")
    if (
        after.workspace_id != journal.workspace_id
        or after.revision != journal.revision_after
        or after.sequence != before.sequence + 1
        or after.sequence != revision_after.session_sequence
        or revision_after.session_digest != _digest(session_after_payload)
        or after.stage != before.stage
        or after.next_mission != before.next_mission
        or after.last_delta_id != journal.delta_id
        or after.last_delta_id != confirmed.delta_id
        or after.open_question_ids
    ):
        raise AuthoringAtomicError("confirmation session output differs from exact transition")
    current_questions = {question.id for question in _compile_questions_under_lock(workspace)}
    if set(after.open_question_ids) - current_questions:
        raise AuthoringAtomicError("confirmation session contains stale current questions")
    return after


def _validate_live_confirmation(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    actor: ActorCapability,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, before_payload, after_payload = _staged_change(staged, "proposal")
    if before_payload is None:
        raise AuthoringAtomicError("confirmation proposal before-state is missing")
    before = Proposal.model_validate_json(before_payload)
    after = Proposal.model_validate_json(after_payload)
    _validate_confirmation_actor(before, actor)
    if (
        before.status != "proposed"
        or after.status != "confirmed"
        or after.confirmer_principal != actor.principal_id
        or after.confirmer_role != before.target_owner_role
        or after.confirmed_at is None
    ):
        raise AuthorizationError("recovered confirmation actor or lifecycle is invalid")
    authority = _load_authority(workspace, provider)
    if before.proposer_authority_digest != authority.statement_digest:
        raise AuthorizationError("recovered proposal authority is no longer current")
    _validate_evidence_ids(
        workspace,
        after.evidence_ids,
        client_boundary=after.client_boundary,
        confirmed_at=after.confirmed_at,
    )
    _assert_candidate_only(after.replacement_body)
    _validate_target_document(after.target_path, after.replacement_body)
    confirmed_session = _validate_live_confirmation_session(
        workspace,
        journal,
        staged,
        after,
    )
    _, _, _, target, _, _ = next(item for item in staged if item[0].kind == "target")
    actual = _existing_digest(target)
    if actual == after.expected_target_digest:
        _assert_target_precondition(
            target,
            after.expected_target_digest,
            after.target_path,
        )
    elif actual != after.replacement_digest:
        raise StaleProposalError("recovered confirmation target is stale")
    _assert_reconstructed_intent(
        journal,
        {
            "delta_id": after.delta_id,
            "confirmed_at": after.confirmed_at.isoformat(),
            "session": confirmed_session.model_dump(mode="json"),
        },
        mandatory_revision=False,
    )


def _validate_live_session(
    workspace: Workspace,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, _, after_payload = _staged_change(staged, "session")
    session = SessionState.model_validate_json(after_payload)
    if session.last_delta_id is not None:
        proposal = _load_proposal_path(
            workspace,
            _proposal_path(workspace, session.last_delta_id),
        )
        if proposal.workspace_id != workspace.manifest.workspace_id:
            raise AuthoringValidationError("recovered session delta belongs to another workspace")
    current_ids = {question.id for question in _compile_questions_under_lock(workspace)}
    stale = set(session.open_question_ids) - current_ids
    if stale:
        raise AuthoringValidationError(
            "recovered session references non-current questions: " + ", ".join(sorted(stale))
        )
    _assert_reconstructed_intent(
        journal,
        {
            "stage": session.stage,
            "last_delta_id": session.last_delta_id,
            "open_question_ids": list(session.open_question_ids),
            "next_mission": session.next_mission,
        },
        mandatory_revision=True,
    )


def _validate_live_recovery(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    actor: ActorCapability,
    high_water: AuthorityHighWater,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    if journal.operation == "install_authority":
        _validate_live_authority(workspace, high_water, journal, staged)
    elif journal.operation in {
        "register_source",
        "update_source",
        "withdraw_source",
    }:
        _validate_live_source(workspace, journal, staged)
    elif journal.operation == "record_evidence":
        _validate_live_evidence(workspace, journal, staged)
    elif journal.operation == "propose":
        _validate_live_proposal(workspace, actor, journal, staged)
    elif journal.operation == "confirm":
        _validate_live_confirmation(workspace, provider, actor, journal, staged)
    else:
        _validate_live_session(workspace, journal, staged)


def _validate_transaction_semantics(
    workspace: Workspace,
    provider: AuthoringTrustProvider,
    actor: ActorCapability,
    high_water: AuthorityHighWater,
    journal: _TransactionJournal,
    staged: Sequence[tuple[_JournalChange, Path | None, Path, Path, bytes | None, bytes]],
) -> None:
    _, revision_before_payload, revision_after_payload = _staged_change(
        staged,
        "revision",
    )
    revision_before, revision_after = _revision_transition(
        journal,
        revision_before_payload,
        revision_after_payload,
    )
    if journal.operation in {"update_session", "confirm"}:
        _validate_session_transition(
            journal,
            revision_before,
            revision_after,
            staged,
        )
    elif (
        revision_after.session_sequence != revision_before.session_sequence
        or revision_after.session_digest != revision_before.session_digest
    ):
        raise AuthoringAtomicError("non-session mutation changes session anchor")
    if journal.operation == "install_authority":
        _validate_authority_transition(workspace, high_water, journal, staged)
    elif journal.operation in {
        "register_source",
        "update_source",
        "withdraw_source",
    }:
        _validate_source_transition(journal, staged)
    elif journal.operation == "record_evidence":
        _validate_evidence_transition(workspace, journal, staged)
    elif journal.operation in {"propose", "confirm"}:
        _validate_proposal_transition(journal, actor, staged)
        if journal.operation == "confirm":
            _, target_before, target_after = _staged_change(staged, "target")
            _, _, proposal_after_payload = _staged_change(staged, "proposal")
            proposal = Proposal.model_validate_json(proposal_after_payload)
            if (
                _digest(target_after) != proposal.replacement_digest
                or target_after != _canonical_json(proposal.replacement_body)
                or (_digest(target_before) if target_before is not None else None)
                != proposal.expected_target_digest
            ):
                raise AuthoringAtomicError("confirmation target transition mismatch")

    _validate_live_recovery(
        workspace,
        provider,
        actor,
        high_water,
        journal,
        staged,
    )


def _journal_path(
    workspace: Workspace,
    journal: _TransactionJournal,
) -> Path:
    stem = journal.delta_id if journal.operation == "confirm" else journal.transaction_id
    if stem is None or re.fullmatch(_SAFE_ID_PATTERN, stem) is None:
        raise AuthoringAtomicError("transaction journal id is invalid")
    return _safe_resolve(workspace, f"locks/transactions/{stem}.journal")


def _stage_path(
    workspace: Workspace,
    journal: _TransactionJournal,
    index: int,
) -> Path:
    if index < 0 or index > 99:
        raise AuthoringAtomicError("transaction stage index is invalid")
    stem = journal.delta_id if journal.operation == "confirm" else journal.transaction_id
    if stem is None or re.fullmatch(_SAFE_ID_PATTERN, stem) is None:
        raise AuthoringAtomicError("transaction stage id is invalid")
    return _safe_resolve(
        workspace,
        f"locks/transactions/{stem}-{index:02}.stage",
    )


def _before_stage_path(
    workspace: Workspace,
    journal: _TransactionJournal,
    index: int,
) -> Path:
    if index < 0 or index > 99:
        raise AuthoringAtomicError("transaction before-stage index is invalid")
    stem = journal.delta_id if journal.operation == "confirm" else journal.transaction_id
    if stem is None or re.fullmatch(_SAFE_ID_PATTERN, stem) is None:
        raise AuthoringAtomicError("transaction before-stage id is invalid")
    return _safe_resolve(
        workspace,
        f"locks/transactions/{stem}-{index:02}.before",
    )


def _semantic_path(
    workspace: Workspace,
    *,
    kind: _ChangeKind,
    entity_id: str | None,
    target_path: str | None,
) -> Path:
    if kind == "authority":
        relative = "locks/authoring-authority.json"
    elif kind == "source_register":
        relative = "sources/source-register.yaml"
    elif kind == "material_bindings":
        relative = "locks/source-material-bindings.json"
    elif kind == "evidence":
        if entity_id is None:
            raise AuthoringAtomicError("evidence transaction source id is missing")
        relative = f"sources/extracted/{entity_id}.json"
    elif kind == "proposal":
        if entity_id is None or re.fullmatch(_DELTA_PATTERN, entity_id) is None:
            raise AuthoringAtomicError("proposal transaction delta id is invalid")
        relative = f"authoring/proposals/{entity_id}.yaml"
    elif kind == "session":
        relative = "authoring/sessions/current/session.yaml"
    elif kind == "target":
        if target_path is None or re.fullmatch(_TARGET_PATTERN, target_path) is None:
            raise AuthoringAtomicError("target transaction path is invalid")
        relative = target_path
    elif kind == "revision":
        relative = "locks/authoring-revision.json"
    else:
        raise AuthoringAtomicError("unknown transaction semantic path")
    return _safe_resolve(workspace, relative)


def _safe_resolve(workspace: Workspace, relative: str) -> Path:
    if (
        Path(relative).is_absolute()
        or "\\" in relative
        or ":" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise AuthoringAtomicError("unsafe transaction path")
    try:
        ArchiveEntry(
            path=relative,
            role="authoring-transaction",
            media_type="application/octet-stream",
            byte_count=0,
            sha256="sha256:" + "0" * 64,
        )
    except ValidationError as exc:
        raise AuthoringAtomicError("non-portable transaction path") from exc
    root = workspace.root.resolve()
    candidate = workspace.root.joinpath(*relative.split("/"))
    resolved = candidate.resolve(strict=False)
    try:
        if os.path.commonpath((str(root), str(resolved))) != str(root):
            raise AuthoringAtomicError("transaction path escapes workspace")
    except ValueError as exc:
        raise AuthoringAtomicError("transaction path drive mismatch") from exc
    current = workspace.root
    for part in relative.split("/")[:-1]:
        current = current / part
        if not current.exists():
            continue
        info = os.lstat(current)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        attributes = getattr(info, "st_file_attributes", 0)
        if stat.S_ISLNK(info.st_mode) or (reparse and attributes & reparse):
            raise AuthoringAtomicError("transaction path crosses a linked directory")
    if candidate.exists() or os.path.lexists(candidate):
        info = os.lstat(candidate)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        attributes = getattr(info, "st_file_attributes", 0)
        if (
            stat.S_ISLNK(info.st_mode)
            or (reparse and attributes & reparse)
            or not stat.S_ISREG(info.st_mode)
        ):
            raise AuthoringAtomicError("transaction target is not a plain file")
    return candidate


def _ensure_safe_plain_file(workspace: Workspace, path: Path) -> None:
    relative = path.relative_to(workspace.root).as_posix()
    if _safe_resolve(workspace, relative) != path:
        raise AuthoringAtomicError("transaction file path substitution")


def _read_safe_file(workspace: Workspace, path: Path) -> bytes:
    _ensure_safe_plain_file(workspace, path)
    return _read_control_file(path)


def _existing_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return _digest(_read_control_file(path))


def _write_journal(path: Path, journal: _TransactionJournal) -> None:
    if journal.provider_transaction_digest is None:
        raise AuthoringAtomicError("refusing to write an unreserved transaction journal")
    _durable_write(path, _canonical_json(journal.model_dump(mode="json")))


def _discard_unapplied_transaction(
    workspace: Workspace,
    journal_path: Path,
    journal: _TransactionJournal,
) -> None:
    for index in range(len(journal.changes)):
        before_path = _before_stage_path(workspace, journal, index)
        stage_path = _stage_path(workspace, journal, index)
        if before_path.exists():
            before_path.unlink()
        if stage_path.exists():
            stage_path.unlink()
    if journal_path.exists():
        journal_path.unlink()
    _sync_directory(journal_path.parent)


def _inject_kill(point: str) -> None:
    if _TEST_KILL_POINT is not None:
        _TEST_KILL_POINT(point)


def _linked_or_reparse(info: os.stat_result) -> bool:
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISLNK(info.st_mode) or bool(reparse and attributes & reparse)


def _validate_workspace_and_locks(root: Path) -> Workspace:
    try:
        root_info = os.lstat(root)
        locks_path = root / "locks"
        locks_info = os.lstat(locks_path)
    except OSError as exc:
        raise AuthoringAtomicError("workspace root or locks directory is unavailable") from exc
    if (
        _linked_or_reparse(root_info)
        or not stat.S_ISDIR(root_info.st_mode)
        or _linked_or_reparse(locks_info)
        or not stat.S_ISDIR(locks_info.st_mode)
    ):
        raise AuthoringAtomicError("workspace root and locks path must be ordinary directories")
    try:
        current = Workspace.open(root)
    except (WorkspaceError, OSError) as exc:
        raise AuthoringAtomicError("workspace validation failed before lock") from exc
    if current.root.absolute() != root.absolute():
        raise AuthoringAtomicError("workspace root identity changed")
    return current


@contextmanager
def _locked_workspace(
    workspace: WorkspaceRef,
    provider: AuthoringTrustProvider,
) -> Iterator[Workspace]:
    root = _workspace_root(workspace)
    _validate_workspace_and_locks(root)
    with _authoring_lock(root):
        current = _validate_workspace_and_locks(root)
        transaction_dir = current.root / "locks" / "transactions"
        if not transaction_dir.exists() or not any(transaction_dir.glob("*.journal")):
            _load_authority(current, provider, required=False)
        _recover_transactions(current, provider)
        current = _validate_workspace_and_locks(root)
        _load_authority(current, provider, required=False)
        yield current


def _workspace_root(workspace: WorkspaceRef) -> Path:
    value = workspace.root if isinstance(workspace, Workspace) else workspace
    return Path(value).absolute()


@contextmanager
def _authoring_lock(root: Path) -> Iterator[None]:
    if os.name == "nt":
        with _windows_authoring_lock(root):
            yield
    else:
        with _posix_authoring_lock(root):
            yield


@contextmanager
def _posix_authoring_lock(root: Path) -> Iterator[None]:
    locks_path = root / "locks"
    directory_flags = os.O_RDONLY
    directory_flags |= getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        directory_descriptor = os.open(locks_path, directory_flags)
    except OSError as exc:
        raise AuthoringAtomicError("cannot open verified locks directory") from exc
    descriptor: int | None = None
    try:
        directory_info = os.fstat(directory_descriptor)
        path_info = os.stat(locks_path, follow_symlinks=False)
        if (
            not stat.S_ISDIR(directory_info.st_mode)
            or _linked_or_reparse(path_info)
            or (directory_info.st_dev, directory_info.st_ino)
            != (path_info.st_dev, path_info.st_ino)
        ):
            raise AuthoringAtomicError("locks directory identity changed")
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        flags |= getattr(os, "O_NOFOLLOW", 0)
        while descriptor is None:
            try:
                descriptor = os.open(
                    "authoring.lock",
                    flags,
                    0o600,
                    dir_fd=directory_descriptor,
                )
            except FileExistsError as exc:
                if time.monotonic() >= deadline:
                    raise AuthoringConflictError(
                        "authoring workspace is busy or stale-locked"
                    ) from exc
                time.sleep(0.01)
        os.write(descriptor, b"ontowiz-authoring-lock\n")
        os.fsync(descriptor)
        path_info = os.stat(locks_path, follow_symlinks=False)
        if (directory_info.st_dev, directory_info.st_ino) != (
            path_info.st_dev,
            path_info.st_ino,
        ):
            raise AuthoringAtomicError("locks directory was swapped during acquisition")
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
            try:
                os.unlink("authoring.lock", dir_fd=directory_descriptor)
                os.fsync(directory_descriptor)
            except OSError as exc:
                raise AuthoringAtomicError("cannot release authoring workspace lock") from exc
        os.close(directory_descriptor)


class _WindowsFileInformation(ctypes.Structure):
    _fields_ = [
        ("file_attributes", ctypes.c_uint32),
        ("creation_time_low", ctypes.c_uint32),
        ("creation_time_high", ctypes.c_uint32),
        ("last_access_time_low", ctypes.c_uint32),
        ("last_access_time_high", ctypes.c_uint32),
        ("last_write_time_low", ctypes.c_uint32),
        ("last_write_time_high", ctypes.c_uint32),
        ("volume_serial_number", ctypes.c_uint32),
        ("file_size_high", ctypes.c_uint32),
        ("file_size_low", ctypes.c_uint32),
        ("number_of_links", ctypes.c_uint32),
        ("file_index_high", ctypes.c_uint32),
        ("file_index_low", ctypes.c_uint32),
    ]


class _WindowsUnicodeString(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ushort),
        ("maximum_length", ctypes.c_ushort),
        ("buffer", ctypes.POINTER(ctypes.c_wchar)),
    ]


class _WindowsObjectAttributes(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ulong),
        ("root_directory", ctypes.c_void_p),
        ("object_name", ctypes.POINTER(_WindowsUnicodeString)),
        ("attributes", ctypes.c_ulong),
        ("security_descriptor", ctypes.c_void_p),
        ("security_quality_of_service", ctypes.c_void_p),
    ]


class _WindowsIoStatusValue(ctypes.Union):
    _fields_ = [
        ("status", ctypes.c_long),
        ("pointer", ctypes.c_void_p),
    ]


class _WindowsIoStatusBlock(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [
        ("value", _WindowsIoStatusValue),
        ("information", ctypes.c_size_t),
    ]


def _windows_file_information(
    kernel32: object,
    handle: int,
) -> _WindowsFileInformation:
    info = _WindowsFileInformation()
    get_info = getattr(kernel32, "GetFileInformationByHandle")  # noqa: B009
    get_info.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    get_info.restype = ctypes.c_int
    if not get_info(handle, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    return info


def _windows_file_identity(info: _WindowsFileInformation) -> tuple[int, int, int]:
    return (
        info.volume_serial_number,
        info.file_index_high,
        info.file_index_low,
    )


@contextmanager
def _windows_authoring_lock(root: Path) -> Iterator[None]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    create_file.restype = ctypes.c_void_p
    nt_create_file = ntdll.NtCreateFile
    nt_create_file.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_ulong,
        ctypes.POINTER(_WindowsObjectAttributes),
        ctypes.POINTER(_WindowsIoStatusBlock),
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_ulong,
    ]
    nt_create_file.restype = ctypes.c_long
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int
    write_file = kernel32.WriteFile
    write_file.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.c_void_p,
    ]
    write_file.restype = ctypes.c_int
    flush_file = kernel32.FlushFileBuffers
    flush_file.argtypes = [ctypes.c_void_p]
    flush_file.restype = ctypes.c_int
    invalid_handle = ctypes.c_void_p(-1).value
    file_read_attributes = 0x0080
    file_write_data = 0x0002
    delete_access = 0x00010000
    synchronize = 0x00100000
    share_read = 0x00000001
    share_write = 0x00000002
    open_existing = 3
    backup_semantics = 0x02000000
    open_reparse_point = 0x00200000
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400
    file_create = 2
    file_non_directory_file = 0x00000040
    file_delete_on_close = 0x00001000
    file_open_reparse_point = 0x00200000
    file_synchronous_io_nonalert = 0x00000020
    object_case_insensitive = 0x00000040
    retry_statuses = {0xC0000022, 0xC0000035, 0xC0000043}

    def open_directory(path: Path) -> int:
        handle = create_file(
            str(path),
            file_read_attributes,
            share_read | share_write,
            None,
            open_existing,
            backup_semantics | open_reparse_point,
            None,
        )
        if handle == invalid_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        return int(handle)

    root_handle: int | None = None
    directory_handle: int | None = None
    lock_handle: int | None = None
    try:
        root_handle = open_directory(root)
        directory_handle = open_directory(root / "locks")
        root_info = _windows_file_information(kernel32, root_handle)
        directory_info = _windows_file_information(kernel32, directory_handle)
        for label, info in (("root", root_info), ("locks", directory_info)):
            if (
                not info.file_attributes & file_attribute_directory
                or info.file_attributes & file_attribute_reparse_point
            ):
                raise AuthoringAtomicError(
                    f"Windows {label} directory is linked or not a directory"
                )
        lock_name_buffer = ctypes.create_unicode_buffer("authoring.lock")
        lock_name = _WindowsUnicodeString(
            length=len("authoring.lock") * ctypes.sizeof(ctypes.c_wchar),
            maximum_length=ctypes.sizeof(lock_name_buffer),
            buffer=ctypes.cast(
                lock_name_buffer,
                ctypes.POINTER(ctypes.c_wchar),
            ),
        )
        attributes = _WindowsObjectAttributes(
            length=ctypes.sizeof(_WindowsObjectAttributes),
            root_directory=directory_handle,
            object_name=ctypes.pointer(lock_name),
            attributes=object_case_insensitive,
            security_descriptor=None,
            security_quality_of_service=None,
        )
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        _inject_kill("before-windows-relative-lock-create")
        while lock_handle is None:
            candidate = ctypes.c_void_p()
            io_status = _WindowsIoStatusBlock()
            status = nt_create_file(
                ctypes.byref(candidate),
                file_write_data | delete_access | synchronize,
                ctypes.byref(attributes),
                ctypes.byref(io_status),
                None,
                0,
                share_read,
                file_create,
                (
                    file_non_directory_file
                    | file_delete_on_close
                    | file_open_reparse_point
                    | file_synchronous_io_nonalert
                ),
                None,
                0,
            )
            unsigned_status = ctypes.c_uint32(status).value
            if unsigned_status == 0:
                if candidate.value is None:
                    raise AuthoringAtomicError("NtCreateFile returned no lock handle")
                lock_handle = candidate.value
                break
            if unsigned_status not in retry_statuses:
                raise OSError(f"NtCreateFile failed with NTSTATUS 0x{unsigned_status:08x}")
            if time.monotonic() >= deadline:
                raise AuthoringConflictError("authoring workspace is busy or stale-locked")
            time.sleep(0.01)
        payload = b"ontowiz-authoring-lock\n"
        written = ctypes.c_uint32()
        buffer = ctypes.create_string_buffer(payload)
        if not write_file(
            lock_handle,
            buffer,
            len(payload),
            ctypes.byref(written),
            None,
        ) or written.value != len(payload):
            raise ctypes.WinError(ctypes.get_last_error())
        if not flush_file(lock_handle):
            raise ctypes.WinError(ctypes.get_last_error())
        fresh_root = open_directory(root)
        fresh_locks = open_directory(root / "locks")
        try:
            if _windows_file_identity(
                _windows_file_information(kernel32, fresh_root)
            ) != _windows_file_identity(root_info) or _windows_file_identity(
                _windows_file_information(kernel32, fresh_locks)
            ) != _windows_file_identity(directory_info):
                raise AuthoringAtomicError(
                    "Windows workspace directory identity changed during lock"
                )
        finally:
            close_handle(fresh_locks)
            close_handle(fresh_root)
        _validate_workspace_and_locks(root)
        yield
    except OSError as exc:
        raise AuthoringAtomicError("Windows authoring lock operation failed") from exc
    finally:
        if lock_handle is not None and not close_handle(lock_handle):
            raise AuthoringAtomicError("cannot close Windows authoring lock")
        if directory_handle is not None and not close_handle(directory_handle):
            raise AuthoringAtomicError("cannot close Windows locks directory handle")
        if root_handle is not None and not close_handle(root_handle):
            raise AuthoringAtomicError("cannot close Windows workspace root handle")


def _durable_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 1.0
    while True:
        try:
            _atomic_write(path, payload)
            break
        except WorkspaceError:
            if os.name != "nt" or time.monotonic() >= deadline:
                raise
            time.sleep(0.01)
    _sync_directory(path.parent)


def _sync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY)
        os.fsync(descriptor)
    except OSError as exc:
        raise AuthoringAtomicError(f"cannot synchronize directory: {path.name}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _is_aware(value: datetime | None) -> bool:
    return value is not None and value.tzinfo is not None and value.utcoffset() is not None


def _quote_digest(payload: str) -> str:
    normalized = unicodedata.normalize("NFC", payload).encode("utf-8")
    return _digest(normalized)


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()
