# Mini-spec — S1.1: Deterministic, fresh, digest-addressed compile + exact inventory

**Unit:** S1.1 (Platform Step 1, unit 1 of 3) · **Owner:** BE · **Depends on:** none ·
**Blocks:** S1.2 (manifest-driven load), S1.3 (eval receipt), and every later compile step.
**Baseline SHA:** `1dc26ca` (Step-0 architecture baseline) · **Review SHA:** *this commit*.
**Accepted contracts:** `ontowiz-spec` PackManifest (pre-baseline) → **manifest v2** (this unit);
`ontowiz-ctx` serializer/parser (unchanged). **Anchors:** DOMAIN_PACK_PLATFORM §5.6
(deterministic compiler, items 1–10 + behavior), §8 Step 1 (all eight gaps), §15 leak tests
(undeclared / missing / stale / post-eval-changed / duplicate-normalized file), §17 stop
conditions (non-deterministic compiler), §18 anti-patterns (input order → digest/bytes;
counts-only inventory; write into existing version dir; reseal after eval), §13 DoR (16 items);
ADR-018/019.

## 0. Spec-red closure (the five review findings)

This revision exists to close the CHANGES-REQUIRED review of the prior draft. Each finding is
closed by a precise envelope rule **and** a can-fail test (see §10); nothing below is asserted
in prose without a falsifying test:

| # | Finding | Closure | Rule | Test(s) |
|---|---|---|---|---|
| 1 | same digest, different bytes (volatile `compiled_at` inside candidate) | no volatile field lives in the candidate; whole dir is byte-identical across builds | §5.1, §5.4 | T1a/T1b/T1c |
| 2 | `output_inventory` self-referential / seal cycle | inventory lists **payload only**; `pack.yaml`/`pack.sig` are control files; fixed verify order | §5.2, §5.3, §6.4 | T2a–T2d |
| 3 | duplicate output paths (id-only filenames) | reject duplicate logical identity; injective, case-folded path guard **before** staging | §6.2 | T3a/T3b/T3c |
| 4 | v1 migration contradicts conflict policy | `write_pack` never migrates in place; a v1 target at the same version **conflicts**; migration needs a version bump (authorized in-place migrate deferred) | §6.5, §13 | T4a/T4b |
| 5 | fresh writer lacks fs-safety + concurrency acceptance | validated `name`/`version`, reparse/traversal refusal, atomic create-or-fail promote | §6.1, §6.3, §6.6 | T5a–T5e |

## 1. Objective & named consumer

The compiler emits a **byte-identical, reproducibly digest-addressed candidate regardless of
input order, working directory, or wall-clock time**, written **fresh** (no artifact removed
upstream can survive on disk), carrying an **exact input + output inventory** in the manifest; a
zero-artifact ("empty diagnostic") compile is produced but **flagged non-releasable**.
Consumers: S1.2's runtime loader (loads the declared inventory, verifies the candidate digest
and seal before serving) and S1.3's eval receipt (keyed by `candidate_digest`).

## 2. In-scope / out-of-scope

**In:** `compile_pack` stable ordering + duplicate-identity rejection; a reproducible
`candidate_digest` over an explicit allowlist; **manifest v2** (`input_inventory`,
`output_inventory`, `candidate_digest`, `releasable`, `candidate_status`); an injective
output-path scheme with a pre-stage collision guard; `write_pack` fresh staging → staged-bytes
verification → atomic create-or-fail promote → idempotency/conflict; validated `name`/`version`
and reparse/traversal refusal; the empty-candidate non-releasable flag; a reusable
`verify_candidate_dir` inventory/seal checker used at staging-verify time.

**Out:** runtime load/verify wiring (S1.2 — reuses `verify_candidate_dir`); eval receipt +
`PackEvalSummary` demotion to a derived catalog view (S1.3); the three-manifest resolver +
validation engine (Step 5); a digest-addressed **candidate store vs release registry** split
(F0.6A); an **authorized in-place v1→v2 migrate op** with backup/restore (F0.6A/Step 10). S1.1
keeps the `<name>/<version>/` layout but makes it fresh, reproducible, and conflict-checked.

