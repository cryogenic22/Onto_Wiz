# Onto_Wiz Design-System Convergence Plan

**Version:** 1.0
**Date:** 2026-07-12
**Status:** PLANNING SPEC — NOT AN IMPLEMENTATION-READY MINI-SPEC
**Lane:** FE (author) · informs INT slice-mapping and the D0/D1 backlog
**Audience:** INT, FE, BE, KE, REV
**Governs:** how the control-plane prototype's UI layer converges onto the reviewed D0
`frontend/src/ui` design system, so the productionized surface is one high-grade,
integrated system rather than two look-alikes.

---

## 0. Why this document exists

The Context Control Plane blueprint (`CONTROL_PLANE_PRODUCT_BLUEPRINT_2026-07.md`) makes
the design system load-bearing: §16.3 requires "accepted D0 tokens and primitives … route-
scoped prototype CSS must not establish a second global design system"; §5 line 161 lists
the route-local CSS duplication as a P1 production blocker; §5 line 160 requires the
prototype's parallel lifecycle vocabulary to rebase onto canonical `ontowiz-spec` contracts.

On inspection, that duplication already exists in the tree. There are **two** UI foundations
under `frontend/`:

1. **Canonical (reviewed):** `frontend/src/ui/` — `tokens.ts`/`tokens.css` (D0.1),
   `LifecycleBadge` (D0.2), `chips` (D0.3). Extracted verbatim from Prototype 9.
2. **Prototype (unreviewed):** `frontend/src/features/control-plane/` — `Primitives.tsx`
   (3 exports), a **3,360-line** route-scoped `control-plane.module.css` (~800 classes), and
   `types.ts` carrying its own status vocabulary.

They look similar but are **not the same system**. This plan sets the convergence rule,
provides the authoritative crosswalks, reshapes the D0 backlog to cover what the control
plane actually needs, and defines the incremental rebase (the D1.2-era work). It does **not**
start the rebase, build control-plane views, or freeze the reference SHA (Slice A) — those
are INT-sequenced and, for data-bearing views, gated on BE's F0.3A contract.

---

## 1. Ratified decision

**D0 `frontend/src/ui` tokens are the single canonical design system.** The prototype's
`--cp-*` custom properties and `control-plane.module.css` retire onto them. The prototype's
appearance shifts imperceptibly (the deltas below are ≤ a few hex points per channel); the
reviewed D0.1 SHA is unaffected. One system, not two.

> Rationale: D0 tokens are the reviewed, Prototype-9-true source of truth. The `--cp-*` set
> reads as a slightly-off re-typing of the same palette, not a deliberate second theme.

---

## 2. Finding: the drift, quantified

**0 of 15 color tokens match**, and the font stacks differ. §A is the authoritative crosswalk
used by the rebase.

### §A — Token reconciliation (authoritative rebase map)

| Role | D0 canonical (`tokens.ts`) | Prototype (`--cp-*`) | Δ |
|---|---|---|---|
| page background | `void` `#0A1519` | `--cp-bg` `#081317` | drift |
| raised surface | `carbon` `#0E1D22` | `--cp-surface` `#0D1C21` | drift |
| surface-2 | `slab` `#15282E` | `--cp-surface-2` `#12262C` | drift |
| surface-3 | `slab2` `#1C333A` | `--cp-surface-3` `#193239` | drift |
| hairline border | `edge` `#26414A` | `--cp-edge` `#24434C` | drift |
| strong border | `edge2` `#365660` | `--cp-edge-strong` `#35606A` | drift |
| primary text | `ink` `#E8EFEC` | `--cp-text` `#E8F0ED` | drift |
| secondary text | `ink2` `#9FB4B2` | `--cp-muted` `#A7BAB7` | drift |
| faint text | `ink3` `#647C7B` | `--cp-faint` `#78928F` | drift |
| primary accent | `cyan` `#4CC6D4` | `--cp-cyan` `#55C9D4` | drift |
| warning accent | `molten` `#EDA93C` | `--cp-gold` `#EFAD43` | drift |
| success accent | `jade` `#46C08A` | `--cp-jade` `#4EC28D` | drift |
| danger accent | `ember` `#EF6A50` | `--cp-coral` `#EF7259` | drift |
| info accent | `info` `#6BA8E8` | `--cp-blue` `#72AAE7` | drift |
| special accent | `iris` `#9E8BEE` | `--cp-iris` `#A594EC` | drift |
| hot warning | `molten-hot` `#FFC44D` | *(none)* | D0-only |

