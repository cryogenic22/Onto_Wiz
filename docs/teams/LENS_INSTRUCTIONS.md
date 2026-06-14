# Team LENS — "How the World Sees the System" — Instruction Packet

> **Team Code:** `LENS`  |  **Ticket Prefix:** `LENS-NNN`
> Read this file FIRST at the start of every session.
> Then: `anti_slop.md` → `docs/BOARD.md` → `docs/Lead2Dev.md` → `docs/DECISION_LOG.md` → sprint files
> Protocol: `docs/AUTONOMOUS_AGENT_PROTOCOL.md`

---

## 1. Project Context

**Onto_Wiz** is an Agentic Semantic Readiness Platform. It captures expert judgment through a scenario-based game and converts it into a deployable knowledge layer for enterprise AI agents.

**The Pipeline:** `SME Game → ReasoningEvent → DeltaGenerator → Delta Queue → Approval → Graph Promotion → Intelligence Packet`

**Your Role in the Pipeline:** You own everything the outside world touches — the game UI where SMEs play scenarios AND the FastAPI server that exposes the pipeline as HTTP endpoints. You are the surface layer and the contract.

**UX Philosophy:** "Duolingo meets Bloomberg Terminal." The game must feel engaging and fast (< 7 min per session) while capturing structured, high-quality reasoning data. Experts never see ontology terms.

---

## 2. Your Mission

You own the **API surface** and the **Game UI**. Every endpoint must be tested. Every screen must be responsive and accessible.

**Your tickets (LENS-NNN) map to:**
- **EPIC-001:** SME Game & Judgment Capture (US-001 through US-009) — frontend
- **Phase 2.1:** API integration tests, server decomposition — backend
- **EPIC-003 (API side):** HITL routing endpoints, audit export — backend
- **EPIC-005 (API side):** RBAC middleware, persistence endpoints — backend

---

## 3. File Ownership

**You own (exclusive write access):**

### Backend (FastAPI)
```
src/api/server.py           — FastAPI application, all endpoints (578 lines)
src/api/schemas.py          — Pydantic request/response models
src/api/__init__.py
tests/test_api.py           — API integration tests (TO BE CREATED)
```

### Frontend (Next.js + React)
```
frontend/src/app/           — Next.js pages and layouts
frontend/src/components/    — React components (SituationRoom + game steps)
frontend/src/services/      — API client functions (TO BE CREATED)
frontend/src/hooks/         — Custom React hooks (TO BE CREATED)
frontend/src/types/         — TypeScript type definitions (TO BE CREATED)
frontend/public/            — Static assets
frontend/package.json       — Dependencies
frontend/tailwind.config.js — Styling config
frontend/tsconfig.json      — TypeScript config
frontend/next.config.ts     — Next.js config
```

### Shared (requires Lead approval to modify)
```
conftest.py                 — Root pytest config (needs sys.path fix)
tests/conftest.py           — Shared test fixtures (TO BE CREATED)
```

**You do NOT touch:**
```
src/core/**         — Owned by Team CORTEX
src/reasoning/**    — Owned by Team CORTEX
src/ingestion/**    — Owned by Team CORTEX
ontology/**         — Owned by Team CORTEX
docs/**             — Owned by Tech Lead
```

---

## 4. Current State — Backend (FastAPI)

### API Server (`src/api/server.py` — 578 lines)

**17 endpoints, 0 integration tests:**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | System health + store status |
| GET | `/stats` | Store statistics |
| POST | `/deltas` | Create proposed delta |
| GET | `/deltas` | List deltas (filter by status) |
| GET | `/deltas/{id}` | Get specific delta |
| POST | `/deltas/{id}/approve` | Approve pending delta |
| POST | `/deltas/{id}/reject` | Reject with reason |
| POST | `/deltas/promote` | Promote approved deltas to graph |
| POST | `/patterns` | Create pattern (starts as draft) |
| GET | `/patterns` | List patterns |
| POST | `/patterns/{id}/approve` | Approve for production |
| POST | `/guardrails` | Create guardrail |
| GET | `/guardrails` | List guardrails |
| POST | `/guardrails/{id}/approve` | Approve guardrail |
| POST | `/intelligence-packet` | Main output endpoint |
| POST | `/reason` | Legacy reasoning endpoint |
| GET | `/scenarios` | Demo scenarios list |

**Known Issues:**
- `generate_intelligence_packet` = 113 lines (max 50). Needs decomposition.
- `sys.path.insert` hack on line 16. Fix: use `pip install -e .`.
- File at 578 lines (warning: 500).
- PRS 88/100 — below 85 minimum on touched files.

### API Design Principles
- **Pydantic everywhere:** All bodies through `schemas.py`. No raw dicts.
- **HTTP semantics:** POST creates, GET reads. 201 created, 404 not found, 422 validation.
- **No business logic in endpoints:** Endpoints call store/engine methods. HTTP concerns only.
- **Error format:** `{"error": "ERROR_CODE", "message": "...", "details": {...}}`

---

## 5. Current State — Frontend (Next.js + React)

### Tech Stack
- **Framework:** Next.js 16.1.6, React 19.2.3
- **Visualization:** ReactFlow 11.11.4
- **Styling:** TailwindCSS 4, TailwindMerge, clsx
- **Icons:** Lucide React 0.563.0

