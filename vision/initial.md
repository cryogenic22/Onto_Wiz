# Vision Document: Agentic Semantic Readiness Platform

## 1. Vision (North Star)

Build a **living semantic layer** that captures, tests, and operationalizes expert judgment so AI systems can reason, explain, and act like ZS’s best practitioners—safely, repeatedly, and at scale.

This platform turns **tacit expertise** into **agent-ready intelligence**, continuously proving its value by answering real business questions better over time.

**In one line:** *A system that learns how experts think, not just what data exists—and makes that thinking deployable across clients.*

---

## 2. The Problem We Are Solving

### The Reality Today

* Client data products are technically strong but **semantically thin**
* LLMs can summarize but **cannot reliably reason or diagnose**
* Expert knowledge lives in people’s heads, decks, and meeting rooms
* Each client engagement re-discovers the same heuristics, edge cases, and constraints

### The Core Gap

> AI fails not because of lack of data, but because **meaning, judgment, and constraints are implicit**.

Without explicit semantics:

* Agents hallucinate confidently
* Explanations lack traceability
* Recommendations feel generic
* Risk increases in regulated or high-stakes decisions

---

## 3. The Big Idea

Create an **Agentic Semantic Readiness Platform** that:

1. **Elicits expert judgment through play and scenarios** (not documentation)
2. **Codifies that judgment into ontologies, rules, and prompts**
3. **Continuously tests readiness using real business questions**
4. **Binds semantics to client data products without replacing them**

Ontology is not the output. **Improved answerability and actionability are.**

---

## 4. Core Design Principles

1. **Ontology Emerges from Use**
   No big-bang modeling. Semantics evolve from scenarios, failures, and questions.

2. **Business Questions as Unit Tests**
   Every semantic element must improve the system’s ability to answer a real question.

3. **Expert-Friendly by Default**
   Experts teach by reacting, choosing, and explaining—not by defining schemas.

4. **Thin, Non-Invasive Architecture**
   Sits on top of client data products; never becomes a system of record.

5. **Evidence-Backed Reasoning**
   Every assertion is linked to data, documents, or expert validation.

---

## 5. What the Platform Does (Functional Vision)

### 5.1 The Scenario & Game Engine

A conversational, agentic experience where users:

* Respond to realistic scenarios and counterfactuals
* Compare explanations and trade-offs
* Reveal heuristics, confidence, and boundaries

**What gets captured:**

* Concepts (e.g., promo saturation, access friction)
* Relationships (causal, conditional, contextual)
* Constraints (when reasoning is allowed vs prohibited)
* Confidence signals and disagreement

---

### 5.2 Continuous Ontology & Semantic Layer

A living knowledge structure containing:

* Domain concepts and hierarchies
* Relationships and inference paths
* Business rules and guardrails
* Prompt fragments and few-shot exemplars

Versioned by:

* Domain (forecasting, commercial, supply, etc.)
* Maturity
* Client context

---

### 5.3 Business-Question Test Harness

Canonical questions the system must answer, such as:

* “How is Spain performing vs expectation?”
* “Why did sales dip last quarter?”
* “Where are patients dropping from the funnel—and why?”

Each question defines:

* Required entities and data
* Allowed reasoning patterns
* Expected outputs (narrative, attribution, confidence)

The platform tracks **answerability scores** over time.

---

### 5.4 Synthetic Data & Scenario Simulation

Synthetic data is used to:

* Simulate edge cases and stress-test reasoning
* Train agents when real data is unavailable
* Identify semantic gaps early

Synthetic data is always labeled as **test-only**, never as truth.

---

### 5.5 Multi-Modal Ingestion & Evidence Supply Chain

The platform ingests:

* Structured data tables and schemas
* Data catalogs and metrics definitions
* Meeting notes and working docs
* PMRs, clinical reports, unstructured text

From each source it:

* Extracts entities, events, measures, and claims
* Links them to existing ontology nodes
* Attaches provenance, confidence, and ownership

---

## 6. What Gets Deployed to Clients

Clients do **not** receive the game engine.

They receive a **Semantic & Agent Readiness Package**:

* Domain-specific ontology slice
* Business-question tests
* Prompt and policy bundles
* Mappings to client data products

This layer enables:

* Safer copilots
* Faster diagnostics
* Consistent executive narratives
* Reusable agent workflows

---

## 7. Architectural Positioning

