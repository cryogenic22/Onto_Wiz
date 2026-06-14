"""Loop 5 (F3-B) — REST API tests (FastAPI TestClient)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from ontowiz_factory.compiler import compile_pack, write_pack
from ontowiz_factory.seed import build_commercial_pack
from ontowiz_serve.api import create_app
from ontowiz_spec import DecisionHeuristic, Lifecycle, Tag, TagDimension

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"


def _client(tmp_path) -> TestClient:
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    return TestClient(create_app(tmp_path))


def test_health(tmp_path):
    assert _client(tmp_path).get("/health").json() == {"status": "ok"}


def test_catalog_page_served_at_root(tmp_path):
    r = _client(tmp_path).get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "Domain Intelligence Catalog" in r.text
    # the page is wired to the live API, not a static mock
    assert "/v1/catalog" in r.text


def test_list_packs(tmp_path):
    r = _client(tmp_path).get("/v1/packs")
    assert r.status_code == 200
    assert any(p["name"] == "commercial_analytics" for p in r.json())


def test_comment_post_and_list(tmp_path):
    c = _client(tmp_path)
    base = "/v1/packs/commercial_analytics/0.1.0/artifacts/rule_formulary_exclusion/comments"
    posted = c.post(base, json={"author": "Priya", "text": "payer-driven"},
                    headers={"X-OntoWiz-Role": "sme"})
    assert posted.status_code == 200
    assert posted.json()["role"] == "sme"
    got = c.get(base).json()
    assert len(got) == 1 and got[0]["text"] == "payer-driven"
    # commenting on a missing artifact is a 404
    bad = "/v1/packs/commercial_analytics/0.1.0/artifacts/nope/comments"
    assert c.post(bad, json={"author": "x", "text": "y"}).status_code == 404


def test_pack_diff_route(tmp_path):
    def _h(hid, fn):
        return DecisionHeuristic(
            id=hid, name=hid, decision_logic="x => y",
            tags=[Tag(dimension=TagDimension.FUNCTION, value=fn)],
        ).transition(Lifecycle.ACTIVE, changed_by="c", delta_id="d")

    write_pack(compile_pack([_h("rule_keep", "market_access")], name="p", version="0.1.0"), tmp_path)
    write_pack(
        compile_pack([_h("rule_keep", "market_access"), _h("rule_loe", "forecasting")],
                     name="p", version="0.2.0"),
        tmp_path,
    )
    c = TestClient(create_app(tmp_path))
    d = c.get("/v1/packs/p/diff", params={"from": "0.1.0", "to": "0.2.0"}).json()
    assert d["added"] == ["rule_loe"]
    assert d["function_deltas"]["forecasting"] == {"from": 0, "to": 1, "delta": 1}


def test_roles_and_rbac_review(tmp_path):
    c = _client(tmp_path)
    caps = c.get("/v1/roles").json()
    assert "review" in caps["curator"] and "review" not in caps["builder"]

    review = "/v1/packs/commercial_analytics/0.1.0/artifacts/rule_formulary_exclusion/review"
    body = {"decision": "approve", "note": "payer logic sound"}
    # builder lacks the review capability → 403
    assert c.post(review, json=body, headers={"X-OntoWiz-Role": "builder"}).status_code == 403
    # an unknown role → 403
    assert c.post(review, json=body, headers={"X-OntoWiz-Role": "intern"}).status_code == 403
    # curator may review → 200, decision recorded
    ok = c.post(review, json=body, headers={"X-OntoWiz-Role": "curator"})
    assert ok.status_code == 200 and ok.json()["decision"] == "approve"


def test_usage_and_stats_route(tmp_path):
    c = _client(tmp_path)
    c.post("/v1/usage", json={"pack": "commercial_analytics", "version": "0.1.0",
                              "function": "forecasting", "hit": True})
    c.post("/v1/usage", json={"pack": "commercial_analytics", "version": "0.1.0",
                              "function": "forecasting", "hit": False})
    stats = c.get("/v1/catalog/stats").json()
    ca = next(p for p in stats if p["pack"] == "commercial_analytics")
    assert ca["consults"] == 2 and ca["hits"] == 1
    assert ca["by_function"]["forecasting"] == 2


def test_catalog_route(tmp_path):
    c = _client(tmp_path)
    cat = c.get("/v1/catalog").json()
    entry = next(e for e in cat if e["name"] == "commercial_analytics")
    assert entry["domain"] == "commercial"
    assert entry["latest_version"] == "0.1.0"
    # the pack's function slices are surfaced with counts
    assert entry["functions"]["market_access"] >= 8
    assert entry["functions"]["forecasting"] == 4
    assert entry["signed"] is True


def test_catalog_search_route(tmp_path):
    c = _client(tmp_path)
    hits = c.get("/v1/catalog/search", params={"q": "formulary"}).json()
    assert any(h["name"] == "commercial_analytics" for h in hits)
    hit = next(h for h in hits if h["name"] == "commercial_analytics")
    assert any(m["id"] == "rule_formulary_exclusion" for m in hit["matched_artifacts"])
    # function filter narrows to packs that have the slice
    fc = c.get("/v1/catalog/search", params={"function": "forecasting"}).json()
    assert [h["name"] for h in fc] == ["commercial_analytics"]


def test_artifact_route(tmp_path):
    c = _client(tmp_path)
    base = "/v1/packs/commercial_analytics/0.1.0/artifacts"
    a = c.get(f"{base}/rule_pathway_exclusion").json()
    assert a["function"] == "market_access"
    assert a["therapy"] == "oncology"
    assert a["anti_patterns"]
    assert "rule_pathway_exclusion" in a["yaml"]
    assert c.get(f"{base}/nope").status_code == 404


def test_functions_route(tmp_path):
    c = _client(tmp_path)
    fns = c.get("/v1/packs/commercial_analytics/0.1.0/functions").json()
    by = {s["function"]: s for s in fns}
    assert by["forecasting"]["count"] == 4
    assert by["forecasting"]["slice_tokens"] < by["forecasting"]["full_tokens"]


def test_get_pack_and_404(tmp_path):
    c = _client(tmp_path)
    # 1 entity registry + 19 base heuristics + 4 forecasting-module heuristics
    assert c.get("/v1/packs/commercial_analytics/0.1.0").json()["artifact_count"] == 24
    assert c.get("/v1/packs/nope/9.9.9").status_code == 404


def test_pack_detail_route(tmp_path):
    c = _client(tmp_path)
    r = c.get("/v1/packs/commercial_analytics/0.1.0/detail")
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "commercial_analytics"
    assert len(d["artifacts"]) == 24  # base pack + forecasting module (drop-a-file)
    # every artifact row carries the explorer flags
    assert all({"served", "has_eval", "lifecycle"} <= set(a) for a in d["artifacts"])
    assert c.get("/v1/packs/nope/9.9.9/detail").status_code == 404


def test_explain_route(tmp_path):
    c = _client(tmp_path)
    r = c.get("/v1/packs/commercial_analytics/0.1.0/explain", params={"concept": "share"})
    assert r.status_code == 200
    d = r.json()
    assert d["concept"] == "share"
    assert isinstance(d["lineage"], list)
    if d["lineage"]:
        assert {"artifact_id", "served", "sources", "governance_steps"} <= set(d["lineage"][0])
    assert c.get(
        "/v1/packs/nope/9.9.9/explain", params={"concept": "x"}
    ).status_code == 404


def test_context_route(tmp_path):
    c = _client(tmp_path)
    r = c.post(
        "/v1/context",
        json={
            "query": "why did Brand X lose share?",
            "pack_name": "commercial_analytics",
            "pack_version": "0.1.0",
            "agent_type": "commercial",
            "tags": [{"dimension": "analytics_domain", "value": "commercial"}],
        },
    )
    assert r.status_code == 200
    d = r.json()
    assert d["trust"]["pack"] == "commercial_analytics@0.1.0"
    assert d["eligible"]
    assert "ctx/hydrate" in d["system_prompt"]


def test_dev_mode_is_refused_unless_server_allows_it(tmp_path):
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    body = {
        "query": "q", "pack_name": "commercial_analytics", "pack_version": "0.1.0",
        "agent_type": "commercial", "dev_mode": True,
    }
    # default app: a client asking for dev_mode is served the production floor
    prod = TestClient(create_app(tmp_path)).post("/v1/context", json=body).json()
    assert prod["trust"]["lifecycle_floor"] == "active"
    # only a server explicitly allowing dev context honours the flag
    dev = TestClient(create_app(tmp_path, allow_dev_context=True)).post("/v1/context", json=body).json()
    assert dev["trust"]["lifecycle_floor"] == "verified"


def test_bad_tag_dimension_is_422_not_500(tmp_path):
    c = _client(tmp_path)
    r = c.post("/v1/context", json={
        "query": "q", "pack_name": "commercial_analytics", "pack_version": "0.1.0",
        "tags": [{"dimension": "not_a_real_dimension", "value": "x"}],
    })
    assert r.status_code == 422


def test_context_route_missing_pack_404(tmp_path):
    c = _client(tmp_path)
    r = c.post(
        "/v1/context",
        json={"query": "q", "pack_name": "nope", "pack_version": "0.0.0"},
    )
    assert r.status_code == 404
