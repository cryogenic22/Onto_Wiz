## [SEN-004] Review Report: Integration Test Coverage Audit + Gap Report
**Date:** 2026-02-01
**Scope:** All src/ modules, all tests/ files
**Verdict:** PASS_WITH_NOTES (79.6% overall, above 70% min, below 80% target)

---

### Test Inventory

| Test File | Tests | Category |
|-----------|-------|----------|
| tests/test_api.py | 55 | API integration (FastAPI TestClient) |
| tests/test_core.py | 56 | Unit tests (models, stores, patterns, guardrails) |
| tests/test_graph_evidence.py | 22 | Unit + integration (graph store, evidence store) |
| tests/test_reasoning.py | 3 | Integration (reasoning engine scenarios) |
| tests/gold_set/test_gold_set.py | 5 (parametrized) | End-to-end (YAML scenario validation) |
| **Total** | **134** | |

### Coverage by Module

| Module | Stmts | Miss | Cover | Trend | Action Required |
|--------|-------|------|-------|-------|----------------|
| src/api/schemas.py | 215 | 0 | **100%** | - | None |
| src/core/__init__.py | 9 | 0 | **100%** | - | None |
| src/reasoning/engine.py | 76 | 2 | **97%** | - | None |
| src/core/models.py | 311 | 9 | **97%** | - | None |
| src/core/reasoning_event.py | 146 | 7 | **95%** | - | None |
| src/core/delta_generator.py | 110 | 7 | **94%** | - | None |
| src/api/server.py | 202 | 14 | **93%** | - | Low priority |
| src/core/stores.py | 261 | 50 | **81%** | - | Medium priority |
| src/core/evidence.py | 181 | 39 | **78%** | - | Medium priority |
| src/core/graph_store.py | 226 | 68 | **70%** | - | Medium priority |
| src/core/semantic_store.py | 199 | 113 | **43%** | ! | **HIGH priority** |
| src/core/confidence.py | 157 | 118 | **25%** | ! | **CRITICAL** |
| **TOTAL** | **2093** | **427** | **79.6%** | | |

---

### CRITICAL GAP: src/core/confidence.py (25%)

The entire `ConfidenceEngine` class is untested. This is the confidence scoring system — a core business logic component.

**Untested functions:**
- `ConfidenceEngine.compute()` — Main confidence calculation (75 lines)
- `_compute_base_prior()` — Driver prior extraction
- `_compute_evidence_reliability()` — Evidence weight averaging
- `_compute_corroboration()` — Diminishing returns bonus
- `_compute_conflict_penalty()` — Contradiction penalty
- `_compute_freshness()` — Pattern decay/staleness
- `_check_missing_evidence()` — Required evidence validation
- `is_actionable()` — Threshold check
- `should_halt()` — Halt decision logic
- `compute_quick()` — Fast confidence computation

**Risk:** HIGH. Confidence scoring drives traversal decisions and intelligence packet quality. Any regression here is invisible without tests.

**Recommendation:** CTX team should add `tests/test_confidence.py` with:
1. Basic compute() happy path
2. Evidence reliability weighting
3. Corroboration bonus calculation
4. Conflict penalty calculation
5. Freshness decay
6. Halt conditions (low confidence, missing evidence, conflict)
7. Edge cases (no evidence, no patterns)

Estimated effort: M (8-12 test functions)

---

### HIGH GAP: src/core/semantic_store.py (43%)

`SemanticStore` is 57% untested. This is the synonym/canonical resolution layer.

**Untested functions:**
- `SemanticStore.__init__()` — Store initialization
- `add_canonical_term()` / `get_canonical_term()` — Basic CRUD
- `find_canonical_by_name()` — Name lookup
- `add_relation()` — Relation creation with anti-synonym validation
- `add_synonym()` / `add_alias()` / `add_anti_synonym()` — Convenience methods
- `resolve_to_canonical()` — Main synonym resolution (critical path)
- `get_all_variants()` — Variant retrieval
- `get_taxonomy_children()` / `get_taxonomy_path()` — Hierarchy traversal
- `seed_commercial_synonyms()` — Seed data (84 lines)
- `extract_semantic_captures()` — NLP extraction from SME text

**Risk:** MEDIUM-HIGH. Semantic resolution is used by the intelligence pipeline. Incorrect synonym resolution could produce wrong ontology mappings.

**Recommendation:** CTX team should add `tests/test_semantic_store.py` with:
1. Add/get canonical term
2. Synonym resolution (exact match, case-insensitive)
3. Anti-synonym exclusion
4. Taxonomy hierarchy traversal
5. Commercial synonym seeding
6. Text extraction from SME input

