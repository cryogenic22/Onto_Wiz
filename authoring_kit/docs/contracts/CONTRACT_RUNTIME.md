# CONTRACT · Runtime & dependency matrix (P3.3)

**Status:** FROZEN @ `0b0245c` · Parent: [`P3.0_CONTRACT_FREEZE.md`](P3.0_CONTRACT_FREEZE.md) ·
Implemented by **P3.3** (NB1).

**Two-artifact runtime model (correction #6 — frozen, no longer "pinned download *or* vendored wheels").**
P3 ships **two** separate artifacts, not one:

- **Artifact A — the `owak` runtime.** The engine + `AuthorityHostClient` + transports + the four runtime
  dependencies, **installed separately at an exact version** by the operator (out-of-band, e.g.
  `pip install "ontowiz-authoring-kit==<exact>"` resolving exact, hash-pinned deps). Exact-version pinned;
  not carried inside the skill.
- **Artifact B — the thin skill bundle.** The portable, uploadable host wrapper + `references/` + `assets/`
  (schemas + pinned spec) + a `SKILL.md`/`CLAUDE.md` that **declares the required exact `owak` runtime
  version**. It carries **no wheels, no vendored deps, no engine copy** — it *depends on* Artifact A being
  installed. Portability comes from staying thin.

This resolves the earlier ambiguity: **exact-version install is Artifact A's job; the skill bundle vendors
nothing.** Dependency presence is **never assumed** — it is provided by installing Artifact A at the
declared version, proven by the clean-environment acceptance test (§3).

## 1. Supported runtime (frozen from `pyproject.toml`)

- **Python floor:** `>=3.11` (`pyproject.toml:9`; `[tool.mypy] python_version = "3.11"` `:54`;
  `[tool.ruff] target-version = "py311"` `:66`). Development machine is 3.13.x; the floor, not the dev
  interpreter, is the contract.
- **Runtime dependencies** (`pyproject.toml:10-15`) — **today pinned only by floor**, which the skill
  contract tightens (§2):

  | Package | Repo spec (`0b0245c`) | Skill contract |
  |---|---|---|
  | `cryptography` | `>=42.0` | exact-pinned version + hash |
  | `jsonschema` | `>=4.22` | exact-pinned version + hash |
  | `pydantic` | `>=2.0` | exact-pinned version + hash |
  | `PyYAML` | `>=6.0` | exact-pinned version + hash |

- **Vendored, byte-frozen (not a pip dep):** `src/ontowiz_spec/pinned_v0_1/*`, verified by
  `tools/verify_vendor_lock.py` against `locks/vendor-origin.json` (CI: `.github/workflows/quality.yml:28`).
  The skill bundle carries this pinned snapshot per `CONTRACT_SKILL_BUNDLE.md`; it is **not** re-fetched.

## 2. Dependency provisioning — via Artifact A, not the bundle (correction #6)

- **Artifact A (the `owak` runtime)** declares the **runtime/dependency matrix**: Python floor + **exact**,
  hash-pinned dependency versions (not `>=`) — the material tightening over the repo's floor-only specs
  today. Its install is the single, explicit provisioning step (a pinned requirements set with hashes).
- **Artifact B (the thin skill bundle)** provisions **nothing**: no wheels, no pinned requirements, no
  network fetch. It only **declares the exact `owak` runtime version it requires** and fails closed if the
  installed runtime is absent or a different version.
- No dependency is added beyond the four runtime deps above. The one-of ambiguity ("pinned download *or*
  vendored wheels in the bundle") is **resolved**: exact-version install lives in Artifact A; the bundle
  carries none of it.

## 3. Clean-environment acceptance test (frozen)

P3.3 ships a test that, from a **fresh environment with none of the four deps present**:

1. Installs **Artifact A** (the `owak` runtime) at its declared **exact** version with hash-pinned deps —
   the only provisioning step — then loads **Artifact B** (the thin skill bundle) against it and asserts the
   bundle's required runtime version matches the installed one (mismatch → fail closed).
2. Runs the full loop end-to-end through the public product path:
   `resume → register-source → record-evidence → propose → confirm → update-session → validate →
   checkpoint → package`, against a reference host over the wire protocol.
3. Produces a real `.owworkspace` (`checkpoint`) and a candidate `.owpack` (`package` → `verify_archive`,
   `archive.py:2135`).
4. Fails **closed** if any dep is missing/unpinned or if provisioning reaches outside the declared set.

## 4. Error taxonomy touching the runtime

- **`E_AUTHORITY_UNAVAILABLE`** (D6) — unprovisioned/unreachable host, missing protected config, server-pin
  mismatch, transport down, or timeout. Distinct from `E_AUTHORIZATION` (`adapters.py:95`). Raised from the
  transport/config layer via `AuthorityTransportError` (`CONTRACT_IPC_WIRE.md §5`).
- The evaluator error enum (`evaluator.py:38-52`, 13 codes incl. `E_PREREG_UNAPPROVED` `:249`,
  `E_VAULT_ISOLATION_UNPROVEN` `:284`) is **out of P3's runtime path** — the skill ships no runnable
  evaluator (evaluation stays contract-only, `docs/reviews/EVALUATION_FIREBREAK.md`). Listed here so the
  reviewer knows the skill's runtime does **not** depend on a held-out evaluator being present.

## 5. Quality ratchet (unchanged, must not regress)

- `ruff` (`[tool.ruff.lint] select = ["A","B","E","F","I","N","SIM","UP","W"]`, `pyproject.toml:70`).
- `mypy --strict` over `ontowiz_spec`/`ontowiz_authoring`/`ontowiz_evaluator` (`pyproject.toml:53-57`).
- `pytest -q --strict-markers` (`pyproject.toml:34`); coverage `fail_under = 80.77` branch-mode
  (`pyproject.toml:42-51`), rising toward 85% on new P3 code.
- New P3 code lands under these same gates; the pinned vendor namespace stays omitted from coverage
  (`omit = ["src/ontowiz_spec/pinned_v0_1/*"]`, `:45,:51`).
