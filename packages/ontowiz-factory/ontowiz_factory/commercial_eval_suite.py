"""The commercial_analytics agent-lift eval suite (Tier B).

Each case is a real diagnostic scenario whose governed answer lives in one of the
19 decision-heuristics compiled into the ``commercial_analytics`` pack (from
``ontology/commercial.yaml``). The suite is built to *measure* pack value, not to
flatter it:

* **Coverage** — at least one case per governed heuristic, so a run exercises the
  whole pack rather than a flattering subset.
* **Distinctive tokens** — each ``must_contain`` is the specific governed term the
  heuristic supplies (``displacement``, ``pathway``, ``biomarker``, ``lockout``,
  ``reimbursement`` …), each verified to actually appear in the pack content so
  the with-pack path can produce it. Generic terms a blind model volunteers
  anyway are avoided.
* **No leaked answers** — the required term never appears verbatim in its own
  question (enforced by a test). The model must *supply* the term from knowledge
  or the pack, not echo it back. This is what makes the suite hard.
* **Distractor traps** — several scenarios put a plausible wrong cause on the
  surface (a competitor launch, an apparent demand drop) when the governed
  diagnosis is something else, so a blind model is tempted toward the wrong call.

Scoring note (see ``evals.score_answer``): matching is word-boundary and the lift
metric is driven by ``must_contain``; ``must_not_contain`` only sharpens pass/fail
(it does not move the lift number), and it is used sparingly — many governed
verdicts name-and-negate the alternative cause ("X, not Y"), which would make a
naive forbid of "Y" backfire.
"""

from __future__ import annotations

from ontowiz_spec import EvalCase

