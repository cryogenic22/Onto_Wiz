"""F-RB1 — auth service: bcrypt hashing + pyjwt HS256 tokens (Tier A).

Ported from market_zero `services/auth.py`. Pure helpers (no DB/HTTP); the
principal binding (Bearer → role) lives in api.py. OntoWiz authz stays
capability-based (roles.py) — the token just carries the verified role.
"""

from __future__ import annotations

import pytest
from ontowiz_serve.auth import (
    AuthError,
    decode_token,
    hash_password,
    issue_token,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    h = hash_password("s3cret")
    assert h != "s3cret"  # not stored in the clear
    assert verify_password("s3cret", h)
    assert not verify_password("wrong", h)


def test_verify_rejects_garbage_and_empty():
    assert not verify_password("x", "not-a-bcrypt-hash")
    assert not verify_password("", "")


def test_issue_and_decode_roundtrip():
    tok = issue_token("u1", "curator", email="c@x.io")
    claims = decode_token(tok)
    assert claims["sub"] == "u1"
    assert claims["role"] == "curator"
    assert claims["email"] == "c@x.io"


def test_decode_expired_raises():
    tok = issue_token("u1", "sme", expires_in_seconds=-10)
    with pytest.raises(AuthError):
        decode_token(tok)


def test_decode_tampered_or_missing_raises():
    tok = issue_token("u1", "sme")
    with pytest.raises(AuthError):
        decode_token(tok + "tamper")
    with pytest.raises(AuthError):
        decode_token("")
