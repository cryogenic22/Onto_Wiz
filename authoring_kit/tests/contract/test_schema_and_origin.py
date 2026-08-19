from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ontowiz_spec.origin import OriginDriftError, verify_origin_lock
from ontowiz_spec.schema_export import schema_documents


@pytest.mark.contract
def test_checked_in_schemas_match_contract_models() -> None:
    root = Path(__file__).parents[2]
    expected = schema_documents()
    actual = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((root / "schemas").glob("*.schema.json"))
    }
    assert actual == expected


@pytest.mark.contract
def test_origin_lock_verifies_exact_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    reference = source / "contract.txt"
    reference.write_bytes(b"candidate-only\n")
    digest = hashlib.sha256(reference.read_bytes()).hexdigest()
    lock = tmp_path / "lock.json"
    lock.write_text(
        json.dumps(
            {
                "lock_version": 1,
                "source_repository": source.as_posix(),
                "phase_one_access": "read-only",
                "schema_target": "ontowiz-spec/vNext-min",
                "schema_revision": 1,
                "files": [{"path": "contract.txt", "bytes": 15, "sha256": digest}],
            }
        ),
        encoding="utf-8",
    )

    verify_origin_lock(lock)
    reference.write_bytes(b"changed\n")
    with pytest.raises(OriginDriftError, match="contract.txt"):
        verify_origin_lock(lock)
