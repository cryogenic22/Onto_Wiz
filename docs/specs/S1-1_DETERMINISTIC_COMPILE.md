# Mini-spec — S1.1: Deterministic, fresh, digest-addressed compile + exact inventory

**Unit:** S1.1 (Platform Step 1, unit 1 of 3) · **Owner:** BE · **Depends on:** none ·
**Blocks:** S1.2 (manifest-driven load), S1.3 (eval receipt), and every later compile step.
**Baseline SHA:** `1dc26ca` (Step-0 architecture baseline) · **Review SHA:** *this commit*.
**Anchors:** DOMAIN_PACK_PLATFORM §5.6 (deterministic compiler), §8 Step 1 (items 1–3, 7),
§15 leak tests (stale/duplicate/undeclared file), §18 anti-patterns (input-order affects
digest; counts-only inventory; write into existing version dir); DoR §13; ADR-018/019.

## 1. Objective & named consumer

The compiler emits a **byte-identical, reproducibly digest-addressed candidate regardless of
input order**, written **fresh** (no artifact removed upstream can survive on disk), carrying
an **exact input + output inventory** in the manifest; a zero-artifact ("empty diagnostic")
compile is produced but **flagged non-releasable**. Consumer: S1.2's runtime loader (loads
the declared inventory, verifies the candidate digest) and S1.3's eval receipt (keyed by the
candidate digest).

## 2. In-scope / out-of-scope

**In:** `compile_pack` stable ordering; `write_pack` fresh staging + atomic promote +
idempotency/conflict; a reproducible `candidate_digest` (excludes volatile fields); an exact
inventory in `PackManifest` (manifest v2); the empty-candidate non-releasable flag.
**Out:** runtime load/verify (S1.2); eval receipt + `PackEvalSummary` demotion (S1.3); the
full three-manifest resolver + validation engine (Step 5); full digest-addressed *candidate
store vs release registry* separation (F0.6A) — S1.1 keeps the `<name>/<version>/` layout but
makes it fresh, reproducible, and conflict-checked.

## 3. Files & ownership (BE)

- **modify** `packages/ontowiz-factory/ontowiz_factory/compiler.py` — stable sort of `active`;
  reproducible `candidate_digest`; fresh staging write + atomic promote + idempotent/conflict;
  populate the inventory; set `releasable=False` when `active == []`.
- **modify** `packages/ontowiz-spec/ontowiz_spec/pack_manifest.py` — **manifest v2**: add
  `manifest_version`, `input_inventory`, `output_inventory`, `candidate_digest`, `releasable`,
  `candidate_status`. Keep `artifact_count`/`artifact_kinds` as derived convenience (not the
  source of truth). `evals` stays for now (S1.3 demotes it).
- **modify** `packages/ontowiz-factory/tests/test_compiler.py` (+ new cases) — the determinism,
  freshness, inventory, digest-reproducibility, and empty-candidate tests.
- No files outside these packages + this spec.

## 4. Typed contract changes (manifest v2)

```
InventoryEntry:  id, kind, content_digest            # one per input artifact
OutputFile:      path, byte_count, sha256             # one per emitted file
PackManifest (v2 additions):
  manifest_version: int = 2
  candidate_digest: str                               # reproducible content id (see §5)
  input_inventory:  list[InventoryEntry]              # every input artifact, sorted by (kind,id)
  output_inventory: list[OutputFile]                  # every emitted file + bytes + digest
  releasable: bool = True                             # False for empty/diagnostic candidates
  candidate_status: "candidate" | "diagnostic" = "candidate"
```
Backward compatibility: v1 packs (no `manifest_version`) load in compat mode with empty
inventories and `candidate_digest=""`; strict v2 is required for any new compile (ADR-018:
"v1 loading only for explicit migration/non-production compatibility").

## 5. Determinism & digest (the reproducibility contract)

- **Stable order:** sort `active` by `(kind.value, id)` before building sections, the L2 doc,
  and the inventory — so shuffled input yields byte-identical `context.ctx`/`index.l3.ctx`.
- **`candidate_digest` = `sha256(canonical_json(core))`** where `core = { "artifacts": [each
  input artifact's canonical json, sorted by (kind,id)], "l2": l2_text, "l3": l3_directory,
  "manifest_core": manifest minus volatile fields }`. `canonical_json` = `json.dumps(nfc(x),
  sort_keys=True, separators=(',',':'), ensure_ascii=False)`. **Volatile fields excluded**
  (§5.6 item 7): `compiled_at`, `signed`, `candidate_digest` itself, `output_inventory`
  digests, and any run-id/local-path. Two compiles at different times ⇒ identical
  `candidate_digest`.