**Layered Model:**

* Client systems and data products remain unchanged
* The platform provides a semantic and reasoning layer above them
* Agents and copilots consume this layer

**Key principle:** Client owns data. ZS provides meaning.

---

## 8. Value for ZS

### Strategic Value

* Turns expertise into reusable IP
* Creates a differentiated agentic offering
* Strengthens EDMA and Scaled AI propositions

### Economic Value

* 60–70% reuse across clients
* Faster time-to-value per engagement
* New annuity-style offerings (semantic refresh, agent upgrades)

### Cultural Value

* Experts become teachers of AI, not documentation writers
* Knowledge compounds instead of resetting per project

---

## 9. What This Is Not

* Not a data lake
* Not an MDM system
* Not a generic knowledge graph
* Not a standalone SaaS replacing client platforms

It is a **semantic accelerator and agent control plane**.

---

## 10. Success Metrics

* Reduction in time to answer core business questions
* Increase in answer consistency across teams
* Agent accuracy and confidence calibration
* Reuse rate of semantic assets across clients
* Expert participation and engagement

---

## 11. The End State

A future where:

* ZS deploys AI agents that reason with institutional memory
* Client work starts at judgment, not data wrangling
* Expertise compounds across years and accounts

**ZS doesn’t just deliver insights. It delivers thinking—at scale.**



raw notes 


You said:
What’s the role of ontology now when we talk about data readiness for ai. Is it relevant
ChatGPT said:
Short answer:
Yes—ontology is still relevant for AI data readiness, but its role has changed. It’s no longer about rigid enterprise taxonomies; it’s about making meaning explicit so agents can act safely, traceably, and at scale.

Long answer (Answer first, then logic):
Ontology has shifted from being a data modeling artifact to a control plane for AI behavior. If you’re building agentic systems (not just analytics), you cannot avoid it—you can only decide whether it’s designed or accidental.

1. What Ontology Used to Be (and why people got tired of it)
Old world (EDW / BI era):

Heavy upfront canonical models

Centralized, slow, brittle

Optimized for reporting consistency, not decision-making

Failed because business moved faster than schema governance

👉 Result: “Ontology is academic / over-engineered” became the dominant take.

That critique was valid then.

2. What Ontology Is Now in AI-Ready Data
Modern ontology = semantic scaffolding for AI systems

Think of it as:

A map of meaning, not a schema of tables

A constraint system, not a data dictionary

A shared language between humans, models, and agents

In practice, ontology now does 5 critical jobs:
Job	Why it matters for AI
Disambiguation	“Customer,” “HCP,” “Account,” “Patient” ≠ same thing to an agent
Reasoning paths	Enables inference (“if X + Y → risk”)
Action boundaries	What an agent may vs must not do
Traceability	Why the model made a recommendation
Composability	Allows agents to generalize across use cases
Without this, LLMs hallucinate confidently.

3. Ontology vs Embeddings vs LLMs (This is the real confusion)
A lot of teams think embeddings replace ontology. They don’t—they complement it.

Layer	Role
Embeddings	Capture statistical similarity
LLMs	Generate language + plans
Ontology	Defines meaning, rules, and constraints
Key insight:
Embeddings answer “what is similar?”
Ontology answers “what is allowed, true, or causal?”

Agents need both.

4. Where Ontology Becomes Non-Negotiable
Ontology becomes mandatory when you cross any of these lines:

1. From “insight” → “action”
The moment an agent:

Writes back to a system

Changes a document

Triggers a workflow

Makes a recommendation with risk

You need explicit semantics.

2. From single use case → platform
Reusable agents need shared meaning.
Otherwise, every agent re-learns the world slightly differently → chaos.

3. Regulated domains (pharma, healthcare, finance)
Ontology is how you encode:

Indications vs off-label

Medical vs promotional language

Source-of-truth hierarchies (CCDS → SmPC → Label)

You already live in ontologies—you just call them SOPs today.

5. The Right Way to Think About Ontology Now (This is the trap to avoid)
❌ Wrong approach
“Let’s build an enterprise ontology”

Big-bang canonical models

Central governance first

✅ Right approach
Ontology emerges from agent needs

Start with:

What decisions will agents make?

What actions are high-risk?

Where must meaning be precise?

Then encode:

Concepts (not tables)

Relationships (not joins)

Constraints (not validation rules)

