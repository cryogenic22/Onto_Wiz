# Onto_Wiz Foundry — Delivery Loops Backlog v1.0

**Teams:** Backend (BE) · Frontend (FE) · **Cadence:** 2-week loops · **Derived from:** BUILD_INSTRUCTION_SET_2026-07.md (unit IDs reference it) · **UI source of truth:** Prototype 9

**North star:** an SME's tacit judgment enters through Intake / Forge / Capture / Studio and leaves as a gated, versioned, provenance-carrying pack that measurably lifts an agent — with every object SME-ratified and every change through one governed pipe.

---

## 0. First, your question: should the backend team own the FE↔BE linking?

**Yes — with one refinement, and it's the thing that makes the whole parallel plan work.** Raw "backend does integration" has a known failure mode: FE builds against imagined APIs for two weeks, then integration becomes a crunch of mismatched shapes and blame. The refinement is **contract-first**: the BE team's first deliverable in every loop is not the implementation but the **handshake artefact** — the OpenAPI contract for that loop's endpoints, the generated TypeScript client, and a fixture pack (realistic mock responses). FE builds the whole loop against the mock client; BE implements against the same contract; in the last 2–3 days of the loop BE swaps mocks for real and owns making the wire work (auth, error shapes, pagination, latency).

So the allocation you proposed stands: **BE owns the contract, the generated client, the fixtures, and the final wiring. FE never hand-writes a fetch call** — it consumes the typed client only. What FE owns is everything from the client boundary up: components, state, interaction, accessibility, tests. The rule that keeps everyone honest: *if integration breaks, the contract was wrong or the implementation drifted from it — both BE-owned; if the UI misuses a correctly-shaped response, that's FE-owned.* Clean seam, no blame ambiguity, and each loop ends with a joint demo on the live URL, never on mocks.

---

## 1. The loop map (what runs in parallel, what must be sequential)

```
Loop 0        Loop 1        Loop 2        Loop 3        Loop 4        Loop 5        Loops 6–8
Foundations   One System    Intake        Forge v0      Curation      Compose &     Forge v1 →
(parallel,    (G0 gate)     (+ gate       (G1: PILOT    Depth +       Release       Studio
no wire)                    hard-fail)    STARTS)       Ontology v1   (G3 gate)     (gated)
BE ████       BE ████       BE ████       BE ████       BE ████       BE ████       BE ████
FE ████       FE ████       FE ████       FE ████       FE ████       FE ████       FE ████
   no integ.     integ.²       integ.²       integ.²       integ.²       integ.²      integ.²
```
² = BE-owned wiring in the final days of the loop, joint demo to close.

Sequencing constraints that cannot be traded away: persistence (L0) before anything user-facing; one authenticated backend (L1) before any new station; the eval gate hard-fail (L2) before the pilot; Forge v0 (L3) *is* the pilot instrument so it lands exactly at pilot start; Forge v1 waits for pilot evidence; Studio waits for Intake's extraction machinery to be proven in batch. Everything else parallelises.

---

## 2. The loops

### Loop 0 — Foundations (weeks 1–2) · *fully parallel, deliberately zero integration*

| | Backend team | Frontend team |
|---|---|---|
| Work | **F0.1** rotate key, purge history, CI = 5-gate set · **F0.2** governance persistence (deltas/approvals/audit/contributions on SQLite; restart-survival test) · **F0.4** parser interface + pptx/vtt/xlsx/eml parsers (golden files) · **Tooling:** OpenAPI-first pipeline — spec → generated TS client → mock server, wired into the FE repo | **D0** extract the design system from Prototype 9 into `frontend/src/ui/`: tokens, lifecycle badges, attribution/provenance chips, ConfirmSheet, card stack, drawer, diff view, tree — Storybook'd, Vitest'd · **D1** app shell: role-shaped nav (SME/curator), auth screens against mock client, route skeletons for all 7 stations |
| Exit demo | Kill the process mid-approval, restart, audit trail intact — on video | Storybook walk-through of every component; shell click-through in both roles |

### Loop 1 — One System (weeks 3–4) · **gate G0**

| | Backend team | Frontend team |
|---|---|---|
| Handshake (day 1–2) | **Contract v1:** `/v1/auth`, `/v1/deltas` (list/get/approve/reject/escalate/resubmit), `/v1/ontology` (nodes + layers read), dashboard stats + fixtures | — consumes |
| Work | **F0.3** port the ~14–18 SME endpoints under JWT/real principals · **F0.7** hierarchy `parent` + roll-up query · **F0.8** deploy to Railway · **F0.5** delete `src/` + gate 6 once FE has re-pointed | **Dashboard** (stat tiles, expandable coverage board, attention feed) and **Curation Queue v1** (table + drawer with human-readable diff, approve/reject) — built on mocks days 1–8 |
| Integration (BE, days 8–10) | Swap mock→real; auth flows; error/empty/loading states verified against live | joint bug-bash |
| Exit demo | On the **live URL**: log in as curator, approve a delta, restart the server, approval survives, audit shows a named principal. Legacy `src/` deleted same day. |

### Loop 2 — Intake + Gate Integrity (weeks 5–6)

