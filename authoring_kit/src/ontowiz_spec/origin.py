"""Verification for the read-only source-origin content lock."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class OriginDriftError(RuntimeError):
    """Raised when a source reference no longer matches the recorded bytes."""


def verify_origin_lock(lock_path: str | Path) -> None:
    lock_file = Path(lock_path)
    data = json.loads(lock_file.read_text(encoding="utf-8"))
    if data.get("phase_one_access") != "read-only":
        raise OriginDriftError("source origin is not locked read-only")
    source_root = Path(data["source_repository"])
    for entry in data["files"]:
        relative = Path(entry["path"])
        candidate = source_root / relative
        try:
            payload = candidate.read_bytes()
        except OSError as exc:
            raise OriginDriftError(f"{relative.as_posix()}: unreadable") from exc
        actual = hashlib.sha256(payload).hexdigest()
        if len(payload) != entry["bytes"] or actual != entry["sha256"]:
            raise OriginDriftError(f"{relative.as_posix()}: source drift")