**Fonts:** D0 = Space Grotesk (display) / IBM Plex Sans (body) / IBM Plex Mono (mono).
Prototype = `--font-geist-sans` / `--font-geist-mono`. **Converge on D0 fonts.**

**Rebase mechanic (token step):** repoint each `--cp-*` declaration at the matching D0
`@theme` token (or delete `--cp-*` and swap class colors to D0 Tailwind utilities). This one
mechanical pass unifies color + type across the whole surface with no workflow change.

---

## 3. §B — Status-vocabulary reconciliation

`Primitives.tsx` `StatusPill` maps **14** flat statuses onto 6 color tones and renders
**color + text but no icon** — weaker than blueprint §16.4 (icon + text) and the D0.2
`LifecycleBadge` invariant. The 14 statuses also mix four different axes. They must sort onto
the correct canonical axis; **new canonical state names are owned by BE/KE against
`ontowiz-spec`, never invented by FE** (blueprint invariant #5, §5 line 160).

| StatusPill status | Prototype tone | Canonical home | Axis | Action |
|---|---|---|---|---|
| `passed` | good | `pass` | gate outcome | maps → D0.2 |
| `failed` | danger | `fail` | gate outcome | maps → D0.2 |
| `rejected` | danger | `rejected` | delta status | maps → D0.2 |
| `review_required` | warning | `review` | lifecycle | maps → D0.2 (label override) |
| `at_risk` | warning | `warn` / health | health | maps → D0.2 or HealthPill |
| `current` / `released` | good | `active` | release | maps → ReleaseBadge |
| `superseded` | neutral | `deprecated` | lifecycle | maps → D0.2 (or new) |
| `candidate` | info | **new** `candidate` | release | ★ ratify (BE/KE) |
| `building` | info | **new** `building`/`running` | job | ★ ratify (job axis) |
| `blocked_pending_review` | danger | **new** `blocked` | gate/release | ★ ratify |
| `stale` | danger | **new** `stale` / `stale_critical` | staleness | ★ ratify (Slice F core) |
| `quarantined` | iris | **new** `quarantined` | source safety | ★ ratify (Slice C) |
| `healthy` | good | **new** `healthy` | health | ★ ratify (health axis) |

Blueprint §16.11 also names label-qualifiers not in `StatusPill`: `withdrawn`,
`demo released`, `production released`, `provisional`, `synthetic`, `reference`,
`internal eval`, `not measured`. These are release/qualifier states on the same axes.

**Conclusion:** the canonical `LifecycleBadge` (13 states: artifact-lifecycle + delta-status
+ gate-outcome) stays the home for those three axes. The control plane needs **sibling
status components on orthogonal axes** — a job's `running` is not an artifact's `active`.
See D0.10 in §D. Each is icon + label, never color-only.

---

## 4. §C — Pattern → component map

Every major `control-plane.module.css` pattern mapped to the D0 component that should own it.
"Existing" = already in the D0 plan; "NEW" = a D0 gap this exercise surfaced (see §D).

| Prototype pattern (module.css / Primitives) | D0 owner | Status |
|---|---|---|
| `statusPill` / `tone_*` | LifecycleBadge + status siblings | D0.2 + **D0.10** |
| `primaryButton`/`secondaryButton`/`textButton`/`runButton` | Button | D0.4 |
| `globalSearch`/`catalogSearch`, `selectWrap`/`roleSelect`, `promptField` | Input / Select / Textarea | D0.4 |
| `segmentedControl`, `filterRail` | Tabs / SegmentedControl | D0.4 |
| `toolSurface`/`surfaceHeader`, `sectionTitle`/`eyebrow` | Card / SectionHeader | D0.4 |
| `correctionPanel`/`approvalReceipt`/`actionReceipt`/`deltaCreated` | ConfirmSheet + receipts | D0.5 |
| `scenarioRail`/`scenarioButton`, phone-stacked lists | CardStack | D0.6 |
| `inspector`/`inspectorSection`/`workbenchGrid` detail pane | Drawer / detail pane | D0.7 |
| `expectedActual`, `releaseDiff`, `diffLists` | DiffView (semantic diff) | D0.8 |
| `relationshipList`, hierarchy/reparent | Tree | D0.9 |
| `topbar`/`sidebar`/`navigation`/`navItem` | App Shell | D1.1 |
| `statBand`/stat tiles, `extractionSummary`, `evalHeroMeta` | StatTile / MetricTile | **D0.11** |
| `coverageTrack`/`confidenceRow`/`evalSegments` | Meter / ProgressBar | **D0.11** |
| `scoreRingPassed`/`scoreRingFailed` | ScoreRing / Gauge | **D0.11** |
| `emptyState`/`simEmptyState`/`loadingInline`/`apiState` | Empty / Loading / Denied / Partial states | **D0.12** |
| `blockerBanner`/`readyBanner`/`errorBanner`/`hardRuleCallout`/`simulatorBoundary` | Banner / Callout / Alert (tone family) | **D0.12** |
| `catalogTable`(`catalogHeader`/`catalogRow`/`Active`), `matrixRow`, `caseList`, `consumerTable`, `sourceRow` | DataTable (master-detail, sticky header, active row) | **D0.13** |
| `evidenceBlock` (blockquote + source code + locator), `receiptStrip` | EvidenceBlock (wraps D0.3 ProvenanceChip) | **D0.14** |
| `documentPreview`/`highlightSpan` | SourceViewer (highlighted span) | **D0.14** |
| `lineageList`/`traceTimeline` (connector timeline) | Timeline / LineageTrail | **D0.14** |
| `flowBand`/`flowStep`/`flowArrow` (product-loop stepper) | FlowStepper | **D0.12** (or compose) |
| `gateChecklist`/`layerManifest` | GatePanel | compose in Slice G feature unit |
| `comparisonGrid`/`governedResult`/`baselineResult` | ComparisonPanel (diagnostic-labeled) | compose in Slice H feature unit |
| `traceArtifacts` (artifact-ref chips) | chips (Provenance/Layer) | D0.3 |

---

## 5. §D — Proposed D0 backlog reshape

The prototype proves D0 was under-scoped for the full product. The existing D0.1–D0.9 + D1.1
remain correct; this adds a small, clustered set of new units. **INT assigns real IDs and
Loop placement**; each is ≤ one person-week and independently reviewable.

**Confirmed (existing plan) — scope validated against the prototype:**
- **D0.4 Primitives** — Button, Input, Select, Textarea, Card, SectionHeader, Tabs/Segmented.
- **D0.5 ConfirmSheet** — absorbs the correction/approval receipt-confirm flow (AC-03/04).
- **D0.6 CardStack** · **D0.7 Drawer** · **D0.8 DiffView** (fits `expectedActual`/`releaseDiff`) ·
  **D0.9 Tree** · **D1.1 App Shell** (fits `topbar`/`sidebar`/`nav`).

**Proposed new units (clustered; sourced from the prototype + blueprint §16/§17):**
- **D0.10 Status axes** — `ReleaseBadge`, `StalenessBadge`, `JobStatus`, `HealthPill` as
  icon+label siblings to `LifecycleBadge`, on BE/KE-ratified canonical vocab (§B). Retires
  `StatusPill`. *Loop 0 — everything renders status.*
- **D0.11 Data surfaces** — `StatTile`/`MetricTile` (carrying definition · denominator ·
  clock · data-status, per blueprint §9 and the `not measured` rule), `Meter`/`ProgressBar`,
  `ScoreRing`. *Loop 0 — the dashboard/eval spine.*
- **D0.12 State & feedback family** — `Empty`/`Loading`/`Denied`/`Partial`/`Stale`/`Retry`/
  `Conflict` states + `Banner`/`Callout`/`Alert` tone family (blueprint §16.7). *Loop 0 — the
  honest-operational-states requirement touches every view.*
- **D0.13 DataTable** — master-detail catalog table (sticky header, active row, ellipsis,
  keyboard rows, bounded scroll). *Pull in with Slice C (Knowledge/Source) — its first
  consumer.* May split into table + master-detail layout.
- **D0.14 Evidence & lineage** — `EvidenceBlock` (provenance blockquote over D0.3
  `ProvenanceChip`), `SourceViewer` (highlighted span), `Timeline`/`LineageTrail`. *Pull in
  with Slice C.*

`GatePanel` (Slice G) and `ComparisonPanel` (Slice H) compose from the above and live with
their feature units rather than as standalone D0 units.

---

## 6. §E — The rebase approach (D1.2-era)

Blueprint §5 line 161: rebase **incrementally onto reviewed tokens/primitives without changing
the proven workflow.** The prototype's existing tests and 390×844 geometry audit are the
regression guard: the **only** intended visual change is the token/font unification approved
in §1.

Ordered, each step its own committed mini-spec + immutable review SHA (per blueprint §18):

1. **Tokens & fonts (unblocked, cheap, high-leverage).** Apply §A: repoint `--cp-*` at D0
   `@theme` tokens; swap Geist → D0 fonts. Zero workflow change; instant unification. Can land
   as an early D0↔control-plane bridge unit before the data slices, once INT schedules it.
2. **Leaf primitives.** Replace `StatusPill` → `LifecycleBadge`/D0.10; buttons/inputs/selects
   /tabs → D0.4; banners/empty/loading → D0.12; tiles/meters/rings → D0.11.
3. **Composite patterns.** Tables → D0.13; evidence/source/lineage → D0.14; diffs → D0.8.
4. **Retire `control-plane.module.css`** as its classes reach zero references; add the shipped
   feature paths to the ≥85% blocking coverage include (blueprint §5 line 158).

**Guardrails:** no visual change beyond §1; the prototype's workflow, deep-links, and state
machine are untouched; data-bearing views (steps 2–3 where they read fields) wait on F0.3A's
generated client and never hand-write endpoint/response types (blueprint §11, R11).

---

## 7. §F — Boundaries and ownership

- **FE (me):** this plan; the D0 component library (D0.4→D0.14) via the normal per-unit loop;
  authoring the rebase mini-specs when INT schedules D1.2.
- **INT:** assigns new-unit IDs and Loop placement; sequences Slice A (freeze the prototype as
  an immutable reference SHA — it is currently unfrozen in the tree); owns merge order.
- **BE/KE:** ratify the new canonical status names in §B against `ontowiz-spec`; own the
  F0.3A contract the data-bearing rebase steps consume.
- **REV:** read-only verdict per unit.

**Non-goals of this document:** it does not modify any prototype file, build control-plane
views, freeze the reference SHA, or start the rebase. No implementation follows from this plan
alone (blueprint §1).

---

## 8. §G — Open decisions requested from INT / BE / KE

1. **New canonical status names (§B ★ rows)** — BE/KE to ratify `candidate`, `building`/
   `running`, `blocked`, `stale`/`stale_critical`, `quarantined`, `healthy`, `withdrawn`
   against `ontowiz-spec`, so D0.10 renders sourced (not invented) vocabulary.
2. **New D0 unit IDs + Loop placement (§D)** — confirm D0.10–D0.12 as Loop-0 foundational and
   D0.13–D0.14 as deferred-to-Slice-C; assign IDs in the backlog dependency graph.
3. **Early token-bridge unit (§E step 1)** — approve landing the token/font unification as an
   early standalone unit (cheap, unblocked) vs folding it into the full D1.2 rebase.
4. **Slice A ownership** — confirm INT freezes the control-plane prototype reference SHA before
   any rebase begins, so the "proven workflow" has a fixed baseline to preserve against.