| | Backend team | Frontend team |
|---|---|---|
| Handshake | Contract v2: `/v1/intake` (sources, candidates, promote/edit/reject) + fixtures incl. a real parsed VTT | — |
| Work | **E1** extraction job (layer-classified candidates w/ seeding sentence + locator + paired eval for L3), sources/candidates tables + API · **F0.6** compiler hard-fails ungated packs; re-gate 0.3.0→0.4.0; fix Germany/US gold-set bug | **SourceLibrary** (yield-by-layer chips, promoted x/y) · **ExtractionSheet** (two-pane: highlighted transcript ↔ candidate list, click-to-jump) · **CandidateCard** (promote / fix / reject-with-reason) |
| Exit demo | Drop the real Field Force QBR .vtt on the live system → triage a candidate → its delta appears in the queue with the seeding sentence in the evidence pane. The served pack has `gate_passed: true` + a lift number. **Metric live:** candidates promoted/SME-hour. |

### Loop 3 — Forge v0 (weeks 7–8) · **gate G1 — the pilot starts here**

| | Backend team | Frontend team |
|---|---|---|
| Handshake | Contract v3: `/v1/forge` next/answer/impact + fixtures for both mission types | — |
| Work | **E2.1** question compiler (signals 1–3, 8), Assay + Name-the-caveat via existing `submit_mission`, ratification-ladder states, impact feed, k=1 routing · **theatre-alarm telemetry** (deltas/SME-hour) from day one | **ShiftQueue** card stack (mobile-width first), **AssayCard**, **CaveatCard**, shared **ConfirmSheet** ("here's the artifact + eval I drafted — ship it?"), **ImpactPanel v0**, ratification-ladder tile on dashboard |
| Exit demo | A real SME completes a 5-question shift on a phone in <4 min; every answer visible in the queue as delta+eval; SME-validated % ticks up on the dashboard. **Pilot cohort (3–5 ZS SMEs) onboarded this week.** |

### Loop 4 — Curation Depth + Ontology v1 (weeks 9–10) · *pilot running in background — expect interrupt capacity ~20%*

| | Backend team | Frontend team |
|---|---|---|
| Handshake | Contract v4: dry-run endpoint, conflict detection, lineage query, layer CRUD-as-deltas | — |
| Work | **E3.1-be** conflict detector (shared tags/adjacent priority), `GET /deltas/:id/dryrun` on gold set, lineage query · **E3.2-be** structured editors' delta composition per layer | **Drawer upgrade** (conflict callout, dry-run button, source-specific evidence renderers, edit-and-resubmit w/ dual attribution) · **Layer browser** L1–L5 with structured editors, node column, inheritance chips · **Lineage tab** |
| Exit demo | The full DELTA-147 flow from the prototype, live: conflict warning → dry-run → edit → approve → watch recompile+eval toast sequence → new version in Packs. |

### Loop 5 — Hierarchy, Mappings, Compose & Release (weeks 11–12) · **gate G3**

| | Backend team | Frontend team |
|---|---|---|
| Work | **E3.3-be** hierarchy ops as deltas + reparent · **E3.4-be** mappings (synonym, cross-domain) as governed artifacts · **E4-be** pack composer (node+layer selection → manifest), version diff, publish gated | **Manage-hierarchy mode**, **Mapping Workbench** (side-by-side, typed links), **Pack composer + release-gate panel** (publish button structurally absent when failing), **consume tab** + try-it console |
| Exit demo | Compose a pack scoped to Commercial › Payer/Access + Field Force → gate passes with ≥1 SME-authored held-out eval → publish → an agent consumes it via MCP live. |

### Loops 6–8 — Evidence-gated expansion (months 4–6)

**Loop 6 — Forge v1** (gated on the G1+2wk kill-test: deltas/SME-hour ≥ quick-capture baseline AND week-2 return > 0): BE — k=3 routing, `resolve_consensus`, gold probes + weights, Duel + Hunt signals; FE — DuelCard, calibration panel, crew standing, corpus heat. **Loop 7 — Standards & graph:** BE — standards-glossary mapping API, graph query; FE — standards workbench tab, read-only reactflow graph. **Loop 8 — Studio** (gated on Intake extraction quality proven in batch): BE — conversation-as-source service, the grounded structurer contract (quoted-span validation, boundary-question behaviour), stage/commit; FE — StudioCanvas (dashed staging), TurnStream, commit flow. If the pilot evidence is weak, Loops 6–8 are replaced by hardening Intake + Queue — that decision is taken at the loop boundary, not mid-loop.

---

## 3. Standing rules for every loop

1. **Handshake before build:** no FE story starts until the loop's contract + fixtures are merged (BE days 1–2). A contract change mid-loop is a BE bug.
2. **Integration is a BE deliverable** with a named owner per loop; FE pairs on the bug-bash but the wire is BE's to make good.
3. **Demo on the live URL or it didn't happen.** Mock-only demos don't close a loop.
4. **The unit loop discipline (R2) applies inside both lanes:** mini-spec → failing test → implement → gates → PROJECT_STATUS evidence.
5. **One pipe regression suite runs every loop** — a test that actively attempts to mutate the corpus around the delta pipe and must fail.
6. **Loop boundaries are the only place scope changes.** Pilot feedback lands in a triage list, not in the current loop.
7. **Metrics reviewed at every close:** deltas/SME-hour, SME-validated %, median review latency, pilot return rate — the north-star dashboard is itself a Loop 1 deliverable and never regresses.