[Visual: Layered stack – Data → Semantics → Reasoning → Action]

6. A Simple Heuristic I Use
If your AI roadmap includes agents, then:

Ontology is the “constitution.”
Prompts are just “policy memos.”

You can ship without a constitution—but only until something breaks.

Bottom line (BLUF)
Ontology is absolutely relevant

It has moved from data modeling → AI control & reasoning

You don’t need more ontology work

You need just-enough semantics, driven by agent behavior

If you want, next we can:

Map ontology vs knowledge graph vs feature store

Define “minimum viable ontology” for an agentic platform

Or pressure-test whether your current EDMA assets already are an ontology in disguise

You said:
so i want to create a bit of an agentic game or a chatbot that plays a discussion game with a user or expert in zs lets say someone with deep forecasting knowledge. the game works on premise of series of questions or scenarios it proactively lays out. its fundamental mission is to codify the expert knowledge into these agent ready ontologies along woth other metadata, few shot prompts etc relevant for the domain. the tools works in a way that by playing the scenarios with different users and based on responses, it continues to build this ontology and this is also enhanced by the agents reading throigh existing documents, data tables, catalogs etc. do you feel this could be an idea to crowd source creation of a zs wide effort to codofy this knowledge that can then be selectively deployed for agents ?
ChatGPT said:
Short answer:
Yes — this is a strong idea. Done right, it’s not a chatbot; it’s a knowledge distillation engine disguised as a game. That’s exactly the right move if your goal is to codify tacit ZS expertise into agent-ready assets without asking experts to “do ontology work.”

Now let me pressure-test it and sharpen it.

1. What You’re Actually Proposing (Reframed Clearly)
This is not:

Crowdsourcing content

A survey tool

A generic chatbot

This is:

A human-in-the-loop semantic compiler that converts expert judgment into:

Ontologies (concepts, relationships, constraints)

Decision heuristics

Edge cases & failure modes

Few-shot exemplars

Confidence bands & uncertainty signals

Key insight:
Experts don’t write knowledge well — they react to scenarios exceptionally well. You’re exploiting that.

2. Why the “Game” Framing Is the Right Trojan Horse
You’re solving three hard problems simultaneously:

Problem 1: Tacit knowledge is invisible
Forecasting expertise lives in:

“I wouldn’t trust that signal”

“This looks right but smells wrong”

“This only works in market X, not Y”

Your scenario game forces externalization.

Problem 2: Experts hate formalization
If you ask:

“Define your ontology for demand elasticity”

You’ll get nothing.

If you ask:

“Scenario A vs B — which forecast would you bet your bonus on, and why?”

You’ll get gold.

Problem 3: Ontology design doesn’t scale centrally
You’re replacing:

Central modeling
With:

Emergent, evidence-backed semantics

This is exactly how Wikipedia beat Britannica — but for judgment, not facts.

3. The Right Mental Model (This Is Important)
Think of this as a 3-layer learning loop, not a single system.

Layer 1: The Scenario Engine (The Game)
Presents dilemmas, trade-offs, counterfactuals

Asks why, not just what

Introduces controlled ambiguity

Example (forecasting):

“Demand drops 8% QoQ, promo intensity increases, competitor launches biosimilar.
Which driver do you overweight — and which do you explicitly ignore?”

This is ontology extraction in disguise.

Layer 2: The Semantic Harvester (Behind the Scenes)
From each interaction, you extract:

Concepts (“Promo fatigue”, “Channel saturation”)

Relationships (“Promo ↑ does not imply demand ↑ after threshold T”)

Constraints (“Only valid for chronic therapies”)

Confidence signals (“Expert certainty: high/medium/low”)

This is where:

Ontology nodes

KG edges

Few-shot prompts

Guardrails
are incrementally built.

Layer 3: The Agent Feedback Loop
Agents then:

Use this ontology to reason

Fail in specific ways

Feed new scenarios back into the game

This creates a self-improving epistemic loop:
Human → Ontology → Agent → Failure → Better Scenarios → Better Ontology

That’s rare and powerful.

4. Why This Is Especially Right for ZS
This fits ZS’s real asset base:

What ZS actually has (but hasn’t productized):
Deep vertical judgment (forecasting, GTM, access, pricing)

Long-tenured client-embedded experts

Pattern recognition across accounts

Strong opinions with nuance

What ZS lacks today:
A scalable way to reuse judgment

