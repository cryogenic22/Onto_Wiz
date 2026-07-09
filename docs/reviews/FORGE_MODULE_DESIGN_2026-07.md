# The Forge — Crowdsourced SME Ratification Module

**Companion to:** UX_UI_PLAN_2026-07.md and STRATEGIC_REVIEW_2026-07.md · **Scope:** a separable module — backend service + frontend surface — added to the Domain Knowledge Factory

---

## 1. The honest premise first

The strategic review's sharpest warning applies directly here: *a game that produces no deltas is theatre* (the repo's own prior review named this risk #1, and the founder's red-team called the whole product "an elegant expert system with a modern coat of paint" if scale never arrives). So this design starts from the one thing that makes an SME game not-theatre, which — remarkably — is already enforced in the codebase: `submit_mission()` in ontowiz-factory **refuses any submission that doesn't produce a governed PROPOSED Delta, a gold EvalCase, and an explicit confidence**. The game cannot emit vibes; it can only emit artifacts. That contract is the module's constitution, and every mechanic below is built on top of it rather than around it.

The second honest point: the review found that the corpus is ~92% Claude-drafted and SME-unvalidated. That reframes what the game is *for*. It is not primarily a capture tool (quick capture and document intake already do that more cheaply). **The Forge is the ratification engine** — the mechanism that turns "8% SME-validated" into 80%, one 40-second question at a time, across many SMEs in parallel. Crowdsourced ratification is the scale answer to the validation problem, and it's the only mechanic in the product that gets *stronger* with more players.

And the third: the AI is a co-player, not a scorekeeper. The tool works *with* the SME — it generates the questions from the corpus's own weaknesses, it structures the SME's free-text answer into schema fields live ("is this what you meant?"), and it drafts the artifact + paired eval case in the background. The SME's job is judgment; the machine's job is paperwork. The machine proposes, only humans promote — the confirm step keeps that invariant inside the game itself.

---

## 2. The loop

