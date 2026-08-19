# Session memory (session fde086af, 509 turns)

Deterministic ledger recovered from the session transcript. Full detail: `ctxpack hydrate` on the session .ctx, or grep the raw transcript.

## Decision conflicts (UNRESOLVED — comply, or restate with `Supersedes: <fact_id> — <reason>`)
- turn 154: "Decision: consolidation lands in two places — curation-time dedup/contradiction pass (E2, after E1+F" vs constraint_collision (s:fde086af#turn104, fact 321d1f8c911c6f96): "Constraint: consolidation (multi-SME dedup, contradiction detection, merge policy) has no owner, des"

## Constraints (verbatim — do not violate)
- Constraint: consolidation (multi-SME dedup, contradiction detection, merge policy) has no owner, design, or milestone anywhere in the current program — the report schedules a minimal curation-time pass at M3 and cross-pack conflict surfacing with the M4 resolver; until then external narratives should say "governed authoring," not "consolidation." (turn 104)
- Constraint: A1 (INT review of S1.1 at `4eead82`) gates every build loop — nothing in Waves B–G should start before it closes. (turn 154)
- Constraint: before minting any new unit ID, reconcile against DELIVERY_LOOPS_BACKLOG_2026-07.md plus the B0–B12/GM0–GM7/Slice A–J inventories — the crosswalk alone is not the full card set. (turn 177)
- Constraint: no BE unit can reach the completion gate until the stale `pack.sig` fixture blocker is dispositioned — treat `verify-audit` gate 1 as unreachable, not as a per-unit caveat. (turn 508)

## Decisions
- Decision: the report reframes the +0.308 number as a governed-term-adoption lift (word-boundary containment judge) dated to the v0.1.0 receipt, and bans "signed" in favor of "content-sealed, unverified at load" — both critic-verified in source. (turn 104)
- Decision: the context-layer target design commits to compile-time resolution — base + overlay packs resolved into one digest-addressed sealed release, serve-time multi-pack merging rejected — because it preserves the invariant that the served thing is the eval-gated thing. (turn 104)
- Decision: recommend GovernanceStore as the single governance write model (resolving Blueprint Open Decision 4), with authenticated approvals and a read-only `/v1/deltas` so trust-envelope delta ids finally resolve. (turn 104)
- Decision: the milestone plan (M1 trustworthy serve → M2 pilot consumption → M3 governed authoring → M4 second pack) rides the existing S1.1–S1.3 + F0.3 + control-plane Slices B/D sequence rather than inventing a parallel roadmap; the two enablers are re-aiming the harness at prod (turn 104)
- Decision: adopted the VDP blueprint as the team-facing architecture baseline and demoted the 2026-07-20 readiness audit to an archived evidence snapshot, per the VDP's own authority section. (turn 154)
- Decision: new gap-closure units use declared NEW card IDs (S1.4, S1.5, C1–C3, E1, E2, V1–V4, R1, H1, DOC-1, G3-probe) attached to existing Steps rather than a parallel numbering scheme, honoring the crosswalk's no-silent-renumbering rule. (turn 154)
- Decision: consolidation lands in two places — curation-time dedup/contradiction pass (E2, after E1+F0.3) and compile-time cross-pack conflict surfacing (R1 resolver) — and until E2 lands, external narratives say "governed authoring," not "consolidation." (turn 154)
- Decision: retired 9 of v1's 14 new card IDs into existing backlog cards (v2 §1 table); the only new code card that survived is F0.10 serve-door contract parity, which merges v1's S1.4+C2 remainder. (turn 177)
- Decision: the backlog's Gates G0–G4 are the milestone frame of record; the audit's M1–M4 are mapped onto them rather than kept as a second frame. (turn 177)
- Decision: build F0.10 rather than S1.2 next, because it is the only unblocked code card that shares no file with the unreviewed `build/S1.1`, so no review outcome can force rework. (turn 508)
- Decision: the hydrate refusal is deliberately non-leaking — a gated-out section and a nonexistent one return an identical error, because distinguishing them would turn the door into an existence oracle for DRAFT content; a test asserts the two messages are the same. (turn 508)
- Decision: "enforce ALWAYS_INCLUDED_KINDS" is scoped to the tag filter, not to trimming, because there is no budget or trim step anywhere in the runtime — the constant's "forbidden from budget-trimming" docstring is aspirational, and inventing a budget here would be scope creep on (turn 508)
- Decision: `TOOL_NAMES` is now derived from the published schema table rather than compared to it by a test, so the name list, MCP schema list and dispatch table cannot diverge by construction; the test was rewritten to assert the property that can still fail — every advertised to (turn 508)
- Decision: the stale-`pack.sig` fixture is left unfixed inside F0.10 and escalated to INT instead of being resealed to turn gate 1 green. (turn 508)

## Exact identifiers (verbatim) (showing 18 highest-rank of 21 — full set in the ledger)
- C:/Users/kapil/Documents/Onto_Wiz/SME_Knowledge_Codification_Blueprint.html [path] (turn 5)
- docs/reviews/PLATFORM_READINESS_AUDIT_2026-07.html [path] (turn 104)
- C:/Users/kapil/Documents/Onto_Wiz/docs/reviews/PLATFORM_READINESS_AUDIT_2026-07.html [path] (turn 104)
- v0.1.0 [version] (turn 104)
- v0.3.0 [version] (turn 104)
- C:/Users/kapil/Documents/Onto_Wiz/docs/reviews/ONTOWIZ_VALIDATED_DOMAIN_PACK_BLUEPRINT_2026-07.html [path] (turn 110)
- docs/specs/VDP_GAP_CLOSURE_LOOPS_2026-07.md [path] (turn 154)
- 9d52b47 [git_sha] (turn 154)
- 4eead82 [git_sha] (turn 154)
- #3 [pr] (turn 154)
- 0.3.0 [version] (turn 177)
- 630a08b [git_sha] (turn 508)
- 2b055e3 [git_sha] (turn 508)
- fa070fa [git_sha] (turn 508)
- 5ebbda3 [git_sha] (turn 508)
- 0.1.0 [version] (turn 508)
- f8a79a3 [git_sha] (turn 508)
- 100% [number_unit] (turn 508)

## Memory incidents (ctx telemetry)
- ctx-incident: saved | fact="local browser-capture path is documented-flaky here" | evidence="headless Chrome and Edge screenshot both timed out on 2026-07-21, exactly as the banked constraint predicted — stopped after two attempts instead of looping" (turn 104)
- ctx-incident: saved | fact="S1.1 review state detail" | evidence="ledger memory carried finding-#3-garbled and the pre-existing fixture-red disposition items that neither the VDP nor the audit mentioned — both now folded into unit A1" (turn 154)
- ctx-incident: user-corrected | fact="v1 loop plan minted duplicate card IDs" | expected="reuse-first applied to planning docs (check backlog before creating cards)" | got="14 new IDs, 9 of them duplicating F0.6A/B, F0.9, E1.1/2, E3.1-be, E4-be, F0.2H, F0.8A, F0.3A–D" | evidence="v2 §1 retirement table" (turn 177)
- ctx-incident: saved | fact="pre-existing red test_write_results_reseals_signed_pack (stale pack.sig on committed 0.1.0 fixture)" | expected="gate 1 red for reasons unrelated to my diff" | got="exactly that, first verify-audit run" | evidence="banked note let me diagnose immediately; independently re-proved at baseline f8a79a3 in a detached worktree, 1 failed in 2.37s" (turn 508)

## What was asked
- /compact (turn 178)
- This session is being continued from a previous conversation that ran out of context (turn 179)