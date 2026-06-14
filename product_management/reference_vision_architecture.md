# Onto_Wiz Vision & Agentic Architecture Reference

**Created:** 2026-02-02
**Author:** Team CORTEX (architecture analysis session)
**Purpose:** Concrete reference for what Onto_Wiz produces, how agents consume it, and where it sits in ZS's agentic future.

---

## What Onto_Wiz IS (One Sentence)

Onto_Wiz is a **pharma reasoning database** — it captures expert judgment through low-friction games, governs it through auditable workflows, and exposes it as structured knowledge that AI agents call when they need to make safe, evidence-backed decisions.

---

## What Onto_Wiz Is NOT

- Not a chatbot or copilot (it's the knowledge layer BEHIND copilots)
- Not a BI tool (it provides the "why" behind the "what" that BI shows)
- Not a data warehouse (it stores judgment + evidence, not raw data)
- Not a standalone app end-users open (it's infrastructure, like a database)

---

## The Intelligence Packet — Onto_Wiz's Core Output

An Intelligence Packet is a structured JSON response that answers a business question with governed, evidence-backed reasoning. It is the primary deliverable of the system.

### Concrete Example

**Query:** "Why is Keytruda losing share in the Northeast?"

```json
{
  "packet_id": "IP-2026-00847",
  "query": "share decline drivers for Keytruda in Northeast US",
  "generated_at": "2026-03-15T14:32:01Z",
  "confidence": 0.82,

  "signal": {
    "metric": "TRx_share",
    "entity": "Keytruda",
    "geography": "Northeast US",
    "change": -3.2,
    "period": "Q4-2025 vs Q3-2025",
    "severity": "MODERATE"
  },

  "sources": [
    { "entity": "Aetna Northeast", "contribution_pct": 42, "type": "payer" },
    { "entity": "Mount Sinai Network", "contribution_pct": 28, "type": "account" },
    { "entity": "Community Oncology NE", "contribution_pct": 18, "type": "account" }
  ],

  "drivers": [
    {
      "driver": "Formulary restriction tightened (Step therapy added)",
      "confidence": 0.88,
      "pattern_id": "PAT-0231",
      "evidence": ["Aetna formulary update 2025-Q3", "Field report FR-4821"],
      "judgment_type": "EMPIRICAL"
    },
    {
      "driver": "Competitor biosimilar launched at 40% discount",
      "confidence": 0.74,
      "pattern_id": "PAT-0087",
      "evidence": ["WAC pricing data 2025-10", "Claims data NE region"],
      "judgment_type": "CAUSAL_HYPOTHESIS"
    }
  ],

  "recommendations": {
    "brand": "Prioritize Aetna contracting renegotiation",
    "field": "Deploy MSLs to Mount Sinai with updated efficacy data",
    "access": "Submit exception request with real-world evidence package",
    "medical": "Accelerate KEYNOTE-X subgroup analysis for NE demographics"
  },

  "guardrails_applied": [
    "No demand claim without NBRx evidence (GUARD-012)",
    "No pricing comparison without WAC source citation (GUARD-003)"
  ],

  "evidence_trace": {
    "patterns_matched": 3,
    "evidence_items_used": 7,
    "sources_hard": 4,
    "sources_soft": 3,
    "oldest_evidence": "2025-08-12",
    "newest_evidence": "2026-01-30"
  },

  "audit": {
    "patterns_by": ["Dr. Sarah Chen (oncology KOL)", "Mike Torres (access SME)"],
    "approved_by": "Jennifer Walsh (curator)",
    "traversal_depth": 3,
    "guardrails_checked": 5,
    "time_to_generate_ms": 187
  }
}
```

### What Makes This Different From a ChatGPT Answer

| Aspect | Raw LLM | Onto_Wiz Intelligence Packet |
|--------|---------|------------------------------|
| Source | Training data (stale, generic) | Governed SME knowledge (current, client-specific) |
| Evidence | None — sounds confident, may hallucinate | Hard refs: formulary docs, field reports, claims data |
| Guardrails | None — will overclaim freely | Active: "cannot claim X without evidence Y" |
| Audit trail | None | Full: who contributed, who approved, when, why |
| Confidence | Implied (always sounds certain) | Explicit: 0.82 with breakdown per driver |
| Recommendations | Generic best practices | Cross-functional, context-scoped, guardrail-checked |

---

## How Agents Consume Intelligence Packets

### Flow: ZS Copilot (Internal)

```
Consultant types: "Why is Keytruda losing share in the Northeast?"
        │
        ▼
Claude/GPT agent receives the question
        │
        ▼
Agent recognizes: this needs pharma market knowledge
        │
        ▼
Agent calls Onto_Wiz via MCP:
    get_intelligence_packet(
        signal="TRx_share decline",
        entity="Keytruda",
        geography="Northeast US"
    )
        │
        ▼
Onto_Wiz internally:
    1. Finds matching patterns in the knowledge graph
    2. Retrieves evidence for each driver
    3. Checks guardrails (what CAN'T be claimed)
    4. Scores confidence
    5. Assembles the Intelligence Packet
        │
        ▼
Agent receives the packet (JSON above)
        │
        ▼
Agent formats into human answer WITH citations:

    "Keytruda's 3.2% share decline in NE appears driven by two
     factors:

     1. Aetna added step therapy in Q3 (88% confidence, based on
        their formulary update and field report FR-4821)
     2. A biosimilar launched at 40% WAC discount (74% confidence,
        based on pricing data)

     For the brand team, I'd recommend prioritizing the Aetna
     contracting renegotiation and deploying MSLs to Mount Sinai
     with updated efficacy data.

     Note: I cannot make demand claims without NBRx evidence
     per guardrail GUARD-012."
```

### MCP Tools Exposed to Agents

```
get_intelligence_packet(signal, entity, geography)
    → Full Intelligence Packet for a business question

check_guardrail_violations(claim, evidence_ids)
    → What guardrails would this claim violate?

find_matching_patterns(signals, context)
    → Which expert patterns apply to this situation?

get_evidence_for_driver(driver_id)
    → Hard/soft evidence with reliability scores

get_entity_relationships(entity_id, depth)
    → Graph neighborhood: what's connected to this entity?

validate_recommendation(action, guardrail_ids)
    → Is this recommendation safe to surface?
```

---

## Full ZS Agentic Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE CAPTURE (How knowledge gets IN)                │
│                                                                                 │
│  ┌──────────────┐   ┌──────────────────┐   ┌───────────────────┐               │
│  │  SME Game     │   │ Document Ingestion│   │  Expert Mode      │               │
│  │  (5-min       │   │ (PDFs, reports,   │   │  (Direct entity/  │               │
│  │  scenarios)   │   │  field notes,     │   │   rule editing    │               │
│  │              │   │  claims data)     │   │   by KOLs)        │               │
│  └──────┬───────┘   └────────┬──────────┘   └────────┬──────────┘               │
│         │                    │                       │                           │
│         ▼                    ▼                       ▼                           │
│  ┌──────────────────────────────────────────────────────────────┐                │
│  │                    DELTA PIPELINE                            │                │
│  │  Everything becomes a proposal → reviewed → approved/rejected│                │
│  │  (blast radius routing, 3-tier HITL, audit trail)           │                │
│  └──────────────────────────┬───────────────────────────────────┘                │
│                             │ approved                                           │
│                             ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────┐                │
│  │                ONTO_WIZ KNOWLEDGE GRAPH                      │                │
│  │                                                              │                │
│  │  Patterns ─── "When you see X signals in Y context,         │                │
│  │               the driver is usually Z (conf: 0.85)"         │                │
│  │                                                              │                │
│  │  Guardrails ─ "Never claim X without evidence Y"            │                │
│  │                                                              │                │
│  │  Evidence ─── Hard data (claims, TRx) + Soft (field notes)  │                │
│  │               with reliability scores + provenance           │                │
│  │                                                              │                │
│  │  Entities ─── Brands, HCPs, Payers, Indications,            │                │
│  │               Competitors, Territories, Signals              │                │
│  │                                                              │                │
│  │  Actions ──── Cross-functional playbooks                     │                │
│  │               (brand, field, access, medical)                │                │
│  └──────────────────────────┬───────────────────────────────────┘                │
│                             │                                                    │
└─────────────────────────────┼────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────┼────────────────────────────────────────────────────┐
│              KNOWLEDGE ACCESS (How knowledge gets OUT)                            │
│                             │                                                    │
│              ┌──────────────┴──────────────┐                                     │
│              │   ONTO_WIZ API LAYER        │                                     │
│              │                             │                                     │
│              │  ┌───────┐ ┌─────┐ ┌─────┐ │                                     │
│              │  │  MCP  │ │REST │ │GrQL │ │                                     │
│              │  │Server │ │ API │ │     │ │                                     │
│              │  └───┬───┘ └──┬──┘ └──┬──┘ │                                     │
│              └──────┼────────┼───────┼────┘                                     │
│                     │        │       │                                            │
│    MCP Tools exposed to agents:                                                  │
│    ├─ get_intelligence_packet(signal, entity, geo)                               │
│    ├─ check_guardrail_violations(claim, evidence)                                │
│    ├─ find_matching_patterns(signals, context)                                   │
│    ├─ get_evidence_for_driver(driver_id)                                         │
│    ├─ get_entity_relationships(entity_id, depth)                                 │
│    └─ validate_recommendation(action, guardrails)                                │
│                                                                                  │
└─────────────┬────────────────┬───────────────┬───────────────────────────────────┘
              │                │               │
              ▼                ▼               ▼
┌─────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│  ZS COPILOT     │ │ CLIENT PLATFORM  │ │ AUTOMATED AGENTS     │
│  (Internal)     │ │ (Client-facing)  │ │ (Workflows)          │
│                 │ │                  │ │                      │
│  Claude/GPT     │ │ CogniMesh or     │ │ Brand Review Bot:    │
│  agent used by  │ │ custom dashboard │ │  Runs weekly,        │
│  ZS consultants │ │ at the client    │ │  pulls signals,      │
│                 │ │ site             │ │  generates packets,  │
│  "Why is share  │ │                  │ │  flags anomalies     │
│   dropping?"    │ │ Shows "why" not  │ │                      │
│                 │ │ just "what" in   │ │ Regulatory Drafting: │
│  Agent calls    │ │ their BI layer   │ │  Agent assembles     │
│  Onto_Wiz MCP,  │ │                  │ │  safety narratives   │
│  gets grounded  │ │ Onto_Wiz feeds   │ │  using evidence from │
│  answer with    │ │ the semantic     │ │  knowledge graph     │
│  evidence +     │ │ definitions +    │ │                      │
│  citations      │ │ driver analysis  │ │ Launch Readiness:    │
│                 │ │ behind their     │ │  Agent checks all    │
│                 │ │ metrics          │ │  patterns + guardrails│
│                 │ │                  │ │  for go/no-go        │
└────────┬────────┘ └────────┬─────────┘ └──────────┬───────────┘
         │                   │                      │
         ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    THE HUMAN RECEIVES                            │
│                                                                 │
│  Not: "I think the decline might be due to competition..."      │
│       (LLM hallucination, no evidence, no audit)                │
│                                                                 │
│  But: "Share declined 3.2% driven by Aetna step therapy         │
│        (conf: 0.88, evidence: formulary update + field report)  │
│        and biosimilar launch (conf: 0.74, WAC pricing data).    │
│        Recommend: renegotiate Aetna contract, deploy MSLs.      │
│        Guardrail: cannot claim demand impact without NBRx."     │
│                                                                 │
│  → Auditable. Governed. Evidence-backed. Repeatable.            │
└─────────────────────────────────────────────────────────────────┘
```

---

## How CogniMesh / External BI Connects

CogniMesh is a **semantic layer for BI** — it makes dashboards smarter.
Onto_Wiz is the **reasoning backbone** underneath.

```
CogniMesh Dashboard                    Onto_Wiz
─────────────────                      ────────
Shows: "Keytruda TRx down 3.2%"   →   Calls: get_intelligence_packet()
       (the WHAT — from data)          Returns: drivers, evidence,
                                                confidence, guardrails
                                                (the WHY — from knowledge)

Shows: "Revenue metric definition" →   Calls: get_entity_relationships()
       (what IS revenue here?)         Returns: governed metric definition
                                                with provenance

Shows: "Recommended actions"       →   Calls: find_matching_patterns()
       (what should we DO?)            Returns: cross-functional playbook
                                                with guardrail constraints
```

CogniMesh answers **"what happened?"** from data.
Onto_Wiz answers **"why did it happen and what should we do?"** from governed expert knowledge.

---

## The Value Chain

```
SME expertise (tacit, in people's heads)
    → captured via game (low friction, 5 min)
    → governed via delta model (safe for pharma)
    → stored as patterns + evidence (structured, queryable)
    → exposed via MCP/API (any agent can call it)
    → consumed by copilots, dashboards, bots (many surfaces)
    → delivered to humans as grounded, auditable answers
```

Every ZS engagement that feeds the graph makes every future engagement better.
That's the flywheel.

---

## Three User-Facing Surfaces

| Surface | Who Uses It | What They See |
|---------|-------------|---------------|
| **SME Game** | Consultants, KOLs, medical affairs | 5-min scenario — feels like a case discussion, not data entry |
| **Curator Dashboard** | Knowledge engineers, data stewards | Delta queue, graph explorer, conflict resolution, audit logs |
| **Intelligence Packets** (API) | AI agents, copilots, dashboards | Structured answers with evidence, confidence, guardrails applied |

---

## Success/Failure Criteria

**Succeeds if:**
1. SMEs actually play the game (adoption > friction)
2. Intelligence Packets measurably outperform raw LLM answers
3. Knowledge compounds across engagements (client #11 starts pre-loaded)
4. Audit trails satisfy pharma compliance requirements

**Fails if:**
1. SMEs don't contribute (knowledge management adoption problem)
2. Raw LLMs are "good enough" for the use cases (the 80% problem)
3. The cold start problem isn't solved (empty graph = useless system)
4. Architecture complexity becomes a maintenance burden

**The architecture is sound. The adoption loop is the risk.**

---

_End of Vision Reference — Team CORTEX_
