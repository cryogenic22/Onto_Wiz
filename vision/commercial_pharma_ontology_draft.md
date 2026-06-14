# Commercial Pharma Ontology (Seed Draft)

## 1. Top-Level Concepts (Meta-Model)
*   **Entity:** Real-world object (Person, Place, Product).
*   **Event:** Something that happens at a point in time (Script, Call, Launch).
*   **Constraint:** A rule that limits an action (Regulation, Policy).
*   **Evidence:** Source of truth (File, Database Row, Hearsay).

## 2. Commercial Domain Layer

### 2.1 Market & Product
*   **Brand:** The commercial product (e.g., *Keytruda*, *Humira*).
    *   *Properties:* LaunchDate, LifecycleStage (Launch, Growth, Maturity, LoE).
*   **Indication:** The approved use case (e.g., *NSCLC 1st Line*, *Crohn's Disease*).
*   **Competitor:** Rival brand or generic.
*   **Asset Class:** Small Molecule, Biologics, Cell & Gene.

### 2.2 Customer & Stakeholder
*   **HCP (Health Care Professional):**
    *   *Subtypes:* Prescriber, KOL (Key Opinion Leader), Nurse Educator.
    *   *Attributes:* Decile (1-10), Specialty, AdoptionSegment (Innovator, Laggard).
*   **HCO (Health Care Organization):**
    *   *Subtypes:* Hospital, IDN (Integrated Delivery Network), Private Practice.
*   **Payer:**
    *   *Subtypes:* Commercial, Medicare, Medicaid, PBM (Pharmacy Benefit Manager).

### 2.3 Access & Flow
*   **Formulary Status:**
    *   *Values:* Preferred, Non-Preferred, Blocked, T1/T2/T3.
*   **Restriction:**
    *   *Ex:* PA (Prior Auth), Step Edit (Fail First).
*   **Pathway:** Clinical guideline flow.

### 2.4 "Dark Data" & Insight Nodes (The Value Layer)
*This is where we capture non-structured insights.*

*   **Sentiment:** The emotional tone of an HCP towards a Brand.
    *   *Source:* Rep interactions.
*   **Access Barrier:** A specific friction point reported by field.
    *   *Ex:* "System X requires fax forms for Indication Y."
*   **Competitor Rumor:** Unverified intel.
    *   *Ex:* "Rep says Competitor Z is discounting by 40%."
*   **Patient Journey Gap:** Drop-off point.
    *   *Ex:* "Patients dropping after 2nd infusion due to infusion center distance."

## 3. Relationships (The Glue)

### Standard (Data-Driven)
*   `HCP` **PRESCRIBES** `Brand` (Volume: X)
*   `Payer` **COVERS** `Brand` (Tier: 2)
*   `HCP` **AFFILIATED_WITH** `HCO`

### Semantic (Expert-Derived)
*   `Indication` **DRIVES** `Growth` (Context: "Launch Phase")
*   `Competitor Event` **THREATENS** `Brand Share` (Logic: "If biosimilar launch")
*   `Access Barrier` **CAUSES** `Treatment Discontinuation` (Confidence: High)

## 4. Inference Rules (Examples)
*   **Rule 1 (The "Launch" Heuristic):**
    *   `IF (Brand.Stage == "Launch") AND (HCP.Segment == "Innovator") THEN (Strategy = "High Frequency Visit")`
*   **Rule 2 (The "Access" Heuristic):**
    *   `IF (Region == "Germany") AND (Brand.Type == "Orphan") THEN (Expect "AMNOG Assessment" within 6 months)`
