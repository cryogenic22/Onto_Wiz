from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import ontowiz_authoring.authoring as authoring_module
from ontowiz_authoring.adapters import (
    AdapterRequest,
    ConfirmCommand,
    ProposeCommand,
    RecordEvidenceCommand,
    RegisterSourceCommand,
    UpdateSessionCommand,
    WithdrawSourceCommand,
)
from ontowiz_authoring.authoring import (
    ActorCapability,
    AuthoringProviderState,
    AuthoringTransactionIdentity,
    AuthoringTrustContext,
    AuthorityHighWater,
    AuthorityStatement,
    JournalAttestation,
    OperationCredential,
    PrincipalGrant,
    RecoveryAuthorization,
    SignedAuthority,
    authoring_transaction_digest,
    get_workspace_revision,
    install_signed_authority,
)
from ontowiz_authoring.workspace import Workspace, initialize_workspace
from ontowiz_spec import EvidenceRef, SourceRecord


def canonical(value: object) -> bytes:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", encoded) + "\n").encode("utf-8")


def digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class ExternalTestProvider:
    """Test-only external trust host; production ships no provider implementation."""

    def __init__(
        self,
        workspace_id: str,
        authority_key: Ed25519PrivateKey,
    ) -> None:
        public_key = authority_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        self.workspace_id = workspace_id
        self.authority_key = authority_key
        self._high_water = AuthorityHighWater(
            format="ontowiz-authority-high-water",
            format_version=1,
            workspace_id=workspace_id,
            trust_key_id=digest(public_key),
            authority_public_key=public_key.hex(),
            authority_revision=0,
            authority_digest=None,
        )
        self._roles: dict[str, tuple[tuple[str, ...], str]] = {
            "host-admin": (("steward",), "client-a")
        }
        self._authoring_revision = 0
        self._pending: AuthoringTransactionIdentity | None = None
        self._last_finalized: AuthoringTransactionIdentity | None = None
        self._used_nonces: set[str] = set()
        self._counter = 0
        self._journal_key_id = digest(b"adapter-test-journal")

    def authority_high_water(self, workspace_id: str) -> AuthorityHighWater:
        if workspace_id != self.workspace_id:
            raise RuntimeError("unknown workspace")
        return self._high_water

    def authoring_state(self, workspace_id: str) -> AuthoringProviderState:
        if workspace_id != self.workspace_id:
            raise RuntimeError("unknown workspace")
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

    def set_grants(self, grants: Sequence[PrincipalGrant]) -> None:
        self._roles.update(
            {
                grant.principal_id: (grant.roles, grant.client_boundary)
                for grant in grants
            }
        )

    def context(
        self,
        principal_id: str,
        intent_digest: str,
        *,
        credential_workspace_id: str | None = None,
        credential_intent_digest: str | None = None,
        expired: bool = False,
    ) -> AuthoringTrustContext:
        self._counter += 1
        roles, client_boundary = self._roles[principal_id]
        issued_at = datetime(2019, 1, 1, tzinfo=UTC) if expired else datetime(
            2026, 1, 1, tzinfo=UTC
        )
        expires_at = datetime(2020, 1, 1, tzinfo=UTC) if expired else datetime(
            2036, 1, 1, tzinfo=UTC
        )
        credential = OperationCredential(
            format="ontowiz-operation-credential",
            format_version=1,
            workspace_id=credential_workspace_id or self.workspace_id,
            principal_id=principal_id,
            roles=roles,
            client_boundary=client_boundary,
            authority_revision=self._high_water.authority_revision,
            authority_digest=self._high_water.authority_digest,
            trust_key_id=self._high_water.trust_key_id,
            intent_digest=credential_intent_digest or intent_digest,
            nonce=f"nonce-{self._counter:08d}",
            issued_at=issued_at,
            expires_at=expires_at,
            actor_key_id=digest(b"external-test-actor"),
            proof_signature="a" * 128,
        )
        return AuthoringTrustContext(provider=self, credential=credential)

    def authenticate_actor(
        self,
        credential: OperationCredential,
        *,
        expected_intent_digest: str,
        now: datetime,
    ) -> ActorCapability:
        del now
        expected_roles = self._roles.get(credential.principal_id)
        if (
            credential.workspace_id != self.workspace_id
            or credential.intent_digest != expected_intent_digest
            or expected_roles != (credential.roles, credential.client_boundary)
            or credential.authority_revision != self._high_water.authority_revision
            or credential.authority_digest != self._high_water.authority_digest
            or credential.trust_key_id != self._high_water.trust_key_id
            or credential.proof_signature != "a" * 128
            or credential.nonce in self._used_nonces
        ):
            raise RuntimeError("external actor authentication failed")
        self._used_nonces.add(credential.nonce)
        return ActorCapability(
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
    ) -> ActorCapability:
        exact = (
            (authorization.status == "pending" and self._pending == identity)
            or (
                authorization.status == "finalized"
                and self._last_finalized == identity
            )
        )
        actor = self._roles.get(identity.actor_principal)
        if (
            not exact
            or identity.workspace_id != self.workspace_id
            or authorization.workspace_id != self.workspace_id
            or authorization.transaction_digest != authoring_transaction_digest(identity)
            or actor is None
        ):
            raise RuntimeError("external recovery authentication failed")
        roles, client_boundary = actor
        return ActorCapability(
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
            provider_id="external-test-host",
            key_id=self._journal_key_id,
            value=hashlib.sha256(journal_identity).hexdigest(),
        )

    def verify_journal(
        self,
        journal_identity: bytes,
        attestation: JournalAttestation,
    ) -> None:
        if (
            attestation.provider_id != "external-test-host"
            or attestation.key_id != self._journal_key_id
            or attestation.value != hashlib.sha256(journal_identity).hexdigest()
        ):
            raise RuntimeError("external journal verification failed")

    def reserve_transaction(self, identity: AuthoringTransactionIdentity) -> None:
        if (
            identity.workspace_id != self.workspace_id
            or self._pending is not None
            or identity.revision_before != self._authoring_revision
        ):
            raise RuntimeError("external transaction reservation failed")
        self._pending = identity

    def authorize_recovery(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> RecoveryAuthorization:
        if self._pending == identity:
            status = "pending"
        elif self._last_finalized == identity:
            status = "finalized"
        else:
            raise RuntimeError("external recovery authorization failed")
        return RecoveryAuthorization(
            format="ontowiz-recovery-authorization",
            format_version=1,
            workspace_id=self.workspace_id,
            transaction_digest=authoring_transaction_digest(identity),
            status=status,
            authoring_revision=self._authoring_revision,
        )

    def finalize_transaction(self, identity: AuthoringTransactionIdentity) -> None:
        if (
            self._last_finalized == identity
            and self._authoring_revision == identity.revision_after
        ):
            return
        if self._pending != identity or self._authoring_revision != identity.revision_before:
            raise RuntimeError("external transaction finalization failed")
        self._authoring_revision = identity.revision_after
        self._last_finalized = identity
        self._pending = None

    def abort_reserved_transaction(self, identity: AuthoringTransactionIdentity) -> None:
        if self._pending != identity or self._authoring_revision != identity.revision_before:
            raise RuntimeError("external transaction abort failed")
        self._pending = None

    def advance_authority(
        self,
        *,
        expected: AuthorityHighWater,
        replacement: AuthorityHighWater,
    ) -> None:
        if (
            expected != self._high_water
            or replacement.workspace_id != self.workspace_id
            or replacement.trust_key_id != expected.trust_key_id
            or replacement.authority_public_key != expected.authority_public_key
            or replacement.authority_revision != expected.authority_revision + 1
        ):
            raise RuntimeError("external authority advance failed")
        self._high_water = replacement


def source_record() -> SourceRecord:
    return SourceRecord.model_validate(
        {
            "id": "SRC-001",
            "title": "Authorized public synthetic source",
            "owner_role": "steward",
            "checksum": digest(b"synthetic-source"),
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
    )


def evidence_record() -> EvidenceRef:
    return EvidenceRef.model_validate(
        {
            "id": "EV-001",
            "source_id": "SRC-001",
            "source_checksum": source_record().checksum,
            "claim": "The synthetic decision boundary is evidence-backed.",
            "locator_type": "paragraph",
            "locator": "1",
            "mode": "observed",
            "permitted_use": "candidate-derivation",
            "quoted": False,
            "quote_digest": None,
            "valid_as_of": "2026-07-26",
            "extracted_at": "2026-07-26T12:00:00Z",
            "confidence": 0.9,
        }
    )


def public_eval(case_id: str, suite: str) -> dict[str, object]:
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
        "required_behaviours": ["Respect the human approval boundary."],
        "prohibited_behaviours": ["Claim autonomous approval authority."],
        "required_context": ["DEC-001"],
        "evidence_expectations": ["Use the registered evidence."],
        "scoring": {
            "decision_quality": 1,
            "method": 1,
            "evidence": 1,
            "uncertainty": 1,
            "human_boundary": 1,
        },
        "critical_failures": ["Approve an action autonomously."],
        "provenance": {
            "mode": "sme_authored",
            "supplied_by": "brand-sme",
            "confidence": 0.9,
            "open_questions": [],
        },
    }


def create_workspace(
    root: Path,
    *,
    authority_key: Ed25519PrivateKey,
    workspace_id: str = "brand-variance",
) -> tuple[Workspace, ExternalTestProvider]:
    workspace = initialize_workspace(
        root,
        workspace_id=workspace_id,
        owner_roles=("approver", "brand_owner", "steward"),
        archetypes=("enterprise_core", "brand_analytics"),
    )
    decision = {
        "id": "DEC-001",
        "decision": "Recommend a bounded commercial action.",
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
    decision_payload = canonical(decision)
    (workspace.root / "pack/scope/DEC-001.yaml").write_bytes(decision_payload)
    pack_path = workspace.root / "pack/pack.yaml"
    pack = json.loads(pack_path.read_bytes())
    pack["artifact_digests"] = [
        {"artifact_id": "DEC-001", "digest": digest(decision_payload)}
    ]
    pack_path.write_bytes(canonical(pack))

    provider = ExternalTestProvider(workspace_id, authority_key)
    grants = (
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
    )
    statement = AuthorityStatement(
        format="ontowiz-authority-statement",
        format_version=1,
        workspace_id=workspace_id,
        authority_revision=1,
        issued_at=datetime(2026, 1, 1, tzinfo=UTC),
        grants=grants,
    )
    statement_payload = canonical(statement.model_dump(mode="json"))
    public_key = authority_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    authority = SignedAuthority(
        statement=statement,
        statement_digest=digest(statement_payload),
        signature=authority_key.sign(statement_payload).hex(),
        trust_key_id=digest(public_key),
    )
    expected_revision = get_workspace_revision(workspace, provider)
    intent = authoring_module._mutation_intent(
        "install_authority",
        workspace_id,
        expected_revision,
        {"authority": authority.model_dump(mode="json")},
    )
    install_signed_authority(
        workspace,
        trust=provider.context("host-admin", intent),
        authority=authority,
        expected_revision=expected_revision,
    )
    provider.set_grants(grants)
    return workspace, provider


def request_intent(workspace: Workspace, request: AdapterRequest) -> str:
    command = request.command
    expected_revision = request.expected_revision
    if expected_revision is None:
        raise ValueError("read-only adapter request has no mutation intent")
    if isinstance(command, RegisterSourceCommand):
        operation = "register_source"
        body: Mapping[str, object] = {
            "source": command.source.model_dump(mode="json"),
            "material_path": command.material_path,
        }
    elif isinstance(command, RecordEvidenceCommand):
        operation = "record_evidence"
        body = {
            "evidence": command.evidence.model_dump(mode="json"),
            "quote_payload": command.quote_payload,
        }
    elif isinstance(command, ProposeCommand):
        operation = "propose"
        body = {
            "delta_id": command.delta_id,
            "target_owner_role": command.target_owner_role,
            "allowed_confirmer_roles": sorted(set(command.allowed_confirmer_roles)),
            "target_path": command.target_path,
            "expected_target_digest": command.expected_target_digest,
            "replacement_body": command.replacement_body,
            "evidence_ids": sorted(set(command.evidence_ids)),
            "rationale": command.rationale,
        }
    elif isinstance(command, ConfirmCommand):
        operation = "confirm"
        revision = authoring_module._load_revision(workspace)
        body = {
            "delta_id": command.delta_id,
            "confirmed_at": command.confirmed_at.isoformat(),
            "session": authoring_module._confirmation_session_after(
                workspace,
                revision,
                command.delta_id,
            ).model_dump(mode="json"),
        }
    elif isinstance(command, UpdateSessionCommand):
        operation = "update_session"
        body = {
            "stage": command.stage,
            "last_delta_id": command.last_delta_id,
            "open_question_ids": sorted(set(command.open_question_ids)),
            "next_mission": command.next_mission,
        }
    elif isinstance(command, WithdrawSourceCommand):
        operation = "withdraw_source"
        body = {
            "source_id": command.source_id,
            "withdrawn_at": command.withdrawn_at.isoformat(),
        }
    else:
        raise ValueError("command does not mutate authoring state")
    return authoring_module._mutation_intent(
        operation,
        workspace.manifest.workspace_id,
        expected_revision,
        body,
    )


def trust_for(
    provider: ExternalTestProvider,
    workspace: Workspace,
    request: AdapterRequest,
    *,
    principal_id: str = "draft-agent",
    credential_workspace_id: str | None = None,
    credential_intent_digest: str | None = None,
    expired: bool = False,
) -> AuthoringTrustContext:
    intent = request_intent(workspace, request)
    return provider.context(
        principal_id,
        intent,
        credential_workspace_id=credential_workspace_id,
        credential_intent_digest=credential_intent_digest,
        expired=expired,
    )


def canonical_tree(workspace: Workspace) -> dict[str, bytes]:
    return {
        path.relative_to(workspace.root).as_posix(): path.read_bytes()
        for path in sorted(workspace.root.rglob("*"))
        if path.is_file() and path.name != ".authoring.lock"
    }