### What Exists
- `layout.tsx` — Root layout shell
- `page.tsx` — Main page (imports SituationRoom)
- `SituationRoom.tsx` — **Scaffold only.** No game loop, no API integration.

### What's Missing
- No game loop (9-step flow per EPIC-001)
- No API client service layer
- No TypeScript types matching backend schemas
- No state management for game session
- No error/loading states
- No session summary view

### The Game Loop (EPIC-001: US-001 → US-009)
```
Step 1: View Scenario Card        → Brand, region, timeframe, observation
Step 2: Select Primary Hypothesis → Commercial | Market access | Clinical | Competitive | Too early
Step 3: Prioritize Signals        → Pick up to 2: NBRx, TRx, Decile, Payer, Field, Safety
Step 4: Disconfirming Logic       → Free-text: "What would change your mind?"
Step 5: Pattern Recognition       → Often | Sometimes | Rarely | Never
Step 6: Flag Common Mistakes      → Free-text: "What do people typically get wrong?"
Step 7: Recommend Next Actions    → Pull data | Ask access | Shift field | Escalate | Wait | None
Step 8: Calibrate Confidence      → Slider 0-100%
Step 9: View Session Summary      → Acknowledgment of what was captured
```

### Frontend File Organization (Target)
```
frontend/src/
├── components/
│   ├── SituationRoom.tsx         — Game orchestrator
│   ├── game/
│   │   ├── ScenarioCard.tsx      — Step 1
│   │   ├── HypothesisSelect.tsx  — Step 2
│   │   ├── SignalPriority.tsx    — Step 3
│   │   ├── DisconfirmInput.tsx   — Step 4
│   │   ├── PatternRecognition.tsx — Step 5
│   │   ├── CommonMistakes.tsx    — Step 6
│   │   ├── ActionRecommend.tsx   — Step 7
│   │   ├── ConfidenceSlider.tsx  — Step 8
│   │   └── SessionSummary.tsx    — Step 9
│   └── ui/                       — Reusable primitives
├── services/api.ts               — Backend fetch wrapper
├── hooks/useGameSession.ts       — Game state hook
└── types/
    ├── game.ts                   — Game types
    └── api.ts                    — API response types
```

### Frontend Rules
- **API URL** from `NEXT_PUBLIC_API_URL` env var, never hardcoded
- **One component per game step** — don't put all 9 in one file
- **TypeScript strict** — no `any` types
- **Accessibility** — labels, keyboard support, semantic HTML
- **No new npm deps** without Lead approval

---

## 6. Key TypeScript Types (Reference)

```typescript
interface GameSession {
  id: string;
  scenario: Scenario;
  currentStep: number;
  responses: Partial<GameResponses>;
  startedAt: Date;
}

interface Scenario {
  id: string;
  brand: string;
  region: string;
  timeframe: string;
  observation: string;
  nationalContext: string;
}

interface GameResponses {
  primaryHypothesis: HypothesisType;
  signalPriorities: SignalType[];
  disconfirmingLogic: string;
  patternFrequency: 'often' | 'sometimes' | 'rarely' | 'never';
  commonMistakes: string;
  recommendedActions: ActionType[];
  confidencePercent: number;
}

type HypothesisType = 'commercial_execution' | 'market_access' | 'clinical_safety' | 'competitive' | 'too_early_to_tell';
type SignalType = 'nbrx' | 'trx' | 'decile' | 'payer_changes' | 'field_activity' | 'safety';
type ActionType = 'pull_data' | 'ask_access_team' | 'shift_field' | 'escalate' | 'wait' | 'do_nothing';
```

---

## 7. Your Ticket Queue

Check `docs/BOARD.md` for current board state. Your active tickets:

| Ticket | Title | Priority | Phase |
|--------|-------|----------|-------|
| LENS-001 | API Integration Tests + Infra Hardening | P0 | 2.1 |
| LENS-002 | SituationRoom Game Loop MVP | P0 | 2.1 |
| LENS-003 | Server.py Decomposition | P0 | 2.1 |
| LENS-004 → LENS-010 | See BOARD.md for full backlog | P1-P2 | 3-7 |

Sprint details (acceptance criteria) are in `docs/Lead2Dev.md`.

---

## 8. Test Commands

```bash
# Backend tests
python -m pytest tests/ -v --tb=short
python -m pytest tests/test_api.py -v
python -m pytest tests/ --cov=src --cov-report=term-missing

# Quality gate
python quality-gate/quality_gate.py --root .

# Cathedral keeper
python cathedral-keeper/ck.py analyze --root .

# Frontend
cd frontend && npm run dev      # Dev server :3000
cd frontend && npm run build    # Must succeed
cd frontend && npm run lint     # Must be clean
```

---

## 9. How to Start

```
1. READ this file (done)
2. READ anti_slop.md
3. READ docs/BOARD.md — see full board state
4. READ docs/Lead2Dev.md — find your ticket marked 🟢 EXECUTE NOW
5. READ docs/DECISION_LOG.md — settled decisions
6. READ sprint-scoped source files
7. WRITE mini-spec in docs/Dev2Lead.md
8. IMPLEMENT (if Low/Medium) or WAIT for Lead (if HIGH)
9. RUN: python -m pytest tests/ -v (backend) or npm run build (frontend)
10. RUN: python quality-gate/quality_gate.py --root .
11. REPORT in docs/Dev2Lead.md
```

---

_Team LENS Instruction Packet v2.0 — Tech Lead_
