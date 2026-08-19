"""Loop 6 (F3-C) — MCP tool handler tests (no live transport needed)."""

from __future__ import annotations

import json
from pathlib import Path

from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import PackRegistry
from ontowiz_serve.mcp import (
    TOOL_NAMES,
    dispatch,
    handle_context_get,
    handle_pack_list,
    handle_pack_query,
)

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"


def _registry(tmp_path) -> PackRegistry:
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    return PackRegistry(tmp_path)


def test_tool_names():
    # F0.10 added ctx/hydrate — the tool the served L3 directory has always
    # instructed agents to call, and which this door previously did not register.
    assert set(TOOL_NAMES) == {"context/get", "pack/list", "pack/query", "ctx/hydrate"}


def test_pack_list(tmp_path):
    out = json.loads(handle_pack_list(_registry(tmp_path)))
    assert any(p["name"] == "commercial_analytics" for p in out)


def test_pack_query_filter_by_kind(tmp_path):
    out = json.loads(
        handle_pack_query(
            _registry(tmp_path),
            {"pack_name": "commercial_analytics", "pack_version": "0.1.0", "kind": "decision_heuristic"},
        )
    )
    assert out["count"] == 23  # 19 base + 4 forecasting-module heuristics
    assert all(a["kind"] == "decision_heuristic" for a in out["artifacts"])


def test_context_get(tmp_path):
    out = json.loads(
        handle_context_get(
            _registry(tmp_path),
            {
                "query": "why did Brand X lose share?",
                "pack_name": "commercial_analytics",
                "pack_version": "0.1.0",
                "tags": [{"dimension": "analytics_domain", "value": "commercial"}],
            },
        )
    )
    assert out["trust"]["pack"] == "commercial_analytics@0.1.0"
    assert "ctx/hydrate" in out["system_prompt"]
    assert out["eligible"]


def test_dispatch_returns_clean_error_on_missing_pack(tmp_path):
    reg = _registry(tmp_path)
    out = json.loads(dispatch(reg, "context/get", {"query": "q", "pack_name": "nope", "pack_version": "9.9.9"}))
    assert out == {"error": "pack not found"}
    # no traceback / filesystem path leaks
    out2 = json.loads(dispatch(reg, "pack/query", {"pack_name": "commercial_analytics"}))
    assert "missing required argument" in out2["error"]
    assert json.loads(dispatch(reg, "bogus/tool", {}))["error"].startswith("unknown tool")


def test_mcp_dev_mode_requires_server_optin(tmp_path):
    reg = _registry(tmp_path)
    args = {"query": "q", "pack_name": "commercial_analytics", "pack_version": "0.1.0", "dev_mode": True}
    # client flag alone does not unlock dev context
    prod = json.loads(handle_context_get(reg, args))
    assert prod["trust"]["lifecycle_floor"] == "active"
    dev = json.loads(handle_context_get(reg, args, allow_dev_context=True))
    assert dev["trust"]["lifecycle_floor"] == "verified"
