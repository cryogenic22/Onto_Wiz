# ADR-019 — Deployment planes, PackSource/registry seams, and the frontend Context Control Plane

**Status:** Accepted (Step 0 addendum) · **Date:** 2026-07-12
**Extends:** ADR-018 (three-part separation) · **Relates:** ADR-012 (two-tier packaging),
ADR-016 (SQLite dev / Postgres prod), ADR-014 (headless serve)

## Context

A follow-on architecture recommendation refines ADR-018: keep Onto_Wiz a **modular
monorepo** (not one repo holding every client pack, not microfrontends/microservices now),
but produce **separately deployable** services from it; introduce a `PackSource` abstraction
so the compiler contract is stable while the physical pack backing evolves; use standard
supply-chain primitives (OCI, Sigstore, SLSA) instead of a bespoke distribution format; and
grow the frontend into a **Context Control Plane**, not just an ontology editor.

## Decision

1. **One monorepo, three deployables (planes).** `ontowiz-platform` stays a single modular
   source repo that builds three independently deployable services:
   - **Control plane** — catalog, governance, curation, releases, eval metadata, admin
     (Tier-A `ontowiz-serve` + governance adapter).
   - **Build plane** — isolated compiler/evaluation workers holding model credentials and
     controlled source access (Tier-B `ontowiz-factory`); cannot activate artifacts directly.
   - **Data plane** — per-tenant, key-free runtime: projections, embeddings, context
     resolution, agent traffic (Tier-A `ontowiz-runtime`).
   This is the deployment expression of ADR-018 §7 and ADR-012; no tier boundary changes.

2. **`PackSource` is the compiler input seam.** The resolver/compiler (Step 5) consume a
   `PackSource` interface, **not** a filesystem path. Backings evolve without changing the
   compiler contract: local directory (now, for Auravia + `packs/commercial_analytics`) →
   private Git repo at an immutable SHA (pilot) → materialized-from-governance-DB+object-store
   (later). Introduced as a Step-2 contract; this is the clean form of ADR-018 §6's
   Delta→Git materialization — the materializer becomes one `PackSource`/registry impl, not a
   compiler rewrite.

3. **`ArtifactRegistry` is the release output seam, OCI-shaped.** Compiled candidates and
   releases publish through an `ArtifactRegistry` interface whose **target** implementation is
   an OCI-compatible registry (non-container artifacts + content digests + attestations),
   with **Sigstore/cosign** signing and **SLSA-v1**-aligned provenance (source commit, inputs,
   compiler, dependency digests). Backed by a simple local/content-addressed impl until the
   kernel works. Our existing `pack.sig` SHA-256 integrity seal is a precursor, not the end
   state.

4. **Deployment modes + honest IP posture.** Offer Managed API (strongest IP, least client
   control) · Onto_Wiz-managed client VPC (balanced default for pharma) · client-hosted/on-prem
   (highest client control, lowest technical IP protection). **Signing proves integrity and
   authorship, not confidentiality**; an on-prem admin can inspect runtime material. Base-pack
   IP is protected by service-side execution where possible, compiled/minimized artifacts,
   tenant keys, access controls, licensing, and contracts — not by signing alone. Consistent
   with PROJECT_STATUS's standing honesty (plaintext packs, lint-time IP boundary today).

5. **Frontend = Context Control Plane (FE lane; product direction).** One Next.js modular-
   monolith app (no microfrontends now) with feature modules: Context Catalog, Universal
   Search, Artifact Inspector, Curation Workbench, Evaluation Center, Release Center,
   Simulator, Operations, Administration. Search and dense filtered lists are primary; graph
   views show focused neighborhoods, not a full-screen graph. **Staleness is typed** (source
   expired/superseded · label/policy changed · SME review overdue · dependent changed · eval
   too old · projection model obsolete · runtime serving superseded · withdrawn), each a
   derived view carrying reason, affected agents/releases, accountable owner, and required
   remediation — never a generic "last updated" badge.

6. **Simulator extends the benchmark, not greenfield.** Offline replay (deterministic
   fixtures, CI-safe) first; connected sandbox (isolated creds, production writes prohibited)
   later. It compares without/with context, release/candidate, base/overlay, and retrieval
   strategies, exposing the full trace (resolved scope, retrieved artifacts, evidence, tool
   calls, tokens, latency, cost, answer, findings, verdict). Trace attributes align with
   **OpenTelemetry** semantic conventions (target, no dep now). A simulation **never** mutates
   a released pack — it may emit a proposed Delta, failure case, or regression (invariant 5 /
   §5.12).

## Consequences

- **Step 2 gains two interface contracts** (`PackSource`, `ArtifactRegistry`) in `ontowiz-spec`,
  backed by local impls — so the compiler/resolver (Step 5) and release path (Step 5/F0.6A)
  are written against stable seams from the start.
- **Reuse, not new build:** the shipped catalog frontend seeds the Context Catalog; the
  `benchmark.py` agent-lift path seeds the offline simulator; `pack.sig` seeds attestation.
- **Naming reconciled:** the shared base-pack repo is canonically **`ontowiz-base-packs`**
  (supersedes ADR-018's `ontowiz-domain-packs` label); `client-*` for private overlays.

## Deferred (owner + trigger) — no new dependencies now

- OCI registry, cosign/Sigstore, SLSA provenance tooling, OpenTelemetry — **target**
  standards; adopt when the release/trace layers are built, not before (R6).
- Connected-sandbox simulator, client-VPC and on-prem delivery — later sequence steps, after
  offline simulator, signing, licensing, and support behavior are proven.
- The 9 frontend modules are **FE-lane** deliverables; this ADR records the product direction,
  not their specs (0B: BE owns `packages/`).

## Non-negotiables preserved

No gate, tier boundary, reviewer independence, evidence requirement, or dependency-approval
rule is relaxed. Interfaces are introduced cheaply; the product surface is built strictly
behind a working, deterministic kernel.
