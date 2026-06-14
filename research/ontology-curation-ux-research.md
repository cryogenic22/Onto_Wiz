Here is the comprehensive UX research report with concrete findings across all six domains.

---

# Deep UX Research: Ontology Curation & Artifact Management UIs

---

## 1. Ontology Editors and Managers

### Protege (Stanford)

**UI Architecture:** Protege uses a tabbed-panel desktop layout. The primary tabs are: Classes (tree view), Object Properties, Data Properties, Individuals, and OWLViz (graph). Each tab has a left-side hierarchy browser and a right-side detail/annotation editor. The class hierarchy is presented as a collapsible tree with indented sub-classes.

**What works:**
- The tree-based class browser is universally understood for hierarchical navigation. Every ontology tool copies this.
- Plugin architecture allows adding custom views (OntoGraf for graph viz, SPARQL query tab, etc.).
- Reasoner integration (HermiT, Pellet) is surfaced via a single "Start Reasoner" button that overlays inferred hierarchy in a different color (typically yellow background) atop the asserted hierarchy. This "asserted vs. inferred" dual-view is a pattern unique to ontology editors and is highly valued.

**What does not work:**
- The UI is a Java Swing desktop app, visually dated. Community consensus is that many ontologists prefer hand-editing Turtle files over using Protege, indicating serious UX friction.
- WebProtege (the cloud successor) has been effectively stalled for 5+ years and is "riddled with bugs" per community reports.
- No built-in collaboration, no approval workflows, no conflict resolution. Multi-user editing requires external version control.
- The property/annotation editor is a dense form with many fields visible simultaneously -- no progressive disclosure.

**Concrete interaction patterns:**
- **Hierarchy browsing:** Click-to-expand tree. Right-click context menu for "Add Subclass," "Add Sibling," "Delete." Drag-and-drop for reparenting.
- **Entity editing:** Select a class in the tree; right panel shows Description (equivalent classes, superclasses, disjoint classes), Annotations (labels, comments, custom annotations), and Usage (where this class is referenced).
- **Search:** Global search bar with type-ahead; results grouped by entity type (Class, Property, Individual).

### TopBraid Composer / TopBraid EDG

**UI Architecture:** Built on Eclipse, offering a graph-based visual editor alongside form-based editors. TopBraid EDG (Enterprise Data Governance) is the modern web successor.

**What works:**
- Visual graph editing: users can create and edit ontologies using a node-link diagram, making relationships visually explicit. The "SPARQL by example" feature lets users draw a pattern in the graph view and generate the corresponding query.
- TopBraid EDG provides role-based workflows for vocabulary governance: editors propose terms, managers review, administrators approve. This is the only major tool with built-in governance workflow.
- Class diagram generation from OWL models for stakeholder communication.

**What does not work:**
- Eclipse-based UI has the same dated-feeling problem as Protege.
- The learning curve for the Maestro edition is steep -- it bundles SPARQLMotion, web service configuration, and data governance into one dense interface.

### PoolParty Semantic Suite

**UI Architecture:** Web-based, modern-feeling interface. Left panel has a concept scheme tree. Center panel has concept detail. Right panel has related concepts and metadata.

**What works:**
- **Taxonomy Advisor (LLM-powered):** Suggests new terms based on company documents. This is a concrete pattern: an AI sidebar that proposes candidates with relevance scores, and the user accepts/rejects them one by one.
- **NLP-based term extraction:** Semi-automated taxonomy extension from content sources, with the system proposing candidate terms that humans curate. The pattern is: upload corpus, system extracts candidates, user sees a ranked list, clicks to accept/reject/modify each.
- **Faceted navigation and semantic search** built into the browsing experience -- type-ahead search with disambiguation using thesaurus relationships (synonyms, near-synonyms, abbreviations mapped to preferred terms).
- **Concept-centric relationship visualization:** When you select a concept, the right panel shows a mini-graph of its relationships, color-coded by relationship type (broader, narrower, related, etc.).

