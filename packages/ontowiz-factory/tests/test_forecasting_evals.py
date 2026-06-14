"""C8 — forecasting eval cases: extend the suite to cover the forecasting slice.

The 26-case suite targeted the original 19 heuristics; the forecasting module
shipped unbenched. These 4 cases close that structural gap — each governed term
is verified present in its heuristic's served content (grounded) and absent from
its own question (hard). The live agent-lift number for 0.3.0 remains a separate,
deferred measurement step.
"""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.commercial_eval_suite import COMMERCIAL_EVAL_CASES, FORECASTING_EVAL_CASES
from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import load_pack

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"

# eval case id → (heuristic id it validates, the governed term)
_MAP = {
    "lift_loe_erosion_curve": ("rule_loe_erosion_curve", "plateau"),
    "lift_demand_sensing_divergence": ("rule_demand_sensing_divergence", "divergence"),
    "lift_analog_launch_trajectory": ("rule_analog_launch_trajectory", "analog"),
    "lift_scenario_sensitivity": ("rule_scenario_sensitivity", "sensitivity"),
}


def test_suite_grew_to_thirty_with_forecasting():
    assert len(FORECASTING_EVAL_CASES) == 4
    assert len(COMMERCIAL_EVAL_CASES) == 30          # 19 core + 7 traps + 4 forecasting
    ids = [c.id for c in COMMERCIAL_EVAL_CASES]
    assert len(ids) == len(set(ids))                 # still unique


def test_forecasting_terms_are_grounded_in_the_served_pack(tmp_path):
    pack = load_pack(build_commercial_pack(COMMERCIAL_YAML, tmp_path))
    by_id = {a.id: a for a in pack.artifacts}
    cases = {c.id: c for c in FORECASTING_EVAL_CASES}
    for case_id, (rule_id, term) in _MAP.items():
        case = cases[case_id]
        assert term in case.must_contain
        body = f"{by_id[rule_id].name} {by_id[rule_id].to_prompt_text()}".lower()
        assert term in body, f"{rule_id} body does not contain governed term '{term}'"
        assert term.lower() not in case.question.lower()   # not leaked in the question
