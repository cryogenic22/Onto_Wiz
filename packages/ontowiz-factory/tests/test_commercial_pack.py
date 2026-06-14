"""Loop 3 (F2-C) — compile the first real pack from ontology/commercial.yaml."""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.seed import artifacts_from_commercial, build_commercial_pack
from ontowiz_runtime.registry import load_pack
from ontowiz_spec import ArtifactKind, EntityRegistry, Lifecycle

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"


def test_commercial_yaml_present():
    assert COMMERCIAL_YAML.is_file(), f"missing {COMMERCIAL_YAML}"


def test_artifacts_from_commercial():
    arts = artifacts_from_commercial(COMMERCIAL_YAML)
    kinds = {a.kind for a in arts}
    assert ArtifactKind.ENTITY_REGISTRY in kinds
    assert ArtifactKind.DECISION_HEURISTIC in kinds
    er = next(a for a in arts if isinstance(a, EntityRegistry))
    assert any(e.name == "Brand" for e in er.entities)
    # heuristics come from the inference rules
    heuristics = [a for a in arts if a.kind == ArtifactKind.DECISION_HEURISTIC]
    assert len(heuristics) >= 3
    assert all(h.decision_logic for h in heuristics)
    # L2: the rule's disambiguating `description` is no longer dropped — it now
    # rides into the heuristic content (trigger_context), so it reaches the BODY.
    by_id = {h.id: h for h in heuristics}
    assert any(h.trigger_context for h in heuristics)
    assert by_id["rule_pathway_exclusion"].trigger_context
    # L3: overlapping heuristics carry an explicit anti-pattern (what they are NOT)
    pathway = by_id["rule_pathway_exclusion"]
    assert pathway.anti_patterns
    assert any("guideline" in ap.why_wrong.lower() for ap in pathway.anti_patterns)
    # L4: the rule's trigger conditions + priority are no longer dropped
    assert pathway.trigger_signals
    assert pathway.scope.get("priority")
    # L5: the ontology's entity relationships ride into the registry (were dropped)
    brand = next(e for e in er.entities if e.name == "Brand")
    assert brand.relationships
    assert any(r.get("target") for r in brand.relationships)


def test_build_and_load_commercial_pack(tmp_path):
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    loaded = load_pack(pack_dir)
    assert loaded.manifest.name == "commercial_analytics"
    assert loaded.manifest.version == "0.1.0"
    assert loaded.manifest.artifact_count >= 5
    assert loaded.manifest.artifact_kinds.get("decision_heuristic", 0) >= 3
    # everything in a pack is ACTIVE (governance enforced at compile)
    assert all(a.lifecycle == Lifecycle.ACTIVE for a in loaded.artifacts)
    # and every ACTIVE artifact carries a governing delta_id — even seeds go
    # through the bridge (no ungoverned promotion ships in a pack)
    assert all(a.lifecycle_history[-1].delta_id for a in loaded.artifacts)
    # the CTX context layer round-tripped
    assert loaded.l2_doc.body