## 3. Files & ownership (BE)

- **modify** `packages/ontowiz-factory/ontowiz_factory/compiler.py` — stable sort + duplicate
  `(kind,id)` rejection; injective output paths + pre-stage guard; reproducible
  `candidate_digest`; `write_pack` staging → verify → atomic promote → idempotent/conflict;
  `name`/`version` validation + reparse/traversal refusal; new `verify_candidate_dir`; populate
  inventories; `releasable=False` when `active == []`.
- **modify** `packages/ontowiz-spec/ontowiz_spec/pack_manifest.py` — **manifest v2**: add
  `manifest_version`, `input_inventory`, `output_inventory`, `candidate_digest`, `releasable`,
  `candidate_status`; keep `artifact_count`/`artifact_kinds` as derived convenience (not identity);
  `evals` excluded from the candidate identity (S1.3 demotes it).
- **modify** `packages/ontowiz-factory/tests/test_compiler.py` (+ new cases) — every T-row in §10.
- New error types live in `compiler.py`. No files outside these packages + this spec.

## 4. Typed contract changes (manifest v2)

```python
InventoryEntry:  id: str; kind: str; content_digest: str      # one per input artifact
OutputFile:      path: str; byte_count: int; sha256: str       # one per emitted PAYLOAD file
PackManifest (v2 additions):
  manifest_version: int   = 1             # model default 1: an unmarked pack loads as v1; compile_pack sets 2
  candidate_digest: str   = ""            # reproducible content id (see §5); "" only for v1 compat
  input_inventory:  list[InventoryEntry]  = []   # every input artifact, sorted by (kind, id)
  output_inventory: list[OutputFile]      = []   # every emitted PAYLOAD file, sorted by path
  releasable:       bool  = True          # False for empty/diagnostic candidates
  candidate_status: Literal["candidate","diagnostic"] = "candidate"
```

**Errors (all fatal, raised before any promote):** `DuplicateArtifactIdentityError`,
`DuplicateOutputPathError`, `UnsafePackNameError`, `UnsafePackVersionError`,
`UnsafeCandidatePathError`, `StagedCandidateInvalidError`, `CandidateDigestConflictError`.

**Backward compatibility:** v1 packs (no `manifest_version`, or `< 2`) load in compat mode with
empty inventories and `candidate_digest=""`; strict v2 is required for any new compile
(ADR-018: "v1 loading only for explicit migration/non-production compatibility").

## 5. The candidate envelope & reproducibility contract (closes #1, #2)

### 5.1 What is *in* the candidate

The candidate is the directory `<name>/<version>/`. It contains exactly two categories of file:

- **Payload** — the addressable content: `artifacts/<file>.yaml` (governed sources),
  `context.ctx` (compiled L2), `index.l3.ctx` (compiled L3). Every payload file is written
  NFC-normalized, LF line endings, UTF-8, and appears in `output_inventory`.
- **Control** — `pack.yaml` (the manifest) and `pack.sig` (the integrity seal). Control files
  are **never** listed in `output_inventory` and are the *only* non-payload files permitted in
  the directory.

**Constraint: the candidate `pack.yaml` is serialized from an explicit allowlist — no other field
reaches disk.** The candidate manifest serializes **exactly** the digest `core` fields (§5.2) plus
the two deterministically-derived convenience counts `artifact_count`/`artifact_kinds` (both
functions of `input_inventory`, so fixed per content). Every field excluded from `candidate_digest`
is therefore **also omitted from the candidate `pack.yaml`**: the mutable catalog/eval fields
(`evals`, `coverage`, `freshness_days`) and the provenance fields (`compiled_at`,
`compiler_version`, `signed`, `encrypted`, `license_id`) live only in the in-memory model, the
external catalog, or the registration/release event — never in candidate bytes. Because the
serialized set is exactly {digest core} ∪ {deterministic derived counts}, **candidate bytes are a
pure function of the digest**: any field a caller mutates (existing callers already mutate `evals`)
is stripped on write and cannot produce different bytes under the same digest. Implemented as a
pydantic serialization allowlist in `write_pack`, not an ad-hoc field drop. Consequence: repeated
builds of the same inputs produce a **byte-identical directory**, including `pack.yaml` and
`pack.sig`.

