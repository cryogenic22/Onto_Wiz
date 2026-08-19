"""Verify that the pinned v0.1 namespace remains byte-for-byte immutable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def verify_vendor_lock(repository_root: Path) -> None:
    lock_path = repository_root / "locks" / "vendor-origin.json"
    lock: dict[str, Any] = json.loads(lock_path.read_text(encoding="utf-8"))
    vendor_root = repository_root / str(lock["vendor_package"])

    expected_names: set[str] = set()
    for entry in lock["files"]:
        relative_path = str(entry["path"])
        expected_names.add(relative_path)
        candidate = vendor_root / relative_path
        data = candidate.read_bytes()
        if len(data) != int(entry["bytes"]):
            raise ValueError(f"vendor byte-count drift: {relative_path}")
        digest = hashlib.sha256(data).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"vendor digest drift: {relative_path}")

    actual_names = {
        path.relative_to(vendor_root).as_posix()
        for path in vendor_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    unexpected = actual_names - expected_names
    missing = expected_names - actual_names
    if unexpected or missing:
        raise ValueError(
            f"vendor inventory drift: unexpected={sorted(unexpected)}, missing={sorted(missing)}"
        )


def main() -> None:
    verify_vendor_lock(Path(__file__).resolve().parents[1])
    print("vendor-lock-ok")


if __name__ == "__main__":
    main()
