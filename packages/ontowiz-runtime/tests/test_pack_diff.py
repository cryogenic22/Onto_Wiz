"""C9 — version diff: what changed between two pack versions (the evolve view)."""

from __future__ import annotations

from ontowiz_ctx.core.model import CTXDocument, Header, Layer
from ontowiz_runtime import LoadedPack, pack_diff
from ontowiz_spec import DecisionHeuristic, Lifecycle, PackManifest, Tag, TagDimension


def _h(hid: str, function: str, logic: str = "x => y") -> DecisionHeuristic:
    return DecisionHeuristic(
        id=hid, name=hid, decision_logic=logic,
        tags=[Tag(dimension=TagDimension.FUNCTION, value=function)],
    ).transition(Lifecycle.ACTIVE, changed_by="c", delta_id="d")


def _pack(version: str, artifacts) -> LoadedPack:
    doc = CTXDocument(header=Header(magic="§CTX", version="1.0", layer=Layer.L2))
    return LoadedPack(
        manifest=PackManifest(name="commercial_analytics", version=version),
        l2_doc=doc, artifacts=artifacts,
    )


def test_pack_diff_added_removed_changed():
    a = _pack("0.1.0", [_h("rule_keep", "market_access"), _h("rule_gone", "brand_performance")])
    b = _pack("0.3.0", [
        _h("rule_keep", "market_access", logic="x => z"),   # changed content
        _h("rule_loe", "forecasting"),                       # added
    ])
    d = pack_diff(a, b)

    assert d.from_version == "0.1.0" and d.to_version == "0.3.0"
    assert d.added == ["rule_loe"]
    assert d.removed == ["rule_gone"]
    assert d.changed == ["rule_keep"]
    # per-function deltas: forecasting appeared, brand_performance disappeared
    assert d.function_deltas["forecasting"] == {"from": 0, "to": 1, "delta": 1}
    assert d.function_deltas["brand_performance"] == {"from": 1, "to": 0, "delta": -1}


def test_pack_diff_identical_is_empty():
    a = _pack("0.1.0", [_h("rule_keep", "market_access")])
    b = _pack("0.1.1", [_h("rule_keep", "market_access")])
    d = pack_diff(a, b)
    assert d.added == [] and d.removed == [] and d.changed == []