- **`pack.sig` unchanged in role:** it remains the on-disk *integrity seal* over the written
  bytes (incl. `compiled_at`) — detects post-write tampering. `candidate_digest` is *content
  identity* (reproducible); `pack.sig` is *byte integrity* (as-written). Two digests, two jobs.

## 6. Fresh write, atomic promote, idempotency (§5.6 items 8–10, 17)

`write_pack` writes to a sibling **staging dir**, verifies it (digest recomputed from staged
bytes), then promotes:
- target `<name>/<version>/` absent → atomic `rename(staging → target)`.
- target present with the **same** `candidate_digest` → **idempotent success** (discard staging,
  no rewrite).
- target present with a **different** `candidate_digest` → raise `CandidateDigestConflictError`
  (same version, different bytes — §5.6 "same semantic version with a different digest:
  conflict"); the caller must bump the version.
Result: a removed upstream artifact **cannot** leave a stale `artifacts/*.yaml` behind (the
promoted dir is built fresh), and re-running a compile is safe.

## 7. Empty / diagnostic candidate (§8 Step 1 item 7)

`active == []` → compile still succeeds (for diagnosis) but sets `releasable=False`,
`candidate_status="diagnostic"`. S1.2/F0.6A enforce "diagnostic ⇒ never served/published";
S1.1 only sets the flag (single source of truth) so downstream refusal is unambiguous.

## 8. Persistence / transaction / determinism boundary

No DB. File writes are staging-then-atomic-rename (no partial dir promoted). The compile is
**fully deterministic** — no network, model, clock, or random input feeds the
`candidate_digest` (DoR §9). `compiled_at` may still be recorded in `pack.yaml` but never
enters the reproducible digest.

## 9. Authorization / tenancy / privacy / egress

None new — the compiler is a pure Tier-B build-plane function over already-governed ACTIVE
artifacts (model-free). No source text, credentials, or tenant data added to logs or manifest.

## 10. Tests mapped 1:1 to acceptance (positive / negative / near-miss / migration / packaging)

| Acceptance (item) | Test |
|---|---|
| **#1** shuffled input → byte-identical ctx + same `candidate_digest` | `test_shuffled_input_same_digest_and_bytes` |
| **#1** different work dir → same `candidate_digest` | `test_different_workdir_same_digest` |
| digest excludes `compiled_at` (two times → same digest) | `test_candidate_digest_excludes_timestamp` |
| **#2** stale artifact from a prior compile is gone after recompile | `test_removed_artifact_absent_after_fresh_write` |
| **#2** partial/failed staging never promotes | `test_staging_failure_leaves_target_untouched` |
| idempotent recompile (same digest) is a no-op success | `test_recompile_same_digest_idempotent` |
| same version, different content → `CandidateDigestConflictError` | `test_same_version_different_digest_conflicts` |
| **#3** manifest lists every input artifact id+digest | `test_input_inventory_exact` |
| **#3** manifest lists every emitted file + bytes + sha256 | `test_output_inventory_matches_disk` |
| **#7** empty compile → `releasable=False`, `candidate_status='diagnostic'` | `test_empty_candidate_not_releasable` |
| v1 pack still loads (compat) | `test_v1_manifest_loads_in_compat_mode` |
| existing write/load round-trip + `verify_pack` stay green | existing `test_compiler.py` suite |

Coverage ≥85% on changed compiler/manifest code; branch + negative (conflict, empty, staging
failure) covered.

## 11. Evaluation cases & critical gate

Determinism is the critical gate: `test_shuffled_input_same_digest_and_bytes` must pass (a
non-deterministic compile blocks the whole platform, §17 stop condition). No model-judged
cases (deterministic unit).

## 12. Evidence bundle (§14) & DoD

`verify-audit` PASS (ruff/mypy/pytest≥85%/boundary/CK/src); the determinism, fresh-write,
inventory, and empty-candidate tests green; a shuffled-order + different-workdir digest proof;
the manifest-v2 schema diff; confirmation existing packs load in compat mode; "unrelated
changes excluded." **DoD:** items #1/#2/#3/#7 closed with can-pass/can-fail tests; the
candidate is reproducible, fresh, exactly inventoried, and empty→non-releasable.

## 13. Compatibility, migration position, kill criteria, deferred

- **Migration position:** introduces manifest **v2**; v1 remains loadable (compat). Existing
  on-disk `packs/commercial_analytics/*` are not force-migrated; recompiling regenerates v2.
- **Kill criteria:** if a reproducible `candidate_digest` cannot be achieved without a broad
  canonical-serialization rewrite, stop and fold the digest into the Step-5 compiler-v2 unit;
  ship #1/#2/#3/#7 minus digest-addressing rather than expand scope.
- **Explicitly deferred:** digest-addressed *write-once candidate store* + release-registry
  mapping (F0.6A); runtime load/verify (S1.2); eval receipt + `PackEvalSummary` demotion (S1.3).
