# ontowiz-ctx

**Tier A — ships to clients.** The Onto_Wiz context engine.

Vendored from [CTX.ai](https://github.com/cryogenic22/CTX.ai) (`cryogenic22/CTX.ai`),
the deterministic knowledge compiler. We vendor rather than depend so all code
lives in one repo (per the Foundation Design, decision D1).

## What it gives us

- **Multi-resolution layers** — L0 raw → L1 prose → L2 semantic graph → L3 directory index.
- **LLM-as-router hydration** — the L3 directory (~<500 tokens) lives in the system
  prompt; the agent calls `ctx/hydrate(section=...)` to pull only what it needs
  (~3.9k tokens/query vs ~92k stuffed). This *is* our inbuilt context management.
- **MCP server** — `ontowiz_ctx.integrations.mcp_server` exposes `ctx/pack`,
  `ctx/parse`, `ctx/validate`, `ctx/format`, `ctx/hydrate`. The headless MCP door
  extends this.
- **Packer** — corpus (YAML/MD/JSON/TOML/CSV) → compiled `.ctx`. The pack compiler
  (Tier B) drives this to build the context layer of each Domain Pack.

## Provenance / upstream sync

Source of truth upstream is CTX.ai. The only local edits on vendoring were import
renames (`ctxpack` → `ontowiz_ctx`). The heavy `benchmarks/` tree was intentionally
not vendored. To pull upstream changes, re-copy `core/`, `modules/`, `cli/`,
`integrations/`, `agent/` and re-apply the rename.
