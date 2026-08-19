# CONTRACT · Skill bundle — Codex-first, Claude-second (P3.3)

**Status:** FROZEN @ `0b0245c` · Parent: [`P3.0_CONTRACT_FREEZE.md`](P3.0_CONTRACT_FREEZE.md) ·
Implemented by **P3.3** (D5).

`owak skill build --host {codex|claude}` emits a deterministic, uploadable skill bundle that **ships no
trust**. It reuses the kit's determinism machinery rather than reinventing it.

## 1. Determinism — reuse the **generic** ZIP primitives only (corrected by P3.0a #9)

The builder reuses the archive layer's **format-agnostic** determinism primitives — and **only** those:

- Fixed epoch `1980-01-01`, `ZIP_STORED` (no compression entropy), sorted entries, zeroed
  extra/comment, fixed external attributes, UTF-8 flag (`archive.py:422-461`).
- Canonical JSON (`_canonical_json`, `archive.py:204-215`): `sort_keys`, `separators=(",",":")`,
  `allow_nan=False`, NFC-normalised, trailing `\n`.
- Portable-path hardening (`_portable_path`, `archive.py:238-262`).
- Collision + byte guards: `_assert_no_namespace_collisions` (`archive.py:1613`), case-fold collision
  (`:1497`), `_MAX_TOTAL_BYTES`/`_MAX_ENTRY_BYTES` caps.
- The generic build/verify spine: `_build(format_name, …)` (`archive.py:1471`) + `_base_manifest`
  (`:387`) + `_entry` (`:411`) + `verify_archive(expected_format=…)` (`:2135`).

