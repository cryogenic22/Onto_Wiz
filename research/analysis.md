# Research Analysis: Process Ontology & SME Digital Twin

> **Source:** Transcript — Kapil Pant & Shivam (stakeholder conversation)
> **Context:** Requirements gathering for Onto_Wiz platform evolution
> **Analyzed by:** Team ATLAS | 2026-02-02
> **Cross-references:** `gamification-ux-research-expert-knowledge-capture.md`, `sme-impact-feedback-loops-research.md`

---

## Executive Summary

The conversation reveals **three interconnected knowledge layers** that Onto_Wiz must eventually capture, only one of which (data/domain) the current architecture addresses. The two missing layers — **process knowledge** and **agent skill acquisition** — represent the gap between "knowing what" and "knowing how." Shivam validates the gamification approach ("110%") and introduces the concept of **process ontology** as a prerequisite for useful agentic AI.

---

## 1. Three Knowledge Layers Identified

### Layer 1: Data Domain Knowledge (Currently Captured)
- Metrics, business rules, KPIs — standard ontology content
- Example: "Drivers and barriers for a brand" — entities, relationships, tags
- **Onto_Wiz status:** Addressed by `commercial.yaml`, inference rules, gold sets
- **Backlog mapping:** ATL-001 (done), ATL-002 (done), ATL-004 (Market Access)

### Layer 2: Process Knowledge (Gap — New Concept)
- **Definition:** How an SME approaches a problem step-by-step, which systems they visit, in what order, and what decisions they make at each node
- **Example from transcript:** A field rep deciding which physician to approach must visit 5 different systems (Veeva, Salesforce, Excel, IQVIA, internal tools), filter on different metrics at each step, and their decision changes based on incentives, therapy area, and drug potential
- **Key insight:** "Different people take different approaches. Process mapping is crucial."
- **Shivam's term:** "Process ontology" — mapping the how, not just the what
- **Onto_Wiz status:** Not captured. Current ontology models entities and rules but not decision workflows
- **Backlog mapping:** CTX-025 (Process Trace Model), CTX-027 (Canonical Procedure Extraction)

### Layer 3: Agent Skill Acquisition (Vision — Future)
- **Definition:** Agent learns user patterns over time — episodic memory of question sequences, intent prediction, automatic prompt refinement
- **Key insight:** "If you see the sequence of questions a person is asking, that itself tells you a lot about what they are trying to finally solve"
- **Memory types discussed:** Semantic (domain facts) and episodic (session-level interaction patterns)
- **Desired outcome:** Reduced follow-up questions over time; agent anticipates user intent
- **Onto_Wiz status:** Not scoped
- **Backlog mapping:** LENS-024 (Question Sequence Analytics), CTX-028 (Expert Profile Model), EPIC-008 (Agentic AI)

---

## 2. Key Concepts Extracted

### 2.1 Process Ontology
**What it is:** A structured representation of how domain experts approach problems — the sequence of steps, decision points, information sources consulted, and criteria applied at each node.

**Distinct from data ontology:** Data ontology says "market share is a metric in the Commercial domain." Process ontology says "to diagnose a market share drop, the analyst first checks TRx trends, then filters by territory, then compares to competitor launches, then checks access barriers."

**Shivam's framing:**
- "Step by step, rules need to come out, and each rule's corresponding actions will be governed by these metrics and use cases"
- Analogized to manufacturing process maps (which take 2-3 years in industry)

**Implication for Onto_Wiz:** The SME game currently captures *what* the expert thinks (hypothesis, drivers, confidence). It does not capture *how* they arrived at that conclusion (which data they checked, in what order, what alternatives they considered and discarded).

### 2.2 Gamification as Knowledge Extraction
**Shivam's validation:** "110% useful" — gamification keeps the SME engaged while their approach gets codified in the background.

**Mechanism described:**
1. Progressive difficulty (Duolingo model) — start simple, increase complexity
2. SME learns from the process (refresher effect) while the system learns from them
3. The "how they approach" is more valuable than the "what they answer"

**Connection to existing research:** Directly aligns with `gamification-ux-research-expert-knowledge-capture.md` — particularly the micro-contribution pattern (3-5 minute sessions) and the progressive challenge design.

