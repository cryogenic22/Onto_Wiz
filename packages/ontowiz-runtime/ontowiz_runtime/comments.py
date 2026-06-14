"""Annotation / comment store (Tier A) — governed discussion on an artifact.

A lightweight, JSON-on-disk store of role-attributed comments keyed by
(pack, version, artifact_id). This is the collaboration layer of the catalog:
SMEs annotate, curators record decisions, builders note usage. MVP persistence
(a single JSON file, not a database) — honest and self-contained; swappable for a
real store later without changing the call sites.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


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
    """Append-only comments keyed by (pack, version, artifact_id), JSON-backed."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._file = self.root / "comments.json"

    def _load(self) -> dict[str, list[dict]]:
        if not self._file.is_file():
            return {}
        data = json.loads(self._file.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _key(pack: str, version: str, artifact_id: str) -> str:
        return f"{pack}\x1f{version}\x1f{artifact_id}"

    def add(
        self, pack: str, version: str, artifact_id: str,
        *, author: str, role: str, text: str, at: str | None = None,
    ) -> Comment:
        """Append a comment and persist it. Returns the stored Comment."""
        comment = Comment(
            pack=pack, version=version, artifact_id=artifact_id,
            author=author, role=role, text=text, created_at=at or _now(),
        )
        data = self._load()
        data.setdefault(self._key(pack, version, artifact_id), []).append(asdict(comment))
        self._file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return comment

    def list(self, pack: str, version: str, artifact_id: str) -> list[Comment]:
        """All comments on an artifact, in the order they were added."""
        rows = self._load().get(self._key(pack, version, artifact_id), [])
        return [Comment(**row) for row in rows]
