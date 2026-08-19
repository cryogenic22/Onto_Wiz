"""MCP door (Tier A) — pack-aware tools including the governed ctx/hydrate.

Tools: context/get, pack/list, pack/query, ctx/hydrate. The handlers are plain
functions (testable without the optional `mcp` package); the server wrapper is
guarded on that dependency. Tier A: ontowiz_runtime / ontowiz_spec only.

`ctx/hydrate` is the tool the served L3 directory has always instructed agents to
call. Until F0.10 this door did not register it, so the advertised loop dead-ended
at "unknown tool" and the only working hydrate path read a raw .ctx file — outside
the governance gate. Here it hydrates strictly from the gated projection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ontowiz_runtime import (
    PackRegistry,
    SectionNotServableError,
    context_for_pack,
    hydrate_for_pack,
)
from ontowiz_spec import Tag, TagDimension

from .envelope import context_payload, hydration_payload

try:  # pragma: no cover
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    HAS_MCP = True
except ImportError:  # pragma: no cover
    HAS_MCP = False

_PACK_ARGS = {"pack_name": {"type": "string"}, "pack_version": {"type": "string"}}
_SECTION_ARG = {
    "type": "string",
    "description": (
        "Section name to hydrate (e.g. 'ENTITY-CUSTOMER'). "
        "Use comma-separated names for multiple sections."
    ),
}

# The door's advertised surface, as data. `TOOL_NAMES` is derived from it and
# `create_server` builds its Tool objects from it, so the name list, the MCP
# schema list and the dispatch table cannot drift apart the way they had.
_TOOL_SCHEMAS: tuple[dict[str, Any], ...] = (
    {
        "name": "pack/list",
        "description": "List available domain packs.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "pack/query",
        "description": "List a pack's artifacts.",
        "inputSchema": {
            "type": "object",
            "properties": {**_PACK_ARGS, "kind": {"type": "string"}},
            "required": ["pack_name", "pack_version"],
        },
    },
    {
        "name": "context/get",
        "description": "Governance-gated context for a query over a pack.",
        "inputSchema": {
            "type": "object",
            "properties": {**_PACK_ARGS, "query": {"type": "string"}},
            "required": ["query", "pack_name", "pack_version"],
        },
    },
    {
        "name": "ctx/hydrate",
        "description": (
            "Retrieve full detail for sections listed in the domain map returned "
            "by context/get. Only sections in that map are servable."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {**_PACK_ARGS, "query": {"type": "string"}, "section": _SECTION_ARG},
            "required": ["section", "pack_name", "pack_version"],
        },
    },
)

TOOL_NAMES = [t["name"] for t in _TOOL_SCHEMAS]


def declared_tools() -> list[dict[str, Any]]:
    """The tool descriptors this door advertises (copies — callers may not mutate)."""
    return [dict(t) for t in _TOOL_SCHEMAS]


def _to_tags(items: list[dict] | None) -> list[Tag]:
    return [Tag(dimension=TagDimension(t["dimension"]), value=t["value"]) for t in (items or [])]


def _requested_sections(args: dict[str, Any]) -> list[str]:
    """Accept the advertised `section="A,B"` string or an explicit `sections` list."""
    raw: Any = args.get("sections", args.get("section", ""))
    if isinstance(raw, str):
        raw = raw.split(",")
    return [str(s).strip() for s in raw if str(s).strip()]


def handle_pack_list(registry: PackRegistry) -> str:
    """pack/list — every available pack manifest."""
    return json.dumps([m.model_dump(mode="json") for m in registry.list_manifests()], indent=2)


def handle_pack_query(registry: PackRegistry, args: dict[str, Any]) -> str:
    """pack/query — list a pack's artifacts, optionally filtered by kind."""
    loaded = registry.load(args["pack_name"], args["pack_version"])
    arts = [
        {"id": a.id, "kind": a.kind.value, "name": a.name, "lifecycle": a.lifecycle.value}
        for a in loaded.artifacts
    ]
    kind = args.get("kind")
    if kind:
        arts = [a for a in arts if a["kind"] == kind]
    return json.dumps(
        {"pack": f"{loaded.manifest.name}@{loaded.manifest.version}", "count": len(arts), "artifacts": arts},
        indent=2,
    )


def handle_context_get(
    registry: PackRegistry, args: dict[str, Any], *, allow_dev_context: bool = False
) -> str:
    """context/get — governance-gated context + CTX hydration directory for a query.

    ``dev_mode`` is honoured only when the server was started with
    ``allow_dev_context`` — parity with the REST door, so an MCP client cannot
    pull non-ACTIVE artifacts by setting a flag.
    """
    loaded = registry.load(args["pack_name"], args["pack_version"])
    dev_mode = bool(args.get("dev_mode")) and allow_dev_context
    res = context_for_pack(
        args["query"], loaded, agent_type=args.get("agent_type", "general"),
        tags=_to_tags(args.get("tags")), dev_mode=dev_mode,
    )
    # one shared serializer with the REST door — the envelope cannot drift again
    payload = context_payload(res)
    return json.dumps(
        {k: payload[k] for k in ("system_prompt", "eligible", "trust", "tokens_estimate")},
        indent=2,
    )


def handle_hydrate(
    registry: PackRegistry, args: dict[str, Any], *, allow_dev_context: bool = False
) -> str:
    """ctx/hydrate — full detail for sections the gated directory advertised.

    Reads only the gated projection, so a section this pack holds but this request
    gated out refuses exactly like one that never existed.
    """
    loaded = registry.load(args["pack_name"], args["pack_version"])
    dev_mode = bool(args.get("dev_mode")) and allow_dev_context
    payload = hydrate_for_pack(
        args.get("query", ""), loaded, _requested_sections(args),
        agent_type=args.get("agent_type", "general"),
        tags=_to_tags(args.get("tags")), dev_mode=dev_mode,
    )
    return json.dumps(hydration_payload(payload), indent=2)


def dispatch(registry: PackRegistry, name: str, args: dict[str, Any]) -> str:
    """Safe tool boundary — maps a tool call to a handler, returning a clean JSON
    error (never a traceback or filesystem path) on bad input or missing pack."""
    try:
        if name == "pack/list":
            return handle_pack_list(registry)
        if name == "pack/query":
            return handle_pack_query(registry, args)
        if name == "context/get":
            return handle_context_get(registry, args)
        if name == "ctx/hydrate":
            return handle_hydrate(registry, args)
        return json.dumps({"error": f"unknown tool: {name}"})
    except SectionNotServableError as e:
        return json.dumps({"error": str(e)})
    except FileNotFoundError:
        return json.dumps({"error": "pack not found"})
    except KeyError as e:
        return json.dumps({"error": f"missing required argument: {e}"})
    except ValueError as e:
        return json.dumps({"error": f"invalid argument: {e}"})


def create_server(packs_root: str | Path = "packs"):  # pragma: no cover
    """Build the MCP server (requires the `mcp` package)."""
    if not HAS_MCP:
        raise ImportError("MCP SDK not installed. Install with: pip install mcp")
    registry = PackRegistry(packs_root)
    server = Server("ontowiz")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [Tool(**t) for t in declared_tools()]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        return [TextContent(type="text", text=dispatch(registry, name, arguments))]

    return server


def main() -> None:  # pragma: no cover
    import asyncio

    async def _run() -> None:
        server = create_server()
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())

    asyncio.run(_run())
