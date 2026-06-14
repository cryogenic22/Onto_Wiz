# ADR-014: CTX as the context engine; headless library + REST + MCP

**Date:** 2026-06-10
**Status:** SETTLED
**Deciders:** Founder + Tech Lead
**Source:** Foundation Design, decisions D3 & D4

## Context

Two requirements landed together: (1) inbuilt context management so every query
leverages the right domain details, and (2) everything exposed headless behind a
well-defined API and an MCP layer, with the library also consumable directly by
trusted agents.

CTX.ai (`cryogenic22/CTX.ai`) is a deterministic knowledge compiler with a
multi-resolution layer system (L0/L1/L2/L3), LLM-as-router hydration, a packer,
and an MCP server — zero runtime dependencies. market_zero already runs a copy.

## Decision

**CTX is the context engine.** Vendored into `ontowiz-ctx` (Tier A). Context
management for a query runs a four-step pipeline in the runtime:

```
query + agent_type + pinned pack(s) + budget
  -> 1. governance + relevance gate   (runtime; deterministic; ACTIVE-only)
  -> 2. CTX L3 directory              (ontowiz_ctx.hydration_protocol; ~<500 tok)
  -> 3. LLM-as-router hydration       (ontowiz_ctx.hydrator; agent pulls sections)
  -> 4. trust envelope                (runtime; provenance + confidence + pack@ver)
```

The governance gate runs *before* any section is listed in the L3 directory, so
a draft/deprecated artifact is never offered to the agent — governance cannot be
bypassed downstream. Safety layers (OverrideRule, Guardrail, DataQuirk) are
always included and never budget-trimmed.

**Headless — one core, three doors**, all over `ontowiz-runtime.get_context()`
with no business logic in the adapters:

1. **Direct library** — `from ontowiz_runtime import get_context` (trusted
   in-process agents: MarketZero, copilots).
2. **REST** — `ontowiz-serve` FastAPI (`POST /v1/context`, `GET /v1/packs`, ...).
3. **MCP** — `ontowiz-serve` MCP server, extending the vendored CTX tools
   (`ctx/hydrate`, ...) with pack-aware tools (`context/get`, `pack/list`,
   `pack/query`).

## Consequences

**Positive:** ~24x cheaper context than raw stuffing at comparable fidelity, by
eliminating proactive interference; one engine serves three surfaces; the MCP
door is largely pre-built. Governance is structurally unbypassable.
**Negative:** CTX is vendored, so upstream syncs are manual (documented in
`packages/ontowiz-ctx/README.md`).
**Neutral:** RAG is not precluded; for governed packs where precision/provenance
beat broad recall, CTX hydration is the better default.
