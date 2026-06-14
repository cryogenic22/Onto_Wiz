# Sprint 3/4 Reports — Archived

> Archived from `docs/Dev2Lead.md` on 2026-02-02
> Sprint 3: CTX-006, LENS-004, SEN-006, SEN-007, ATL-003 — all DONE
> Sprint 4: CTX-018 DONE

---

## TEAM CORTEX [CTX] — Sprint 3

### CTX-006: HITL Routing Logic
**Status:** DONE
**Started:** 2026-02-01
**Completed:** 2026-02-01
**Ticket:** CTX-006 | P0 | Est: L

**Files Modified (3):**
- `src/core/models.py` — Added `RoutingDecision` dataclass (assigned_to, queue, priority, sla_hours, reason)
- `src/core/stores.py` — Added `route_delta()` with `_ROUTING_TABLE` (9 entries), `_ESCALATION_PATH`. DeltaStore gains: auto-routing in `propose()`, `get_pending_for_role()`, `escalate()`, `get_queue_stats()`.
- `src/core/__init__.py` — Exported `RoutingDecision`, `route_delta`

**Tests:** 10 new in `TestHITLRouting` class
**Bug Fix:** `get_pending_for_role()`/`get_queue_stats()` passed `limit=0` causing empty slice — fixed to `limit=9999`
**Quality:** 74 passed (test_core.py scope), 0 failed. No function > 50 lines. No new dependencies.

---

## TEAM LENS [LENS] — Sprint 3

### LENS-004: HITL Routing Endpoints + Audit Export API
**Status:** DONE
**Started:** 2026-02-01
**Completed:** 2026-02-01
**Ticket:** LENS-004 | P0 | Est: M

**Files Modified (4):**
- `src/api/schemas.py` — Added `ReviewQueueItem`, `QueueStatsResponse`, `EscalateRequest`, `AuditEntryResponse`
- `src/api/server.py` — 5 new endpoints (HITL tag: 3, Audit tag: 2), imported `route_delta` + new schemas
- `src/core/stores.py` — Added `JudgmentStore.get_audit_log()` (missing public getter for existing `_audit_log`)
- `tests/test_api.py` — 11 new tests in `TestReviewQueue` (7) and `TestAuditLog` (4) classes
- `tests/conftest.py` — Added `_audit_log` clearing to `_reset_stores` fixture

**Bug Fix:** `JudgmentStore` had `_audit_log` list and `_log_audit()` method but no public `get_audit_log()` getter. Added 3-line method.
**Quality:** 167 passed (11 new), 0 failed. npm build + lint clean. All endpoints under 25 lines.

---

## TEAM SENTINEL [SEN] — Sprint 3

### SEN-006: Security Review (OWASP Top 10)
**Status:** DONE
**Started:** 2026-02-01
**Completed:** 2026-02-01
**Ticket:** SEN-006 | P1 | Est: M

**Files Created (1):**
- `docs/reviews/security_review.md` — Full OWASP Top 10 audit report

**Verdict:** PASS_WITH_FINDINGS (7 findings: 2 HIGH, 3 MEDIUM, 2 LOW)
- F-001 HIGH: No Authentication/Authorization (OWASP A01)
- F-002 HIGH: CORS allows all origins with credentials (OWASP A05)
- F-003 MEDIUM: No object-level access control (A01)
- F-004 MEDIUM: No rate limiting (A05)
- F-005 MEDIUM: Unbounded list fields (A04)
- F-006 LOW: No security event logging (A09)
- F-007 LOW: Missing security headers (A05)

**Clean:** Injection (A03), SSRF (A10), Data Integrity (A08) all PASS.
**Quality:** 134 passed, 0 failed. No source code modifications (DEC-011 compliant).

---

### SEN-007: Architecture Decision Records (ADR-001 through ADR-011)
**Status:** DONE
**Started:** 2026-02-01
**Completed:** 2026-02-01
**Ticket:** SEN-007 | P1 | Est: M

**Files Created (12):**
- `docs/adr/README.md` — ADR index with links, status legend, categories
- `docs/adr/ADR-001-delta-model.md` through `docs/adr/ADR-011-sentinel-reviews-read-only.md`