### 5.2 `candidate_digest` — reproducible content identity (no self-reference)

```
candidate_digest = sha256( canonical_json(core) ).hexdigest()

core = {                                   # explicit ALLOWLIST — new manifest fields never leak in
  "manifest_version": 2,
  "name": name, "version": version, "domain": domain,
  "author": author, "description": description,
  "layers": [layer canonical json...], "depends_on": [...],
  "input_inventory":  [ {id,kind,content_digest}   sorted by (kind,id) ],
  "output_inventory": [ {path,byte_count,sha256}    sorted by path ],
  "releasable": releasable, "candidate_status": candidate_status,
}

canonical_json(x) = json.dumps(nfc(x), sort_keys=True,
                               separators=(",",":"), ensure_ascii=False).encode("utf-8")
```

`core` reads each payload file's digest **out of `output_inventory`** rather than re-hashing the
files, and it excludes `candidate_digest` itself — so there is **no cycle** and the field is
well-defined. Excluded by construction (denylist, belt-and-suspenders on top of the allowlist):
`candidate_digest`, `compiled_at`, `signed`, `compiler_version`, `encrypted`, `license_id`,
`evals`, `coverage`, `freshness_days`, `artifact_count`, `artifact_kinds`, and any run-id/local
path. `content_digest` for an input artifact = `sha256(canonical_json(artifact.model_dump("json")))`.

### 5.3 `pack.sig` — local byte-integrity seal (an external envelope file)

`pack.sig` is written **last**, after `pack.yaml` is frozen. **Reuse-first (anti-bloat gate):**
it keeps the existing `_pack_digest` construction already in `compiler.py` — sorted
`artifacts/*.yaml` + `context.ctx` + `index.l3.ctx` + `pack.yaml`, each hashed as `filename +
bytes` — rather than a new scheme. That construction is safe here because the §6.2 injective guard
guarantees unique payload basenames, and it is now **reproducible** because §5.1 removed every
volatile value it hashes over.

```
sig = _pack_digest(pack_dir)   # existing helper; covers payload + pack.yaml, excludes pack.sig
```

It covers `pack.yaml` in full (including the stored `candidate_digest` field), so on-disk
tampering with the recorded digest is caught. It does **not** cover `pack.sig` itself. Two
distinct jobs: `candidate_digest` = portable, reproducible *content identity* (envelope-independent);
`pack.sig` = *byte integrity as-written*. `write_pack` and `verify_pack` call the same helper, so
the existing write→verify round-trip stays green under v2.

### 5.4 Stable order

Sort `active` by `(kind.value, id)` before building sections, the L2 doc, the L3 directory, and
both inventories — so shuffled input yields byte-identical `context.ctx` / `index.l3.ctx` and an
identical `output_inventory`.

## 6. Fresh write, injective paths, atomic promote, safety, concurrency

### 6.1 `name` / `version` validation (closes #5, part 1)

Before any path is constructed, validate:
- `name` matches `^[a-z0-9][a-z0-9_-]{0,62}$` else `UnsafePackNameError`.
- `version` matches semver `^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$` else `UnsafePackVersionError`.
- Reject (case-insensitively) Windows reserved device names (`con`, `prn`, `aux`, `nul`,
  `com1..9`, `lpt1..9`) and any trailing dot/space for both tokens.

