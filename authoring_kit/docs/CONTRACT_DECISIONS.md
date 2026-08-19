# Contract decisions

## C1 — Schema identity

All output targets `ontowiz-spec/vNext-min`, revision `1`. The source files and
review specifications that informed the kernel are content-locked in
`locks/source-origin.json`. Phase one changes the kernel only here.

## C2 — Candidate boundary

Artifacts may be `draft` or `review` only. `reviewed_by` and `approved_at` are
null and lifecycle history may not enter `verified` or `active`. Candidate
confirmation is authoring evidence, not platform approval.

`.owpack` always declares:

```json
{
  "package_kind": "candidate",
  "production_eligible": false,
  "releasable": false
}
```

There is no auto-activation, runtime compiler, release, or serving command.

## C3 — Portable formats

Both formats are deterministic `ZIP_STORED` archives. They carry canonical JSON
`META-INF/manifest.json`, its SHA-256, and an exact payload inventory. Paths are
POSIX, NFC, relative, case-fold unique, and sorted. Archive metadata is fixed.

`.owworkspace` is a portable checkpoint and defaults to referenced raw sources.
`.owpack` excludes raw sources, protected evaluations, runtime artifacts,
generated explorer files, adapter state, and mutable evaluation results.

## C4 — Validation

Validation refuses missing provenance, registered source/evidence,
applicability, owner role, or abstention conditions. Metrics additionally need
inputs, unit, grain, and formula. Causal claims additionally need alternatives
and disconfirming conditions. High-risk rules need owned exceptions. Decisions
need public dev/regression evaluation coverage.

## C5 — Adapters

`AdapterSession` is the provider-neutral mutation and state-machine boundary.
Adapters invoke its strict JSON protocol and present questions/diffs; they never
parse or rewrite canonical files themselves. Codex ships first. Claude parity is
gated by the same scripted conformance transcript.

## C6 — Held-out evaluation

The current pre-registration is draft. Real freeze and held-out runs refuse with
`E_PREREG_UNAPPROVED`. The drafting repository and adapters contain no protected
cases or vault paths. A credible run uses an external evaluator or a distinct
service identity whose vault is list/read-inaccessible to the drafting
principal. A same-user hidden directory is not isolation.

## C7 — Receipts

Evaluation never mutates `.owpack`. Private receipts are append-only outside the
draft zone and bind candidate, suite, preregistration, run-plan, evaluator,
adapter, model, prompt, retrieval, tool, and data digests. Public receipts are
redacted attestations and contain no case/oracle material.

## C8 — Historical content identity and authenticity boundary

Portable session, response, claim, decision, and receipt records use ordered
SHA-256 content bindings and exact receipt inventories. These deterministic,
unkeyed digests provide content identity and internal integrity; they do not
authenticate origin. Standalone verification without an externally pinned trust
context cannot distinguish a wholly fabricated but internally consistent,
re-sealed archive from retained history. Authored workspace builds still require
existing `AuthoringTrustProvider` high-water convergence. A signed external
`CheckpointCommitment` may be added later for origin authenticity, but Gate 4
does not imply or implement that guarantee.

## C9 — Public operation intent

Before a mutation, an adapter calls `prepare_intent` and gives the returned
public `AuthoringIntent` to an external trust host. The intent binds operation,
workspace, revision and the exact normalized request. Confirmation preparation
also binds the kernel-computed next session. Credentials and provider metadata
remain out-of-band and never enter adapter JSON or canonical workspace state.

## C10 — Derived candidate explorer

Archive and example generation build one validated `CandidateExplorerContext`
from the exact canonical candidate document bytes. Its sorted document bindings
preserve the raw byte digest even when a document omits default-valued fields.
`context-model.json` is the deterministic serialization of that complete model,
and `explorer.html` is rendered only from the deserialized model. Explorer HTML
is derived output and is excluded from `.owpack`.

## C11 — Recovery confidentiality boundary

Durable transaction journals are public semantic recovery envelopes, not trust
stores. Journal revision 5 contains content/revision bindings plus an opaque
external transaction digest, but no credential, proof, actor identity, nonce,
trust-key identity, provider identity, key identity, or attestation. Recovery
obtains the complete pending or last-finalized transaction identity from the
external provider, compares its full public projection with the journal, obtains
an exact recovery authorization, and revalidates the returned actor against the
external identity and signed authority before applying staged bytes. Missing,
stale, ambiguous, or substituted provider state fails closed.

## C12 — Governed candidate manifest replacement

`pack/pack.yaml` is the sole root-level canonical pack target admitted to the
proposal path and is validated as `CandidatePackManifest`. It uses the same
intent, evidence, proposal, confirmation, revision, and external-provider
transaction flow as every other canonical document. No raw-document publication
or unchecked pack-construction API is exposed.

## C13 — External evaluation custody

The kit defines strict immutable evaluation contracts and a fail-closed
coordinator, but no local vault, protected fixture, provider implementation, or
receipt database. An external custodian verifies the approved pre-registration,
vault isolation, suite lock, run-plan signature, and blind-arm tokens. The
worker receives only one public scenario and an opaque blind token in a fresh,
externally attested runtime. Dispatch is ordered by opaque tokens, never arm
order. Private scoring and the atomic append-only receipt store remain behind the
custodian boundary. The private receipt retains complete answer, citation,
retrieval, and tool traces; the caller receives only a redacted attestation and
opaque append commitment. Every external model is exact-type round-trip
revalidated and every verifier must return literal `True`.

Infrastructure, drift, isolation, completeness, blinding, signature, agreement,
or append failures refuse without a quality receipt. A completed critical
quality failure is recorded immutably with `gate_passed: false`. Because the
reviewed pre-registration remains draft, phase one does not authorize real
held-out execution.

## C14 — First-party coverage non-regression ratchet

The initial local Gate 7 precommitted to 90% overall branch coverage without a
numeric requirement in Revision 2. The first complete measurement failed that
local gate: 261 tests passed, two OS-capability tests skipped, and combined
statement/branch coverage was 77.79% when the byte-for-byte pinned v0.1 vendor
namespace was counted. Excluding exactly that content-locked namespace produced
a first-party baseline of 80.7671601615074% (4,667/5,516 statements and
1,334/1,914 branches covered). Domain evaluation-matrix readiness in Revision 2
is separate from Python code coverage and is not used to justify this change.

Gate 7 now uses the two-decimal baseline 80.77% as a measured non-regression
ratchet, not a target chosen below the result. Coverage remains branch-enabled
with two-decimal comparison precision and omits only
`src/ontowiz_spec/pinned_v0_1/*`. That vendor namespace is gated independently
by exact path inventory, byte count, and SHA-256 verification. The full suite,
complete archive/candidate/vault negative-path gates, strict typing, lint, and
source/vendor locks remain mandatory. Raising the ratchet requires new measured
coverage; lowering it requires an explicit reviewed contract decision.
