"""Test-only reference authority host.

Serves the P3.1 authority wire protocol over authenticated local IPC, backed by the
existing in-memory :class:`ExternalTestProvider`. This host, and any provider, live
**only** under ``tests/`` — the ``src`` tree and the shipped skill bundle carry no host,
keys, admin surface, or provider (asserted by the evaluation repository-boundary test).
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import threading
import uuid
from datetime import datetime
from multiprocessing import AuthenticationError
from multiprocessing.connection import Listener
from typing import Literal

from adapters._support import ExternalTestProvider
from ontowiz_authoring.authoring import (
    AuthoringIntent,
    AuthoringTransactionIdentity,
    OperationCredential,
    RecoveryAuthorization,
)
from ontowiz_authoring.authority_client import (
    PROTOCOL_VERSION,
    WIRE_METHODS,
    canonical_message_bytes,
)

_MAX_MESSAGE_BYTES = 1_048_576


def default_address(family: Literal["AF_PIPE", "AF_UNIX"]) -> str:
    """A unique, non-colliding local endpoint for the given IPC family."""

    token = uuid.uuid4().hex
    if family == "AF_PIPE":
        return rf"\\.\pipe\ontowiz-authority-{token}"
    return os.path.join(tempfile.gettempdir(), f"ontowiz-authority-{token}.sock")


def _strict_parse(raw: bytes, max_bytes: int) -> dict[str, object]:
    if not raw or len(raw) > max_bytes:
        raise ValueError("message size is invalid")

    def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def _reject_non_finite(value: str) -> object:
        raise ValueError(f"non-finite constant: {value}")

    parsed = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_non_finite,
    )
    if not isinstance(parsed, dict):
        raise ValueError("message is not an object")
    return parsed


class ReferenceAuthorityHost:
    """One-connection-per-exchange reference host, run in a background thread."""

    def __init__(
        self,
        provider: ExternalTestProvider,
        *,
        family: Literal["AF_PIPE", "AF_UNIX"],
        authkey: bytes,
        address: str | None = None,
        drafting_principal: str = "draft-agent",
    ) -> None:
        self._provider = provider
        self._family = family
        self._authkey = authkey
        self.address = address or default_address(family)
        self._drafting_principal = drafting_principal
        self._listener: Listener | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def __enter__(self) -> ReferenceAuthorityHost:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()

    def start(self) -> None:
        self._listener = Listener(self.address, family=self._family, authkey=self._authkey)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        # Closing the listener unblocks a blocked accept() (it fails with OSError, which
        # _serve treats as shutdown). No dummy client is connected — that deadlocks on
        # Windows named pipes after a failed-auth connection.
        if self._listener is not None:
            with contextlib.suppress(OSError):
                self._listener.close()
        if self._thread is not None:
            # Daemon thread: a still-blocked accept() dies with the process rather than
            # hanging teardown.
            self._thread.join(timeout=2)

    def _serve(self) -> None:
        listener = self._listener
        assert listener is not None
        while not self._stop.is_set():
            try:
                connection = listener.accept()
            except (OSError, AuthenticationError):
                continue
            with connection:
                if self._stop.is_set():
                    break
                try:
                    raw = connection.recv_bytes(maxlength=_MAX_MESSAGE_BYTES)
                    connection.send_bytes(self._dispatch(raw))
                except (OSError, EOFError):
                    continue

    def _dispatch(self, raw: bytes) -> bytes:
        try:
            request = _strict_parse(raw, _MAX_MESSAGE_BYTES)
        except ValueError:
            return self._error("unknown", "E_PROTOCOL", "malformed request")
        correlation_id = request.get("correlation_id")
        if not isinstance(correlation_id, str):
            correlation_id = "unknown"
        if request.get("protocol_version") != PROTOCOL_VERSION:
            return self._error(correlation_id, "E_PROTOCOL", "protocol version mismatch")
        method = request.get("method")
        if method not in WIRE_METHODS:
            return self._error(correlation_id, "E_METHOD_NOT_ALLOWED", "method is not allowed")
        workspace_id = request.get("workspace_id")
        params = request.get("params")
        if not isinstance(workspace_id, str) or not isinstance(params, dict):
            return self._error(correlation_id, "E_PROTOCOL", "malformed envelope")
        try:
            result = self._call(str(method), workspace_id, params)
        except Exception:  # noqa: BLE001 - any provider refusal is redacted to one code
            return self._error(correlation_id, "E_PROVIDER_REFUSED", "operation refused")
        return self._ok(correlation_id, result)

    def _call(
        self,
        method: str,
        workspace_id: str,
        params: dict[str, object],
    ) -> dict[str, object]:
        provider = self._provider
        if method == "authority_high_water":
            return provider.authority_high_water(workspace_id).model_dump(mode="json")
        if method == "authoring_state":
            return provider.authoring_state(workspace_id).model_dump(mode="json")
        if method == "authenticate_actor":
            credential = OperationCredential.model_validate(params["credential"])
            actor = provider.authenticate_actor(
                credential,
                expected_intent_digest=str(params["expected_intent_digest"]),
                now=datetime.fromisoformat(str(params["now"])),
            )
            return actor.model_dump(mode="json")
        if method == "authenticate_recovery":
            identity = AuthoringTransactionIdentity.model_validate(params["identity"])
            authorization = RecoveryAuthorization.model_validate(params["authorization"])
            return provider.authenticate_recovery(identity, authorization).model_dump(mode="json")
        if method == "reserve_transaction":
            provider.reserve_transaction(AuthoringTransactionIdentity.model_validate(params["identity"]))
            return {}
        if method == "authorize_recovery":
            identity = AuthoringTransactionIdentity.model_validate(params["identity"])
            return provider.authorize_recovery(identity).model_dump(mode="json")
        if method == "finalize_transaction":
            provider.finalize_transaction(AuthoringTransactionIdentity.model_validate(params["identity"]))
            return {}
        if method == "abort_reserved_transaction":
            identity = AuthoringTransactionIdentity.model_validate(params["identity"])
            provider.abort_reserved_transaction(identity)
            return {}
        if method == "issue_credential":
            intent = AuthoringIntent.model_validate(params["intent"])
            context = provider.context(self._drafting_principal, intent.intent_digest)
            return context.credential.model_dump(mode="json")
        raise KeyError(method)

    def _ok(self, correlation_id: str, result: dict[str, object]) -> bytes:
        return canonical_message_bytes(
            {
                "protocol_version": PROTOCOL_VERSION,
                "correlation_id": correlation_id,
                "status": "ok",
                "result": result,
            }
        )

    def _error(self, correlation_id: str, code: str, message: str) -> bytes:
        return canonical_message_bytes(
            {
                "protocol_version": PROTOCOL_VERSION,
                "correlation_id": correlation_id,
                "status": "error",
                "code": code,
                "message": message,
            }
        )
