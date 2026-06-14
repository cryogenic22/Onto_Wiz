"""Tests for the ported artifact library (SpecOmagic 10 + judgment 3)."""

from __future__ import annotations

import yaml
from ontowiz_spec import (
    ARTIFACT_MODELS,
    ActionTemplate,
    ArtifactBase,
    ArtifactKind,
    DataQuirk,
    DecisionHeuristic,
    EntityRecord,
    EntityRegistry,
    FewShotExample,
    FewShotLibrary,
    FunctionAction,
    Guardrail,
    HeuristicAntiPattern,
    InstructionSet,
    JargonEntry,
    JargonMap,
    JudgmentPattern,
    Lifecycle,
    OverrideRule,
    PlaybookStep,
    ProcessPlaybook,
    PromptTemplate,
    Rule,
    Tag,
    TagDimension,
    Taxonomy,
    TaxonomyNode,
    TriggerCondition,
)

# ── registry completeness (DoD: all 19 kinds registered) ────────────────────


def test_registry_covers_every_kind():
    assert set(ARTIFACT_MODELS) == set(ArtifactKind), (
        "ARTIFACT_MODELS missing kinds: "
        f"{set(ArtifactKind) - set(ARTIFACT_MODELS)}"
    )
    assert len(ARTIFACT_MODELS) == 19
    for kind, model in ARTIFACT_MODELS.items():
        assert issubclass(model, ArtifactBase)
        # the registered model's default kind matches its registry key
        assert model(id="x", name="x", **_required(kind)).kind == kind


def _required(kind: ArtifactKind) -> dict:
    """Minimal required fields for kinds whose base has non-defaulted extras."""
    if kind == ArtifactKind.EVAL_CASE:
        return {"question": "q"}
    if kind == ArtifactKind.SOURCE_CONTRACT:
        return {"source": "IQVIA"}
    return {}


# ── inherited governance works on ported types ──────────────────────────────


def test_ported_type_inherits_lifecycle_and_transition():
    is_ = InstructionSet(id="i1", name="brand-diag", context="diagnose share")
    assert is_.lifecycle == Lifecycle.DRAFT
    active = is_.transition(Lifecycle.ACTIVE, changed_by="sme:kp", delta_id="d1")
    assert active.lifecycle == Lifecycle.ACTIVE
    assert active.lifecycle_history[-1].delta_id == "d1"


# ── behaviour: SpecOmagic renderers/helpers reused faithfully ────────────────


def test_instruction_set_rules_by_priority_and_render():
    is_ = InstructionSet(
        id="i1", name="diag",
        rules=[Rule(id="r2", rule="check access", priority=2),
               Rule(id="r1", rule="decompose share", priority=1)],
    )
    assert [r.id for r in is_.rules_by_priority()] == ["r1", "r2"]
    text = is_.to_prompt_text()
    assert "decompose share" in text and "[P1]" in text


def test_taxonomy_paths_and_find_node():
    tx = Taxonomy(id="t1", name="channels",
                  tree=[TaxonomyNode(name="retail", children=[TaxonomyNode(name="independent")])])
    assert "retail > independent" in tx.all_paths()
    assert tx.find_node("independent") is not None
    assert tx.find_node("missing") is None


def test_jargon_resolve_and_lookup():
    jm = JargonMap(id="j1", name="terms",
                   entries=[JargonEntry(canonical="pull-through", synonyms=["pullthrough", "PT"])])
    assert jm.resolve("PT") == "pull-through"
    assert jm.resolve("unknown") is None
    assert jm.lookup("pullthrough").canonical == "pull-through"
    assert jm.lookup("unknown") is None


def test_entity_registry_resolution():
    er = EntityRegistry(id="e1", name="reg",
                        entities=[EntityRecord(id="d1", entity_type="drug", name="Keytruda",
                                               aliases=["pembrolizumab"])])
    assert er.resolve_name("pembrolizumab").id == "d1"
    assert er.get_by_type("drug")[0].name == "Keytruda"
    assert er.get_by_id("nope") is None


def test_override_rule_matches_tags():
    onc = Tag(dimension=TagDimension.THERAPY_AREA, value="oncology")
    other = Tag(dimension=TagDimension.THERAPY_AREA, value="cardiology")
    rule = OverrideRule(id="o1", name="onco-rule", rule="use IQVIA only", trigger_tags=[onc])
    assert rule.matches([onc]) is True
    assert rule.matches([other]) is False
    assert OverrideRule(id="o2", name="always").matches([]) is True  # no trigger = always


def test_prompt_template_render_and_missing():
    pt = PromptTemplate(id="p1", name="q", template="share of {brand} in {ind}",
                        defaults={"ind": "NSCLC"})
    assert pt.render(brand="Keytruda") == "share of Keytruda in NSCLC"
    assert "Missing placeholder" in pt.render()  # brand missing, no default


