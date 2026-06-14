"""Red-team round 3 fix — the factory composes end-to-end.

Proves the previously-missing weld: raw text → mined PROPOSED Deltas → governed
(approved) → ACTIVE artifacts → compiled pack → written/loaded → served context.
"""

from __future__ import annotations

import pytest
from ontowiz_factory.compiler import write_pack
from ontowiz_factory.mining import mine_to_deltas
from ontowiz_factory.orchestrate import mine_govern_compile, promote_candidate
from ontowiz_runtime import context_for_pack
from ontowiz_runtime.registry import load_pack
from ontowiz_spec import Lifecycle

TEXT = (
    "If access is rejected then the brand loses share. "
    "IQVIA data lags by 6 weeks."
)


def test_promote_candidate_governs_a_mined_delta_to_active():
    delta = mine_to_deltas(TEXT, source_id="doc1")[0]
    assert delta.content["op"] == "add"
    art = promote_candidate(delta, approved_by="kp")
    assert art.lifecycle == Lifecycle.ACTIVE
    assert art.lifecycle_history[-1].delta_id  # carries a governing delta
    # a non-add delta is refused
    delta.content["op"] = "other"
    with pytest.raises(ValueError):
        promote_candidate(delta)


def test_full_pipeline_text_to_served_context(tmp_path):
    # mine → govern → compile
    pack = mine_govern_compile(TEXT, name="mined_pack", version="0.1.0", source_id="doc1")
    assert pack.manifest.artifact_count >= 2  # the if/then heuristic + the data-lag quirk
    assert all(a.lifecycle == Lifecycle.ACTIVE for a in pack.artifacts)

    # write → load → serve
    pack_dir = write_pack(pack, tmp_path)
    loaded = load_pack(pack_dir)
    res = context_for_pack("why did the brand lose share?", loaded)
    assert res.eligible  # governed knowledge reaches the agent
    assert "ctx/hydrate" in res.system_prompt
    # provenance is real: every served artifact is backed by a delta
    assert res.trust.backing_deltas
    assert len(res.trust.backing_deltas) == len(res.eligible)
