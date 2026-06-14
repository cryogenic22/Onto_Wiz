"""Loop 5 / UX-2 (F5-B) — Pack Registry detail view (Tier A, read-only).

Backs the Registry UI: artifact explorer (lifecycle + served + eval-coverage
flags) and the gaps list that the Forge turns into missions. Pure over a
LoadedPack — no factory, no network.
"""

from __future__ import annotations

from ontowiz_ctx.core.model import CTXDocument, Header, Layer
from ontowiz_runtime import LoadedPack, pack_detail
from ontowiz_spec import (
    DecisionHeuristic,
    EvalCase,
    Lifecycle,
    PackEvalSummary,
    PackManifest,
)


def _loaded() -> LoadedPack:
    served = DecisionHeuristic(id="h1", name="served + tested").transition(
        Lifecycle.ACTIVE, changed_by="c", delta_id="d"
    )
    served_gap = DecisionHeuristic(id="h2", name="served, no eval").transition(
        Lifecycle.ACTIVE, changed_by="c", delta_id="d"
    )
    draft = DecisionHeuristic(id="h3", name="draft, not served")  # stays DRAFT
    ec = EvalCase(id="ec1", name="covers h1", question="q?", gold_answer="a", validates=["h1"])
    manifest = PackManifest(
        name="commercial_analytics",
        version="0.1.0",
        artifact_count=4,
        evals=PackEvalSummary(eval_cases=1, pass_rate=1.0, agent_lift=0.4, gate_passed=True),
    )
    doc = CTXDocument(header=Header(magic="§CTX", version="1.0", layer=Layer.L2))
    return LoadedPack(manifest=manifest, l2_doc=doc, artifacts=[served, served_gap, draft, ec])


def test_detail_flags_served_and_eval_coverage():
    d = pack_detail(_loaded())
    by_id = {r.id: r for r in d.artifacts}
    assert by_id["h1"].served and by_id["h1"].has_eval
    assert by_id["h2"].served and not by_id["h2"].has_eval
    assert not by_id["h3"].served  # DRAFT is not served to agents


def test_detail_gaps_are_served_artifacts_missing_eval():
    d = pack_detail(_loaded())
    # h2 is served but has no eval → it's a gap the Forge should close
    assert "h2" in d.gaps
    assert "h1" not in d.gaps  # covered
    assert "h3" not in d.gaps  # not served, so not a serving-quality gap


def test_detail_surfaces_manifest_eval_summary():
    d = pack_detail(_loaded())
    assert d.name == "commercial_analytics"
    assert d.evals["agent_lift"] == 0.4
    assert d.evals["gate_passed"] is True
