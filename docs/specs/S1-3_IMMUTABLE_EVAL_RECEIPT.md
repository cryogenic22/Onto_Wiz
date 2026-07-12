# Mini-spec — S1.3: Immutable eval receipt; PackEvalSummary derived; no post-eval reseal

**Unit:** S1.3 (Platform Step 1, unit 3 of 3) · **Owner:** BE · **Depends on:** S1.1
(`candidate_digest`) · **Blocks:** release attestation binding a passing receipt set (F0.6A).
**Baseline SHA:** `1dc26ca` · **Review SHA:** *this commit* · **Contingent on S1.1**.
**Anchors:** DOMAIN_PACK_PLATFORM §5.8 (evaluation framework, the immutable flow), §8 Step 1
items 6 & 8, invariant 10 ("evaluation creates a separate immutable receipt; it never edits or
reseals a candidate"), §18 anti-patterns (reseal-after-eval; inventories/summaries as mutable
release truth); ADR-019 §5.1 (`eval_contracts.py`); DoR §13.

## 1. Objective & named consumer

Evaluation writes a **separate immutable `EvalReceipt` keyed by `candidate_digest`** and
**never edits or reseals the candidate**; the catalog's eval summary becomes a **derived view**
computed from the receipt, not mutable manifest truth. Consumers: the catalog/registry view
(derives lift/pass-rate) and F0.6A's release check (a release binds a passing receipt set for
the unchanged digest).

## 2. In-scope / out-of-scope

**In:** an `EvalReceipt` contract; `benchmark.py` writes the receipt (not the manifest) and
**drops the `reseal_pack` call**; `PackEvalSummary` demoted from stored release truth to a
derived catalog view; the catalog reads receipts.
**Out:** the full independent-evaluation suites (§5.8 Step 6+); release attestation + publish
authorization (F0.6A); the eval *runner* redesign — S1.3 reuses the existing `run_suite`/
`agent_lift`, only changing **where the verdict is written**.

## 3. Files & ownership (BE)

- **new** `packages/ontowiz-spec/ontowiz_spec/eval_contracts.py` — `EvalReceipt` (immutable,
  strict, Tier A). Exported from `ontowiz_spec`.
- **modify** `packages/ontowiz-factory/ontowiz_factory/benchmark.py` — after computing results,
  write an `EvalReceipt` to the receipts store; **remove** the `manifest.evals = …` write and
  the `reseal_pack(pack_dir)` call (`benchmark.py:224-238`).
- **modify** `packages/ontowiz-spec/ontowiz_spec/pack_manifest.py` — `evals: PackEvalSummary`
  **deprecated**: not written for v2 candidates (kept readable for v1 compat); `PackEvalSummary`
  becomes the shape of a *derived view*, not a stored release field.
- **modify** the catalog/registry view (`ontowiz_runtime` `catalog`/`pack_detail`) — derive the
  eval summary by reading the latest receipt for the pack's `candidate_digest`.
- **modify** `test_benchmark.py`, `test_catalog.py`, `test_registry_view.py` — update the
  now-derived expectations; add receipt-immutability tests.

## 4. Typed contract (`EvalReceipt`, immutable)

```
EvalReceipt:
  candidate_digest: str        # the S1.1 reproducible id this receipt attests
  suite_digest: str            # frozen eval-suite identity
  eval_cases: int
  pass_rate: float
  agent_lift: float | None
  results: list[CaseResult]    # per-case verdict (deterministic + model-judged kept separate)
  model_config: str | None     # model/prompt/provider for non-deterministic runs (§5.8)
  created_at: str
```
Stored at `<pack_dir>/receipts/<candidate_digest>.eval.json` (append-only; a receipt is never
overwritten — a re-run writes a new receipt, latest-by-`created_at` wins in the view).

## 5. Immutable flow (invariant 10)

```
candidate_digest (S1.1) -> run_suite/agent_lift (reuse) -> EvalReceipt(candidate_digest, …) [written once]
```
`pack.yaml` bytes are **identical before and after** evaluation (test-enforced); `reseal_pack`
is **not** called by the eval path (the function itself may remain for other governed edits, but
eval never invokes it). A receipt whose `candidate_digest` ≠ the pack's is **not matched**
(wrong-digest → no summary), so a stale receipt cannot masquerade as current.

## 6. Persistence / determinism / egress

Deterministic checks are recorded separately from model-judged ones (§5.8). The receipt records
`model_config` for non-deterministic runs. No candidate bytes mutated; no source text logged.

## 7. Tests mapped 1:1 to acceptance

| Acceptance (item / invariant) | Test |
|---|---|
| **#6/inv10** eval leaves `pack.yaml` bytes unchanged | `test_eval_does_not_mutate_pack_yaml` |
| **#6** `reseal_pack` is not called during eval | `test_eval_does_not_reseal` |
| receipt written, keyed by `candidate_digest`, immutable | `test_eval_receipt_written_and_immutable` |
| re-run writes a new receipt, latest wins (no overwrite) | `test_rerun_appends_new_receipt` |
| **#8** catalog summary is derived from the receipt | `test_catalog_summary_derived_from_receipt` |
| wrong-digest receipt is not matched | `test_wrong_digest_receipt_ignored` |
| v2 manifest carries no stored eval truth | `test_v2_manifest_has_no_stored_evals` |
| v1 pack's embedded evals still readable (compat) | `test_v1_evals_readable_compat` |

Coverage ≥85% on changed code; the mutation/reseal negative paths covered.

## 8. Migration, kill criteria, deferred

- **Migration:** v1 packs keep their embedded `evals` (compat, read-only); v2 packs store none —
  the summary is derived. Existing `commercial_analytics/*` are not force-migrated.
- **Kill criteria:** if deriving the catalog summary from receipts requires the S1.2 loader
  changes to land first, sequence S1.3 after S1.2 rather than duplicating load logic.
- **Deferred:** publish authorization + release attestation binding the receipt set → F0.6A;
  the 10 independent eval suites → §5.8 (Step 6+).

## 9. DoD

Evaluation never mutates candidate files or reseals; a separate immutable receipt is written per
`candidate_digest`; the catalog summary is a derived view; stale/wrong-digest receipts don't
authorize a summary; `verify-audit` PASS; evidence bundle per §14.
