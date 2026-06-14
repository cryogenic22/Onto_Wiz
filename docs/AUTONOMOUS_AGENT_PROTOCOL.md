# Onto_Wiz Autonomous Agent Protocol v3.0

> Effective: 2026-01-31
> Owner: Tech Lead (Claude)
> Status: ACTIVE

---

## 1. Purpose

This protocol governs how four development teams collaborate on the Onto_Wiz codebase. Each agent reads its team instruction file, executes scoped sprints via an agile board, writes mini-specs before code, reports progress, and waits for the next assignment. The Tech Lead orchestrates via markdown files.

The protocol optimizes for: **context efficiency**, **drift prevention**, **architectural rigor**, and **zero-slop delivery**.

---

## 2. Team Structure

```
Human (CEO / Product Owner)
    ↓  (intervention only — strategic direction, approvals)
Tech Lead (Sprint Management, Code Review, Architecture Governance)
    ├─→ Team LENS      [LENS-NNN]  — UI + API surface layer
    ├─→ Team CORTEX    [CTX-NNN]   — Core engine + reasoning brain
    ├─→ Team ATLAS     [ATL-NNN]   — Domain content + ontology
    └─→ Team SENTINEL  [SEN-NNN]   — Quality infrastructure + enforcement
```

### Team LENS — *"How the world sees the system"*
- **Code prefix:** `LENS`
- **Owns:** `frontend/`, `src/api/`, `tests/test_api.py`
- **Mission:** Game UI, FastAPI endpoints, API contract tests, Pydantic schemas
- **Instruction file:** `docs/teams/LENS_INSTRUCTIONS.md`

### Team CORTEX — *"The reasoning brain"*
- **Code prefix:** `CTX`
- **Owns:** `src/core/`, `src/reasoning/`, `src/ingestion/`, `tests/test_core.py`, `tests/test_graph_evidence.py`, `tests/test_reasoning.py`
- **Mission:** Models, stores, graph, evidence, confidence, delta generation, reasoning, semantic resolution
- **Instruction file:** `docs/teams/CORTEX_INSTRUCTIONS.md`

### Team ATLAS — *"The knowledge architect"*
- **Code prefix:** `ATL`
- **Owns:** `ontology/`, `tests/gold_set/`
- **Mission:** Ontology design, inference rules, therapeutic area taxonomies, gold-set scenarios, synthetic data
- **Instruction file:** `docs/teams/ATLAS_INSTRUCTIONS.md`

### Team SENTINEL — *"The quality guardian"*
- **Code prefix:** `SEN`
- **Owns:** `quality/`, `.github/workflows/`, `docs/reviews/`
- **Mission:** CI/CD, quality gate enforcement, slop checker, architecture reviews, coverage audits, security reviews
- **Instruction file:** `docs/teams/SENTINEL_INSTRUCTIONS.md`

---

## 3. Coordination Files

| File | Direction | Max Size | Purpose |
|------|-----------|----------|---------|
| `docs/BOARD.md` | Lead ↔ Teams | — | Agile board: BACKLOG → READY → IN_PROGRESS → REVIEW → DONE |
| `docs/Lead2Dev.md` | Lead → Teams | 200 lines | Active sprint details + acceptance criteria |
| `docs/Dev2Lead.md` | Teams → Lead | 200 lines | Mini-specs, progress reports, blockers |
| `docs/DECISION_LOG.md` | Lead ↔ Teams | Append-only | Settled architectural decisions |
| `docs/teams/LENS_INSTRUCTIONS.md` | Lead → LENS | Stable | Full context packet |
| `docs/teams/CORTEX_INSTRUCTIONS.md` | Lead → CORTEX | Stable | Full context packet |
| `docs/teams/ATLAS_INSTRUCTIONS.md` | Lead → ATLAS | Stable | Full context packet |
| `docs/teams/SENTINEL_INSTRUCTIONS.md` | Lead → SENTINEL | Stable | Full context packet |

---

## 4. Context Loading Order

Every agent session begins with this exact read sequence. No deviations.

```
STEP 1: READ  docs/teams/[YOUR_TEAM]_INSTRUCTIONS.md     ← project context + scope
STEP 2: READ  anti_slop.md                                ← governance rules
STEP 3: READ  docs/BOARD.md                               ← see full board state
STEP 4: READ  docs/Lead2Dev.md                            ← find your sprint details
STEP 5: READ  docs/DECISION_LOG.md                        ← settled decisions
STEP 6: READ  sprint-scoped source files (listed in Lead2Dev)
STEP 7: READ  relevant test files for those source files
```

