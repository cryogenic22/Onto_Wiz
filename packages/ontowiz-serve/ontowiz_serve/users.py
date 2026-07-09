"""User store (Tier A) — the authenticated principals behind RBAC.

A DB-backed table of users (id, email, password_hash, role) sharing the catalog
database (``<root>/catalog.db``, ADR-016). Seeded with one demo user per known
role so a deployment has working logins out of the box; real identity
provisioning (signup, reset, SSO) is out of scope (see ADR-017 boundaries).

The demo seed password defaults to ``ONTOWIZ_SEED_PASSWORD`` or ``ontowiz-demo``.
The bcrypt hash is computed once per process and reused across the seed users —
they share the demo password anyway — so test apps don't pay bcrypt per build.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ontowiz_runtime import Database

from .auth import hash_password, verify_password
from .roles import KNOWN_ROLES

_SEED_EMAILS = {role: f"{role}@ontowiz.ai" for role in sorted(KNOWN_ROLES)}
_seed_hash_cache: dict[str, str] = {}


def _seed_hash(password: str) -> str:
    if password not in _seed_hash_cache:
        _seed_hash_cache[password] = hash_password(password)
    return _seed_hash_cache[password]


@dataclass
class User:
    """An authenticated principal."""

    id: str
    email: str
    role: str


class UserStore:
    """Users keyed by email, DB-backed under ``root``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._db = Database(self.root / "catalog.db")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
            "password_hash TEXT NOT NULL, role TEXT NOT NULL)"
        )

    def seed_default(self, password: str | None = None) -> None:
        """Insert one demo user per known role (idempotent)."""
        pw = password or os.getenv("ONTOWIZ_SEED_PASSWORD") or "ontowiz-demo"
        for role, email in _SEED_EMAILS.items():
            if self._db.fetch_one("SELECT id FROM users WHERE email = ?", (email,)) is None:
                self._db.execute(
                    "INSERT INTO users (id, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    (role, email, _seed_hash(pw), role),
                )

    def authenticate(self, email: str, password: str) -> User | None:
        """Return the User on a correct email+password, else None."""
        row = self._db.fetch_one(
            "SELECT id, email, password_hash, role FROM users WHERE email = ?",
            ((email or "").strip().lower(),),
        )
        if row is None or not verify_password(password, row["password_hash"]):
            return None
        return User(id=row["id"], email=row["email"], role=row["role"])
