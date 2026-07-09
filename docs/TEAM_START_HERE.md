# Start Here — Onto_Wiz Foundry Build (July 2026)

Welcome. Read in this order, then claim a Loop 0 unit. Budget: ~half a day of reading before any code.

## 1. Read these, in order

**Everyone (≈2 hrs):**
1. `docs/specs/DELIVERY_LOOPS_BACKLOG_2026-07.md` — **the plan you are executing.** Loops, team lanes (BE/FE), handshakes, exit demos. Find your lane and your Loop 0 work.
2. `docs/specs/BUILD_INSTRUCTION_SET_2026-07.md` — the rules of engagement (R1–R6 are non-negotiable, especially R1: one pipe — nothing writes ACTIVE except via an APPROVED Delta), unit-level specs, API and data-model masters.
3. `ontowiz_nextgen_prototype 9.html` — open it in a browser and click every station. This is the **UI source of truth**. (If it isn't committed yet, commit it to `docs/reviews/` first.)
4. `docs/reviews/STRATEGIC_REVIEW_2026-07.md` — *why* we're building this and not something else. Skim §Verdict, §Kill/Keep/Rebuild, and "What the adversarial pass overturned".

**Context, skim as needed:** `docs/reviews/UX_UI_PLAN_2026-07.md` (screen specs, layer model, design principles) · `docs/reviews/FORGE_MODULE_DESIGN_2026-07.md` (Forge mechanics, consensus maths, ratification ladder — mandatory before Loop 3).

**Backend engineers additionally:**
- `docs/PROJECT_STATUS.md` and `docs/adr/` (esp. ADR-012 tier architecture, ADR-015 unit loop) — the existing discipline; we keep it.
- Code tour, in order: `packages/ontowiz-spec/` (contracts + lifecycle), `packages/ontowiz-core/ontowiz_core/bridge.py` (the delta pipe — read every line, it's small), `packages/ontowiz-runtime/` (`context.py` gate, `db.py` — the SQLite seam all new tables go on), `packages/ontowiz-serve/ontowiz_serve/api.py`, `packages/ontowiz-factory/` (`missions.py`, `steward.py`, `forge.py` — the Forge contracts already exist; build on them, don't reinvent).
- `ontology/commercial.yaml` + `packs/commercial_analytics/` — what the machine actually produces.
- Run `scripts/verify-audit.sh` locally before your first commit; it must be green before and after you.

**Frontend engineers additionally:**
- `frontend/src/` — existing app: catalog slice is the quality bar (tested); game/curator components get rewired, not rewritten; the seven `ui/` primitives get adopted.
- Loop 0 job D0: extract the design system *from Prototype 9* (tokens, badges, chips, ConfirmSheet, card stack) into `frontend/src/ui/` with Storybook + Vitest.
- You never hand-write a fetch call — you consume the generated typed client the BE team publishes at each loop's handshake (backlog §0 explains the contract-first seam).

## 2. Refresh your harness — kp_sdlc

Before writing code, pull the latest from the **kp_sdlc** repo and refresh your local dev/test harness and quality checks from it (pre-commit hooks, review checklists, test conventions). Where kp_sdlc and this repo's gate set differ, this repo's CI gate set wins (Build Instruction Set R3: ruff, mypy, pytest ≥85% on shipped code, `check_boundaries.py`, frontend Vitest — all blocking). slop_checker and quality-gate are advisory only from Loop 0 — don't wire them back into the blocking path.

## 3. Memory management — ctx_pack

Use the **ctx_pack** repo for session/context memory management during development: generate your working context packs from it at the start of each unit, and refresh them at loop boundaries (not mid-unit) so the whole team is reasoning from the same snapshot. Keep generated packs out of git (add to `.gitignore` if not already).

## 4. Then start

1. Claim a Loop 0 unit in the backlog (BE: F0.1/F0.2/F0.4/contract tooling · FE: D0/D1).
2. Write the ½-page mini-spec in `docs/specs/`, get a thumbs-up, write the failing test, build.
3. Evidence into `PROJECT_STATUS.md` on completion — the loop closes with a demo on the live URL, never on mocks.

Questions about *why* → Strategic Review. Questions about *what* → Build Instruction Set. Questions about *when/who* → Delivery Loops Backlog. Questions about *how it should feel* → Prototype 9.
