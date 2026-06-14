"""L4 — the forecasting function module expands the real pack (drop-a-file).

Dropping ``ontology/commercial/forecasting.yaml`` next to the base ontology makes
``build_commercial_pack`` pick it up with no seed change; its rules ship tagged
FUNCTION=forecasting and serve as their own slice.
"""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import context_for_function, load_pack
from ontowiz_spec import Lifecycle

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"
FORECASTING_IDS = {
    "rule_loe_erosion_curve",
    "rule_demand_sensing_divergence",
    "rule_analog_launch_trajectory",
    "rule_scenario_sensitivity",
}


def test_forecasting_module_ships_in_the_real_pack(tmp_path):
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    pack = load_pack(pack_dir)
    ids = {a.id for a in pack.artifacts}
    assert ids >= FORECASTING_IDS                       # forecasting rules shipped
    assert "rule_formulary_exclusion" in ids            # base pack still intact
    assert all(a.lifecycle == Lifecycle.ACTIVE for a in pack.artifacts)


def test_forecasting_slice_serves_in_isolation(tmp_path):
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    pack = load_pack(pack_dir)
    served = {
        a.id
        for a in context_for_function("model our post-LOE erosion", pack, "forecasting").eligible
    }
    assert served == FORECASTING_IDS  # exactly the forecasting slice, nothing else


def test_forecasting_entities_merged_into_registry(tmp_path):
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    pack = load_pack(pack_dir)
    from ontowiz_spec import EntityRegistry

    registry = next(a for a in pack.artifacts if isinstance(a, EntityRegistry))
    names = {e.name for e in registry.entities}
    assert {"Brand", "Forecast", "ScenarioDriver"} <= names  # base + module entities