def test_decision_heuristic_confidence_bounds_and_render():
    dh = DecisionHeuristic(
        id="dh1", name="pa-escalation", decision_logic="if PA reject > 30%, escalate to MSL",
        trigger_signals=[TriggerCondition(signal_name="pa_reject_rate", threshold=">0.30")],
        anti_patterns=[HeuristicAntiPattern(wrong_conclusion="demand drop", why_wrong="it's access")],
        confidence=0.8,
    )
    assert dh.confidence == 0.8
    text = dh.to_prompt_text()
    assert "escalate to MSL" in text and "WRONG: demand drop" in text


def test_process_playbook_orders_steps():
    pb = ProcessPlaybook(id="pb1", name="share-decomp",
                         steps=[PlaybookStep(order=2, action="check access"),
                                PlaybookStep(order=1, action="split market vs share")])
    text = pb.to_prompt_text()
    assert text.index("split market vs share") < text.index("check access")


def test_data_quirk_render():
    dq = DataQuirk(id="dq1", name="iqvia-lag", data_source="IQVIA",
                   quirk_description="claims lag ~6 weeks", impact_severity="high",
                   affects_metrics=["TRx"])
    assert "SEVERITY".lower() in dq.to_prompt_text().lower()
    assert "TRx" in dq.to_prompt_text()


def test_judgment_pattern_render():
    from ontowiz_spec import DriverAttribution
    jp = JudgmentPattern(id="jp1", name="share-loss",
                         applies_when_signals=["trx_down"],
                         typical_drivers=[DriverAttribution(driver="access", prior_confidence=0.6)])
    assert "trx_down" in jp.to_prompt_text()
    assert jp.judgment_type == "causal_hypothesis"


def test_guardrail_render_is_safety_layer():
    g = Guardrail(id="g1", name="no-promo", blocks_drivers=["off-label uplift"],
                  unless_evidence=["approved label"])
    assert g.kind in __import__("ontowiz_spec").ALWAYS_INCLUDED_KINDS
    assert "DO NOT conclude" in g.to_prompt_text()


def test_action_template_function_routing():
    at = ActionTemplate(id="at1", name="share-recovery", trigger_pattern_id="jp1",
                        brand_actions=[FunctionAction(action="reprice", priority="high")])
    assert at.get_actions_for_function("brand")[0].action == "reprice"
    assert at.get_actions_for_function("field") == []
    assert "reprice" in at.to_prompt_text()


# ── YAML round-trip for every kind (DoD) ────────────────────────────────────


def test_yaml_roundtrip_every_kind():
    samples = _one_of_each()
    assert set(samples) == set(ArtifactKind)
    for kind, art in samples.items():
        dumped = art.model_dump(mode="json")
        reloaded = ARTIFACT_MODELS[kind].model_validate(yaml.safe_load(yaml.safe_dump(dumped)))
        assert reloaded.kind == kind
        assert reloaded.model_dump(mode="json") == dumped


def _one_of_each() -> dict[ArtifactKind, ArtifactBase]:
    base = {"id": "x", "name": "x"}
    return {
        ArtifactKind.INSTRUCTION_SET: InstructionSet(**base),
        ArtifactKind.TAXONOMY: Taxonomy(**base),
        ArtifactKind.JARGON_MAP: JargonMap(**base),
        ArtifactKind.ENTITY_REGISTRY: EntityRegistry(**base),
        ArtifactKind.FEWSHOT_LIBRARY: FewShotLibrary(
            **base, examples=[FewShotExample(input="a", output="b")]),
        ArtifactKind.OVERRIDE_RULE: OverrideRule(**base, rule="r"),
        ArtifactKind.PROMPT_TEMPLATE: PromptTemplate(**base, template="t"),
        ArtifactKind.DECISION_HEURISTIC: DecisionHeuristic(**base),
        ArtifactKind.DATA_QUIRK: DataQuirk(**base),
        ArtifactKind.PROCESS_PLAYBOOK: ProcessPlaybook(**base),
        ArtifactKind.JUDGMENT_PATTERN: JudgmentPattern(**base),
        ArtifactKind.GUARDRAIL: Guardrail(**base),
        ArtifactKind.ACTION_TEMPLATE: ActionTemplate(**base),
        ArtifactKind.EVAL_CASE: _eval(),
        ArtifactKind.METRIC_DEFINITION: _metric(),
        ArtifactKind.SOURCE_CONTRACT: _source(),
        ArtifactKind.QUESTION_PLAYBOOK: _question(),
        ArtifactKind.ANTI_PATTERN: _anti(),
        ArtifactKind.EXCEPTION_RULE: _exception(),
    }


def _eval():
    from ontowiz_spec import EvalCase
    return EvalCase(id="x", name="x", question="q")


def _metric():
    from ontowiz_spec import MetricDefinition
    return MetricDefinition(id="x", name="x")


def _source():
    from ontowiz_spec import SourceContract
    return SourceContract(id="x", name="x", source="IQVIA")


def _question():
    from ontowiz_spec import QuestionPlaybook
    return QuestionPlaybook(id="x", name="x")


def _anti():
    from ontowiz_spec import AntiPattern
    return AntiPattern(id="x", name="x")


