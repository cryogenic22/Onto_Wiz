# Mini-spec — F0.10: The serve door honors its own contract

**Unit:** F0.10 — serve-door contract parity (NEW; ratified in
`VDP_GAP_CLOSURE_LOOPS_2026-07.md` §1 — merges v1's S1.4 with the un-owned remainder of C2)
· **Owner:** BE · **Size:** M
**Depends on:** nothing (disjoint from `build/S1.1`: touches no compiler, writer, or
`pack_manifest` file) · **Blocks:** F0.8A pilot profile, DOC-1 adopter quickstart, and any
honest "an agent can consume a pack" claim.
**Baseline SHA:** `f8a79a3` (`foundry-build`) · **Review SHA:** *this branch's submission SHA*
**Anchors:** VDP gap register G5, G9, G19 · audit §"serve door" · invariant "the served
directory and the hydratable set are the same set" · DoR §13 (16 items) · evidence bundle §14.

---

## 1. Objective & named consumer

**The serve door instructs agents to call a tool it does not serve, and answers a request
for knowledge it has deliberately gated with silent success rather than refusal.** F0.10
makes the door's behavior match the contract it prints: the advertised hydrate tool exists
and is governance-gated; a request outside the gated directory is a typed refusal; the
declared safety carve-out is actually enforced; and the two doors return the same trust
envelope.

**Consumer:** any agent integrating over REST or MCP. Today such an agent reads
`system_prompt`, follows its instruction to call `ctx/hydrate(section=...)`
(`hydration_protocol.py:44,81`), and receives `{"error": "unknown tool: ctx/hydrate"}` from
`dispatch` (`mcp.py:93`) because the door registers only three tools
(`mcp.py:26`). Over REST there is no hydrate route at all. The only working hydrate path is
`ontowiz_ctx.integrations.mcp_server`, which reads a `.ctx` **file path** and therefore
serves the *ungated* document — the governance gate is bypassed entirely. So the
consumption half of the product is either broken or unsafe, and the DOC-1 quickstart cannot
be written honestly until this closes.

---

## 2. In-scope / out-of-scope

**In:**
1. `hydrate_for_pack(...)` — a Tier-A runtime function that hydrates **only** from the
   gated, query-restricted document (the same set `get_context` advertises).
2. `SectionNotServableError` — one typed, non-leaking refusal for any requested section
   that is not in the gated directory.
3. `ALWAYS_INCLUDED_KINDS` enforcement in `gate()`: a safety-layer artifact is exempt from
   the **tag** filter (it stays subject to the lifecycle filter).
4. Trust-envelope parity: one shared serializer used by both doors; MCP `context/get` gains
   `artifacts_used` + `backing_deltas`.
5. New doors: MCP tool `ctx/hydrate`, REST `POST /v1/hydrate`.
6. A blocking end-to-end test: load pack → `context` → read a section name out of the
   returned directory → hydrate it through the door → assert governed content came back.

**Out:**
- Authentication on `/v1/context` and `/v1/hydrate` (both are unauthenticated today) →
  **F0.8A** pilot serve profile, together with disabling the `X-OntoWiz-Role` dev fallback.
- Deleting or re-gating `ontowiz_ctx.integrations.mcp_server` (the raw-file-path server) →
  **F0.8A** deployment profile decides what a tenant may reach. F0.10 only adds the
  in-package warning that it is a local/dev tool and must not be tenant-exposed.
- Changing `hydrate_by_name`'s contract inside `ontowiz-ctx` → **F0.9** owns that package;
  F0.10 wraps it rather than editing it, so CLI/benchmark callers are untouched.
- A token budget or trimming step. **There is none in the runtime** — `get_context` takes no
  budget parameter and nothing trims (only `context.py:190` counts words after the fact).
  The `ALWAYS_INCLUDED_KINDS` docstring's "forbidden from budget-trimming" is therefore
  aspirational; F0.10 enforces the carve-out against the filter that *does* exist. A real
  budget step → **Step-5 compiler-v2 / SCALE-1** findings.
- Per-kind `to_prompt_text` renderers, BODY-format changes → **G16 / Step-5 compiler v2**.

---

## 3. Files & ownership (BE)

- **modify** `packages/ontowiz-runtime/ontowiz_runtime/context.py` — `gate()` safety
  carve-out (`:77-88`); `ContextResult` gains `eligible_doc` so hydration reuses the exact
  restricted document rather than re-deriving it (`:50-62`, `:180-191`).
- **new** `packages/ontowiz-runtime/ontowiz_runtime/hydrate.py` — `hydrate_for_pack`,
  `HydrationPayload`, `SectionNotServableError`, `servable_sections`.
- **modify** `packages/ontowiz-runtime/ontowiz_runtime/__init__.py` — exports.
- **new** `packages/ontowiz-serve/ontowiz_serve/envelope.py` — `trust_payload(trust)`, the
  single trust serializer both doors call (kills the drift class, not just this instance).
- **modify** `packages/ontowiz-serve/ontowiz_serve/api.py` — `_context_payload` (`:104-119`)
  delegates to `trust_payload`; new `HydrateRequest` model + `POST /v1/hydrate`.
- **modify** `packages/ontowiz-serve/ontowiz_serve/mcp.py` — `TOOL_NAMES` (`:26`) gains
  `ctx/hydrate`; `handle_hydrate`; `handle_context_get` trust block (`:72-77`) delegates to
  `trust_payload`; `Tool(...)` list (`:109-115`); `dispatch` (`:83-99`) error boundary gains
  a `SectionNotServableError` branch.
- **modify** `packages/ontowiz-ctx/ontowiz_ctx/integrations/mcp_server.py` — module-docstring
  warning only (no behavior change).
- **new tests** `packages/ontowiz-runtime/tests/test_hydrate.py`,
  `packages/ontowiz-serve/tests/test_serve_door_parity.py`;
  **modify** `packages/ontowiz-runtime/tests/test_context.py` (carve-out cases).

Untouched: every file on `build/S1.1` (`pack_manifest.py`, `compiler.py`, `writer.py`) —
F0.10 and S1.1 are mergeable in either order.

---

## 4. The gated hydration pipeline (ordered, fail-closed)

`get_context` already computes the eligible set and restricts the document to it
(`context.py:180-186`). F0.10 keeps that as the single source of eligibility and hydrates
from its output — the served directory and the hydratable set are the same object, so they
cannot drift.

```
1. gate(artifacts, tags, dev_mode)        # lifecycle filter, then tag filter
                                          #   + NEW: ALWAYS_INCLUDED_KINDS bypass tag filter
2. _rank_by_query(...)                    # unchanged
3. _restrict_doc(doc, eligible_ids)       # unchanged -> eligible_doc
4. servable = {section names in eligible_doc}
5. for each requested name (case-insensitive):
       if name not in servable: raise SectionNotServableError   # FAIL CLOSED, before any read
6. hydrate_by_name(eligible_doc, names, include_header=False)    # reused from ontowiz-ctx
7. return HydrationPayload(text, sections_matched, trust)        # same TrustEnvelope as /context
```

Step 5 is **all-or-nothing**: one non-servable name refuses the whole request. A partial
success is what produced the silent-empty defect; splitting the difference reintroduces it.

**Non-leaking refusal (deliberate).** A section that exists in the pack but was gated out
and a section that never existed produce the **identical** error. Distinguishing them would
turn the hydrate door into an oracle for the existence of REVIEW/DRAFT artifacts — the exact
information the lifecycle gate exists to withhold. The error names the requested section and
lists the currently-servable ones (which the caller already holds from the directory), and
nothing else.

### `ALWAYS_INCLUDED_KINDS` — what "enforce" means here

`ALWAYS_INCLUDED_KINDS` (`artifacts.py:80-84`: `override_rule`, `guardrail`, `data_quirk`)
has **zero non-test consumers** today; `context.py` never imports it. The filter that
actually drops artifacts is the tag intersection at `context.py:80-87` (`have & wanted`),
so a `GUARDRAIL` that carries no matching tag is silently removed from a tag-sliced request
— a safety layer disappearing from a narrowed context is the worst possible failure mode of
a slice.

New rule, stated precisely:

> Within one loaded pack, an artifact whose kind is in `ALWAYS_INCLUDED_KINDS` is **exempt
> from the tag filter**. It remains subject to the lifecycle filter — an unapproved
> guardrail is still not servable.

Scope is deliberately "within one loaded pack": `gate()` only ever sees one pack's
artifacts, so this cannot leak a guardrail across pack boundaries. When multi-pack
composition arrives (**E4-be**), the rule must be re-examined; noted in §8.

---

## 5. Typed errors and door mapping (new, Tier A)

| Error | Raised when | MCP `dispatch` | REST |
|---|---|---|---|
| `SectionNotServableError(LookupError)` | any requested section is absent from the gated directory | `{"error": "section not servable: <name>"}` | **404** `section not servable: <name>` |
| `ValueError` (empty `sections` list) | caller requests zero sections | `{"error": "invalid argument: ..."}` | 422 (pydantic `min_length=1`) |
| existing `FileNotFoundError` | unknown pack | `{"error": "pack not found"}` (unchanged) | 404 (unchanged) |

404 rather than 403 for the refusal: 403 would confirm the section exists.

---

## 6. Persistence / determinism / egress

No database, no network, no model call, no filesystem write. `hydrate_for_pack` is a pure
function of (loaded pack, query, tags, dev_mode, requested sections). Nothing new is logged;
the refusal message contains only names the caller already supplied or already received in
the directory — no filesystem paths, no gated artifact ids, no tracebacks (the `dispatch`
boundary at `mcp.py:83-99` remains the only MCP error surface).

---

## 7. Tests mapped 1:1 to acceptance

| Acceptance | Test |
|---|---|
| Hydrating a servable section returns its governed body | `test_hydrate.py::test_hydrate_returns_gated_section_body` |
| A section gated out by **tags** refuses | `::test_hydrate_refuses_tag_gated_section` |
| A section gated out by **lifecycle** (DRAFT) refuses | `::test_hydrate_refuses_non_servable_lifecycle` |
| A section that does not exist refuses **identically** (no oracle) | `::test_unknown_and_gated_sections_are_indistinguishable` |
| Refusal is all-or-nothing (one bad name in a good batch) | `::test_partial_batch_refuses_whole_request` |
| Refusal names no gated artifact id and no path | `::test_refusal_message_leaks_nothing` |
| Case-insensitive names, matching `hydrate_by_name` | `::test_section_names_are_case_insensitive` |
| Hydration carries the same TrustEnvelope as `/v1/context` | `::test_hydrate_trust_matches_context_trust` |
| Guardrail survives a tag slice that excludes its tags | `test_context.py::test_guardrail_survives_tag_slice` |
| …and all three always-included kinds do | `::test_all_always_included_kinds_bypass_tag_filter` |
| …but an **unapproved** guardrail is still refused | `::test_draft_guardrail_is_not_rescued_by_carve_out` |
| A non-safety kind is still dropped by the tag filter (carve-out is narrow) | `::test_tag_filter_still_drops_ordinary_kinds` |
| MCP `context/get` trust == REST `/v1/context` trust, key for key | `test_serve_door_parity.py::test_trust_envelope_keys_match_across_doors` |
| MCP trust carries `backing_deltas` | `::test_mcp_context_get_carries_backing_deltas` |
| `TOOL_NAMES` == the tools `create_server` declares (anti-drift) | `::test_declared_tools_match_tool_names` |
| `ctx/hydrate` is dispatchable and gated | `::test_mcp_hydrate_dispatch_returns_content` / `::test_mcp_hydrate_refuses_gated_section` |
| REST `POST /v1/hydrate` 200 / 404 / 422 | `::test_rest_hydrate_ok`, `::test_rest_hydrate_404_on_gated`, `::test_rest_hydrate_422_on_empty` |
| **Blocking e2e:** directory → hydrate → governed content, through the door only | `::test_e2e_directory_to_hydrate_through_serve_door` |
| The prompt's advertised tool is actually served (the original defect) | `::test_advertised_tool_is_registered` |

Coverage ≥85% on changed runtime and serve code; every refusal path has a can-fail test.
The e2e test parses the section name **out of the returned `system_prompt`** rather than
hard-coding it — otherwise it would pass even if the directory and the hydratable set drifted
apart again.

---

## 8. Migration, kill criteria, deferred

**Migration:** purely additive at both doors. `_context_payload`'s REST keys are unchanged
(the shared serializer is extracted from it, so REST is the reference shape and MCP moves to
match). The `gate()` carve-out changes no existing expectation — the real
`commercial_analytics` pack contains zero always-included kinds (verified: 1
`entity_registry` + 23 `decision_heuristic`), so no shipped slice count moves. New behavior
is exercised on artifacts built inline in tests.

**Kill criteria:** if enforcing the carve-out turns out to require a real budget/trim step to
be meaningful, stop and fold item 3 into the Step-5 compiler-v2 slice rather than inventing
a budget here. If the refusal contract conflicts with S1.2's `release_verifier` error
taxonomy when S1.1/S1.2 land, F0.10's errors defer to that taxonomy in a follow-up amend.

**Deferred:** auth/tenancy on both doors → **F0.8A**. Raw-path hydrate server disposition →
**F0.8A**. Guardrail semantics under multi-pack composition → **E4-be**. Real BPE token
counts on the hydrate payload → **SCALE-1**. Per-kind renderers so a hydrated
`MetricDefinition` reads well → **G16 / Step-5**.

---

## 9. DoD

The advertised `ctx/hydrate` tool is registered and dispatchable at both doors; hydration
reads only from the gated document; a non-servable section refuses with one typed,
non-leaking error at both doors; the three `ALWAYS_INCLUDED_KINDS` survive a tag slice while
an unapproved guardrail does not; both doors emit an identical trust envelope from one
serializer; a directory→hydrate→content e2e passes through the serve door; `verify-audit`
PASS; evidence bundle per §14 with unrelated changes excluded. **The builder does not mark
this VERIFIED** — one review SHA on `build/F0.10`, REV reviews it, INT integrates.
