from __future__ import annotations

import hashlib
import inspect
import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import JsonValue

import ontowiz_authoring.authoring as authoring_module
from ontowiz_authoring.authoring import (
    ActorCapability,
    AuthoringConflictError,
    AuthoringProviderState,
    AuthoringTransactionIdentity,
    AuthoringTrustContext,
    AuthoringValidationError,
    AuthorityHighWater,
    AuthorityStatement,
    JournalAttestation,
    OperationCredential,
    PrincipalGrant,
    Proposal,
    RecoveryAuthorization,
    SignedAuthority,
    StaleProposalError,
    authoring_transaction_digest,
    operation_credential_bytes,
)
from ontowiz_authoring.authoring import (
    ActorCapability as _CoreActorCapability,
)
from ontowiz_authoring.authoring import (
    compile_questions as _core_compile_questions,
)
from ontowiz_authoring.authoring import (
    confirm_proposal as _core_confirm_proposal,
)
from ontowiz_authoring.authoring import (
    get_workspace_revision as _core_get_workspace_revision,
)
from ontowiz_authoring.authoring import (
    install_signed_authority as _core_install_signed_authority,
)
from ontowiz_authoring.authoring import (
    load_proposal as _core_load_proposal,
)
from ontowiz_authoring.authoring import (
    load_session_state as _core_load_session_state,
)
from ontowiz_authoring.authoring import (
    propose_replacement as _core_propose_replacement,
)
from ontowiz_authoring.authoring import (
    record_evidence as _core_record_evidence,
)
from ontowiz_authoring.authoring import (
    register_source as _core_register_source,
)
from ontowiz_authoring.authoring import (
    update_session_state as _core_update_session_state,
)
from ontowiz_authoring.authoring import (
    update_source as _core_update_source,
)
from ontowiz_authoring.authoring import (
    validate_authoring as _core_validate_authoring,
)
from ontowiz_authoring.authoring import (
    withdraw_source as _core_withdraw_source,
)
from ontowiz_authoring.workspace import Workspace
from ontowiz_spec import EvidenceRef, SourceRecord


def _canonical(value: object) -> bytes:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", encoded) + "\n").encode("utf-8")


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class _TestActor:
    provider: _TestTrustProvider
    signing_principal: str
    workspace_id: str
    principal_id: str
    roles: tuple[str, ...]
    client_boundary: str
    authority_revision: int
    authority_digest: str | None
    trust_key_id: str

    def model_copy(self, *, update: Mapping[str, object]) -> _TestActor:
        return dataclass_replace(self, **update)


