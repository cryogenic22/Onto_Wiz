"""C3 — catalog search: rank packs by query, surface matching artifacts, filter."""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.compiler import compile_pack, write_pack
from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import PackRegistry, catalog_search
from ontowiz_spec import DecisionHeuristic, Lifecycle

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"


def _finance_pack(tmp_path) -> None:
    h = DecisionHeuristic(
        id="rule_covenant_breach", name="Covenant Breach",
        decision_logic="leverage spike => covenant breach risk",
    ).transition(Lifecycle.ACTIVE, changed_by="c", delta_id="d")
    write_pack(compile_pack([h], name="finance_risk", version="0.1.0", domain="financial"), tmp_path)


def _registry(tmp_path) -> PackRegistry:
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    _finance_pack(tmp_path)
    return PackRegistry(tmp_path)


def test_search_matches_pack_by_artifact_text(tmp_path):
    reg = _registry(tmp_path)
    hits = {h.name: h for h in catalog_search(reg, "formulary")}
    assert "commercial_analytics" in hits
    assert "finance_risk" not in hits
    assert any(m["id"] == "rule_formulary_exclusion" for m in hits["commercial_analytics"].matched_artifacts)


def test_search_isolates_other_domain(tmp_path):
    reg = _registry(tmp_path)
    hits = [h.name for h in catalog_search(reg, "covenant")]
    assert hits == ["finance_risk"]


def test_search_function_filter(tmp_path):
    reg = _registry(tmp_path)
    hits = [h.name for h in catalog_search(reg, "", function="forecasting")]
    assert hits == ["commercial_analytics"]  # only the pack with a forecasting slice


def test_empty_query_returns_all(tmp_path):
    reg = _registry(tmp_path)
    assert {h.name for h in catalog_search(reg, "")} == {"commercial_analytics", "finance_risk"}