### 2.3 Digital Twin of SME
**Shivam's concept:** "If I can ask 100 people, I codify that thing as a ZS SME. Future, you just ask this ZS SME."

**Architecture implied:**
1. Crowdsource knowledge from multiple SMEs via gamification
2. Extract and codify into a knowledge graph
3. The graph becomes a queryable "digital twin" that can answer questions the way those 100 people collectively would
4. Layered graph: commercial level → patient level → access level → field level, with nodes that "keep exploding into details"

**Strategic insight:** "This should never be shared directly with clients. It's the secret sauce. What we deploy for the client is the output."

**Backlog mapping:** CTX-028 (Expert Profile Model) is the closest ticket — but Shivam's vision is broader: not just one expert's profile, but a composite organizational knowledge agent.

### 2.4 Agent Intent Prediction from Question Sequences
**Key pattern:** Leadership doesn't ask "what is the market share?" — they ask "why did it drop?" The agent should detect the *intent* behind a sequence of questions.

**Example:** If a user asks market share → TRx range → territory breakdown, the sequence reveals they're diagnosing a regional performance issue. The agent should proactively surface relevant drivers without being asked.

**Technical approach discussed:**
- Episodic memory: store question-answer sequences per user
- Pattern learning: detect recurring question sequences across users
- Reinforcement: agent reduces follow-up questions over time as it learns patterns
- Skill acquisition: "The number of follow-ups will automatically reduce over time"

**Backlog mapping:** LENS-024 (Question Sequence Analytics), EPIC-008 (Agentic AI — CTX-033 through CTX-039)

### 2.5 User Analytics for Prompt Intelligence
**Insight:** Track what users write as prompts in analytics tools (Laila, or any query interface). The prompt patterns reveal:
- What users are trying to solve
- Where existing tools fall short (high follow-up count = poor UX)
- How different personas approach the same data differently

**Shivam's suggestion:** Deploy Matomo or Google Analytics to capture prompt-level telemetry. "People are just tracking user adoption metrics today, but this data is going to be huge."

**Connection to Onto_Wiz:** This validates the SME game as a telemetry source — every game session generates structured prompt-equivalent data (question + response + confidence) that feeds the knowledge graph.

---

## 3. Implications for Onto_Wiz Architecture

### 3.1 Process Ontology Layer (New)

The current ontology stack is:
```
commercial.yaml          → inference rules, entities, relationships
therapeutic_areas/       → oncology, (future: immunology, CNS, etc.)
synthetic_data/          → accounts, signals, dark data
scenarios/               → structured scenario definitions
```

A process ontology layer would add:
```
process/                 → decision workflows, step sequences
  field_rep_targeting.yaml    → how reps choose physicians
  market_share_diagnosis.yaml → how analysts diagnose drops
  access_barrier_triage.yaml  → how access teams prioritize
```

Each process file would contain:
- **Steps:** Ordered sequence of decision nodes
- **Information sources:** Which system/data each step consumes
- **Decision criteria:** What metrics/rules govern branching
- **Variant paths:** How different personas traverse differently
- **Output:** What each step produces for the next

**Recommendation:** Create **ATL-020: Process Ontology Seed** as a research spike. Define the YAML schema for process workflows, create 2-3 seed processes from the field rep example in this transcript. This informs CTX-025 (Process Trace Model) and CTX-027 (Canonical Procedure Extraction).

### 3.2 SME Game Enhancement Path

Current game flow: `Signal → Hypothesis → Drivers → Confidence → Submit`

Enhanced flow (informed by this research):
```
Signal → [How did you reach this hypothesis?]
       → [Which data sources did you check?]
       → [What alternatives did you consider and discard?]
       → Hypothesis → Drivers → Confidence → Submit
```

The bracketed steps capture process knowledge without adding burden — they're gamified as progressive difficulty levels. This maps to CTX-025 (add step tracking to ReasoningEvent) and the existing gamification research.

### 3.3 Composite Expert Model

The "digital twin of ZS SME" vision suggests the ContributionStore (CTX-018, done) is the foundation, but needs extension:
- CTX-028 (Expert Profile Model): Builds per-SME profiles from contributions
- **New concept:** Composite profiles that merge multiple SMEs' process knowledge into canonical procedures (CTX-027)
- Graph layers: `commercial → patient → access → field` with progressive detail expansion