class _TestTrustProvider:
    """Test-only provider; production contains no local trust implementation."""

    def __init__(
        self,
        workspace_id: str,
        authority_key: Ed25519PrivateKey,
        bootstrap_role: str = "steward",
    ) -> None:
        self.workspace_id = workspace_id
        self.authority_key = authority_key
        public_key = authority_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        self._high_water = AuthorityHighWater(
            format="ontowiz-authority-high-water",
            format_version=1,
            workspace_id=workspace_id,
            trust_key_id=_digest(public_key),
            authority_public_key=public_key.hex(),
            authority_revision=0,
            authority_digest=None,
        )
        self._journal_key = Ed25519PrivateKey.from_private_bytes(
            hashlib.sha256(("journal:" + workspace_id).encode()).digest()
        )
        journal_public = self._journal_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        self._journal_key_id = _digest(journal_public)
        self._actor_keys: dict[str, Ed25519PrivateKey] = {}
        self._actors: dict[str, tuple[tuple[str, ...], str]] = {
            "host-admin": ((bootstrap_role,), "client-a"),
        }
        self._used_nonces: dict[str, str] = {}
        self._authoring_revision = 0
        self._pending: AuthoringTransactionIdentity | None = None
        self._last_finalized: AuthoringTransactionIdentity | None = None
        self._recovery_credential_digest: str | None = None
        self._counter = 0
        self._lock = Lock()

    def authority_high_water(self, workspace_id: str) -> AuthorityHighWater:
        if workspace_id != self.workspace_id:
            raise RuntimeError("unknown test workspace")
        with self._lock:
            return self._high_water

    def set_grants(self, grants: Sequence[PrincipalGrant]) -> None:
        with self._lock:
            for grant in grants:
                self._actors[grant.principal_id] = (
                    grant.roles,
                    grant.client_boundary,
                )

    def _actor_key(self, principal_id: str) -> Ed25519PrivateKey:
        with self._lock:
            key = self._actor_keys.get(principal_id)
            if key is None:
                key = Ed25519PrivateKey.from_private_bytes(
                    hashlib.sha256((self.workspace_id + ":" + principal_id).encode()).digest()
                )
                self._actor_keys[principal_id] = key
            return key

    def actor(self, principal_id: str) -> _TestActor:
        with self._lock:
            roles, boundary = self._actors[principal_id]
            high_water = self._high_water
        return _TestActor(
            provider=self,
            signing_principal=principal_id,
            workspace_id=self.workspace_id,
            principal_id=principal_id,
            roles=roles,
            client_boundary=boundary,
            authority_revision=high_water.authority_revision,
            authority_digest=high_water.authority_digest,
            trust_key_id=high_water.trust_key_id,
        )

    def context(
        self,
        actor: _TestActor,
        intent_digest: str,
    ) -> AuthoringTrustContext:
        with self._lock:
            self._counter += 1
            nonce = f"nonce-{self._counter:08d}"
        signing_key = self._actor_key(actor.signing_principal)
        actor_public = signing_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        unsigned = OperationCredential(
            format="ontowiz-operation-credential",
            format_version=1,
            workspace_id=actor.workspace_id,
            principal_id=actor.principal_id,
            roles=actor.roles,
            client_boundary=actor.client_boundary,
            authority_revision=actor.authority_revision,
            authority_digest=actor.authority_digest,
            trust_key_id=actor.trust_key_id,
            intent_digest=intent_digest,
            nonce=nonce,
            issued_at=datetime(2026, 7, 25, tzinfo=UTC),
            expires_at=datetime(2036, 7, 25, tzinfo=UTC),
            actor_key_id=_digest(actor_public),
            proof_signature="0" * 128,
        )
        credential = unsigned.model_copy(
            update={"proof_signature": signing_key.sign(operation_credential_bytes(unsigned)).hex()}
        )
        return AuthoringTrustContext(provider=self, credential=credential)

    def authenticate_actor(
        self,
        credential: OperationCredential,
        *,
        expected_intent_digest: str,
        now: datetime,
    ) -> _CoreActorCapability:
        del now
        credential_digest = _digest(_canonical(credential.model_dump(mode="json")))
        with self._lock:
            high_water = self._high_water
            expected_actor = self._actors.get(credential.principal_id)
            pending_match = (
                self._pending is not None
                and self._pending.credential_nonce == credential.nonce
                and self._pending.credential_digest == credential_digest
                and self._pending.intent_digest == expected_intent_digest
            )
            finalized_match = (
                self._last_finalized is not None
                and self._last_finalized.credential_nonce == credential.nonce
                and self._last_finalized.credential_digest == credential_digest
                and self._last_finalized.intent_digest == expected_intent_digest
            )
            recovery_replay = self._recovery_credential_digest == credential_digest and (
                pending_match or finalized_match
            )
            nonce_digest = self._used_nonces.get(credential.nonce)
            if nonce_digest is not None and (
                nonce_digest != credential_digest or not recovery_replay
            ):
                raise RuntimeError("credential nonce replay")
            if expected_actor is None:
                raise RuntimeError("unknown actor")
            authority_matches = (
                credential.authority_revision == high_water.authority_revision
                and credential.authority_digest == high_water.authority_digest
            )
            if pending_match:
                authority_matches = (
                    credential.authority_revision == self._pending.authority_revision
                    and credential.authority_digest == self._pending.authority_digest
                )
            elif finalized_match:
                authority_matches = (
                    credential.authority_revision == self._last_finalized.authority_revision
                    and credential.authority_digest == self._last_finalized.authority_digest
                )
            if (
                credential.intent_digest != expected_intent_digest
                or not authority_matches
                or credential.trust_key_id != high_water.trust_key_id
                or (credential.roles, credential.client_boundary) != expected_actor
            ):
                raise RuntimeError("credential claims are not externally authorized")
        key = self._actor_key(credential.principal_id)
        public_key = key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        if credential.actor_key_id != _digest(public_key):
            raise RuntimeError("actor key id mismatch")
        key.public_key().verify(
            bytes.fromhex(credential.proof_signature),
            operation_credential_bytes(credential),
        )
        with self._lock:
            nonce_digest = self._used_nonces.get(credential.nonce)
            if nonce_digest is not None and nonce_digest != credential_digest:
                raise RuntimeError("credential nonce substitution")
            self._used_nonces[credential.nonce] = credential_digest
            self._recovery_credential_digest = None
        return _CoreActorCapability(
            format="ontowiz-authenticated-actor",
            format_version=1,
            workspace_id=credential.workspace_id,
            principal_id=credential.principal_id,
            roles=credential.roles,
            client_boundary=credential.client_boundary,
            authority_revision=credential.authority_revision,
            authority_digest=credential.authority_digest,
            trust_key_id=credential.trust_key_id,
            intent_digest=credential.intent_digest,
            credential_nonce=credential.nonce,
        )

    def authenticate_recovery(
        self,
        identity: AuthoringTransactionIdentity,
        authorization: RecoveryAuthorization,
    ) -> _CoreActorCapability:
        transaction_digest = authoring_transaction_digest(identity)
        with self._lock:
            exact_pending = (
                authorization.status == "pending"
                and self._pending == identity
                and self._authoring_revision == identity.revision_before
            )
            exact_finalized = (
                authorization.status == "finalized"
                and self._last_finalized == identity
                and self._authoring_revision == identity.revision_after
            )
            expected_actor = self._actors.get(identity.actor_principal)
            if (
                not (exact_pending or exact_finalized)
                or authorization.workspace_id != self.workspace_id
                or authorization.transaction_digest != transaction_digest
                or expected_actor is None
            ):
                raise RuntimeError("recovery identity mismatch")
            roles, client_boundary = expected_actor
            self._recovery_credential_digest = None
        return _CoreActorCapability(
            format="ontowiz-authenticated-actor",
            format_version=1,
            workspace_id=identity.workspace_id,
            principal_id=identity.actor_principal,
            roles=roles,
            client_boundary=client_boundary,
            authority_revision=identity.authority_revision,
            authority_digest=identity.authority_digest,
            trust_key_id=identity.trust_key_id,
            intent_digest=identity.intent_digest,
            credential_nonce=identity.credential_nonce,
        )

    def attest_journal(self, journal_identity: bytes) -> JournalAttestation:
        return JournalAttestation(
            format="ontowiz-journal-attestation",
            format_version=1,
            provider_id="test-provider",
            key_id=self._journal_key_id,
            value=self._journal_key.sign(journal_identity).hex(),
        )

    def verify_journal(
        self,
        journal_identity: bytes,
        attestation: JournalAttestation,
    ) -> None:
        if attestation.key_id != self._journal_key_id:
            raise RuntimeError("wrong journal key")
        self._journal_key.public_key().verify(
            bytes.fromhex(attestation.value),
            journal_identity,
        )

    def authoring_state(self, workspace_id: str) -> AuthoringProviderState:
        if workspace_id != self.workspace_id:
            raise RuntimeError("unknown test workspace")
        with self._lock:
            finalized = self._last_finalized
            return AuthoringProviderState(
                format="ontowiz-provider-state",
                format_version=1,
                workspace_id=self.workspace_id,
                authoring_revision=self._authoring_revision,
                pending=self._pending,
                last_finalized=finalized,
                last_finalized_transaction_id=(
                    finalized.transaction_id if finalized is not None else None
                ),
                last_finalized_transaction_digest=(
                    authoring_transaction_digest(finalized) if finalized is not None else None
                ),
            )

    def reserve_transaction(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> None:
        with self._lock:
            if (
                identity.workspace_id != self.workspace_id
                or self._pending is not None
                or identity.revision_before != self._authoring_revision
                or identity.revision_after != self._authoring_revision + 1
            ):
                raise RuntimeError("transaction reservation compare-and-swap failed")
            self._pending = identity

    def authorize_recovery(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> RecoveryAuthorization:
        digest = authoring_transaction_digest(identity)
        with self._lock:
            if self._pending == identity:
                status = "pending"
                revision = self._authoring_revision
            elif (
                self._last_finalized == identity
                and self._authoring_revision == identity.revision_after
            ):
                status = "finalized"
                revision = self._authoring_revision
            else:
                raise RuntimeError("transaction is neither exact pending nor last finalized")
            self._recovery_credential_digest = identity.credential_digest
        return RecoveryAuthorization(
            format="ontowiz-recovery-authorization",
            format_version=1,
            workspace_id=self.workspace_id,
            transaction_digest=digest,
            status=status,
            authoring_revision=revision,
        )

    def finalize_transaction(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> None:
        with self._lock:
            if (
                self._last_finalized == identity
                and self._authoring_revision == identity.revision_after
            ):
                return
            if self._pending != identity or self._authoring_revision != identity.revision_before:
                raise RuntimeError("transaction finalize compare-and-swap failed")
            self._authoring_revision = identity.revision_after
            self._last_finalized = identity
            self._pending = None

    def abort_reserved_transaction(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> None:
        with self._lock:
            if self._pending != identity or self._authoring_revision != identity.revision_before:
                raise RuntimeError("transaction abort compare-and-swap failed")
            self._pending = None

    def force_pending_for_test(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> None:
        with self._lock:
            if identity.revision_before != self._authoring_revision:
                raise RuntimeError("forced transaction has wrong before revision")
            self._pending = identity

    def advance_authority(
        self,
        *,
        expected: AuthorityHighWater,
        replacement: AuthorityHighWater,
    ) -> None:
        with self._lock:
            if self._high_water != expected:
                raise RuntimeError("authority compare-and-swap failed")
            if (
                replacement.trust_key_id != expected.trust_key_id
                or replacement.authority_public_key != expected.authority_public_key
                or replacement.authority_revision != expected.authority_revision + 1
            ):
                raise RuntimeError("invalid authority high-water advance")
            self._high_water = replacement


_TEST_PROVIDERS: dict[str, _TestTrustProvider] = {}


def _workspace_key(workspace: object) -> str:
    if isinstance(workspace, Workspace):
        return str(workspace.root.absolute())
    return str(Path(workspace).absolute())


def _provider(workspace: object) -> _TestTrustProvider:
    return _TEST_PROVIDERS[_workspace_key(workspace)]


def _intent(
    operation: str,
    workspace: object,
    expected_revision: int | None,
    request: Mapping[str, object],
) -> str:
    return authoring_module._mutation_intent(
        operation,
        _provider(workspace).workspace_id,
        expected_revision,
        request,
    )


def get_workspace_revision(workspace: object) -> int:
    provider = _provider(workspace)
    return _core_get_workspace_revision(workspace, provider)


def load_actor_capability(workspace: object, principal_id: str) -> _TestActor:
    return _provider(workspace).actor(principal_id)


def register_source(
    workspace: object,
    source: SourceRecord,
    *,
    material_path: str | None = None,
    expected_revision: int | None = None,
) -> SourceRecord:
    provider = _provider(workspace)
    intent = _intent(
        "register_source",
        workspace,
        expected_revision,
        {"source": source.model_dump(mode="json"), "material_path": material_path},
    )
    return _core_register_source(
        workspace,
        source,
        trust=provider.context(provider.actor("draft-agent"), intent),
        material_path=material_path,
        expected_revision=expected_revision,
    )


def update_source(
    workspace: object,
    source: SourceRecord,
    *,
    expected_revision: int | None = None,
) -> SourceRecord:
    provider = _provider(workspace)
    intent = _intent(
        "update_source",
        workspace,
        expected_revision,
        {"source": source.model_dump(mode="json")},
    )
    return _core_update_source(
        workspace,
        source,
        trust=provider.context(provider.actor("draft-agent"), intent),
        expected_revision=expected_revision,
    )


def withdraw_source(
    workspace: object,
    source_id: str,
    *,
    withdrawn_at: datetime,
    expected_revision: int | None = None,
) -> SourceRecord:
    provider = _provider(workspace)
    intent = _intent(
        "withdraw_source",
        workspace,
        expected_revision,
        {"source_id": source_id, "withdrawn_at": withdrawn_at.isoformat()},
    )
    return _core_withdraw_source(
        workspace,
        source_id,
        trust=provider.context(provider.actor("draft-agent"), intent),
        withdrawn_at=withdrawn_at,
        expected_revision=expected_revision,
    )


def record_evidence(
    workspace: object,
    evidence: EvidenceRef,
    *,
    quote_payload: str | None = None,
    expected_revision: int | None = None,
) -> EvidenceRef:
    provider = _provider(workspace)
    intent = _intent(
        "record_evidence",
        workspace,
        expected_revision,
        {
            "evidence": evidence.model_dump(mode="json"),
            "quote_payload": quote_payload,
        },
    )
    return _core_record_evidence(
        workspace,
        evidence,
        trust=provider.context(provider.actor("draft-agent"), intent),
        quote_payload=quote_payload,
        expected_revision=expected_revision,
    )


def propose_replacement(
    workspace: object,
    *,
    actor: _TestActor,
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
    request: dict[str, object] = {
        "delta_id": delta_id,
        "target_owner_role": target_owner_role,
        "allowed_confirmer_roles": sorted(set(allowed_confirmer_roles)),
        "target_path": target_path,
        "expected_target_digest": expected_target_digest,
        "replacement_body": dict(replacement_body),
        "evidence_ids": sorted(set(evidence_ids)),
        "rationale": rationale,
    }
    intent = _intent("propose", workspace, expected_revision, request)
    return _core_propose_replacement(
        workspace,
        trust=actor.provider.context(actor, intent),
        delta_id=delta_id,
        target_owner_role=target_owner_role,
        allowed_confirmer_roles=allowed_confirmer_roles,
        target_path=target_path,
        expected_target_digest=expected_target_digest,
        replacement_body=replacement_body,
        evidence_ids=evidence_ids,
        rationale=rationale,
        expected_revision=expected_revision,
    )


def confirm_proposal(
    workspace: object,
    delta_id: str,
    *,
    actor: _TestActor,
    confirmed_at: datetime,
    expected_revision: int | None = None,
) -> Proposal:
    current = workspace if isinstance(workspace, Workspace) else Workspace.open(Path(workspace))
    proposal = authoring_module._load_proposal_path(
        current,
        authoring_module._proposal_path(current, delta_id),
    )
    request: dict[str, object] = {
        "delta_id": delta_id,
        "confirmed_at": confirmed_at.isoformat(),
    }
    credential_revision = expected_revision
    if proposal.status == "proposed":
        revision = authoring_module._load_revision(current)
        if credential_revision is None:
            credential_revision = revision.revision
        planned_session = authoring_module._confirmation_session_after(
            current,
            revision,
            delta_id,
        )
        request["session"] = planned_session.model_dump(mode="json")
    intent = _intent(
        "confirm",
        workspace,
        credential_revision,
        request,
    )
    return _core_confirm_proposal(
        workspace,
        delta_id,
        trust=actor.provider.context(actor, intent),
        confirmed_at=confirmed_at,
        expected_revision=credential_revision,
    )


def update_session_state(
    workspace: object,
    *,
    stage: str,
    last_delta_id: str | None,
    open_question_ids: Sequence[str],
    next_mission: str,
    expected_revision: int,
) -> object:
    provider = _provider(workspace)
    intent = _intent(
        "update_session",
        workspace,
        expected_revision,
        {
            "stage": stage,
            "last_delta_id": last_delta_id,
            "open_question_ids": sorted(set(open_question_ids)),
            "next_mission": next_mission,
        },
    )
    return _core_update_session_state(
        workspace,
        trust=provider.context(provider.actor("draft-agent"), intent),
        stage=stage,
        last_delta_id=last_delta_id,
        open_question_ids=open_question_ids,
        next_mission=next_mission,
        expected_revision=expected_revision,
    )


def compile_questions(workspace: object) -> object:
    return _core_compile_questions(workspace, _provider(workspace))


def load_proposal(workspace: object, delta_id: str) -> Proposal:
    return _core_load_proposal(workspace, delta_id, _provider(workspace))


def load_session_state(workspace: object) -> object:
    return _core_load_session_state(workspace, _provider(workspace))


def validate_authoring(workspace: object) -> object:
    return _core_validate_authoring(workspace, _provider(workspace))


def _workspace(
    tmp_path: Path,
    *,
    name: str = "workspace",
    workspace_id: str = "brand-variance",
    owner_roles: Sequence[str] = ("steward", "brand_owner", "approver"),
) -> Workspace:
    workspace = Workspace.initialize(
        tmp_path / name,
        workspace_id=workspace_id,
        owner_roles=owner_roles,
        archetypes=("enterprise_core", "brand_analytics"),
    )
    key = Ed25519PrivateKey.from_private_bytes(
        hashlib.sha256(b"ontowiz-test-authority-key").digest()
    )
    _TEST_PROVIDERS[_workspace_key(workspace)] = _TestTrustProvider(
        workspace_id,
        key,
        bootstrap_role=owner_roles[0],
    )
    default_actors = (
        ("approver-1", "approver"),
        ("brand-1", "brand_owner"),
        ("draft-agent", "steward"),
    )
    _install_authority(
        workspace,
        grants=tuple(
            PrincipalGrant(
                principal_id=principal_id,
                roles=(role,),
                client_boundary="client-a",
            )
            for principal_id, role in default_actors
            if role in owner_roles
        ),
    )
    return workspace


def _source(**changes: object) -> SourceRecord:
    data: dict[str, object] = {
        "id": "SRC-001",
        "title": "Weekly brand data dictionary",
        "owner_role": "data_steward",
        "checksum": "sha256:" + "b" * 64,
        "source_date": "2026-01-01",
        "fresh_until": "2026-12-31",
        "scope": ["GB", "Brand A"],
        "client_boundary": "client-a",
        "confidentiality": "internal",
        "permitted_uses": ["candidate-derivation"],
        "quotation_allowed": True,
        "redistribution_allowed": False,
        "raw_transfer_allowed": False,
        "retention_until": "2026-12-31",
        "contains_personal_data": False,
        "personal_data_transfer_allowed": False,
        "consent_basis": None,
        "status": "current",
        "withdrawn_at": None,
    }
    data.update(changes)
    return SourceRecord.model_validate(data)


def _evidence(**changes: object) -> EvidenceRef:
    data: dict[str, object] = {
        "id": "EV-001",
        "source_id": "SRC-001",
        "source_checksum": "sha256:" + "b" * 64,
        "claim": "NBRx is below plan.",
        "locator_type": "page",
        "locator": "12",
        "mode": "observed",
        "permitted_use": "candidate-derivation",
        "quoted": False,
        "quote_digest": None,
        "valid_as_of": "2026-07-25",
        "extracted_at": "2026-07-25T12:00:00Z",
        "confidence": 0.9,
    }
    data.update(changes)
    return EvidenceRef.model_validate(data)


def _decision(decision: str, *, decision_id: str = "DEC-001") -> dict[str, JsonValue]:
    return {
        "id": decision_id,
        "decision": decision,
        "action_mode": "recommend",
        "human_owned_actions": ["Approve the commercial action."],
        "out_of_scope": ["Patient-level targeting."],
        "materially_unsafe_answers": ["Unsupported causal attribution."],
        "applicability": {
            "markets": ["GB"],
            "lifecycle_stages": ["launch"],
            "products": [],
            "audiences": [],
            "effective_from": "2026-01-01",
        },
        "owner_role": "brand_owner",
    }


def _eval_case(
    case_id: str,
    suite: str,
    *,
    required_context: Sequence[str],
) -> dict[str, JsonValue]:
    return {
        "id": case_id,
        "decision_id": "DEC-001",
        "suite": suite,
        "status": "candidate",
        "protected": False,
        "applicability": {
            "markets": ["GB"],
            "lifecycle_stages": ["launch"],
            "products": [],
            "audiences": [],
            "effective_from": "2026-01-01",
        },
        "scenario": [{"name": "actual_nbrx", "value": "80"}],
        "deliberately_missing": [],
        "required_behaviours": ["Quantify the variance."],
        "prohibited_behaviours": [],
        "required_context": list(required_context),
        "evidence_expectations": ["Cite the registered evidence."],
        "scoring": {
            "decision_quality": 1,
            "method": 1,
            "evidence": 1,
            "uncertainty": 1,
            "human_boundary": 1,
        },
        "critical_failures": ["Invent a metric value."],
        "provenance": {
            "mode": "sme_authored",
            "supplied_by": "brand_sme",
            "confidence": 0.9,
            "open_questions": [],
        },
    }


def _write_pack_document(workspace: Workspace, relative: str, body: object) -> Path:
    target = workspace.root / relative
    target.write_bytes(_canonical(body))
    return target


def _install_authority(
    workspace: Workspace,
    *,
    grants: Sequence[PrincipalGrant],
    signing_key: Ed25519PrivateKey | None = None,
    authority_revision: int | None = None,
) -> SignedAuthority:
    provider = _provider(workspace)
    high_water = provider.authority_high_water(workspace.manifest.workspace_id)
    revision = authority_revision or high_water.authority_revision + 1
    if high_water.authority_revision > 0 and authority_revision in {
        None,
        high_water.authority_revision,
    }:
        existing = authoring_module._load_authority(workspace, provider)
        if existing.statement.grants == tuple(sorted(grants, key=lambda item: item.principal_id)):
            return existing
    key = signing_key or provider.authority_key
    public_key = key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    statement = AuthorityStatement(
        format="ontowiz-authority-statement",
        format_version=1,
        workspace_id=workspace.manifest.workspace_id,
        authority_revision=revision,
        issued_at=datetime(2026, 7, 25, tzinfo=UTC),
        grants=tuple(sorted(grants, key=lambda item: item.principal_id)),
    )
    statement_bytes = authoring_module._authority_bytes(statement)
    authority = SignedAuthority(
        statement=statement,
        statement_digest=_digest(statement_bytes),
        signature=key.sign(statement_bytes).hex(),
        trust_key_id=_digest(public_key),
    )
    if high_water.authority_revision > 0:
        current_authority = authoring_module._load_authority(workspace, provider)
        actor = provider.actor(current_authority.statement.grants[0].principal_id)
    else:
        actor = provider.actor("host-admin")
    expected_revision = get_workspace_revision(workspace)
    intent = _intent(
        "install_authority",
        workspace,
        expected_revision,
        {"authority": authority.model_dump(mode="json")},
    )
    installed = _core_install_signed_authority(
        workspace,
        trust=provider.context(actor, intent),
        authority=authority,
        expected_revision=expected_revision,
    )
    provider.set_grants(grants)
    return installed


def _configure(
    workspace: Workspace,
) -> tuple[ActorCapability, ActorCapability, ActorCapability]:
    _install_authority(
        workspace,
        grants=(
            PrincipalGrant(
                principal_id="approver-1",
                roles=("approver",),
                client_boundary="client-a",
            ),
            PrincipalGrant(
                principal_id="brand-1",
                roles=("brand_owner",),
                client_boundary="client-a",
            ),
            PrincipalGrant(
                principal_id="draft-agent",
                roles=("steward",),
                client_boundary="client-a",
            ),
        ),
    )
    return (
        load_actor_capability(workspace, "draft-agent"),
        load_actor_capability(workspace, "brand-1"),
        load_actor_capability(workspace, "approver-1"),
    )


def _prepare_evidence(
    workspace: Workspace,
) -> tuple[ActorCapability, ActorCapability, ActorCapability]:
    actors = _configure(workspace)
    register_source(workspace, _source())
    record_evidence(workspace, _evidence())
    return actors


def _propose(
    workspace: Workspace,
    actor: ActorCapability,
    *,
    delta_id: str = "DELTA-001",
    target_path: str = "pack/scope/decision.json",
    expected_target_digest: str | None,
    replacement: Mapping[str, JsonValue],
) -> Proposal:
    return propose_replacement(
        workspace,
        actor=actor,
        delta_id=delta_id,
        target_owner_role="brand_owner",
        allowed_confirmer_roles=("brand_owner",),
        target_path=target_path,
        expected_target_digest=expected_target_digest,
        replacement_body=replacement,
        evidence_ids=("EV-001",),
        rationale="Preserve the SME-edited full decision wording.",
    )


def _prepare_proposal(
    workspace: Workspace,
) -> tuple[Path, dict[str, JsonValue], ActorCapability, ActorCapability]:
    drafter, owner, _ = _prepare_evidence(workspace)
    target = _write_pack_document(
        workspace,
        "pack/scope/decision.json",
        _decision("Recommend the initial response to NBRx variance."),
    )
    replacement = _decision("Recommend the edited, evidence-qualified response to NBRx variance.")
    _propose(
        workspace,
        drafter,
        expected_target_digest=_digest(target.read_bytes()),
        replacement=replacement,
    )
    return target, replacement, drafter, owner


@pytest.mark.contract
def test_end_to_end_confirm_reopen_resume_and_full_body_preservation(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    target, replacement, _, owner = _prepare_proposal(workspace)
    questions = compile_questions(workspace)
    update_session_state(
        workspace,
        stage="ratify",
        expected_revision=get_workspace_revision(workspace),
        last_delta_id=None,
        open_question_ids=tuple(question.id for question in questions),
        next_mission="ratify",
    )

    confirmed_at = datetime(2026, 7, 25, 13, 0, tzinfo=UTC)
    confirmed = confirm_proposal(
        workspace,
        "DELTA-001",
        actor=owner,
        confirmed_at=confirmed_at,
    )
    reopened = Workspace.open(workspace.root)
    resumed = load_session_state(reopened)
    persisted = load_proposal(reopened, "DELTA-001")
    report = validate_authoring(reopened)

    assert json.loads(target.read_text(encoding="utf-8")) == replacement
    assert persisted.replacement_body == replacement
    assert persisted.status == "confirmed"
    assert persisted.confirmer_principal == "brand-1"
    assert persisted.confirmer_role == "brand_owner"
    assert resumed.workspace_id == workspace.manifest.workspace_id
    assert resumed.last_delta_id == "DELTA-001"
    assert resumed.open_question_ids == ()
    assert report.confirmed_proposals == 1
    assert not any((workspace.root / "sources" / "inbox").iterdir())

    assert (
        confirm_proposal(
            reopened,
            "DELTA-001",
            actor=owner,
            confirmed_at=confirmed_at,
        )
        == confirmed
    )


@pytest.mark.contract
def test_source_registration_is_idempotent_and_same_id_drift_conflicts(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    source = _source()
    assert register_source(workspace, source) == source
    assert register_source(workspace, source) == source

    with pytest.raises(AuthoringConflictError, match="source id"):
        register_source(workspace, _source(title="Changed title"))
    with pytest.raises(AuthoringConflictError, match="withdrawal"):
        update_source(workspace, _source(title="Changed title"))

    withdrawn_at = datetime(2026, 7, 26, tzinfo=UTC)
    withdrawn = withdraw_source(
        workspace,
        "SRC-001",
        withdrawn_at=withdrawn_at,
    )
    assert withdrawn.status.value == "withdrawn"
    assert (
        withdraw_source(
            workspace,
            "SRC-001",
            withdrawn_at=withdrawn_at,
        )
        == withdrawn
    )


@pytest.mark.contract
def test_evidence_refuses_missing_checksum_permission_quote_and_withdrawal(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    with pytest.raises(AuthoringValidationError, match="missing source"):
        record_evidence(workspace, _evidence())

    register_source(workspace, _source())
    with pytest.raises(AuthoringValidationError, match="checksum"):
        record_evidence(
            workspace,
            _evidence(source_checksum="sha256:" + "c" * 64),
        )
    with pytest.raises(AuthoringValidationError, match="permitted use"):
        record_evidence(workspace, _evidence(permitted_use="public-quotation"))
    quoted = _evidence(
        id="EV-QUOTED",
        quoted=True,
        quote_digest=authoring_module._quote_digest("governed quote"),
    )
    with pytest.raises(AuthoringValidationError, match="explicit quote"):
        record_evidence(workspace, quoted)

    evidence = record_evidence(workspace, _evidence())
    assert record_evidence(workspace, evidence) == evidence
    with pytest.raises(AuthoringConflictError, match="evidence id"):
        record_evidence(workspace, _evidence(claim="Changed claim."))

    withdraw_source(
        workspace,
        "SRC-001",
        withdrawn_at=datetime(2026, 7, 26, tzinfo=UTC),
    )
    with pytest.raises(AuthoringValidationError, match="withdrawn"):
        record_evidence(workspace, _evidence(id="EV-002"))
    with pytest.raises(AuthoringValidationError, match="withdrawn"):
        validate_authoring(workspace)


@pytest.mark.contract
def test_proposal_refuses_stale_missing_and_candidate_boundary(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    target, _, drafter, owner = _prepare_proposal(workspace)

    target.write_bytes(_canonical(_decision("Concurrent edit.")))
    concurrent = target.read_bytes()
    with pytest.raises(StaleProposalError, match="stale"):
        confirm_proposal(
            workspace,
            "DELTA-001",
            actor=owner,
            confirmed_at=datetime(2026, 7, 25, tzinfo=UTC),
        )
    assert target.read_bytes() == concurrent

    with pytest.raises(StaleProposalError, match="missing"):
        _propose(
            workspace,
            drafter,
            delta_id="DELTA-002",
            target_path="pack/scope/missing.json",
            expected_target_digest="sha256:" + "0" * 64,
            replacement=_decision("Missing target."),
        )
    with pytest.raises(AuthoringValidationError, match="candidate-only"):
        propose_replacement(
            workspace,
            actor=drafter,
            delta_id="DELTA-003",
            target_owner_role="brand_owner",
            allowed_confirmer_roles=("brand_owner",),
            target_path="pack/scope/decision.json",
            expected_target_digest=_digest(target.read_bytes()),
            replacement_body={"id": "BAD", "lifecycle": "active"},
            evidence_ids=("EV-001",),
            rationale="Forbidden activation attempt.",
        )


@pytest.mark.contract
def test_question_compiler_is_content_addressed_owned_deterministic_and_finite(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    first = compile_questions(workspace)
    second = compile_questions(Workspace.open(workspace.root))
    assert first == second
    assert len(first) == 5
    assert all(re.fullmatch(r"Q-[A-Z-]+-[0-9a-f]{16}", item.id) for item in first)
    assert all(item.owner_role in workspace.manifest.owner_roles for item in first)
    assert tuple(item.id for item in first) == tuple(sorted(item.id for item in first))

    register_source(workspace, _source())
    record_evidence(workspace, _evidence())
    _write_pack_document(
        workspace,
        "pack/scope/decision.json",
        _decision("Recommend an evidence-qualified response."),
    )
    _write_pack_document(
        workspace,
        "pack/evaluations/dev.json",
        _eval_case("EVAL-DEV-001", "dev", required_context=("DEC-001",)),
    )
    _write_pack_document(
        workspace,
        "pack/evaluations/regression.json",
        _eval_case("EVAL-REG-001", "regression", required_context=("DEC-001",)),
    )
    assert compile_questions(workspace) == ()


@pytest.mark.contract
def test_free_form_role_strings_cannot_confirm(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    _prepare_proposal(workspace)
    with pytest.raises(TypeError):
        confirm_proposal(  # type: ignore[call-arg]
            workspace,
            "DELTA-001",
            confirmer_role="brand_owner",
            confirmed_at=datetime(2026, 7, 25, tzinfo=UTC),
        )


@pytest.mark.contract
def test_module_has_no_approval_or_platform_execution_surface() -> None:
    module_source = inspect.getsource(authoring_module)
    assert "ontowiz_core" not in module_source
    assert "ontowiz_factory" not in module_source
    assert not hasattr(authoring_module, "approve")
    assert not hasattr(authoring_module, "activate")
    assert not hasattr(authoring_module, "serve")