**What does not work:**
- Full ontology complexity (OWL axioms, restrictions, etc.) is secondary -- PoolParty is optimized for SKOS/thesaurus work, not full OWL ontology engineering.

### Semaphore (Progress/Smartlogic)

**UI Architecture:** Web-based Knowledge Model Manager (KMM) with a side panel widget framework allowing extensible UI.

**What works:**
- **Say-as-you-type querying:** Natural language input to navigate the ontology.
- **Extensible side panel widgets:** Developers can build custom widgets (separate web apps) that load in a side panel when a concept is selected. This is a powerful extensibility pattern -- the core UI stays clean while domain-specific views are pluggable.
- **Automatic classification engine:** Content is tagged against the ontology in real-time, with confidence scores shown inline.
- Users report the Ontology Manager is "really easy to learn" -- suggesting successful simplification.

### Common Interaction Patterns Across All Tools

| Pattern | Description |
|---|---|
| **Tree + Detail** | Left tree hierarchy, right detail panel. Universal. |
| **Search with Type-Ahead** | Global search with results grouped by entity type. |
| **Right-Click Context Menu** | Add/delete/reparent operations on tree nodes. |
| **Asserted vs. Inferred** | Visual differentiation (color, icon) of authored vs. computed facts. |
| **Annotation Pane** | Structured form for labels, definitions, editorial notes per entity. |
| **Relationship Viewer** | Mini-graph or list of incoming/outgoing relationships for selected entity. |

---

## 2. Knowledge Graph Visualization

### Rendering Technology Decision Matrix

This is the most critical architectural decision for a graph UI:

| Technology | Node Capacity | Best For |
|---|---|---|
| **SVG (D3.js)** | Up to ~500 nodes | Crisp, CSS-stylable, accessible. Every element is a DOM node. |
| **Canvas (2D)** | 500 -- 10,000 nodes | Immediate-mode rendering. Must implement hit-testing manually. |
| **WebGL (Sigma.js, Ogma, KeyLines)** | 10,000 -- 1,000,000+ nodes | GPU-accelerated. KeyLines achieves 60fps at 10,000 elements. |
| **Hybrid (WebGL + DOM overlay)** | Large scale + rich UI | WebGL for graph geometry, HTML/SVG overlay for labels, tooltips, controls. This is the production-grade pattern. |

**Concrete finding from benchmarks (PMC study):** Tested D3.js, ECharts.js, G6.js across SVG/Canvas/WebGL with graphs from 100 to 200,000 nodes. For a 3,000-node graph at 30fps minimum, D3-WebGL and D3-Canvas both qualify. SVG drops below usable framerates above ~1,000 nodes with edges.

### Tool-Specific Patterns

**Neo4j Browser:**
- Uses d3-force layout. Nodes are circles, relationships are labeled arrows.
- Click a node to expand its neighbors (incremental exploration). This "expand on click" pattern is the most common graph navigation paradigm.
- Property panel appears on right when a node/relationship is selected.
- Cypher query bar at top -- users type queries, results render as graph or table.
- Architecture pattern: production apps should NOT connect the browser directly to Neo4j. The recommended pattern is API-mediated: client -> API -> Neo4j, with the API controlling what data is exposed.

**Gephi:**
- Three-screen architecture: Overview (interactive visualization), Data Laboratory (spreadsheet view of nodes/edges), Preview (publication-quality export).
- **Filtering is the killer feature:** Drag-and-drop filter composition. Users drag a filter type (Degree Range, Attribute Range, Edge Weight, Giant Component) into a query builder, set thresholds with sliders, and see results update in real-time.
- **Meta-nodes for drill-down:** Clustering algorithms (e.g., modularity) group nodes into collapsible meta-nodes. Click to expand a cluster and see its internal structure. This "semantic zoom" pattern is essential for large graphs.
- Force-directed layout: ForceAtlas 2 handles up to 1 million nodes. Force-based layouts follow a simple principle: linked nodes attract, unlinked nodes repel.
- **Visual encoding:** Node size mapped to degree/centrality, node color mapped to cluster/category, edge thickness mapped to weight. These three channels (size, color, thickness) are the standard visual vocabulary.

