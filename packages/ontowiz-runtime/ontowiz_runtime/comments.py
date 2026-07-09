"""Annotation / comment store (Tier A) — governed discussion on an artifact.

Role-attributed comments keyed by (pack, version, artifact_id): SMEs annotate,
curators record decisions, builders note usage. Backed by the shared catalog
database (``<root>/catalog.db``) through the ``Database`` wrapper — SQLite for
dev/test, Postgres for production (ADR-016). The call-site contract
(``CommentStore(root)`` + ``add`` / ``list``) is unchanged from the JSON MVP.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .db import Database

_COLUMNS = "pack, version, artifact_id, author, role, text, created_at"


@dataclass
class Comment:
    """One role-attributed comment on an artifact."""

    pack: str
    version: str
    artifact_id: str
    author: str
    role: str
    text: str
    created_at: str


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


class CommentStore:
    """Append-only comments keyed by (pack, version, artifact_id), DB-backed."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._db = Database(self.root / "catalog.db")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS comments ("
            "pack TEXT NOT NULL, version TEXT NOT NULL, artifact_id TEXT NOT NULL, "
            "author TEXT NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL, "
            "created_at TEXT NOT NULL)"
        )

    def add(
        self, pack: str, version: str, artifact_id: str,
        *, author: str, role: str, text: str, at: str | None = None,
    ) -> Comment:
        """Append a comment and persist it. Returns the stored Comment."""
        comment = Comment(
            pack=pack, version=version, artifact_id=artifact_id,
            author=author, role=role, text=text, created_at=at or _now(),
        )
        self._db.execute(
            f"INSERT INTO comments ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pack, version, artifact_id, author, role, text, comment.created_at),
        )
        return comment

    def list(self, pack: str, version: str, artifact_id: str) -> list[Comment]:
        """All comments on an artifact, in the order they were added."""
        rows = self._db.fetch_all(
            f"SELECT {_COLUMNS} FROM comments "
            "WHERE pack = ? AND version = ? AND artifact_id = ? ORDER BY rowid",
            (pack, version, artifact_id),
        )
        return [Comment(**row) for row in rows]