A way to turn expertise into agent behavior

A living semantic layer across practices

Your idea is a knowledge flywheel, not a tool.

5. Where This Could Fail (And How to Fix It)
Let me be sharp here.

Risk 1: You accidentally build a “fun survey”
Fix:
Every scenario must map to an explicit semantic delta, e.g.:

New concept

New constraint

Stronger confidence weighting

Contradiction resolution

No semantic output → scenario is useless.

Risk 2: Ontology sprawl
Crowdsourcing can create noise.

Fix:
Introduce:

Reputation-weighted experts

Conflict detection (“Experts disagree here” becomes a first-class signal)

Versioned ontologies by domain maturity

Disagreement is signal, not a bug.

Risk 3: Too abstract, not agent-ready
If outputs stay “interesting,” agents can’t use them.

Fix:
Every ontology element must map to at least one of:

Prompt fragment

Decision rule

Retrieval filter

Action constraint

If it can’t be operationalized, don’t store it.

6. This Is the Killer Reframe (Use This Internally)
Don’t pitch this as:

“Crowdsourcing ontology”

Pitch it as:

“Turning ZS experts into teachers of AI colleagues — without changing how they work.”

Or even stronger:

“A system that learns how ZS thinks, not just what it knows.”

That’s a platform narrative, not a tool.

7. My Verdict
Yes — this is a viable, differentiated, ZS-native idea.
More than that: it’s one of the few credible ways to build agentic IP at scale without burning expert goodwill.

If you want, next we can:

Design a Minimum Viable Game Loop (first 10 scenarios)

Define the semantic data model behind it

Or pressure-test this as an internal platform vs client-facing offering

This idea is worth taking seriously.

You said:
one more thing will be that the ontology we create should continously test for key business questions and generate synhetic data, its like as a user plays the game , they can also see the ontology developing and the system sayins, now you can better answers questions like how is the spain market performing or why was there a dip in sale or patients dropping from funnel etc. other things is that somehow the system also has mechanism that we can add different types of data files, meeting notes, exerpts and data schemas etc. as well as unstructured data like a pmr or a clinical report and the system extracts entities and relevance and curate the ontology and associated elements for data for ai readiness. 
ChatGPT said:
Yes — and the moment you add (a) “business-question tests” + (b) “synthetic data generation” + (c) multi-modal ingestion, you’ve upgraded the concept from ontology crowdsourcing to an Agentic Data Readiness Workbench.

Below is the clean way to structure it so it doesn’t become a science project.

The Core Product Idea
A living semantic layer that proves its value daily by answering business questions better over time.

Ontology isn’t the deliverable. Improved answerability is.

[Visual: Flywheel — Play Scenarios → Update Semantics → Improve Q&A → Generate Tests/Synthetic Data → Identify Gaps → New Scenarios]

1) “Business Questions as Unit Tests” (Non-negotiable)
Treat each key business question as a semantic unit test.

Example question families (forecasting / commercial)
Performance: “How is Spain performing vs expectation?”

Drivers: “Why did sales dip in week 32?”

Funnel: “Why are patients dropping after step X?”

Competition: “Did competitor Y shift share or just pull-forward?”

Execution: “Is this field issue, access issue, or supply issue?”

How the system uses them
For each question, the system maintains:

Required entities (Market, Brand, Channel, Segment, Time)

Required relationships (e.g., promo intensity → demand, with lag/threshold)

Required evidence types (claims, TRx, channel inventory, formulary)

Allowed reasoning templates (causal vs correlational)

Expected outputs (narrative + attribution + confidence + recommended next data)

Scorecard per question (simple, visible to users):

Coverage: do we have the concepts?

Grounding: do we have the data links?

Consistency: do experts agree?

Actionability: did it recommend next-best action/data?

This becomes your “ontology health dashboard.”

2) Synthetic Data: Use It as a Diagnostic, Not a Toy
Synthetic data is valuable, but only if it’s tied to semantic gap detection.

Three practical uses
Scenario simulation for learning

Generate plausible market time series + events (launch, shortage, price change)

Ask experts to diagnose “what happened” → harvest heuristics

Unit test scaffolding

When real data is missing or restricted, synthetic data lets you validate:

entity extraction

reasoning pathways

attribution logic

prompt templates

Robustness testing

Create adversarial cases: noisy signals, confounders, missing weeks

Ensure the agent doesn’t over-claim causality

