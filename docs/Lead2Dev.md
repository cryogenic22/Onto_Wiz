# Lead2Dev — Sprint Queue & Instructions

> Tech Lead → Team LENS + Team CORTEX + Team ATLAS + Team SENTINEL
> Board: `docs/BOARD.md`
> Protocol: `docs/AUTONOMOUS_AGENT_PROTOCOL.md`
> Anti-Slop: `anti_slop.md`
> Last Updated: 2026-02-17 (Sprint 9 active — CTX-041, LENS-014, ATL-006, SEN-009)

---

## How to Read This File

1. Read your team instruction file FIRST (`docs/teams/LENS_INSTRUCTIONS.md`, `CORTEX_INSTRUCTIONS.md`, `ATLAS_INSTRUCTIONS.md`, or `SENTINEL_INSTRUCTIONS.md`)
2. Check `docs/BOARD.md` for full board state
3. Find your ticket below marked `EXECUTE NOW`
4. Write mini-spec in `docs/Dev2Lead.md` BEFORE writing code
5. Follow acceptance criteria exactly — no scope creep

---

## Dependencies

| Ticket | Blocked By | Status |
|--------|-----------|--------|
| CTX-005 | — | **DONE** (144 tests) |
| LENS-011 | CTX-017 ✓ | **DONE** |
| ATL-003 | ATL-002 ✓ | **EXECUTE NOW** — oncology taxonomy available |
| SEN-005 | — | **DONE** |
| CTX-006 | CTX-005 ✓ | **DONE** (74 tests, routing matrix) |
| LENS-004 | CTX-006 ✓ | **DONE** (167 tests, 5 endpoints) |
| SEN-006 | — | **DONE** (OWASP review, 7 findings) |
| SEN-007 | — | **DONE** (12 ADR files created) |
| CTX-018 | CTX-017 ✓ | **DONE** (82 tests, ContributionStore) |
| ATL-003 | ATL-002 ✓ | **DONE** (180 tests, 10/10 gold sets) |
| LENS-005 | LENS-004 ✓, LENS-012 ✓ | **DONE** (Curator Dashboard, 189 tests) |
| SEN-008 | — | **DONE** (9 E2E smoke tests) |
| ATL-004 | ATL-001 ✓ | **DONE** (192 tests, 13/13 gold sets) |
| CTX-008 | CTX-005 ✓ | **DONE** (93 tests, enhanced audit trail) |
| LENS-013 | CTX-018 ✓, LENS-012 ✓ | **DONE** (209 tests, SME Impact Dashboard) |
| CTX-007 | CTX-005 ✓ | **DONE** (102 tests) |
| CTX-009 | CTX-001 ✓ | **DONE** (115 tests) |
| CTX-019 | — | **DONE** (148 tests, semantic search) |
| CTX-041 | CTX-001 ✓, CTX-019 ✓ | **EXECUTE NOW** — Sprint 9 (Unify Reasoning Paths) |
| LENS-014 | LENS-012 ✓ | **EXECUTE NOW** — Sprint 9 (Intelligence Packet Viewer) |
| ATL-006 | ATL-001 ✓ | **EXECUTE NOW** — Sprint 9 (Immunology TA) |
| SEN-009 | SEN-005 ✓ | **EXECUTE NOW** — Sprint 9 (Load Testing) |

---

## Phase 2.1 — COMPLETE

All 7 tickets delivered. Archived to `docs/archive/phase_2_1_sprint_reports.md`.

---

## Sprint 1 — COMPLETE

All 5 tickets delivered. Archived to `docs/archive/sprint_1_reports.md`.

- CTX-017: ReasoningEvent Ingestion + Delta Generation — DONE (133 tests)
- LENS-012: Design System + Persona Modes — DONE
- ATL-001: Commercial Ontology Expansion — DONE (12 rules, 15 entities, 3 gold sets)
- SEN-001: Quality Gate Infrastructure — DONE (CI pipeline)
- SEN-002: Automated Anti-Slop Checker — DONE (5 AST checks, delivered early)

---

## Sprint 2 — Session Wiring + Governance Foundation

> Sprint 2 COMPLETE — all tickets delivered.
> CTX-005 DONE (144 tests). LENS-011 DONE. SEN-005 DONE. ATL-002 DONE. SEN-003 + SEN-004 DONE.
> ATL-003 EXECUTE NOW (Sprint 3). CTX-006 now unblocked (Sprint 3).

### TEAM CORTEX

#### CTX-005: Artifact Ownership + Judgment Classification `DONE`

**Priority:** P0  |  **Est:** M  |  **Sprint:** 2
**Scope:** `src/core/models.py`, `src/core/stores.py`, `tests/test_core.py`
**Depends On:** None (unblocked)
**Product Ref:** `product_management/epics/EPIC-002.md` (Governance), `src/core/models.py` (Governance dataclass, JudgmentType enum, RiskClass enum)

**Objective:** Enforce that every Delta and JudgmentPattern has a clear owner, a judgment classification (empirical / causal_hypothesis / normative), and that governance rules (who can approve, review cycle) are derived from the classification. This is the foundation for HITL routing (CTX-006) and review cycles (CTX-007).

**Acceptance Criteria:**
- [ ] `Delta` gets a new field `owner: str = "system"` — who proposed it
- [ ] `Delta` gets a new field `judgment_type: JudgmentType = JudgmentType.EMPIRICAL` — classification
- [ ] `JudgmentPattern` already has `governance: Governance` and `judgment_type` — verify these are used consistently
- [ ] New function `classify_delta(delta: Delta) -> JudgmentType` in `stores.py` — derives classification from delta type + content:
  - `PROPOSED_SYNONYM`, `PROPOSED_MAPPING` → `EMPIRICAL` (data-derived, auto-approvable)
  - `PROPOSED_PATTERN`, `PROPOSED_GUARDRAIL` → `CAUSAL_HYPOTHESIS` (mixed, needs review)
  - `PROPOSED_ACTION` → `NORMATIVE` (human-only, requires explicit approval)
  - `PROPOSED_EDGE`, `PROPOSED_ENTITY` → based on `blast_radius`: LOW→EMPIRICAL, MEDIUM→CAUSAL, HIGH→NORMATIVE
- [ ] `DeltaStore.propose()` auto-sets `judgment_type` via `classify_delta()` if not already set
- [ ] New function `get_required_approver(delta: Delta) -> str` in `stores.py`:
  - `EMPIRICAL` → `"system_auto"` (auto-approve if confidence >= 0.9)
  - `CAUSAL_HYPOTHESIS` → `"domain_expert"` (human review)
  - `NORMATIVE` → `"governance_board"` (escalated review)
- [ ] Tests: 6 new tests minimum:
  - `test_classify_synonym_as_empirical`
  - `test_classify_pattern_as_causal`
  - `test_classify_action_as_normative`
  - `test_classify_edge_by_blast_radius`
  - `test_propose_auto_classifies`
  - `test_get_required_approver`
- [ ] All existing 134 tests still pass
- [ ] No function > 50 lines

**Anti-Slop:**
- `Governance`, `JudgmentType`, `RiskClass` already exist in `models.py` — reuse them, do NOT create new enums
- `is_auto_approvable()` on Delta already checks blast_radius + confidence — `classify_delta` should be consistent with this logic, not contradictory
- Check `DeltaStore.propose()` at `stores.py:45` — the auto-approve path already exists, integrate classification there
- Do NOT change the Governance dataclass fields — only add logic that uses existing fields

---

### TEAM LENS

#### LENS-011: Game Session Submission API + Hook `DONE`

**Priority:** P0  |  **Est:** M  |  **Sprint:** 2
**Scope:** `frontend/src/services/api.ts`, `frontend/src/hooks/useGameSession.ts`, `frontend/src/components/game/SessionSummary.tsx`
**Depends On:** CTX-017 DONE — `POST /sessions` endpoint exists and is tested
**Product Ref:** `frontend/src/types/game.ts` (GameResponses, GameSession), `src/api/schemas.py` (GameSessionCreate)

**Objective:** Wire the frontend game session to the backend. When the SME completes all 9 steps, the SessionSummary component submits the collected responses to `POST /sessions` and displays the result (deltas generated, session ID). This closes the loop from SME game play → backend delta generation.

**Acceptance Criteria:**
- [ ] `frontend/src/services/api.ts` — add `submitGameSession(responses: GameResponses): Promise<SessionResult>` function
  - Posts to `POST /sessions` with the GameResponses payload
  - Maps frontend camelCase fields to backend expected format (see `src/api/schemas.py` GameSessionCreate)
  - Returns `{ sessionId: string, deltasGenerated: number, deltaIds: string[] }`
  - Handles error (non-2xx) by throwing with status + message
- [ ] `frontend/src/services/api.ts` — add `fetchSessionDetail(sessionId: string): Promise<SessionDetail>` function
  - Gets from `GET /sessions/{sessionId}`
- [ ] `frontend/src/types/api.ts` — add `SessionResult` and `SessionDetail` types
- [ ] `frontend/src/hooks/useGameSession.ts` — add `submitSession()` async function:
  - Calls `submitGameSession(session.responses)`
  - Returns result, sets submitting/submitted state
  - Error handling: stores error message in state
- [ ] `frontend/src/components/game/SessionSummary.tsx` — add "Submit to Ontology" button:
  - Calls `submitSession()` on click
  - Shows loading state while submitting
  - On success: displays delta count, session ID, and a "View Deltas" message
  - On error: displays error message with retry option
  - Button disabled if already submitted
