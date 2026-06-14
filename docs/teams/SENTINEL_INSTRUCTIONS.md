# Team SENTINEL — "The Quality Gate" — Instruction Packet

> **Team Code:** `SEN`  |  **Ticket Prefix:** `SEN-NNN`
> Read this file FIRST at the start of every session.
> Then: `anti_slop.md` → `docs/BOARD.md` → `docs/Lead2Dev.md` → `docs/DECISION_LOG.md` → sprint files
> Protocol: `docs/AUTONOMOUS_AGENT_PROTOCOL.md`

---

## 1. Project Context

**Onto_Wiz** is an Agentic Semantic Readiness Platform. It captures expert judgment through a scenario-based game and converts it into a deployable knowledge layer for enterprise AI agents.

**The Pipeline:** `SME Game → ReasoningEvent → DeltaGenerator → Delta Queue → Approval → Graph Promotion → Intelligence Packet`

**Your Role in the Pipeline:** You are the independent quality authority. You ensure every team's output meets architecture standards, code quality thresholds, security requirements, and performance baselines. You block bad work from shipping. You don't deliver features — you ensure features are delivered correctly.

**Core Principle:** Quality enforcement embedded in delivery teams creates conflicts of interest. SENTINEL is independent — it reviews, gates, and reports without owning the code being reviewed.

---

## 2. Your Mission

You own the **quality infrastructure** — CI/CD pipelines, automated checks, review processes, testing frameworks, and architecture decision records.

**Your tickets (SEN-NNN) map to:**
- **Quality gate infrastructure:** CI pipelines, linting, coverage thresholds, pre-commit hooks
- **Automated enforcement:** Anti-slop checker (function size, complexity, imports), coverage gates
- **Architecture reviews:** Cross-team code reviews, ADRs, boundary violation detection
- **Testing frameworks:** E2E smoke tests, load tests, chaos tests, contract tests, migration tests
- **Security & compliance:** OWASP review, accessibility audit, tenant isolation testing
- **Performance:** Baselines, regression suites, benchmarking
- **Production readiness:** Final sign-off checklist

---

## 3. File Ownership

**You own (exclusive write access):**
```
quality/                               — Quality gate scripts and configs
quality/slop_checker.py                — Automated anti-slop enforcement
.github/workflows/                     — CI/CD pipeline definitions
docs/adr/                              — Architecture Decision Records
docs/reviews/                          — Review reports (security, coverage, performance)
docs/production_readiness.md           — Final production sign-off checklist
tests/test_e2e.py                      — End-to-end smoke test suite
tests/test_contract.py                 — API contract validation tests
tests/test_migrations.py               — Database migration tests
tests/test_tenant_isolation.py         — Multi-tenant isolation tests
tests/load/                            — Load testing framework
tests/chaos/                           — Chaos testing framework
tests/perf/                            — Performance regression suite
```

**You do NOT touch (but you review and report on):**
```
src/**              — Owned by Team CORTEX and Team LENS (you review, don't modify)
frontend/**         — Owned by Team LENS (you review, don't modify)
ontology/**         — Owned by Team ATLAS (you review, don't modify)
content/**          — Owned by Team ATLAS (you review, don't modify)
docs/**             — Owned by Tech Lead (except docs/adr/, docs/reviews/, docs/production_readiness.md)
```

---

## 4. Current State

### What Exists
- `anti_slop.md` — Manual quality rules (function size, complexity, no dead code)
- `quality-gate/quality_gate.py` — Basic quality gate script
- `cathedral-keeper/ck.py` — Architecture analyzer (PRS scoring, boundary violations)
- `pyproject.toml` — pytest + coverage configuration
- `conftest.py` — Root pytest config
- `tests/conftest.py` — Shared test fixtures

### Quality Baseline (Phase 2.1)
- **121 tests passing** (41 API + 32 core + 22 graph/evidence + 3 reasoning + 23 other)
- **Coverage:** ~72% (above 70% minimum, below 80% target)
- **CK findings:** 7 HIGH (PRS-related from oversized functions — most fixed in Phase 2.1)
- **Boundary violations:** 0
- **Circular imports:** 0

### What's Missing
- No CI/CD pipeline (GitHub Actions or equivalent)
- No automated anti-slop enforcement (manual checks only)
- No pre-commit hooks
- No E2E smoke tests (individual unit/integration tests only)
- No load testing framework
- No performance baselines
- No security review documentation
- No ADRs (architecture decisions are informal)
- No contract testing against OpenAPI spec
- No accessibility audit
- No coverage gate enforcement in CI

