# Gate 4 adversarial review — attempt 2

Decision: **BLOCKED**  
Reviewer: independent portable-adapters owner  
Gate 5 authorization: **not granted**

## Attempt-1 disposition

The reviewer traced direct remediation for all five prior P1 findings and both
P2 findings:

- canonical byte-complete ZIP layout;
- exact candidate path/schema and digest inventory;
- locked provider-converged snapshot with identity-pinned reads;
- caller-trusted import date/boundary and repeated rights checks;
- portable state/cross-reference validation and derived regeneration;
- component-prefix collision refusal;
- exact governed inbox bytes.

## Remaining P1

`.owworkspace` did not yet portably validate the full Revision 2 record graph.
The importer refused some required record classes rather than validating them,
and the canonical resume state was not fully reconciled to exact delta and
question records during standalone verification.

Required record support:

- `sources/candidate-claims/SRC-*.yaml`;
- `authoring/decisions/DDR-*.yaml`;
- `authoring/sessions/<id>/session.yaml`;
- `authoring/sessions/<id>/questions.yaml`;
- `authoring/sessions/<id>/responses.yaml`;
- `authoring/sessions/<id>/receipt.yaml`;
- the existing Gate 3 live `authoring/sessions/current/session.yaml`, without
  reinterpreting it as a named candidate session bundle.

Required invariants include strict schemas, candidate-only status, canonical
self-digests, exact workspace/revision/session binding, complete session
bundles, resume-to-proposal/question anchors, response-to-question anchors,
receipt inventory/digests, and source/evidence/candidate-artifact references.
Build, standalone verification, and staged import must share the same graph
validator.

## Close condition

Attempt 3 must independently confirm that a fully rehashed but dangling record
graph is refused by standalone verification as well as import, and that valid
complete record bundles round-trip.