Guardrail: synthetic data should never be presented as “realistic truth,” only as test harness / training arena.

3) Ingestion: Make It an “Evidence Supply Chain”
You want to add:

data files (tables, extracts)

schemas/catalogs

meeting notes

PMRs, clinical reports, unstructured docs

This should be treated as an evidence pipeline with provenance.

Ingestion pipeline (minimum viable)
Step A: Classify

What is this? (schema, KPI table, narrative note, report)

What domain? (forecasting, access, supply, safety, etc.)

Step B: Extract

Entities (Spain, product, channel, payer, cohort)

Events (launch, formulary win/loss, supply disruption)

Measures (TRx, NBRx, WAC, adherence)

Claims/Assertions (“Drop due to stocking issue”)

Step C: Link

Map extracted entities to canonical ontology IDs

Attach evidence: source, date, confidence, owner

Step D: Curate

Propose new nodes/edges/constraints

Route to “expert confirmation” via the game (lightweight)

Key design choice:
Everything new is “suggested” until validated by either:

multiple corroborating sources, or

a credentialed expert interaction

4) What the User Sees (This is how you drive adoption)
As they play, they see a live “Answerability” bar improving.

Example UI moments:

“You just taught the system a new driver: promo saturation threshold.”

“Coverage for ‘Why did Spain dip?’ improved from 62% → 74%.”

“Remaining gaps: lacks channel inventory and payer restriction events.”

“Upload a weekly inventory file or tag notes from the Spain WBR.”

This makes ontology visibly useful.

5) The Architecture You Want (Keep it disciplined)
You’re building 4 assets in parallel:

Semantic Layer

Ontology + relationships + constraints

Versioned by domain and maturity

Evidence Layer

Linked sources (docs, tables, notes)

Provenance + permissions + trust scores

Prompt/Policy Layer

Few-shots, reasoning templates, allowed actions

“Do/Don’t” guardrails per use case

Test Harness

Business questions as unit tests

Synthetic scenarios as regression tests

If any of these is missing, the system won’t scale.

6) The Sharp Risk (and the fix)
Risk: This becomes a “knowledge graph project with a chatbot skin.”
Fix: Ruthless product principle:

If a new ontology element does not improve at least one business-question test, it doesn’t ship.

That keeps it grounded, measurable, and adoption-friendly.

Bottom line
You’re describing a system that:

learns expert judgment through play

curates semantics through evidence ingestion

proves readiness through business-question tests

uses synthetic data to stress-test and fill gaps

That’s coherent — and it’s exactly the kind of “data-for-agents” platform that can become reusable ZS IP.

If you want the next artifact, I’d produce:

a 1-page product spec with the 4 layers above

a starter set of 12 “unit test” questions for forecasting + commercial analytics

the ontology delta schema (node/edge/constraint/evidence) so the system can version it cleanly

You said:
how would the output be used in client projects? will this be shipped as sonething that sits on top of their data products?
ChatGPT said:
BLUF:
Yes — the output should be shipped as a semantic + reasoning layer that sits on top of client data products, not as a replacement for them. Its value in client work is that it compresses time-to-insight, de-risks agent deployment, and makes expert judgment portable.

Below is the clean, client-ready framing.

1. What Actually Gets “Shipped” to a Client
Not the game. Not the raw ontology.

What gets deployed is a Client Semantic & Agent Readiness Package, consisting of four concrete assets:

Asset	What it is	Why clients care
Domain Ontology Slice	Concepts, relationships, constraints relevant to the client’s use cases	Makes AI “understand” their business
Business-Question Tests	Canonical questions + success criteria	Proves AI readiness in business terms
Prompt & Policy Pack	Few-shots, reasoning templates, guardrails	Safe, consistent agent behavior
Evidence Mappings	Links to client data products, schemas, docs	Grounded answers, auditability
This is configuration + IP, not a new system of record.

2. Where It Sits in the Client Architecture
You want a thin semantic + reasoning layer, not another data platform.

[Visual: Layered architecture]

Client Source Systems
  ↓
Client Data Products / Lakehouse / EDMA
  ↓
Semantic & Ontology Layer (Your output)
  ↓
Agent & Insight Layer (Copilots, Workflows)
  ↓
Business Users
Key principle:

Client owns the data. ZS provides the meaning.

3. How It Integrates with Client Data Products
Each ontology element is bound, not duplicated.

