# CONTRACT · IPC / authority wire protocol (P3.1)

**Status:** FROZEN @ `0b0245c` · Parent: [`P3.0_CONTRACT_FREEZE.md`](P3.0_CONTRACT_FREEZE.md) ·
Implemented by **P3.1**.

This freezes the **authority wire protocol** — the channel between the keyless `AuthorityHostClient`
([`CONTRACT_AUTHORITY.md`](CONTRACT_AUTHORITY.md)) and the external authority host. It is **distinct** from
the in-process **adapter protocol** (`adapters.py`); see the freeze index §2. Rejected outright: **loading
a provider module into the CLI process** (arbitrary-code load; provider state inside the drafting process).

## 1. Envelope (versioned, length-bounded, strict)

One **protocol method per exchange** — a strict request/response envelope:

```
request  = { protocol_version, method, workspace_id, correlation_id, params }
response = strict, REDACTED result | strict error
```

- **`protocol_version`** — integer/semver constant, checked on every exchange; a mismatch is a hard
  refusal (no negotiation-down, no silent coercion).
- **`method`** — restricted to the **authority wire allowlist** (correction #3): the **eight** authoring
  `AuthoringTrustProvider` methods (`CONTRACT_AUTHORITY.md §2`, methods 1–8) plus the credential-issuance
  exchange (`AuthoringIntent` → `OperationCredential`). **`advance_authority` (method 9) is NOT on the
  allowlist** — it is authority administration, carried on a separate administrative channel, and any
  attempt to send it over the authoring channel is rejected.
- **`params`** — validated against the pinned model for that method; **unknown, oversized, or
  duplicate-key** messages are rejected. Reuse the adapter protocol's proven discipline:
  `_reject_duplicate_keys` (`adapters.py:285`), `_reject_json_constant` (non-finite, `:281`), and
  canonical NFC JSON on the wire (`adapter_response_bytes` pattern, `:307`).
- **Bounds.** A maximum message-byte cap and a per-call timeout come from **protected config** (§3), not
  from the workspace. The adapter cap `_MAX_REQUEST_BYTES = 1_048_576` (`adapters.py:50`) is the reference
  ceiling; the wire cap MUST be explicit and configured.
- **Credential transit is expected, not avoided (correction #2).** The credential-issuance response carries
  the exact `OperationCredential` host→client, and `authenticate_actor` carries it client→host. The wire
  **does** transmit it transiently (protected in transit, never logged/persisted, §4). This is the opposite
  of the **adapter** protocol, which never carries a credential.
- **Responses are redacted** — the host returns only what the method's return type declares
  (`AuthorityHighWater`, `AuthoringProviderState`, `ActorCapability`, `RecoveryAuthorization`,
  `OperationCredential`). No keys, no internal state, no diagnostics leak to the client.

## 2. Transports (correction #8 — HTTPS is future / out of P3)

| Transport | Environment | In P3? | Requirement |
|---|---|---|---|
| **Windows named pipe** | local (Windows) | **P3.1 target** | authenticated endpoint; ACL-restricted to host service identity |
| **Unix-domain socket** | local (POSIX) | **P3.1 target** | peer-credential-checked; filesystem-ACL restricted |
| **HTTPS + enterprise auth** | production | **FUTURE / OUT of P3** | TLS with server-pin verification; enterprise identity — not implemented in P3 |

**P3.1 implements the authenticated local IPC target only** (named-pipe on Windows / UDS on POSIX), which
satisfies the GO's "authenticated local IPC." One `AuthorityHostClient` runs over either; the transport
stays a swappable channel so HTTPS can be added later **without** touching the client. Do not build or claim
HTTPS in P3.

## 3. Protected configuration (no TOFU)

Endpoint and trust parameters live **outside the workspace**, in an OS config location that the drafting
principal may **read but NOT write** (correction #4): it is writable **only by an administrative identity**
(the same or a peer of the host's service identity), and the drafting principal has read-only access at run
time. A drafting principal that could rewrite the endpoint or pin could redirect the client to a host it
controls; the ACL forbids that.

- `endpoint` (pipe name / socket path / HTTPS URL)
- `protocol_version`
- provider identity
- **server pin** (the host key/cert the client verifies — mutual auth)
- `max_message_bytes`, per-call `timeout`

Rules:

- **No trust-on-first-use.** An unpinned or unverifiable host is a refusal, never an accept-and-remember.
- **The workspace never supplies the endpoint or pin.** A workspace-supplied endpoint is ignored/rejected —
  the drafting agent cannot redirect the client to a host it controls.
- **Drafting-principal-read-only (correction #4).** The config is installed with a **read-only** ACL for
  the drafting principal; only the administrative identity may write it. P3.1 verifies (best-effort) that
  the resolved config is not drafting-principal-writable and treats a writable or absent config as a
  fail-closed `E_AUTHORITY_UNAVAILABLE`.
- Missing / unreadable / drafting-writable config ⇒ `E_AUTHORITY_UNAVAILABLE` (§5).

## 4. Authentication on the wire

- **Mutual:** the host authenticates the client (workload/proposer principal); the client authenticates the
  host (server pin). Neither direction is skippable.
- **Service-identity separation:** the host runs under a **separate service identity**; its keys and
  high-water state are unreadable/unwritable by the drafting principal.
- **Credential transit is transient and channel-protected (correction #2):** the `OperationCredential`
  **does** cross the authenticated local IPC channel — host→client at issuance, client→host at
  `authenticate_actor` — held only in client memory for the duration of the operation. It is **never**
  written to argv, env, logs, disk, or any adapter/wire field bound for the workspace, and never appears in
  an `AdapterRequest`. (Credential handling on the CLI side is frozen in `CONTRACT_CLI.md §5`.)

## 5. Error contract — how `AuthorityTransportError` survives kernel wrapping (correction #7)

The provider is called **deep inside** kernel functions (`_snapshot` → `get_workspace_revision` /
`load_session_state` / `validate_authoring` / `compile_questions`; mutations via `_authenticate_mutation`;
`build_candidate_pack` / `build_workspace_archive`). A transport failure raised there must reach
`AdapterSession.execute` **as itself** and map to `E_AUTHORITY_UNAVAILABLE` — not be swallowed into
`E_AUTHORIZATION`/`E_VALIDATION`/`E_OPERATION_FAILED`, and not escape uncaught. The mechanism is frozen as:

1. **Distinct type, no accidental inheritance.** `AuthorityTransportError` derives from a fresh client base
   (`AuthorityClientError`) and is **not** a subclass of any type the kernel or adapter already catches:
   `AuthoringError`, `WorkspaceError`, `ArchiveError`, `AuthorizationError`, `StaleProposalError`,
   `AuthoringConflictError`, `pydantic.ValidationError`, `OSError`, or the private `_Adapter*Error`s. This
   is what keeps it from being relabelled `E_AUTHORIZATION` (`adapters.py:624`) or `E_VALIDATION`
   (`:636`).
2. **Pass-through at kernel wrap sites.** `build_candidate_pack` / `build_workspace_archive` catch only
   `(AuthoringError, WorkspaceError)` (`archive.py:1609`, `:1569`), so a non-`AuthoringError`
   `AuthorityTransportError` propagates through them unwrapped. P3.1 **audits every provider-call site** for
   a broad `except Exception`/`except AuthoringError` that would swallow or relabel it and, where found,
   adds a narrow re-raise so `AuthorityClientError` always passes through. (Note the admin-only
   `except Exception → AuthoringAtomicError` at `authoring.py:3200` wraps `advance_authority`, which is
   excluded from the authoring channel, §1.)
3. **Explicit first-matched arm.** `AdapterSession.execute` and `execute_json` gain
   `except AuthorityClientError → E_AUTHORITY_UNAVAILABLE`, ordered **before** the generic
   `except (AuthoringError, WorkspaceError, ArchiveError, ValidationError)` (`adapters.py:636`) and
   `except OSError` (`:642`) arms. `AdapterErrorCode` (`adapters.py:92-100`) gains
   `"E_AUTHORITY_UNAVAILABLE"`. The CLI maps it to its own stable exit code (`CONTRACT_CLI.md §6`).
4. **Recovery, not replay.** The client MUST NOT blindly retry a **mutation** on this error; it returns to
   recovery (`CONTRACT_AUTHORITY.md §4`).

`E_AUTHORITY_UNAVAILABLE` is **distinct** from `E_AUTHORIZATION` (`adapters.py:95`, "reachable host
refused"). Both are redacted.

**Test obligation:** a transport failure injected on **each** verb — including the read-only
`resume`/`validate`/`package`/`checkpoint`, which reach the provider via `_snapshot` — surfaces
`E_AUTHORITY_UNAVAILABLE`, never `E_AUTHORIZATION`/`E_VALIDATION`/`E_OPERATION_FAILED`, and never an
uncaught exception.

## 6. Test obligations (P3.1, red→green)

Frozen so the reviewer can check the implementation:

1. Version mismatch, oversized message, duplicate key, non-finite constant, unknown method → each rejected.
2. Missing config / bad pin / unreachable endpoint / timeout → `AuthorityTransportError` →
   `E_AUTHORITY_UNAVAILABLE` (never `E_AUTHORIZATION`).
3. Workspace-supplied endpoint is ignored; only protected config is honoured (no TOFU).
4. A reachable host that **refuses** → `E_AUTHORIZATION` (proving the two codes are genuinely distinct).
5. Interruption mid-mutation → recovery path exercised; **no** blind replay (round-trips
   `reserve`/`authorize_recovery`/`finalize`|`abort`).
6. Responses carry no key/credential/internal-state material (redaction asserted structurally).
7. **`advance_authority` sent over the authoring channel → rejected** (not on the allowlist, §1).
8. **Config writable by the drafting principal → `E_AUTHORITY_UNAVAILABLE`** (fail closed, §3).
9. Transport failure on each verb (incl. read-only) → `E_AUTHORITY_UNAVAILABLE`, never mislabelled/uncaught
   (§5 test obligation).
