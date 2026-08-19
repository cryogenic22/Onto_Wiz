"""Verify the phase-one read-only Onto_Wiz source content lock."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from ontowiz_spec.origin import verify_origin_lock  # noqa: E402


def main() -> None:
    verify_origin_lock(REPOSITORY_ROOT / "locks" / "source-origin.json")
    print("source-lock-ok")


if __name__ == "__main__":
    main()