- [ ] `npm run build` passes with 0 errors
- [ ] No new npm dependencies
- [ ] No component > 50 lines (decompose if needed)

**Anti-Slop:**
- The backend `POST /sessions` already exists (CTX-017) — read `tests/test_api.py:488` for the exact payload format that works
- The `GameSessionCreate` Pydantic model uses `populate_by_name=True` with camelCase aliases — frontend can send camelCase directly
- Do NOT add state management libraries (Redux, Zustand) — use existing React state in `useGameSession` hook
- Do NOT add axios — use native `fetch` (matches existing `api.ts` pattern)
- Read `frontend/src/components/game/SessionSummary.tsx` first to understand current layout before modifying

---

### TEAM ATLAS

#### ATL-002: Oncology Therapeutic Area — Deep Taxonomy `DONE`

**Status:** DONE — archived to `docs/archive/sprint_2_reports.md`

#### ATL-003: Scenario Library v1 — 10 Oncology Scenarios `EXECUTE NOW`

**Priority:** P0  |  **Est:** XL  |  **Sprint:** 3
**Scope:** `ontology/scenarios/`, `ontology/synthetic_data/compellium_pharma.yaml`, `tests/gold_set/scenarios/`
**Depends On:** ATL-002 DONE — oncology taxonomy, biomarkers, indications all available
**Product Ref:** `tests/gold_set/scenarios/GOLD-001-safety-signal.yaml` (scenario format), `tests/gold_set/test_gold_set.py` (test harness), `ontology/therapeutic_areas/oncology_indications.yaml` (indication subtypes)

**Objective:** Create 5 new gold set scenarios (GOLD-006 through GOLD-010) and 10 structured scenario definition files that exercise oncology-specific reasoning across multiple indications, biomarkers, and commercial dynamics. New scenarios must pass the existing test harness and expand coverage beyond the NSCLC-only focus of GOLD-001 through GOLD-005.

**Acceptance Criteria:**

1. **5 New Gold Set Scenarios** in `tests/gold_set/scenarios/`:
   - [ ] `GOLD-006-biomarker-testing-gap.yaml` — Tests `rule_biomarker_testing_gap`. Scenario: EGFR testing delays at an account cause eligible patients to miss targeted therapy, defaulting to chemo. Uses existing account + dark signals referencing biomarker testing rates.
   - [ ] `GOLD-007-breast-her2-sequencing.yaml` — Tests cross-indication reasoning. Scenario: HER2+ breast cancer patient journey disrupted by T-DXd sequencing change. Must reference breast cancer subtypes from `oncology_indications.yaml`.
   - [ ] `GOLD-008-dual-driver-separation.yaml` — Tests multi-signal disambiguation. Scenario: Budget crisis AND safety signal co-occur at same account. Engine should distinguish the primary driver (safety) from confounding signal (budget).
   - [ ] `GOLD-009-biosimilar-entry.yaml` — Tests competitive pricing pressure. Scenario: LungoFix (biosimilar) gains formulary preferred status, triggering margin erosion for OncoVance. Uses existing competitor data.
   - [ ] `GOLD-010-pathway-exclusion.yaml` — Tests `rule_pathway_exclusion`. Scenario: Institutional pathway committee excludes OncoVance from NSCLC 1L protocol despite guideline support.

2. **10 Structured Scenario Files** in `ontology/scenarios/`:
   - [ ] Create `ontology/scenarios/` directory
   - [ ] 10 YAML files following a consistent schema:
     ```
     id, name, description, therapeutic_area, indication,
     brand_context, account_context, trigger_signal,
     expected_hypothesis, expected_drivers, complexity_level
     ```
   - [ ] At least 3 NSCLC scenarios (different molecular subtypes: EGFR, ALK, wild-type)
   - [ ] At least 2 breast cancer scenarios (HER2+, TNBC)
   - [ ] At least 1 hematologic malignancy scenario (AML or DLBCL)
   - [ ] At least 1 cross-indication/tumor-agnostic scenario (MSI-H or TMB-H)
   - [ ] Remaining 3 can cover any oncology indication from `oncology_indications.yaml`
   - [ ] Each scenario references real biomarkers from `oncology_biomarkers.yaml`
   - [ ] Each scenario maps to at least one inference rule in `commercial.yaml`

3. **Synthetic Data Expansion** (if needed for new gold sets):
   - [ ] Add new dark data signals to `compellium_pharma.yaml` for any account that needs them
   - [ ] New signals must follow existing format (`category`, `signal_type`, `description`, `tags`)
   - [ ] Keep `compellium_pharma.yaml` under 300 lines (split into separate account files if needed)

4. **Quality Gates:**
   - [ ] All 10 gold set scenarios pass: `pytest tests/gold_set/ -v` (GOLD-001 through GOLD-010)
   - [ ] All existing tests pass: `pytest tests/ -v`
   - [ ] All YAML files parse correctly (no syntax errors)
   - [ ] No scenario file exceeds 300 lines
   - [ ] No source code modified (ontology content only)

**Anti-Slop:**
- Follow EXACT gold set format from `GOLD-001-safety-signal.yaml`: `id`, `name`, `description`, `input` (with `signal`/`question` + `context`), `expected` (with `min_confidence`, `reasoning_not_empty`, `must_contain_tags`)
- Test harness in `test_gold_set.py` auto-discovers `*.yaml` in `tests/gold_set/scenarios/` — no test code changes needed
- Confidence bounds must be realistic: existing scenarios use 0.5-0.85. Don't set `min_confidence` above 0.9 without justification
- `must_contain_tags` must match tags that the ReasoningEngine actually produces (check `commercial.yaml` inference rules for tag vocabulary)
- Do NOT modify `test_gold_set.py` or any source code
- Scenario descriptions should be pharma-realistic, not generic — use specific clinical/commercial language from the oncology taxonomy

---

### TEAM SENTINEL

#### SEN-003 + SEN-004: `DONE`

**Status:** Both delivered early. Archived to `docs/archive/sprint_2_reports.md`.
- SEN-003: Architecture Review — `docs/reviews/architecture_review_phase2_5.md`
- SEN-004: Coverage Audit — `docs/reviews/coverage_audit.md`

#### SEN-005: Performance Baseline `DONE`

**Priority:** P1  |  **Est:** M  |  **Sprint:** 5 (pulled forward — SENTINEL idle)
**Scope:** `tests/test_performance.py`, `quality/config.yaml`, `quality/README.md`
**Depends On:** None (unblocked)
**Product Ref:** `quality/config.yaml` (existing thresholds), `src/api/server.py` (endpoints), `src/core/stores.py` (store operations)

**Objective:** Establish baseline performance measurements for all API endpoints and core store operations. Create a repeatable benchmark test suite with documented thresholds. This baseline is the reference for SEN-018 (Performance Regression Suite, Sprint 18).

**Acceptance Criteria:**

1. **Performance Test File** `tests/test_performance.py`:
   - [ ] Marked with `@pytest.mark.perf` (separable from unit tests)
   - [ ] Uses `time.perf_counter()` for high-precision timing (not `datetime.utcnow()`)
   - [ ] Tests 8 endpoint latencies via TestClient:
     - `GET /health` — baseline < 10ms
     - `POST /deltas` — baseline < 50ms
     - `GET /deltas/{id}` — baseline < 30ms
     - `POST /intelligence-packet` — baseline < 200ms
     - `POST /sessions` (full game session → deltas) — baseline < 500ms
     - `POST /patterns` — baseline < 50ms
     - `GET /patterns` — baseline < 100ms
     - `GET /sessions` — baseline < 50ms
   - [ ] Tests 4 store operation latencies directly:
     - `DeltaStore.find_conflicts()` with 100 deltas — baseline < 100ms
     - `JudgmentStore.find_matching_patterns()` with 50 patterns — baseline < 150ms
     - `DeltaStore.get_pending_review()` with 100 pending — baseline < 50ms
     - `JudgmentStore.check_driver_guardrails()` with 20 guardrails — baseline < 50ms
   - [ ] Bulk data fixtures: `create_n_deltas(n)`, `create_n_patterns(n)` helpers
   - [ ] Each test runs 10 iterations, asserts p95 < threshold
   - [ ] All assertions use soft thresholds (2x baseline) to avoid CI flakiness

2. **Baseline Snapshot** `quality/perf_baseline.json`:
   - [ ] JSON file recording actual measured p50/p95/max for each operation
   - [ ] Generated by running `pytest tests/test_performance.py -v --perf-snapshot`
   - [ ] Or: a simple script / test that writes the snapshot after measurement

3. **Config Integration** `quality/config.yaml`:
   - [ ] Add `performance:` section with threshold values
   - [ ] Thresholds used by test assertions (not hardcoded in test file)

4. **Quality Gates:**
   - [ ] `pytest tests/test_performance.py -v` — all perf tests pass
   - [ ] `pytest tests/ -v` — all existing tests still pass (134+)
   - [ ] No source code modified (test infrastructure only)
   - [ ] No new dependencies (use stdlib `time`, `statistics`)
   - [ ] No test function > 50 lines

