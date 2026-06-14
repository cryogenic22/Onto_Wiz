"""C1 — catalog index: one rich entry per pack, grouped across versions.

Backs the Domain Intelligence Catalog grid: domain, every version (latest first),
artifact count, the pack's function slices with counts, sealed flag, and the
eval/lift summary from the manifest.
"""

from __future__ import annotations

from ontowiz_factory.compiler import compile_pack, write_pack
from ontowiz_runtime import PackRegistry, catalog_index
from ontowiz_spec import DecisionHeuristic, Lifecycle, PackEvalSummary, Tag, TagDimension


def _h(hid: str, function: str) -> DecisionHeuristic:
    art = DecisionHeuristic(
        id=hid, name=hid, decision_logic="x => y",
        tags=[
            Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial"),
            Tag(dimension=TagDimension.FUNCTION, value=function),
        ],
    )
    return art.transition(Lifecycle.ACTIVE, changed_by="c", delta_id="d")


def _build(tmp_path, version: str, *, lift: float | None) -> None:
    pack = compile_pack(
        [_h("rule_a", "market_access"), _h("rule_b", "market_access"), _h("rule_c", "brand_performance")],
        name="commercial_analytics", version=version, domain="commercial",
    )
    pack.manifest.evals = PackEvalSummary(eval_cases=3, pass_rate=1.0, agent_lift=lift, gate_passed=True)
    write_pack(pack, tmp_path)


def test_catalog_index_groups_versions_and_functions(tmp_path):
    _build(tmp_path, "0.1.0", lift=0.30)
    _build(tmp_path, "0.2.0", lift=0.31)
    idx = catalog_index(PackRegistry(tmp_path))

    assert len(idx) == 1
    e = idx[0]
    assert e.name == "commercial_analytics"
    assert e.domain == "commercial"
    assert e.latest_version == "0.2.0"               # semver-latest, not lexical
    assert set(e.versions) == {"0.1.0", "0.2.0"}
    assert e.artifact_count == 3
    assert e.functions == {"market_access": 2, "brand_performance": 1}
    assert e.signed is True                          # write_pack seals
    assert e.eval_cases == 3 and e.agent_lift == 0.31  # latest version's summary


def test_catalog_index_sorts_versions_descending(tmp_path):
    for v in ("0.9.0", "0.10.0", "0.2.0"):           # 0.10.0 must beat 0.9.0
        _build(tmp_path, v, lift=None)
    e = catalog_index(PackRegistry(tmp_path))[0]
    assert e.latest_version == "0.10.0"
    assert e.versions[0] == "0.10.0"                 # descending