**Template:** Michael Nygard (Title, Date, Status, Deciders, Source, Context, Decision, Consequences).
**Categories:** Governance (001, 008, 011), Quality (003, 004, 006), Architecture (005, 007), Process (002, 009, 010).
**Anti-Slop:** No source code modifications. No new dependencies. All 11 decisions documented faithfully.

---

## TEAM ATLAS [ATL] — Sprint 3

### ATL-003: Scenario Library v1 — 10 Oncology Scenarios
**Status:** DONE
**Started:** 2026-02-01
**Completed:** 2026-02-02
**Ticket:** ATL-003 | P0 | Est: XL

**Deliverables:**
- 5 new gold set scenarios (GOLD-006 through GOLD-010)
- 10 structured scenario definitions (ONC-001 through ONC-010)
- 5 new synthetic accounts + 10 dark data signals

**Coverage:** 3 NSCLC, 2 breast, 1 AML, 1 DLBCL, 1 MSI-H tumor-agnostic, 1 RCC, 1 melanoma
**Quality:** 180 passed (13 new), 0 failed. 10/10 gold sets passing. 0 source lines modified.

---

## TEAM CORTEX [CTX] — Sprint 4

### CTX-018: Contribution Tracking Store
**Status:** DONE
**Started:** 2026-02-01
**Completed:** 2026-02-02
**Ticket:** CTX-018 | P1 | Est: M

**Files Modified (4):**
- `src/core/models.py` — `Contribution` dataclass (9 fields)
- `src/core/stores.py` — `ContributionStore` class (6 public methods + audit log)
- `src/core/delta_generator.py` — `process_sme_session()` gains optional `contribution_store` param
- `src/core/__init__.py` — Exported `Contribution`, `ContributionStore`

**Tests:** 8 new in `TestContributionStore` class
**Quality:** 82 passed (test_core.py scope), 0 failed. All functions under 25 lines. No new dependencies.

---

## TEAM LENS [LENS] — Sprint 4

### LENS-005: Curator Dashboard MVP
**Status:** DONE
**Started:** 2026-02-02
**Completed:** 2026-02-02
**Ticket:** LENS-005 | P0 | Est: XL

**Files Created (7):**
- `frontend/src/types/curator.ts` — 4 interfaces
- `frontend/src/components/curator/QueueStats.tsx` — Stats bar
- `frontend/src/components/curator/ReviewQueue.tsx` — Queue list with role filter
- `frontend/src/components/curator/DeltaDetail.tsx` — Detail panel with actions
- `frontend/src/components/curator/AuditTrail.tsx` — Collapsible audit log
- `frontend/src/components/CuratorDashboard.tsx` — Page orchestrator
- `frontend/src/app/curator/page.tsx` — Next.js route

**Files Modified (2):**
- `frontend/src/services/api.ts` — 7 new API functions
- `frontend/src/components/SituationRoom.tsx` — Added Curator nav link

**Quality:** npm build clean, lint 0 errors/warnings, pytest 189 passed. All components under 50 lines. 0 new dependencies.

---

## TEAM SENTINEL [SEN] — Sprint 4

### SEN-008: End-to-End Smoke Test Suite
**Status:** DONE
**Started:** 2026-02-02
**Completed:** 2026-02-02
**Ticket:** SEN-008 | P1 | Est: L

**Files Created (1):**
- `tests/test_e2e_smoke.py` — 9 smoke tests marked `@pytest.mark.e2e`

**Files Modified (1):**
- `pyproject.toml` — Registered `e2e` pytest marker

**Quality:** 9 smoke tests passed, pytest full 189 passed. 0 regressions. No src/ modifications.

---

## TEAM ATLAS [ATL] — Sprint 4

### ATL-004: Market Access Domain — Payer/Formulary Taxonomy
**Status:** DONE
**Started:** 2026-02-02
**Completed:** 2026-02-02
**Ticket:** ATL-004 | P1 | Est: L

**Deliverables:**
- 1 domain taxonomy (`ontology/domains/market_access_payer_archetypes.yaml`)
- 4 new inference rules in `ontology/commercial.yaml` (19 total)
- 3 new gold set scenarios (GOLD-011..013)
- 3 new synthetic accounts + 6 dark data signals

**Quality:** 192 passed, 13/13 gold sets. 0 source lines modified. All YAML clean.

---

_End of Sprint 3/4 Archive_
