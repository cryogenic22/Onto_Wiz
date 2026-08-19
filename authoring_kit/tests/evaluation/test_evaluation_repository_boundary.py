from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_production_tree_contains_no_vault_or_protected_fixture() -> None:
    production = [ROOT / "src", ROOT / "adapters"]
    forbidden_names = {"heldout", "oracles", "private-receipts", "vault"}
    for tree in production:
        for path in tree.rglob("*"):
            assert path.name.casefold() not in forbidden_names


def test_authoring_adapters_expose_no_custodian_command() -> None:
    adapter_text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ROOT / "src/ontowiz_authoring", ROOT / "adapters")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".md", ".yaml"}
    ).casefold()
    forbidden = (
        '"evaluate"',
        '"freeze-heldout"',
        '"score-heldout"',
        '"vault-status"',
    )
    assert not any(command in adapter_text for command in forbidden)
