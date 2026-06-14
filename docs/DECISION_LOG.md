# Onto_Wiz Decision Log

> Append-only. Every architectural or design decision gets an entry.
> Agents must READ this before proposing alternatives to settled decisions.
> Only the Tech Lead or Human can add entries.

---

## DEC-001: Delta Model — Everything is a Proposal

**Date:** 2026-01-31
**Decision:** All mutations to the knowledge graph go through Deltas. No direct writes.
**Context:** The system must be auditable and reversible. Direct graph mutations bypass governance.
**Rationale:** Enterprise pharma clients require full audit trails. The Delta model provides this natively.
**Status:** SETTLED — do not propose alternatives.

---

## DEC-002: Four-Team Structure — LENS + CORTEX + ATLAS + SENTINEL _(Revised x2)_

**Date:** 2026-02-01 (revised from 2-team to 4-team)
**Decision:** Four teams: **Team LENS** (UI + API surface, code `LENS`), **Team CORTEX** (core engine, code `CTX`), **Team ATLAS** (domain content + ontology, code `ATL`), **Team SENTINEL** (quality infrastructure, code `SEN`).
**Context:** As the codebase grew to ~6,500 lines with ontology content and quality tooling, domain knowledge work and quality enforcement needed dedicated ownership separate from feature delivery teams.
**Rationale:** ATLAS decouples ontology design (YAML, gold sets, scenarios) from Python engineering. SENTINEL decouples CI/CD, quality audits, and architecture reviews from feature velocity. Both can operate in parallel without blocking LENS or CORTEX. File ownership is clean: ATLAS owns `ontology/` and `tests/gold_set/`, SENTINEL owns `quality/`, `.github/workflows/`, `docs/reviews/`.
**Status:** SETTLED — revisit only when codebase exceeds 15,000 lines.

---

## DEC-003: Quality Gate PRS Minimum 85

**Date:** 2026-01-31
**Decision:** All new code must score PRS >= 85. Existing debt is addressed incrementally.
**Context:** Current codebase has 2 files below 85 (delta_generator.py, semantic_store.py). New code must not add to this.
**Rationale:** PRS 85 means max 1 error and 7 warnings. This is strict enough to catch real problems without blocking velocity.
**Status:** SETTLED.

---

## DEC-004: Function Size Max 50 Lines

**Date:** 2026-01-31
**Decision:** No function may exceed 50 lines (enforced by quality gate).
**Context:** 6 existing functions exceed this. They are technical debt, not precedent.
**Rationale:** Long functions have high cyclomatic complexity, are hard to test, and attract slop. 50 lines forces decomposition into testable units.
**Status:** SETTLED.

---

## DEC-005: In-Memory Stores Until Phase 6

**Date:** 2026-01-31
**Decision:** All stores remain in-memory (Python dicts/lists) until Phase 6 introduces Postgres/Neo4j.
**Context:** Premature persistence adds complexity without business value at this stage.
**Rationale:** The store interfaces are abstracted. Swapping in a database later requires implementing the same interface. Don't add ORM/migration complexity until the domain model is stable.
**Status:** SETTLED — do not add database dependencies before Phase 6.

---

## DEC-006: No New Dependencies Without Lead Approval

**Date:** 2026-01-31
**Decision:** Agents cannot add pip/npm packages without explicit Lead approval in Lead2Dev.md.
**Context:** Dependency creep is a major slop vector. Each new package is an attack surface, a compatibility risk, and a context burden.
**Rationale:** The current stack (FastAPI, Pydantic, PyYAML, pytest for Python; Next.js, React, ReactFlow, Tailwind for frontend) covers all Phase 2-5 needs.
**Status:** SETTLED.

---

## DEC-007: Architecture Boundaries Enforced by Cathedral Keeper

**Date:** 2026-01-31
**Decision:** `src/core/` and `src/reasoning/` must never import from `src/api/`. Enforced by CK policy.
**Context:** Core logic must be invocable without the web server. This enables testing, reuse, and eventual microservice extraction.
**Rationale:** Clean architecture. Dependencies point inward (API → Core), never outward (Core → API).
**Status:** SETTLED — Cathedral Keeper will block violations.

