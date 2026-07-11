# Mini-spec — F0.2H: Governance state & persistence hardening (v4, post-review pass 3)

**Unit:** F0.2H · **Owner:** BE · **Depends on:** F0.2 (`GovernanceStore`) ·
**Blocks:** F0.3A/B/C (0C hard order `F0.2H → F0.3A`)
**Anchors:** BUILD_INSTRUCTION_SET §13 (F0.2H card), §12.3 (common API behaviour),
§5/§6 (DoD, evidence bundle). Status target: NOT READY → READY on acceptance.

> **Review response — REV pass 1 (findings 5–8, ACCEPTED by REV):**
> additive+transactional migration over an existing F0.2 DB (#5); append-only
> `idempotency_keys` (#6); embedded Python migration constants, no `.sql` resource (#7);
> `reason`/principal caps + never-logged + one-way hash (#8). REV accepted all four.
>
> **Review response — REV pass 2 (findings 1–5):**
> - **#1 `expected_version` (P1):** now **required** on `approve`/`reject`/`escalate`,
>   implemented as a single compare-and-swap `UPDATE … WHERE id=? AND status='proposed'
>   AND version=?` asserting exactly one affected row. The F0.2 tests that call these
>   without a version **are amended** (they are the only callers; no HTTP consumer yet) —
>   correcting the earlier "stays unchanged" claim. Concurrency tests now cover
>   approve-vs-reject and approve-vs-escalate, not only approve-vs-approve. (§3, §5, §7)
> - **#2 baseline adoption (P1):** before stamping `0001`, the runner **fingerprints** the
>   DB (`sqlite_master` + `PRAGMA table_info`) against the exact F0.2 table/column/PK set;
>   a partial or unexpected schema **fails closed** without writing the ledger. (§4, §7)
> - **#3 integrity gate (P1):** `foreign_key_check` can't see the FK-less legacy tables, so
>   the gate adds **explicit orphan anti-joins** for every app-enforced relationship; schema
>   + orphan + row-count checks run **inside** the migration transaction before COMMIT and
>   roll back automatically on failure. The pre-migration backup is created **exclusively**
>   and never overwritten by a retry. (§4, §7)
> - **#4 idempotency shape (P1):** the record is **operation-neutral**
>   (`resource_type`/`resource_id`, nullable) so it covers `record_contribution` (multi/no
>   delta); **canonical hashing** is precisely specified (NFC, sorted keys, fixed
>   separators, UTF-8, server-generated fields excluded); `result_json` holds the **minimal**
>   replay response, not full reasons/principals/payloads. (§4, §5, §7)
> - **#5 retention (P2, deferred with an owner):** retention is owned by INT/governance,
>   target unit **E8**; interim F0.2H rule stated explicitly (§6). Named residual, not an
>   open "lifetime."
>
> **Review response — REV pass 3 (findings 1–3):**
> - **#1 governance ancestry (cross-cutting):** the v2 control docs are committed as their
>   own governance SHA (`2ba342b`); this spec is parented on it, so §12/§13 resolve in-tree.
> - **#2 shared-DB fingerprint:** §4 scopes the baseline fingerprint to the **five
>   governance tables only** — `comments`/`usage`/`users`/`sqlite_*` legitimately coexist;
>   fail-closed fires only on a broken *governance* table, never on unrelated tables.
> - **#3 `foreign_key_check`:** §4 reworded — the orphan anti-joins are the integrity
>   control; `foreign_key_check` is retained only as a guard for future declared FKs.

## 1. Objective & user-observable outcome

The durable store enforces a **legal, single-writer, replay-safe** decision lifecycle:
an illegal transition (decide a non-`proposed` delta) fails deterministically; two
reviewers deciding the same delta-version yield **exactly one** accepted decision (the
loser gets a typed conflict); replaying the *same* request (same idempotency key +
identical payload) returns the original result, never a second write; and F0.2's
restart-survival guarantee still holds — proven against a database created by F0.2, not
only a fresh one. No HTTP surface yet (F0.3).

## 2. Preconditions & pinned dependencies

- Baseline SHA `5f2a4b5` (F0.2, VERIFIED). Existing `catalog.db` files with the F0.2
  governance tables are a **supported input**, not a fresh-only assumption.
- No new third-party dependency (R6). Migration runner = hand-rolled stdlib `sqlite3`
  over the existing `db.py` seam; migrations are Python constants (no ORM, no Alembic,
  no external resource files).
- Contracts pinned: §12.3 (Idempotency-Key; version/ETag → 409 on stale; typed error
  envelope; logs never contain source text/credentials); §13 F0.2H steps 1–7.

## 3. Files & ownership paths (BE, `packages/ontowiz-runtime/`)

- **new** `ontowiz_runtime/migrations.py` — migration runner + the ordered migration
  list as **in-module Python constants** (each `Migration(version, name, statements)`);
  a `schema_migrations` ledger; **schema-fingerprinted baseline adoption** (#2);
  the in-transaction **integrity gate** (schema + orphan anti-joins + row counts, #3).
- **modify** `ontowiz_runtime/governance.py` — run migrations (not inline
  `CREATE TABLE`); typed transitions via compare-and-swap; **required** `expected_version`
  on `approve`/`reject`/`escalate` (#1); operation-neutral append-only idempotency (#4).
- **modify** `ontowiz_runtime/db.py` — `PRAGMA foreign_keys = ON` (safe; catalog tables
  have no FKs) + a `backup(dest)` helper (`sqlite3` online backup API; **exclusive** dest).
- **modify** `ontowiz_runtime/__init__.py` — export new typed errors.
- **modify** `tests/test_governance.py` (F0.2) — the `approve`/`reject`/`escalate` callers
  are amended to pass `expected_version` (#1). This is a deliberate, contained API change,
  not a silent break; every other F0.2 assertion is preserved.
- **new** `tests/test_governance_hardening.py` — preconditions / idempotency (incl.
  escalate + contribution) / concurrency / **upgrade-from-F0.2** / backup+restore /
  fresh-DB / baseline-fingerprint / orphan-rollback / canonical-hash.

No `.sql` files, so **no `pyproject.toml` package-data change** is needed (#7). No files
outside `packages/ontowiz-runtime/` + this spec; the FE lane's uncommitted D0.1 changes
are **excluded** from every F0.2H commit (§6).

## 4. Schema / migration model (additive, transactional, fail-closed)

The runner keeps a `schema_migrations(version, name, applied_at)` ledger and applies
each pending migration in **one `db.transaction()`** (BEGIN…COMMIT; SQLite DDL rolls back).

- **Governance-subset baseline adoption (#2):** `catalog.db` is **shared** — `comments`,
  `usage`, `users` and SQLite system tables (`sqlite_*`) legitimately coexist with the
  governance tables, so the fingerprint is scoped to the **five governance tables only**. If
  the ledger is empty and at least one governance table exists, the runner verifies each of
  the five has **exactly** its expected columns + primary key (via `PRAGMA table_info`) and
  **ignores every non-governance table**. Match → stamp `0001_governance_baseline` as
  *applied* (no data touched). Fail closed (`SchemaMismatchError`, **write nothing**) only on
  a **missing governance table, an extra/renamed column within a governance table, or a wrong
  governed-table definition/PK** — never on unrelated app or system tables. A DB with **no**
  governance tables *runs* `0001` fresh (creates the five F0.2 tables as-built).
- **`0002_governance_hardening` (purely additive):**
  - `ALTER TABLE deltas ADD COLUMN` × 4: `version INTEGER NOT NULL DEFAULT 1`,
    `resource_id TEXT`, `artifact_id TEXT`, `base_version INTEGER` (ADD COLUMN preserves
    all existing rows; no rebuild, no copy).
  - `CREATE TABLE idempotency_keys(...)` — **operation-neutral** (see §5), no FK to
    `deltas`, `UNIQUE(actor, operation, idempotency_key)`.
  - `CREATE INDEX` on `deltas(status)`, `deltas(artifact_id)`, `delta_events(delta_id)`,
    `approvals(delta_id)`, `audit_log(actor)`, `audit_log(created_at)`.
- **Integrity gate — inside the transaction, before COMMIT (#3):**
  1. schema post-condition: the four new columns + `idempotency_keys` + indexes present.
  2. **orphan anti-joins are the integrity control** for the app-enforced relationships (the
     legacy tables *and* the operation-neutral `idempotency_keys` have no DB-level FK, so
     `foreign_key_check` validates **nothing** on them today):
     `SELECT COUNT(*) FROM delta_events e LEFT JOIN deltas d ON e.delta_id=d.id WHERE d.id IS NULL` = 0,
     the same for `approvals`. `PRAGMA foreign_key_check` is still run, but **only as a guard
     for future declared FKs** (e.g. under Postgres) — not as validation of any current record.
  3. row-count preservation: pre/post counts on `deltas`/`approvals`/`audit_log`/
     `delta_events` equal.
  Any check failing raises → `db.transaction()` issues ROLLBACK; the DB is untouched and
  the backup remains the recovery point.
- **Exclusive backup before mutating a non-fresh DB (#3):** copy to
  `<db>.bak-pre-<target_version>` via the `sqlite3` backup API, opening the destination
  **exclusively** (`x` semantics). If it already exists, the runner **reuses/refuses** —
  it never overwrites, so a retry cannot clobber a known-good pre-migration snapshot.
  Restore = stop process, move backup over `catalog.db`.

Generated-client/OpenAPI impact: none (F0.3A owns the contract).

## 5. State machine, concurrency & idempotency (the typed contracts)

**Transitions** (one typed table in `governance.py`):
```
proposed --approve--> approved   (terminal)
proposed --reject---> rejected   (terminal)
proposed --escalate-> proposed   (status unchanged; routing event logged; version bumps)
approved | rejected --any decision--> IllegalTransitionError
```

**Optimistic concurrency (#1) — `expected_version` is REQUIRED on `approve`/`reject`/
`escalate`.** Each is one atomic compare-and-swap:
```sql
UPDATE deltas SET status = :new_status, version = version + 1
WHERE id = :id AND status = 'proposed' AND version = :expected_version
```
(`escalate` keeps `status='proposed'` but still bumps `version`, so it shares the CAS
lane — two ops at the same version cannot both win). The runner asserts `rowcount == 1`.
On `0` rows it re-reads the row to diagnose deterministically:
- no such delta → `NotFoundError`;
- `status != 'proposed'` → `IllegalTransitionError` (already terminal);
- `status == 'proposed'` but `version != expected_version` → `ConcurrencyConflictError` (409).

Two reviewers at the same version → exactly one CAS succeeds; the other gets
`ConcurrencyConflictError` and must re-fetch. The process `RLock` in `db.transaction()`
serialises in-process writes; the `version` CAS is the **portable** guard that also holds
across processes and under Postgres.

**Idempotency (append-only, operation-neutral — #4):** table
```
idempotency_keys(
  id TEXT PRIMARY KEY, actor TEXT, operation TEXT, idempotency_key TEXT,
  request_hash TEXT, resource_type TEXT, resource_id TEXT NULL,
  result_json TEXT, created_at TEXT,
  UNIQUE(actor, operation, idempotency_key))
```
`resource_type`/`resource_id` name the primary resource (`'delta'`/`<delta_id>` for
decisions; `'contribution'`/`<contribution_id>` for `record_contribution`, which may touch
many or no deltas — hence **no** FK to `deltas`). Every mutation — `propose`, `approve`,
`reject`, **`escalate`**, `record_contribution` — accepts an optional `idempotency_key`.
When supplied, within the same `transaction()`:
- compute `request_hash` (below); look up `(actor, operation, key)`:
  - hit + same `request_hash` → return the stored `result_json` (no second write/audit);
  - hit + different `request_hash` → `IdempotencyConflictError` (409);
  - miss → execute the op **and** insert the idempotency record. The `UNIQUE` constraint is
    the backstop if two same-key requests race the lookup.

**Canonical request hash (#4):** `request_hash = sha256(canonical(payload)).hexdigest()`
where `payload` = the **typed client inputs** for the op (actor, operation, resource ids,
`expected_version`, `reason`, `content`, `delta_ids`, …) **excluding** the
`idempotency_key` itself and **all server-generated fields** (new `version`, timestamps,
server-minted ids). `canonical(x)` = `json.dumps(nfc(x), sort_keys=True,
separators=(',',':'), ensure_ascii=False).encode('utf-8')`, with string fields
NFC-normalised. Reordered dict keys and NFC-equivalent strings therefore hash identically.

**`result_json` is minimal (#4, #8):** only the immutable response needed to replay —
e.g. `{"id":…, "status":…, "version":…}` — never the full `reason`, principal, or
contribution payload (keeps PII out of the idempotency table).

Invariants: events/approvals/audit remain **append-only**; each mutation is one atomic
`transaction()` (CAS + event + approval + audit + idempotency record all-or-nothing);
attribution is always a real principal (R4), never literal `'curator'`.

Typed errors (new, Tier A): `IllegalTransitionError`, `ConcurrencyConflictError`,
`IdempotencyConflictError`, `SchemaMismatchError` — F0.3 maps to 409/422/500.

## 6. Threat & data-egress delta (closes #8; #5 owned+deferred)

No network / LLM / source text. Local SQLite integrity only. Controls:
- `reason` capped at 4000 chars, principal identifiers at 512; over-limit → 422.
- `reason` and principals are **potentially sensitive**: never written to structured
  logs and never echoed verbatim in error envelopes (§12.3); `result_json` excludes them.
- `request_hash` is **one-way** SHA-256 used only for equality — it does not expose
  reason text.
- **Retention (#5):** owned by **INT/governance**, target unit **E8** (tenant retention &
  erasure). Interim F0.2H rule, stated explicitly: audit/idempotency rows are retained
  indefinitely in the single-tenant dev SQLite (no automated purge); E8 introduces a
  retention window + purge/erasure before real SME/client data enters. Field-level
  redaction/erasure (legal hold, tenant deletion) is the E8 capability, flagged not built.
Threats closed: lost-update (required-version CAS), duplicate-submit replay (idempotency),
orphaned child rows (app-integrity + migration-time orphan gate).

## 7. Tests mapped 1:1 to acceptance (red→green; negative/concurrency/upgrade/restart)

| Acceptance (DoD / finding) | Test |
|---|---|
| illegal / double transition fails | `test_approve_non_proposed_raises`, `test_double_approve_raises` |
| **#1** required version — omitting it is an error | `test_decision_without_expected_version_raises` |
| **#1** stale version rejected | `test_expected_version_mismatch_raises` |
| **#1** two reviewers, same version → one winner | `test_concurrent_approve_vs_approve_one_winner` |
| **#1** approve-vs-reject / approve-vs-escalate → one winner | `test_concurrent_approve_vs_reject`, `test_concurrent_approve_vs_escalate` |
| **#4** idempotent replay (approve/reject/escalate/propose) | `test_same_idempotency_key_returns_original[op]` |
| **#4** contribution replay (no/many deltas) | `test_idempotent_contribution_without_delta` |
| **#4** conflicting key → 409 | `test_idempotency_key_conflict_raises` |
| **#4** canonical hash is order/NFC-invariant | `test_request_hash_ignores_key_order_and_unicode_form` |
| **#4** `result_json` is minimal (no reason/principal) | `test_result_json_excludes_sensitive_fields` |
| app-integrity: no orphan child rows at write time | `test_event_on_unknown_delta_rejected` |
| append-only counts correct | `test_audit_and_event_counts_after_decisions` |
| migration idempotent (re-apply no-op) | `test_migrations_apply_once` |
| **#2** baseline adopts the governance subset with `comments`/`usage`/`users` present | `test_baseline_adopts_with_shared_catalog_tables_present` |
| **#2** baseline fails closed on a broken governance table (missing/extra column) | `test_baseline_fails_closed_on_bad_governance_table` |
| **#2** upgrade over a **shared** `catalog.db` (gov + comments/usage/users) preserves all rows | `test_upgrade_from_shared_catalog_db_preserves_rows` |
| **#3** migration-time orphan detected → rollback | `test_orphan_rows_fail_integrity_and_roll_back` |
| **#3** backup created exclusively, retry doesn't overwrite | `test_backup_not_overwritten_on_retry` |
| **#3** backup restores | `test_backup_restores_pre_migration_state` |
| **#7** fresh-DB apply from Python constants (wheel-safe) | `test_fresh_database_migrates_from_python_constants` |
| restart-survival stays green | existing `test_approval_and_audit_survive_restart` + new `test_version_and_idempotency_survive_restart` |
| rollback leaves no partial rows | `test_failed_decision_rolls_back_atomically` |

Amended F0.2 tests (#1): `test_approve_records_…`, `test_reject_records_…`, and any
escalate caller pass `expected_version` (the post-propose value); all other assertions
unchanged. Coverage ≥85% on changed runtime code; governance boundary → branch + negative
+ concurrency tests (§5.3).

## 8. Migration, rollback & recovery

Forward: the runner fingerprints and adopts an F0.2 baseline (or creates fresh), takes an
exclusive backup for a non-fresh DB, then applies `0002` additively **and runs the
integrity gate inside the same transaction**; re-open is a no-op (ledger guard).
**Rollback:** any integrity failure auto-rolls-back the transaction (DB untouched); a
manual revert restores the pre-migration backup. **Recovery:** a decision interrupted
mid-transaction rolls back atomically (test-proven); restart re-opens and re-reads
committed state.

## 9. Telemetry & operational failure behaviour

Conflicts (`Illegal`/`Concurrency`/`Idempotency`/`SchemaMismatch`) are typed and raised,
not swallowed — F0.3 surfaces them as 409/422/500 with stable codes. No logging of
`reason`/principal/source.

## 10. Out of scope & residual risk

- No HTTP endpoints / JWT / capability checks (F0.3A/B).
- No `outbox_events`/`jobs` (F0.3C); no `artifact_versions`/`applicability`/`evidence_refs`
  (F0.7A/E1).
- **DB-level FKs on the pre-existing `delta_events`/`approvals`** are deferred (would need
  a table rebuild on existing data); the migration-time orphan gate + app-integrity
  (`_require_delta`) + `PRAGMA foreign_keys=ON` guard them, and native FKs land with the
  Postgres migration. `idempotency_keys` is intentionally FK-free (operation-neutral, #4);
  its `resource_id` integrity is app-enforced.
- **Retention purge/erasure** of `reason`/principals → E8 (owned by INT/governance, #5).
- SQLite serialises writes via the existing lock; the required-version CAS is the portable
  guard that still holds under Postgres concurrency.

## 11. Dependency change

None. No new package; migrations are in-module Python (no package-data). `PRAGMA
foreign_keys=ON` and the `sqlite3` backup API are config/stdlib, not dependencies.
