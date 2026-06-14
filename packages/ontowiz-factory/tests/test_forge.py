"""Loop 5 / UX-4 (F5-D) — ForgeRating + multiplayer consensus.

ForgeRating is a calibrated judgement score (Elo-like), computed not awarded,
moving on five signals (dissent weighted highest) — never on volume/speed.
Multiplayer consensus settles SME disagreement into a consensus + dissent +
confidence, and manufactures an ExceptionRule capturing the situated judgement.

Tier B (factory).
"""

from __future__ import annotations

from ontowiz_factory.forge import (
    Contribution,
    SMEAnswer,
    consensus_to_exception_rule,
    forge_rating,
    resolve_consensus,
)
from ontowiz_spec import ArtifactKind

# ---- ForgeRating ------------------------------------------------------------


def test_dissent_is_weighted_highest():
    from ontowiz_factory.forge import SIGNAL_WEIGHTS

    # dissent must carry the single highest weight, strictly above every other
    assert max(SIGNAL_WEIGHTS, key=lambda k: SIGNAL_WEIGHTS[k]) == "dissent_value"
    others = [v for k, v in SIGNAL_WEIGHTS.items() if k != "dissent_value"]
    assert SIGNAL_WEIGHTS["dissent_value"] > max(others)
    # and a pure-dissent contribution must out-rate a pure-anything-else one
    def only(signal):
        return forge_rating([Contribution("a", "x", **{signal: 1.0})])
    assert only("dissent_value") > max(
        only("correctness"), only("novelty"), only("impact"), only("eval_value")
    )


def test_rating_ignores_zero_weight_gaming_clicks():
    real = Contribution(sme_id="a", artifact_id="x", correctness=0.9, eval_value=0.8)
    # a maximally-different weight-0 click: if weight were ignored it would move
    # the rating a lot; honoured at weight 0 it must change nothing.
    spam = Contribution(
        sme_id="a", artifact_id="x", correctness=1.0, novelty=1.0, impact=1.0,
        eval_value=1.0, dissent_value=1.0, weight=0.0,
    )
    assert forge_rating([real, spam]) == forge_rating([real])


def test_rating_clamps_out_of_range_signals():
    # an un-normalised signal (e.g. raw usage as impact) cannot escape [1000,2000]
    huge = Contribution(sme_id="a", artifact_id="x", impact=999.0)
    capped = Contribution(sme_id="a", artifact_id="x", impact=1.0)
    assert forge_rating([huge]) == forge_rating([capped]) <= 2000.0
    assert forge_rating([Contribution("a", "x", correctness=-5.0)]) == 1000.0


def test_rating_is_a_nonneg_number_and_empty_is_baseline():
    assert forge_rating([]) == 1000.0  # Elo-like baseline
    r = forge_rating([Contribution(sme_id="a", artifact_id="x", correctness=1.0)])
    assert r >= 1000.0


# ---- Multiplayer consensus --------------------------------------------------


def test_consensus_picks_majority_and_flags_dissent():
    answers = [
        SMEAnswer("a", "payer access", 0.9),
        SMEAnswer("b", "payer access", 0.8),
        SMEAnswer("c", "channel execution", 0.6),
    ]
    res = resolve_consensus(answers)
    assert res.consensus == "payer access"
    assert 0.0 < res.agreement < 1.0
    assert "channel execution" in res.dissent
    assert 0.0 < res.confidence <= 1.0


def test_consensus_empty_is_safe():
    res = resolve_consensus([])
    assert res.consensus == "" and res.agreement == 0.0 and res.confidence == 0.0
    assert res.dissent == []


def test_consensus_becomes_an_exception_rule():
    res = resolve_consensus([SMEAnswer("a", "stocking, not demand", 0.9)])
    rule = consensus_to_exception_rule(
        res, rule_id="exr-1", name="Q4 stocking exception",
        applies_to="dh-share", condition="Q4 wholesaler buy-in",
    )
    assert rule.kind == ArtifactKind.EXCEPTION_RULE
    assert rule.applies_to_artifact_id == "dh-share"
    assert rule.instead == "stocking, not demand"
    assert rule.confidence == res.confidence
