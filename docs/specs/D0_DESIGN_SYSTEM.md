# D0 — Design System from Prototype 9 (FE Loop 0)

**Lane:** Frontend · **Loop:** 0 (Foundations, zero integration) · **Source of truth:**
`docs/reviews/ontowiz_nextgen_prototype_9.html` · **Normative:** Backlog v2 (`§0A–0C`,
`§4`, `§13` D0/D1 table) + Instruction Set (`R1–R14`, `§12` mini-spec + contracts,
`§13` D0/D1 card).

Extract Prototype 9's "foundry" design system into `frontend/src/ui/` and adopt the
existing seven primitives onto it. **Gallery harness: an in-app `/ui` route, not
Storybook** (honors ADR-006 — zero new deps; and Backlog v2 §4 mandates exactly this
"zero-dependency `/ui` gallery + Vitest").

## v2 process alignment (read before D0.2)

- **Builder ≠ verifier (R14, §0A).** FE is the *builder*. A unit is submitted as a §6
  review evidence bundle at an immutable SHA; a read-only reviewer returns a verdict;
  **only INT marks `VERIFIED`** and copies the outcome to `PROJECT_STATUS.md`. Builders
  never self-verify and never write completion claims into `PROJECT_STATUS.md`.
- **Mini-spec depth.** D0.1 keeps its ½-page spec (§13 says so). **D0.2–D0.9 + D1.1 use
  the §12.1 11-section template** (objective, pinned preconditions, ownership paths,
  API/schema, state machine/invariants, threat/egress, 1:1 test map incl.
  negative/retry/concurrency, migration/rollback, telemetry, out-of-scope, dep change).
- **Shared FE DoD (§13).** WCAG 2.2 AA; **360 / 768 / 1440px screenshots** with no
  overlap/clipping; Vitest + type + lint + build pass; relevant Playwright path; **no
  feature-complete claim from the `/ui` gallery alone.**
- **Contract before consumer (R11, §4).** **D1.1 waits on BE F0.3A** (OpenAPI +
  generated TS client + fixtures). FE hand-writes no endpoint calls or response types;
  the shell + route skeletons consume the generated client/fixtures only. D0.2–D0.9
  have no API dependency and proceed freely in Loop 0.

## Unit split (Backlog v2 §13 D0/D1 table)

| Unit | Output | Key unit DoD (beyond shared FE DoD) |
|---|---|---|
| **D0.1** | Tokens + `/ui` gallery | Existing mini-spec; isolated review; **no token drift** |
| D0.2 | Lifecycle/gate badges | **Icon + label, not colour-only**; all true states represented |
| D0.3 | Attribution / provenance / layer chips | Long names/locators responsive; links keyboard-accessible |
| D0.4 | Primitives on Foundry tokens | No nested-card regressions; focus/error/disabled states |
| D0.5 | ConfirmSheet | Shows the **exact** generated artifact+eval; requires explicit confirm |
| D0.6 | CardStack | Stable phone layout; keyboard alternative; **no gesture-only action** |
| D0.7 | Drawer | Focus trap/return; URL/deep-link state; responsive full-screen |
| D0.8 | DiffView | Human semantic diff primary; raw YAML secondary; add/remove accessible |
| D0.9 | Tree | Keyboard tree semantics; stable IDs; depth/overflow handling |
| D1.1 | App shell | Role nav, auth, route skeletons **against generated fixtures** (needs F0.3A) |

---

## D0.1 — Tokens + gallery harness

**Goal.** Make Prototype 9's tokens the canonical, typed source of truth the whole
design system consumes, generate matching Tailwind 4 utilities, and stand up the `/ui`
gallery that later D0 units append to.

**Contract / surface (new files).**
- `frontend/src/ui/tokens.ts` — typed source of truth: `FOUNDRY_COLORS` (void/carbon/
  slab/slab2/edge/edge2/ink/ink2/ink3/cyan/molten/molten-hot/jade/ember/info/iris),
  `FOUNDRY_FONTS` (display/body/mono), `FOUNDRY_RADII` (sm/md/lg/pill). Verbatim hex
  from Prototype 9 `:root`.
- `frontend/src/ui/tokens.css` — `@theme { --color-*, --font-*, --radius-* }` mapping
  the same values → Tailwind utilities (`bg-carbon`, `text-cyan`, `border-edge`,
  `font-display`, `rounded-lg`…).
- `frontend/src/app/ui/page.tsx` — `/ui` gallery scaffold; a **Tokens** section
  rendering colour swatches + type specimens from `FOUNDRY_COLORS`/`FOUNDRY_FONTS`.
- `frontend/src/app/globals.css` — move to Tailwind v4 form (`@import "tailwindcss"`
  + `@import "./…/tokens.css"`); keep existing persona vars/body until D0.4.

**No new deps.** Fonts: family stacks with system fallbacks in D0.1 (Space Grotesk /
IBM Plex Sans / IBM Plex Mono → system-ui). Webfont *loading* via built-in
`next/font/google` is a noted follow-up, kept out of D0.1 to stay offline-safe.

**Tests (Vitest, TDD red first).**
1. `tokens.test.ts` — `FOUNDRY_COLORS` has the 16 named tokens with exact Prototype-9
   hex; fonts/radii present.
2. `tokens.test.ts` (drift guard) — read `tokens.css`; every hex in `FOUNDRY_COLORS`
   appears in it (single source of truth stays in sync; no silent CSS/TS drift).
3. `ui.test.tsx` — `/ui` gallery renders a "Design Tokens" heading and a swatch for
   every `FOUNDRY_COLORS` key.

**Definition of Done (v2).** Vitest green incl. above; coverage `include` extended to
`src/ui/**` + `src/app/ui/**`, ≥85% on new code; `tsc --noEmit`, `eslint`, `next build`
(with `/ui` prerendered) all clean; existing tests stay green; **evidence assembled in
the §6 review bundle** (`docs/reviews/D0.1_REVIEW_BUNDLE.md`), submitted for isolated
review — **not** self-marked in `PROJECT_STATUS.md`; INT records the verified outcome.
Outstanding shared-FE-DoD item: 360/768/1440 responsive screenshots.

**Honest boundaries (deferred, not hidden).** Webfonts declared as stacks, not yet
downloaded. Primitives still on legacy Tailwind colours until D0.4. Visual parity with
Prototype 9 is asserted by build + token-swatch render, not yet by pixel diff.