# ── Core coverage: one case per governed heuristic ──────────────────────────
_CORE: list[EvalCase] = [
    EvalCase(
        id="lift_safety_signal",
        name="volume drop that is really a safety signal",
        question=(
            "A brand's prescription volume fell sharply in the same weeks that physicians "
            "began raising unsolicited questions about adverse events and tolerability. "
            "Payer coverage and the competitive set were unchanged. Most likely root cause?"
        ),
        must_contain=["safety"],
        must_not_contain=["pricing"],
    ),
    EvalCase(
        id="lift_supply_disruption",
        name="supply-driven volume loss",
        question=(
            "National units dispensed dropped about 30% over two weeks. Demand indicators "
            "and payer policy were unchanged, but the manufacturer disclosed a fill-finish "
            "interruption at its plant. Diagnose the volume loss."
        ),
        must_contain=["supply"],
    ),
    EvalCase(
        id="lift_budget_crisis",
        name="genuine budget crisis vs bargaining",
        question=(
            "A large account says it simply cannot fund adding the product this year, and "
            "audited filings confirm the health system is in severe fiscal distress. Is the "
            "objection a real constraint or a bargaining posture?"
        ),
        must_contain=["budget"],
    ),
    EvalCase(
        id="lift_pa_access_barrier",
        name="prior-auth / formulary access friction",
        question=(
            "Field teams report a jump in rejected scripts that now need extra paperwork and "
            "a failed cheaper-drug trial before approval, right after the payer changed its "
            "coverage rules. What is creating the friction?"
        ),
        must_contain=["formulary"],
    ),
    EvalCase(
        id="lift_formulary_exclusion",
        name="payer exclusion, not field execution",
        question=(
            "A brand's volume fell across an entire payer's book of business at once, "
            "immediately after that payer moved it to a non-preferred position. Leadership "
            "wants to blame the sales team — what is the actual root cause?"
        ),
        must_contain=["formulary"],
    ),
    EvalCase(
        id="lift_copay_accumulator",
        name="copay accumulator abandonment",
        question=(
            "Patients are abandoning therapy around mid-year and new-start scripts are "
            "sliding. The dominant plan recently adopted a policy that stops manufacturer "
            "copay assistance from counting toward the patient's deductible. What's driving it?"
        ),
        must_contain=["accumulator"],
    ),
    EvalCase(
        id="lift_reimbursement_squeeze",
        name="buy-and-bill reimbursement squeeze",
        question=(
            "For a physician-administered injectable, practices are steering patients to "
            "hospital outpatient sites and in-office volume is falling, following cuts to "
            "what Medicare pays per dose. What is the driver?"
        ),
        must_contain=["reimbursement"],
    ),
    EvalCase(
        id="lift_competitive_displacement",
        name="competitive displacement",
        question=(
            "A brand began losing share right after a direct rival launched a new product and "
            "cut its price hard in the same indication. Diagnose the share loss."
        ),
        must_contain=["displacement"],
    ),
    EvalCase(
        id="lift_340b_erosion",
        name="340B margin erosion",
        question=(
            "Net revenue is compressing even though unit volume is flat. The share of units "
            "flowing through disproportionate-share and covered-entity hospital channels has "
            "been climbing. What is eroding the net revenue?"
        ),
        must_contain=["340b"],
    ),
    EvalCase(
        id="lift_biosimilar_erosion",
        name="biosimilar erosion",
        question=(
            "An originator biologic is steadily losing share with sustained downward price "
            "pressure, starting soon after lower-cost interchangeable versions of the same "
            "molecule launched. Diagnose."
        ),
        must_contain=["biosimilar"],
    ),
    EvalCase(
        id="lift_competitor_lockout",
        name="lockout masquerading as a budget objection",
        question=(
            "An account cites affordability to justify not adding the product, and at the same "
            "time there is an unverified rumor that a rival is offering deep discounts. There "
            "is no hard financial evidence of distress. What is most likely really going on?"
        ),
        # NOTE: no must_not_contain here — the correct lockout answer legitimately
        # says "not a budget crisis", so forbidding "crisis" would penalise it.
        must_contain=["lockout"],
    ),
    EvalCase(
        id="lift_demand_erosion",
        name="genuine demand erosion",
        question=(
            "New-to-brand scripts are falling and prescribers are disengaging — fewer calls "
            "accepted, key opinion leaders cooling. There was no payer or distribution change. "
            "What does this indicate?"
        ),
        must_contain=["demand"],
    ),
    EvalCase(
        id="lift_launch_stall",
        name="launch stall, not market rejection",
        question=(
            "Six months post-launch, uptake is well below plan. Surveys show many target "
            "physicians still do not know the product exists, and reps have not reached much "
            "of the territory. Is the market rejecting it, or something else?"
        ),
        must_contain=["awareness"],
    ),
    EvalCase(
        id="lift_field_execution_gap",
        name="field execution gap",
        question=(
            "One territory badly trails its neighbors on volume. That territory has had a "
            "vacant rep seat and thin call coverage for a quarter, while market conditions "
            "match the neighboring territories. Root cause?"
        ),
        must_contain=["execution"],
    ),
    EvalCase(
        id="lift_rebate_trap",
        name="rebate trap",
        question=(
            "A brand cannot flex its net price and margins are thinning because it is bound to "
            "a payer agreement with steep share-based penalties and exclusivity clauses. "
            "Diagnose the constraint."
        ),
        must_contain=["rebate"],
    ),
    EvalCase(
        id="lift_channel_shift",
        name="channel shift vs true demand loss",
        question=(
            "Reported retail-pharmacy volume fell, yet total patient demand looks unchanged "
            "and a specialty pharmacy was just added as a dispensing route. Is true demand "
            "actually declining, or is something else going on?"
        ),
        must_contain=["channel"],
    ),
    EvalCase(
        id="lift_guideline_shift",
        name="guideline-driven displacement",
        question=(
            "An oncology brand is losing share across many institutions simultaneously, right "
            "after a major clinical recommendation body revised its standard-of-care advice. "
            "Root cause?"
        ),
        must_contain=["guideline"],
    ),
    EvalCase(
        id="lift_biomarker_testing_gap",
        name="biomarker testing gap",
        question=(
            "A targeted oncology therapy has soft uptake. In its eligible population, rates of "
            "the diagnostic test that identifies candidates are low, so few patients are being "
            "flagged as eligible. What is suppressing uptake?"
        ),
        must_contain=["biomarker"],
    ),
    EvalCase(
        id="lift_pathway_exclusion",
        name="institutional pathway exclusion",
        question=(
            "At several large cancer centers, new starts for a brand dropped after each "
            "institution's treatment-protocol committee removed it from the preferred "
            "regimen. What happened?"
        ),
        must_contain=["pathway"],
    ),
]

