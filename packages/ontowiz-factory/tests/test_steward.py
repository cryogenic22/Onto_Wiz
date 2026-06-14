"""Loop 8 (F4-B) — steward loop tests."""

from __future__ import annotations

from ontowiz_factory.steward import collect_signals, pack_quality_score, signals_to_missions
from ontowiz_spec import DecisionHeuristic, Lifecycle


def _a(aid: str, conf: float, active: bool = True) -> DecisionHeuristic:
    h = DecisionHeuristic(id=aid, name=aid, confidence=conf)
    return h.transition(Lifecycle.ACTIVE, changed_by="c", delta_id="d") if active else h


def test_low_confidence_signal():
    sigs = collect_signals([_a("a", 0.3), _a("b", 0.9)])
    low = [s for s in sigs if s.kind == "low_confidence"]
    assert any(s.artifact_id == "a" for s in low)
    assert not any(s.kind == "low_confidence" and s.artifact_id == "b" for s in sigs)


def test_missing_eval_signal_clears_when_covered():
    assert any(s.kind == "missing_eval" for s in collect_signals([_a("a", 0.9)]))
    assert not any(s.kind == "missing_eval" for s in collect_signals([_a("a", 0.9)], eval_targets={"a"}))


def test_signals_ranked_by_impact_and_become_missions():
    sigs = collect_signals([_a("a", 0.1), _a("b", 0.45)])
    impacts = [s.impact for s in sigs]
    assert impacts == sorted(impacts, reverse=True)
    missions = signals_to_missions(sigs, limit=3)
    assert 1 <= len(missions) <= 3
    assert all(m.artifact_id and m.prompt for m in missions)


def test_pack_quality_score_bounds():
    arts = [_a("a", 0.8), _a("b", 0.9)]
    assert 0.0 <= pack_quality_score(arts, eval_targets={"a", "b"}) <= 1.0
    # full coverage + high confidence + all active should beat low coverage
    high = pack_quality_score(arts, eval_targets={"a", "b"})
    low = pack_quality_score(arts, eval_targets=set())
    assert high > low
    assert pack_quality_score([]) == 0.0