---

## 4. Backlog Impact Assessment

### Directly Validated (Already Scheduled)

| Ticket | Validation from Transcript |
|--------|---------------------------|
| CTX-025 | "Step by step, rules need to come out" — process trace is essential |
| CTX-027 | "Different people take different approaches... process map is crucial" |
| CTX-028 | "Digital twin... codify as a ZS SME" — expert profiles needed |
| LENS-024 | "Sequence of questions tells you what they're trying to solve" |
| EPIC-008 | Agent learning patterns, episodic memory, skill acquisition |
| ATL-021 | Auto-scenario generation from real sessions — Shivam confirms value |

### Priority Adjustments Recommended

| Ticket | Current Sprint | Recommended | Reason |
|--------|---------------|-------------|--------|
| CTX-025 | Sprint 4-6 (HIGH) | Sprint 5 | Process traces are prerequisite for process ontology; validated as critical |
| LENS-024 | Sprint 7-10 (MED) | Sprint 6 | Question sequence analytics directly feeds agent intent prediction |
| CTX-028 | Sprint 7-10 (MED) | Sprint 7 | Expert profiles are the "digital twin" foundation; move up |

### New Tickets Suggested

| ID | Title | Team | Depends On | Est | Description |
|----|-------|------|-----------|-----|-------------|
| ATL-020 | Process Ontology Schema + Seed | ATL | ATL-001 ✓ | M | Define YAML schema for process workflows; create 2-3 seed processes (field rep targeting, market share diagnosis) |
| CTX-040 | Episodic Memory Store | CTX | CTX-018, CTX-025 | L | Store question-answer sequences per user session; enable pattern detection across sessions |
| LENS-029 | Prompt Telemetry Capture | LENS | LENS-005 | M | Capture structured telemetry from game sessions + any query interfaces; feed into analytics pipeline |

---

## 5. Strategic Observations

1. **The "secret sauce" framing is important.** Shivam explicitly says the knowledge graph is not shared with clients — only outputs are deployed. This validates the Onto_Wiz architecture where the ontology + inference rules are internal, and Intelligence Packets are the client-facing artifact.

2. **Process knowledge is the harder, higher-value problem.** Data domain ontology is "standard" (Shivam's word). Process ontology is where competitive advantage lives, because it captures how ZS experts think, not just what they know.

3. **Gamification is validated by stakeholders, not just UX research.** The existing `gamification-ux-research-expert-knowledge-capture.md` provided theoretical backing. This transcript provides stakeholder buy-in from an operational leader who has done 6+ projects manually.

4. **The agent vision is real but distant.** Agent skill acquisition, episodic memory, and intent prediction are Sprint 7-10+ capabilities. The near-term value is in process ontology (capturable now via the SME game) and question sequence analytics (buildable on current infrastructure).

---

## Appendix: Raw Transcript Themes Index

| Theme | Transcript Location (Approximate) | Key Quote |
|-------|-----------------------------------|-----------|
| Standard ontology approach | Opening | "There are ways like a standard ontology and that's the process we also do" |
| Gamification validation | Early | "110% useful... instead of us asking questions" |
| Process vs. data knowledge | Mid-early | "There are 2 different kinds of things in domain: data domain and process" |
| Process ontology concept | Mid | "Process ontology — mapping the how, not just the what" |
| Field rep example | Mid | "They have to go to 5 different places to get all of this information" |
| Agent data aggregation | Mid-late | "The agent goes through all 5 systems and becomes a single platform" |
| Question sequence insight | Mid-late | "The sequence of questions tells you what they are trying to solve" |
| Episodic memory | Late-mid | "Semantic or episodic memory... based on your question-answer patterns" |
| Agent skill learning | Late | "Automatically, the agent starts learning your pattern — that becomes agent skill set" |
| Digital twin of SME | Late | "If I can ask 100 people, I codify that thing as a ZS SME" |
| ZS Ontology as a Service | End | "This would be all the ZS knowledge in one place... the secret sauce" |
| User prompt analytics | Late | "What data to capture? Track what people write as prompts" |
