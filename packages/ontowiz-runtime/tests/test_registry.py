"""Loop 2 (F2-B) — pack write/load round-trip + registry."""

from __future__ import annotations

import pytest
from ontowiz_ctx.core.model import Section
from ontowiz_factory.compiler import compile_pack, write_pack
from ontowiz_runtime.registry import LoadedPack, PackRegistry, load_pack
from ontowiz_spec import DataQuirk, Lifecycle, MetricDefinition


def _active(art):
    return art.transition(Lifecycle.ACTIVE, changed_by="curator", delta_id="d1")


def test_load_rejects_path_traversal(tmp_path):
    reg = PackRegistry(tmp_path)
    # traversal, the target==base degenerate case, and empty components all refuse
    for name, version in [("..", ".."), ("../../etc", "x"), ("../..", "0.1"),
                          ("foo", ".."), ("", ""), (".", ".")]:
        with pytest.raises(FileNotFoundError):
            reg.load(name, version)


def test_write_load_roundtrip(tmp_path):
    dq = _active(DataQuirk(id="dq1", name="iqvia-lag", data_source="IQVIA", quirk_description="lag"))
    m = _active(MetricDefinition(id="m1", name="trx", formula="sum(scripts)"))
    pack = compile_pack([dq, m], name="commercial_analytics", version="0.1.0")

    pack_dir = write_pack(pack, tmp_path)
    loaded = load_pack(pack_dir)

    assert isinstance(loaded, LoadedPack)
    assert loaded.manifest.name == "commercial_analytics"
    assert loaded.manifest.artifact_count == 2
    assert {a.id for a in loaded.artifacts} == {"dq1", "m1"}

    # artifact types + fields reconstructed faithfully
    dq_loaded = next(a for a in loaded.artifacts if a.id == "dq1")
    assert isinstance(dq_loaded, DataQuirk)
    assert dq_loaded.data_source == "IQVIA"
    assert dq_loaded.lifecycle == Lifecycle.ACTIVE
    # the CTX L2 layer parsed back into sections (uppercase directory keys)
    assert any("dq1" in s.name.lower() for s in loaded.l2_doc.body if isinstance(s, Section))


def test_pack_is_signed_and_tamper_evident(tmp_path):
    from ontowiz_factory.compiler import verify_pack
    pack = compile_pack([_active(DataQuirk(id="dq1", name="q"))], name="p", version="0.1.0")
    pack_dir = write_pack(pack, tmp_path)
    assert (pack_dir / "pack.sig").is_file()
    assert load_pack(pack_dir).manifest.signed is True
    assert verify_pack(pack_dir) is True
    # tampering with a shipped artifact is detected
    next((pack_dir / "artifacts").glob("*.yaml")).write_text(
        "kind: data_quirk\nid: hacked\n", encoding="utf-8"
    )
    assert verify_pack(pack_dir) is False


def test_registry_lists_and_loads(tmp_path):
    pack = compile_pack([_active(DataQuirk(id="dq1", name="q"))], name="p", version="0.1.0")
    write_pack(pack, tmp_path)

    reg = PackRegistry(tmp_path)
    manifests = reg.list_manifests()
    assert len(manifests) == 1
    assert manifests[0].name == "p" and manifests[0].version == "0.1.0"

    loaded = reg.load("p", "0.1.0")
    assert loaded.artifacts[0].id == "dq1"
