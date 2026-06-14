"""Loop 5 / UX-1 (F5-A) — mission framework: daily feed + submit contract.

The Forge spec's core rule: a mission that doesn't produce an artifact *and* an
eval doesn't ship. These tests pin the submit contract (delta + eval + confidence)
and the steward-ranked daily feed (the 5-minute loop).
"""

from __future__ import annotations

import pytest
from ontowiz_core import DeltaStatus
from ontowiz_factory.missions import (
    MissionContractError,
    MissionSubmission,
    daily_missions,
    submit_mission,
)
from ontowiz_spec import ArtifactKind, DecisionHeuristic, Lifecycle


def _a(aid: str, conf: float, active: bool = True) -> DecisionHeuristic:
    h = DecisionHeuristic(id=aid, name=aid, confidence=conf)
    return h.transition(Lifecycle.ACTIVE, changed_by="c", delta_id="d") if active else h


# ---- daily feed (reuses steward) -------------------------------------------


def test_daily_feed_is_steward_ranked_and_capped():
    arts = [_a("a", 0.1), _a("b", 0.45), _a("c", 0.95)]
    missions = daily_missions(arts, limit=5)
    assert 1 <= len(missions) <= 5
    # ranked by impact, highest first
    impacts = [m.impact for m in missions]
    assert impacts == sorted(impacts, reverse=True)
    # the lowest-confidence artifact ("a", 0.1) must surface as the top mission
    assert missions[0].artifact_id == "a"
    assert all(m.artifact_id and m.prompt and m.type for m in missions)


def test_daily_feed_empty_is_safe():
    assert daily_missions([]) == []


def test_daily_feed_respects_limit():
    arts = [_a(f"x{i}", 0.1) for i in range(10)]
    assert len(daily_missions(arts, limit=3)) <= 3


# ---- submit contract: delta + eval + confidence ----------------------------


def test_submit_produces_delta_eval_and_confidence():
    sub = MissionSubmission(
        mission_type="validate",
        artifact=DecisionHeuristic(id="new-1", name="share loss = access"),
        confidence=0.8,
        gold_answer="loss driven by formulary access, not demand",
        question="why are we losing share?",
    )
    res = submit_mission(sub)
    assert res.delta.status == DeltaStatus.PROPOSED
    assert res.confidence == 0.8
    assert res.eval_case.kind == ArtifactKind.EVAL_CASE
    assert res.eval_case.validates == ["new-1"]
    assert "loss driven by formulary access, not demand" in res.eval_case.must_contain


def test_submit_without_eval_material_is_rejected():
    sub = MissionSubmission(
        mission_type="validate",
        artifact=DecisionHeuristic(id="new-2", name="x"),
        confidence=0.7,
    )
    with pytest.raises(MissionContractError):
        submit_mission(sub)


def test_submit_with_bad_confidence_is_rejected():
    sub = MissionSubmission(
        mission_type="validate",
        artifact=DecisionHeuristic(id="new-3", name="x"),
        confidence=1.5,
        gold_answer="something",
    )
    with pytest.raises(MissionContractError):
        submit_mission(sub)


def test_submit_rejects_existing_artifact_id_mismatch():
    existing = _a("ex-1", 0.6)
    sub = MissionSubmission(
        mission_type="correct",
        artifact=DecisionHeuristic(id="different", name="x"),
        confidence=0.8,
        correction="fix",
    )
    with pytest.raises(MissionContractError):
        submit_mission(sub, existing=existing)


def test_submit_against_existing_artifact_proposes_review_transition():
    existing = _a("ex-1", 0.6)
    sub = MissionSubmission(
        mission_type="correct",
        artifact=existing,
        confidence=0.9,
        correction="it's access not demand",
        question="why share loss?",
    )
    res = submit_mission(sub, existing=existing)
    assert res.delta.status == DeltaStatus.PROPOSED
    assert res.delta.content["to"] == Lifecycle.REVIEW.value
    assert res.eval_case.validates == ["ex-1"]
