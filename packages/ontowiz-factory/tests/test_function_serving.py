"""L3 — serve a single function slice of the one licensable pack.

``context_for_function`` is the convenience door over the tag gate: it narrows a
loaded pack to one ``TagDimension.FUNCTION`` slice, so a market-access consult
never sees brand-performance or competitive heuristics (and vice-versa).
"""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import context_for_function, load_pack

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"

MARKET_ACCESS_CORE = {
    "rule_genuine_budget_crisis", "rule_pa_access_barrier", "rule_formulary_exclusion",
    "rule_copay_accumulator_impact", "rule_medicare_reimbursement_squeeze",
    "rule_340b_contract_erosion", "rule_rebate_trap", "rule_competitor_lockout",
}
NON_MARKET_ACCESS = {
    "rule_safety_signal", "rule_supply_disruption",            # base
    "rule_demand_erosion", "rule_launch_stall", "rule_channel_shift",  # brand
    "rule_competitive_displacement", "rule_biosimilar_erosion",  # competitive
}


def test_context_for_function_serves_only_that_slice(tmp_path):
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    pack = load_pack(pack_dir)

    result = context_for_function(
        "Why did the payer's formulary change cut our volume?", pack, "market_access"
    )
    served = {a.id for a in result.eligible}

    assert served >= MARKET_ACCESS_CORE            # the whole market-access slice serves
    assert served.isdisjoint(NON_MARKET_ACCESS)    # no other function leaks in
    # the L3 directory the agent is shown is built from the slice only (section
    # names are the uppercased KIND-ID keys, e.g. ...-RULE_FORMULARY_EXCLUSION)
    assert "FORMULARY_EXCLUSION" in result.system_prompt
    assert "DEMAND_EROSION" not in result.system_prompt
    # trust envelope is stamped with the pack identity
    assert result.trust.pack == "commercial_analytics@0.1.0"


def test_full_pack_still_serves_everything(tmp_path):
    # the default (no function filter) still serves the whole pack — slicing is opt-in
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    pack = load_pack(pack_dir)
    from ontowiz_runtime import context_for_pack

    served = {a.id for a in context_for_pack("anything", pack).eligible}
    assert served >= MARKET_ACCESS_CORE
    assert {"rule_demand_erosion", "rule_safety_signal"} <= served


def test_function_slice_is_leaner_than_full_pack(tmp_path):
    # the functionalization payoff (offline, deterministic): serving one slice
    # ships a materially smaller L3 directory than the whole pack — fewer eligible
    # artifacts and a smaller token estimate for the system prompt.
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    pack = load_pack(pack_dir)
    from ontowiz_runtime import context_for_pack

    full = context_for_pack("anything", pack)
    slice_ = context_for_function("anything", pack, "market_access")

    assert len(slice_.eligible) < len(full.eligible)          # fewer artifacts served
    assert slice_.tokens_estimate < full.tokens_estimate      # leaner directory
    assert slice_.eligible                                    # but not empty
