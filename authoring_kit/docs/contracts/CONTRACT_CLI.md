# CONTRACT · `owak` CLI surface (P3.2)

**Status:** FROZEN @ `0b0245c` · Parent: [`P3.0_CONTRACT_FREEZE.md`](P3.0_CONTRACT_FREEZE.md) ·
Implemented by **P3.2**.

The `owak` console script (`ontowiz_authoring.cli:main`, `pyproject.toml:26`) today exposes only
`workspace init/status/validate` (`cli.py:24-47`). P3.2 promotes the deterministic authoring loop to
stable CLI verbs so the skill has a safe script surface, **without** exposing any trust administration.

## 1. Frozen verb set

Each verb runs through `AdapterSession` with the `AuthorityHostClient` as `trust_provider`. Mutations
additionally pass a host-issued credential as `trust=` (§5). "Op" is the existing `AdapterOperation`
(`adapters.py:81-91`) unless marked **new**.

| Verb | Adapter op | Credential | Grounding |
|---|---|---|---|
| `owak resume` | `resume` | none (needs provider) | `ResumeCommand` `adapters.py:107` |
| `owak register-source` | `register_source` | host credential | `RegisterSourceCommand` `:111`; engine `authoring.py:866` |
| `owak record-evidence` | `record_evidence` | host credential | `RecordEvidenceCommand` `:117`; engine `:1065` |
| `owak propose` | `propose` | host credential | `ProposeCommand` `:123`; engine `:1136` |
| `owak confirm` | `confirm` | host credential | `ConfirmCommand` `:135`; engine `:1340` |
| **`owak update-session`** | `update_session` | host credential | `UpdateSessionCommand` `:141`; engine `:1452` (D3) |
| **`owak withdraw-source`** | `withdraw_source` | host credential | `WithdrawSourceCommand` `:149`; engine `:1004` (D3) |
| `owak validate` | `validate` | none (needs provider) | `ValidateCommand` `:155`; `validate_authoring` `:1787` |
| `owak package` | `package` | none (needs provider) | `PackageCommand` `:159`; `build_candidate_pack` `archive.py:1573` |
| **`owak checkpoint`** | **`export_workspace` (new)** | none (needs provider) | D4 — see §3 |

`update-session` takes `stage`, `last_delta_id`, `open_question_ids`, `next_mission`
(`Stage = discover|scenario|challenge|ratify`, `adapters.py:80`). `withdraw-source` takes `source_id` and a
timezone-aware `withdrawn_at`.

## 2. Request construction & CAS

- The CLI builds an `AdapterRequest` (`format:"ontowiz-adapter-request"`, `format_version:1`, safe
  `request_id`, exact `workspace_id`, one discriminated `command`; `adapters.py:177-191`).
- **Every command except `resume` requires `expected_revision`** (optimistic CAS,
  `mutation_and_checkpoint_commands_use_cas`, `adapters.py:187-191`). `checkpoint` is non-`resume` and so
  MUST carry `expected_revision`.
- On `E_STALE` / `E_CONFLICT` / interruption the CLI discards conversational assumptions and re-`resume`s
  from verified disk/provider high-water (per `references/protocol.md`).

## 3. `owak checkpoint` — the one new kernel op (B4 / D4)

- Adds a **read-only, provider-converged `export_workspace` `AdapterOperation`** plus its command model to
  `adapters.py`, converging on **`build_workspace_archive`** (`archive.py:1508`,
  signature `(workspace, out, *, source_profile, as_of, target_client_boundary=None, trust_provider=None)`).
- Emits a **real `.owworkspace`** archive. The CLI **MUST NOT** call private archive helpers directly — it
  goes through the new adapter op, exactly as `package` goes through `build_candidate_pack`.
- Read-only: it takes no credential (needs the provider for converged snapshot only) and performs no
  mutation.
- **Exempt from the readiness gate (§3a):** `checkpoint` **may preserve an incomplete workspace** — it
  snapshots in-progress state even while blocking questions remain.

## 3a. Readiness gate — per-verb behaviour (correction #1)

One shared readiness gate governs the loop verbs (`P3.0_CONTRACT_FREEZE.md §6a`; reuses `compile_questions`
blocking questions, `authoring.py:1796-1901` — no parallel validator):

| Verb | Behaviour under open blocking questions |
|---|---|
| `owak resume` | **reports** the blockers (surfaces `AdapterQuestion(blocking=True)` in its snapshot); does not fail |
| `owak checkpoint` | **preserves** an incomplete workspace (exempt); succeeds |
| `owak validate` | **MUST fail** while any blocking question remains (`E_VALIDATION`) |
| `owak package` | **MUST fail** while any blocking question remains (`E_VALIDATION`) |