Corpus scan → **question compilation** (the corpus's weaknesses become questions) → **routing** (each question to k SMEs whose profile matches the hierarchy node) → **play** (40-second missions) → **structured answers** (AI-structured, SME-confirmed) → **consensus** (rating-weighted; dissent preserved) → **auto-composed deltas + evals** → curation queue → recompile → the corpus improves → *the question compiler finds new, harder weaknesses*. The flywheel feeds itself: every ratified artifact retires its questions; every disagreement mints new ones.

---

## 3. The Question Compiler (backend's brain)

The steward already converts two signals into missions (low confidence → *validate*; missing eval → *name the caveat*). The compiler generalises this to eight signal sources, each mapping to a mission type:

| # | Signal (scanned nightly + on recompile) | Question it becomes | Mission type |
|---|---|---|---|
| 1 | Unvalidated artifact (`sme_id: ''`, Claude-drafted) | "Is this rule right?" | **Ratify** |
| 2 | Low confidence (< 0.5, the steward's existing signal) | "Confirm or correct" | **Ratify** |
| 3 | Missing eval case (steward's existing signal) | "Give a real example where this changes the answer" | **Name the caveat** |
| 4 | Rule conflict — overlapping tags, adjacent priorities (the curation drawer already detects these) | "These two rules both claim this situation — which wins, and when?" | **Adjudicate** |
| 5 | Consensus dissent — prior answers split below threshold | Same question re-asked as a head-to-head with both positions shown | **Adjudicate (duel)** |
| 6 | Eval failure — the agent got a gold case wrong even with the pack | "The agent said X. What did it miss?" | **Teach-back** |
| 7 | Coverage gap — a hierarchy node (e.g. Commercial › Field Force) with entities but no rules | "You're seeing [scenario at this node] — what do you check first?" | **Order the cascade** |
| 8 | Anti-pattern gap — a rule with no exceptions recorded | "When does this rule NOT apply?" | **Name the caveat** |

Each question carries the steward's existing `impact` score, so the daily feed is *targeted curation, not a blank-page interview* — the five minutes an SME gives us go to the corpus's weakest, highest-traffic spots. Every question also stamps its hierarchy node, so routing and coverage roll-ups come free from the subdomain model.

---

## 4. The mission catalogue

Four missions at launch, two in v2. Every one ends in the same beat: the AI shows the artifact + eval it drafted from your answer, you confirm or tweak, it lands in the queue as PROPOSED with your name on it.

**Ratify** *(the volume workhorse — 30–60s)*. A rule card: statement, tags, node, one linked example. Three answers: **Agree** / **Disagree** / **It depends**. Agree = endorsement signal toward the ratification ladder. Disagree demands one sentence of why (free text; AI structures it into a correction delta). *It depends* is the gold path: it opens a one-line caveat capture, and the answer becomes an anti-pattern or ExceptionRule — the consensus engine literally has a `consensus_to_exception_rule()` function waiting for this. "It depends" is not indecision; it is the most valuable judgment an SME owns.

**Adjudicate / Duel** *(conflict resolution — 60–90s)*. Two conflicting judgments side by side (from signal 4 or 5), a concrete scenario underneath, and the ask: which wins here, and what would flip it? Output: a priority ordering + boundary condition — exactly the data the L3 priority cascade needs. When the crowd itself stays split (agreement below threshold after k answers), the split is *promoted to knowledge*: an ExceptionRule capturing both positions and their conditions, or escalation to a curator with the full dissent record attached. Disagreement is never averaged away — ForgeRating already weights `dissent_value` highest of all five signals, and this is why.

**Name the caveat** *(exists in the steward today)*. "Give a real case where this rule changes the answer" / "when does it break?" Output: a gold eval case authored by an SME — which is precisely what the strategic review said the lift benchmark is missing (dev-authored evals are circular; SME-authored held-out cases are the fix). Every caveat mission answered is a brick in the real moat.

**Order the cascade** *(coverage gaps — 90s)*. A scenario at an under-served node, five candidate first-moves, drag to rank. Output: hypothesis priorities for a node that had none — cold-start content generation disguised as a ranking puzzle.

*v2:* **Spot the flaw** (an agent answer with one planted error; finding it authors a discriminating eval) and **Teach-back** (replay a real failed eval; the SME's correction becomes both delta and regression test).

---

## 5. Crowdsourcing mechanics: routing, consensus, the ratification ladder

**Routing.** Each question goes to **k SMEs** (default 3; 1 during the cold-start pilot) selected by hierarchy-node profile match, ForgeRating, and freshness (nobody re-answers their own artifact). A question that sits unanswered decays and re-routes wider.

**Consensus** uses the shipped `resolve_consensus()`: consensus answer, agreement fraction, dissent list, and a consensus-weighted confidence that is *honest* — a split room yields low confidence by construction. Votes are weighted by ForgeRating, so a proven contrarian outweighs three rubber-stampers.

**The ratification ladder** — the module's core state machine, and the mechanism behind the dashboard's "SME-validated %" tile:

`unvalidated` (Claude-drafted) → `endorsed` (1 SME agree) → `ratified` (k-consensus at ≥ threshold agreement, rating-weighted) → and on any disagree/depends → `contested` → adjudication → back to `ratified` (with new caveats) or `exception` (a governed it-depends) or curator escalation. Ratification is displayed everywhere the validation chip appears today; the game is what moves it.

**Reliability calibration.** A small fraction of each SME's feed is **gold probes** — questions with curator-settled answers. Probe performance calibrates the per-contribution `weight` multiplier that forge.py already consumes (weight 0 = fully excluded), which is the anti-gaming spine: rapid-fire clicking earns nothing because correctness, not volume, drives rating, and probes catch the clickers.

**Incentives.** ForgeRating is already designed correctly — five signals, dissent weighted highest, volume and speed deliberately absent. The frontend's job is to make earned status *visible and meaningful*: the leaderboard (SMEDashboard exists), and above all the **impact feed**: "Your caveat on R-090 shipped in pack 0.4.0 and now guards eval COMP-SAF-09" — with lineage links to prove it. For consultants, the durable incentive isn't points; it's *attributable, shipped expertise*. Streaks and weekly node challenges ("Field Force week: 14 questions open") are seasoning, never the meal.

---

## 6. Backend module spec — `ontowiz-forge`

A separable Tier-B module: a FastAPI router mounted in ontowiz-serve (same deploy, same JWT/RBAC, no second app — the review's one-backend rule holds) with its logic in the factory package where the contracts already live.

**Reused as-is** (~zero new risk): `missions.py` submit contract (delta + eval + confidence or rejection) · `steward.py` signals→missions · `forge.py` ForgeRating + `resolve_consensus` + `consensus_to_exception_rule` · `bridge.py` governed proposals · the SQLite `db.py` seam · JWT principals.

**New components** (≈ 1.5–2k LOC total, in build order):

| Component | Responsibility | Notes |
|---|---|---|
| **Question Compiler** | Nightly + post-recompile scan of the corpus against the 8 signals → question queue with impact + node | Extends steward's 2 signals to 8; pure functions over artifacts + eval results |
| **Router** | Assign each question to k SMEs by node profile / rating / freshness; decay + re-route | Simple scoring query over SQLite |
| **Play API** | `GET /forge/next` (the feed) · `POST /forge/answer` · `GET /forge/impact` (your shipped contributions) · `GET /forge/leaderboard` | Thin router; answers validated against mission schemas |
| **Answer Structurer** | LLM turns free-text (“why do you disagree?”) into schema fields; returns a confirm payload to the client | The only LLM call in the play path; falls back to raw-text-in-rationale if the model is down |
| **Consensus Engine** | On kth answer: `resolve_consensus` → ladder transition → compose delta(s) via `submit_mission` → queue | Dissent below threshold → mint adjudication question |
| **Probe & Weight Service** | Seed gold probes; compute per-SME contribution weights for forge.py | The anti-gaming spine |
| **Impact Notifier** | On pack publish: match shipped artifacts to contributing answers → impact-feed entries / weekly digest | Reads lineage, writes notifications |

**Data model** (new SQLite tables on the existing seam): `forge_questions` (signal, node, artifact_id, impact, status) · `forge_assignments` (question, sme, expires) · `forge_answers` (structured payload, confidence, raw text, probe flag) · `forge_ratifications` (artifact ladder state + history) · `forge_ratings` (per-SME contribution log → rating) · `forge_probes`.

**Invariants** (non-negotiable, enforced server-side): every accepted answer route terminates in `submit_mission` or an explicit ladder-signal write — no side channel to ACTIVE; the Answer Structurer's output is never persisted without the SME's confirm; consensus never deletes dissent; all writes attributed to JWT principals.

---

## 7. Frontend module spec — `/forge`

A separable route group in the one Next.js app, reusing the nine existing game components' patterns and the design system (lifecycle badges, attribution chips, provenance chips).

**SME surfaces:**
- **Daily Queue** — a card stack, mobile-first (this is the surface SMEs will use from a phone between meetings; it must feel like 40-second turns, not a workstation session). Header: "5 questions · ~3 min · Field Force week". One card = one mission.
- **Mission players** — one component per type: `RatifyCard` (agree / depends / disagree with slide-out caveat line), `DuelCard` (two positions, scenario, boundary-condition prompt), `CaveatCard` (example elicitation), `CascadeCard` (drag-to-rank). All share a `ConfirmSheet`: "here's the artifact + eval I drafted from your answer — ship it to review?"
- **Impact panel** — your rating, your ratified count, and the feed of "your judgment shipped": pack version, eval it guards, lineage link. The retention surface.
- **Leaderboard** — upgrade of the existing SMEDashboard, rating-based (never volume-based), with node-level standings for the weekly challenge.

**Curator surfaces** (inside the existing Workspace/Queue, not a new area):
- **Conflict heatmap** — hierarchy tree coloured by open contests + dissent density; click through to the underlying questions.
- **Question console** — inspect/author/retire questions, set k and thresholds per node, seed probes, review the escalation inbox (persistent splits arriving with full dissent records).
- Forge-originated deltas land in the same Curation Queue, tagged `⚔ forge` with consensus stats (agreement, k, dissent) rendered in the evidence pane.

---

## 8. Phasing, effort, and the kill-test

**Forge v0 — inside month 3, ~2 weeks of the plan's pilot month.** Ratify + Name-the-caveat only, k=1, card stack on the existing contracts, impact feed stubbed to a list. Rationale: the month-3 pilot *needs* a ratification instrument anyway — v0 *is* the pilot instrument, pointed at the 22 unvalidated artifacts. This resolves the review's "don't build the game UI" caution correctly: don't build the 13-mission multiplayer vision; do build the thin ratification loop the strategy already requires.

**v1 — months 4–5.** k=3 routing, consensus engine, ladder, Adjudicate, probes + weights, curator console. This is when "crowdsourced" becomes true — and it's gated on v0 evidence that SMEs come back.

**v2 — month 6+.** Duels from live dissent, Spot-the-flaw, Teach-back, weekly node challenges, PWA polish, cross-client SME pools (needs the multi-tenancy decision first).

**The kill-test, instrumented from day one** (the theatre alarm): governed deltas per SME-hour (must beat the quick-capture baseline or the game is decoration); week-2 SME return rate; ratified-% velocity on the dashboard tile; median answers-per-question (routing health); probe accuracy distribution (crowd quality). If v0's numbers say SMEs won't play, the loss is two weeks — and quick capture + document intake still carry the pilot.

---

## 9. Why this design survives its own critique

The three ways SME games die, and the countermeasure built into each: **(1) They produce engagement, not artifacts** → the submit contract makes non-artifact-producing interaction structurally impossible, and deltas-per-SME-hour is the headline metric. **(2) They reward the wrong people** → rating is correctness- and dissent-driven with volume absent, probes calibrate weights, and consensus is rating-weighted. **(3) They flatten disagreement into mush** → dissent is the highest-paid signal, splits become ExceptionRules or curator escalations with the minority position preserved verbatim — because in consulting judgment, "it depends, and here's on what" *is* the product.
