"""Tests for the runtime context pipeline (governance gate + CTX directory)."""

from __future__ import annotations

from ontowiz_ctx.core.model import CTXDocument, Header, KeyValue, Layer, Section
from ontowiz_runtime import gate, get_context
from ontowiz_spec import ArtifactKind, EvalCase, Lifecycle, Tag, TagDimension


def _doc() -> CTXDocument:
    return CTXDocument(
        header=Header(magic="§CTX", version="1.0", layer=Layer.L2),
        body=(
            Section(name="ENTITY-BRAND-X",
                    children=(KeyValue(key="IDENTIFIER", value="BRX"),)),
            Section(name="METRIC-MARKET-SHARE",
                    children=(KeyValue(key="FORMULA", value="brand TRx / market TRx"),)),
        ),
    )


def _artifact(id_: str, state: Lifecycle, domain: str = "commercial") -> EvalCase:
    ec = EvalCase(
        id=id_, name=id_, question="q",
        tags=[Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value=domain)],
    )
    if state == Lifecycle.DRAFT:
        return ec
    # governed states must be reached via a delta-bearing transition
    delta = "d" if state in (Lifecycle.ACTIVE, Lifecycle.VERIFIED) else None
    return ec.transition(state, changed_by="c", delta_id=delta)


COMMERCIAL = [Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial")]


def test_gate_excludes_non_active_in_production():
    arts = [_artifact("a", Lifecycle.ACTIVE), _artifact("d", Lifecycle.DRAFT),
            _artifact("r", Lifecycle.REVIEW)]
    eligible = gate(arts)
    assert [a.id for a in eligible] == ["a"]


def test_gate_dev_mode_admits_review_and_verified_but_not_draft():
    arts = [_artifact("a", Lifecycle.ACTIVE), _artifact("v", Lifecycle.VERIFIED),
            _artifact("r", Lifecycle.REVIEW), _artifact("d", Lifecycle.DRAFT)]
    eligible = {a.id for a in gate(arts, dev_mode=True)}
    assert eligible == {"a", "v", "r"}
    assert "d" not in eligible


def test_gate_tag_relevance_filters_out_of_domain():
    arts = [_artifact("c", Lifecycle.ACTIVE, domain="commercial"),
            _artifact("x", Lifecycle.ACTIVE, domain="manufacturing")]
    eligible = gate(arts, tags=COMMERCIAL)
    assert [a.id for a in eligible] == ["c"]


def test_get_context_gates_draft_and_builds_directory():
    arts = [_artifact("active", Lifecycle.ACTIVE), _artifact("draft", Lifecycle.DRAFT)]
    res = get_context("Why did Brand X lose share?", doc=_doc(),
                      agent_type="commercial", artifacts=arts, tags=COMMERCIAL,
                      pack="commercial_analytics@0.1")
    # governance: draft never reaches the agent
    assert [a.id for a in res.eligible] == ["active"]
    # CTX L3 directory lists the sections the agent may hydrate
    assert "ENTITY-BRAND-X" in res.system_prompt
    assert "ctx/hydrate" in res.system_prompt
    # trust envelope
    assert res.trust.pack == "commercial_analytics@0.1"
    assert res.trust.lifecycle_floor == "active"
    assert res.trust.artifacts_used == ["active"]
    assert res.tokens_estimate > 0


def test_get_context_empty_artifacts_yields_zero_confidence():
    res = get_context("q", doc=_doc(), artifacts=[])
    assert res.eligible == []
    assert res.trust.confidence == 0.0


def test_get_context_dev_mode_floor_is_verified():
    res = get_context("q", doc=_doc(), artifacts=[], dev_mode=True)
    assert res.trust.lifecycle_floor == "verified"


def test_gated_out_section_is_absent_from_the_directory():
    # H1: the directory shown to the agent must contain only eligible sections
    doc = CTXDocument(
        header=Header(magic="§CTX", version="1.0", layer=Layer.L2),
        body=(
            Section(name="DH-KEEP", children=(KeyValue(key="ID", value="keep"),)),
            Section(name="DH-DROP", children=(KeyValue(key="ID", value="drop"),)),
        ),
    )
    arts = [_artifact("keep", Lifecycle.ACTIVE, domain="commercial"),
            _artifact("drop", Lifecycle.ACTIVE, domain="manufacturing")]
    res = get_context("q", doc=doc, artifacts=arts, tags=COMMERCIAL)
    assert res.trust.artifacts_used == ["keep"]
    assert "DH-KEEP" in res.system_prompt
    assert "DH-DROP" not in res.system_prompt  # gated out → not hydratable


def test_query_orders_the_directory_by_relevance():
    doc = CTXDocument(
        header=Header(magic="§CTX", version="1.0", layer=Layer.L2),
        body=(
            Section(name="DH-REBATE", children=(KeyValue(key="ID", value="rebate"),)),
            Section(name="DH-ACCESS", children=(KeyValue(key="ID", value="access"),)),
        ),
    )
    arts = [_artifact("rebate", Lifecycle.ACTIVE), _artifact("access", Lifecycle.ACTIVE)]
    res = get_context("why is market access the problem?", doc=doc, artifacts=arts, tags=COMMERCIAL)
    # the access-relevant artifact ranks first (query-sensitive ordering)
    assert res.trust.artifacts_used[0] == "access"


def test_trust_envelope_carries_backing_deltas():
    arts = [_artifact("a", Lifecycle.ACTIVE)]
    res = get_context("q", doc=_doc(), artifacts=arts)
    assert res.trust.backing_deltas == ["d"]  # the governing delta is surfaced


def test_always_included_kinds_constant_available():
    # safety layers the F2 budget step must never trim (consumed downstream)
    from ontowiz_spec import ALWAYS_INCLUDED_KINDS
    assert ArtifactKind.GUARDRAIL in ALWAYS_INCLUDED_KINDS
