# Synthetic Auravia Marketing Domain Pack

This directory is a **non-production design fixture** for the Onto_Wiz pharma marketing reference architecture. Auravia, velunimab, all clinical results, policies, sources, plans, and performance values in this directory are fictional.

## What it demonstrates

- A scoped content-generation request.
- Claim, evidence, risk, and MLR-preflight relationships.
- A governed omnichannel next-action decision.
- A semantic brand-performance question with metric and data lineage.
- Named failure modes linked to golden evaluations.
- Exact modular composition inspired by Setu's typed domain boundary.

## What it is not

- It is not a compiled Onto_Wiz pack.
- It is not compatible with the current production artifact schema without the extensions described in `docs/specs/PHARMA_MARKETING_DOMAIN_PACK_REFERENCE_2026-07.md`.
- It is not a source of real clinical, regulatory, legal, promotional, or analytical truth.
- It cannot be promoted to production. The permanent `synthetic_reference` and `production_eligible: false` markers must survive compilation.

## Example questions

### Content and MLR

> Draft a short US HCP email for dermatologists evaluating Auravia for eligible adults, and return an MLR preflight with evidence.

The expected output is a draft, never an approval. It must include the synthetic scoped claim, required risk bundle, approved CTA, evidence locator, and human-review requirement.

### Omnichannel

> Which action may be considered for a consented dermatologist in the evaluation journey state who has reached the email frequency limit?

The email action is excluded. The response must show the governing frequency rule and return only other eligible released actions, or abstain.

### Brand analytics

> Why was Auravia Northeast NBRx below plan in 2026-W26, and was weak email performance responsible?

The correct response reproduces the variance, checks data quality, treats access as a supported hypothesis, observes that the email proxy did not weaken, and refuses a causal conclusion because no controlled experiment exists.

## Intended compiler behavior

1. Require the exact module list in `pack.yaml` to match the files declared by the source pack.
2. Parse each module through shared typed contracts.
3. Reject duplicate IDs, unresolved references, illegal layer broadening, and missing evidence/applicability.
4. Generate graph, retrieval, catalog, agent-contract, and evaluation projections.
5. Stamp every output as synthetic and non-production.
6. Run all critical golden cases before creating a candidate release.

Raw source systems, identity stores, consent systems, warehouses, and MLR workflow systems remain authoritative. This pack contains governed semantic contracts and source identities, not uncontrolled copies of operational or patient-level data.

