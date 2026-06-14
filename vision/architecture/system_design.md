# System Architecture: Agentic Semantic Readiness Platform

## 1. Core Design Philosophy: "The Onion"
To ensure the system can **expand outwards** (new domains like R&D, Supply Chain) and **go deeper** (granular logic), we use a layered "Onion" architecture. The core is abstract, and domains are "skins" wrapped around it.

### Layer 0: The Kernel (Meta-Model)
*   **Responsibility:** Defines the physics of the universe.
*   **Components:**
    *   `Node`: Base class for everything.
    *   `Edge`: Base class for relationships.
    *   `Constraint`: Logic that forbids or requires connections.
    *   `Evidence`: Link to source data.
*   **Constraint:** NO domain logic here (e.g., "Prescription" is unknown at this level).

### Layer 1: Domain Semantics (The Skins)
*   **Responsibility:** Defines specific business worlds.
*   **Modules:**
    *   `Commercial`: (Our starting point) Brands, HCPs, Payers.
    *   `Medical`: (Future) Clinical Trials, Adverse Events.
    *   `Access`: (Future) Payer Archetypes, Contract Tiers.

### Layer 2: The "Dark Data" Refinery
*   **Responsibility:** Turning unstructured chaos into structured propositions.
*   **Pipeline:**
    1.  **Ingestion & Chunking:** OCR PDFs, parse emails.
    2.  **Embedding (pgvector):** Store semantic vectors of chunks.
    3.  **Extraction Agent:** LLM (Gemini/GPT) prompts: "Extract <Subject> <Predicate> <Object> tuples that match Layer 1 definitions."
    4.  **Proposition Store:** Staging area for "Proposed Facts" (e.g., "Rep Note says Dr. Smith hates the new protocol").

### Layer 3: The "Game" (Interaction Layer)
*   **Responsibility:** Human validation of Layer 2 propositions.
*   **Mechanism:**
    *   System: "My confidence is 60% on this 'Access Barrier'. Is it real?"
    *   Expert: "Yes, and it applies to the whole Region." (Refines the rule).

### Layer 4: The Agentic Interface (The Product)
*   **Responsibility:** Serving "Ready" knowledge to client agents.
*   **API:**
    *   `GET /reasoning/explain`: "Why did sales drop?" -> Returns subgraph of evidence + logic.
    *   `POST /agent/guardrail`: "Can I say X?" -> Checks Constraints in Layer 0/1.

## 2. Hybrid Knowledge Store (PostgreSQL + pgvector)
We unify the stack to simplify deployment.

### Schema Concept
```sql
-- 1. The Graph (Neo4j-style structure in SQL)
CREATE TABLE nodes (
    id UUID PRIMARY KEY,
    type VARCHAR(50), -- 'Brand', 'HCP'
    properties JSONB  -- {'name': 'Keytruda', 'stage': 'Launch'}
);

CREATE TABLE edges (
    source_id UUID,
    target_id UUID,
    type VARCHAR(50), -- 'PRESCRIBES', 'RESTRICTS'
    properties JSONB, -- {'tier': 2}
    PRIMARY KEY (source_id, target_id, type)
);

-- 2. The Evidence (Vector Store)
CREATE TABLE evidence (
    id UUID PRIMARY KEY,
    content TEXT,
    embedding VECTOR(1536), -- pgvector
    source_metadata JSONB   -- {'file': 'Q3_Strategy.pdf', 'author': 'Jane Doe'}
);

-- 3. The Link (Grounding)
CREATE TABLE knowledge_grounding (
    node_id UUID,
    evidence_id UUID,
    confidence SCORE,
    verified_by_user_id UUID
);
```

## 3. Dark Data Pipeline Workflow
1.  **User Upload:** Uploads `Field_Report_Q3_Germany.pdf`.
2.  **System:**
    *   Splits into chunks.
    *   Embeds into `evidence` table.
    *   Runs `ExtractionAgent`: Finds "Competitor X launching Biosimilar in Q4".
3.  **Ontology Update (Provisional):**
    *   Creates tentative Node: `Event(BiosimilarLaunch)` linked to `Brand(CompetitorX)`.
    *   Tags as `unverified`.
4.  **Game Trigger:**
    *   Next time a Commercial Director logs in, the Game asks: "We detected a signal of a Q4 Biosimilar launch. Is this credible?"
    *   Director: "Yes, confirm." -> Node becomes `verified`.
