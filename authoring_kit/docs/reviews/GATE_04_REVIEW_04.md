# Gate 4 adversarial review — attempt 4

Decision: **BLOCKED**  
Reviewer: independent portable-adapters owner  
Gate 5 authorization: **not granted**

## Finding

**P1 — historical meaning was ID-bound rather than content-bound**

Historical session responses, claims, decisions, and receipts preserved source,
evidence, artifact, proposal, and pack identifiers but not the exact referenced
content identity. A later ordinary same-ID artifact revision could therefore
silently reinterpret an unchanged historical record, or make it fail
portability despite its checkpoint remaining unchanged.

The historical binding must include, under the record self-digest:

- source ID, registered checksum, and source-record digest;
- evidence ID, evidence-item digest, source ID, and source checksum;
- candidate artifact ID and exact payload digest;
- proposal/delta ID and exact proposal digest;
- pack-manifest digest at the session checkpoint.

Session receipts must bind exact digest inventories for their record graph.
Current/live records must match current bytes and provenance edges. Retained
historical records may continue to refer to their immutable content digests
after a later revision, without being reinterpreted or rewritten.

## Checks that held

- Historical revision/sequence checkpoints are unique, monotonic, immutable,
  and below the current high-water.
- Claims and decisions bind to a historical session checkpoint.
- Current provenance edges are checked as source → evidence → artifact.
- Shared build, standalone verification, and staged import validation remains
  present.

## Close condition

Attempt 5 must confirm that a same-ID later artifact revision neither changes
nor invalidates the earlier content-bound record, while any substituted digest
or mismatched current/live binding is refused.