Do NOT read files outside this sequence unless the sprint explicitly requires it.
Do NOT explore the codebase freely — your instruction file already contains the context you need.

---

## 5. Agile Board Workflow

### Board Columns
```
BACKLOG  →  READY  →  IN_PROGRESS  →  REVIEW  →  DONE
```

### Column Definitions
| Column | Who Moves Here | Meaning |
|--------|---------------|---------|
| BACKLOG | Tech Lead | Prioritized but not sprint-planned. Has ticket ID, team, priority. |
| READY | Tech Lead | Sprint-planned. Has acceptance criteria in Lead2Dev.md. Marked `🟢 EXECUTE NOW`. |
| IN_PROGRESS | Agent | Agent has picked up the ticket. Writing mini-spec or implementing. |
| REVIEW | Agent | Agent reports DONE. Awaiting Lead 5-point verification. |
| DONE | Tech Lead | Lead verified. Archived. |

### WIP Limits
- **IN_PROGRESS:** Max 1 ticket per team
- **REVIEW:** Max 2 tickets total
- Finish before starting. No multitasking.

### Ticket Format
```
[TEAM]-NNN: [Title]
Team: LENS | CORTEX
Priority: P0 | P1 | P2
Phase: 2.1 | 3 | 4 | 5 | 6 | 7
Blocked By: [ticket ID or "—"]
Est: S | M | L | XL
```

### Board Updates
- **Agent:** When picking up a ticket, move it to IN_PROGRESS in Dev2Lead report
- **Agent:** When done, set status to REVIEW in Dev2Lead report
- **Tech Lead:** Moves tickets on BOARD.md after verification. Archives completed work.

---

## 6. Sprint Lifecycle

```
BACKLOG             → Ticket exists, prioritized, not yet detailed
READY               → Acceptance criteria written in Lead2Dev.md
🟢 EXECUTE NOW      → Agent should pick up immediately
IN_PROGRESS:SPEC    → Agent is writing mini-spec (Phase 2 of anti-slop)
IN_PROGRESS:IMPL    → Agent is implementing (Phase 3 of anti-slop)
BLOCKED             → Agent hit a dependency/question — needs Lead input
REVIEW              → Sprint done, awaiting Lead 5-point check
✅ DONE             → Accepted by Lead, moved to DONE column, archived
```

---

## 7. The Mini-Spec Gate

**Mandatory. No code without a mini-spec.**

Before writing ANY implementation code, the agent must write a mini-spec in Dev2Lead.md:

```markdown
### Mini-Spec: [Ticket ID]

**Files to touch:**
- path/to/file.py — [add/modify] — [what changes]

**Functions to add/modify:**
- `function_name(arg: Type) -> ReturnType` — [purpose]

**Slop risk:**
- [Where hallucination might happen — unfamiliar APIs, complex types, unclear specs]

**Reuse opportunities:**
- [Existing code/patterns to leverage — cite file:line]

**Test plan:**
- `test_function_name` — [what it validates]

**Complexity:** [Low / Medium / HIGH]
```

**Rules:**
- LOW/MEDIUM complexity: proceed to implementation after writing spec
- HIGH complexity: STOP. Set status to `IN_PROGRESS:SPEC`. Wait for Lead approval.
- If the sprint touches > 3 files or adds > 100 lines: complexity is HIGH by default.

---

## 8. File Ownership Rules

| Team | Owns (exclusive write) | Can read |
|------|----------------------|----------|
| LENS | `frontend/**`, `src/api/**`, `tests/test_api.py` | Everything |
| CORTEX | `src/core/**`, `src/reasoning/**`, `src/ingestion/**`, `tests/test_core.py`, `tests/test_graph_evidence.py`, `tests/test_reasoning.py` | Everything |
| ATLAS | `ontology/**`, `tests/gold_set/**` | Everything |
| SENTINEL | `quality/**`, `.github/workflows/**`, `docs/reviews/**` | Everything |
| Shared | `conftest.py`, `tests/conftest.py` | — |
| Tech Lead | `docs/**` (except reviews), `anti_slop.md`, configs, `Makefile`, `pyproject.toml` | Everything |

**Cross-team changes** require explicit Lead approval in Lead2Dev.md.
**Shared files** (`src/core/models.py` enums, `pyproject.toml` deps) require Lead approval for modification.

---

## 9. Report Format

Every Dev2Lead entry follows this structure:

