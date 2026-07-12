# Mini-spec — S1.2: Manifest-driven runtime load (no glob, verify-before-load)

**Unit:** S1.2 (Platform Step 1, unit 2 of 3) · **Owner:** BE · **Depends on:** S1.1
(manifest v2 inventory + `candidate_digest` + `releasable`) · **Blocks:** safe MCP/REST pack
exposure (ADR-019), F0.6A release registry.
**Baseline SHA:** `1dc26ca` · **Review SHA:** *this commit* · **Contingent on S1.1** — reconciles
if S1.1's inventory/digest contract changes in review.
**Anchors:** DOMAIN_PACK_PLATFORM §5.10 (release registry & runtime loader), §8 Step 1 items
4–5, §15 leak tests (undeclared/missing/stale/changed/duplicate/withdrawn), invariant 13
("never discover artifacts by glob"); §12.3 stable error codes; DoR §13.

## 1. Objective & named consumer

The runtime loads a pack **only from its declared inventory**, verifying integrity and release
eligibility **before returning any data**, and refuses extra / missing / changed / duplicate /
stale / withdrawn / non-releasable / unknown-schema packs with **stable typed error codes**.
No globbing for runtime truth. Consumer: the per-tenant data plane (REST/MCP), which must
never serve an unattested or withdrawn pack — this unit is the safety gate for MCP exposure.

## 2. In-scope / out-of-scope

**In:** `load_pack` becomes inventory-driven (loads exactly `output_inventory`, refuses
undeclared/stale files) + a `release_verifier` that runs the pre-load checks; `PackRegistry.load`
enforces eligibility; strict-v2 default with an explicit non-production compat mode for v1.
**Out:** the catalog **browse** view (`list_manifests`) and the full digest-addressed
release-registry index → **F0.6A** (noted §10); eval-receipt-based release gating → S1.3/F0.6A;
tenant/authorization checks → the serve plane (F0.3).

## 3. Files & ownership (BE, `packages/ontowiz-runtime/`)

- **new** `ontowiz_runtime/release_verifier.py` — the ordered pre-load checks (below) returning a
  typed result; the single place "is this pack loadable?" is decided.
- **modify** `ontowiz_runtime/registry.py` — `load_pack` loads from `output_inventory` (no
  `artifacts/*.yaml` glob); `PackRegistry.load` calls the verifier before returning; keep the
  existing path-traversal containment (`:72-77`).
- **modify** `ontowiz_runtime/__init__.py` — export the typed loader errors.
- **new** `tests/test_release_verifier.py` + additions to `test_registry.py`.

## 4. Verify-before-load pipeline (§5.10 steps, ordered, fail-closed)

Before returning any artifact data, `release_verifier.verify(pack_dir)`:
1. **Schema/version:** `manifest_version == 2` (else strict-mode `UnsupportedManifestError`; v1
   only loads when `allow_v1_compat=True`, a non-production flag — ADR-018/§5.10).
2. **Eligibility:** `releasable is True` and `candidate_status != "diagnostic"` and lifecycle
   not withdrawn — else `NonReleasablePackError` / `WithdrawnPackError`.
3. **Integrity seal:** `verify_pack(pack_dir)` (pack.sig matches) — else `TamperedPackError`.
4. **Inventory match (exact):** the set of files on disk equals `output_inventory` **exactly** —
   any **missing**, **extra/undeclared**, or **duplicate-normalized** file → `InventoryMismatchError`;
   each declared file's `byte_count` + `sha256` must match — any **changed** file → same error.
5. **Load from the inventory**, not a glob: reconstruct artifacts by iterating
   `input_inventory` (id, kind, content_digest), validating each against its content digest.

Only after all pass does `load_pack` return a `LoadedPack`. Every failure is a typed error with
a stable code the serve plane maps to a refusal (§12.3).

## 5. Typed errors (new, Tier A)

`UnsupportedManifestError`, `NonReleasablePackError`, `WithdrawnPackError`, `TamperedPackError`,
`InventoryMismatchError` — plus the existing `FileNotFoundError` for traversal/missing pack.

## 6. Persistence / determinism / egress

No DB, no network, model-free. Verification is a pure function of the pack directory. No source
text or credentials logged (§12.3) — errors carry codes + the pack id, never file contents.

## 7. Tests mapped 1:1 to acceptance (§15 leak tests)

| Acceptance | Test |
|---|---|
| clean v2 pack loads from inventory (no glob) | `test_v2_pack_loads_from_inventory` |
| **undeclared/stale** file present → refuse | `test_extra_file_refused` |
| **missing** declared file → refuse | `test_missing_file_refused` |
| **changed** file (byte/digest mismatch) → refuse | `test_changed_file_refused` |
| **duplicate** normalized filename → refuse | `test_duplicate_normalized_name_refused` |
| tampered pack.sig → refuse | `test_tampered_seal_refused` |
| non-releasable / diagnostic candidate → refuse | `test_diagnostic_candidate_refused` |
| withdrawn release → refuse | `test_withdrawn_pack_refused` |
| v1 pack refused in strict mode, loads under explicit compat | `test_v1_strict_refuse_compat_allow` |
| path traversal still refused | existing `test_registry` traversal cases stay green |

Coverage ≥85% on changed runtime code; every refusal path has a can-fail test (§5.7 DoD).

## 8. Migration, kill criteria, deferred

- **Migration:** existing on-disk v1 packs are refused by default; the compat flag is
  non-production only. Recompiling under S1.1 yields v2 packs that load strictly.
- **Kill criteria:** if exact inventory verification cannot be met without S1.1's `output_inventory`
  landing first, block on S1.1 rather than approximating with a re-glob.
- **Deferred:** the catalog browse list + release-registry index (replacing `list_manifests`'s
  `*/*/pack.yaml` glob) → F0.6A; until then the browse list is a **non-authoritative view** and
  is **not** a load path (all actual loads go through the verifier).

## 9. DoD

Runtime refuses extra / missing / changed / duplicate / stale / tampered / diagnostic /
withdrawn / unknown-schema packs with stable codes; a clean v2 pack loads from its declared
inventory with no glob; `verify-audit` PASS; evidence bundle per §14.
