# Deep UX Research: Dual-Persona Enterprise Application Design

## 1. Persona-Specific Entry Points

### How Major Platforms Split Experiences

**Salesforce: Admin vs. End-User**

Salesforce uses **dedicated Lightning Apps per persona** as its primary routing mechanism. Each user group gets its own app container with a curated set of tabs, navigation items, and a custom homepage. The architecture works in three layers:

- **App-level routing**: Admins create separate Lightning Apps (e.g., "Sales Console," "Service Console," "Admin Hub"). Each app exposes different object tabs, utility bars, and home pages. Users are assigned to apps via profiles and permission sets.
- **Page-level personalization**: Lightning Pages are assigned to specific apps, meaning the homepage an admin sees is structurally different from what a sales rep sees -- different components, different data density, different action buttons.
- **Navigation bar customization**: End-users can personalize their nav tabs within the boundaries set by admins, creating a negotiated space between admin-defined structure and user autonomy.

The key pattern: **the platform routes at the container level, not the page level**. You don't show the same dashboard with different widgets; you route to entirely different app shells.

**Shopify: Merchant vs. Customer**

Shopify implements the most aggressive separation of any platform studied: **two completely separate design systems** for two completely separate interfaces.

- **Merchant side**: Uses **Polaris** (Shopify's admin design system) with App Bridge for embedded apps. The admin is a configuration-heavy, data-dense environment. Third-party apps embed via iframe and must conform to Polaris to maintain trust.
- **Customer side**: Uses the **storefront theme system** with a 12-column responsive grid, customer account extensions, and server-driven UI for personalization. The customer never sees Polaris components.
- **The bridge**: Merchants configure what customers see. The UX principle is "merchants configure, customers consume." Server-driven UI architecture enables merchant stores to be personalized through templated layouts that render sections needed by each merchant.

**Figma: Designer vs. Developer**

Figma's approach is the most instructive for a shared-platform scenario because both personas work in the **same file** but see it differently:

- **Dev Mode** is a dedicated view toggle that transforms the same canvas into an inspection-oriented interface. Designers see layers, properties, and design tools; developers see CSS values, spacing measurements, component specifications, and Code Connect snippets.
- **Component Playground** lets developers view all possible component variations and get implementation code, while designers see the same components as drag-and-drop building blocks.
- **Shared naming conventions** serve as the translation layer: a "button" in Figma corresponds directly to a "button" in the code repository. The design token system (variables) provides corresponding code syntaxes.

The key pattern: **same underlying artifact, different interaction modes accessed via a view toggle**.

**Notion: Builder vs. Viewer**

Notion uses **permission-gated progressive disclosure**:

- Builders (editors) see the block manipulation UI, slash commands, database configuration, relation/rollup setup, and formula editing.
- Viewers see clean, rendered content with no editing affordances. The entire block manipulation layer disappears.
- The permission system controls which UI layer is active, not which content is visible.

### Architectural Recommendation

For a dual-persona platform, the pattern hierarchy from most to least separation is:

1. **Separate apps with separate design systems** (Shopify model) -- highest development cost, cleanest UX
2. **Separate app shells with shared component library** (Salesforce model) -- moderate cost, good persona alignment
3. **View mode toggle within shared workspace** (Figma model) -- lowest cost, best for shared artifacts
4. **Permission-gated progressive disclosure** (Notion model) -- lowest cost, but risks "leaky" abstraction

---

## 2. The "Duolingo Meets Bloomberg Terminal" Paradox

### How Products Serve Both Playful and Powerful

**Slack: Fun Surface, Deep Engine**

Slack's dual-nature was intentional from day one. When MetaLab designed the original app, the goal was explicit: at a time when business applications were dull and boring, they wanted Slack to stand out. The mechanisms:

- **Micro-interactions as personality layer**: The logo animates in a burst of color as it loads, modals slide down, elements "playfully jump around and pop off the screen." These are cosmetic -- they don't affect functionality.
- **Copy as delight vector**: Every piece of copy is treated as an opportunity to be playful. Slackbot acts as a "wise-cracking robot sidekick." Loading screens and error messages inject fun.
- **Power hidden behind progressive triggers**: The 2023 redesign moved the Compose button to include a lightning bolt icon that unlocks shortcuts, integrations, and workflow tools. New users see a simple message field; power users discover the integration layer.
- **Slack Kit design system**: Built as a "gradual design system" -- it evolved organically from rapid growth code into a consistent system. The key insight: consistency enables playfulness because users develop trust in patterns, which creates space for delightful surprises.

The architecture: **delight lives in the interaction layer (animations, copy, emoji), power lives in the integration layer (workflows, bots, APIs). They share components but occupy different depths.**

**Spotify: Simple Player, Complex System**

Spotify's approach uses **Encore**, a family of design systems rather than a single monolithic one:

- **Global Encore**: Shared tokens, typography scales, spacing rules, and core components used everywhere.
- **Local design systems**: Product-specific systems (e.g., Spotify for Artists has its own navigation patterns and table layouts) that extend Encore with audience-specific components.
- The simple player interface and the complex library management interface share Encore's foundation but use different local component sets.

Before Encore, Spotify had 22 disconnected design systems. The consolidation preserved persona-specific expression while creating shared infrastructure.

**Apple: Three-Layer UX Philosophy**

The helloSystem project (modeled on early Mac OS X) articulated what Apple practiced but never named -- a **three-layer UX model**:

1. **Surface layer**: Clean, minimal, immediately usable by anyone. High-level controls, large targets, limited options.
2. **Preference layer**: System Preferences / Settings -- moderate complexity, organized by domain, accessible to interested users.
3. **Deep layer**: Terminal, system configuration files, developer tools -- full power, no guardrails, explicitly "under the hood."

Each layer has progressively more information density, smaller UI elements, and less visual warmth. The critical design principle: **each layer is self-contained and complete for its audience**. A casual user never needs to visit the deep layer; a power user can live there.

### Design System Architecture for the Paradox

The enabling pattern is **semantic token aliasing with persona-specific expression**:

```
Foundation tokens (shared):
  spacing-unit: 8px
  border-radius-base: 4px
  font-family-body: "Inter"

Persona expression "warm" (SME/casual):
  surface-primary: warm-gray-50      (lighter, warmer)
  border-radius-card: 12px           (rounder)
  font-size-body: 16px               (larger)
  animation-duration-feedback: 400ms  (more "juicy")
  illustration-style: enabled

Persona expression "precise" (curator/power):
  surface-primary: cool-gray-100     (denser, cooler)
  border-radius-card: 4px            (sharper)
  font-size-body: 14px               (denser)
  animation-duration-feedback: 150ms  (snappier)
  illustration-style: disabled
```

The same `<Card>` component renders differently under each expression, but the layout grid, interaction patterns, and accessibility standards remain identical.

---

## 3. Pharma/Healthcare Dual UX Precedents

### Clinical Trial Platform Patterns

**Veeva Vault EDC**

Veeva represents the most modern approach to the dual-persona problem in clinical trials:

- **Personalized dashboards with role-based interfaces**: Site personnel (clinical practitioners) see patient visit schedules, form completion status, and query resolution workflows. Data managers see cross-site data quality metrics, edit check results, and coding tables.
- **No-code configurability**: Teams can adapt the software to their internal SOPs without coding, meaning the "admin" persona can reshape the "practitioner" experience.
- **Protocol amendment without downtime**: The system architecture allows study modifications without database downtime, critical for adaptive trial designs. This is a lesson in how the data layer must support persona-specific views without structural rigidity.

**Medidata Rave EDC**

Medidata's approach is more traditional but reveals important patterns:

- **Drag-and-drop study design** eliminates programming for clinical teams (practitioner-friendly), while the underlying data model supports complex edit checks and derivations (data manager-friendly).
- **Ease of use score of 9.5 on G2** for the site-facing interface, despite enormous backend complexity. The key: the practitioner interface is form-centric (fill in patient data), while the data manager interface is table-centric (review, clean, query across patients).
- **Legacy integration challenge**: Medidata historically had siloed systems requiring physical integrations between modules. This created UX fragmentation -- a cautionary tale about letting backend architecture leak into frontend persona separation.

**Oracle Argus Safety (Pharmacovigilance)**

- Handles high-volume case processing with role-based workflows: safety officers see case narratives and assessment forms; data entry staff see structured data capture screens; regulatory teams see submission-ready CIOMS and MedWatch forms.
- Same adverse event data, three completely different presentations.

**Key Pattern from Healthcare**: The clinical domain universally uses **form-based interfaces for practitioners** (who think in patient encounters) and **table/grid-based interfaces for data managers** (who think in datasets). The same data record appears as a form in one view and a row in another. This is not progressive disclosure -- it is **structural reformatting** of the same information.

### Healthcare-Specific Lessons

1. **Regulatory compliance forces role separation**: In clinical trials, audit trails must show who did what. This means role-based interfaces are not optional -- they are required by regulation (21 CFR Part 11, GxP).
2. **"Source of truth" must be role-agnostic**: The underlying data model cannot be biased toward either persona's view. Both the form view and the table view must be projections of a neutral canonical model.
3. **Workflow state machines drive persona routing**: A case in "data entry" state shows the data entry interface; the same case in "medical review" state shows the medical reviewer interface. The persona-specific experience is driven by workflow state, not just user role.

---

## 4. Design System Architecture for Dual Personas

### Three-Tier Token Architecture

Based on research into SAP's Digital Design System, Contentful's design token documentation, and multi-brand design system implementations, the recommended architecture is:

**Tier 1 -- Global/Foundation Tokens (Shared, immutable)**
```
color-blue-500: #2563EB
spacing-4: 16px
font-weight-bold: 700
shadow-elevation-2: 0 4px 6px rgba(0,0,0,0.1)
breakpoint-md: 768px
```

**Tier 2 -- Semantic Tokens (Shared meaning, persona-variable values)**
```
// "Warm" persona (SME/casual)
color-action-primary: color-teal-400
color-surface-card: color-warm-gray-50
radius-container: 16px
motion-feedback: 400ms ease-out
typography-heading: 24px/1.3 "Nunito"

// "Precise" persona (curator/power)
color-action-primary: color-blue-600
color-surface-card: color-cool-gray-25
radius-container: 4px
motion-feedback: 120ms ease-in-out
typography-heading: 18px/1.4 "IBM Plex Sans"
```

**Tier 3 -- Component Tokens (Persona-specific component behavior)**
```
// Warm persona
card-padding: spacing-6
card-illustration: visible
card-metric-style: large-centered
progress-bar-style: animated-gradient
notification-style: toast-with-emoji

// Precise persona
card-padding: spacing-3
card-illustration: hidden
card-metric-style: inline-tabular
progress-bar-style: static-bar
notification-style: inline-banner-with-id
```

### Component Variant Strategy

Instead of building separate components, build **one component with persona-driven variant selection**:

```typescript
// Pseudo-code for a shared ResultCard component
<ResultCard
  variant={persona === 'sme' ? 'achievement' : 'artifact'}
  data={deltaRecord}
/>

// "achievement" variant: large icon, congratulatory copy,
//   progress ring, simplified metrics
// "artifact" variant: compact layout, full metadata,
//   status badge, blast radius indicator, review actions
```

The component consumes the same props/data but renders through different internal templates selected by the persona context. This is how Spotify's Encore handles product-specific variations within a shared system.

### Tools for Implementation

- **Style Dictionary** or **Tokens Studio**: Transform design tokens across platforms (CSS custom properties, iOS, Android)
- **Figma Variables with Modes**: Define "Warm" and "Precise" as variable modes; components switch appearance automatically when the mode changes
- **Theme Provider pattern**: React/CSS context that injects persona-specific token values at the application shell level

---

## 5. Information Architecture for Shared Data

### The Content Projection Pattern

The core architectural pattern is **CQRS (Command Query Responsibility Segregation) with persona-specific read model projections**. This is the most well-documented pattern for the "same data, different views" problem.

**How it works:**

1. **Write model** (canonical): A single, persona-neutral data store captures all events.
   ```
   Event: DELTA_CREATED
   Payload: {
     id: "delta-4721",
     type: "PROPOSED_PATTERN",
     source_insight_id: "insight-892",
     contributed_by: "user-jane-sme",
     blast_radius: "MEDIUM",
     affected_guardrails: ["GR-12", "GR-45"],
     status: "PENDING_REVIEW",
     created_at: "2026-01-31T14:23:00Z"
   }
   ```

2. **SME Read Model** (projection: "game results"):
   ```json
   {
     "title": "New Pattern Discovered!",
     "message": "Your insight about medication interactions was added to the knowledge base.",
     "impact": "This could help 3 other teams",
     "points_earned": 25,
     "streak": "5 contributions this week",
     "next_milestone": "Expert Contributor (3 more to go)"
   }
   ```

3. **Curator Read Model** (projection: "governance artifact"):
   ```json
   {
     "delta_id": "delta-4721",
     "type": "PROPOSED_PATTERN",
     "source": "insight-892 (Jane Doe, Cardiology SME)",
     "blast_radius": "MEDIUM",
     "affected_guardrails": ["GR-12: Drug Interaction Protocol", "GR-45: Dosage Bounds"],
     "status": "PENDING_REVIEW",
     "review_actions": ["approve", "reject", "request_revision", "escalate"],
     "audit_trail": [...]
   }
   ```

**Same event, same underlying data, two completely different read models.**

### API Design for Dual Views

**Option A -- Role-based endpoints:**
```
GET /api/sme/activity-feed      -> gamified view
GET /api/curator/deltas/pending  -> governance view
```
Both query the same event store but return persona-shaped responses.

**Option B -- Field projection with persona context:**
```
GET /api/deltas/4721?view=sme
GET /api/deltas/4721?view=curator
```
Single endpoint, server-side projection based on the `view` parameter (validated against user role).

**Option C -- GraphQL with persona-specific fragments:**
```graphql
# SME fragment
fragment GameResult on Delta {
  title: displayTitle(persona: SME)
  message: impactSummary
  points: contributionPoints
  streak: currentStreak
}

# Curator fragment
fragment GovernanceArtifact on Delta {
  deltaId
  type
  blastRadius
  affectedGuardrails { id name }
  status
  reviewActions
  auditTrail { timestamp actor action }
}
```

### Retroactive Projection Capability

A major advantage of CQRS noted in the research: **projections are retroactive**. When you add a new persona or a new view requirement, you can replay the event stream and build the new read model from historical data. You are not locked into the views you designed at launch.

### Data Layer Principles

1. **The canonical model must be persona-neutral**: Never store "points" or "blast_radius" as primary fields. Store the raw event; derive persona-specific attributes in projections.
2. **Projections are disposable and rebuildable**: If the SME gamification model changes, rebuild the projection. The source of truth is the event stream.
3. **Shared identifiers, persona-specific labels**: `delta-4721` is the same ID in both views. But it displays as "Contribution #47" to the SME and "Delta DELTA-4721" to the curator. The labeling is a projection concern, not a data concern.

---

## 6. Role-Based Progressive Disclosure

### The Lens Pattern

The most applicable pattern for "same event, different detail levels" is what I'll synthesize as the **Lens Pattern** -- combining progressive disclosure research from NNGroup, role-based notification design, and CQRS projections:

**Single Event, Multiple Lenses:**

| Event | SME Lens | Curator Lens |
|-------|----------|--------------|
| Delta created | "Your insight was added to the knowledge base" | "Delta PROPOSED_PATTERN created, blast_radius=MEDIUM, pending review" |
| Delta approved | "Your pattern is now helping others! +50 points" | "Delta-4721 APPROVED by @curator-mike, merged to guardrail GR-12, effective immediately" |
| Delta rejected | "Your insight needs a small revision -- tap to see feedback" | "Delta-4721 REJECTED: insufficient evidence. Rejection reason: 'Contradicts GR-45 bounds. Requires clinical citation.' Routed back to contributor." |
| Conflict detected | "Heads up: your suggestion overlaps with an existing pattern" | "CONFLICT: Delta-4721 overlaps Delta-3892 (confidence: 0.87). Resolution required. Blast radius upgraded to HIGH." |

### Implementation Patterns

**Pattern 1: Notification Template Engine**

```typescript
// Event occurs once, notification templates render per persona
const templates = {
  DELTA_CREATED: {
    sme: (delta) => ({
      icon: 'sparkle',
      title: 'New Pattern Discovered!',
      body: `Your insight was added to the knowledge base.`,
      action: { label: 'See Impact', route: '/my-contributions' },
      tone: 'celebratory'
    }),
    curator: (delta) => ({
      icon: 'delta',
      title: `Delta ${delta.type} created`,
      body: `blast_radius=${delta.blast_radius}, pending review`,
      action: { label: 'Review', route: `/review/${delta.id}` },
      metadata: {
        source: delta.source_insight_id,
        affected: delta.affected_guardrails,
        contributor: delta.contributed_by
      },
      tone: 'neutral'
    })
  }
};
```

**Pattern 2: Detail Escalation (Drill-Down by Role)**

For the SME, the notification is the endpoint -- "Your insight was added." If they tap, they see their contribution history and points.

For the curator, the notification is the entry point -- "Delta created, pending review." Tapping opens the full review interface with audit trail, affected guardrails, blast radius visualization, and approval/rejection controls.

Same event triggers both, but the **information depth at each click level** differs by role:

```
SME Click Path:
  Notification -> Contribution Summary -> (optional) View Pattern Detail

Curator Click Path:
  Notification -> Delta Review Panel -> Affected Guardrails ->
  Blast Radius Analysis -> Audit Trail -> Approve/Reject
```

**Pattern 3: Adaptive Verbosity**

Drawing from Slack's notification frequency adaptation and NNGroup's progressive disclosure research:

- **Summary level** (default for SMEs): Natural language, outcome-focused, emotional tone. "3 of your insights were reviewed today -- 2 approved!"
- **Detail level** (default for curators): Structured data, process-focused, neutral tone. "3 deltas reviewed: DELTA-4721 APPROVED, DELTA-4722 APPROVED, DELTA-4698 REJECTED (insufficient evidence)."
- **Expandable**: SMEs can optionally expand to see more detail; curators can optionally collapse to summary. The default differs, but the information is accessible to both.

**Pattern 4: Contextual Metadata Escalation**

From the healthcare domain, where the same adverse event appears differently to different roles:

```
Shared visible fields (both personas):
  - Event name
  - Timestamp
  - Status

SME-additional fields:
  - Impact statement (plain language)
  - Points/contribution metrics
  - Related patterns (simplified)

Curator-additional fields:
  - Delta ID, type classification
  - Blast radius score + visualization
  - Affected guardrails (linked)
  - Contributor identity + history
  - Audit trail
  - Review action buttons
  - Conflict detection alerts
```

The UI renders a shared card skeleton, then populates it with role-appropriate fields. This is the Notion model (same block structure, different editing affordances based on permission) applied to data display.

---

## Cross-Cutting Architectural Recommendations

### 1. Persona Context Provider
Implement a top-level context that flows through the entire component tree:

```typescript
<PersonaProvider persona={currentUser.role === 'sme' ? 'warm' : 'precise'}>
  <ThemeProvider theme={personaThemes[persona]}>
    <NotificationProvider templates={personaTemplates[persona]}>
      <App />
    </NotificationProvider>
  </ThemeProvider>
</PersonaProvider>
```

### 2. Single Event Bus, Multiple Consumers
Every significant action produces one canonical event. Persona-specific projections subscribe independently. Never duplicate the event for different personas.

### 3. Shared Component Library, Persona Variants
Build one `<DeltaCard>`, one `<NotificationToast>`, one `<ActivityFeed>`. Each accepts a `persona` prop or reads from context. Internally, they select the appropriate template, token set, and information density.

### 4. Escape Hatches
Allow curators to temporarily view the SME experience (to understand what contributors see) and allow advanced SMEs to optionally see more technical detail. Figma's Dev Mode toggle is the model here -- not a permanent assignment, but a switchable lens.

### 5. Test with Real Users from Both Personas
NNGroup's research emphasizes that the main danger of progressive disclosure is incorrect assumptions about what each persona needs. Card sorting and task analysis with actual SMEs and actual curators will validate or invalidate the information split.

---

## Sources

- [Salesforce UX Design Principles](https://www.salesforce.com/blog/ux-design-principles-for-sales/)
- [Salesforce Lightning Design Guide (Noltic)](https://noltic.com/stories/the-complete-guide-to-ui-ux-design-for-salesforce)
- [Salesforce UI Features | Salesforce Ben](https://www.salesforceben.com/salesforce-ui-features-to-implement-in-every-org/)
- [Shopify App Design Guidelines](https://shopify.dev/docs/apps/design)
- [Shopify UX for Customer Accounts](https://shopify.dev/docs/apps/build/customer-accounts/ux)
- [Shopify Server-Driven UI Architecture](https://shopify.engineering/server-driven-ui-in-shop-app)
- [Figma Dev Mode](https://www.figma.com/dev-mode/)
- [Figma Guide to Developer Handoff](https://www.figma.com/best-practices/guide-to-developer-handoff/)
- [Figma Designer's Handbook for Handoff](https://www.figma.com/blog/the-designers-handbook-for-developer-handoff/)
- [Slack Kit: The Gradual Design System](https://slack.engineering/the-gradual-design-system-how-we-built-slack-kit/)
- [Slack Product Design Case Study (MetaLab)](https://www.metalab.com/projects/slack)
- [Slack Redesign for Focus](https://slack.com/blog/productivity/a-redesigned-slack-built-for-focus)
- [Reimagining Design Systems at Spotify](https://spotify.design/article/reimagining-design-systems-at-spotify)
- [helloSystem Three-Layer UX Philosophy](https://medium.com/@probonopd/hellosystem-three-layer-ux-design-philosophy-for-simplicity-and-power-37c95bf58398)
- [Navigating the Complexity Paradox in UX](https://medium.com/@luke.a.firth/navigating-the-complexity-paradox-in-ux-design-3473eba43840)
- [Progressive Disclosure | NNGroup](https://www.nngroup.com/articles/progressive-disclosure/)
- [Progressive Disclosure | Interaction Design Foundation](https://www.interaction-design.org/literature/topics/progressive-disclosure)
- [Progressive Disclosure in SaaS UX Design](https://lollypop.design/blog/2025/may/progressive-disclosure/)
- [Veeva vs Medidata | In Practise](https://inpractise.com/articles/veeva-vs-medidata)
- [Medidata Rave EDC](https://www.medidata.com/en/clinical-trial-products/clinical-data-management/edc-systems/)
- [Advanced Theming with Design Tokens](https://david-supik.medium.com/advanced-theming-techniques-with-design-tokens-bd147fe7236e)
- [Design Token System | Contentful](https://www.contentful.com/blog/design-token-system/)
- [Multi-brand Design Systems with Tokens](https://wppluginsify.com/blog/designing-with-tokens-multibrand-design-systems-that-scale-2/)
- [Naming Tokens in Design Systems | EightShapes](https://medium.com/eightshapes-llc/naming-tokens-in-design-systems-9e86c7444676)
- [CQRS Pattern | Microsoft Azure](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- [Projections and Read Models in Event-Driven Architecture](https://event-driven.io/en/projections_and_read_models_in_event_driven_architecture/)
- [CQRS | Martin Fowler](https://www.martinfowler.com/bliki/CQRS.html)
- [API Design Best Practices | Microsoft Azure](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)
- [Playful Design: Gamification of Business Software](https://medium.com/@caleb.kingcott/playful-design-gamification-of-business-software-7d9882604440)
- [Gamification at Work | IxDF](https://www.interaction-design.org/literature/book/gamification-at-work-designing-engaging-business-software)
- [Gamification in Product Design](https://snowball.digital/blog/gamification-in-product-design-make-enterprise-software-suck-less)
- [Notification Design Guidelines | Smashing Magazine](https://www.smashingmagazine.com/2025/07/design-guidelines-better-notifications-ux/)
- [Notification Design | Toptal](https://www.toptal.com/designers/ux/notification-design)
- [User Rights Management UX Case Study](https://medium.com/anothercircus/user-rights-management-redlink-ux-ui-case-study-part-i-8206885208b2)
