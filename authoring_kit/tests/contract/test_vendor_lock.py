from pathlib import Path

from tools.verify_vendor_lock import verify_vendor_lock


def test_pinned_namespace_matches_vendor_lock() -> None:
    verify_vendor_lock(Path(__file__).resolve().parents[2])
