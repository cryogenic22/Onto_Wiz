"""Loop 9 (F4-C) — eval loop tests."""

from __future__ import annotations

from ontowiz_factory.evals import agent_lift, gate, run_suite, score_answer
from ontowiz_spec import EvalCase


def _case() -> EvalCase:
    return EvalCase(
        id="ec1", name="share", question="why did Brand X lose share?",
        must_contain=["access", "competitor"], must_not_contain=["stocking"],
    )


def test_score_pass_fail_and_forbidden():
    c = _case()
    assert score_answer(c, "access changes and competitor activity").passed
    miss = score_answer(c, "just access")
    assert not miss.passed and "competitor" in miss.missing
    forb = score_answer(c, "access competitor but it's a stocking effect")
    assert not forb.passed and "stocking" in forb.forbidden_hits


def test_run_suite_and_gate():
    cases = [_case(), _case()]
    good = run_suite(cases, lambda c: "access competitor")
    assert good.pass_rate == 1.0 and gate(good)
    bad = run_suite(cases, lambda c: "nothing useful")
    assert bad.pass_rate == 0.0 and not gate(bad)


def test_agent_lift_positive_when_pack_helps():
    cases = [_case()]
    lift = agent_lift(
        cases,
        with_pack_fn=lambda c: "access and competitor",
        without_pack_fn=lambda c: "access only",
    )
    assert lift > 0


def test_gate_blocks_a_pack_with_no_lift():
    # a pack that passes its evals but adds zero lift must NOT promote when gated on lift
    summary = run_suite([_case()], lambda c: "access competitor")
    assert summary.pass_rate == 1.0
    assert gate(summary)  # pass-rate only → ships
    assert not gate(summary, lift=0.0, min_lift=0.05)  # lift-gated → blocked
    assert gate(summary, lift=0.2, min_lift=0.05)  # real lift → ships


def test_score_word_boundary_avoids_false_positive():
    c = EvalCase(id="e", name="n", question="q", must_contain=["access"])
    assert not score_answer(c, "this accessory is unrelated").passed  # 'access' ⊄ 'accessory'
    assert score_answer(c, "market access matters").passed


def test_empty_case_does_not_pass_vacuously():
    c = EvalCase(id="e", name="n", question="q")  # no must_contain / must_not_contain
    r = score_answer(c, "anything at all")
    assert not r.passed and r.score == 0.0
