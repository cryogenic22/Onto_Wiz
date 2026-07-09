# Onto_Wiz — UX/UI Plan: The Domain Knowledge Factory

**Companion to:** STRATEGIC_REVIEW_2026-07.md · **Audience:** the build team · **Scope:** internal ZS tool for the next 6 months

---

## 1. What this plan is for

The strategic review found that Onto_Wiz has a sound governed engine and a polished but orphaned front end: the SME game and curator console run against an unauthenticated legacy backend whose approvals evaporate on restart, the catalogue runs against the deployed backend but isn't linked from navigation, there is no ontology browsing or mapping surface at all (reactflow is installed and never imported), and no screen anywhere lets anyone create or edit an ontology object directly. Meanwhile the content that exists was Claude-drafted and awaits SME validation — which means the UX's real job is to make **SME validation and codification cheap, attributable and continuous**.

This plan designs the tool as what it actually needs to be: a **Domain Knowledge Factory** — one application where SMEs codify judgment, curators govern and map it into layered ontology assets, and the output is compiled, eval-gated packs that agents consume via REST/MCP. Creation and management of organisation ontologies *is* the experience — but scoped to the judgment-layer product that works, not a generic Protégé competitor.

---

## 2. Users and their jobs

**Domain SME** (pharma commercial, market access, oncology…). Job: get what's in my head into the system in minutes, see it respected (attribution, impact), never touch YAML. Secondary job: validate candidates the machine proposes from documents.

**Ontology Curator** (knowledge engineer / senior consultant). Job: govern the corpus — review deltas, resolve conflicts, maintain the layer structure, map concepts across domains and to external standards, decide what compiles into which pack. The curator is the power user; most new UI surface in this plan is theirs.

**Engine / agent builder** (consumer, not editor). Job: find the right pack, trust it (lift receipt, governance trail), wire it in via MCP. Served by the existing catalogue, upgraded, read-only.

One app, one login (the existing JWT/RBAC in ontowiz-serve), role-shaped navigation. The hardcoded `'curator'` identity dies; every action is attributed to a named principal — this is a UX feature, not just security: attribution is what makes SME contribution visible and valued.

---

## 3. The layer model the UI must make tangible

The repo already implies a layered ontology; the UI's core idea is to make those layers first-class, visible, and individually manageable. Six layers, mapped to what exists:

| Layer | What it is | Exists today as |
|---|---|---|
| **L0 Domain hierarchy** | A *tree*, not a flat list: domains → subdomains → (optionally) sub-subdomains, plus cross-domain edges and the standards glossary. E.g. Commercial → Field Force, Marketing & Omnichannel, Payer/Access interface, Patient Services, Analytics & Insights. Every other layer's objects attach to a node at any depth. | ontology/ARCHITECTURE.yaml (flat today — needs a `parent` field; small schema change, big UX change) |
| **L1 Entities & taxonomy** | Entity types, hierarchies, synonyms per domain | commercial.yaml entities, domain files |
| **L2 Relationships** | Typed edges within and across domains | commercial.yaml relationships, cross-domain edges |
| **L3 Judgment rules** | Priority-ordered inference/triage rules with anti-patterns and confidence modifiers — the product's heart | 20 commercial + 4 forecasting rules |
| **L4 Signals & metrics** | Metrics with signal roles that rules consume | metrics.yaml (16 metrics) |
| **L5 Scenarios & evals** | Gold cases and eval suites that make every layer falsifiable | compellium gold set, scenario files, eval suite |

Above the layers sits the **Pack** — a versioned, governed compilation of selected layers for an agent audience, with client **overlays** layered on a base pack.

Every object in every layer carries the same governance chrome: lifecycle badge (DRAFT → PROPOSED → APPROVED → ACTIVE → DEPRECATED), SME attribution (or "unvalidated — Claude-drafted", surfaced honestly), provenance (source document / capture session), and eval linkage. This uniform chrome is the single most important visual pattern in the product: it makes governance ambient rather than a separate screen.

---

## 4. Information architecture

One Next.js app, one API client, one auth. Six areas in a left sidebar (role-filtered):