**Do NOT apply candidate-document validation to a skill bundle (correction #9).**
`_validate_candidate_document` (`archive.py:1292`) and `_validate_candidate_inventory` (`:1450`) are gated
to `format == "ontowiz-candidate-pack"` (`verify_archive` `:2241-2243`; `build_candidate_pack` `:1587`) —
a **skill bundle is not a candidate document**, so these MUST NOT run over it.

**Byte-identical rebuilds are required:** the same inputs at the same `0b0245c` produce byte-identical
bundles under shuffle / EOL / repeat.

## 1.1 Skill archive format / version / manifest / verifier (new — correction #9)

The skill bundle is a **new, third `ArchiveFormat`**, parallel to the two that exist today
(`ArchiveFormat = Literal["ontowiz-authoring-workspace","ontowiz-candidate-pack"]`, `archive.py:61-63`):

- **`format`:** `"ontowiz-skill-bundle"`; **`format_version`: `1`** (via `_base_manifest`, `archive.py:395`).
- **Canonical suffix (correction #5):** **`.owskill`** — the single frozen extension for this format (no
  "e.g."). `_build`'s suffix guard (`archive.py:1479`) gains this exact third case; it does **not** reuse
  `.owpack`/`.owworkspace`.
- **Manifest:** a canonical-JSON manifest declaring `format`, `format_version`, the host
  (`{codex|claude}`), the entry table (path/role/media/digest), the **shared-core digest set** (for the
  §2 parity check), and the **required exact `owak` runtime version** (`CONTRACT_RUNTIME.md §2`). No trust
  material (§4).
- **Verifier:** a dedicated `verify_archive(expected_format="ontowiz-skill-bundle")` branch that checks the
  ZIP layout, manifest schema, portable paths, and collision/byte guards — **structural + manifest checks
  only**, with **no** candidate-document validation.

**Host-upload mapping (correction #5).** A single `.owskill` archive is built per host and unpacks to that
host's native skill shape:

| Host (`--host`) | `.owskill` unpacks to | Upload target |
|---|---|---|
| `codex` | a skill directory `<name>/` = `SKILL.md` + `references/` + `scripts/` (glue) + `assets/` + `agents/openai.yaml` — mirrors `adapters/codex/skills/ontowiz-authoring/` | the Codex/ChatGPT **skills** location (a skill folder) |
| `claude` | a skill = `CLAUDE.md` + the same shared `references/`/`scripts/`/`assets/` | **Claude Desktop skill upload** (the P3.4 acceptance path) |

The archive is the deterministic transport; the per-host **unpacked layout** above is what the host loads.
Only the host wrapper differs; the shared core (§2/§3) is byte-identical across both.

## 2. Host ordering & parity (D5)

- **Codex is primary** — built and validated **first**. **Claude is second.** Both wrap **one
  byte-identical shared core** — the host-agnostic bundle files (`scripts/` glue + `references/` +
  `assets/` + runtime declaration); the engine itself is Artifact A, outside the bundle (§3).
- Grounded in the existing dual surface: `adapters/codex/skills/ontowiz-authoring/`
  (`SKILL.md`, `references/protocol.md`, `agents/openai.yaml`) and `adapters/claude/CLAUDE.md`
  (`ClaudeAdapterSession`, which already states "identical to Codex").
- **Parity is test-enforced:** the shared core files are **byte-for-byte equal** across the two bundles;
  only the host wrapper (skill manifest / guidance file / agent descriptor) differs. A parity test asserts
  the shared-core digests match between `--host codex` and `--host claude` outputs.

`Supersedes: P3_REVISED_MINISPEC.md §5.1 host token "{claude|openai}" — frozen "{codex|claude}", Codex-first.`

## 3. Bundle layout (thin — Artifact B; corrections #6, #9)

Per host, a deterministic **thin** bundle. The engine, `AuthorityHostClient`, transports, and deps are
**not** in the bundle — they are the separately-installed **Artifact A** `owak` runtime
(`CONTRACT_RUNTIME.md §1`). The bundle contains **only**:

- **Host wrapper (differs per host)** — Codex: `SKILL.md` (frontmatter `name`/`description`) +
  `agents/openai.yaml`. Claude: `CLAUDE.md`. (Mirrors the existing `adapters/**` layout.)
- **`scripts/` — thin host glue** that invokes the **installed** `owak` runtime; **no copy** of the engine,
  client, or transports, **no keys**. (Shared, host-agnostic.)
- **`references/`** — protocol/usage docs (prose only). (Shared.)
- **`assets/`** — JSON schemas + the pinned `ontowiz-spec` snapshot (`src/ontowiz_spec/pinned_v0_1/*`,
  vendor-locked). (Shared.)
- **Runtime declaration** — the **required exact `owak` runtime version** the bundle depends on
  (`CONTRACT_RUNTIME.md §2`). **No wheels, no pinned dependency set, no engine** are carried in the bundle.

The **shared core** for the §2 parity check is the host-agnostic set (`scripts/` glue + `references/` +
`assets/` + the runtime declaration); only the host wrapper differs between the Codex and Claude bundles.

## 4. Exclusion contract (inherited from `.owpack`, material-not-words)

The bundle **MUST exclude**, as data/structure:

- keys, credentials, host admin, credential-minting, key rotation, journal-attestation code;
- held-out vaults, protected held-out cases/answers/rubrics/mappings, private receipts, protected
  scorer/receipt providers;
- raw sources beyond the transfer contract.

The bundle **MAY contain** public `dev`/`regression` eval cases and prose that *mentions* "credential",
"vault", or "held-out" — keywords are not violations (freeze index §7). The boundary test extends
`tests/evaluation/test_evaluation_repository_boundary.py` to scan the **built bundle** for actual protected
material.

## 5. What the built skill can and cannot do

- **Can:** resume, register-source, record-evidence, propose, confirm, update-session, withdraw-source,
  validate, checkpoint (`.owworkspace`), package (candidate `.owpack`) — always candidate-only, always
  against an **external** authority host over the wire protocol.
- **Cannot (structurally):** install/replace authority, mint credentials, hold keys, attest journals,
  approve, activate, release, serve, or access/freeze/score protected held-out evaluations. The forbidden
  set is the CLI's (`CONTRACT_CLI.md §4`); the bundle exposes no path around it.

## 6. Test obligations (P3.3, red→green)

1. Byte-identical rebuild (shuffle/EOL/repeat) per host.
2. Shared-core parity between `--host codex` and `--host claude`.
3. Boundary scan of the built bundle: no protected material as data/structure; prose keywords allowed.
4. Clean-environment acceptance (`CONTRACT_RUNTIME.md §3`) installs Artifact A, then runs the full loop
   from the thin bundle against it.
5. Determinism reuse asserted (the builder calls the **generic** `archive.py` primitives; no parallel
   ZIP/JSON path).
6. **Format/verifier (correction #9):** the bundle verifies under
   `verify_archive(expected_format="ontowiz-skill-bundle")`, and **candidate-document validation is not
   applied** — the skill format's verifier runs structural/manifest checks only.
7. **Thin bundle (correction #6):** the bundle contains no wheels, no pinned dependency set, and no copy of
   the engine/client/transports; it declares the required exact `owak` runtime version.
