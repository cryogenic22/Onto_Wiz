# Platform Baseline Structure & Crosswalk (Step 0)

**Status:** Accepted baseline for review · **Date:** 2026-07-12
**Governs:** repo topology, truth boundaries, the client-pack pinning contract, and the
crosswalk from the Domain Pack Platform steps to the existing delivery backlog.
**Anchors:** ADR-018 (three-part separation), ADR-019 (deployment planes / PackSource /
registry / frontend), ADR-012 (two-tier packaging),
`DOMAIN_PACK_PLATFORM_BUILD_INSTRUCTION_SET_2026-07.md`, and the domain team's three-part
architecture recommendation (recorded below).

## 1. Three-part topology

```
KP_SDLC (sibling repo, exists)          Onto_Wiz (this repo)                 Domain-pack repos (later)
  delivery governance:                    knowledge-product mechanics:         client semantic truth:
  agent instr., mini-specs, CI,           schemas, curation, Deltas,           ontowiz-domain-packs/ (shared base)
  gates, boundary checks, evidence,       compiler, validation, eval,          client-<name>-domain-context/ (private)
  reviewer isolation                      release, typed serving               + Auravia conformance exam (stays here)
        |                                         |                                   |
        +------- wraps / bootstraps into ---------+----- approved Delta materializes ->+
                                                  |
                                          tenant release registry (signed, evaluated bundles)
                                                  |
                                          Onto_Wiz runtime + typed APIs -> client agents
```

**Rule:** KP_SDLC is never a knowledge store; Onto_Wiz never holds confidential client
content; client repos never fork the schema/compiler/lifecycle/serving.

### 1a. Deployment planes (one modular monorepo → three deployables, ADR-019)

The single `ontowiz-platform` repo builds three independently deployable services:

| Plane | Tier | Deployable responsibility |
|---|---|---|
| Control plane | A (`ontowiz-serve` + governance adapter) | catalog, governance, curation, releases, eval metadata, admin |
| Build plane | B (`ontowiz-factory` workers) | isolated compiler/eval workers; hold model creds + controlled source access; cannot activate artifacts |
| Data plane | A (`ontowiz-runtime`, per-tenant, key-free) | projections, embeddings, context resolution, agent traffic |

Deployment modes (ADR-019 §4): Managed API · Onto_Wiz-managed client VPC (pharma default) ·
client-hosted/on-prem. Signing proves integrity/authorship, **not** confidentiality.

## 2. Onto_Wiz internal layout (platform repo)

Existing package tiers (ADR-012) with the Step-2/5 kernel files slotted in (§9 of the
instruction set). New files are additive to existing packages — no parallel stack.

```
packages/ontowiz-spec/ontowiz_spec/          # Tier A — pure contracts, no db/llm/web/compiler dep
  schema_registry.py  source_contracts.py  semantic_contracts.py
  analytics_contracts.py  validation_contracts.py  eval_contracts.py  release_contracts.py
  pack_source.py       artifact_registry.py  # interface seams (ADR-019): local impl now, Git/OCI later
packages/ontowiz-core/ontowiz_core/          # Tier B — governed write model, Delta lifecycle, policy
packages/ontowiz-factory/ontowiz_factory/    # Tier B — resolver.py compiler.py canonicalize.py
  parsers/  validation/  projections/  evals/
packages/ontowiz-runtime/ontowiz_runtime/    # Tier A — registry.py release_verifier.py projection_registry.py
  governance.py                              #   (F0.2 durable store = persistence adapter, ADR-018 §7)
packages/ontowiz-serve/ontowiz_serve/        # Tier A — auth, tenant resolution, REST/MCP routing
examples/reference_domain_packs/auravia_marketing/0.1.0/   # conformance exam (KEEP; synthetic, non-releasable)
packages/ontowiz-factory/tests/fixtures/compiler/          # valid/ invalid/<rule> near_miss/<rule> golden/
packs/commercial_analytics/                  # real pack, in-repo for now -> Step-10 second-consumer test
```

Conformance fixtures live beside the platform because they are the exam it must pass on any
schema/compiler/runtime change; the current `packs/commercial_analytics/` stays until Step 10
migrates it as the compatibility test.

## 3. Client-pack repository template (define now, create later)

```
client-<name>-domain-context/
  pack.yaml                 # the pin/lock (see §4)
  ontology/  terminology/  claims/  policies/
  semantic_data/  omnichannel/  agents/  evaluations/
  source_manifests/         # source IDENTITIES: id, content hash, locator, access class,
                            #   applicability, excerpt — never raw documents
```

