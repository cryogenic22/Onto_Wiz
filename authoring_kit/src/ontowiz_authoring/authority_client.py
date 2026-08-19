"""Keyless authority-host client over authenticated local IPC (P3.1).

The client is a thin, **keyless** proxy for the eight authoring methods of
``AuthoringTrustProvider`` plus the out-of-band credential-issuance exchange. It holds
no signing key, no credential-minting secret, and no authority high-water state; it
forwards each protocol method as one strict, versioned, length-bounded, redacted
request/response over an authenticated local IPC transport (Windows named pipe / POSIX
UDS). ``advance_authority`` (provider method 9) is authority administration: it exists
only for protocol conformance, is **off** the wire allowlist, and hard-refuses here.

Contracts frozen at ``d2997ad``: ``docs/contracts/CONTRACT_AUTHORITY.md`` and
``docs/contracts/CONTRACT_IPC_WIRE.md``.

The reference authority host is **not** shipped here (or anywhere in ``src``): the
skill bundle carries no host, keys, admin surface, or provider. Tests supply a reference
host that lives only under ``tests/``.
"""

from __future__ import annotations

import itertools
import json
import multiprocessing.connection as ipc
import os
import stat
import unicodedata
from collections.abc import Mapping
from datetime import datetime
from multiprocessing import AuthenticationError
from pathlib import Path
from typing import Final, Literal, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .authoring import (
    ActorCapability,
    AuthoringIntent,
    AuthoringProviderState,
    AuthoringTransactionIdentity,
    AuthorityHighWater,
    OperationCredential,
    RecoveryAuthorization,
)
from .authority_errors import (
    AuthorityAdministrationError,
    AuthorityClientError,
    AuthorityProtocolError,
    AuthorityTransportError,
)

PROTOCOL_VERSION: Final = 1
_DEFAULT_MAX_MESSAGE_BYTES: Final = 1_048_576

# The authoring wire allowlist: the eight authoring provider methods plus credential
# issuance. ``advance_authority`` is deliberately absent (authority administration).
WIRE_METHODS: Final = frozenset(
    {
        "authority_high_water",
        "authoring_state",
        "authenticate_actor",
        "authenticate_recovery",
        "reserve_transaction",
        "authorize_recovery",
        "finalize_transaction",
        "abort_reserved_transaction",
        "issue_credential",
    }
)


class AuthorityHostRefusalError(RuntimeError):
    """A reachable host refused an application-level operation.

    This is **not** an :class:`AuthorityClientError`: a host refusal (e.g. a rejected
    credential proof) must be wrapped by the kernel into its normal authorization error
    and surface as ``E_AUTHORIZATION`` — never as ``E_AUTHORITY_UNAVAILABLE``, which is
    reserved for an unprovisioned/unreachable host.
    """


