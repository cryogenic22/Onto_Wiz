"""C2 — function-slice surface: per-function counts, coverage, and token leanness."""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import load_pack, pack_functions

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"


def test_pack_functions_surface(tmp_path):
    pack = load_pack(build_commercial_pack(COMMERCIAL_YAML, tmp_path))
    slices = {s.function: s for s in pack_functions(pack)}

    assert set(slices) == {"base", "market_access", "brand_performance", "competitive_intel", "forecasting"}
    fc = slices["forecasting"]
    assert fc.count == 4
    assert fc.served_count == 4            # all forecasting heuristics are ACTIVE
    assert fc.eval_count == 0             # forecasting is not yet eval-covered (honest)
    # the functionalization payoff: a slice's directory is leaner than the full pack
    assert fc.slice_tokens < fc.full_tokens
    assert slices["market_access"].count == 9   # 8 core + pathway_exclusion overlay


def test_pack_functions_full_tokens_constant(tmp_path):
    pack = load_pack(build_commercial_pack(COMMERCIAL_YAML, tmp_path))
    slices = pack_functions(pack)
    fulls = {s.full_tokens for s in slices}
    assert len(fulls) == 1                 # full-pack token estimate is the same baseline for all
