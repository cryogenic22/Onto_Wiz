"""Loop 7 (F4-A) — mining loop tests."""

from __future__ import annotations

from ontowiz_core import DeltaStatus
from ontowiz_factory.mining import mine_text, mine_to_deltas
from ontowiz_spec import ArtifactKind, Lifecycle

SAMPLE = (
    "If PA reject rate exceeds 30%, then escalate to MSL. "
    "IQVIA data lags by 6 weeks, so recent-week TRx is undercounted."
)


def test_mine_text_finds_heuristic_and_quirk():
    arts = mine_text(SAMPLE, source_id="deck1")
    kinds = {a.kind for a in arts}
    assert ArtifactKind.DECISION_HEURISTIC in kinds
    assert ArtifactKind.DATA_QUIRK in kinds
    dh = next(a for a in arts if a.kind == ArtifactKind.DECISION_HEURISTIC)
    assert "msl" in dh.decision_logic.lower()
    # candidates are low-confidence DRAFT — must be governed before serving
    assert all(a.lifecycle == Lifecycle.DRAFT for a in arts)
    assert all(a.confidence < 0.5 for a in arts)
    assert all(a.source_document_ids == ["deck1"] for a in arts)


def test_mine_to_deltas_are_proposed_add_ops():
    deltas = mine_to_deltas(SAMPLE, source_id="deck1")
    assert deltas
    assert all(d.status == DeltaStatus.PROPOSED for d in deltas)
    assert all(d.content["op"] == "add" for d in deltas)
    assert all(d.source_type == "mining" for d in deltas)
    # the candidate artifact rides along in the delta for review
    assert all("artifact" in d.content for d in deltas)