Estimated effort: M (10-15 test functions)

---

### MEDIUM GAPS

#### src/core/graph_store.py (70%)

**Untested functions:**
- `update_node()` / `remove_node()` — Mutation operations
- `remove_edge()` — Edge deletion
- `find_evidence_for_hypothesis()` — Evidence lookup
- `find_actions_for_hypothesis()` — Action lookup
- `find_constraints_for_action()` — Constraint lookup
- `import_from_dict()` — Graph deserialization

**Recommendation:** 6-8 additional tests. Effort: S.

#### src/core/stores.py (81%)

**Untested functions:**
- `DeltaStore.propose()` auto-approve edge case
- `get_audit_log()` — Audit trail retrieval
- `_promote_action()` — Action delta promotion
- `get_stale_patterns()` — Pattern decay detection
- `get_template_for_pattern()` — Action template lookup

**Recommendation:** 5-7 additional tests. Effort: S.

#### src/core/evidence.py (78%)

**Untested functions:**
- Evidence chain traversal methods
- Corroboration/contradiction finding
- Evidence linking to entities

**Recommendation:** 5-6 additional tests. Effort: S.

---

### LOW GAPS (Acceptable)

#### src/api/server.py (93%)

Missing: error handling branches (FileNotFoundError, YAMLError), status filter edge cases, legacy `/reason` endpoint exception handling. These are defensive code paths. Acceptable at current level.

#### src/core/models.py (97%), reasoning_event.py (95%), delta_generator.py (94%)

Near-complete. Remaining gaps are edge cases and helper methods. No action needed.

---

### Missing Test Categories

| Category | Exists? | Gap |
|----------|---------|-----|
| Unit tests (models, dataclasses) | Yes (56) | None |
| API integration (TestClient) | Yes (55) | Minor (error handlers) |
| Store integration | Partial (22) | SemanticStore, ConfidenceEngine |
| Reasoning scenarios | Yes (3) | Could use more scenarios |
| Gold set e2e | Yes (5) | Adequate |
| Cross-module integration | No | **Missing: pipeline tests** |
| Confidence engine | No | **Missing entirely** |
| Semantic resolution | No | **Missing entirely** |
| Performance regression | No | SEN-005 scope |
| Load testing | No | SEN-009 scope |
| Contract testing | No | SEN-011 scope |

### Missing Integration Test: Full Pipeline

No test exercises the complete pipeline: `SME Input -> ReasoningEvent -> DeltaGenerator -> Delta -> Approval -> Promotion -> Graph`. Individual pieces are tested, but the chain is not.

**Recommendation:** Add `tests/test_pipeline_integration.py` with:
1. Submit session -> verify deltas created
2. Approve deltas -> verify graph updated
3. Generate intelligence packet from promoted data
4. Verify end-to-end data integrity

Estimated effort: M.

---

### Priority Recommendations

| Priority | Action | Owner | Effort | Coverage Impact |
|----------|--------|-------|--------|-----------------|
| P0 | Add tests/test_confidence.py (8-12 tests) | CTX | M | +5.6% (25% -> ~85%) |
| P0 | Add tests/test_semantic_store.py (10-15 tests) | CTX | M | +4.5% (43% -> ~80%) |
| P1 | Add tests/test_pipeline_integration.py (4 tests) | CTX/LENS | M | Cross-cutting |
| P2 | Expand graph_store tests (6-8 tests) | CTX | S | +2% (70% -> ~85%) |
| P2 | Expand stores.py tests (5-7 tests) | CTX | S | +1.5% (81% -> ~90%) |
| P3 | Expand evidence.py tests (5-6 tests) | CTX | S | +1.2% (78% -> ~88%) |

**Projected coverage after P0+P1:** ~86% (above 80% target)
**Projected coverage after all:** ~90%

---

### Metrics Summary

- Overall coverage: **79.6%** (above 70% min, below 80% target)
- Test count: **134** (55 API + 56 core + 22 graph/evidence + 3 reasoning + 5 gold set)
- Modules at 100%: 2 (schemas.py, __init__.py)
- Modules below 50%: 2 (**confidence.py 25%, semantic_store.py 43%**)
- Modules below 80%: 4 (+ graph_store.py 70%, evidence.py 78%)
- Missing test categories: Confidence engine, Semantic resolution, Full pipeline integration

---

_Review by Team SENTINEL | SEN-004_
