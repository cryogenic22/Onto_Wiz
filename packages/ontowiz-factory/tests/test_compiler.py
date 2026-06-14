"""Loop 1 (F2-A) — pack compiler tests."""

from __future__ import annotations

from ontowiz_factory.compiler import CompiledPack, compile_pack
from ontowiz_spec import DataQuirk, Lifecycle, MetricDefinition


def _active(art):
    return art.transition(Lifecycle.ACTIVE, changed_by="curator", delta_id="d1")


def test_compile_includes_only_active_artifacts():
    dq = _active(DataQuirk(id="dq1", name="iqvia-lag", data_source="IQVIA"))
    draft = MetricDefinition(id="m1", name="trx")  # stays DRAFT
    pack = compile_pack([dq, draft], name="commercial_analytics", version="0.1.0")
    assert isinstance(pack, CompiledPack)
    assert pack.manifest.name == "commercial_analytics"
    assert pack.manifest.version == "0.1.0"
    assert pack.manifest.artifact_count == 1
    names = [s.name.lower() for s in pack.l2_doc.body]
    assert any("dq1" in n for n in names)
    assert all("m1" not in n for n in names)  # draft excluded from the pack


def test_manifest_counts_kinds():
    pack = compile_pack(
        [_active(DataQuirk(id="dq1", name="q")), _active(MetricDefinition(id="m1", name="trx"))],
        name="p", version="0.1.0",
    )
    assert pack.manifest.artifact_count == 2
    assert pack.manifest.artifact_kinds["data_quirk"] == 1
    assert pack.manifest.artifact_kinds["metric_definition"] == 1


def test_l3_directory_is_hydration_map():
    pack = compile_pack([_active(DataQuirk(id="dq1", name="iqvia-lag"))], name="p", version="0.1.0")
    assert "ctx/hydrate" in pack.l3_directory
    assert "dq1" in pack.l3_directory.lower()
    # serializable L2 context layer
    assert "dq1" in pack.l2_text().lower()


def test_empty_pack_is_valid():
    pack = compile_pack([], name="p", version="0.1.0")
    assert pack.manifest.artifact_count == 0
    assert pack.l2_doc.body == ()


def test_compiled_section_carries_knowledge_not_just_metadata():
    # the agent must actually receive the metric's content, not only its name
    m = _active(MetricDefinition(id="trx", name="Total Rx", formula="sum(scripts)"))
    pack = compile_pack([m], name="p", version="0.1.0")
    ctx = pack.l2_text()
    assert "BODY:" in ctx
    assert "sum(scripts)" in ctx  # the formula reaches the compiled context


def test_unbalanced_bracket_in_body_does_not_swallow_next_section():
    # CTX parser continues a value across lines while brackets are unbalanced — an
    # unclosed '[' in a regex/array index would eat the following section. The
    # compiler must neutralise brackets so every section survives the round-trip.
    from ontowiz_ctx.core.model import Section
    from ontowiz_ctx.core.parser import parse

    m1 = _active(MetricDefinition(id="m1", name="m1", formula="value[0 unclosed"))
    m2 = _active(MetricDefinition(id="m2", name="m2", formula="second"))
    pack = compile_pack([m1, m2], name="p", version="0.1.0")
    reparsed = parse(pack.l2_text(), level=2)
    names = {s.name for s in reparsed.body if isinstance(s, Section)}
    assert "METRIC_DEFINITION-M1" in names
    assert "METRIC_DEFINITION-M2" in names  # not swallowed


def test_field_newline_cannot_forge_a_section():
    # a value containing a section marker + newline must not create a 2nd section
    from ontowiz_ctx.core.model import Section
    from ontowiz_ctx.core.parser import parse

    m = _active(MetricDefinition(id="x", name="real\n±FAKE\nID:evil"))
    pack = compile_pack([m], name="p", version="0.1.0")
    reparsed = parse(pack.l2_text(), level=2)
    sections = [e for e in reparsed.body if isinstance(e, Section)]
    assert len(sections) == 1  # the forged ±FAKE never becomes its own section
    assert "FAKE" not in sections[0].name
