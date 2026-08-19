# Gate 3 adversarial review — attempt 1

Status: **BLOCKED**  
Reviewer role: independent portability/adversarial reviewer  
Scope: evidence-backed proposal/confirmation workflow and deterministic question
compiler.

The behavioral suite passed, but the gate remained closed because tests did not
cover six security and durability properties:

1. Proposals were not bound to a workspace, actor, or target-owner authority,
   and confirmation trusted a caller-supplied role string.
2. Evidence freshness and retention were evaluated only at evidence-recording
   time. Source and quotation content were not reverified immediately before
   commit.
3. Source, evidence, proposal, and session mutations were not all protected by
   a lock or compare-and-swap revision.
4. Confirmation used exception rollback but had no durable recovery journal
   for process or power loss between target and proposal writes.
5. Session state accepted dangling question identifiers and was not bound to a
   workspace revision.
6. Question compilation accepted unvalidated bodies, had no explicit work
   bounds or deduplication, and silently rerouted missing owner roles.

No runtime import, activation, release, or platform-approval authority was found.

Required disposition: remediate all six findings, add adversarial tests, rerun
the full gate checks, and obtain a new independent review. This review does not
authorize Gate 4.
