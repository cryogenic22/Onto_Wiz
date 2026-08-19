from __future__ import annotations

import json
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from adapters._support import create_workspace, digest, source_record
from ontowiz_authoring.adapters import (
    AdapterRequest,
    AdapterSession,
    PackageCommand,
    RegisterSourceCommand,
    ResumeCommand,
    ValidateCommand,
)
from ontowiz_authoring.authoring import (
    ActorCapability,
    AuthoringTransactionChange,
    AuthoringTransactionIdentity,
    AuthoringTrustContext,
    RecoveryAuthorization,
    authoring_transaction_digest,
    get_workspace_revision,
)
from ontowiz_authoring.authority_client import (
    PROTOCOL_VERSION,
    WIRE_METHODS,
    AuthorityAdministrationError,
    AuthorityClientError,
    AuthorityHostClient,
    AuthorityHostRefusalError,
    AuthorityProtocolError,
    AuthorityTransportError,
    LocalIpcTransport,
    ProtectedConfig,
    canonical_message_bytes,
    config_is_group_or_other_writable,
    resolve_protected_config,
)
from ontowiz_authoring.authority_client import _parse_message as parse_message

from .reference_host import ReferenceAuthorityHost, default_address

FAMILY = "AF_PIPE" if os.name == "nt" else "AF_UNIX"
PIN = "0011223344556677889900aabbccddeeff"
WRONG_PIN = "ffeeddccbbaa00998877665544332211"


def _config(endpoint: str, *, pin: str = PIN, version: int = PROTOCOL_VERSION) -> ProtectedConfig:
    return ProtectedConfig(
        endpoint=endpoint,
        family=FAMILY,
        protocol_version=version,
        provider_id="reference-host",
        server_pin=pin,
        max_message_bytes=1_048_576,
        timeout_seconds=5.0,
    )


def _transport(config: ProtectedConfig) -> LocalIpcTransport:
    return LocalIpcTransport(
        config.endpoint,
        family=config.family,
        authkey=config.authkey,
        timeout_seconds=config.timeout_seconds,
        max_message_bytes=config.max_message_bytes,
    )


def _request(request_id, workspace_id, expected_revision, command):  # noqa: ANN001, ANN201
    return AdapterRequest.model_validate(
        {
            "format": "ontowiz-adapter-request",
            "format_version": 1,
            "request_id": request_id,
            "workspace_id": workspace_id,
            "expected_revision": expected_revision,
            "command": command,
        }
    )


class _DeadTransport:
    """A transport whose host is unprovisioned/unreachable."""

    def roundtrip(self, payload: bytes) -> bytes:
        raise AuthorityTransportError("authority host is down")


class _EchoTransport:
    """A canned host response echoing the request correlation id (no real IPC)."""

    def __init__(
        self,
        *,
        status: str = "ok",
        code: str | None = None,
        result: dict | None = None,  # noqa: ANN401
        protocol_version: int = PROTOCOL_VERSION,
        correlation_id: str | None = None,
    ) -> None:
        self._status = status
        self._code = code
        self._result = result
        self._version = protocol_version
        self._correlation_id = correlation_id

    def roundtrip(self, payload: bytes) -> bytes:
        request = json.loads(payload.decode("utf-8"))
        message: dict = {
            "protocol_version": self._version,
            "correlation_id": self._correlation_id or request["correlation_id"],
            "status": self._status,
        }
        if self._status == "ok":
            message["result"] = {} if self._result is None else self._result
        else:
            message["code"] = self._code
            message["message"] = "redacted"
        return canonical_message_bytes(message)


def _transaction_identity() -> AuthoringTransactionIdentity:
    return AuthoringTransactionIdentity(
        format="ontowiz-provider-transaction",
        format_version=1,
        workspace_id="brand-variance",
        transaction_id="TX-1",
        operation="register_source",
        revision_before=1,
        revision_after=2,
        actor_principal="draft-agent",
        intent_digest=digest(b"intent"),
        credential_nonce="nonce-1",
        credential_digest=digest(b"credential"),
        trust_key_id=digest(b"trust-key"),
        authority_revision=1,
        authority_digest=digest(b"authority"),
        changes=(
            AuthoringTransactionChange(
                kind="revision", before_digest=None, after_digest=digest(b"rev")
            ),
        ),
    )


def _make(tmp_path):  # noqa: ANN001, ANN202
    key = Ed25519PrivateKey.generate()
    workspace, provider = create_workspace(tmp_path / "ws", authority_key=key)
    return workspace, provider