**Anti-Slop:**
- Do NOT add pytest-benchmark or other third-party perf libraries — use `time.perf_counter()` + stdlib `statistics`
- Do NOT modify any `src/` files — this is measurement only
- The intelligence-packet endpoint already captures `time_to_generate_ms` — read that pattern but don't duplicate it
- Reuse existing `conftest.py` fixtures (`client`, `sample_delta_payload`, etc.) — do NOT create parallel fixtures
- Thresholds are generous intentionally (in-memory stores, TestClient) — the goal is establishing a baseline, not enforcing production SLAs
- Keep bulk data realistic: use the same payload shapes as existing tests, just more of them

---

## Sprint 3/4 — HITL + Scenarios + Contribution + Curator + Smoke Tests

> CTX-006 DONE. LENS-004 DONE (167 tests). SEN-006 DONE. SEN-007 DONE (12 ADR files).
> CTX-018 DONE (82 tests). ATL-003 DONE (180 tests, 10/10 gold sets).
> **LENS-005 EXECUTE NOW** (Curator Dashboard). **SEN-008 EXECUTE NOW** (E2E Smoke Tests).

### TEAM CORTEX

#### CTX-006: HITL Routing Logic `DONE`

**Priority:** P0  |  **Est:** L  |  **Sprint:** 3
**Scope:** `src/core/models.py`, `src/core/stores.py`, `tests/test_core.py`
**Depends On:** CTX-005 DONE — `classify_delta()`, `get_required_approver()`, `Delta.judgment_type` all available
**Product Ref:** `product_management/epics/EPIC-003.md` (Governance), `src/core/models.py` (Governance, RiskClass)

**Objective:** Build the routing engine that assigns deltas to the correct review queue/role based on judgment type and blast radius. When a delta is proposed, it should be automatically routed to the right reviewer level. This is the core logic that LENS-004 will expose via API endpoints.

**Acceptance Criteria:**

1. **RoutingDecision dataclass** in `models.py`:
   - [ ] `assigned_to: str` — role that should review (system_auto, domain_expert, governance_board)
   - [ ] `queue: str` — queue name (auto, standard, escalated)
   - [ ] `priority: str` — review priority (low, normal, high, critical)
   - [ ] `sla_hours: int` — deadline for review
   - [ ] `reason: str` — why routed here

2. **`route_delta(delta: Delta) -> RoutingDecision`** function in `stores.py`:
   - [ ] Uses `delta.judgment_type` and `delta.blast_radius` to determine routing
   - [ ] Routing matrix:
     - EMPIRICAL + LOW → auto queue, system_auto, priority=low, sla=0
     - EMPIRICAL + MEDIUM → standard queue, domain_expert, priority=normal, sla=48
     - EMPIRICAL + HIGH → standard queue, domain_expert, priority=high, sla=24
     - CAUSAL + any → standard queue, domain_expert, priority=normal/high (by blast), sla=24
     - NORMATIVE + LOW/MEDIUM → escalated queue, governance_board, priority=high, sla=12
     - NORMATIVE + HIGH → escalated queue, governance_board, priority=critical, sla=5
   - [ ] Returns a RoutingDecision with reason explaining the routing

3. **DeltaStore enhancements**:
   - [ ] `propose()` — after classification, auto-set `delta.assigned_to` via `route_delta()`
   - [ ] `get_pending_for_role(role: str) -> List[Delta]` — filter pending deltas by `assigned_to`
   - [ ] `escalate(delta_id: str, reason: str) -> Optional[Delta]` — promote delta to next review level (domain_expert → governance_board), log reason in audit
   - [ ] `get_queue_stats() -> Dict[str, int]` — count of pending deltas per queue (auto, standard, escalated)

4. **Tests (8+ new)**:
   - [ ] `test_route_empirical_low_auto` — auto queue
   - [ ] `test_route_causal_medium_standard` — standard queue, domain_expert
   - [ ] `test_route_normative_high_escalated` — escalated queue, governance_board, critical
   - [ ] `test_propose_auto_routes` — propose() sets assigned_to
   - [ ] `test_get_pending_for_role` — filter by role
   - [ ] `test_escalate_delta` — domain_expert → governance_board
   - [ ] `test_escalate_nonexistent_400` — escalate missing delta returns None
   - [ ] `test_get_queue_stats` — correct counts per queue

5. **Quality:**
   - [ ] All existing tests still pass
   - [ ] No function > 50 lines
   - [ ] No new dependencies

**Anti-Slop:**
- `classify_delta()` and `get_required_approver()` already exist (CTX-005) — `route_delta()` builds ON them, do NOT duplicate classification logic
- `Delta.assigned_to` field already exists — use it, do NOT add new fields for routing
- `DeltaStore._log_audit()` already exists — use it for escalation audit entries
- `get_pending_review()` already sorts by blast_radius — `get_pending_for_role()` should filter the same way
- Keep routing matrix as data (dict/table), not if/elif chains

---

#### CTX-018: Contribution Tracking Store `EXECUTE NOW`

**Priority:** P1  |  **Est:** M  |  **Sprint:** 4 (pulled forward to Sprint 3)
**Scope:** `src/core/models.py`, `src/core/stores.py`, `src/core/__init__.py`, `tests/test_core.py`
**Depends On:** CTX-017 DONE — `ReasoningEvent`, `DeltaGenerator`, `Delta.owner`/`source_type`/`source_id` all available
**Product Ref:** `research/sme-impact-feedback-loops-research.md` (4-tier feedback), `product_management/02_backlog.md` (US-030), `product_management/epics/EPIC-003_governance.md`

**Objective:** Create a `ContributionStore` that tracks SME contributions — who proposed what, which deltas resulted, approval outcomes, and aggregated contributor profiles. This is the foundation for the SME Impact Dashboard (LENS-013) and the "digital twin of SME" vision. Scope is the **data layer only** — no API endpoints (LENS scope), no UI.

**Acceptance Criteria:**

1. **`Contribution` dataclass** in `models.py`:
   - [ ] `id: str` — UUID
   - [ ] `reasoning_event_id: str` — back-link to ReasoningEvent
   - [ ] `sme_id: str` — anonymized SME identifier
   - [ ] `sme_persona: str` — role (commercial_lead, access_strategist, etc.)
   - [ ] `delta_ids: List[str]` — deltas generated from this session
   - [ ] `contributed_at: datetime` — when the session was processed
   - [ ] `therapeutic_area: str` — from ScenarioContext
   - [ ] `scenario_type: str` — scenario name/type
   - [ ] `sme_confidence: float` — SME's self-reported confidence (0-1)

2. **`ContributionStore`** in `stores.py`:
   - [ ] `record(event: ReasoningEvent, delta_ids: List[str]) -> Contribution` — create and index a contribution
   - [ ] `get_by_sme(sme_id: str, limit: int = 50) -> List[Contribution]` — all contributions by an SME, newest first
   - [ ] `get_contributor_summary(sme_id: str) -> Dict[str, Any]` — aggregated stats:
     - `total_contributions: int`
     - `total_deltas: int`
     - `domains: Dict[str, int]` — count per therapeutic_area
     - `avg_confidence: float`
     - `last_contributed: Optional[datetime]`
   - [ ] `get_top_contributors(limit: int = 10) -> List[Dict[str, Any]]` — leaderboard by total_deltas
   - [ ] `stats() -> Dict[str, Any]` — store-level totals (total_contributions, unique_smes, total_deltas)
   - [ ] Internal indexes: `_by_sme_id`, `_by_therapeutic_area`
   - [ ] `_audit_log` with `_log_audit()` — follows existing store pattern

3. **Integration with DeltaGenerator**:
   - [ ] `process_sme_session()` in `delta_generator.py` — after generating deltas, call `ContributionStore.record()` if a store is provided
   - [ ] Pass `ContributionStore` as optional parameter (default None for backward compat)

4. **Exports** in `__init__.py`:
   - [ ] `Contribution` in model imports and `__all__`
   - [ ] `ContributionStore` in store imports and `__all__`

5. **Tests (8+ new)**:
   - [ ] `test_record_contribution` — record from ReasoningEvent, verify fields
   - [ ] `test_get_by_sme` — multiple contributions, correct ordering
   - [ ] `test_get_by_sme_empty` — unknown sme_id returns empty list
   - [ ] `test_contributor_summary` — stats computed correctly
   - [ ] `test_contributor_summary_unknown` — returns zeroed stats for unknown SME
   - [ ] `test_top_contributors` — ranked by total_deltas
   - [ ] `test_stats` — store-level totals
   - [ ] `test_process_sme_session_records_contribution` — end-to-end with DeltaGenerator

6. **Quality:**
   - [ ] All existing tests still pass
   - [ ] No function > 50 lines
   - [ ] No new dependencies

