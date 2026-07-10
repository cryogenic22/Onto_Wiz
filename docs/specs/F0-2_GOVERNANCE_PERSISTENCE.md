# Mini-spec — F0.2: Governance persistence on the SQLite seam

**Epic:** F0 (Loop 0) · **Rule anchors:** R2 (unit loop), R1 (one pipe — untouched), R4 (real attribution), R6 (SQLite, no speculative infra)
**Provenance:** `BUILD_INSTRUCTION_SET_2026-07.md` §F0.2 + §9 (DDL master) + §11 (restart-survival test).

## Problem

The governance records that matter to the *deployed* product — proposed deltas,
their approvals, the audit trail, SME contributions — live only in **in-memory
dicts** inside the Tier B legacy store (`ontowiz-core/stores.py`: `DeltaStore`,
`ContributionStore`). A process restart loses them. F0.2 gives them a durable home
on the existing `db.py` SQLite seam (ADR-016: SQLite dev, Postgres prod via DSN).

## Success criteria (acceptance)

> Approve a delta, **restart the process**, the approval and audit trail survive; a
> test proves it. (This is the "restart-survival test that runs in CI forever," §11.)

## Design (reuse-first, tier-correct)

`Decision:` the durable store is **Tier A** (`ontowiz-runtime/governance.py`), not
Tier B. The deployed `ontowiz-serve` app (Tier A) must consume it in F0.3, and
**Tier A → Tier B is a build failure** (ADR-012); the `db.py` seam is already Tier A.
It mirrors the `CommentStore`/`UsageStore` pattern exactly (dataclass rows +
`CREATE TABLE IF NOT EXISTS` + ISO timestamps), so no new persistence machinery.

`Decision:` rows are **flat, hand-rolled** (their own small dataclasses), *not* the
Tier B `Delta`/`AuditEntry`/`Contribution` behavioural models. §9 mandates "no ORM
cleverness"; the boundary forbids importing Tier B. This is intended separation
(Tier A flat storage vs Tier B behavioural IP), **not** duplication.

`Decision:` one dev SQLite file (the shared `catalog.db`) holds the governance
tables alongside the catalog tables — mirroring the single prod Postgres DB where
all these tables live in one schema (ADR-016, R6). No new DB file.

`Constraint:` the store records the **delta lifecycle**; it does **not** promote any
artifact to ACTIVE. R1's one-pipe (`bridge.py`, Tier B) is untouched. F0.3 wires
`/v1/deltas` endpoints to this store; approval → ACTIVE promotion still routes
through the bridge. The Tier B in-memory `DeltaStore`/`ContributionStore` remain for
offline factory composition (slated for reduction per §2); F0.2 does **not** rewrite
that legacy-debt file.

`Constraint:` every attribution field is a passed-in principal — never the literal
string `'curator'` (R4).

## Tables (DDL §9 — TEXT ids, ISO timestamps, attribution per row, soft-delete via status)

- **deltas**(`id` PK, `type`, `status`∈{proposed,approved,rejected,merged}, `content` JSON, `created_by`, `created_at`, `updated_at`, `reviewer`?, `reason`?)
- **delta_events**(`id` PK, `delta_id`, `event`∈{proposed,approved,rejected,escalated,merged}, `actor`, `detail` JSON, `created_at`) — append-only per-delta history
- **approvals**(`id` PK, `delta_id`, `approver`, `decision`∈{approve,reject}, `reason`, `created_at`)
- **audit_log**(`id` PK, `actor`, `action`, `action_category`∈{create,approve,reject,escalate,merge,record}, `store_type`, `artifact_id`, `details` JSON, `created_at`)
- **contributions**(`id` PK, `sme_id`, `sme_persona`, `delta_ids` JSON, `therapeutic_area`, `scenario_type`, `sme_confidence`, `created_by`, `created_at`)

Soft-delete = status (deltas); the four log tables are append-only (never deleted).

## Store surface (`GovernanceStore(root)`)

Writes (each also appends a `delta_events` row **and** an `audit_log` row atomically):
`propose_delta`, `approve_delta`, `reject_delta`, `escalate_delta`, `record_contribution`.
Reads: `get_delta`, `list_deltas(status=)`, `list_delta_events(delta_id)`,
`list_approvals(delta_id)`, `get_audit_log(limit=, action=)`, `list_contributions(sme_id)`.
Unknown delta on a write → `ValueError` (F0.3 maps to 404/409).

## Test plan (TDD red → green) — `tests/test_governance.py`

1. `test_propose_delta_persists_row_event_and_audit`
2. `test_approve_records_approval_event_audit_and_status`
3. `test_reject_records_reason_and_status`
4. `test_escalate_logs_without_changing_status`
5. `test_record_contribution_persists`
6. `test_write_on_unknown_delta_raises`
7. `test_get_audit_log_filter_and_limit`
8. **`test_approval_and_audit_survive_restart`** — the acceptance: approve on
   instance #1, close it, open instance #2 on the same dir → delta is `approved`,
   `approvals` + `audit_log` (`propose`,`approve`) present. Attribution is the real
   principal, never `'curator'`.

## Evidence (Completion gate)

`verify-audit.sh` → PASS (new store ≥85% cov, ruff + mypy Tier A clean, boundary
clean — no Tier B import); F0.2 row + restart-survival evidence in `PROJECT_STATUS.md`.
API §8 / DDL §9 already list these; endpoint wiring is F0.3.