Shared base: `ontowiz-base-packs/{pharma-commercial-base, commercial-marketing,
commercial-analytics, market-policy-us, market-policy-gb, supply-chain}/` (canonical name per
ADR-019; supersedes ADR-018's `ontowiz-domain-packs`). A client repo may carry
brand/market/engagement overlays (not one repo per brand). Every pack repo is consumed
through the `PackSource` interface (ADR-019 §2) — a local directory today, a Git SHA or
governance-materialized source later, with the same compiler contract.

## 4. Client-pack pin/lock contract

Every client `pack.yaml` pins, at compile time:

```
schema_version           # exact ontowiz-spec schema registry version + digest
compiler_range           # compatible Onto_Wiz compiler versions
base_packs[]             # base-pack name -> version + content digest
client_source_commit     # immutable SHA of the client pack repo
eval_suite_digest        # frozen held-out/adversarial suite
candidate_digest         # deterministic compiled candidate
release_attestation      # binds candidate digest to passing receipt set
```

Floating `latest` dependencies are rejected (§5.5). A correction bumps the client-pack
version only — the platform is untouched.

## 5. Truth boundaries

| Truth | Home |
|---|---|
| Raw evidence | Client source systems (Veeva/SharePoint/DMS/data platform) — outside Git |
| Approved semantic source | Client pack repo at an immutable SHA |
| Workflow & audit | Onto_Wiz governance DB (F0.2 store, the Tier-A adapter) |
| Released | Immutable compiled pack + eval receipts + release attestation |
| Vector/graph/lexical/catalog | Disposable derived projections |
| Engineering delivery evidence | KP_SDLC workflow |

An approved Delta **materializes** a pack-repo commit; compilation starts from that merged
immutable commit (ADR-018 §6) — the DB and Git are never independently editable competing
truths.

## 6. Crosswalk — platform steps ↔ existing cards (no silent renumbering)

| Platform step | Existing card / area | Status |
|---|---|---|
| Step 0 accept + commit baseline | *this doc + ADR-018* | **in progress (this commit)** |
| Step 1 harden candidate/release | overlaps F0.6A; new small unit for the 2 verified gaps | glob (`registry.py:43,60`) + reseal (`benchmark.py:238`) OPEN; path-traversal/seal/gate-decouple DONE |
| Step 2 schema-registry kernel | new, `ontowiz-spec` | PLANNED (build source/evidence + governance contracts first) |
| Step 3 source/evidence boundary | **F0.4A** | mini-spec at `2a493d4`; #7 superseded by ADR-018 → v3 after Step 2 |
| Step 4 persistent governance | **F0.2H** | mini-spec at `2a493d4`; store = Tier-A adapter; write-model → core at F0.3 |
| Step 5 resolver + compiler v2 + validators | new, `ontowiz-factory` | PLANNED |
| Step 6 domain artifact profiles | new | PLANNED (2 vertical questions only) |
| Step 7 make Auravia executable | conformance harness | PLANNED |
| Step 8 projections + typed serving | relates F0.3A | PLANNED |
| Step 9 SME curation + learning loop | relates F4/F5 | PLANNED (after lifecycle executable) |
| Step 10 second-consumer gate | `packs/commercial_analytics` migration + neutral pack | PLANNED |
| Delta→Git materialization | new (R1 reshape, ADR-018 §6) | PLANNED (after F0.2H/F0.3); one `PackSource` impl |
| `PackSource` + `ArtifactRegistry` interfaces | new, `ontowiz-spec` (ADR-019) | PLANNED (Step 2 contracts; local impls first, Git/OCI later) |
| Offline simulator + trace | extends `benchmark.py` / `run_agent_lift_benchmark.py` | PLANNED (reuse; with/without-context lift already exists) |
| Typed staleness (8 reasons) | Step-2 contract + §5.12 invalidation loop; FE surfaces | PLANNED (derived view, not a badge) |
| Frontend Context Control Plane (9 modules) | **FE lane**; catalog already seeds Context Catalog | product direction (ADR-019 §5); FE specs, not BE |

## 7. Create-now vs define-for-later

- **Now (in this repo):** commit this baseline (Step 0); then Step 1 hardening; then the
  Step-2 schema-registry kernel.
- **Defined, not yet created:** `ontowiz-domain-packs`, `client-*` repos, and the tenant
  registry (created when the Step-5 compiler can consume an external pack repo).
- **User/INT operational calls (not agent-initiated):** KP_SDLC harness extraction; creating
  external repos; provisioning the tenant registry.

## Appendix — recorded architecture recommendation (verbatim intent)

The domain team's recommendation: **KP_SDLC governs delivery, Onto_Wiz governs
knowledge-product mechanics, private pack repositories govern client semantic truth, and
client systems retain raw evidence.** Putting real client packs in Onto_Wiz couples
confidential content to platform releases; putting them in KP_SDLC turns an engineering
harness into a knowledge platform — both are the wrong long-term boundary. Immediate
approach: keep Auravia as the conformance fixture; create a reusable private pack-repo
template; bootstrap the KP_SDLC harness into Onto_Wiz and the template; implement
schema/compiler/runtime capability; pilot one private client pack repo; publish to a
tenant-specific registry; migrate commercial analytics as a second compatibility test; add a
neutral/non-pharma pack before declaring the kernel generic.
