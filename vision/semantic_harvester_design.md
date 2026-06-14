# Semantic Harvester: The Game Design
## 1. Core Concept
The "Semantic Harvester" is a game played by Domain Experts (e.g., Commercial Directors, Medical Leads). 
**Goal:** Review "Dark Data" signals that the AI has flagged as "Ambiguous" and codify the logic to resolve them.
**Outcome:** Every move in the game creates a new `Inference Rule` in the `commercial.yaml` ontology.

## 2. The Game Loop
1.  **The Trigger:** System flags a cluster of Dark Data (e.g., "3 Rep Notes + 1 Rumor") with Low Confidence (<60%).
2.  **The Scenario (The 'Level'):** User is presented with the "Situation Room" UI.
    *   *Context:* "Account: St. Mary's. Brand: OncoVance."
    *   *Evidence:* Cards showing the Rep Notes and Rumors.
3.  **The Action:** User chooses a "Strategic Interpretation".
    *   *Option A:* "This is a Competitor Lock-out."
    *   *Option B:* "This is a Genuine Budget Crisis."
    *   *Option C:* "Ignore (Noise)."
4.  **The Codification (The 'Harvest'):**
    *   System asks: *"Why? What evidence tipped the scale?"*
    *   User clicks the specific "Evidence Cards" (e.g., "The Finance Memo").
    *   **System Generates:** A new JSONLogic Rule (e.g., `IF HardEvidence AND BudgetBarrier THEN ...`).

## 3. The "Golden Scenarios" (Prototype Levels)

### Level 1: The Smoke & Mirrors (Competitor Lock-out)
*   **Situation:** High volume of "Budget Objections" at a rich Academic Center.
*   **Hidden Signal:** A single MSL note about a "MegaCorp bundled deal".
*   **Correct Move:** Identify "Lock-out Risk".
*   **Lesson:** "Budget objections often mask competitor contracting."

### Level 2: The Hard Stop (Genuine Financial Crisis)
*   **Situation:** "Budget Objections" at a mid-tier IDN.
*   **Hidden Signal:** Public News Report about "Hospital Layoffs".
*   **Correct Move:** Identify "Genuine Constraint".
*   **Lesson:** "Public financial health data trumps rep sentiment."

### Level 3: The Clinical Trojan Horse (Safety Signal)
*   **Situation:** Sudden drop in 2L prescriptions. Reps report "Physician Preference".
*   **Hidden Signal:** Medical Inquiry log showing 3 questions about "Rash" in the last month.
*   **Correct Move:** Identify "Emerging Safety Signal".
*   **Lesson:** "Clinical concerns often masquerade as preference or access issues."

## 4. UI Design (The "Glass Box")
### View: "The Situation Room"
*   **Left Panel (The Field):** Interactive Map of the Account.
*   **Center Panel (The Evidence):** A stack of "Signal Cards". 
    *   Cards have tags: `#Rumor`, `#Finance`, `#CRM`.
    *   User can *Drag & Drop* cards into a "Theory Builder" slot.
*   **Right Panel (The Ontology):** Real-time visualization of the Knowledge Graph updating as the user makes choices.
