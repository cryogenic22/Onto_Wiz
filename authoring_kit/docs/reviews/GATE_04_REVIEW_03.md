# Gate 4 adversarial review — attempt 3

Decision: **BLOCKED**  
Reviewer: independent portable-adapters owner  
Gate 5 authorization: **not granted**

## Findings

1. **P1 — historical session history was not portable**
   - Named completed session bundles were required to equal the latest
     workspace revision and session sequence.
   - Advancing the workspace would therefore invalidate or require rewriting
     immutable earlier session receipts.
   - Historical bundles must retain their own exact revision/sequence binding,
     be unique and ordered below the current high-water, and never be rewritten
     merely because the workspace advances.

2. **P1 — provenance edges were checked as unrelated memberships**
   - Claim and decision source, evidence, and candidate-artifact identifiers
     were each checked against a known-ID set.
   - Validation did not prove that cited evidence belongs to a cited source or
     that each cited artifact carries the same source/evidence links.
   - Cross-reference validation must preserve the actual provenance graph, not
     only node existence.

## Checks that held

- Shared record-graph validation is present in build, standalone verification,
  and staged import.
- Canonical resume proposal/question anchors, complete named session bundles,
  responses/receipts, live-current handling, and the prior archive hardening
  remained wired.

## Close condition

Attempt 4 must independently confirm immutable multi-session history across a
later workspace revision and reject provenance-inconsistent but individually
known source/evidence/artifact identifiers.

