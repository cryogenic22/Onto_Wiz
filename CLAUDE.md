# CLAUDE.md — operating contract for Onto_Wiz

Build discipline is **loop-driven with an anti-overstatement harness** (ADR-015,
adopted from Content_medical_hub ADR-0001). Read `docs/PROJECT_STATUS.md` for
current truth and `docs/DELIVERY_PROTOCOL.md` for the full loop.

## The loop (one unit at a time)

```
mini-spec (ADR-008) → reuse-first → TDD red → build (green) → gates → fix → verify → record
```
Stop at unit boundaries and report. Do not run ahead.

## Three gates (non-negotiable)

1. **Anti-bloat gate.** Before writing new code, search for what exists and
   reuse it (SpecOmagic / market_zero / `src` / `packages`). The Slop Checker
   enforces this. Porting > re-creating; note provenance when you port.
2. **Reproduce-the-failure gate.** Write the failing test FIRST (TDD red) that
   encodes the success criteria. No implementation before a red test.
3. **Completion gate.** A unit is DONE only when `bash scripts/verify-audit.sh`
   passes AND the evidence is recorded in `docs/PROJECT_STATUS.md`.
   **"Written" / "committed" ≠ "done."** Never mark a Task complete on a partial
   implementation or a red gate.

## Definition of Done

- [ ] Failing test written first, now green; coverage ≥ 85% on new code.
- [ ] `ruff` + `mypy` clean on changed packages.
- [ ] `scripts/verify-audit.sh` passes (all 6 owned gates green).
- [ ] No reused logic re-implemented (Slop Checker); provenance noted on ports.
- [ ] `docs/PROJECT_STATUS.md` updated with the evidence.

## Persistence check

After edits, confirm they persisted (the harness emits file-modification
notices; re-read on doubt). Guards the silent linter-revert failure mode.

## Status lives in one place

`docs/PROJECT_STATUS.md` — NOT in chat or memory. Memory may point to it; it must
not hold the status itself.

## Tier boundary (ADR-012) — protects the IP

```
Tier A (ships):  ontowiz-spec · ontowiz-ctx · ontowiz-runtime · ontowiz-serve
Tier B (secret): ontowiz-core · ontowiz-factory
Rule: Tier A imports Tier A only. Tier A → Tier B is a build failure.
```
Enforced by `tools/check_boundaries.py` (pytest + pre-commit) and ADR-007's
Cathedral Keeper.

## Verify

```bash
bash scripts/verify-audit.sh   # the independent gate that makes "done" falsifiable
```

<!-- ctxpack:session-memory:v4 -->
## Session memory (ctxpack ledger)

This repo uses CtxPack Checkpoint: hooks pack every compaction and
session end into `.claude/ctx/` (a deterministic ledger — the raw
transcript is never deleted), and each session start re-injects the
previous session's gist. Trust the gist's constraints and decisions.

**Resuming or recalling past-session detail — use the ledger read path
FIRST**; fall back to grepping the raw transcript only if it fails
(fallbacks are tracked):

- One-call resume: `ctx/resume` (MCP) or `ctxpack session resume` —
  gist + decisions + constraints + failed approaches + exact identifiers
- MCP (if connected): `ctx/session_recall`, `ctx/session_timeline`,
  `ctx/session_decisions`, `ctx/session_literals`, `ctx/why`,
  `ctx/graph_query`
- CLI twins: `ctxpack session decisions | timeline | recall | literals |
  why | graph | resume` (`--session <id>` targets older sessions;
  `ctxpack session stats` shows adoption + capture metrics)
- Bank the session BEFORE `/clear` or risky context loss: `ctx/checkpoint`
  (MCP) or bare `ctxpack checkpoint` (both auto-resolve the live
  transcript)

**Decision convention (load-bearing):** state every nontrivial decision
(design choice, root cause, chosen fix, abandoned approach) in your reply
on its own sentence starting with `Decision:` — e.g. `Decision: use
exponential backoff with base 750ms because the vendor limit is 40
req/min.` The deterministic parser extracts these; unmarked decisions in
free prose are often missed. State marker lines in the turn-FINAL
message (the reply that ends your turn): Claude Code 2.1.x does not
reliably persist mid-turn assistant text to the transcript, and what
never reaches the transcript can never reach the ledger — restate
mid-work decisions in your closing summary. Dead ends the same way:
"The X approach didn't work because ...". Operating rules you set
yourself the same way, sentence-leading: `Constraint: eval results are
immutable — write new versioned files, never overwrite.`

**Override convention (conflict lint):** when a new decision knowingly
changes a banked decision or constraint, follow the `Decision:` line
with its own line: `Supersedes: <fact_id> — <reason>` (recover the
fact_id via `ctxpack session why "<value>"`). The checkpoint lint
surfaces unresolved collisions at the top of the next gist; a declared
supersession resolves the row and demotes the old fact in rank. The
goal is "never change decisions silently", not "never change
decisions". Malformed overrides are ignored — the conflict stays
visible rather than being silently waved through.

**Incident convention (memory telemetry):** when the ledger visibly helps
or fails you, record it on its own line, sentence-leading:
`ctx-incident: <type> | fact="<the fact involved>" | expected="..." |
got="..." | evidence="..."` — types: saved, missed, stale, wrong,
conflicting, native-better, user-corrected. Only type and fact are
required; include the concrete value so the row is auditable. Examples:
`ctx-incident: stale | fact="CACHE-TTL-S current value" | expected="25"
| got="50"` or `ctx-incident: saved | fact="commit 66cdded scope" |
evidence="session why returned turn 408"`. Report failures as readily as
saves — a missed/stale row is worth more than a flattering one.
<!-- /ctxpack:session-memory -->