def _host(provider, config):  # noqa: ANN001, ANN202
    return ReferenceAuthorityHost(
        provider, family=config.family, authkey=config.authkey, address=config.endpoint
    )


def _register_source():  # noqa: ANN202
    return RegisterSourceCommand(
        operation="register_source", source=source_record(), material_path=None
    )


# --------------------------------------------------------------------------- unit tests


def test_advance_authority_hard_refuses_without_touching_transport() -> None:
    client = AuthorityHostClient(_DeadTransport(), _config(r"\\.\pipe\unused"))
    with pytest.raises(AuthorityAdministrationError) as caught:
        client.advance_authority(expected=None, replacement=None)  # type: ignore[arg-type]
    # It is an AuthorityClientError, and no transport call was made (else the dead
    # transport would have raised AuthorityTransportError first).
    assert isinstance(caught.value, AuthorityClientError)


def test_advance_authority_is_off_the_wire_allowlist() -> None:
    assert "advance_authority" not in WIRE_METHODS
    assert {
        "authority_high_water",
        "authoring_state",
        "authenticate_actor",
        "authenticate_recovery",
        "reserve_transaction",
        "authorize_recovery",
        "finalize_transaction",
        "abort_reserved_transaction",
        "issue_credential",
    } >= WIRE_METHODS


def test_wire_codec_is_versioned_bounded_and_strict() -> None:
    message = {"protocol_version": 1, "method": "authoring_state", "params": {"a": [1, 2]}}
    assert parse_message(canonical_message_bytes(message), max_bytes=4096) == message
    with pytest.raises(AuthorityProtocolError):
        parse_message(b'{"a":1,"a":2}', max_bytes=4096)  # duplicate key
    with pytest.raises(AuthorityProtocolError):
        parse_message(b'{"a":NaN}', max_bytes=4096)  # non-finite constant
    with pytest.raises(AuthorityProtocolError):
        parse_message(canonical_message_bytes(message), max_bytes=4)  # oversized


def test_config_writability_predicate() -> None:
    assert config_is_group_or_other_writable(0o600) is False
    assert config_is_group_or_other_writable(0o644) is False
    assert config_is_group_or_other_writable(0o646) is True
    assert config_is_group_or_other_writable(0o620) is True
    assert config_is_group_or_other_writable(0o666) is True


def _write_config(path, *, version: int = PROTOCOL_VERSION) -> None:  # noqa: ANN001
    path.write_bytes(
        canonical_message_bytes(
            {
                "endpoint": r"\\.\pipe\ontowiz",
                "family": FAMILY,
                "protocol_version": version,
                "provider_id": "reference-host",
                "server_pin": PIN,
                "max_message_bytes": 1_048_576,
                "timeout_seconds": 5.0,
            }
        )
    )


