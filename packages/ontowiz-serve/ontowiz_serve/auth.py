"""Auth service (Tier A) — bcrypt password hashing + pyjwt HS256 tokens.

Ported from market_zero `services/auth.py`, adapted to OntoWiz: authorization
stays *capability-based* (``roles.py``), so a token carries the caller's verified
role and api.py derives capabilities from it. Pure helpers — no DB, no HTTP.

Security notes:
  - Passwords hashed with bcrypt (library-default work factor).
  - JWTs signed HS256 with ``ONTOWIZ_JWT_SECRET``. With no env var a random
    per-process secret is used (dev): a restart invalidates all tokens, and
    production MUST set the env var.
  - Tokens carry: sub (user id), role, email, iat, exp. 24h default TTL.
"""

from __future__ import annotations

import os
import secrets
import time
from typing import Any

import bcrypt
import jwt

DEFAULT_TOKEN_TTL_SECONDS = 24 * 3600
_JWT_SECRET = os.getenv("ONTOWIZ_JWT_SECRET") or secrets.token_urlsafe(32)
_JWT_ALGORITHM = "HS256"


class AuthError(Exception):
    """Raised on auth-layer failures (bad token, expired, signature mismatch)."""


def hash_password(plaintext: str) -> str:
    """Hash a password with bcrypt. Returns the hash as a UTF-8 string."""
    if not isinstance(plaintext, str):
        raise TypeError("password must be a string")
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Constant-time bcrypt verify. Returns False on any error (defensive)."""
    if not (isinstance(plaintext, str) and isinstance(hashed, str)) or not (plaintext and hashed):
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False  # garbage hash format → treat as non-match


def issue_token(
    user_id: str, role: str, *, email: str = "",
    expires_in_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
) -> str:
    """Issue a signed JWT carrying the user's id, role and email.

    A negative ``expires_in_seconds`` is allowed so tests can mint expired tokens.
    """
    now = int(time.time())
    payload = {
        "sub": str(user_id), "role": role, "email": email,
        "iat": now, "exp": now + expires_in_seconds,
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises AuthError on any failure."""
    if not token or not isinstance(token, str):
        raise AuthError("missing or invalid token")
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError(f"invalid token: {exc}") from exc
