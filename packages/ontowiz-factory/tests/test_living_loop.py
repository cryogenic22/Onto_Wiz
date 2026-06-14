"""End-to-end living loop — the MVP that ties the factory together.

Proves the closing weld: a gap in a served pack becomes an SME mission, the
governed addition is carried into the *next* pack version, and the new version
serves knowledge the old one could not. No network — the LLM consumer is tested
separately (test_consume.py); here we prove the governance/compile cycle closes.

    v0.1.0 (no cyber heuristic)  → SME mission (submit_mission add-Delta)
        → evolve_pack → v0.2.0  → get_context serves the new artifact
"""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.compiler import verify_pack, write_pack
from ontowiz_factory.missions import MissionSubmission, submit_mission
from ontowiz_factory.orchestrate import evolve_pack
from ontowiz_runtime.context import context_for_pack
from ontowiz_runtime.registry import PackRegistry, load_pack
from ontowiz_spec import ArtifactKind, DecisionHeuristic, Lifecycle, Tag, TagDimension

PACK_DIR = Path(__file__).resolve().parents[3] / "packs" / "commercial_analytics" / "0.1.0"
_TAG = Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial")
_GAP_QUERY = "Volume collapsed after a cyberattack took our distributor's systems offline. Why?"


def _new_heuristic() -> DecisionHeuristic:
    return DecisionHeuristic(
        id="rule_cyber_disruption",
        name="Cyber Disruption",
        decision_logic="cyberattack on distributor IT => fulfillment outage => volume drop",
        typical_outcome="Cyberattack-driven distribution outage: an IT incident at the "
        "distributor halted fulfillment — a supply-side outage, not demand or access.",
        trigger_context=["A cyber/IT incident at a distributor can masquerade as a demand drop."],
        confidence=0.8,
        tags=[_TAG],
    )


def _mission_add_delta():
    sub = MissionSubmission(
        mission_type="add",
        artifact=_new_heuristic(),
        confidence=0.8,
        gold_answer="cyberattack distribution outage",
        question=_GAP_QUERY,
        submitted_by="sme",
    )
    return submit_mission(sub)  # existing=None → a PROPOSED add-Delta


def test_evolve_pack_governs_and_compiles_the_addition():
    base = load_pack(PACK_DIR).artifacts
    result = _mission_add_delta()
    evolved = evolve_pack(
        base, [result.delta], name="commercial_analytics", version="0.2.0"
    )
    new = next(a for a in evolved.artifacts if a.id == "rule_cyber_disruption")
    # the addition is governed: ACTIVE with a real backing delta_id
    assert new.lifecycle == Lifecycle.ACTIVE
    assert new.lifecycle_history[-1].delta_id
    # and it joined the existing pack, not replaced it
    assert len(evolved.artifacts) == len(base) + 1


def test_v2_serves_what_v1_could_not(tmp_path):
    base = load_pack(PACK_DIR).artifacts
    # v1 has no cyber heuristic
    assert all(a.id != "rule_cyber_disruption" for a in base)

    result = _mission_add_delta()
    evolved = evolve_pack(base, [result.delta], name="commercial_analytics", version="0.2.0")
    write_pack(evolved, tmp_path)

    reg = PackRegistry(tmp_path)
    v2 = reg.load("commercial_analytics", "0.2.0")
    assert verify_pack(tmp_path / "commercial_analytics" / "0.2.0")  # sealed

    # the new version serves the previously-missing knowledge
    ctx = context_for_pack(_GAP_QUERY, v2)
    served_ids = {a.id for a in ctx.eligible}
    assert "rule_cyber_disruption" in served_ids
    assert any(a.kind == ArtifactKind.DECISION_HEURISTIC for a in v2.artifacts)