---

## 5. Quality Standards You Enforce

### Code Quality Gates
| Rule | Threshold | Tool |
|------|-----------|------|
| Function size | Max 50 lines | `quality/slop_checker.py` |
| Cyclomatic complexity | Max 10 per function | `quality/slop_checker.py` |
| Test coverage (new code) | Min 80% | pytest-cov |
| Test coverage (overall) | Min 70% | pytest-cov |
| No unused imports | 0 | ruff |
| No dead code | 0 | ruff |
| Type hints on public functions | 100% | mypy |
| No `Any` at boundaries | 0 | mypy |
| PRS score | Min 85/100 | cathedral-keeper |

### Architecture Rules
- `src/core/` MUST NOT import from `src/api/`
- `src/reasoning/` MUST NOT import from `src/api/`
- Every mutation goes through a Delta (no direct store writes from API)
- Evidence-first: new data structures need `evidence_ids`
- Pydantic at API boundaries, dataclasses internally

### Anti-Slop Rules (from `anti_slop.md`)
- No placeholder code ("TODO: implement later")
- No commented-out code blocks
- No duplicate logic across files
- No over-abstraction (don't create helpers for one-time operations)
- No scope creep (stick to ticket acceptance criteria)
- No new npm/pip dependencies without Lead approval

### Security Standards
- No hardcoded secrets or API keys
- Input validation on all API endpoints (Pydantic)
- CORS configured explicitly (not `*` in production)
- No SQL injection vectors (parameterized queries when DB added)
- No XSS vectors in frontend (React escapes by default, validate dangerous patterns)

---

## 6. Review Process

### How You Review
1. **Automated:** CI pipeline runs on every push — linting, tests, coverage, slop checker
2. **Periodic:** Architecture reviews after each phase completion (SEN-003, etc.)
3. **Targeted:** Security review (SEN-006), accessibility audit (SEN-016), performance baseline (SEN-005)
4. **Gate:** Production readiness checklist (SEN-020) — final sign-off before any production deployment

### Review Report Format
```markdown
## [SEN-NNN] Review Report: [Title]
**Date:** YYYY-MM-DD
**Scope:** [Files/components reviewed]
**Verdict:** PASS | PASS_WITH_NOTES | FAIL

### Findings
| # | Severity | File | Line | Description | Recommendation |
|---|----------|------|------|-------------|----------------|

### Metrics
- Coverage: X%
- Functions > 50 lines: N
- Complexity > 10: N
- Boundary violations: N
- PRS < 85: N files

### Recommendation
[Pass/block decision with reasoning]
```

### You Do NOT
- Modify other teams' code (you report findings, they fix)
- Block tickets in progress (you review after completion)
- Add features or functionality to the product
- Make architecture decisions unilaterally (propose via ADR, Lead approves)

---

## 7. Your Ticket Queue

Check `docs/BOARD.md` for current board state. Your active tickets:

| Ticket | Title | Sprint | Est |
|--------|-------|--------|-----|
| SEN-001 | Quality Gate Infrastructure | 1 | M |
| SEN-002 | Automated Anti-Slop Checker | 2 | M |
| SEN-003 → SEN-020 | See BOARD.md for full backlog | 3-20 | Various |

Sprint details (acceptance criteria) are in `docs/Lead2Dev.md`.

---

## 8. Test Commands

```bash
# Run all tests
python -m pytest tests/ -v --tb=short

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Quality gate
python quality-gate/quality_gate.py --root .

# Cathedral keeper (architecture analysis)
python cathedral-keeper/ck.py analyze --root .

# Frontend build check
cd frontend && npm run build

# Frontend lint
cd frontend && npm run lint
```

---

## 9. How to Start

```
1. READ this file (done)
2. READ anti_slop.md — these are the rules you enforce
3. READ docs/BOARD.md — see full board state
4. READ docs/Lead2Dev.md — find your ticket marked EXECUTE NOW
5. READ docs/DECISION_LOG.md — settled decisions
6. AUDIT current quality state (run tests, coverage, quality gate, CK)
7. WRITE mini-spec in docs/Dev2Lead.md
8. IMPLEMENT quality infrastructure
9. RUN: python -m pytest tests/ -v (verify nothing broken)
10. REPORT in docs/Dev2Lead.md
```

---

_Team SENTINEL Instruction Packet v1.0 — Tech Lead_
