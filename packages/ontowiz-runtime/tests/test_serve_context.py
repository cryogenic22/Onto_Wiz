"""Loop 4 (F3-A) — get_context() serves a loaded pack end-to-end."""

from __future__ import annotations

from pathlib import Path

from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import PackRegistry, context_for_pack, load_pack
from ontowiz_spec import Tag, TagDimension

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"
COMMERCIAL = [Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial")]


def test_context_for_pack_end_to_end(tmp_path):
    pack_dir = build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    loaded = load_pack(pack_dir)

    res = context_for_pack(
        "Why did Brand X lose share this quarter?",
        loaded,
        agent_type="commercial",
        tags=COMMERCIAL,
    )

    # provenance stamped with name@version
    assert res.trust.pack == "commercial_analytics@0.1.0"
    # every pack artifact is ACTIVE + commercial-tagged → all eligible
    assert len(res.eligible) == loaded.manifest.artifact_count
    # the agent gets a CTX hydration directory
    assert "ctx/hydrate" in res.system_prompt
    assert res.trust.confidence > 0
    assert res.trust.lifecycle_floor == "active"


def test_registry_then_serve(tmp_path):
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    reg = PackRegistry(tmp_path)
    loaded = reg.load("commercial_analytics", "0.1.0")
    res = context_for_pack("share decomposition", loaded, tags=COMMERCIAL)
    assert res.eligible
    # an out-of-domain query tag yields no eligible knowledge (governance gate)
    off = context_for_pack(
        "q", loaded, tags=[Tag(dimension=TagDimension.THERAPY_AREA, value="dermatology")]
    )
    assert off.eligible == []