**Anti-Slop:**
- `Delta.owner`, `Delta.source_type`, `Delta.source_id` already exist — do NOT duplicate these fields on Contribution, just reference via `delta_ids`
- `ReasoningEvent` already has `sme_id`, `sme_persona`, `sme_confidence`, `scenario` — extract from these, do NOT add new fields to ReasoningEvent
- Follow the exact DeltaStore/JudgmentStore in-memory pattern: `Dict[str, obj]` + secondary indexes + audit log
- `process_sme_session()` is the integration point — make ContributionStore optional (don't break existing callers)
- Keep `get_contributor_summary()` as a computed aggregation, NOT a cached/stored entity — M-size ticket, not L
- Do NOT build Tier 1-4 reporting methods (LENS-013 scope) — just provide the raw data they'll query

---

### TEAM LENS

#### LENS-004: HITL Routing Endpoints + Audit Export API `DONE`

**Priority:** P0  |  **Est:** M  |  **Sprint:** 3
**Scope:** `src/api/server.py`, `src/api/schemas.py`, `tests/test_api.py`
**Depends On:** CTX-006 DONE — `route_delta()`, `get_pending_for_role()`, `escalate()`, `get_queue_stats()` all available
**Product Ref:** `product_management/epics/EPIC-003.md` (US-033, US-036)

**Objective:** Expose CTX-006's HITL routing logic via REST API. Add review queue endpoints, escalation endpoint, queue stats, and audit log export. These endpoints power the Curator Dashboard (LENS-005).

**IMPORTANT:** The CORTEX agent (CTX-006) already added routing endpoints to `server.py` and schemas to `schemas.py` during its implementation. **Read `server.py` lines 335-420 and `schemas.py` lines 349-381 FIRST** — you may find the work is partially or fully done. Your job is to verify, complete, and add tests.

**Acceptance Criteria:**

1. **Review Queue Endpoints** (verify/complete in `server.py`):
   - [ ] `GET /review-queue` — list pending deltas with routing metadata (queue, assigned_to, priority, sla_hours)
     - Query params: `role` (optional filter), `limit` (default 50, max 200)
     - Response: `List[ReviewQueueItem]` (delta + routing fields)
   - [ ] `GET /review-queue/stats` — queue counts
     - Response: `QueueStatsResponse` (auto, standard, escalated, total_pending)
   - [ ] `POST /deltas/{delta_id}/escalate` — escalate to next review level
     - Body: `EscalateRequest(reason: str)`
     - Response: updated `DeltaResponse`
     - 404 if delta not found, 400 if already at highest level

2. **Audit Export Endpoints** (verify/complete in `server.py`):
   - [ ] `GET /audit-log` — list audit entries
     - Query params: `limit` (default 100, max 500), `store` (optional: 'deltas' or 'judgments')
     - Response: `List[AuditEntryResponse]`
   - [ ] `GET /audit-log/export` — full audit export as JSON
     - Query params: `limit` (default 500, max 5000)
     - Content-Type: `application/json`

3. **Schemas** (verify/complete in `schemas.py`):
   - [ ] `ReviewQueueItem` — delta + queue + assigned_to + priority + sla_hours + reason + judgment_type
   - [ ] `QueueStatsResponse` — auto + standard + escalated + total_pending
   - [ ] `EscalateRequest` — reason: str
   - [ ] `AuditEntryResponse` — id + timestamp + actor + action + artifact_id + details

4. **Tests (6+ new in `tests/test_api.py`)**:
   - [ ] `test_review_queue_empty` — GET /review-queue returns empty list
   - [ ] `test_review_queue_with_deltas` — POST delta, GET /review-queue returns it with routing metadata
   - [ ] `test_review_queue_filter_by_role` — filter by `role=domain_expert`
   - [ ] `test_queue_stats` — GET /review-queue/stats returns correct counts
   - [ ] `test_escalate_delta` — POST escalate, verify assigned_to changes
   - [ ] `test_audit_log` — GET /audit-log returns entries after delta operations
   - [ ] `test_audit_export` — GET /audit-log/export returns JSON array

5. **Quality:**
   - [ ] All existing tests still pass
   - [ ] `npm run build` passes (no frontend changes expected)
   - [ ] No function > 50 lines
   - [ ] No new dependencies

**Anti-Slop:**
- CTX-006 may have ALREADY added these endpoints — READ before writing. Do NOT duplicate.
- `route_delta()` lives in `stores.py` — call it, don't reimplement
- `DeltaStore.get_pending_for_role()`, `.escalate()`, `.get_queue_stats()` already exist — wire them to endpoints
- Audit entries are already logged by `DeltaStore._log_audit()` — just expose them
- Use `ReviewQueueItem` schema (may already exist in `schemas.py`) — don't create a new schema if one exists
- If endpoints already exist and pass tests, mark as DONE and report what you found

---

#### LENS-005: Curator Dashboard MVP `EXECUTE NOW`

**Priority:** P0  |  **Est:** XL  |  **Sprint:** 4
**Scope:** `frontend/src/pages/CuratorDashboard.tsx`, `frontend/src/components/curator/`, `frontend/src/services/api.ts`, `frontend/src/types/`
**Depends On:** LENS-004 DONE (review-queue + audit-log endpoints), LENS-012 DONE (design system + persona modes)
**Product Ref:** `product_management/epics/EPIC-003.md` (US-031, US-032, US-033, US-034)

**Objective:** Build the Curator Dashboard — the primary interface for domain experts and governance reviewers to manage the delta review queue. Must display pending deltas with routing metadata, support approve/reject/escalate actions, show conflict warnings, and provide delta diff views. This is the centerpiece of the HITL governance workflow.

**Acceptance Criteria:**

1. **CuratorDashboard page** (`frontend/src/pages/CuratorDashboard.tsx`):
   - [ ] Route: `/curator` — accessible from PersonaMode selector (curator persona)
   - [ ] Layout: Queue panel (left, 60%) + Detail panel (right, 40%)
   - [ ] Queue panel shows pending deltas from `GET /review-queue` with:
     - Delta type badge (PROPOSED_PATTERN, PROPOSED_GUARDRAIL, etc.)
     - Judgment type indicator (Empirical/Causal/Normative with color coding)
     - Priority badge (low/normal/high/critical)
     - SLA countdown (hours remaining)
     - Assigned role
   - [ ] Queue stats summary bar at top using `GET /review-queue/stats`
   - [ ] Filter by role (system_auto, domain_expert, governance_board)
   - [ ] Sort by priority (default), SLA remaining, or date

2. **Delta Detail Panel** (`frontend/src/components/curator/DeltaDetail.tsx`):
   - [ ] Shows full delta payload when a queue item is selected
   - [ ] Diff view: before/after for entity changes (proposed_name, proposed_value)
   - [ ] Evidence section: shows delta's evidence references
   - [ ] Conflict indicator: if delta conflicts with existing (uses `GET /deltas/{id}` conflict data)
   - [ ] Action buttons: Approve, Reject (with reason), Escalate
   - [ ] Uses `PUT /deltas/{id}/approve`, `PUT /deltas/{id}/reject`, `POST /deltas/{id}/escalate`

3. **ReviewQueue component** (`frontend/src/components/curator/ReviewQueue.tsx`):
   - [ ] Fetches from `GET /review-queue?role=&limit=50`
   - [ ] Auto-refreshes every 30 seconds (configurable)
   - [ ] Empty state: "No deltas pending review"
   - [ ] Loading state: skeleton cards
   - [ ] Error state: retry button

4. **QueueStats component** (`frontend/src/components/curator/QueueStats.tsx`):
   - [ ] Three stat cards: Auto queue, Standard queue, Escalated queue
   - [ ] Total pending count
   - [ ] Fetches from `GET /review-queue/stats`

5. **AuditTrail component** (`frontend/src/components/curator/AuditTrail.tsx`):
   - [ ] Collapsible audit log panel at bottom of dashboard
   - [ ] Fetches from `GET /audit-log?limit=50`
   - [ ] Shows: timestamp, actor, action, artifact_id
   - [ ] "Export All" button → `GET /audit-log/export` triggers JSON download

6. **API service additions** (`frontend/src/services/api.ts`):
   - [ ] `fetchReviewQueue(role?: string, limit?: number): Promise<ReviewQueueItem[]>`
   - [ ] `fetchQueueStats(): Promise<QueueStatsResponse>`
   - [ ] `escalateDelta(deltaId: string, reason: string): Promise<DeltaResponse>`
   - [ ] `fetchAuditLog(limit?: number, store?: string): Promise<AuditEntry[]>`
   - [ ] `exportAuditLog(limit?: number): Promise<Blob>` — downloads as JSON

7. **Types** (`frontend/src/types/curator.ts`):
   - [ ] `ReviewQueueItem` — mirrors backend schema
   - [ ] `QueueStatsResponse` — mirrors backend schema
   - [ ] `AuditEntry` — mirrors backend schema

8. **Routing + Navigation**:
   - [ ] Add `/curator` route in app router
   - [ ] Add "Curator Dashboard" link in sidebar/nav (visible in curator persona mode)
   - [ ] PersonaMode.CURATOR selects this as default view

9. **Quality:**
   - [ ] `npm run build` — 0 errors
   - [ ] `npm run lint` — 0 warnings
   - [ ] No component > 50 lines (decompose into sub-components)
   - [ ] No new npm dependencies (use existing Tailwind, React, ReactFlow)
   - [ ] All existing tests still pass (`pytest tests/ -v`)

**Anti-Slop:**
- Backend endpoints ALL exist (LENS-004) — this is pure frontend. Do NOT modify `server.py` or `schemas.py`.
- Design system exists (LENS-012) — use existing Tailwind classes, color tokens, and component patterns from `frontend/src/components/ui/`
- Persona modes exist (LENS-012) — `PersonaMode.CURATOR` is already defined. Wire it to the new route.
- `frontend/src/services/api.ts` already has patterns for `fetch` calls — follow the existing error handling pattern
- Approve/Reject endpoints already exist (`PUT /deltas/{id}/approve`, `PUT /deltas/{id}/reject`) — wire them, don't recreate
- Do NOT add state management libraries (Redux, Zustand) — use React state + custom hooks
- Do NOT add charting libraries yet — queue stats are simple number displays
- `GET /review-queue` returns items with routing metadata (queue, assigned_to, priority, sla_hours) — display all of it
- The dashboard is READ-HEAVY with action buttons. Optimize for scan-ability: badges, color coding, clear hierarchy

---

### TEAM SENTINEL

#### SEN-008: End-to-End Smoke Test Suite `EXECUTE NOW`

**Priority:** P1  |  **Est:** L  |  **Sprint:** 4 (pulled forward from Sprint 8 — SENTINEL idle)
**Scope:** `tests/test_e2e_smoke.py`
**Depends On:** None — all endpoints and stores are stable (180 tests passing)
**Product Ref:** SEN-005 (Performance Baseline — existing perf tests for pattern), `tests/test_api.py` (existing API test patterns)

**Objective:** Create an end-to-end smoke test suite that exercises the full Onto_Wiz pipeline from session submission through delta generation, review queue, approval, and audit trail. These tests validate that the entire system works as an integrated whole, not just individual units. They serve as the regression backbone for all future sprints.

**Acceptance Criteria:**

1. **Test File** `tests/test_e2e_smoke.py`:
   - [ ] Marked with `@pytest.mark.e2e` (separable from unit tests via `pytest -m e2e`)
   - [ ] Uses existing `TestClient` from conftest (same pattern as `test_api.py`)
   - [ ] Each test is a complete user journey, not an isolated API call

2. **Smoke Test Scenarios (8+ tests)**:
   - [ ] `test_full_game_session_pipeline` — POST /sessions with full 9-step game responses → verify deltas generated → verify deltas appear in GET /review-queue → verify routing metadata present
   - [ ] `test_delta_approve_flow` — POST delta → GET review-queue confirms pending → PUT /deltas/{id}/approve → verify status=APPROVED → verify audit-log entry
   - [ ] `test_delta_reject_flow` — POST delta → PUT /deltas/{id}/reject with reason → verify status=REJECTED → verify audit-log captures rejection reason
   - [ ] `test_escalation_flow` — POST delta (CAUSAL type) → POST /deltas/{id}/escalate → verify assigned_to changes from domain_expert to governance_board → verify audit entry
   - [ ] `test_conflict_detection_e2e` — POST two conflicting deltas → GET /deltas/{id} shows conflicts → verify conflict_ids populated
   - [ ] `test_pattern_matching_e2e` — POST pattern + POST session with matching tags → verify intelligence-packet includes matched pattern with score
   - [ ] `test_guardrail_enforcement_e2e` — POST guardrail → POST intelligence-packet with blocked driver → verify guardrail fires in response
   - [ ] `test_audit_trail_completeness` — Run 5 operations (propose, approve, reject, escalate, pattern create) → GET /audit-log → verify all 5 appear in order with correct actors/actions
   - [ ] `test_queue_stats_accuracy` — POST 3 deltas of different types (EMPIRICAL/CAUSAL/NORMATIVE) → GET /review-queue/stats → verify auto/standard/escalated counts match expected routing

3. **Helper Functions** (reusable within the test file):
   - [ ] `create_game_session(client) -> dict` — submits a full session, returns response with session_id and delta_ids
   - [ ] `create_delta(client, delta_type, blast_radius) -> dict` — submits a delta with specific type/blast, returns response
   - [ ] `approve_delta(client, delta_id, reviewer) -> dict` — approves and returns response
   - [ ] `reject_delta(client, delta_id, reviewer, reason) -> dict` — rejects and returns response

4. **Quality Gates:**
   - [ ] `pytest tests/test_e2e_smoke.py -v` — all smoke tests pass
   - [ ] `pytest tests/ -v` — all existing tests still pass (180+)
   - [ ] No source code modified (`src/` untouched — tests only)
   - [ ] No new dependencies (use stdlib + pytest + TestClient)
   - [ ] No test function > 50 lines (use helpers to decompose)
   - [ ] Tests are order-independent (each test sets up its own data)

**Anti-Slop:**
- Do NOT modify any `src/` files — this is test infrastructure only
- Reuse existing `conftest.py` fixtures (`client`, `_reset_stores`, `sample_delta_payload`, etc.) — do NOT create parallel fixtures
- Read `tests/test_api.py` FIRST to understand existing test patterns (how payloads are structured, how delta creation works, etc.)
- Read `tests/test_performance.py` FIRST to see how SEN-005 structured its test file (you should follow similar organization)
- The full session payload format is in `tests/test_api.py` → search for `POST /sessions` test — use that exact payload structure
- Routing matrix: EMPIRICAL+LOW=auto, CAUSAL+MEDIUM=standard/domain_expert, NORMATIVE+HIGH=escalated/governance_board — use these known mappings
- `conftest.py` has `_reset_stores` that clears all stores between tests — rely on it for test isolation
- Do NOT add pytest plugins (pytest-ordering, pytest-dependency) — tests must be independently runnable
- Keep each smoke test focused on ONE user journey. A smoke test that tests everything tests nothing.

---

### TEAM CORTEX

#### CTX-008: Enhanced Audit Trail `EXECUTE NOW`

**Priority:** P1  |  **Est:** M  |  **Sprint:** 5 (pulled forward — CORTEX idle)
**Scope:** `src/core/models.py`, `src/core/stores.py`, `src/core/__init__.py`, `tests/test_core.py`
**Depends On:** CTX-005 DONE — `Delta.owner`, `Delta.judgment_type`, governance fields all available
**Product Ref:** `product_management/epics/EPIC-003_governance.md` (US-035), `src/api/server.py` (existing audit endpoints)

**Objective:** Enhance the `AuditEntry` model with richer context (store_type, action_category, actor standardization, before/after snapshots) and standardize `_log_audit` across all 3 stores. Add a unified audit query function that merges logs from all stores with filtering. This is the data-layer enhancement — API changes are LENS scope.

**Acceptance Criteria:**

1. **Enhanced `AuditEntry`** in `models.py`:
   - [ ] `store_type: str = ""` — which store produced this entry (delta, judgment, contribution)
   - [ ] `action_category: str = ""` — lifecycle category (create, approve, reject, escalate, merge, record)
   - [ ] `before_snapshot: Dict[str, Any]` — state before the action (empty for creates)
   - [ ] `after_snapshot: Dict[str, Any]` — state after the action
   - [ ] All new fields have defaults — backward compatible

2. **Standardize `_log_audit` across all 3 stores**:
   - [ ] DeltaStore: set `actor` from reviewer param, `store_type="delta"`, populate `action_category`
   - [ ] JudgmentStore: set `actor` from approver param, `store_type="judgment"`, populate `action_category`
   - [ ] ContributionStore: set `actor` from sme_id, `store_type="contribution"`, populate `action_category`
   - [ ] All stores capture `before_snapshot` and `after_snapshot` for state-changing operations (approve, reject, escalate)

3. **Unified audit query** in `stores.py`:
   - [ ] `get_combined_audit_log(stores, limit, action, actor, store_type) -> List[AuditEntry]`
   - [ ] Merges logs from all provided stores
   - [ ] Sorts by timestamp descending (newest first)
   - [ ] Supports filtering by action, actor, store_type (all optional)

4. **Store-level filtering**:
   - [ ] Each store's `get_audit_log()` gains optional `action: str = None` filter param

5. **Exports** in `__init__.py`:
   - [ ] `get_combined_audit_log` added to imports and `__all__`

6. **Tests (8+ new)**:
   - [ ] `test_audit_entry_store_type` — DeltaStore entries have store_type="delta"
   - [ ] `test_audit_entry_actor` — approve/reject entries capture reviewer as actor
   - [ ] `test_audit_entry_action_category` — entries have correct category
   - [ ] `test_audit_before_after_snapshot` — approve captures before=PROPOSED, after=APPROVED
   - [ ] `test_judgment_store_audit_actor` — JudgmentStore entries capture approver
   - [ ] `test_contribution_store_audit_sme` — ContributionStore entries capture sme_id as actor
   - [ ] `test_combined_audit_log` — merges from 3 stores, sorted by timestamp
   - [ ] `test_combined_audit_log_filter` — filter by action/actor/store_type

7. **Quality:**
   - [ ] All existing tests still pass
   - [ ] No function > 50 lines
   - [ ] No new dependencies

**Anti-Slop:**
- `AuditEntry` already exists with 7 fields — EXTEND it, do NOT create a new class
- `_log_audit` exists in all 3 stores — enhance the existing method signature, do NOT create a base class or mixin (M-size ticket)
- `get_combined_audit_log` is a MODULE-LEVEL function, not a class — it takes stores as args
- `before_snapshot`/`after_snapshot` should be minimal dicts (just status + key fields), NOT full object serialization
- Do NOT modify API endpoints or schemas — that's LENS scope
- Do NOT add multi-tenant fields (client_id, mission_id) yet — that's a future ticket
- Existing `_log_audit` callers must continue to work — add params with defaults

---

## Sprint 6 — Review Cycles + Intelligence Viewer

> Sprint 6 ACTIVE — CTX-007 in flight.

### TEAM CORTEX

#### CTX-007: Review Cycle Enforcement `EXECUTE NOW`

**Priority:** P1  |  **Est:** S  |  **Sprint:** 6
**Scope:** `src/core/models.py`, `src/core/stores.py`, `tests/test_core.py`
**Depends On:** CTX-005 DONE — `Governance` dataclass with `review_cycle`, `approved_on`, `risk_class` fields
**Product Ref:** `product_management/epics/EPIC-003_governance.md` (US-034: Track Review Cycles)

**Objective:** Enforce review cycles on governed artifacts (patterns, guardrails, action templates). The `Governance.review_cycle` field exists ("quarterly"/"monthly"/"annual") but has zero enforcement. Add logic to convert review_cycle to days, detect overdue artifacts, and integrate into store queries. This is governance staleness — orthogonal to `DecayConfig` scientific staleness.

**Key Distinction:**
- **Decay** = scientific freshness ("is this knowledge still valid?")
- **Review Cycle** = governance freshness ("has a human re-confirmed this recently?")
- A pattern can be scientifically fresh but governance-stale (or vice versa)

**Acceptance Criteria:**

1. **`Governance` helper** in `models.py`:
   - [ ] `get_review_cycle_days() -> int` — lookup table: monthly→30, quarterly→90, annual→365, default→90
   - [ ] `is_review_due() -> bool` — True if approved_on + review_cycle_days <= now. False if not yet approved.
   - [ ] `days_until_review() -> Optional[int]` — days remaining (negative if overdue), None if not approved

2. **`JudgmentStore` methods** in `stores.py`:
   - [ ] `get_patterns_due_for_review(include_upcoming_days: int = 0) -> List[JudgmentPattern]` — returns approved patterns where review is due or upcoming within N days
   - [ ] `get_guardrails_due_for_review(include_upcoming_days: int = 0) -> List[Guardrail]` — same for guardrails
   - [ ] `get_review_summary() -> Dict[str, Any]` — counts of overdue patterns, guardrails, action_templates; lists of overdue IDs

3. **Exports** in `__init__.py`:
   - [ ] No new exports needed (methods are on existing classes)

4. **Tests (6+ new)**:
   - [ ] `test_review_cycle_days_mapping` — quarterly→90, monthly→30, annual→365
   - [ ] `test_is_review_due_not_approved` — returns False for unapproved artifact
   - [ ] `test_is_review_due_fresh` — returns False for recently approved
   - [ ] `test_is_review_due_overdue` — returns True when past cycle
   - [ ] `test_get_patterns_due_for_review` — store method returns overdue patterns
   - [ ] `test_get_review_summary` — correct counts

5. **Quality:**
   - [ ] All existing tests still pass
   - [ ] No function > 50 lines
   - [ ] No new dependencies

**Anti-Slop:**
- `Governance` already has `review_cycle: str` and `approved_on: Optional[datetime]` — USE these, do NOT add new fields
- Use a lookup dict for cycle→days mapping, NOT if/elif
- `is_review_due()` goes on `Governance`, NOT on each artifact class (DRY)
- Do NOT build a scheduler or notification system — that's LENS scope
- Do NOT modify `get_active_patterns()` or `get_stale_patterns()` — review cycle is a separate query, not a filter on active
- Do NOT add review_cycle logic to DeltaStore — deltas are short-lived proposals, not governed artifacts
- Keep total new lines under 50

---

## Sprint 9 — Reasoning Unification + Intelligence Viewer + Ontology Expansion

> Sprint 9 — The Pivot Sprint. Per `product_management/state_of_the_project.md`: stop adding governance features, start making the reasoning work.
> Priority rebalancing: pull forward reasoning unification (CTX-041), defer governance plumbing (CTX-010/011 → Sprint 12+).

### TEAM CORTEX

#### CTX-041: Unify Reasoning Paths — YAML Rules + JudgmentPatterns `EXECUTE NOW`

**Priority:** P0  |  **Est:** M  |  **Sprint:** 9
**Scope:** `src/reasoning/engine.py`, `tests/test_reasoning.py`
**Depends On:** CTX-001 DONE (pattern matching v2), CTX-019 DONE (semantic search)
**Product Ref:** `product_management/state_of_the_project.md` (Section: "The Architecture's Honest Problem")

**Objective:** Eliminate the two disconnected reasoning paths. Currently:
- **Path A (ReasoningEngine):** Static YAML rules → tag matching → winning rule → verdict. Cannot learn from SME input. Not connected to JudgmentStore.
- **Path B (JudgmentStore):** Game session → delta → approval → pattern → `find_matching_patterns()` → intelligence packet. Can learn but doesn't reason — it's retrieval, not inference.

Wire `JudgmentStore.find_matching_patterns()` into `ReasoningEngine._find_winning_rule()` so that approved JudgmentPatterns compete alongside static YAML rules in a single priority-ranked evaluation. One source of truth for inference.

**Key Design Decisions:**
- **JudgmentStore passed as optional parameter** — dependency injection via `__init__`, default `None`. Backward compatible: without a store, engine works exactly as before (YAML only).
- **Approved patterns converted to rule format** — adapter function converts `JudgmentPattern` → rule dict that `_find_winning_rule()` can evaluate. Fields mapped: `applies_when_signals` → `conditions[].args`, `typical_drivers` → `consequence.risk`/`verdict`, `match_score()` → effective priority.
- **Priority resolution:** Static YAML rules use `priority` (0-100). JudgmentPatterns use `match_score()` (0.0-1.0) × configurable base priority (default 50). This means high-scoring learned patterns compete with mid-priority static rules, but static safety rules (P90+) always win.
- **`_build_response` enhanced** — when the winning "rule" is a JudgmentPattern, build the response from pattern fields (drivers, evidence, governance metadata), not YAML consequence fields.
- **No modification to JudgmentStore or models.py** — this is a consumer change in the reasoning engine only.

**Acceptance Criteria:**

1. **`ReasoningEngine.__init__` signature change:**
   - [ ] Add `judgment_store: Optional[JudgmentStore] = None` parameter
   - [ ] Store as `self._judgment_store`
   - [ ] Existing callers with `(ontology, data)` still work (backward compat)

2. **`_pattern_to_rule(pattern: JudgmentPattern) -> Dict[str, Any]`** helper on ReasoningEngine:
   - [ ] Converts JudgmentPattern to the dict format `_find_winning_rule` expects
   - [ ] Maps `applies_when_signals` → conditions with `tag_match` pattern
   - [ ] Maps `match_score` × `LEARNED_PRIORITY_BASE` (default 50) → priority
   - [ ] Maps `typical_drivers[0].driver` → `consequence.risk` (if drivers exist)
   - [ ] Maps pattern `name` + driver descriptions → `consequence.verdict`
   - [ ] Adds `_source: "judgment_store"` marker and `_pattern_id` to the dict for downstream identification
   - [ ] Under 30 lines

3. **`_find_winning_rule` enhancement:**
   - [ ] After loading static YAML rules, also fetch JudgmentStore patterns via `find_matching_patterns(signals_from_active_tags, {})` if store is present
   - [ ] Convert each matching pattern to rule format via `_pattern_to_rule()`
   - [ ] Merge into the same rule list, sorted by effective priority descending
   - [ ] Return the highest-priority match (static or learned)
   - [ ] Under 25 lines (was 10, grows to ~20)

4. **`_build_response` enhancement:**
   - [ ] Detect if winning rule has `_source: "judgment_store"` marker
   - [ ] If learned: use pattern's `typical_drivers` for risks, pattern name for verdict prefix, pattern's governance metadata in evidence tags
   - [ ] If static: existing behavior unchanged
   - [ ] Under 25 lines (was 15, grows to ~22)

5. **`LEARNED_PRIORITY_BASE` class constant:**
   - [ ] `LEARNED_PRIORITY_BASE: int = 50` — base priority for learned patterns
   - [ ] Effective priority = `match_score * LEARNED_PRIORITY_BASE` (so a perfect 1.0 match = priority 50, competing with mid-range static rules)
   - [ ] Documented: safety rules (P90+) always win over learned patterns

6. **Tests (8+ new in `tests/test_reasoning.py`):**
   - [ ] `test_engine_without_store_unchanged` — existing behavior preserved when `judgment_store=None`
   - [ ] `test_engine_with_empty_store` — no patterns, falls back to YAML rules
   - [ ] `test_learned_pattern_wins_over_low_priority_rule` — approved pattern with matching signals beats a P40 YAML rule
   - [ ] `test_static_safety_rule_wins_over_learned` — P90 safety rule always beats learned pattern (even 1.0 match)
   - [ ] `test_pattern_to_rule_conversion` — correct field mapping
   - [ ] `test_learned_pattern_builds_driver_response` — response includes pattern's typical_drivers, not YAML consequence
   - [ ] `test_multiple_learned_patterns_highest_score_wins` — ranked correctly
   - [ ] `test_mixed_rules_and_patterns_priority_order` — interleaving works

7. **Quality:**
   - [ ] All existing reasoning tests still pass
   - [ ] All 247+ tests pass (`pytest tests/ -v`)
   - [ ] No function > 50 lines
   - [ ] No new dependencies
   - [ ] No modification to `src/core/` (engine is a consumer, not a modifier)

**Anti-Slop:**
- `JudgmentStore.find_matching_patterns()` at `stores.py:488` returns `List[Tuple[JudgmentPattern, float]]` — use the float as match_score, don't recompute
- `JudgmentPattern.typical_drivers` is `List[DriverAttribution]` where each has `.driver` (name) and `.prior_confidence` — use these for response building
- `ReasoningEngine` lives in `src/reasoning/engine.py` — it CAN import from `src/core/` (architecture boundary allows `reasoning → core`)
- Do NOT add SemanticStore to the engine — semantic expansion is JudgmentStore's responsibility (CTX-019). The engine just passes signals; the store expands them.
- Do NOT modify `_check_rule_conditions` — learned patterns don't use it (they use `match_score` directly)
- Do NOT change the `ReasoningResponse` dataclass — use existing fields
- Do NOT add graph traversal or multi-step chaining — that's a future ticket. This ticket unifies the two paths; it doesn't build a new inference engine.
- Keep the adapter pattern (`_pattern_to_rule`) so the core evaluation loop has ONE code path, not two parallel if/else branches
- `_filter_signals` stays unchanged — it produces `active_tags` which are passed to both YAML rule checking AND `find_matching_patterns`

---

### TEAM LENS

#### LENS-014: Intelligence Packet Viewer `EXECUTE NOW`

**Status:** IN_PROGRESS:SPEC (mini-spec written in Dev2Lead.md, approved)
**Priority:** P0  |  **Est:** L  |  **Sprint:** 9
**Scope:** See Dev2Lead.md → LENS-014 mini-spec for full deliverables (16 files, ~400 lines)
**Depends On:** LENS-012 DONE (design system), CTX-019 DONE (semantic search)

**Objective:** Build the Intelligence Packet Viewer at `/intelligence` — the "make the product visible" ticket. Display the core output of Onto_Wiz: signal summary, driver rankings, action recommendations, guardrail flags, evidence trace, pattern provenance.

**Note:** Full acceptance criteria and deliverable list in Dev2Lead.md LENS-014 mini-spec (approved 2026-02-16). Proceed to IMPL phase.

---

### TEAM ATLAS

#### ATL-006: Immunology Therapeutic Area — Taxonomy + Scenarios `EXECUTE NOW`

**Priority:** P1  |  **Est:** L  |  **Sprint:** 9 (pulled forward from Sprint 6)
**Scope:** `ontology/therapeutic_areas/`, `ontology/scenarios/`, `tests/gold_set/scenarios/`
**Depends On:** ATL-001 DONE — commercial ontology available
**Product Ref:** ATL-002 (oncology format), `ontology/therapeutic_areas/` (existing TA structure)

**Objective:** Create immunology therapeutic area taxonomy files and 3 immunology-specific scenarios. Expand gold set coverage beyond oncology. Follow exact format from ATL-002 (oncology deep taxonomy).

**Acceptance Criteria:**

1. **Taxonomy Files** in `ontology/therapeutic_areas/`:
   - [ ] `immunology_indications.yaml` — indication subtypes (RA, psoriasis, lupus, IBD, atopic dermatitis, etc.)
   - [ ] `immunology_biomarkers.yaml` — relevant biomarkers (TNF-alpha, IL-17, IL-23, JAK pathway, etc.)
   - [ ] Follow exact structure from `oncology_indications.yaml` and `oncology_biomarkers.yaml`

2. **3 Scenario Files** in `ontology/scenarios/`:
   - [ ] `IMM-001-ra-biosimilar-switch.yaml` — RA biosimilar switch dynamics
   - [ ] `IMM-002-psoriasis-il23-sequencing.yaml` — IL-23 inhibitor sequencing
   - [ ] `IMM-003-ibd-jak-safety-monitoring.yaml` — JAK inhibitor safety concern
   - [ ] Follow exact schema from `ONC-001` through `ONC-010`

3. **2 Gold Set Scenarios** in `tests/gold_set/scenarios/`:
   - [ ] `GOLD-019-biosimilar-switch-pressure.yaml` — tests rule_biosimilar_erosion with immunology context
   - [ ] `GOLD-020-safety-signal-immunology.yaml` — tests rule_safety_signal with immunology signals
   - [ ] Use existing inference rules (no new rules needed)

4. **Quality:**
   - [ ] All gold set tests pass: `pytest tests/gold_set/ -v`
   - [ ] All existing tests pass: `pytest tests/ -v`
   - [ ] All YAML files parse correctly
   - [ ] No source code modified

**Anti-Slop:**
- Follow EXACT format from existing TA files — do NOT invent new schema
- Gold sets must match existing inference rules (check `commercial.yaml` for tag vocabulary)
- Use clinically accurate immunology terminology
- Do NOT modify any source code files

---

### TEAM SENTINEL

#### SEN-009: Load Testing Framework `EXECUTE NOW`

**Priority:** P1  |  **Est:** M  |  **Sprint:** 9
**Scope:** `tests/perf/`, `quality/config.yaml`
**Depends On:** SEN-005 DONE — performance baselines available
**Product Ref:** `tests/test_performance.py` (existing perf tests), `quality/perf_baseline.json` (baselines)

**Objective:** Create a load testing framework that tests system behavior under concurrent load. Exercise store operations and API endpoints with realistic data volumes (100+ deltas, 50+ patterns, 10+ concurrent requests). Identify degradation thresholds.

**Acceptance Criteria:**

1. **Load Test File** `tests/perf/test_load.py`:
   - [ ] Marked with `@pytest.mark.perf` (same as performance tests)
   - [ ] Uses `concurrent.futures.ThreadPoolExecutor` for concurrency (stdlib only)
   - [ ] Tests 4 load scenarios:
     - Store operations at scale: 500 deltas, 200 patterns → measure find_matching_patterns latency
     - Concurrent delta proposals: 10 threads × 10 deltas each → no data corruption
     - Concurrent read/write mix: 5 writers + 5 readers → no crashes, readers get consistent data
     - API endpoint throughput: 50 requests to GET /health, GET /patterns → measure p95
   - [ ] Each test has pass/fail threshold (2x single-thread baseline from SEN-005)

2. **Quality:**
   - [ ] `pytest tests/perf/test_load.py -v` — all tests pass
   - [ ] All existing tests pass
   - [ ] No source code modified
   - [ ] No new dependencies (stdlib `concurrent.futures`, `threading`, `statistics`)
   - [ ] No test function > 50 lines

**Anti-Slop:**
- Do NOT add locust, k6, or other load testing frameworks — use stdlib `concurrent.futures`
- Do NOT modify any `src/` files
- Reuse existing `conftest.py` fixtures
- Thresholds are 2x baseline (generous) — goal is framework, not strict SLAs
- Keep concurrency realistic for in-memory stores — 10 threads, not 1000

---

## Sprint 8 — Semantic Search + Progressive Disclosure

> Sprint 8 COMPLETE — CTX-019 delivered.

### TEAM CORTEX

#### CTX-019: Semantic Search over Patterns + Evidence `DONE`

**Priority:** P1  |  **Est:** L  |  **Sprint:** 8
**Scope:** `src/core/stores.py`, `src/core/evidence.py`, `tests/test_core.py`, `tests/test_graph_evidence.py`
**Depends On:** None (SemanticStore, JudgmentStore, EvidenceStore all exist)

**Objective:** Bridge the SemanticStore synonym/alias layer into pattern and evidence search. Currently, `find_matching_patterns()` requires exact signal names and `find_for_hypothesis()` requires exact entity_ref strings. Users searching for "PA barriers" won't find patterns tagged with "Prior_Authorization" or evidence referencing "Prior Auth". This ticket adds semantic expansion to both search paths.

**Key Concepts:**
- **Query expansion** = take search terms, resolve through SemanticStore to get all variants (canonical + synonyms + aliases), then search with expanded set
- **Semantic pattern search** = new method on JudgmentStore that accepts raw terms, expands via SemanticStore, then delegates to `find_matching_patterns()`
- **Semantic evidence search** = new method on EvidenceStore that expands hypothesis label via SemanticStore before searching
- SemanticStore is passed as dependency (parameter), NOT imported as global — keeps stores decoupled

**Acceptance Criteria:**

1. **`JudgmentStore` methods** in `stores.py`:
   - [ ] `semantic_find_patterns(query_terms: List[str], context: Dict, semantic_store: SemanticStore, min_score: float = 0.3) -> List[Tuple[JudgmentPattern, float]]` — expand query_terms through SemanticStore, then call `find_matching_patterns()` with expanded set
   - [ ] `expand_signals(signals: List[str], semantic_store: SemanticStore) -> List[str]` — resolve each signal through SemanticStore to get canonical + all variants, return deduplicated expanded list

2. **`EvidenceStore` methods** in `evidence.py`:
   - [ ] `semantic_find_evidence(query: str, semantic_store: SemanticStore, min_reliability: ReliabilityClass = ReliabilityClass.RUMOR) -> List[EvidenceItem]` — expand query through SemanticStore, search expanded terms against entity_refs and claim text
   - [ ] `search_by_text(query: str, fields: List[str] = None) -> List[EvidenceItem]` — basic text search across title, content, and claims (case-insensitive substring match). This is a prerequisite for semantic search but also useful standalone.

3. **Tests (8+ new)**:
   - [ ] `test_expand_signals_with_synonyms` — "PA" expands to include "Prior_Authorization"
   - [ ] `test_expand_signals_unknown_term` — unknown terms pass through unchanged
   - [ ] `test_semantic_find_patterns` — finds patterns via expanded signals
   - [ ] `test_semantic_find_patterns_no_store` — graceful behavior without semantic store
   - [ ] `test_search_by_text` — basic text search across evidence fields
   - [ ] `test_semantic_find_evidence` — finds evidence via expanded query
   - [ ] `test_expand_includes_canonical_and_variants` — expansion includes both directions
   - [ ] `test_semantic_search_no_false_positives` — unrelated terms don't match

4. **Quality:**
   - [ ] All existing tests still pass
   - [ ] No function > 50 lines
   - [ ] SemanticStore passed as parameter, NOT hardcoded dependency

**Anti-Slop:**
- Do NOT modify existing `find_matching_patterns()` or `find_for_hypothesis()` — add new semantic-aware wrappers that call them
- Do NOT add vector/embedding search — this is synonym-based expansion only (vector search is a future ticket)
- `expand_signals` is a pure function (signals in → expanded signals out), keep it testable
- SemanticStore already has `resolve_to_canonical()` and `get_all_variants()` — use those, don't reimplement
- Text search is case-insensitive substring match, NOT regex — keep it simple
- Do NOT add new imports to `__init__.py` unless a new public class is created (methods on existing classes don't need new exports)

---

## Sprint 7 — Pattern Consolidation + Graph Explorer

> Sprint 7 ACTIVE — CTX-009 in flight.

### TEAM CORTEX

#### CTX-009: Pattern Consolidation / Reconciler `EXECUTE NOW`

**Priority:** P1  |  **Est:** L  |  **Sprint:** 7
**Scope:** `src/core/models.py`, `src/core/stores.py`, `tests/test_core.py`
**Depends On:** CTX-001 DONE — pattern matching v2, ranked scoring available
**Product Ref:** `product_management/epics/EPIC-002.md` (Knowledge Quality)

**Objective:** Build a reconciler that detects overlapping/duplicate patterns in the JudgmentStore, computes similarity scores, and can consolidate (merge) two patterns into one. When patterns are consolidated, the superseded pattern is deprecated with lineage tracking (`superseded_by`). This prevents pattern drift where SME sessions slowly create near-duplicate patterns with slightly different signals.

**Key Concepts:**
- **Overlap** = two patterns share ≥50% of their `applies_when_signals`
- **Consolidation** = merge two patterns: union signals, union context, union drivers, combine scenarios, keep higher governance (stricter review cycle, higher risk class)
- **Lineage** = deprecated pattern gets `superseded_by: str` pointing to the consolidated pattern
- Reconciler is a **query + suggestion tool** — it finds candidates, humans decide

**Acceptance Criteria:**

1. **`JudgmentPattern` extension** in `models.py`:
   - [ ] `superseded_by: Optional[str] = None` — ID of the pattern that replaced this one (set on deprecation via consolidation)

2. **`JudgmentStore` methods** in `stores.py`:
   - [ ] `compute_pattern_similarity(a_id: str, b_id: str) -> float` — Jaccard similarity of `applies_when_signals` (intersection / union). Returns 0.0 if either pattern not found.
   - [ ] `find_overlapping_patterns(min_similarity: float = 0.5) -> List[Tuple[str, str, float]]` — scan all active patterns pairwise, return pairs with similarity ≥ threshold. Returns list of (id_a, id_b, similarity) sorted by similarity descending.
   - [ ] `consolidate_patterns(keep_id: str, merge_id: str, actor: str) -> Optional[JudgmentPattern]` — merge `merge_id` into `keep_id`:
     - Union `applies_when_signals` (deduplicated)
     - Union `applies_when_context` (deduplicated)
     - Merge `typical_drivers` (union by driver name, keep higher confidence)
     - Union `disallowed_drivers`
     - Union `trained_from_scenarios`
     - Bump `version` (increment minor: "1.0.0" → "1.1.0")
     - Deprecate `merge_id`, set `superseded_by = keep_id`
     - Audit log both operations (consolidate + deprecate)
     - Return updated `keep` pattern (or None if either ID not found / not APPROVED)
   - [ ] `get_consolidation_candidates(min_similarity: float = 0.5) -> List[Dict[str, Any]]` — user-friendly report: list of {pattern_a_id, pattern_b_id, similarity, shared_signals, total_signals_a, total_signals_b}

3. **No new exports** in `__init__.py` — methods on existing classes.

4. **Tests (8+ new)**:
   - [ ] `test_superseded_by_default_none` — field exists, defaults to None
   - [ ] `test_compute_pattern_similarity_full_overlap` — identical signals → 1.0
   - [ ] `test_compute_pattern_similarity_no_overlap` — disjoint signals → 0.0
   - [ ] `test_compute_pattern_similarity_partial` — partial overlap → correct Jaccard
   - [ ] `test_find_overlapping_patterns` — returns pairs above threshold
   - [ ] `test_consolidate_patterns_merges_signals` — union of signals/context/drivers
   - [ ] `test_consolidate_patterns_deprecates_source` — merge_id deprecated, superseded_by set
   - [ ] `test_consolidate_patterns_version_bump` — version incremented
   - [ ] `test_consolidate_patterns_audit_logged` — audit entries created
   - [ ] `test_get_consolidation_candidates` — returns user-friendly report

5. **Quality:**
   - [ ] All existing 102 tests still pass
   - [ ] No function > 50 lines
   - [ ] No new dependencies

**Anti-Slop:**
- `deprecate_pattern()` already exists — use it inside `consolidate_patterns()`, do NOT create a new deprecation path
- `applies_when_signals` is a `List[str]` — Jaccard on sets: `len(intersection) / len(union)`
- `find_overlapping_patterns` scans pairwise — O(n²) is fine for in-memory store (< 1000 patterns)
- `typical_drivers` is `List[DriverAttribution]` — merge by `driver` name, keep whichever has higher `prior_confidence`
- Do NOT modify `find_matching_patterns()` — consolidation is a separate concern (curator-initiated, not query-time)
- Do NOT add a scheduler or auto-consolidation — reconciler surfaces candidates, humans decide
- Version bump: simple string split on ".", increment middle digit, reset patch
- Keep `consolidate_patterns` under 50 lines — extract `_merge_drivers` helper if needed

---

## Sprint Backlog (Next Up)

| Ticket | Title | Team | Sprint | Blocked By | Est. |
|--------|-------|------|--------|-----------|------|
| ATL-004 | Market Access Domain | ATL | 4 | ATL-001 ✓ | L |
| LENS-013 | SME Impact Dashboard | LENS | 5 | CTX-018 ✓, LENS-012 ✓ | L |
| ATL-005 | Gold Set Expansion | ATL | 5 | ATL-003 ✓ | L |

_Full 20-sprint roadmap: see `docs/BOARD.md`_

---

## Research-Derived Backlog (Unscheduled)

> Source: Talisman "Context Graphs & Process Knowledge" + raw notes analysis
> Slot into sprints during future planning. See `docs/BOARD.md` for full details.

### HIGH — Schedule in Sprints 4-6

| Ticket | Title | Team | Blocked By | Est |
|--------|-------|------|-----------|-----|
| CTX-025 | Process Trace Model — add timing, step durations, skip tracking to ReasoningEvent | CTX | CTX-017 ✓ | M |
| CTX-026 | Decision-Time Context Snapshot — store market state alongside each Delta/Pattern | CTX | CTX-005 | M |
| CTX-018 | _(already scheduled Sprint 4)_ Contribution Tracking — enhance with accuracy-over-time for "digital twin of SME" | CTX | CTX-017 ✓ | M |

### MEDIUM — Schedule in Sprints 7-10

| Ticket | Title | Team | Blocked By | Est |
|--------|-------|------|-----------|-----|
| CTX-027 | Canonical Procedure Extraction — derive canonical procedures from multiple SME sessions | CTX | CTX-025 | L |
| LENS-024 | Question Sequence Analytics — track how SMEs navigate steps, detect intent patterns | LENS | LENS-011 ✓ | M |
| CTX-028 | Expert Profile Model — build composite expert profiles from session contributions | CTX | CTX-018 | L |

### LOWER — Schedule in Sprints 11+

| Ticket | Title | Team | Blocked By | Est |
|--------|-------|------|-----------|-----|
| ATL-021 | Auto-Scenario Generation — generate new scenarios from real session data | ATL | ATL-003, CTX-025 | L |
| ATL-022 | Controlled Vocabulary Registry — formal terminology governance layer | ATL | ATL-001 ✓ | M |

_Note: Agent Navigation Policy maps to existing CTX-010 (Sprint 9) — no separate ticket needed._

---

## EPIC Backlog (New Capabilities — Unscheduled)

> Full specs: `product_management/epics/EPIC-006_expert_mode.md`, `EPIC-007_document_ingestion.md`, `EPIC-008_agentic_ai.md`
> Full ticket list + sequencing: see `docs/BOARD.md` → "EPIC Backlog" section
> Gated by **DEC-012** (new dependencies) for EPIC-007 and EPIC-008

### EPIC-006: Expert Mode (Sprints 5-6) — 4 tickets
LENS-025 (Expert Toggle, M) → LENS-026 (Entity/Rule Editor, L) + LENS-027 (Scenario Author, L)
CTX-029 (Direct Contribution API, M)

### EPIC-008: Agentic AI (Sprints 7-9) — 9 tickets
CTX-033 (LLM Framework, M) → CTX-034 (Entity Extract, L) + CTX-035 (Relationship, L) + CTX-036 (Resolution, M)
CTX-034 + CTX-036 → CTX-037 (Smart Linking, M)
CTX-034 → CTX-038 (Game AI Enhancement, L)
CTX-033 → CTX-039 (Confidence Calibration, M)
ATL-024 (Pharma Prompt Library, L)

### EPIC-007: Document Ingestion (Sprints 9-10) — 5 tickets
CTX-030 (Upload + Parsers, L) → CTX-031 (Parser Impls, L) → CTX-032 (Pipeline, L)
CTX-030 → LENS-028 (Upload UI, L)
ATL-023 (Ingestion Prompts, M)

---

_End of Lead2Dev — Tech Lead_
