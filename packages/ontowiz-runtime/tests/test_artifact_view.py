"""C4 — single-artifact detail view: knowledge + provenance + governance + YAML."""

from __future__ import annotations

from pathlib import Path

import pytest
from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import artifact_view, load_pack

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"


def test_artifact_view_surfaces_knowledge_and_governance(tmp_path):
    pack = load_pack(build_commercial_pack(COMMERCIAL_YAML, tmp_path))
    v = artifact_view(pack, "rule_pathway_exclusion")

    assert v.id == "rule_pathway_exclusion"
    assert v.served is True
    assert v.function == "market_access"
    assert v.therapy == "oncology"
    # the disambiguating anti-pattern is surfaced
    assert v.anti_patterns and any("guideline" in ap["why_wrong"].lower() for ap in v.anti_patterns)
    # every served artifact carries a governing delta in its history
    assert v.governance and v.governance[-1]["delta_id"]
    assert v.governance[-1]["to_state"] == "active"
    # raw YAML is browsable and carries the function tag
    assert "rule_pathway_exclusion" in v.yaml
    assert "market_access" in v.yaml


def test_artifact_view_missing_raises_keyerror(tmp_path):
    pack = load_pack(build_commercial_pack(COMMERCIAL_YAML, tmp_path))
    with pytest.raises(KeyError):
        artifact_view(pack, "rule_does_not_exist")