---

## DEC-008: Mini-Spec Required Before Implementation

**Date:** 2026-01-31
**Decision:** Every sprint requires a written mini-spec in Dev2Lead.md before any implementation code is written.
**Context:** Agents that start coding without a plan produce scope creep and hallucinated abstractions.
**Rationale:** The mini-spec forces the agent to read existing code, identify reuse opportunities, and declare slop risks. This prevents 80% of rework.
**Status:** SETTLED — sprints without mini-specs will be rejected at review.

---

## DEC-009: Agile Board for Cross-Team Visibility

**Date:** 2026-01-31
**Decision:** `docs/BOARD.md` serves as a single agile board (BACKLOG → READY → IN_PROGRESS → REVIEW → DONE) visible to both teams.
**Context:** With two autonomous teams, we need cross-team awareness of what's in flight, what's blocked, and what's done. The board provides this without adding process overhead.
**Rationale:** WIP limit of 1 per team prevents multitasking. Ticket prefixes (LENS-NNN, CTX-NNN) make ownership instant. Dependency graph in the board shows blocking relationships. Velocity tracking enables Lead to forecast.
**Status:** SETTLED.

---

## DEC-010: Ticket Estimation Scale (S/M/L/XL)

**Date:** 2026-01-31
**Decision:** Use relative sizing (S/M/L/XL) not time estimates. S = 1-2 functions, M = 3-5 functions, L = full feature, XL = subsystem.
**Context:** AI agents don't estimate time reliably. Relative complexity is more useful for sequencing work.
**Rationale:** Estimation is for prioritization and risk assessment, not scheduling. XL tickets should be broken down before execution. L and above auto-trigger HIGH complexity mini-spec gate.
**Status:** SETTLED.

---

## DEC-011: SENTINEL Reviews Are Read-Only

**Date:** 2026-02-01
**Decision:** SENTINEL review tickets (SEN-003, SEN-004, etc.) must NOT modify source code. They produce reports in `docs/reviews/` and recommend tickets — only the Tech Lead creates actual backlog items from recommendations.
**Context:** Architecture reviews that also fix issues conflate auditing with implementation. The reviewer should not be the fixer.
**Rationale:** Separation of concerns. SENTINEL identifies problems. CORTEX/LENS/ATLAS fix them. This prevents audit bias and keeps review reports objective.
**Status:** SETTLED.

---

## DEC-012: Approved Dependencies for EPIC-007 + EPIC-008

**Date:** 2026-02-01
**Decision:** The following new dependencies are approved for EPIC-007 (Document Ingestion) and EPIC-008 (Agentic AI), gated on Lead approval before first use:

**Python (backend):**
- `anthropic` OR `openai` — LLM provider SDK (choose one primary, other as fallback)
- `pdfplumber` — PDF text + table extraction (lightweight, no Java dependency)
- `pyarrow` — Parquet file reading

**NOT approved (use stdlib alternatives):**
- `pandas` — use `csv` stdlib for CSV, `pyarrow` for Parquet
- `langchain` — too heavy, too opinionated. Use direct SDK calls with our own prompt templates.
- `unstructured` — too many transitive dependencies

**Context:** EPIC-007 and EPIC-008 require LLM API calls and multi-format file parsing. DEC-006 ("No New Dependencies Without Lead Approval") remains in effect — this decision is a specific exemption for these EPICs only.
**Rationale:** Minimalist dependency set. One LLM SDK (not a framework), one PDF parser, one columnar format reader. Total: 3 new packages. Each solves a specific problem that stdlib cannot. LangChain explicitly rejected — our own `LLMProvider` abstraction is simpler, testable with `MockProvider`, and doesn't pull in 50+ transitive dependencies.
**Status:** SETTLED — approved by Human (CEO) on 2026-02-01. Dependencies may be added starting Sprint 7.

---

_End of Decision Log — append new entries below this line_