**ReactFlow:**
- Designed for node-based UI builders (workflow editors, no-code tools), not pure graph visualization. Nodes are custom React components with input/output handles.
- Connection handling: drag from an output handle to an input handle to create an edge. This "handle-to-handle connection" pattern works well for directed workflows but is less natural for ontology relationships.
- Built-in minimap, zoom controls, background grid.
- Best for: workflow/pipeline visualization where nodes have complex internal content (forms, previews, status indicators).

**d3-force:**
- Force simulation with configurable forces (charge, link, center, collision). The simulation "ticks" and settles over time.
- Common customizations: click-to-pin (freeze a node's position), drag-to-reposition, hover-to-highlight-neighbors.
- For performance at scale: use Canvas rendering instead of SVG; batch DOM updates; use quadtree for collision detection.

### What Scales and What Does Not

**Scales:**
- Incremental exploration ("expand on click") instead of showing entire graph at once.
- Semantic zoom: show clusters at high level, expand to individual nodes on zoom.
- Server-side layout computation (Apache Spark for very large graphs) with client-side rendering.
- WebGL + DOM hybrid: geometry in WebGL, interactive labels in HTML overlays.
- Edge bundling and aggregation for dense graphs.

**Does not scale:**
- SVG with >1,000 elements (DOM overhead kills performance).
- Showing all nodes and edges simultaneously for graphs >10,000 elements (visual clutter, impossible to interpret).
- Force-directed layouts without constraints (layouts are non-deterministic, unstable, and can be disorienting when the graph shifts).
- Full-text labels on every node at all zoom levels.

---

## 3. Curation Workflows

### The Universal Pipeline Pattern

Every curation system converges on a variant of this pipeline:

```
Draft -> Submit -> Review -> [Request Changes | Approve] -> Promote/Publish
```

The key UX decisions are: (a) how states are visualized, (b) how transitions are triggered, and (c) how context is provided at each step.

### GitHub Pull Request Review (Best-in-Class Code Review UX)

**Concrete patterns:**

1. **Three-action review submission:** Comment (feedback only), Approve (explicit signal), Request Changes (blocking signal). This trinary choice is more nuanced than simple approve/reject and has been widely copied.

2. **Inline comments on specific lines:** The reviewer clicks a line number in the diff, types a comment, and optionally suggests a concrete replacement (code suggestion). This "comment anchored to specific content" pattern is directly applicable to ontology artifacts -- imagine commenting on a specific axiom or relationship.

3. **Batch review:** Comments accumulate as a "pending review" and are submitted together. This prevents notification spam and ensures the reviewer's feedback is coherent.

4. **Branch protection rules:** Repository admins configure required approvals (e.g., "2 approvals from CODEOWNERS required"). The merge button is disabled until all gates pass. This "gate before promotion" pattern maps directly to ontology governance.

5. **Review request routing:** The system suggests or auto-assigns reviewers based on code ownership. PR authors can explicitly request review from individuals or teams.

6. **Status checks:** Automated CI/CD checks (tests, linting) run alongside human review. Both must pass. This "automated + human" dual gate is critical for ontology quality.

### Wikipedia Moderation (Content Curation at Scale)

**Concrete patterns:**

1. **Pending changes:** New/untrusted editors' changes go into a queue. Trusted editors review and release them. The key UX insight: the contributor edits normally -- the moderation is invisible to them. The reviewer sees a separate queue.

2. **Workflow taxonomy from Wikimedia Foundation study:** They identified 88 distinct workflows across 5 wikis with 550 steps. The crucial grouping is **moderation** (focus on changes) vs. **curation/creation** (focus on content). This distinction matters for ontology tools -- reviewing a proposed change is a different task from creating new content.

3. **Moderation Extension pattern:** If an edit conflict is detected and cannot be auto-resolved, the moderator gets a "merge" button. Logs of "who approved what" are maintained. Non-approved revisions are never visible in page history.

4. **Pain point:** Moderation tools involve "a headache-inducing combination of spreadsheets and dozens of browser tabs." The Wikimedia design team explicitly acknowledges that tool complexity restricts participation.

### Microsoft Purview (Asset Curation Approval)

**Concrete pattern:** Template-based workflow creation. You select a trigger type (e.g., "data asset curation request"), define approval stages with specific approvers, and the system generates the pipeline. The UI is: select template -> configure stages -> assign approvers -> activate.

### CMS Approval Workflow Best Practices

**Key UX findings from enterprise case studies:**

1. **Stakeholder outline visible at all times:** Show the user which stages their item must pass through, with status indicators at each stage (Approved / Awaiting / Pending). Color-coded status badges.

2. **Guide accessible at every point:** A persistent help panel or tooltip explaining the current stage and required actions.

3. **Biggest pain point:** Showing too much information. Users abandon the app when presented with fields irrelevant to their role. The fix: role-based form reduction -- show only the fields relevant to the current actor's decision.

4. **AI-suggested approvers:** Models recommend the right reviewer and next action based on historical patterns. This is an emerging pattern that maps to ontology governance (e.g., suggest domain expert reviewers based on the ontology domain being modified).

---

## 4. Conflict Resolution UIs

### Three-Way Merge (Industry Standard)

The dominant pattern across all professional tools (VS Code, IntelliJ, Beyond Compare, P4Merge):

```
+------------------+------------------+
| Incoming (Left)  |  Current (Right) |
|   (theirs)       |    (ours)        |
+------------------+------------------+
|          Result (Bottom)            |
+-------------------------------------+
```

- Left panel: incoming changes (read-only).
- Right panel: current version (read-only).
- Center/bottom panel: the merged result (editable).
- The base version (common ancestor) is sometimes shown as a third read-only panel in a true three-way view.

### VS Code Merge Editor (Modern Reference Implementation)

**Concrete patterns:**
- Mixed layout: branch editors on top (read-only), result editor below (editable).
- Color coding: green for additions, red for deletions, with inline character-level highlighting showing exactly which characters changed within a line.
- **Compact diff by default** with toggle to full diff. Compact shows only a few lines of context around each change.
- **Global actions** at the top of the diff (Accept All Incoming, Accept All Current, Accept All Non-Conflicting).
- **Local actions** appear on hover over each individual conflict hunk: "Accept Incoming," "Accept Current," "Accept Both," or manual edit.
- **One-click resolution for simple conflicts:** When the beginning and end of the same line are modified in different versions, a "Resolve Simple Conflicts" button merges them automatically.

### IntelliJ/JetBrains Merge Tool

**Concrete pattern:**
- Three-column layout: Local (left), Result (center, editable), Repository (right).
- "Apply Non-Conflicting Changes" buttons for left and right sides independently.
- Each conflict hunk has chevron buttons (>>  <<) to accept from left or right.
- Color coding: blue for modifications, green for additions, grey for deletions.

### Google Docs Suggestion Mode (Collaborative Conflict Resolution)

**Concrete patterns for ontology relevance:**
- **Non-destructive editing:** Changes are proposed, not applied. Additions appear in a distinct color (green), deletions are shown as strikethrough. A comment box appears in the right margin for each change.
- **Per-suggestion accept/reject:** Each change gets a checkmark (accept) and X (reject) button. Bulk operations via "Accept All" / "Reject All."
- **Threaded discussion per change:** Each suggestion has a comment thread for discussing the rationale. This is directly applicable to ontology change proposals -- "Why rename this class?" with a discussion thread.
- **Three editing modes:** Editing (direct), Suggesting (propose), Viewing (read-only). Permission levels control which mode users can access. The "Commenter" role is locked to Suggesting mode.
- **Audit trail:** Every suggestion is attributed to a specific user and timestamped.

### Design Principles for Conflict Resolution UIs

1. **Always show context:** Never show just the conflicting lines -- show surrounding context (3-5 lines minimum).
2. **Color is primary, not sole, indicator:** Use color + icons + text labels for accessibility.
3. **Auto-resolve what you can:** Apply non-conflicting changes automatically; only present true conflicts to the user. This reduces cognitive load by 70% per industry data.
4. **Character-level diffs within lines:** Showing which specific characters changed within a modified line is far more useful than just highlighting the entire line.
5. **Side-by-side beats unified for complex conflicts.** Unified (interleaved) diffs work for simple changes; side-by-side is essential when both sides have substantial modifications.

---

## 5. "Powerful but Simple" Enterprise UIs

### Design Principles Extracted from Linear, Notion, Figma, Airtable, Retool

#### Linear: The "Linear Design" Movement

Linear has become a design movement unto itself. Key principles:

1. **Sequential, logical progression:** Content and UI flow naturally in the user's reading direction. No cognitive jumps.
2. **High contrast, dark mode first:** Clean, clutter-free, high-contrast interfaces. Dark mode is the default, not an afterthought.
3. **Keyboard-first interaction:** Every action has a keyboard shortcut. Power users never touch the mouse. Command palette (Cmd+K) for any action.
4. **Information hierarchy through typography and spacing:** Not through borders, boxes, or heavy dividers. White space carries meaning.
5. **Status as color:** Issue states (Backlog, Todo, In Progress, Done, Cancelled) are represented by colored icons -- no text label needed once learned.

#### Notion: Block-Based Progressive Disclosure

1. **Everything is a block:** Text, images, tables, databases, embeds -- all are blocks that can be composed, nested, reordered via drag-and-drop. This gives extreme flexibility with a single interaction model.
2. **Slash command for creation:** Type "/" to get a command palette of block types. This is progressive disclosure at its finest -- the empty page looks simple, but typing "/" reveals enormous capability.
3. **Hover-to-reveal controls:** Block handles, drag grips, and action menus appear only on hover. The page looks clean by default.
4. **Inline database views:** A single database can be viewed as Table, Board, Calendar, Timeline, Gallery, or List -- toggled via tabs above the view. The data model is decoupled from presentation.

#### Figma: Contextual Tooling

1. **Context-sensitive right panel:** The properties panel changes entirely based on what is selected. Select nothing: page properties. Select a frame: frame properties. Select text: text properties. This means the UI surface is small but infinitely deep.
2. **Multiplayer by default:** Real-time cursors, avatar stack in toolbar, comment mode with pins on the canvas. Collaboration is not a feature -- it is the environment.
3. **Component/instance model:** Define a component once, use instances everywhere. Changes to the component propagate. Instances can override specific properties. This pattern maps directly to ontology class/instance relationships.

#### Airtable: Familiar Surface, Deep Power

1. **Spreadsheet as gateway drug:** The default view is a grid that looks like Excel. This is the familiarity principle -- users already know how to interact with rows and columns.
2. **Multiple views of same data:** Grid, Kanban, Calendar, Gallery, Gantt, Form. Each view is a lens on the same underlying data. Users can switch without altering the data.
3. **Field-level hiding per view:** You can show different columns to different roles by configuring view-specific field visibility. This is role-based progressive disclosure without complex permission systems.
4. **Single-click automations:** Buttons in rows can trigger workflows (send email, update field, call API). This surfaces automation within the data view rather than in a separate configuration panel.

#### Retool: Builder Surface Principles

1. **Drag-and-drop component canvas:** 100+ pre-built components (tables, forms, charts, buttons). The user drags components onto a canvas and connects them to data sources.
2. **Unified building surface:** Generation, refinement, and logic in a single surface. No tab-switching between "design" and "code" modes.
3. **Escape hatches to code:** When drag-and-drop is not enough, write JavaScript or SQL inline. The key principle: start simple, escape to power when needed. This is progressive disclosure for developers.
4. **AI-powered generation:** Natural language to generate queries and UIs that are schema-aware and fully editable.

#### Synthesized Principles for "Powerful but Simple"

| Principle | Implementation |
|---|---|
| **Familiar entry point** | Start with a metaphor users already know (spreadsheet, document, tree). |
| **Progressive disclosure via interaction** | Hover reveals controls. Slash commands reveal capabilities. Right-click reveals power features. |
| **Context-sensitive panels** | The detail panel morphs based on selection. One panel, many faces. |
| **Keyboard-first for power users** | Command palette (Cmd+K). Every action has a shortcut. |
| **Data/view separation** | One data model, many visual presentations. Toggle between views without data loss. |
| **Escape hatches** | When the simple UI is not enough, drop into code/query/advanced mode without leaving the tool. |
| **Multiplayer as default** | Real-time presence, comments, and change attribution baked in from day one. |
| **Status as visual encoding** | Colors, icons, and spatial position encode state -- reduce reliance on text labels. |

---

## 6. Audit Trail Visualization

### Regulatory Requirements (FDA 21 CFR Part 11, SOX, ICH E6)

The audit trail must capture the "four Ws": **Who** (user identity with full authentication), **What** (exact change including old value and new value), **When** (time-stamped with controlled clock, timezone-aware), and **Why** (reason for change, mandatory where required). Entries must be computer-generated (not manually entered), immutable (cannot be altered or deleted), and retained for the regulatory period (7 years for SOX, 10+ years for healthcare).

### UI Patterns for Audit Trail Visualization

**1. Chronological Timeline View**

The most common pattern. Each change event is a card/row in a reverse-chronological feed:

```
[Timestamp] [User Avatar + Name] [Action Verb] [Entity Name]
   "Changed 'Therapeutic Area' from 'Oncology' to 'Immuno-Oncology'"
   Reason: "Aligned with updated MeSH terminology"
```

This pattern appears in: Salesforce Field Audit Trail, OpenClinica, Datadog Audit Trail.

**2. Filterable Change Log Table**

A table view with columns: Timestamp, User, Action, Entity, Field, Old Value, New Value, Reason. With column-level filtering and sorting. This is the primary pattern for regulatory review -- auditors need to filter by user, time range, entity, or action type.

**Search and filter capabilities:** Users can search across both live and deleted records and apply filters by user, field, action, original value, or new value, making it simple to locate the exact data change needed for investigation.

**3. Inline Rollback**

View detailed change history and undo specific field changes across multiple records -- all within the native UI, without reverting unrelated updates. This selective rollback is critical: you can undo one field change on one record without affecting other changes in the same time window.

**4. Visualization Dashboards for Trend Analysis**

Clinical trial data management platforms use visualization to show:
- **Cycle time trends:** How long from data entry to approval, visualized over time.
- **User activity heatmaps:** Which users are most/least active, identifying bottlenecks.
- **Anomaly detection:** Spikes in modification activity that might indicate data integrity issues.
- Role-based views: CRAs see site-level trends, data managers see field-level changes, sponsors see portfolio-level dashboards.

**5. Diff View for Individual Changes**

When drilling into a specific change event, show a side-by-side or inline diff of the entity before and after the change. This is especially important for complex entities (an ontology class with multiple axioms, annotations, and relationships).

**6. Decision Trail (Provenance Chain)**

For regulated environments, show not just what changed but the chain of decisions:

```
Proposal: "Add 'CAR-T Therapy' as subclass of 'Immunotherapy'"
  |-- Submitted by: Dr. Smith (2024-03-15)
  |-- Reviewed by: Dr. Jones (2024-03-16)
  |     Comment: "Agreed, but suggest adding 'Cell Therapy' as intermediate class"
  |-- Revised by: Dr. Smith (2024-03-17)
  |-- Approved by: Dr. Jones (2024-03-18)
  |-- Promoted to Production: System (2024-03-18)
```

This provenance chain pattern combines audit trail with workflow state transitions.

### Concrete Platform Examples

**OpenClinica:** Every change in clinical data is visible, secure, and auditable. Site-agnostic audit tracking with centralized dashboards. Regulatory audit trail requirements are "not only met but exceeded through enhanced visibility and real-time monitoring."

**Datadog Audit Trail:** Captures and reports on all audit events across configuration, access, and billing. Supports search and analysis of detailed audit events, with export for regulatory requirements (HIPAA, PCI, SOX, GDPR).

**Clinical trial CTMS/EDC systems:** The challenge is that multiple vendor systems (CTMS, EDC, LIMS, RTSM, eCOA/ePRO, eConsent) each have their own audit trails in different formats. Modern platforms integrate these into a single view for cross-validation and audit readiness.

**AI-assisted audit trail review:** Generative AI is being used to prioritize audit trail entries based on risk (patient safety impact, data integrity criticality) rather than requiring exhaustive review of every entry.

---

## Synthesis: Patterns Most Relevant to Onto_Wiz

Based on the project structure (ontology YAML files, a Next.js frontend, quality-gate tooling, reasoning tests, and pharma domain focus), here are the highest-priority patterns to implement:

1. **Tree + Detail + Relationship Mini-Graph** (from Protege/PoolParty) as the primary browsing interface for ontology artifacts.

2. **Propose -> Review -> Approve pipeline** (from GitHub PR review) with inline commenting anchored to specific ontology elements, batch review submission, and required-approvals gates.

3. **Three-way diff for ontology conflicts** (from VS Code merge editor) adapted for YAML/structured data, showing left/right/result panels with color-coded changes.

4. **WebGL + DOM hybrid rendering** (from the graph visualization research) for knowledge graph views. Use Canvas or WebGL for the graph layout, HTML overlay for interactive labels and tooltips.

5. **Progressive disclosure via slash commands and context-sensitive panels** (from Notion/Figma) to keep the surface simple while exposing ontology power features.

6. **Chronological audit timeline + filterable table + decision provenance chain** (from clinical trial systems) for FDA/regulatory compliance, with the four Ws (who/what/when/why) captured automatically.

7. **AI-suggested terms and reviewers** (from PoolParty's Taxonomy Advisor and CMS workflow patterns) as an augmentation layer, not a replacement for human curation.

---

Sources:
- [Protege - Stanford](https://protege.stanford.edu/)
- [Protege on Hacker News](https://news.ycombinator.com/item?id=38221709)
- [WebProtege: A Cloud-Based Ontology Editor](https://dl.acm.org/doi/10.1145/3308560.3317707)
- [Top 5 Ontology Editors](https://taxonomy.cloud/article/The_5_Best_Ontology_Editors_for_Semantic_Web_Development.html)
- [PoolParty Thesaurus Manager](https://www.poolparty.biz/poolparty-thesaurus-manager)
- [Taxonomy-Driven UX with PoolParty](https://enterprise-knowledge.com/taxonomy-driven-user-experiences-with-poolparty/)
- [Taxonomy Software Trends](https://www.hedden-information.com/taxonomy-software-trends-convergence-and-visualizations/)
- [Semaphore Semantic AI Platform](https://www.smartlogic.com/semaphore)
- [Semaphore Side Panel Widget Framework](https://github.com/Smartlogic-Semaphore-Limited/Smartlogic-Semaphore-side-panel-widget-framework)
- [Neo4j Graph Visualization Tools](https://neo4j.com/docs/getting-started/graph-visualization/graph-visualization-tools/)
- [React Flow](https://reactflow.dev)
- [Neo4j LLM Knowledge Graph Builder 2025](https://medium.com/neo4j/llm-knowledge-graph-builder-first-release-of-2025-532828c4ba76)
- [Graph Visualization Efficiency (PMC Study)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12061801/)
- [KeyLines WebGL Visualization](https://cambridge-intelligence.com/visualizing-graphs-webgl/)
- [SVG vs Canvas vs WebGL Tradeoffs](https://dev.to/vitalf/svg-vs-canvas-vs-webgl-for-diagram-viewers-tradeoffs-bottlenecks-and-how-to-measure-34n7)
- [ParaGraphL - WebGL Graph Layout](https://nblintao.github.io/ParaGraphL/)
- [Gephi Documentation](https://docs.gephi.org/User_Manual/gui/)
- [Gephi Graph Visualization Tutorial](https://medium.com/data-analytics-at-nesta/how-to-create-network-visualisations-with-gephi-a-step-by-step-tutorial-e0743c49ec72)
- [Complex Approvals UX - UXPin](https://www.uxpin.com/studio/blog/complex-approvals-app-design/)
- [Improving Approval Process UX - Case Study](https://medium.com/design-bootcamp/improving-the-approval-request-process-on-an-enterprise-application-a-ux-case-study-12d2756af876)
- [Microsoft Purview Asset Curation Workflow](https://learn.microsoft.com/en-us/purview/legacy/how-to-workflow-asset-curation)
- [UI/UX Enhancements in Workflow Approvals](https://hivo.co/blog/improving-uiux-of-workflow-approvals-software)
- [GitHub Code Review](https://github.com/features/code-review)
- [Improving Code Review on GitHub - Joel Glovier](https://medium.com/@jglovier/improving-code-review-on-github-ca550ceac5b8)
- [VS Code Three-Way Merge UX](https://github.com/microsoft/vscode/issues/146091)
- [XWiki Merge Conflict Resolution UI Design](https://design.xwiki.org/xwiki/bin/view/Design/MergeConflictResolutionUI)
- [IntelliJ Resolve Conflicts](https://www.jetbrains.com/help/idea/resolve-conflicts.html)
- [Google Docs Suggestion Mode](https://support.google.com/docs/answer/6033474)
- [Wikipedia Content Moderation Design](https://design.wikimedia.org/blog/2020/07/30/content-moderation-anti-vandalism-wikipedia.html)
- [Wikimedia Editor Workflows Study](https://wikimediafoundation.org/news/2018/08/14/understanding-workflows-wikimedia-editors/)
- [MediaWiki Moderation Extension](https://www.mediawiki.org/wiki/Extension:Moderation)
- [Linear UI Redesign](https://linear.app/now/how-we-redesigned-the-linear-ui)
- [Linear Design Trend - LogRocket](https://blog.logrocket.com/ux-design/linear-design/)
- [Progressive Disclosure - Nielsen Norman Group](https://www.nngroup.com/articles/progressive-disclosure/)
- [Progressive Disclosure in SaaS UX](https://lollypop.design/blog/2025/may/progressive-disclosure/)
- [Figma UI Design Principles](https://www.figma.com/resource-library/ui-design-principles/)
- [Retool](https://retool.com)
- [21 CFR Part 11 Audit Trail Requirements](https://simplerqms.com/21-cfr-part-11-audit-trail/)
- [FDA Audit Trail Requirements](https://www.complianceg.com/fda-audit-trail/)
- [Audit Trails in Clinical Data - OpenClinica](https://www.openclinica.com/blog/audit-trails-transparency-tracking-changes-in-clinical-data/)
- [Clinical Trial Data Visualisation](https://www.quanticate.com/blog/clinical-trial-data-visualisation)
- [Datadog Audit Trail](https://www.datadoghq.com/product/audit-trail/)