# ── Distractor traps: the surface cue points at the wrong cause ─────────────
_TRAPS: list[EvalCase] = [
    EvalCase(
        id="trap_safety_over_competitor",
        name="competitor launch as decoy for a safety signal",
        question=(
            "A brand's volume slid the same month a generic rival launched — but also the same "
            "month clinicians began reporting unexpected side effects and a journal letter "
            "flagged a possible risk. Which is the more likely primary driver?"
        ),
        must_contain=["safety"],
    ),
    EvalCase(
        id="trap_supply_over_demand",
        name="apparent demand softness that is really supply",
        question=(
            "Volume is down and the brand team assumes prescriber appetite softened. But there "
            "were no leading indicators of that — instead a contract manufacturer had a "
            "sterility hold on a lot. What is the real cause?"
        ),
        must_contain=["supply"],
    ),
    EvalCase(
        id="trap_channel_over_demand",
        name="measurement artifact mistaken for demand loss",
        question=(
            "A brand's tracked units in its main data source dropped 20%. The brand also just "
            "moved fulfillment to a specialty distributor that is not fully captured in that "
            "source. Before declaring a real loss of patient uptake, what should be suspected?"
        ),
        must_contain=["channel"],
    ),
    EvalCase(
        id="trap_formulary_over_field",
        name="payer action blamed on the sales force",
        question=(
            "Volume fell in lockstep across one payer's members the week it raised the "
            "product's tier and added restrictions. The VP wants to put the local reps on a "
            "performance plan. Is field effort the real problem, or something upstream?"
        ),
        must_contain=["formulary"],
    ),
    EvalCase(
        id="trap_demand_over_access",
        name="clinical preference loss mistaken for an access issue",
        question=(
            "Scripts are declining and the team's first instinct is a coverage problem. But "
            "coverage is unchanged; what shifted is prescribers voicing less clinical "
            "enthusiasm and thought leaders stepping back. What does this point to?"
        ),
        must_contain=["demand"],
    ),
    EvalCase(
        id="trap_guideline_over_competitor",
        name="broad simultaneous share loss: guideline, not the rival",
        question=(
            "An oncology brand lost share suddenly and broadly. A rival did launch last year, "
            "but the drop lines up precisely with a revised consensus treatment recommendation "
            "from a major body. What is the primary driver?"
        ),
        must_contain=["guideline"],
    ),
    EvalCase(
        id="trap_rebate_over_price_war",
        name="contract lock mistaken for a simple price war",
        question=(
            "Margins are thinning and the brand cannot drop its net price to answer a rival. "
            "The team blames the competitor's discounting, but the brand is locked into a payer "
            "agreement with share-based penalties and exclusivity terms. What is the deeper "
            "constraint?"
        ),
        must_contain=["rebate"],
    ),
]

# ── Forecasting slice: the forward-looking module (ontology/commercial/forecasting.yaml) ──
# Each governed term is present in its heuristic's served content and absent from
# its own question (both enforced by tests). These extend coverage to the
# forecasting slice; the live agent-lift for 0.3.0 is a separate measurement step.
FORECASTING_EVAL_CASES: list[EvalCase] = [
    EvalCase(
        id="lift_loe_erosion_curve",
        name="post-LOE erosion curve, not a point estimate",
        question=(
            "A brand just lost market exclusivity and a wave of lower-cost substitutes "
            "entered. Leadership wants one number for next year. How should the post-"
            "exclusivity volume decline be modelled, and what shape should the forecast "
            "take across the coming quarters?"
        ),
        must_contain=["plateau"],
    ),
    EvalCase(
        id="lift_demand_sensing_divergence",
        name="leading indicators decoupled from shipped volume",
        question=(
            "Leading indicators — new-patient starts, diagnosis rates, prescribing intent — "
            "are moving one way while shipped volume trends another. The trended forecast "
            "still says steady. What does the gap between the leading signals and shipped "
            "volume imply for the forecast?"
        ),
        must_contain=["divergence"],
    ),
    EvalCase(
        id="lift_analog_launch_trajectory",
        name="launch tracking below its benchmark curve",
        question=(
            "A newly launched brand is tracking below the comparable prior-launch curve the "
            "team agreed to benchmark against. It is still early. How should the launch "
            "forecast be reset, and against what reference?"
        ),
        must_contain=["analog"],
    ),
    EvalCase(
        id="lift_scenario_sensitivity",
        name="one driver dominates the forecast",
        question=(
            "A single uncertain driver — the net-price assumption — swings the forecast more "
            "than the entire base-case change year over year. Stakeholders are asking for one "
            "point estimate. What should be delivered instead?"
        ),
        must_contain=["sensitivity"],
    ),
]

COMMERCIAL_EVAL_CASES: list[EvalCase] = [*_CORE, *_TRAPS, *FORECASTING_EVAL_CASES]
