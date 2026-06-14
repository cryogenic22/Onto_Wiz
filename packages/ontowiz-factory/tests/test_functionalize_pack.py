"""Functionalize the commercial pack — per-function tags + tag-sliced serving.

L1: every heuristic carries a ``function:`` tag (sub-dividing the one licensable
pack by ``TagDimension.FUNCTION``); the three oncology heuristics also carry a
``therapy_area:oncology`` overlay (a therapy tag, not a function).
L3: ``gate``/``get_context`` narrow to a single function slice on that tag.
"""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.seed import artifacts_from_commercial
from ontowiz_runtime.context import gate
from ontowiz_spec import ArtifactKind, Lifecycle, Tag, TagDimension

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"

# The agreed taxonomy (SESSION_HANDOFF open-thread 0). market_access lists the 8
# non-oncology core members; the oncology overlay rules additionally carry a
# function (pathway_exclusion is itself an access barrier → market_access).
BASE = {"rule_safety_signal", "rule_supply_disruption"}
MARKET_ACCESS_CORE = {
    "rule_genuine_budget_crisis", "rule_pa_access_barrier", "rule_formulary_exclusion",
    "rule_copay_accumulator_impact", "rule_medicare_reimbursement_squeeze",
    "rule_340b_contract_erosion", "rule_rebate_trap", "rule_competitor_lockout",
}
BRAND_PERFORMANCE = {
    "rule_demand_erosion", "rule_launch_stall", "rule_channel_shift", "rule_field_execution_gap",
}
COMPETITIVE_INTEL = {"rule_competitive_displacement", "rule_biosimilar_erosion"}
ONCOLOGY = {"rule_guideline_driven_shift", "rule_biomarker_testing_gap", "rule_pathway_exclusion"}


def _functions(artifact) -> set[str]:
    return {t.value for t in artifact.tags if t.dimension == TagDimension.FUNCTION}


def _therapies(artifact) -> set[str]:
    return {t.value for t in artifact.tags if t.dimension == TagDimension.THERAPY_AREA}


def test_every_heuristic_carries_exactly_one_function_tag():
    arts = artifacts_from_commercial(COMMERCIAL_YAML)
    heuristics = [a for a in arts if a.kind == ArtifactKind.DECISION_HEURISTIC]
    assert heuristics
    for h in heuristics:
        assert len(_functions(h)) == 1, f"{h.id} functions={_functions(h)}"


def test_function_taxonomy_mapping():
    arts = {a.id: a for a in artifacts_from_commercial(COMMERCIAL_YAML)}
    for rid in BASE:
        assert _functions(arts[rid]) == {"base"}, rid
    for rid in MARKET_ACCESS_CORE:
        assert _functions(arts[rid]) == {"market_access"}, rid
    for rid in BRAND_PERFORMANCE:
        assert _functions(arts[rid]) == {"brand_performance"}, rid
    for rid in COMPETITIVE_INTEL:
        assert _functions(arts[rid]) == {"competitive_intel"}, rid


def test_oncology_rules_carry_therapy_overlay():
    arts = {a.id: a for a in artifacts_from_commercial(COMMERCIAL_YAML)}
    for rid in ONCOLOGY:
        assert "oncology" in _therapies(arts[rid]), rid
        # oncology is an overlay, not a function — each still has a function
        assert _functions(arts[rid]), rid


def test_gate_serves_only_the_function_slice():
    arts = artifacts_from_commercial(COMMERCIAL_YAML)
    active = [a.transition(Lifecycle.ACTIVE, changed_by="t", delta_id="d") for a in arts]
    slice_ = gate(active, tags=[Tag(dimension=TagDimension.FUNCTION, value="market_access")])
    ids = {a.id for a in slice_}
    # the 8 core market-access heuristics are all served …
    assert ids >= MARKET_ACCESS_CORE
    # … and nothing from another function leaks in
    assert ids.isdisjoint(BASE | BRAND_PERFORMANCE | COMPETITIVE_INTEL)
    # the whole slice is, by construction, market_access
    assert all("market_access" in _functions(a) for a in slice_)