Example
Ontology concept: MarketPerformanceDip

Linked to:

Fact table: weekly_sales

Dimensions: market, product, channel

Events: inventory_shortage, payer_restriction

Documents: WBR notes, PMR excerpts

Confidence rules: minimum data completeness, allowed causal claims

This means:

No re-modeling

No re-ingestion

No new master data layer

Just semantic bindings + reasoning rules.

4. How It’s Used in Live Client Work (Concrete Scenarios)
Use Case 1: Faster Diagnostic Analyses
Before

Analyst manually pulls data

Hypotheses differ by team

Insights vary week to week

After

Agent uses ontology to:

Ask the right diagnostic questions

Pull the right data products

Explain “why” with traceable logic

ZS teams shift from data prep → judgment & recommendation.

Use Case 2: Safe Client-Facing Agents
Instead of:

“Here’s a generic LLM on your data”

You ship:

Pre-validated reasoning paths

Explicit “can/cannot say” constraints

Domain-specific confidence thresholds

This is critical for:

Forecasting

GTM recommendations

Executive Q&A

Regulated narratives

Use Case 3: Rapid Reuse Across Accounts
You don’t start from zero each time.

Example:

Base Commercial Ontology (ZS IP)

Client-specific extensions:

markets

brands

channels

data availability

Result:

60–70% reuse

30–40% client tuning

Massive leverage for ZS

5. How This Shows Up in a Statement of Work
This is important for monetization.

You don’t sell “ontology.”
You sell AI-Ready Decision Enablement.

Typical SOW components:

Semantic Readiness Assessment
→ Run business-question tests against client data

Ontology & Prompt Configuration
→ Bind concepts to client data products

Agent Enablement
→ Deploy copilots / workflows safely

Knowledge Flywheel (Optional)
→ Continuously refine semantics with client SMEs

This aligns perfectly with:

EDMA

Next-gen reporting

Scaled AI offerings

6. What This Is Not
Be explicit internally and with clients.

❌ Not a new MDM
❌ Not a new data lake
❌ Not a standalone SaaS replacing client tools
❌ Not “ZS owning client data”

✅ It is:

A semantic accelerator

A control plane for agents

A portable layer of ZS judgment

7. The One-Liner for Clients
Use this verbatim if you want:

“We don’t replace your data products — we sit on top of them to encode business meaning, so AI can reason and act the way your best experts do.”

Bottom Line
Yes — ship this as a layered capability that plugs into client data products.
That makes it:

Architecturally non-threatening

Commercially clean

Scalable across clients

Aligned with ZS’s role as a trusted operator, not a platform vendor

If you want next, I can:

Draft a client-facing architecture slide

Define what’s ZS IP vs client-specific

Or help you position this differently for IT vs Business vs Medical stakeholders

You said:
can you make a vision document for this idea
ChatGPT said:
Agentic Semantic Readiness Platform – Vision

Vision Document: Agentic Semantic Readiness Platform
1. Vision (North Star)
Build a living semantic layer that captures, tests, and operationalizes expert judgment so AI systems can reason, explain, and act like ZS’s best practitioners—safely, repeatedly, and at scale.

This platform turns tacit expertise into agent-ready intelligence, continuously proving its value by answering real business questions better over time.

In one line: A system that learns how experts think, not just what data exists—and makes that thinking deployable across clients.

2. The Problem We Are Solving
The Reality Today
Client data products are technically strong but semantically thin

LLMs can summarize but cannot reliably reason or diagnose

Expert knowledge lives in people’s heads, decks, and meeting rooms

Each client engagement re-discovers the same heuristics, edge cases, and constraints

The Core Gap
AI fails not because of lack of data, but because meaning, judgment, and constraints are implicit.

Without explicit semantics:

Agents hallucinate confidently

Explanations lack traceability

Recommendations feel generic

Risk increases in regulated or high-stakes decisions

3. The Big Idea
Create an Agentic Semantic Readiness Platform that:

Elicits expert judgment through play and scenarios (not documentation)

Codifies that judgment into ontologies, rules, and prompts

Continuously tests readiness using real business questions

Binds semantics to client data products without replacing them

Ontology is not the output. Improved answerability and actionability are.

4. Core Design Principles
Ontology Emerges from Use
No big-bang modeling. Semantics evolve from scenarios, failures, and questions.

