"""Loop 10 (F4-D) — feedback loop tests."""

from __future__ import annotations

from ontowiz_core import DeltaStatus
from ontowiz_factory.feedback import (
    UsageEvent,
    correction_to_evalcase,
    feedback_to_deltas,
    update_reliability,
)
from ontowiz_spec import ArtifactKind, DecisionHeuristic, Lifecycle


def test_ewma_reliability_moves_with_usage():
    rel = update_reliability({}, [UsageEvent("a", True), UsageEvent("a", True), UsageEvent("b", False)])
    assert rel["a"] > 0.5
    assert rel["b"] < 0.5


def test_correction_becomes_evalcase():
    ec = correction_to_evalcase(
        UsageEvent("a", helpful=False, correction="it's access not demand", query="why share loss?")
    )
    assert ec.kind == ArtifactKind.EVAL_CASE
    assert ec.validates == ["a"]
    assert ec.must_contain == ["it's access not demand"]


def test_correction_proposes_review_delta():
    a = DecisionHeuristic(id="a", name="a").transition(Lifecycle.ACTIVE, changed_by="c", delta_id="d")
    deltas = feedback_to_deltas([UsageEvent("a", helpful=False, correction="fix it")], {"a": a})
    assert deltas
    assert deltas[0].status == DeltaStatus.PROPOSED
    assert deltas[0].content["to"] == "review"
    # a helpful event with no correction proposes nothing
    assert feedback_to_deltas([UsageEvent("a", helpful=True)], {"a": a}) == []