These patterns exclude `.`, `..`, `/`, `\`, drive letters, and leading `-`, so neither token can
become a traversal or absolute-path component.

### 6.2 Injective output paths (closes #3)

- **Reject duplicate logical identity:** if two inputs share `(kind, id)`, raise
  `DuplicateArtifactIdentityError` (fatal) — §5.6 "duplicate identity … fatal".
- **Filename scheme:** `artifacts/{kind.value}__{safe(id)}.yaml`, where
  `safe(id) = re.sub(r"[^a-zA-Z0-9._-]", "-", id)`. Kind-prefixing makes same-`id`/different-`kind`
  land on distinct paths.
- **Pre-stage collision guard (the guarantee):** compute the normalized relative path for every
  payload file (artifacts + `context.ctx` + `index.l3.ctx`); if any two collide under
  **case-folded** comparison (Windows/macOS are case-insensitive), raise `DuplicateOutputPathError`
  **before staging**. This rejects residual `safe()` collisions and case-fold collisions rather
  than silently overwriting.

### 6.3 Reparse-point / traversal refusal (closes #5, part 2)

Before promote, resolve `dest_root` to its real path and assert `realpath(<name>/<version>)` is
contained within it; if any existing component of the destination is a symlink/junction/reparse
point that escapes `dest_root`, raise `UnsafeCandidatePathError`. Never follow a reparse point
out of the root.

### 6.4 Staging → staged-bytes verification → promote (the write order)

`write_pack` (§5.6 items 8–10):

1. Create a **unique sibling staging dir** under `dest_root/<name>/` via `tempfile.mkdtemp`
   (unique per process; no clock/random needed in product code).
2. Write payload (NFC/LF/UTF-8), then `pack.yaml` (with `candidate_digest` filled, `compiled_at`
   omitted), then `pack.sig`.
3. **Verify the staged bytes** with `verify_candidate_dir` (§6.7). Any failure →
   `StagedCandidateInvalidError`, discard staging, **target untouched**.
4. **Promote** by atomic create-or-fail (§6.6).

### 6.5 Idempotency & conflict (closes #4)

On promote, if `<name>/<version>/` already exists, read its manifest and compare digests:
- existing `candidate_digest` **equals** the staged one → **idempotent success** (discard staging,
  no rewrite);
- existing `candidate_digest` **differs** (including a **v1 target**, whose digest is `""` and is
  therefore always ≠ a real v2 digest) → `CandidateDigestConflictError`.

`write_pack` **never** overwrites or migrates in place. Migrating a v1 pack to v2 therefore
requires a **version bump** (a new `<version>/`); an authorized in-place migrate with
backup/restore is deferred to F0.6A/Step 10 (§13).

### 6.6 Concurrency acceptance (closes #5, part 3)

Two concurrent compiles of the same `(name, version)` each stage into distinct dirs, then race to
promote. Promote is `os.rename(staging → <version>)`, which **fails if the destination exists**
(FileExistsError / non-empty target on Windows and POSIX) — the OS gives us create-or-fail. The
loser catches the failure and re-enters §6.5 against the now-present target:
- same digest → idempotent success (exactly one directory, both callers succeed);
- different digest → `CandidateDigestConflictError`.

No partial or interleaved directory is ever observable; a crash mid-stage leaves only an orphan
staging dir, never a promoted candidate. (POSIX `rename` replaces an *empty* target but fails on a
*non-empty* one; this writer only ever materializes the target by renaming a fully-populated
staging dir, so no empty-target window exists for a racer to replace.)

### 6.7 `verify_candidate_dir(dir)` — the reusable checker (closes #2 enforcement)

Fixed order; any step fails → `False` (or a typed error at staging time):

1. Parse `pack.yaml`; require `manifest_version == 2`.
2. Enumerate real files. Partition into control (`pack.yaml`, `pack.sig`) and everything else.
   Any non-payload file that is **not** a known control file → **undeclared** → fail.
3. Every real payload file appears in `output_inventory` (no **undeclared payload**); every
   `output_inventory` entry exists on disk (no **missing declared** file); each payload
   `sha256`/`byte_count` matches its bytes.
4. Recompute `candidate_digest` from the manifest (§5.2); must equal the stored value.
5. Recompute `pack.sig` (§5.3); must equal the on-disk seal.

S1.2 reuses this verbatim at load time; S1.1 uses it at staging-verify time.

## 7. Empty / diagnostic candidate (§8 Step 1 item 7)

`active == []` → compile still succeeds (for diagnosis) but sets `releasable=False`,
`candidate_status="diagnostic"`. `releasable`/`candidate_status` are inside the digest allowlist,
so a diagnostic and a would-be release can never share a `candidate_digest`. S1.2/F0.6A enforce
"diagnostic ⇒ never served/published"; S1.1 sets the single-source-of-truth flag.

## 8. Persistence / determinism boundary; performance

No DB. Writes are staging-then-atomic-rename (no partial dir promoted; §6.4/§6.6). The compile is
**fully deterministic** — no network, model, clock, or random input feeds the candidate bytes or
`candidate_digest` (DoR §9; §5.1). **Performance/resource (DoR §13):** compile + write is O(total
artifact bytes), single-pass hashing, no artifact held in memory more than once; staging adds one
extra dir write + one `rename`; no added network or subprocess. Bounded by input size, not by
prior on-disk pack count.

## 9. Authorization / tenancy / privacy / egress

None new — the compiler is a pure Tier-B build-plane function over already-governed ACTIVE
artifacts (model-free). No source text, credentials, or tenant data added to logs, manifest, or
seal. No egress.

## 10. Tests mapped 1:1 to acceptance, findings, and leak tests

| Ref | Acceptance / finding / leak | Test |
|---|---|---|
| §5.6-DoD, **#1** | shuffled input → **byte-identical whole dir** (recursive files+bytes) + same digest | `test_shuffled_input_bytes_identical_full_dir` (T1a) |
| §5.6-DoD, **#1** | different work dir + sharded-vs-flattened input → same digest & bytes | `test_different_workdir_and_sharding_identical` (T1b) |
| **#1** | two builds at different times → identical `pack.yaml` **and** `pack.sig` (no volatility) | `test_repeated_build_seal_and_manifest_identical` (T1c) |
| **#2**, §15 | undeclared payload file in dir → verify fails | `test_undeclared_payload_file_rejected` (T2a) |
| **#2**, §15 | declared file missing from dir → verify fails | `test_missing_declared_payload_rejected` (T2b) |
| **#2** | payload byte/digest mismatch → verify fails | `test_payload_digest_mismatch_rejected` (T2c) |
| **#2** | unexpected control file (not `pack.yaml`/`pack.sig`) → verify fails | `test_unexpected_control_file_rejected` (T2d) |
| **#3** | same `id`, different `kind` → two distinct output paths, both written | `test_same_id_different_kind_distinct_paths` (T3a) |
| **#3**, §15 | case-fold normalized-path collision → `DuplicateOutputPathError` before staging | `test_case_fold_output_path_collision_fatal` (T3b) |
| **#3** | duplicate logical `(kind,id)` → `DuplicateArtifactIdentityError` | `test_duplicate_logical_identity_fatal` (T3c) |
| **#4** | recompile v2 over an existing **v1** dir, same version → `CandidateDigestConflictError` | `test_recompile_over_existing_v1_same_version_conflicts` (T4a) |
| **#4** | v1→v2 migration via **version bump** succeeds; v1 dir untouched | `test_v1_migration_requires_version_bump` (T4b) |
| **#5** | unsafe `name` (traversal/reserved/`..`) → `UnsafePackNameError` | `test_unsafe_name_rejected` (T5a) |
| **#5** | unsafe `version` (traversal/non-semver) → `UnsafePackVersionError` | `test_unsafe_version_rejected` (T5b) |
| **#5** | reparse/symlink target escaping root → `UnsafeCandidatePathError` | `test_reparse_target_refused` (T5c) |
| **#5** | concurrent same-digest writers → one dir, both succeed (idempotent) | `test_concurrent_same_digest_one_dir` (T5d) |
| **#5** | concurrent different-digest writers → one promotes, other conflicts | `test_concurrent_different_digest_one_conflicts` (T5e) |
| §8-2 | stale artifact from a prior compile is absent after fresh recompile (version bump) | `test_removed_artifact_absent_after_fresh_write` |
| §6.4 | staged-bytes verification fails → target untouched, no promote | `test_staging_failure_leaves_target_untouched` |
| idem | idempotent recompile (same digest) is a no-op success | `test_recompile_same_digest_idempotent` |
| §8-3 | manifest lists every input artifact id+kind+digest | `test_input_inventory_exact` |
| §8-3 | manifest lists every emitted payload file + bytes + sha256; excludes control files | `test_output_inventory_matches_disk_payload_only` |
| §8-7 | empty compile → `releasable=False`, `candidate_status="diagnostic"` | `test_empty_candidate_not_releasable` |
| compat | v1 pack still loads in compat mode (`candidate_digest=""`) | `test_v1_manifest_loads_in_compat_mode` |
| compat/**amend-1** | a manifest with **no** `manifest_version` field loads as `== 1` (not 2) | `test_absent_manifest_version_loads_as_v1` |
| **amend-2** | non-default `evals`/`coverage`/`freshness_days` on the manifest are stripped on write and cannot change candidate bytes (written `pack.yaml` == default-metadata build, byte-for-byte) | `test_mutable_metadata_stripped_bytes_unchanged` |
| regression | existing write/load round-trip + `verify_pack` stay green | existing `test_compiler.py` suite |

Coverage ≥85% on changed compiler/manifest code; branch + every negative path (each typed error,
staging failure, empty, both concurrency outcomes) covered.

## 11. Evaluation cases & critical gate

Determinism is the critical gate (§17 stop condition "the compiler is not deterministic"):
**T1a, T1b, T1c must pass** — a non-deterministic or non-byte-identical candidate blocks the whole
platform. No model-judged cases (deterministic unit).

## 12. Evidence bundle (§14) & objective DoD

`verify-audit` PASS (ruff/mypy/pytest ≥85%/boundary/CK/src); §10 tests green; a shuffled-order +
different-workdir + repeated-build **full-directory byte-equality** proof (not digest-only); the
manifest-v2 schema diff; the reparse/traversal + concurrency evidence; confirmation existing packs
load in compat mode; "unrelated changes excluded." **DoD:** findings #1–#5 each closed by a named
can-fail test above; acceptance #1/#2/#3/#7 closed; the candidate is reproducible (byte-identical),
fresh, exactly inventoried with a non-self-referential seal, injectively pathed, safe against
unsafe names/traversal/reparse and concurrent writers, and empty→non-releasable.

## 13. Compatibility, migration position, kill criteria, deferred

- **Migration position:** introduces manifest **v2**; v1 remains loadable (compat, §4). Existing
  on-disk `packs/commercial_analytics/*` are **not** force-migrated. Recompiling to a **new
  version** regenerates v2 fresh; recompiling to the **same version** as an existing v1 pack
  **conflicts** and is refused (`write_pack` never migrates in place). An **authorized in-place
  v1→v2 migrate** operation (backup → fresh write → verify → restore-on-failure) is deferred to
  F0.6A/Step 10, which owns "migrate the existing commercial analytics pack."
- **Kill criteria:** if a reproducible `candidate_digest` cannot be achieved without a broad
  canonical-serialization rewrite of every artifact kind, stop and fold the digest into the Step-5
  compiler-v2 unit; ship #1/#2/#3/#7 minus digest-addressing rather than expand scope. (The
  envelope here hashes inventories, not a full re-canonicalization of each YAML, to stay inside
  this bound.)
- **Explicitly deferred:** digest-addressed **write-once candidate store** + release-registry
  mapping (F0.6A); runtime load/verify wiring (S1.2 reuses `verify_candidate_dir`); eval receipt +
  `PackEvalSummary` demotion (S1.3); authorized in-place v1→v2 migrate (F0.6A/Step 10).