Business Questions as Unit Tests
Every semantic element must improve the system’s ability to answer a real question.

Expert-Friendly by Default
Experts teach by reacting, choosing, and explaining—not by defining schemas.

Thin, Non-Invasive Architecture
Sits on top of client data products; never becomes a system of record.

Evidence-Backed Reasoning
Every assertion is linked to data, documents, or expert validation.

5. What the Platform Does (Functional Vision)
5.1 The Scenario & Game Engine
A conversational, agentic experience where users:

Respond to realistic scenarios and counterfactuals

Compare explanations and trade-offs

Reveal heuristics, confidence, and boundaries

What gets captured:

Concepts (e.g., promo saturation, access friction)

Relationships (causal, conditional, contextual)

Constraints (when reasoning is allowed vs prohibited)

Confidence signals and disagreement

5.2 Continuous Ontology & Semantic Layer
A living knowledge structure containing:

Domain concepts and hierarchies

Relationships and inference paths

Business rules and guardrails

Prompt fragments and few-shot exemplars

Versioned by:

Domain (forecasting, commercial, supply, etc.)

Maturity

Client context

5.3 Business-Question Test Harness
Canonical questions the system must answer, such as:

“How is Spain performing vs expectation?”

“Why did sales dip last quarter?”

“Where are patients dropping from the funnel—and why?”

Each question defines:

Required entities and data

Allowed reasoning patterns

Expected outputs (narrative, attribution, confidence)

The platform tracks answerability scores over time.

5.4 Synthetic Data & Scenario Simulation
Synthetic data is used to:

Simulate edge cases and stress-test reasoning

Train agents when real data is unavailable

Identify semantic gaps early

Synthetic data is always labeled as test-only, never as truth.

5.5 Multi-Modal Ingestion & Evidence Supply Chain
The platform ingests:

Structured data tables and schemas

Data catalogs and metrics definitions

Meeting notes and working docs

PMRs, clinical reports, unstructured text

From each source it:

Extracts entities, events, measures, and claims

Links them to existing ontology nodes

Attaches provenance, confidence, and ownership

6. What Gets Deployed to Clients
Clients do not receive the game engine.

They receive a Semantic & Agent Readiness Package:

Domain-specific ontology slice

Business-question tests

Prompt and policy bundles

Mappings to client data products

This layer enables:

Safer copilots

Faster diagnostics

Consistent executive narratives

Reusable agent workflows

7. Architectural Positioning
Layered Model:

Client systems and data products remain unchanged

The platform provides a semantic and reasoning layer above them

Agents and copilots consume this layer

Key principle: Client owns data. ZS provides meaning.

8. Value for ZS
Strategic Value
Turns expertise into reusable IP

Creates a differentiated agentic offering

Strengthens EDMA and Scaled AI propositions

Economic Value
60–70% reuse across clients

Faster time-to-value per engagement

New annuity-style offerings (semantic refresh, agent upgrades)

Cultural Value
Experts become teachers of AI, not documentation writers

Knowledge compounds instead of resetting per project

9. What This Is Not
Not a data lake

Not an MDM system

Not a generic knowledge graph

Not a standalone SaaS replacing client platforms

It is a semantic accelerator and agent control plane.

10. Success Metrics
Reduction in time to answer core business questions

Increase in answer consistency across teams

Agent accuracy and confidence calibration

Reuse rate of semantic assets across clients

Expert participation and engagement

11. The End State
A future where:

ZS deploys AI agents that reason with institutional memory

Client work starts at judgment, not data wrangling

Expertise compounds across years and accounts

ZS doesn’t just deliver insights. It delivers thinking—at scale.

Done. I’ve created a full vision document in canvas that’s ready to be socialized with senior ZS leadership or shaped into a client-facing POV.

How I’d suggest using it next (pragmatically):

Internal alignment:

Share as a thinking artifact with EDMA + Scaled AI leads

Pressure-test sections 5–7 (what ships vs what stays internal)

Externalization path:

Strip Sections 5.1 (Game Engine) and parts of 8 → create a clean client POV

Next artifact (if useful):

A 1-slide executive vision

A 2-slide architecture + value narrative

Or a Phase 1 MVP scope (what we build in 90 days, what we explicitly don’t)

If you want, tell me who the audience is (ZS LT, a client CIO/CMO, or an internal product council), and I’ll tailor the next cut ruthlessly for that room.