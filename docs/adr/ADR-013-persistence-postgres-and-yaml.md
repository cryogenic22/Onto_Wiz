# ADR-013: Persistence — Postgres for the machine, YAML for the product

**Date:** 2026-06-10
**Status:** SETTLED
**Deciders:** Founder + Tech Lead
**Source:** Foundation Design, decision D2
**Supersedes:** ADR-005 (in-memory stores)

## Context

ADR-005 chose in-memory stores for early development. The system now needs to
survive restarts, support multiple users, and ship a versionable product. Two
kinds of state with different needs:

- **The product** — Domain Packs and their artifacts — must be diffable,
  reviewable, and shippable to clients.
- **The machine** — Deltas, telemetry, eval runs, Forge sessions — is
  transactional, multi-writer, and stays on our infrastructure.

## Decision

**YAML / files for the product (Tier A consumable):**
- Pack sources: one artifact per YAML file under `packs/<name>/<version>/artifacts/`.
- Compiled context layer: `context.ctx` (L2) + `index.l3.ctx` (L3).
- Signed manifest: `pack.yaml` (the `PackManifest` contract).
- Rationale: knowledge-as-code. A pack change is a reviewable diff/PR. This is
  also exactly what ships to clients.

**Postgres for the machine (Tier B / server state):**
- Delta ledger + audit + HITL queues.
- Consumption telemetry (Loop 5): artifacts used, hit/miss, confidence, corrections.
- Eval runs and agent-lift benchmark history (Loop 4).
- Forge sessions, scores, consensus (Loop 3).
- Rationale: founder's explicit call — Postgres, not SQLite. pgvector is
  available if we later want semantic alias search.

The shipped Tier A runtime is stateless over the pack files; telemetry write-back
is optional and may be disabled or pointed at a local Postgres for air-gapped
client deployments.

## Consequences

**Positive:** packs are git-native and client-shippable; server state is
durable and multi-writer; clean split mirrors the Tier A/B boundary (ADR-012).
**Negative:** two persistence mechanisms to operate; need migrations and a DB in
dev (compose).
**Neutral:** ADR-005 retired; in-memory stores remain usable in unit tests as
fakes behind the same interfaces.