def _exception():
    from ontowiz_spec import ExceptionRule
    return ExceptionRule(id="x", name="x")


# ── fully-populated renderers (cover the optional to_prompt_text branches) ───


def test_instruction_set_full_render():
    is_ = InstructionSet(
        id="i", name="diag", context="ctx",
        rules=[Rule(id="r", rule="do x", condition="when y")],
        output_format={"slide": "1-pager"}, warnings=["mind the lag"],
    )
    text = is_.to_prompt_text()
    assert "Output Format" in text and "Warnings" in text and "when y" in text


def test_jargon_full_render():
    jm = JargonMap(id="j", name="t", entries=[
        JargonEntry(canonical="PT", synonyms=["pull-through"], definition="scripts converted",
                    not_to_be_confused_with=["TRx"])])
    text = jm.to_prompt_text()
    assert "NOT to be confused with: TRx" in text and "scripts converted" in text


def test_entity_registry_full_render():
    er = EntityRegistry(id="e", name="r", entities=[
        EntityRecord(id="d", entity_type="drug", name="Keytruda", aliases=["pembro"],
                     attributes={"class": "IO"})])
    text = er.to_prompt_text()
    assert "aka pembro" in text and "class: IO" in text


def test_fewshot_render():
    fs = FewShotLibrary(id="f", name="ex", examples=[FewShotExample(input="in", output="out")])
    assert "Input:** in" in fs.to_prompt_text()


def test_override_render_with_reason():
    o = OverrideRule(id="o", name="r", rule="use IQVIA only", reason="client mandate")
    assert "Reason: client mandate" in o.to_prompt_text()


def test_decision_heuristic_full_render():
    dh = DecisionHeuristic(
        id="dh", name="h", decision_logic="if A then B", trigger_context=["launch"],
        exceptions=["except onco"], evidence_required=["PA data"],
        typical_outcome="MSL engaged", recommended_actions=["call MSL"],
    )
    text = dh.to_prompt_text()
    for needle in ("Context:** launch", "Exceptions", "Required Evidence",
                   "Typical Outcome:** MSL engaged", "Recommended Actions"):
        assert needle in text


def test_data_quirk_full_render():
    dq = DataQuirk(id="dq", name="q", data_source="IQVIA", quirk_description="lag",
                   workaround="wait 6w", cross_reference="867", seasonal=True,
                   seasonal_pattern="Q4 dip", validation_query="SELECT 1")
    text = dq.to_prompt_text()
    for needle in ("Workaround:** wait 6w", "Cross-Reference:** 867",
                   "Seasonal Pattern:** Q4 dip", "Validation Query"):
        assert needle in text


def test_process_playbook_full_render():
    pb = ProcessPlaybook(
        id="pb", name="p", description="desc", task_type="diag",
        prerequisites=["data ready"], required_data_sources=["IQVIA"], required_tools=["SQL"],
        steps=[PlaybookStep(order=1, action="split", inputs=["trx"], outputs=["share"],
                            quality_check="sums to 100", decision_point="branch?",
                            common_mistake="ignore lag", tools=["pandas"], estimated_minutes=10)],
        estimated_total_minutes=30, common_pitfalls=["stocking"], quality_criteria=["decomposed"],
    )
    text = pb.to_prompt_text()
    for needle in ("Prerequisites", "Data Sources:** IQVIA", "Tools:** SQL", "Inputs: trx",
                   "Outputs: share", "Quality Check: sums to 100", "Decision: branch?",
                   "WARNING: ignore lag", "Tools: pandas", "Est. Time: 10 min",
                   "Total Estimated Time:** 30 min", "Common Pitfalls", "Quality Criteria"):
        assert needle in text


def test_judgment_pattern_full_render():
    from ontowiz_spec import DriverAttribution
    jp = JudgmentPattern(id="jp", name="p", applies_when_signals=["s"],
                         applies_when_context=["launch"],
                         typical_drivers=[DriverAttribution(driver="access", evidence_required=["PA"])],
                         disallowed_drivers=["weather"])
    text = jp.to_prompt_text()
    assert "Context:** launch" in text and "needs: PA" in text and "Disallowed Drivers:** weather" in text


def test_guardrail_full_render():
    g = Guardrail(id="g", name="g", blocks_action_types=["promo"], blocks_drivers=["off-label"],
                  unless_evidence=["label"], unless_approver_role=["compliance"])
    text = g.to_prompt_text()
    assert "DO NOT take actions:** promo" in text and "approved by: compliance" in text


def test_action_template_full_render():
    at = ActionTemplate(
        id="at", name="a", trigger_pattern_id="jp",
        field_actions=[FunctionAction(action="detail", priority="high", conditions=["high decile"])],
        access_actions=[FunctionAction(action="payer mtg")],
        medical_actions=[FunctionAction(action="MSL")],
        expected_impact_metric="TRx", expected_impact_timeframe="Q3",
    )
    text = at.to_prompt_text()
    assert "Field" in text and "if high decile" in text and "Expected impact:** TRx" in text
