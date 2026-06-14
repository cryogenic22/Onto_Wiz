"""Loop 5 / UX-3 (F5-C) — Knowledge Workbench lineage ('explain this definition').

For an agent builder or SME asking "why does the agent believe X?", trace a
concept to the governed artifacts behind it: provenance, confidence, eval
coverage, and how many governed transitions it has survived. Tier A, read-only.
"""

from __future__ import annotations

from ontowiz_ctx.core.model import CTXDocument, Header, Layer
from ontowiz_runtime import LoadedPack, explain_concept
from ontowiz_spec import DecisionHeuristic, EvalCase, Lifecycle, PackManifest


def _loaded() -> LoadedPack:
    pull = DecisionHeuristic(
        id="dh-pullthrough",
        name="pull-through definition",
        decision_logic="pull-through = scripts after access is granted",
        source_document_ids=["sop-commercial-2024"],
    ).transition(Lifecycle.ACTIVE, changed_by="sme", delta_id="d1")
    other = DecisionHeuristic(id="dh-other", name="rebate timing", decision_logic="rebates lag 60 days")
    ec = EvalCase(
        id="ec-pull", name="pull-through eval", question="define pull-through",
        gold_answer="scripts after access", validates=["dh-pullthrough"],
    )
    doc = CTXDocument(header=Header(magic="§CTX", version="1.0", layer=Layer.L2))
    return LoadedPack(manifest=PackManifest(name="commercial_analytics", version="0.1.0"),
                      l2_doc=doc, artifacts=[pull, other, ec])


def test_explain_traces_concept_to_its_artifacts():
    out = explain_concept(_loaded(), "pull-through")
    ids = [e.artifact_id for e in out]
    assert "dh-pullthrough" in ids
    assert "dh-other" not in ids  # unrelated concept excluded


def test_lineage_entry_carries_provenance_and_eval():
    e = next(e for e in explain_concept(_loaded(), "pull-through") if e.artifact_id == "dh-pullthrough")
    assert e.served is True
    assert e.sources == ["sop-commercial-2024"]
    assert e.has_eval is True
    assert e.governance_steps >= 1  # at least the DRAFT→ACTIVE transition


def test_explain_is_case_insensitive_and_empty_for_unknown():
    assert explain_concept(_loaded(), "PULL-THROUGH")
    assert explain_concept(_loaded(), "no-such-concept") == []
