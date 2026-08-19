"""Authority-client error hierarchy.

This module has **no** dependency on the authoring kernel so that both the kernel
(``authoring.py``) and the client (``authority_client.py``) can import it without a
cycle. Every error here derives from :class:`AuthorityClientError` and from nothing in
the kernel/adapter error hierarchies (``AuthoringError``, ``WorkspaceError``,
``ArchiveError``, ``AuthorizationError``, ``pydantic.ValidationError``, ``OSError``).
That distinctness is load-bearing: it is what lets a transport failure raised deep
inside a provider call **survive** the kernel's ``except Exception`` wrapping points and
be mapped by the adapter to the stable ``E_AUTHORITY_UNAVAILABLE`` code
(``CONTRACT_IPC_WIRE.md §5``), instead of being relabelled ``E_AUTHORIZATION`` or
``E_VALIDATION``.
"""

from __future__ import annotations


class AuthorityClientError(Exception):
    """Base for every keyless authority-client failure.

    Deliberately a direct subclass of :class:`Exception` and unrelated to any kernel or
    adapter error type. The adapter maps this base to ``E_AUTHORITY_UNAVAILABLE``.
    """


class AuthorityTransportError(AuthorityClientError):
    """The authority host is unprovisioned or unreachable.

    Raised for missing/unreadable/insecure protected config, server-pin/authentication
    mismatch, an unreachable endpoint, a transport-level failure, an oversized or
    otherwise unframeable message, or a per-call timeout. The client never blindly
    retries a mutation on this error; it returns to recovery.
    """


class AuthorityProtocolError(AuthorityClientError):
    """A reachable host returned a malformed or non-conforming wire message.

    Raised for a protocol-version mismatch, an oversized/duplicate-key/non-finite or
    otherwise unparseable response, an unexpected correlation id, or a response that
    fails to validate against the method's declared return model.
    """


class AuthorityAdministrationError(AuthorityClientError):
    """An authority-administration operation was attempted on the authoring client.

    ``advance_authority`` (provider method 9) exists only for protocol conformance and
    is **off** the authoring wire allowlist; invoking it on the keyless client raises
    this rather than reaching the transport. Administration runs on a separate
    administrative client and channel, out of P3.
    """


__all__ = [
    "AuthorityAdministrationError",
    "AuthorityClientError",
    "AuthorityProtocolError",
    "AuthorityTransportError",
]
