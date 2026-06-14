# ADR-012: Monorepo with Two-Tier Packaging (Tier A ships, Tier B is secret sauce)

**Date:** 2026-06-10
**Status:** SETTLED
**Deciders:** Founder + Tech Lead
**Source:** Foundation Design (vision/FOUNDATION_DESIGN.html), decisions D1 & D5
**Extends:** ADR-007 (architecture boundaries)

## Context

We are consolidating four codebases (Onto_Wiz, SpecOmagic, market_zero, aura.ai)
into one place to build a modular domain-intelligence capability. Two forces:

1. **Consolidation** — the founder wants all code in one repo to build upon,
   rather than pip-depending across four repos.
2. **IP protection** — client deployments must not expose the "secret sauce":
   the extraction engine, the Domain Forge, the curation loops, the pack
   compiler. The thing a client gets should be governed, compiled intelligence,
   not the machine that makes it.

## Decision

A single monorepo under `packages/`, split into two tiers by who may receive them.

**Tier A — ships to clients ("the SDK"):**
`ontowiz-spec`, `ontowiz-ctx`, `ontowiz-runtime`, `ontowiz-serve`.

**Tier B — internal only ("the factory"):**
`ontowiz-core`, `ontowiz-factory` (mining · forge · steward · evals · compiler).

**The product** that crosses the boundary is neither tier: a compiled, signed,
license-gated Domain Pack (`packs/<name>/<version>/`).

**The load-bearing rule (generalises ADR-007):**
```
Tier A  -->  Tier A only
Tier B  -->  Tier A + Tier B
forbidden:   Tier A  -->  Tier B
```
Enforced by `tools/check_boundaries.py` in CI and pre-commit. A Tier A package
importing a Tier B package is a build failure — that is how secret sauce would
leak into a client wheel, so we make it impossible by construction.

## IP protection — defense in depth

1. **Architectural (primary):** the factory never packages into a client
   artifact. ~90% of protection, free, just the dependency boundary.
2. **Packaging:** when Tier A runs on-prem, ship built wheels; compile the most
   sensitive runtime logic to native extensions (Cython/Nuitka) — no readable
   source.
3. **Pack protection:** compiled packs are signed (tamper-evident) and optionally
   encrypted at rest, decrypted by the runtime with a per-client license key.
4. **Deployment mode:** headless (ADR-014) enables SaaS, where the client holds
   neither packs nor runtime — only an API/MCP endpoint we host.

## Consequences

**Positive:** clear commercial story (SaaS / on-prem / licensed-embed from one
architecture); the boundary is mechanically checkable; consolidation gives one
source of truth.
**Negative:** more package manifests to maintain; cross-tier work requires
threading data shapes through `ontowiz-spec` rather than importing logic directly.
**Neutral:** original repos become upstream reference, not runtime dependencies.
