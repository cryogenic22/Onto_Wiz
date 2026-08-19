# CONTRACT · Authority / keyless `AuthorityHostClient` (P3.1)

**Status:** FROZEN @ `0b0245c` · Parent: [`P3.0_CONTRACT_FREEZE.md`](P3.0_CONTRACT_FREEZE.md) ·
Implemented by **P3.1**.

Trust stays **external**. The CLI/skill is a thin **keyless client** to a separately administered
authority host. This contract pins the exact provider surface the client must implement and the discipline
it must obey. The transport that carries these calls is frozen separately in
[`CONTRACT_IPC_WIRE.md`](CONTRACT_IPC_WIRE.md).

## 1. `AuthorityHostClient` — posture (D1)

- **Out-of-process proxy** implementing the **entire** `AuthoringTrustProvider` Protocol (§2). The kernel
  calls provider methods **synchronously during** a mutation (`AdapterSession._dispatch`, `adapters.py:473`;
  `build_candidate_pack(..., trust_provider=)`, `archive.py:1573`), so a **partial** client cannot work.
- **Keyless.** The client holds **no** signing key, credential-minting secret, or authority high-water
  state. It authenticates to the host and forwards calls; it never *is* the authority.
- **One client, pluggable transport — local IPC is the P3 target.** The `AuthorityHostClient` runs over
  **authenticated local IPC** (named-pipe on Windows / UDS on POSIX), which **P3.1 implements**. An HTTPS
  production transport is **future / out of P3** (correction #8); the transport stays a swappable channel
  beneath the client so it can be added later without touching the client.
- **`trust_provider=` identity.** `AdapterSession` is constructed with the client as `trust_provider`
  (`adapters.py:323-334`); mutations require an `AuthoringTrustContext` whose `provider` **is** that same
  instance (`_trusted_mutation`, `adapters.py:454-460`). The client instance is the provider identity.

## 2. Frozen provider surface — the real nine methods

Verbatim from `AuthoringTrustProvider` (`authoring.py:408-463`). The client MUST implement **all nine** for
Protocol conformance, signature-for-signature; it MUST NOT add, drop, or rename methods. **Method 9
(`advance_authority`) is administration-only — see the carve-out below.**

| # | Method | `authoring.py` | Role |
|---|---|---|---|
| 1 | `authority_high_water(workspace_id) -> AuthorityHighWater` | `:411` | externally protected pinned authority state |
| 2 | `authoring_state(workspace_id) -> AuthoringProviderState` | `:414` | finalized revision + ≤1 pending transaction |
| 3 | `authenticate_actor(credential, *, expected_intent_digest, now) -> ActorCapability` | `:417` | verify proof-of-possession, freshness, nonce |
| 4 | `authenticate_recovery(identity, authorization) -> ActorCapability` | `:426` | reconstruct actor from provider-held state |
| 5 | `reserve_transaction(identity) -> None` | `:433` | atomically reserve the exact next transaction |
| 6 | `authorize_recovery(identity) -> RecoveryAuthorization` | `:439` | authorize only the exact pending txn / cleanup |
| 7 | `finalize_transaction(identity) -> None` | `:445` | atomically finalize the pending txn, idempotently |
| 8 | `abort_reserved_transaction(identity) -> None` | `:451` | abort only a reserved, unapplied, unjournaled txn |
| 9 | `advance_authority(*, expected, replacement) -> None` | `:457` | compare-and-advance monotonic authority state |

**Credential issuance is out-of-band, not a tenth method.** For a mutation the kernel builds a public
`AuthoringIntent` via `AdapterSession.prepare_intent(request)` (`adapters.py:375`, returns `None` for
`resume`/`validate`/`package`). That intent — and **only** that intent — is sent to the host, which issues
an `OperationCredential`. The credential is placed in a fresh `AuthoringTrustContext`
(`{provider, credential}`, `authoring.py:466-471`) and passed to `execute(request, trust=...)`
(`adapters.py:591`). The host later verifies it via `authenticate_actor` (method 3).

**Two credential paths — state them accurately (correction #2).** "Out-of-band" is relative to the
**adapter** protocol only. `AdapterRequest`/`AdapterResponse` **never** carry a credential
(`AdapterRequest` docstring `adapters.py:178`; deterministic redacted response `:307`) — the credential
reaches the kernel **in-process** as `trust=`. The **authority IPC**, by contrast, **necessarily transmits
the exact `OperationCredential` transiently**: the issuance exchange returns it host→client, and
`authenticate_actor` (method 3) sends it client→host for verification. On the wire it is protected in
transit and never logged or persisted (`CONTRACT_IPC_WIRE.md §4`).

**Administration carve-out — method 9 hard-refuses (correction #3).** `advance_authority` is authority
**administration** (compare-and-advance the monotonic high-water). In the kernel it is reached **only**
during `install_authority` journal recovery (guard `authoring.py:3181`; call `:3196`), **never** in the
authoring loop (`resume`/`register-source`/`record-evidence`/`propose`/`confirm`/`update-session`/
`withdraw-source`/`validate`/`package`/`checkpoint`). Therefore the authoring
`AuthorityHostClient.advance_authority(...)` **hard-refuses** (raises a typed `AuthorityAdministrationError`)
and `advance_authority` is **excluded from the authority wire allowlist** (`CONTRACT_IPC_WIRE.md §1`) — it
can never be forwarded over the authoring channel. Authority administration (install / rotate / advance) is
a **separate administrative client and channel**, out of P3.

**Correction (D2 / §4 of the freeze index):** r2 prose listed `attest_journal`/`verify_journal` and a
provider-level `prepare_intent`. None exist on the Protocol at `0b0245c`. The frozen surface is the nine
methods above plus the out-of-band issuance exchange — nothing more.

## 3. Which operations need a credential

Frozen from the kernel dispatch (`adapters.py:375-589`):

| Verb / op | Needs provider? | Needs `OperationCredential`? |
|---|---|---|
| `resume`, `validate`, `package`, `checkpoint`(new) | **Yes** — calls `get_workspace_revision`/`load_session_state`/`validate_authoring`/`build_*` | **No** (`prepare_intent` returns `None`) |
| `register-source`, `record-evidence`, `propose`, `confirm`, `update-session`, `withdraw-source` | Yes | **Yes** — mutation trust context required (`_trusted_mutation`, `:454`) |

**Consequence (explicit):** read-only verbs still **require a live provider** (they read
provider-converged high-water); they simply need no credential. The CLI therefore **always** constructs the
client; only mutations additionally request a credential.

## 4. Interruption discipline — recover, never replay

- A transport error or timeout raises a typed **`AuthorityTransportError`** (frozen in
  `CONTRACT_IPC_WIRE.md`), surfaced to the CLI as **`E_AUTHORITY_UNAVAILABLE`** (D6).
- On interruption the client/CLI **returns to the resume/recovery flow** (`authorize_recovery` /
  `authenticate_recovery`, methods 6 & 4) and **never blindly replays a mutation.**
- A **reserved-but-unfinalized** transaction is reconciled through recovery
  (`reserve_transaction`/`authorize_recovery`/`finalize_transaction`/`abort_reserved_transaction`), not
  re-issued. The kernel's journal crash-recovery already converges **without persisting any trust
  material** (`_recover_transactions`, a Gate-5 P1 fix); the client MUST NOT weaken that by caching or
  reconstructing authority state locally.

## 5. Authentication & candidate ratification (corrected by P3.0a — #1, #8)

- **Local demonstration (the P3 target):** the authority host runs under a **separate service identity**;
  its keys + high-water state are **ACL-protected** from the drafting principal (unreadable/unwritable by
  it). The client authenticates as a workload/proposer principal; **host↔client mutual auth** (client
  verifies the host via a configured **server pin**). Same-user OS identity is **rejected** as sufficient.

- **Candidate ratification is a host-side human step — NOT a kernel `proposer ≠ confirmer` invariant
  (correction #1).** The kernel does **not** verify that the confirmer is a *distinct principal* from the
  proposer. `_validate_confirmation_actor` (`authoring.py:2137-2148`) checks only that the confirmer
  **holds the target owner role** (`:2145`) **and an allowed confirmer role** (`:2147`) inside the same
  workspace / client boundary — **role membership, not identity distinctness.** Separation of duty is
  therefore a **host + operational** control, frozen as: the host authenticates **candidate ratification
  through a separate authenticated human confirmer session** and issues the confirmation
  `OperationCredential` **only to that session**, which is **unavailable to the drafting agent**.
  `owak confirm` remains the **execution path** that applies the host-authorized confirmation; it does not
  itself prove distinctness. **Do not claim the kernel enforces proposer ≠ confirmer.**

- **Confirmation flow (exact sequence — correction #2):**
  1. `owak` builds and **submits the exact public intent** — `AdapterSession.prepare_intent(confirm_request)`
     → `AuthoringIntent` (`adapters.py:375`; `prepare_confirmation_intent`, `authoring.py:1316`) — to the
     host. Nothing but the intent leaves the client.
  2. The **host obtains approval through a separate human UI/session** (the distinct confirmer principal),
     out of band from the drafting agent.
  3. **After approval, the host returns the intent-bound `OperationCredential`** — bound to that exact
     intent digest — to the **waiting keyless CLI** (held in memory only).
  4. **`owak confirm` applies it:** `execute(confirm_request, trust=AuthoringTrustContext(client, credential))`
     (`adapters.py:591`); the host verifies the binding via `authenticate_actor(credential,
     expected_intent_digest=…)` (method 3). If approval never returns, the CLI does not confirm — it returns
     to resume/recovery, never fabricating or replaying a confirmation.

- **Independent platform approval (activate / release) is OUT of P3.** Candidate ratification (`confirm`)
  is **not** approval; promotion of a candidate to an active/released artifact is a separate platform
  authority, outside this kit and outside P3 (freeze index §5). The kit never approves, activates, or
  releases.

- **Production auth is future / out of P3 (correction #8).** OIDC / workload identity / Kerberos / Windows
  Integrated Auth / enterprise broker over HTTPS are the eventual production mechanisms; **P3.1 implements
  the authenticated local IPC target only.** SSO / OS credential-manager state must live **outside** the
  agent-readable boundary.

- **Secret hygiene (all environments):** secrets are forbidden in the repository, workspace, skill,
  arguments, environment, logs, and temporary files.

## 6. Reference host placement

The reference authority host lives **outside the built skill and preferably outside the canonical Authoring
Kit repository** (e.g. a separate `ontowiz-reference-authority` component). It is non-production,
service-identity + ACL separated, and is **never** bundled into any `.skill` / `.owpack`.

## 7. Rejected — do not revisit

- **Local-authority provider** (fake separation of duty).
- **Configured Python-module entry-point transport** (arbitrary-code load; provider state inside the
  drafting process).
- **Same-user OS identity as authentication.**