def test_resolve_config_rejects_workspace_supplied_endpoint(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "authority.json"
    _write_config(path)
    with pytest.raises(AuthorityTransportError):
        resolve_protected_config(path, workspace_endpoint=r"\\.\pipe\evil")


def test_resolve_config_missing_is_transport_error(tmp_path) -> None:  # noqa: ANN001
    with pytest.raises(AuthorityTransportError):
        resolve_protected_config(tmp_path / "absent.json")


def test_resolve_config_rejects_unsupported_version(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "authority.json"
    _write_config(path, version=2)
    with pytest.raises(AuthorityTransportError):
        resolve_protected_config(path)


def test_resolve_config_happy_path(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "authority.json"
    _write_config(path)
    config = resolve_protected_config(path)
    assert config.protocol_version == PROTOCOL_VERSION
    assert config.authkey == bytes.fromhex(PIN)


@pytest.mark.skipif(os.name != "posix", reason="POSIX st_mode write bits")
def test_resolve_config_rejects_drafting_writable(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "authority.json"
    _write_config(path)
    os.chmod(path, 0o646)
    with pytest.raises(AuthorityTransportError):
        resolve_protected_config(path)


# -------------------------------------------------------------------- integration (IPC)


def test_client_reads_provider_state_over_ipc(tmp_path) -> None:  # noqa: ANN001
    workspace, provider = _make(tmp_path)
    config = _config(default_address(FAMILY))
    with _host(provider, config):
        client = AuthorityHostClient(_transport(config), config)
        workspace_id = workspace.manifest.workspace_id
        high_water = client.authority_high_water(workspace_id)
        state = client.authoring_state(workspace_id)
    assert high_water.workspace_id == workspace_id
    assert state.workspace_id == workspace_id


def test_wrong_server_pin_is_transport_error(tmp_path) -> None:  # noqa: ANN001
    workspace, provider = _make(tmp_path)
    config = _config(default_address(FAMILY))
    with _host(provider, config):
        wrong = _config(config.endpoint, pin=WRONG_PIN)
        client = AuthorityHostClient(_transport(wrong), wrong)
        with pytest.raises(AuthorityTransportError):
            client.authority_high_water(workspace.manifest.workspace_id)


def test_unreachable_host_is_transport_error() -> None:
    config = _config(default_address(FAMILY))
    client = AuthorityHostClient(_transport(config), config)
    with pytest.raises(AuthorityTransportError):
        client.authority_high_water("brand-variance")


def test_host_rejects_advance_authority_off_allowlist(tmp_path) -> None:  # noqa: ANN001
    workspace, provider = _make(tmp_path)
    config = _config(default_address(FAMILY))
    with _host(provider, config):
        raw = canonical_message_bytes(
            {
                "protocol_version": PROTOCOL_VERSION,
                "method": "advance_authority",
                "workspace_id": workspace.manifest.workspace_id,
                "correlation_id": "cor-0000000000000001",
                "params": {},
            }
        )
        response = json.loads(_transport(config).roundtrip(raw))
    assert response["status"] == "error"
    assert response["code"] == "E_METHOD_NOT_ALLOWED"


def test_keyless_client_drives_a_governed_mutation_over_ipc(tmp_path) -> None:  # noqa: ANN001
    workspace, provider = _make(tmp_path)
    config = _config(default_address(FAMILY))
    with _host(provider, config):
        client = AuthorityHostClient(_transport(config), config)
        session = AdapterSession(workspace, client, output_directory=tmp_path / "out")
        workspace_id = workspace.manifest.workspace_id

        resume = session.execute(
            _request("REQ-RESUME", workspace_id, None, ResumeCommand(operation="resume"))
        )
        assert resume.status == "ok"

        revision = get_workspace_revision(workspace, client)
        source_request = _request(
            "REQ-SOURCE",
            workspace_id,
            revision,
            _register_source(),
        )
        intent = session.prepare_intent(source_request)
        assert intent is not None
        credential = client.issue_credential(intent)  # out-of-band, over the same IPC
        trust = AuthoringTrustContext(provider=client, credential=credential)
        outcome = session.execute(source_request, trust=trust)

    assert outcome.status == "ok", outcome
    assert outcome.outcome is not None
    assert outcome.outcome.entity_id == "SRC-001"
    assert outcome.outcome.entity_status == "current"


# ---------------------------------------------------------- E_AUTHORITY_UNAVAILABLE map


def test_transport_failure_maps_to_e_authority_unavailable_on_read_verbs(tmp_path) -> None:  # noqa: ANN001
    workspace, _ = _make(tmp_path)
    session = AdapterSession(
        workspace,
        AuthorityHostClient(_DeadTransport(), _config(r"\\.\pipe\unused")),
        output_directory=tmp_path / "out",
    )
    workspace_id = workspace.manifest.workspace_id
    requests = (
        _request("R-RES", workspace_id, None, ResumeCommand(operation="resume")),
        _request("R-VAL", workspace_id, 1, ValidateCommand(operation="validate")),
        _request("R-PKG", workspace_id, 1, PackageCommand(operation="package")),
    )
    for request in requests:
        response = session.execute(request)
        assert response.status == "error"
        assert response.error is not None
        assert response.error.code == "E_AUTHORITY_UNAVAILABLE", (
            request.request_id,
            response.error.code,
        )


def test_transport_failure_maps_to_e_authority_unavailable_on_a_mutation(tmp_path) -> None:
    workspace, provider = _make(tmp_path)
    dead_client = AuthorityHostClient(_DeadTransport(), _config(r"\\.\pipe\unused"))
    session = AdapterSession(workspace, dead_client, output_directory=tmp_path / "out")
    workspace_id = workspace.manifest.workspace_id
    request = _request(
        "R-SRC",
        workspace_id,
        1,
        _register_source(),
    )
    credential = provider.context("draft-agent", digest(b"unused-intent")).credential
    trust = AuthoringTrustContext(provider=dead_client, credential=credential)
    response = session.execute(request, trust=trust)
    assert response.error is not None
    assert response.error.code == "E_AUTHORITY_UNAVAILABLE"


def test_e_authorization_stays_distinct_from_e_authority_unavailable(tmp_path) -> None:
    # A local trust failure (missing credential) with an in-process provider must still
    # map to E_AUTHORIZATION, proving the two codes are genuinely distinct.
    workspace, provider = _make(tmp_path)
    session = AdapterSession(workspace, provider, output_directory=tmp_path / "out")
    workspace_id = workspace.manifest.workspace_id
    revision = get_workspace_revision(workspace, provider)
    request = _request(
        "R-NOTRUST",
        workspace_id,
        revision,
        _register_source(),
    )
    response = session.execute(request, trust=None)
    assert response.error is not None
    assert response.error.code == "E_AUTHORIZATION"


# ---------------------------------------------------- client wire error branches + recovery


def test_host_refusal_maps_to_a_host_refusal_error() -> None:
    client = AuthorityHostClient(
        _EchoTransport(status="error", code="E_PROVIDER_REFUSED"), _config(r"\\.\pipe\unused")
    )
    with pytest.raises(AuthorityHostRefusalError):
        client.authority_high_water("brand-variance")
    # A host refusal is NOT an AuthorityClientError (it maps to E_AUTHORIZATION, not
    # E_AUTHORITY_UNAVAILABLE).
    assert not issubclass(AuthorityHostRefusalError, AuthorityClientError)


def test_unrecognized_host_error_is_protocol_error() -> None:
    client = AuthorityHostClient(
        _EchoTransport(status="error", code="E_WEIRD"), _config(r"\\.\pipe\unused")
    )
    with pytest.raises(AuthorityProtocolError):
        client.authority_high_water("brand-variance")


def test_protocol_version_mismatch_is_protocol_error() -> None:
    client = AuthorityHostClient(_EchoTransport(protocol_version=2), _config(r"\\.\pipe\unused"))
    with pytest.raises(AuthorityProtocolError):
        client.authority_high_water("brand-variance")


def test_correlation_mismatch_is_protocol_error() -> None:
    client = AuthorityHostClient(
        _EchoTransport(correlation_id="cor-wrong"), _config(r"\\.\pipe\unused")
    )
    with pytest.raises(AuthorityProtocolError):
        client.authority_high_water("brand-variance")


def test_malformed_result_is_protocol_error() -> None:
    client = AuthorityHostClient(
        _EchoTransport(result={"bogus": "data"}), _config(r"\\.\pipe\unused")
    )
    with pytest.raises(AuthorityProtocolError):
        client.authority_high_water("brand-variance")


def test_recovery_and_void_methods_proxy_over_the_wire() -> None:
    identity = _transaction_identity()
    config = _config(r"\\.\pipe\unused")

    void_client = AuthorityHostClient(_EchoTransport(result={}), config)
    void_client.reserve_transaction(identity)
    void_client.finalize_transaction(identity)
    void_client.abort_reserved_transaction(identity)

    authorization = RecoveryAuthorization(
        format="ontowiz-recovery-authorization",
        format_version=1,
        workspace_id="brand-variance",
        transaction_digest=authoring_transaction_digest(identity),
        status="pending",
        authoring_revision=1,
    )
    authorize_client = AuthorityHostClient(
        _EchoTransport(result=authorization.model_dump(mode="json")), config
    )
    assert authorize_client.authorize_recovery(identity).status == "pending"

    actor = ActorCapability(
        format="ontowiz-authenticated-actor",
        format_version=1,
        workspace_id="brand-variance",
        principal_id="draft-agent",
        roles=("steward",),
        client_boundary="client-a",
        authority_revision=1,
        authority_digest=digest(b"authority"),
        trust_key_id=digest(b"trust-key"),
        intent_digest=digest(b"intent"),
        credential_nonce="nonce-1",
    )
    recover_client = AuthorityHostClient(
        _EchoTransport(result=actor.model_dump(mode="json")), config
    )
    recovered = recover_client.authenticate_recovery(identity, authorization)
    assert recovered.principal_id == "draft-agent"


def test_void_method_rejects_unexpected_payload() -> None:
    client = AuthorityHostClient(
        _EchoTransport(result={"unexpected": 1}), _config(r"\\.\pipe\unused")
    )
    with pytest.raises(AuthorityProtocolError):
        client.reserve_transaction(_transaction_identity())