1. **Home / Domain Dashboard** — the state of the corpus, per domain.
2. **Capture** — SME-facing codification (guided sessions + document intake).
3. **Curation Queue** — the governed inbox: review, edit, approve, escalate.
4. **Ontology Workspace** — browse and edit the six layers; graph view; the Mapping Workbench.
5. **Packs & Releases** — compile, gate, version, diff, publish, consume (MCP).
6. **Admin** — people, roles, domains. (Thin; last.)

Global elements: an omnisearch (⌘K) across all layers and packs; a persistent "pending review" counter for curators; every entity/rule/pack anywhere in the app is a link to its detail drawer — the current dead-end split (delta under review not linked to the artifact it changes) is abolished by convention.

---

## 5. Screen-by-screen specification

### 5.1 Domain Dashboard (Home)

*Primary user: curator; SMEs see a simplified version.*

The question this screen answers: **where is the corpus strong, weak, stale, and unvalidated?**

- **Stat row** (four tiles): active artifacts; % SME-validated (the honesty metric — starts low and that's the point); pending deltas (median age); current pack eval status (gate passed / lift number / "unmeasured" in warning state).
- **Domain coverage board**: one row per domain (from the L0 hierarchy), expandable into subdomain rows with coverage rolled up to the parent, with per-layer depth indicators — entities / relationships / rules / metrics / evals as five small horizontal bars (single-hue sequential; no rainbow). Today this instantly shows commercial as deep and the other eight domains as taxonomy stubs — which is exactly the prioritisation conversation the team should be having on this screen.
- **Attention feed**: rules with zero linked eval cases; artifacts stuck in PROPOSED > 7 days; anti-pattern conflicts; standards drift (e.g. new MedDRA version).
- **Recent activity** with named principals ("Priya approved DELTA-142 → recompile queued").

### 5.2 Capture (SME)

Two doors, one destination — everything lands as PROPOSED deltas in the queue.

**A. Guided session** (evolve the existing Situation Room — keep its 9-step spine, it is genuinely good UX):
- Replace hardcoded scenario/hypothesis/signal content with data served from L4/L5 — content-driven, not code-driven, so new domains need no frontend release.
- End-of-session summary shows *the actual deltas generated*, in plain language ("You proposed: raise priority of safety-signal triage above competitive when clinical inquiries co-occur"), with an edit affordance before submitting — SMEs must see and own what they said.
- Session provenance is stamped on every resulting delta.

**B. Document intake** (the LLM mining path — new):
- Drag in decks, transcripts, SOPs (parsers exist in src/knowledge; port them). Claude proposes candidate rules *and paired eval cases* into a "candidates" tray.
- The SME's job is triage, not authoring: each candidate is a card with the extracted rule, its source snippet (always visible — provenance is trust), and three actions: *looks right* (→ PROPOSED with SME endorsement), *fix it* (inline structured edit — never raw YAML), *wrong* (with a one-tap reason, which becomes training signal).
- Hard rule from the review: **the machine proposes, only humans promote.** The UI must make auto-promotion impossible by construction, not by policy.

**C. Quick capture** (one form, 60 seconds): "When [condition], then [judgment], because [rationale], watch out for [anti-pattern]" — a structured sentence-builder that maps 1:1 onto the L3 rule schema. This is the lowest-friction door and likely the highest-volume one.

### 5.3 Curation Queue

*The curator's inbox — upgrade of the existing CuratorDashboard, which has the right bones.*

- Queue with filters (domain, layer, source: session/mined/manual, age, SME).
- **Delta detail drawer**, three panes: (1) the proposed change as a human-readable diff against the current artifact — never raw YAML as the primary view, YAML available behind a tab; (2) context: the affected artifact with its full governance chrome, *linked*, plus any conflicting rules (same tags, adjacent priorities) surfaced automatically; (3) evidence: source snippet / session transcript excerpt, linked eval cases, and an on-demand "dry-run" showing which gold-set accounts this rule would fire on (the engine can already answer this — expose it).
- Actions: approve / reject (reason required) / escalate / **edit-and-resubmit** (structured editor, the change tracked as the curator's amendment on the SME's proposal — dual attribution).
- **Approve triggers the loop visibly**: a toast + queue entry "recompiling commercial_analytics 0.4.0-rc → running 31 evals" that resolves to pass/fail. The compile-on-approve pipeline is the product's magic moment; the UI must let the curator *watch the flywheel turn*.

### 5.4 Ontology Workspace

*The new surface — the "manage ontologies and domain layers" heart of your ask. Curator-primary.*

**Layout:** left rail = the **domain hierarchy tree** (domains → subdomains, expandable) with the layer tree (L0–L5) scoped to the selected node; centre = the selected layer's view; right = detail drawer for the selected object.

- **Hierarchy as a first-class managed object.** Selecting any node scopes everything — the layer browser, graph, mappings and coverage all show that node's slice, with roll-up from children (Commercial's rule count is its own plus Field's plus Marketing's…). A "Manage hierarchy" mode lets curators add, rename, move, merge and deprecate subdomains — and, critically, **reparent objects** (move a rule from Commercial down to Field Force when it turns out to be field-specific). Every hierarchy change is itself a delta through the governed pipe, because moving a subdomain silently changes what compiles into which pack — that must be reviewable, attributed and reversible like any other change.
- **Inheritance with visible provenance:** a subdomain inherits its ancestors' entities, relationships and rules unless overridden; inherited objects render with an "inherited from Commercial" chip so curators always know what is local versus rolled-down. Overrides at a lower node are the intra-organisation analogue of client overlays — same mental model, same diff UI.
- **Scope-aware capture:** SME capture asks (or infers from the SME's profile) which node judgment belongs to; mined candidates get a proposed node the curator can re-scope in review.

- **Layer browser**: each layer gets a purpose-built list/table view (entities with synonym counts; relationships as subject–predicate–object rows; rules ordered by priority with tag chips and anti-pattern badges; metrics with signal-role tags; scenarios with linked-rule coverage). Inline lifecycle badges and validation state everywhere.
- **Structured editors, not YAML**: every layer object has a form-based editor whose fields mirror the ontowiz-spec schema. Saving as a curator does not write directly — it generates a delta through the same governance pipe (curators self-approve with a second-glance confirm; the audit trail stays uniform). One pipe, no back doors.
- **Graph view** (finally use reactflow): domain-scoped node-link view, entities as nodes, relationships as edges, rules attachable as badges on the edges/nodes they govern. Read-first in phase 2 (navigate, inspect, filter by layer/tag); edit-in-graph (draw an edge → creates a PROPOSED relationship delta) in phase 3. Resist the temptation to make the graph the primary editor — it is a *comprehension* surface; tables edit faster.
- **Mapping Workbench** — the "enable mapping of ontologies" requirement, four mapping types, one consistent side-by-side UI (left: source concept list, right: target, centre: typed link with confidence + rationale, every mapping a governed artifact):
  1. **Synonym & merge mapping** (within a domain): dedupe entities, bind synonyms — the hygiene loop.
  2. **Cross-domain mapping**: link concepts across domains *at any hierarchy level* (commercial "payer" ↔ market_access "payer archetype"; Field Force "call plan" ↔ Marketing "next-best-action") — this is what makes it an *organisation* ontology rather than a set of silos, and it feeds agent traversal.
  3. **Standards mapping**: bind internal concepts to the external glossary already in ARCHITECTURE.yaml (SNOMED, MedDRA, ATC, CDISC, GS1…) — the enterprise-credibility layer, and the answer when a client asks "how does this align to our MDM?"
  4. **Base ↔ overlay mapping**: show which base-pack artifacts a client overlay overrides/extends/suppresses, as a three-column diff. This is how one base pack serves many clients without forking.
- **Lineage tab** on every object: where it came from (session/document/import), every delta that touched it, every pack version that shipped it, every eval that exercises it. Lineage is the anti-"black box" answer for agentic AI governance.

### 5.5 Packs & Releases

*Upgrade of the existing catalogue; serves curators (publish) and agent builders (consume).*

- **Pack composer**: choose hierarchy node(s) (a whole domain, or just Field Force + Marketing), layers, and scope filters → assemble a pack manifest. Shows a live "what's in / what's excluded and why" (e.g. "3 rules excluded: not ACTIVE"). Overlays composed the same way, on a base.
- **Release gate panel**: eval results per version, with the hard rule made visible — *a pack that fails its gate cannot be published, and the button literally isn't there.* Show lift receipts (with/without protocol, case counts, SME-authored held-out count) as the version's headline. The 0.3.0 regression becomes structurally impossible *and visibly impossible*.
- **Version diff**: artifact-level diff between any two versions — added/changed/retired rules, eval delta.
- **Consume tab**: MCP endpoint, REST snippets, token-footprint note per function slice (already exists — keep), and a "try it" console that runs context/get against the pack live.

### 5.6 Admin
Users, roles (SME / curator / consumer / admin), domain ownership assignments. Deliberately thin — build last, seed via CLI until then.

---

## 6. Design principles and system

**Principles** (each traces to a review finding):
1. **Governance is ambient, not a module** — the lifecycle/attribution/provenance chrome on every object, every screen.
2. **Evidence-first** — no claim without its receipt: rules show their eval coverage, packs show their lift, "unvalidated" states are shown honestly rather than hidden. The UI should make an unvalidated corpus *feel* unfinished — that pressure is the product working.
3. **SMEs never see YAML; curators may, but never need it.** Structured editors mirror the spec schema.
4. **One pipe** — every mutation from every surface is a delta through the same governed queue. No back doors, including for curators and the mining engine.
5. **Show the flywheel** — approve → recompile → eval → new version must be observable as one continuous animation of cause and effect. This is the retention mechanic for curators and the trust mechanic for stakeholders.
6. **Content-driven UI** — scenarios, hypotheses, signals, domains all served from the ontology itself; adding a domain never needs a frontend release.

**Design system:** keep the existing dark-slate Tailwind foundation and the seven unused ui/ primitives (Button, Card, Modal…) — adopt them instead of deleting. Add: lifecycle badge set (five states, colour + icon + label, never colour alone), attribution chip (avatar + name + role), provenance chip (source icon + link), layer icons (L0–L5), diff view component, and the side-by-side mapping component. Charts follow the dataviz rules already applied in the prototype: single-hue sequential bars for coverage, reserved status colours for gate/eval states (icon + label, never colour alone), stat tiles for headlines, no dual axes, no rainbow.

---

## 7. Build order (solo dev, mapped to the 3-month plan)

**Phase 1 — Unify (aligns to Month 1–2 of the strategic plan).** One backend, one auth, one nav. Rewire game + curator to ontowiz-serve; named principals; persistent deltas; catalogue linked into nav; delta→artifact linking in the queue; compile-on-approve with visible pipeline state. *No new surfaces yet — this phase makes the existing ones true.*

**Phase 2 — Codify & curate (Month 2–3).** Quick-capture form; document intake with candidate triage tray; curation drawer upgrade (diff view, conflict surfacing, dry-run, edit-and-resubmit); Ontology Workspace v1 = hierarchical domain tree (add `parent` to the L0 schema) + layer browser + structured rule/entity editors + lineage tab. Hierarchy *management* (move/merge/reparent as governed deltas) lands late in this phase; inheritance/override rendering in Phase 3. *This is the phase that serves the SME pilot — sequence it so capture + queue land before the pilot starts.*

**Phase 3 — Map & visualise (Month 3+).** Mapping Workbench (synonyms first, then cross-domain, then standards, then overlays — in that order, matching data readiness); reactflow graph view (read-only); pack composer + release gate panel; version diff.

**Phase 4 — Later.** Edit-in-graph; Forge missions/consensus UI (route mined candidates through the existing submit contracts first — the game UI only if pilot SMEs ask for it); client-facing multi-tenant skin.

**Explicitly not building:** a generic ontology editor for arbitrary schemas; OWL/RDF round-tripping; marketplace features beyond one catalogue; anything client-branded — all deferred behind pilot evidence.

---

## 8. Success measures for the UX

Time-to-first-delta for a new SME (target: < 10 minutes from login); quick-capture completion rate; candidate-triage throughput (candidates/SME-hour); % of corpus SME-validated (the strategic north star, on the dashboard); median delta review latency; approvals per recompile cycle; and — the one that proves the whole thesis — SME return rate in week 2 of the pilot.
