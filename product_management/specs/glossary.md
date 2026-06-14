# Glossary: Onto_Wiz Terms

## Core Concepts

| Term | Definition |
|:---|:---|
| **Judgment Layer** | The living ontology that captures SME reasoning patterns, guardrails, and evidence relationships |
| **Delta Model** | Architecture where every mutation is a proposal that must be reviewed before becoming active |
| **Intelligence Packet** | The structured output of a traversal, containing drivers, confidence, evidence, and actions |
| **SME Game** | Scenario-based interaction where experts answer questions, unknowingly creating ontology artifacts |

---

## Artifacts

| Term | Definition |
|:---|:---|
| **JudgmentPattern** | A reusable reasoning heuristic that maps signals to likely drivers (e.g., "TRx dip + stable NBRx → access friction") |
| **Guardrail** | A safety rule that blocks certain claims unless specific evidence exists |
| **ActionTemplate** | A recommended action tied to specific hypotheses and contexts |
| **Delta** | A proposed change to any artifact, pending review |

---

## Evidence & Confidence

| Term | Definition |
|:---|:---|
| **EvidenceItem** | A piece of supporting information with source, reliability class, and extracted claims |
| **Reliability Class** | Evidence grade: HARD (verified data), SOFT (credible reports), RUMOR (unverified) |
| **ConfidenceEngine** | Computes credible confidence from evidence, priors, conflicts, and freshness |
| **Corroboration** | Multiple independent sources supporting the same claim |

---

## Graph Concepts

| Term | Definition |
|:---|:---|
| **GraphStore** | The reasoning graph containing nodes (entities, signals, hypotheses) and edges (supports, contradicts) |
| **Edge** | A relationship between two nodes (e.g., "TRx_dip supports access_friction") |
| **Traversal** | Walking the graph to answer a question, respecting guardrails and policies |
| **Blast Radius** | The scope of impact if a delta is promoted (LOW, MEDIUM, HIGH, CRITICAL) |

---

## SME Game Terms

| Term | Definition |
|:---|:---|
| **ReasoningEvent** | The structured output from one SME game session |
| **BrandProfile** | Context for a brand: TA, lifecycle, channel, market archetype |
| **Disconfirming Logic** | What would change the SME's mind ("if X, then reconsider Y") |
| **Pattern Recognition** | SME's indication of how often they've seen this situation |
| **Common Mistake** | What people typically get wrong (becomes a guardrail) |

---

## Semantic Store Terms

| Term | Definition |
|:---|:---|
| **CanonicalTerm** | The preferred term for a concept (e.g., "Prior_Authorization") |
| **Synonym** | Alternative terms for the same concept (e.g., "Prior Auth") |
| **Alias** | Abbreviation or shorthand (e.g., "PA") |
| **Anti-synonym** | Terms that should NOT be treated as equivalent |
| **Taxonomy** | Hierarchical relationship (HCP → Prescriber → Oncologist) |

---

## Functional Domains

| Domain | Description |
|:---|:---|
| **Commercial** | Field sales, marketing, brand management |
| **Market Access** | Payer strategy, formulary, PA/step edits |
| **Clinical** | Trials, endpoints, safety data |
| **Medical Affairs** | KOL engagement, MSL activities |
| **Supply Chain** | Manufacturing, distribution, inventory |
| **Pharmacovigilance** | Safety monitoring, adverse events |

---

## Context Dimensions

| Term | Definition |
|:---|:---|
| **Therapeutic Area (TA)** | Disease area: Oncology, CNS, Immunology, etc. |
| **Lifecycle** | Brand maturity: Pre-launch, Launch, Growth, Maturity, LOE |
| **Channel** | Distribution: Specialty, Retail, Hospital |
| **Asset Class** | Drug type: Small molecule, Biologic, CAR-T, Gene therapy |
| **Market Archetype** | Competitive structure: Monopoly, Duopoly, Fragmented |

---

## Governance Terms

| Term | Definition |
|:---|:---|
| **Risk Class** | How risky the judgment is: Advisory, Decision Support, Restricted |
| **Judgment Type** | Nature of judgment: Empirical, Causal Hypothesis, Normative |
| **Review Cycle** | How often artifacts must be re-validated (30, 90, 365 days) |
| **Decay** | How confidence decreases over time |

---

## Agent Behavior

| Term | Definition |
|:---|:---|
| **Agent Mode** | What the agent can do: Explore, Apply, Recommend, Explain |
| **Hard Stop** | Conditions that halt agent execution (low confidence, missing evidence, guardrail hit) |
| **Traversal Policy** | Rules governing agent behavior (depth limits, confidence thresholds) |

---

## Metrics & Signals

| Term | Definition |
|:---|:---|
| **TRx** | Total prescriptions |
| **NBRx** | New to brand prescriptions |
| **PA** | Prior authorization |
| **Share** | Market share |
| **Decile** | Prescriber categorization by volume |

---

## Pharma-Specific

| Term | Definition |
|:---|:---|
| **KOL** | Key Opinion Leader |
| **HCP** | Health Care Professional |
| **REMS** | Risk Evaluation and Mitigation Strategy |
| **Hub** | Patient support services hub |
| **Step Edit** | Payer requirement to try cheaper drugs first |
| **LOE** | Loss of Exclusivity (patent cliff) |
