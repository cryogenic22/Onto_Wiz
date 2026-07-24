"""F0.10 — the serve door honors the contract it prints.

Three defects encoded here:
  1. the served system_prompt instructs `ctx/hydrate`, a tool the door never
     registered — so the advertised consumption loop could not be completed at all;
  2. the MCP trust block omitted `artifacts_used` and `backing_deltas` that REST
     emitted, so the same answer was less attributable depending on the door;
  3. `TOOL_NAMES` and the `Tool(...)` list in `create_server` were maintained by
     hand with nothing cross-checking them.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from ontowiz_factory.seed import build_commercial_pack
from ontowiz_runtime import PackRegistry
from ontowiz_serve.api import create_app
from ontowiz_serve.mcp import TOOL_NAMES, declared_tools, dispatch

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"
PACK = {"pack_name": "commercial_analytics", "pack_version": "0.1.0"}


def _client(tmp_path) -> TestClient:
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    return TestClient(create_app(tmp_path))


def _registry(tmp_path) -> PackRegistry:
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    return PackRegistry(tmp_path)


def _directory_names(system_prompt: str) -> list[str]:
    """Read the hydratable section names the way an agent would — off the prompt.

    Deriving them from the prompt (rather than hard-coding) is the point: it is what
    makes the e2e test fail if the advertised directory and the hydratable set ever
    drift apart again.
    """
    names: list[str] = []
    for line in system_prompt.splitlines():
        if line.startswith("  ") and not line.strip().startswith("ctx/"):
            names.append(line.strip().split()[0])
    return names


# ── 1. the advertised tool exists ────────────────────────────────────────────


def test_advertised_tool_is_registered(tmp_path):
    """The prompt tells the agent to call ctx/hydrate; the door must serve it."""
    c = _client(tmp_path)
    prompt = c.post("/v1/context", json={"query": "share loss", **PACK}).json()["system_prompt"]
    assert "ctx/hydrate" in prompt          # the promise (already true)
    assert "ctx/hydrate" in TOOL_NAMES      # the delivery (the defect)


def test_every_advertised_tool_is_dispatchable(tmp_path):
    """Advertise nothing the door cannot serve.

    TOOL_NAMES is now derived from the same table `create_server` publishes, so
    comparing the two lists would be tautological. The property that actually
    matters — and can still fail — is that dispatch recognises each advertised
    name. `ctx/hydrate` failed exactly this before F0.10.
    """
    reg = _registry(tmp_path)
    for tool in declared_tools():
        assert tool["name"] in TOOL_NAMES
        out = json.loads(dispatch(reg, tool["name"], {}))  # pack/list returns a list
        err = out.get("error", "") if isinstance(out, dict) else ""
        assert not err.startswith("unknown tool"), tool["name"]


# ── 2. trust-envelope parity across doors ────────────────────────────────────


def test_trust_envelope_keys_match_across_doors(tmp_path):
    # both doors must read the SAME pack on disk — delta ids are minted per build,
    # so comparing two separately-built packs would compare noise, not parity
    c = _client(tmp_path)
    q = {"query": "why did Brand X lose share?", **PACK}
    rest = c.post("/v1/context", json=q).json()
    mcp = json.loads(dispatch(PackRegistry(tmp_path), "context/get", q))
    assert set(mcp["trust"]) == set(rest["trust"])
    assert mcp["trust"] == rest["trust"]


def test_mcp_context_get_carries_backing_deltas(tmp_path):
    out = json.loads(dispatch(_registry(tmp_path), "context/get", {"query": "q", **PACK}))
    assert out["trust"]["backing_deltas"]      # provenance, not just a pack label
    assert out["trust"]["artifacts_used"]


# ── 3. the gated hydrate door ────────────────────────────────────────────────


def test_mcp_hydrate_dispatch_returns_content(tmp_path):
    reg = _registry(tmp_path)
    ctx = json.loads(dispatch(reg, "context/get", {"query": "rebate", **PACK}))
    name = _directory_names(ctx["system_prompt"])[0]
    out = json.loads(dispatch(reg, "ctx/hydrate", {"query": "rebate", "section": name, **PACK}))
    assert "error" not in out
    assert out["sections_matched"] == 1
    assert out["text"].strip()


def test_mcp_hydrate_refuses_unknown_section(tmp_path):
    out = json.loads(dispatch(_registry(tmp_path), "ctx/hydrate",
                              {"query": "q", "section": "NO-SUCH-SECTION", **PACK}))
    assert out["error"].startswith("section not servable")
    # the error boundary still leaks nothing
    assert "Traceback" not in out["error"] and "\\" not in out["error"]


def test_mcp_hydrate_refuses_gated_section(tmp_path):
    """A section outside the requested tag slice must refuse, not return empty."""
    reg = _registry(tmp_path)
    full = json.loads(dispatch(reg, "context/get", {"query": "q", **PACK}))
    slice_ = json.loads(dispatch(reg, "context/get", {
        "query": "q", "tags": [{"dimension": "function", "value": "market_access"}], **PACK}))
    gated = sorted(set(_directory_names(full["system_prompt"]))
                   - set(_directory_names(slice_["system_prompt"])))
    assert gated, "fixture no longer produces a narrower slice"

    out = json.loads(dispatch(reg, "ctx/hydrate", {
        "query": "q", "section": gated[0],
        "tags": [{"dimension": "function", "value": "market_access"}], **PACK}))
    assert out["error"].startswith("section not servable")


def test_mcp_hydrate_rejects_an_empty_section_argument(tmp_path):
    out = json.loads(dispatch(_registry(tmp_path), "ctx/hydrate",
                              {"query": "q", "section": " , ", **PACK}))
    assert out["error"].startswith("invalid argument")


def test_mcp_hydrate_accepts_comma_separated_sections(tmp_path):
    # the advertised CTX schema is `section="A,B"` — honour it verbatim
    reg = _registry(tmp_path)
    ctx = json.loads(dispatch(reg, "context/get", {"query": "q", **PACK}))
    names = _directory_names(ctx["system_prompt"])[:2]
    out = json.loads(dispatch(reg, "ctx/hydrate", {"query": "q", "section": ",".join(names), **PACK}))
    assert out["sections_matched"] == 2


# ── REST door ────────────────────────────────────────────────────────────────


def test_rest_hydrate_ok(tmp_path):
    c = _client(tmp_path)
    ctx = c.post("/v1/context", json={"query": "rebate", **PACK}).json()
    name = _directory_names(ctx["system_prompt"])[0]
    r = c.post("/v1/hydrate", json={"query": "rebate", "sections": [name], **PACK})
    assert r.status_code == 200
    body = r.json()
    assert body["sections_matched"] == 1
    assert body["text"].strip()
    assert body["trust"] == ctx["trust"]


def test_rest_hydrate_404_on_unknown_section(tmp_path):
    c = _client(tmp_path)
    r = c.post("/v1/hydrate", json={"query": "q", "sections": ["NO-SUCH-SECTION"], **PACK})
    # 404 not 403: a 403 would confirm the section exists but was withheld
    assert r.status_code == 404
    assert "section not servable" in r.json()["detail"]


def test_rest_hydrate_404_is_identical_for_gated_and_unknown(tmp_path):
    c = _client(tmp_path)
    full = c.post("/v1/context", json={"query": "q", **PACK}).json()
    tags = [{"dimension": "function", "value": "market_access"}]
    sliced = c.post("/v1/context", json={"query": "q", "tags": tags, **PACK}).json()
    gated = sorted(set(_directory_names(full["system_prompt"]))
                   - set(_directory_names(sliced["system_prompt"])))
    assert gated

    a = c.post("/v1/hydrate", json={"query": "q", "sections": [gated[0]], "tags": tags, **PACK})
    b = c.post("/v1/hydrate", json={"query": "q", "sections": ["ZZZ-NOPE"], "tags": tags, **PACK})
    assert a.status_code == b.status_code == 404
    assert a.json()["detail"].replace(gated[0], "<N>") == b.json()["detail"].replace("ZZZ-NOPE", "<N>")


def test_rest_hydrate_422_on_empty_sections(tmp_path):
    c = _client(tmp_path)
    r = c.post("/v1/hydrate", json={"query": "q", "sections": [], **PACK})
    assert r.status_code == 422


def test_rest_hydrate_404_on_unknown_pack(tmp_path):
    c = _client(tmp_path)
    r = c.post("/v1/hydrate", json={"query": "q", "sections": ["X"],
                                    "pack_name": "nope", "pack_version": "9.9.9"})
    assert r.status_code == 404
    assert "pack not found" in r.json()["detail"]


# ── the blocking end-to-end gate ─────────────────────────────────────────────


def test_e2e_directory_to_hydrate_through_serve_door(tmp_path):
    """Pack on disk → directory → hydrate → governed content, over the door only.

    This is the loop the product claims and could not previously complete. The
    section name is read out of the returned prompt, so the test also fails if the
    advertised directory and the hydratable set drift apart.
    """
    c = _client(tmp_path)
    ctx = c.post("/v1/context", json={"query": "why did Brand X lose share?", **PACK}).json()

    names = _directory_names(ctx["system_prompt"])
    assert names, "the directory advertised no hydratable section"

    r = c.post("/v1/hydrate", json={"query": "why did Brand X lose share?",
                                    "sections": names[:3], **PACK})
    assert r.status_code == 200
    body = r.json()
    assert body["sections_matched"] == len(names[:3])
    # governed knowledge, not just section headers
    assert len(body["text"]) > len("".join(names[:3])) * 2
    assert body["trust"]["pack"] == "commercial_analytics@0.1.0"
    assert body["trust"]["backing_deltas"]