# --------------------------------------------------------------------------- wire codec


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> object:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def canonical_message_bytes(message: Mapping[str, object]) -> bytes:
    """Serialize one wire message as deterministic, newline-terminated NFC JSON."""

    serialized = json.dumps(
        dict(message),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")


def _parse_message(raw: bytes, *, max_bytes: int) -> dict[str, object]:
    if not raw or len(raw) > max_bytes:
        raise AuthorityProtocolError("authority wire message size is invalid")
    try:
        text = raw.decode("utf-8")
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except (UnicodeError, ValueError) as exc:
        raise AuthorityProtocolError("authority wire message is not canonical JSON") from exc
    if not isinstance(parsed, dict):
        raise AuthorityProtocolError("authority wire message is not an object")
    return parsed


# ---------------------------------------------------------------------------- transport


@runtime_checkable
class Transport(Protocol):
    """A single authenticated request/response exchange with the authority host."""

    def roundtrip(self, payload: bytes) -> bytes:
        """Send one request payload and return the exact response payload.

        Any connection, authentication, framing, size, or timeout failure MUST raise
        :class:`AuthorityTransportError`.
        """


class LocalIpcTransport:
    """Authenticated local IPC over a Windows named pipe / POSIX UDS.

    Uses :mod:`multiprocessing.connection`, whose ``authkey`` performs a bidirectional
    HMAC challenge/response — the host authenticates the client and the client
    authenticates the host (the ``server_pin``). One connection per exchange.
    """

    def __init__(
        self,
        address: str,
        *,
        family: Literal["AF_PIPE", "AF_UNIX"],
        authkey: bytes,
        timeout_seconds: float,
        max_message_bytes: int,
    ) -> None:
        self._address = address
        self._family = family
        self._authkey = authkey
        self._timeout = timeout_seconds
        self._max_bytes = max_message_bytes

    def roundtrip(self, payload: bytes) -> bytes:
        try:
            connection = ipc.Client(self._address, family=self._family, authkey=self._authkey)
        except (OSError, ValueError, AuthenticationError) as exc:
            raise AuthorityTransportError(
                "authority host is unreachable or unauthenticated"
            ) from exc
        try:
            connection.send_bytes(payload)
            if not connection.poll(self._timeout):
                raise AuthorityTransportError("authority host response timed out")
            return connection.recv_bytes(maxlength=self._max_bytes)
        except (OSError, EOFError) as exc:
            raise AuthorityTransportError("authority host transport failed") from exc
        finally:
            connection.close()


# ------------------------------------------------------------------------ protected cfg


class ProtectedConfig(BaseModel):
    """Endpoint + trust parameters resolved from an admin-owned OS config location.

    Never supplied by the workspace; the client only ever reads it. No trust-on-first-use:
    the ``server_pin`` must be present and is not learned from the host.
    """

    endpoint: str = Field(min_length=1)
    family: Literal["AF_PIPE", "AF_UNIX"]
    protocol_version: int
    provider_id: str = Field(min_length=1)
    server_pin: str = Field(min_length=1, pattern=r"^[0-9a-f]{16,}$")
    max_message_bytes: int = Field(default=_DEFAULT_MAX_MESSAGE_BYTES, ge=1, le=16_777_216)
    timeout_seconds: float = Field(default=5.0, gt=0.0, le=120.0)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @property
    def authkey(self) -> bytes:
        """The shared IPC channel secret (server pin) as raw bytes."""

        return bytes.fromhex(self.server_pin)


def config_is_group_or_other_writable(mode: int) -> bool:
    """Pure predicate: does this st_mode grant write to group or other?"""

    return bool(mode & (stat.S_IWGRP | stat.S_IWOTH))


def resolve_protected_config(
    config_path: str | Path,
    *,
    workspace_endpoint: str | None = None,
) -> ProtectedConfig:
    """Resolve the protected config, failing closed on any insecurity.

    - The workspace MUST NOT supply the endpoint.
    - Missing/unreadable config, a drafting-writable config (POSIX best-effort), a
      malformed body, or a protocol-version mismatch each raise
      :class:`AuthorityTransportError` (→ ``E_AUTHORITY_UNAVAILABLE``).
    - No trust-on-first-use: the pin must already be present in the config.
    """

    if workspace_endpoint is not None:
        raise AuthorityTransportError("the workspace must not supply the authority endpoint")
    path = Path(config_path)
    try:
        info = path.stat()
    except OSError as exc:
        raise AuthorityTransportError(
            "protected authority config is missing or unreadable"
        ) from exc
    # Best-effort: on POSIX, refuse a config the drafting principal (or its group/others)
    # could rewrite to redirect the client. On Windows this st_mode signal is not
    # meaningful; the check is documented as unenforced there.
    if os.name == "posix" and config_is_group_or_other_writable(info.st_mode):
        raise AuthorityTransportError("protected authority config is writable by non-admins")
    try:
        raw = path.read_bytes()
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
        config = ProtectedConfig.model_validate(parsed)
    except (OSError, UnicodeError, ValueError, ValidationError) as exc:
        raise AuthorityTransportError("protected authority config is invalid") from exc
    if config.protocol_version != PROTOCOL_VERSION:
        raise AuthorityTransportError(
            "protected authority config declares an unsupported version"
        )
    return config


# ------------------------------------------------------------------------------- client


class AuthorityHostClient:
    """Keyless proxy implementing the ``AuthoringTrustProvider`` protocol over IPC."""

    def __init__(self, transport: Transport, config: ProtectedConfig) -> None:
        self._transport = transport
        self._config = config
        self._correlation = itertools.count(1)

    # -- wire plumbing ------------------------------------------------------------

    def _invoke(
        self,
        method: str,
        workspace_id: str,
        params: Mapping[str, object],
    ) -> dict[str, object]:
        if method not in WIRE_METHODS:
            # Defensive: nothing here should route a non-allowlisted method (e.g.
            # advance_authority) onto the wire.
            raise AuthorityAdministrationError(
                f"method is not on the authoring wire allowlist: {method}"
            )
        correlation_id = f"cor-{next(self._correlation):016d}"
        request = canonical_message_bytes(
            {
                "protocol_version": PROTOCOL_VERSION,
                "method": method,
                "workspace_id": workspace_id,
                "correlation_id": correlation_id,
                "params": dict(params),
            }
        )
        if len(request) > self._config.max_message_bytes:
            raise AuthorityTransportError("authority request exceeds the configured size limit")
        raw = self._transport.roundtrip(request)
        message = _parse_message(raw, max_bytes=self._config.max_message_bytes)
        if message.get("protocol_version") != PROTOCOL_VERSION:
            raise AuthorityProtocolError("authority host protocol version mismatch")
        if message.get("correlation_id") != correlation_id:
            raise AuthorityProtocolError("authority host correlation id mismatch")
        status = message.get("status")
        if status == "ok":
            result = message.get("result")
            if not isinstance(result, dict):
                raise AuthorityProtocolError("authority host result payload is malformed")
            return result
        if status == "error":
            if message.get("code") == "E_PROVIDER_REFUSED":
                raise AuthorityHostRefusalError("authority host refused the operation")
            raise AuthorityProtocolError("authority host returned an unrecognized error")
        raise AuthorityProtocolError("authority host response is incoherent")

    def _invoke_none(
        self,
        method: str,
        workspace_id: str,
        params: Mapping[str, object],
    ) -> None:
        result = self._invoke(method, workspace_id, params)
        if result != {}:
            raise AuthorityProtocolError(
                "authority host returned an unexpected payload for a void method"
            )

    # -- provider protocol (methods 1-8) -----------------------------------------

    def authority_high_water(self, workspace_id: str) -> AuthorityHighWater:
        result = self._invoke("authority_high_water", workspace_id, {})
        return _validate(AuthorityHighWater, result)

    def authoring_state(self, workspace_id: str) -> AuthoringProviderState:
        result = self._invoke("authoring_state", workspace_id, {})
        return _validate(AuthoringProviderState, result)

    def authenticate_actor(
        self,
        credential: OperationCredential,
        *,
        expected_intent_digest: str,
        now: datetime,
    ) -> ActorCapability:
        result = self._invoke(
            "authenticate_actor",
            credential.workspace_id,
            {
                "credential": credential.model_dump(mode="json"),
                "expected_intent_digest": expected_intent_digest,
                "now": now.isoformat(),
            },
        )
        return _validate(ActorCapability, result)

    def authenticate_recovery(
        self,
        identity: AuthoringTransactionIdentity,
        authorization: RecoveryAuthorization,
    ) -> ActorCapability:
        result = self._invoke(
            "authenticate_recovery",
            identity.workspace_id,
            {
                "identity": identity.model_dump(mode="json"),
                "authorization": authorization.model_dump(mode="json"),
            },
        )
        return _validate(ActorCapability, result)

    def reserve_transaction(self, identity: AuthoringTransactionIdentity) -> None:
        self._invoke_none(
            "reserve_transaction",
            identity.workspace_id,
            {"identity": identity.model_dump(mode="json")},
        )

    def authorize_recovery(
        self,
        identity: AuthoringTransactionIdentity,
    ) -> RecoveryAuthorization:
        result = self._invoke(
            "authorize_recovery",
            identity.workspace_id,
            {"identity": identity.model_dump(mode="json")},
        )
        return _validate(RecoveryAuthorization, result)

    def finalize_transaction(self, identity: AuthoringTransactionIdentity) -> None:
        self._invoke_none(
            "finalize_transaction",
            identity.workspace_id,
            {"identity": identity.model_dump(mode="json")},
        )

    def abort_reserved_transaction(self, identity: AuthoringTransactionIdentity) -> None:
        self._invoke_none(
            "abort_reserved_transaction",
            identity.workspace_id,
            {"identity": identity.model_dump(mode="json")},
        )

    def advance_authority(
        self,
        *,
        expected: AuthorityHighWater,
        replacement: AuthorityHighWater,
    ) -> None:
        # Method 9 exists only for protocol conformance. It is authority administration,
        # off the authoring wire allowlist; hard-refuse without touching the transport.
        del expected, replacement
        raise AuthorityAdministrationError(
            "advance_authority is authority administration, not available on the authoring client"
        )

    # -- out-of-band credential issuance -----------------------------------------

    def issue_credential(self, intent: AuthoringIntent) -> OperationCredential:
        """Exchange a public intent for its intent-bound operation credential."""

        result = self._invoke(
            "issue_credential",
            intent.workspace_id,
            {"intent": intent.model_dump(mode="json")},
        )
        return _validate(OperationCredential, result)


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _validate(model: type[_ModelT], result: Mapping[str, object]) -> _ModelT:
    try:
        return model.model_validate(dict(result))
    except ValidationError as exc:
        raise AuthorityProtocolError(
            f"authority host {model.__name__} payload failed validation"
        ) from exc


__all__ = [
    "PROTOCOL_VERSION",
    "WIRE_METHODS",
    "AuthorityAdministrationError",
    "AuthorityClientError",
    "AuthorityHostClient",
    "AuthorityHostRefusalError",
    "AuthorityProtocolError",
    "AuthorityTransportError",
    "LocalIpcTransport",
    "ProtectedConfig",
    "Transport",
    "canonical_message_bytes",
    "config_is_group_or_other_writable",
    "resolve_protected_config",
]
