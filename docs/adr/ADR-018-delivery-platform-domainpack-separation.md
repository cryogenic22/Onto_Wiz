# ADR-018 — Three-part separation: delivery harness · platform · domain-pack repositories

**Status:** Accepted (Step 0 of the Domain Pack Platform build) · **Date:** 2026-07-12
**Extends:** ADR-012 (monorepo two-tier packaging) · **Relates:** ADR-007 (boundaries),
ADR-011 (read-only reviews), ADR-015 (loop harness)
**Baseline reviewed:** `docs/specs/DOMAIN_PACK_PLATFORM_BUILD_INSTRUCTION_SET_2026-07.md`
(INTENT), the domain team's three-part architecture recommendation (recorded in
`docs/specs/PLATFORM_BASELINE_STRUCTURE_2026-07.md`), and
`examples/reference_domain_packs/auravia_marketing/0.1.0/`.

## Context

The Domain Pack Platform instruction set reframes Onto_Wiz as a domain-independent
"bucket" that safely holds pharma-grade content. A separate recommendation proposes that
three concerns must **not** share one home: how engineering work is delivered, how domain
knowledge becomes a governed product, and where confidential client content lives. `KP_SDLC`
exists as a sibling repo (a portable quality/governance harness bootstrapped into targets).

## Decision

1. **Three homes, not one.**
   - **KP_SDLC** governs *delivery*: agent instructions, mini-specs, CI, quality gates,
     boundary checks, evidence bundles, reviewer isolation. It wraps Onto_Wiz and pack
     repos; it is **not** a knowledge store.
   - **Onto_Wiz** governs *knowledge-product mechanics*: schemas, curation, Deltas,
     compiler, validation, evaluation, release, and typed agent-serving.
   - **Domain-pack repositories** govern *client semantic truth*: reusable base packs
     (`ontowiz-domain-packs/`) and private per-client/legal-IP overlays (`client-*`).
2. **Auravia stays in Onto_Wiz** as the immutable conformance exam (platform test data,
   never production-eligible; synthetic content is permanently barred from release —
   platform invariant 17).
3. **Raw documents stay out of Git.** Veeva/SharePoint/DMS/transcript/data platforms remain
   authoritative. Pack repos hold source *identities, content hashes, `SourceSpan` locators,
   approved semantic artifacts, and controlled excerpts* only.
4. **Compiled releases publish to a tenant-specific artifact registry.** Runtime loads
   signed, evaluated, attested bundles by digest — never a Git checkout, never a glob.
5. **Three independent release cadences:** Onto_Wiz platform · shared base-pack · client
   domain-pack. A client pack pins schema version, compatible compiler range, base-pack
   versions+digests, client source commit, eval-suite digest, candidate digest, and release
   attestation. A knowledge correction produces a new pack release **without** an Onto_Wiz
   deploy.
6. **One-directional truth flow (no DB-vs-Git competing edits).** An approved Onto_Wiz Delta
   **materializes** a controlled pack-repo commit; compilation starts from that merged
   immutable commit. The governance DB is workflow/audit truth; the pack repo at an
   immutable SHA is approved-semantic-source truth; the compiled+attested bundle is released
   truth; projections (vector/graph/lexical/catalog) are disposable.
7. **Governance-tier reconciliation (this session's decision).** F0.2's durable governance
   tables remain a **Tier-A persistence adapter** readable by the key-free serve plane; the
   write-model state machine / decision policy moves to **`ontowiz-core` (Tier B) at F0.3**,
   connected via the DB outbox — no synchronous Tier A→B import (preserves ADR-012).
8. **Sequencing (this session's decision).** Do platform Steps 0→1→2 (accept+commit
   baseline → harden candidate/release → schema-registry kernel) **before** completing
   F0.4A (Step 3) and F0.2H (Step 4) in platform-grade form, so those units are not built on
   contracts that are still churning.

## Consequences

- **R1 is reshaped.** `bridge.py` moves from in-process ACTIVE promotion to *materialize an
  approved Delta into a pack-repo commit*, executed by the Tier-B build worker off the
  outbox. This "Delta→Git materialization" is a named future unit (the §5.3↔§5.5 seam), not
  free.
- **F0.4A finding #7 is superseded.** `ContentObject`/`SourceInstance`/`ParsedChunk`/
  `SourceSpan`/`EvidenceRef` become shared strict contracts in `ontowiz-spec` (Tier A) via
  the schema registry, not parser-local IR — because named cross-tier consumers now exist.
- **Two current Step-1 code gaps are confirmed real and owned:** runtime globs
  (`registry.py:43,60`) and the benchmark reseals `pack.yaml` after eval
  (`benchmark.py:238`). Both violate invariants 13 and 10 and are closed in Step 1.

## Open issues / explicitly deferred (owner + trigger)

- **External repo creation** (`ontowiz-domain-packs`, `client-*`) and the **tenant release
  registry** — deferred until the Step-5 compiler can consume an external pack repo at an
  immutable SHA. Defining the template/pinning contract now; creating repos later.
- **KP_SDLC harness extraction** (moving `cathedral-keeper/`, `quality-gate/`, `quality/`,
  `scripts/verify-audit.sh`, CI, `skills/` out of Onto_Wiz and consuming them back) — a
  distinct delivery-side migration, user/INT operational call, not this session.
- **The Delta→Git materialization unit** — spec after F0.2H/F0.3 land the governed write
  model and outbox.

## Non-negotiables preserved

This ADR does not relax any gate, tier boundary, reviewer independence, evidence
requirement, or the anti-overstatement harness. Until the full platform DoD (§19) is met,
Onto_Wiz is described as *a reference design under construction*, not as producing
release-grade domain packs.