```markdown
## [TEAM]-YYYYMMDD-NNN: [Ticket ID] — [Status]

**Ticket:** [Ticket ID from BOARD.md]
**Date:** YYYY-MM-DD HH:MM
**Status:** IN_PROGRESS:SPEC | IN_PROGRESS:IMPL | BLOCKED | DONE

### Mini-Spec
[Required before implementation — see Section 7]

### Summary
[1-3 sentences: what was done]

### Deliverables
- [x] `path/to/file.py` — [what changed]

### Tests
- [x] `test_name` — PASS

### Quality Results
- pytest: XX passed, 0 failed
- quality-gate PRS: XX/100 on touched files
- cathedral-keeper: 0 new findings

### Blockers
- [None | description]
```

---

## 10. Quality Gates (Sprint Acceptance)

| Gate | Command | Threshold |
|------|---------|-----------|
| All tests pass | `python -m pytest tests/ -v` | 0 failures |
| New tests written | Manual check | >= 1 test per new public function |
| Quality gate | `python quality-gate/quality_gate.py --root .` | PRS >= 85 on touched files |
| Cathedral Keeper | `python cathedral-keeper/ck.py analyze --root .` | No new HIGH findings |
| Anti-slop checklist | See `anti_slop.md` verification table | All checks pass |
| Scope check | Compare touched files to sprint scope | No out-of-scope files |
| Mini-spec match | Compare delivered code to mini-spec | Code matches proposal |

---

## 11. Lead 5-Point Verification

When a team reports DONE, the Tech Lead runs:

1. `python -m pytest tests/ -v --tb=short` — all green
2. `python quality-gate/quality_gate.py --root .` — PRS >= 85 on touched files
3. `python cathedral-keeper/ck.py analyze --root .` — no new findings vs baseline
4. **Mini-spec match** — delivered code matches the proposal in Dev2Lead
5. **Scope check** — no files touched outside sprint boundary

If any check fails: ticket moves back to IN_PROGRESS with fix instructions.

---

## 12. Archiving Protocol

**Rule:** Lead2Dev.md and Dev2Lead.md must stay under **200 lines**.

**Procedure (Lead responsibility):**
1. When a ticket reaches `✅ DONE`, move its content to:
   - `docs/archive/Lead2Dev_Archive.md` (sprint definition)
   - `docs/archive/Dev2Lead_Archive.md` (agent reports)
2. Update BOARD.md: move ticket to DONE column
3. Active files retain only: current/queued sprints + dependency table
4. Agents NEVER read archive files unless explicitly instructed

---

## 13. Drift Detection

Every 3rd ticket completion, the Lead runs a drift check:

1. Compare codebase state against `product_management/02_backlog.md`
2. Compare BOARD.md against `product_management/epics/EPIC-*.md`
3. Run quality-gate audit for quality trend
4. Run Cathedral Keeper for architecture trend

If drift is detected: log in DECISION_LOG.md, write correction ticket before continuing.

---

## 14. Escalation Rules

| Situation | Action |
|-----------|--------|
| Test failure in own code | Fix it, report in Dev2Lead |
| Test failure in other team's code | Report BLOCKED, tag the team |
| Architectural question | Check DECISION_LOG first, then ask Lead |
| Scope creep detected | Stop, report to Lead, wait |
| Confidence < 70% on approach | Write mini-spec, set `IN_PROGRESS:SPEC`, wait for Lead |
| Want to add new dependency | Stop, report to Lead with justification |
| Want to modify shared enums | Stop, report to Lead |
| Ticket touches > 3 files | Auto-HIGH complexity — mini-spec + Lead approval |

---

## 15. IDLE Protocol

When no ticket is in READY for your team:
1. Report IDLE in Dev2Lead.md: `[TEAM] IDLE as of [timestamp]`
2. Run `python -m pytest tests/ -v` — report failures
3. Run quality-gate audit — report regressions
4. Do NOT explore or refactor proactively
5. Check back in 20 minutes

---

## 16. Current Team Assignments

| Team | Ticket | Status | Focus |
|------|--------|--------|-------|
| CORTEX | CTX-005 | READY | Artifact Ownership + Judgment Classification |
| LENS | LENS-011 | READY | Game Session Submission API + Hook |
| ATLAS | ATL-003 | READY | Scenario Library v1 — 10 Oncology Scenarios |
| SENTINEL | — | IDLE | Next: SEN-005 (Sprint 5) |

_Last updated: 2026-02-01 by Tech Lead_
