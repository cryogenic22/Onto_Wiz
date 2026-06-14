"""Tests for the unified artifact contracts (ontowiz-spec)."""

from __future__ import annotations

import pytest
from ontowiz_spec import (
    ALWAYS_INCLUDED_KINDS,
    ARTIFACT_MODELS,
    AntiPattern,
    ArtifactBase,
    ArtifactKind,
    EvalCase,
    ExceptionRule,
    Lifecycle,
    MetricDefinition,
    QuestionPlaybook,
    SourceContract,
    Tag,
    TagDimension,
)


def _eval_case() -> EvalCase:
    return EvalCase(
        id="ec-1",
        name="brand-x-share-loss",
        question="Why did Brand X lose share this quarter?",
        must_contain=["access changes", "competitor activity"],
        validates=["dh-1"],
    )


def test_evalcase_defaults():
    ec = _eval_case()
    assert ec.kind == ArtifactKind.EVAL_CASE
    assert ec.lifecycle == Lifecycle.DRAFT
    assert ec.version == 1
    assert ec.layer == "base"
    assert ec.confidence == 1.0


def test_transition_is_immutable_and_audited():
    ec = _eval_case()
    active = ec.transition(
        Lifecycle.ACTIVE,
        changed_by="sme:kp",
        reason="forge round 3",
        delta_id="delta-42",
        at="2026-06-10T00:00:00Z",
    )
    # new instance advanced; original untouched
    assert active.lifecycle == Lifecycle.ACTIVE
    assert ec.lifecycle == Lifecycle.DRAFT
    # audit entry captured with the governing delta
    entry = active.lifecycle_history[-1]
    assert entry.from_state == Lifecycle.DRAFT
    assert entry.to_state == Lifecycle.ACTIVE
    assert entry.delta_id == "delta-42"
    assert entry.changed_by == "sme:kp"
    # ACTIVE stamps approved_at
    assert active.approved_at == "2026-06-10T00:00:00Z"


def test_transition_to_verified_sets_reviewer():
    ec = _eval_case()
    verified = ec.transition(Lifecycle.VERIFIED, changed_by="sme:rao", delta_id="d-verify")
    assert verified.reviewed_by == "sme:rao"
    assert verified.approved_at is None  # not active yet


def test_promotion_without_delta_id_is_refused():
    from ontowiz_spec import UngovernedTransitionError

    ec = _eval_case()
    # governed states require a delta id — the primitive refuses a direct write
    for state in (Lifecycle.ACTIVE, Lifecycle.VERIFIED):
        with pytest.raises(UngovernedTransitionError):
            ec.transition(state, changed_by="rogue")
        with pytest.raises(UngovernedTransitionError):  # blank delta id too
            ec.transition(state, changed_by="rogue", delta_id="   ")
    # ungoverned states (e.g. REVIEW) need no delta id
    assert ec.transition(Lifecycle.REVIEW, changed_by="sme").lifecycle == Lifecycle.REVIEW


def test_constructing_active_without_governed_history_is_refused():
    from ontowiz_spec import DecisionHeuristic, UngovernedTransitionError

    # the constructor / stale-YAML bypass is closed by the model validator
    with pytest.raises(UngovernedTransitionError):
        DecisionHeuristic(id="x", name="x", lifecycle=Lifecycle.ACTIVE)


def test_unsafe_artifact_id_is_rejected():
    from ontowiz_spec import DecisionHeuristic

    for bad in ["../etc", "a/b", "has space", "dot.id", "con", "NUL", "lpt1"]:
        with pytest.raises(ValueError):
            DecisionHeuristic(id=bad, name="x")


def test_to_prompt_text_includes_kind_and_name():
    text = _eval_case().to_prompt_text()
    assert "eval_case" in text
    assert "brand-x-share-loss" in text


def test_always_included_kinds_are_safety_layers():
    assert ArtifactKind.OVERRIDE_RULE in ALWAYS_INCLUDED_KINDS
    assert ArtifactKind.GUARDRAIL in ALWAYS_INCLUDED_KINDS
    assert ArtifactKind.DATA_QUIRK in ALWAYS_INCLUDED_KINDS


@pytest.mark.parametrize(
    "kind",
    [
        ArtifactKind.EVAL_CASE,
        ArtifactKind.METRIC_DEFINITION,
        ArtifactKind.SOURCE_CONTRACT,
        ArtifactKind.QUESTION_PLAYBOOK,
        ArtifactKind.ANTI_PATTERN,
        ArtifactKind.EXCEPTION_RULE,
    ],
)
def test_new_kinds_registered(kind):
    assert kind in ARTIFACT_MODELS
    assert issubclass(ARTIFACT_MODELS[kind], ArtifactBase)


def test_new_types_instantiate_with_fields():
    assert MetricDefinition(id="m1", name="trx", formula="sum(scripts)").kind == ArtifactKind.METRIC_DEFINITION
    sc = SourceContract(id="s1", name="iqvia", source="IQVIA",
                        trusted_for=["TRx"], not_trusted_for=["net price"])
    assert sc.trusted_for == ["TRx"]
    qp = QuestionPlaybook(id="q1", name="why-share", question_pattern="Why is share declining?",
                          decomposition=["market vs share", "access"])
    assert qp.decomposition[0] == "market vs share"
    ap = AntiPattern(id="a1", name="stocking", wrong_conclusion="stocking read as demand")
    assert "stocking" in ap.wrong_conclusion
    er = ExceptionRule(id="e1", name="onco-sp", applies_to_artifact_id="m1", condition="oncology SP")
    assert er.applies_to_artifact_id == "m1"


def test_tag_key():
    t = Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial")
    assert t.key() == "analytics_domain:commercial"