Every `DecisionContract` must carry linked **dev and regression** evaluation coverage for the gate to pass.
F1 proves this before the Signoile demo.

**Seam (authority binding clarification).** The gate is a **single shared readiness function** (or explicit
`require_ready` mode) invoked **only** by the `validate` command path and `build_candidate_pack` — **never**
inside `validate_authoring`/`AdapterSession._snapshot`, so `resume` and `checkpoint` never fail on open
blocking questions.

## 4. Forbidden verbs (test-asserted ABSENT)

The CLI MUST expose **none** of the following, and P3.2 ships a test asserting their absence (extending the
adapter-boundary posture in `tests/evaluation/test_evaluation_repository_boundary.py`):

- `authority`, `install-authority` (kernel `install_signed_authority` `authoring.py:789` stays unexposed)
- `advance-authority` (correction #3 — authority administration; the authoring client hard-refuses method 9
  and it is off the wire allowlist. Install / rotate / advance run on a **separate administrative client and
  channel**, never the `owak` authoring CLI)
- `grant`, `sign`, `mint-credential`, `rotate-key`, `attest-journal`
- `approve`, `activate`, `release`, `serve`, `promote`
- any `--unsigned` or `--local-authority` flag; any local credential issuance
- any evaluator-custodian verb (`evaluate`, `freeze-heldout`, `score-heldout`, `vault-status`)

## 5. Credential handling (Gate 3 — frozen)

- A mutation's credential is obtained by sending **only** the public `AuthoringIntent`
  (`AdapterSession.prepare_intent(request)`, `adapters.py:375`) to the host, then wrapped in a **fresh**
  `AuthoringTrustContext` and passed **in-process** as `execute(request, trust=...)` (`adapters.py:591`).
- The credential MUST NEVER appear in `AdapterRequest`, `argv`, environment variables, logs, temporary
  files, or on disk. `AdapterRequest` is credential-free by construction (`:178`); responses stay redacted
  (`adapter_response_bytes`, `:307`).
- **State it accurately (correction #2):** the credential **does** transit the **authority IPC** channel
  transiently (issuance + `authenticate_actor`), held only in client memory — but it **never** transits the
  **adapter** protocol. The CLI passes it to the kernel in-process only; the two protocols are separate
  (`CONTRACT_IPC_WIRE.md §1, §4`).
- **`owak confirm` flow (correction #2):** `owak` submits the exact intent → the **host** obtains approval
  through a **separate human UI/session** → the host returns the **intent-bound credential** to the
  **waiting keyless CLI** → `owak confirm` **applies** it. Full sequence frozen in `CONTRACT_AUTHORITY.md §5`.
  If approval never returns, the CLI does not confirm — it returns to resume/recovery, never fabricating or
  replaying a confirmation.

## 6. Output & exit codes

Match the existing CLI idiom (`cli.py:50-100`): one deterministic JSON line per invocation
(`json.dumps(..., allow_nan=False, ensure_ascii=False, separators=(",",":"), sort_keys=True)`), errors as
`{"ok":false,"error":{"code":...,"message":...}}` on stderr, typed non-zero exit codes.

- Existing workspace codes are preserved: `0` ok; `3` `E_WORKSPACE_CONFLICT`; `4` `E_WORKSPACE_INVALID`;
  `5` `E_WORKSPACE_IO` (`cli.py:82-99`).
- Adapter-surfaced errors map from `AdapterErrorCode` (`adapters.py:92-100`): `E_REQUEST_INVALID`,
  `E_WORKSPACE_MISMATCH`, `E_AUTHORIZATION`, `E_STALE`, `E_CONFLICT`, `E_VALIDATION`, `E_OPERATION_FAILED`,
  plus the new **`E_AUTHORITY_UNAVAILABLE`** (D6). Each maps to a distinct, stable exit code frozen in P3.2
  (no reuse of `0`; `E_AUTHORITY_UNAVAILABLE` distinct from `E_AUTHORIZATION`). Messages stay redacted —
  no host paths, keys, or tracebacks.
- **`E_AUTHORITY_UNAVAILABLE` survival (correction #7).** The CLI catches `AuthorityClientError` /
  `AuthorityTransportError` explicitly — both from a verb executed through `AdapterSession` (which already
  maps it, `CONTRACT_IPC_WIRE.md §5`) and from client construction / config resolution that happens
  **before** any `AdapterSession` call (missing/unreadable/writable config, bad pin, unreachable endpoint) —
  and emits `E_AUTHORITY_UNAVAILABLE` with its own exit code. It is never collapsed into `E_AUTHORIZATION`
  or a generic failure.
