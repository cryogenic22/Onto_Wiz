# Gate 4 adversarial review — attempt 1

Decision: **BLOCKED**  
Reviewer: independent portable-adapters owner  
Implementation owner: contract-audit owner  
Gate 5 authorization: **not granted**

## Blocking findings

1. **P1 — unmanifested physical ZIP bytes**
   - Verification accepted bytes before the first local header and did not
     prove a contiguous local-record/central-directory/EOCD layout.
   - Prefix, local-extra, inter-record-gap, and trailing-overlay channels could
     physically carry held-out, raw-source, or private bytes outside the
     manifest.

2. **P1 — fail-open candidate content**
   - Candidate schema validation was conditional on attacker-supplied
     discriminator fields.
   - Unknown structured documents and untyped public text could bypass
     lifecycle, approval, history, provenance, receipt-redaction, and exact
     pack-inventory rules.

3. **P1 — incomplete portable-state import validation**
   - Import did not fully validate every dynamic proposal, evidence,
     candidate-claim, session, decision, pack, and evaluation cross-reference.
   - Required derived-output regeneration was absent before atomic publish.

4. **P1 — stale or uncertain embedded-source rights**
   - The archive controlled the historical rights date used at verification.
   - Import lacked a trusted effective date and destination client boundary;
     missing retention was treated as transferable.

5. **P1 — incoherent workspace snapshot**
   - Packaging could race a governed authoring transaction or a link/reparse
     swap and capture a mixed but internally hashed state.
   - Snapshot creation did not prove provider/revision convergence under the
     Gate 3 cooperative lock.

## Non-blocking findings

- **P2:** reject component-prefix/case-fold namespace collisions during
  verification, not only at extraction.
- **P2:** preserve governed inbox bytes exactly; do not normalize them away
  from the registered checksum.

## Checks that held

- Stored-only compression and central member metadata checks.
- Member path/device/full-name case-fold rejection.
- Entry and streamed byte ceilings.
- Payload inventory and digest enforcement.
- Staged atomic destination creation and no-partial-destination behavior.
- Conflict refusal, source-contained output refusal, and public root exports.

## Required close evidence

- Dedicated can-fail attacks for every P1 and both P2s.
- Targeted archive suite, strict typing, lint, and full regression.
- Independent attempt-2 review with no P0/P1.

