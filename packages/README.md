# Onto_Wiz packages — the two-tier monorepo

All code lives here, in one place, as independently-buildable wheels sharing the
`ontowiz_*` import prefix. The one rule that matters: **Tier A must never import
Tier B** (enforced by `tools/check_boundaries.py`).

## Tier A — ships to clients ("the SDK")

| Package | Imports | Role |
|---|---|---|
| `ontowiz-spec` | pydantic | Data contracts: artifact model, pack manifest, lifecycle, tags. Everything depends on this; it depends on nothing of ours. |
| `ontowiz-ctx` | — (zero runtime deps) | Vendored CTX engine. Context management + LLM-as-router hydration + MCP tools. |
| `ontowiz-runtime` | spec, ctx | `get_context()`, pack loading, governance-gated assembly. What a consumer agent imports. |
| `ontowiz-serve` | runtime, fastapi, mcp | Headless: REST + MCP over the runtime. No business logic. |

## Tier B — internal only ("the factory", secret sauce)

| Package | Imports | Role |
|---|---|---|
| `ontowiz-core` | spec, networkx | Governance brain: Delta model, blast radius, HITL, graph, evidence. |
| `ontowiz-factory` | core, spec, ctx | mining · forge · steward · evals · **compiler** — the machine that makes packs. |

## The product (neither tier — data, not code)

Compiled Domain Packs under `../packs/<name>/<version>/`: artifact YAML +
compiled `.ctx` context layer + signed manifest. The compiler (Tier B) emits
them; the runtime (Tier A) consumes them. This is what gets licensed and shipped.

## Dependency rule

```
Tier A  →  Tier A only
Tier B  →  Tier A + Tier B
never:  Tier A  →  Tier B
```

## Dev install

```powershell
# editable installs, contracts first
pip install -e packages/ontowiz-spec
pip install -e packages/ontowiz-ctx
pip install -e packages/ontowiz-runtime
# Tier B, internal dev only
pip install -e packages/ontowiz-core
pip install -e packages/ontowiz-factory
```
