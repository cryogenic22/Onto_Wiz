"""ontowiz-serve — the headless layer (Tier A).

Two thin doors over ontowiz-runtime, no business logic in either:

  * ``api``  — FastAPI REST  (POST /v1/context, GET /v1/packs, ...)
  * ``mcp``  — MCP server    (context/get, pack/list, pack/query) extending the
               vendored CTX MCP tools (ctx/hydrate, ...)

F0 stub: package exists and declares the doors. The REST app and MCP wiring are
built at F3, once a real pack compiles (F2).
"""

__version__ = "0.1.0"
