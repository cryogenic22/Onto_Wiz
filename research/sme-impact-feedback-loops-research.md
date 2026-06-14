# Deep UX Research: Showing SMEs the Downstream Impact of Their Contributions in Knowledge Systems

## 1. Contribution Impact Visualization

### What Works in the Wild

**Wikipedia's XTools ecosystem** is the most mature example of showing contributors their downstream impact. The [XTools Edit Counter](https://www.mediawiki.org/wiki/XTools/Edit_Counter) provides detailed statistics per editor: total edits, edits by namespace, administrative actions, and pages created. The [XTools PageInfo gadget](https://www.mediawiki.org/wiki/XTools/PageInfo_gadget) shows, below every article header, the number of revisions, number of editors, number of page watchers, and -- critically -- **pageviews in the past 30 days**. This means an editor can see the articles they worked on and directly observe readership volume. The [Page History tool](https://www.mediawiki.org/wiki/XTools/Page_History) provides authorship attribution measured by character count, showing exactly how much of the current article is "yours."

**Stack Overflow's reputation system** awards +10 for an upvoted answer, +15 for an accepted answer, and displays these points next to every answer you post. Research from [Helsinki's "Signals Matter" study](https://tuhat.helsinki.fi/ws/portalfiles/portal/161057963/3308558.3313583.pdf) found that certain non-trivial badges and reputation scores positively correlate with both popularity and impact, and that "costly-to-earn" signals qualitatively differentiate highly impactful users from merely popular ones. The downvoting system costs the downvoter reputation too, which means signals of quality carry weight -- users must feel strongly to spend their own capital.

**GitHub's contribution graph** uses a heatmap of green squares showing commit frequency over 365 days. Tools like [GitHub Unwrapped](https://dev.to/github/your-github-year-in-review-10-fun-ways-to-visualize-your-contributions-392o) extend this with year-in-review summaries showing most productive days, times, and a Christmas tree of issues. The 3D isometric Chrome extension turns the flat heatmap into a city-like skyline. [Graphite Insights](https://graphite.com/guides/github-statistics-and-analytics) adds metrics like median review response time and average review cycles to merge.

### Psychological Mechanisms

Three mechanisms emerge from research:

1. **Self-Determination Theory (Autonomy, Competence, Relatedness)**: Wikipedia's barnstar system and the ["Thank" button](https://en.wikipedia.org/wiki/Help:Notifications/Thanks) directly address relatedness. A [Harvard study by Jana Gallus](https://www.higherlogic.com/blog/the-wikipedia-effect-why-people-volunteer/) found that retention was **20% higher after one month** for editors who received a badge, and 14% higher after two months -- not because of the badge itself but because of what it represents: community belonging.

2. **Loss Aversion and Commitment Bias**: Duolingo's streak system demonstrates this powerfully. [Duolingo's own research](https://blog.duolingo.com/how-duolingo-streak-builds-habit/) shows the streak leverages loss aversion (Kahneman and Tversky), and the Streak Wager increased Day-7 retention by **+14%**. Offering Weekend Amulets made users 4% more likely to return and 5% less likely to lose their streak. For an ontology system, this translates to: once an SME has a contribution history, showing them that history creates commitment to maintain it.

3. **Positive Data Framing (the Spotify Wrapped effect)**: [Spotify Wrapped](https://medium.com/design-bootcamp/why-were-hooked-on-spotify-wrapped-the-perfect-blend-of-ux-and-psychology-b4aa06c9b81f) transforms raw listening data into identity statements ("You're in the top 1% of Taylor Swift fans"). Over 156 million users engaged with Wrapped in 2022, and 60 million stories were shared. The key is **framing data as achievement, not metrics**. For an SME: not "you made 23 ontology contributions" but "your clinical trial expertise shaped how 47 intelligence packets explained regulatory barriers this quarter."

### Concrete Interaction Design for Onto_Wiz

**The "Impact Ripple" Dashboard**:
- A personal home screen showing three tiers of impact:
  - **Direct**: "You contributed 12 judgment calls this month" (with a small sparkline trend)
  - **Propagated**: "Your patterns appeared in 47 intelligence packets" (with expandable list)
  - **Validated**: "3 other experts independently confirmed your access friction judgment" (with names, if appropriate)
- Each tier is a card that can be tapped to expand. The default view is a single sentence per tier. This follows the [2-3 layer progressive disclosure principle](https://www.nngroup.com/articles/progressive-disclosure/).

**Weekly "Your Knowledge This Week" email/notification** (modeled on LinkedIn's "Your post was viewed by X people" notification):
- Subject line: "Your access friction pattern was used 8 times this week"
- Body: One-paragraph summary of downstream usage, one specific example, and a link to see full details
- [LinkedIn's engineering team](https://engineering.linkedin.com/blog/2018/05/concourse--generating-personalized-content-notifications-in-near) found that shortening the feedback loop from hours to minutes via mobile notifications dramatically increased engagement rates

---

## 2. Living Knowledge Visualization

### What the Research Shows

The core challenge is making an abstract ontology feel like something that is **growing because of you**. [Cambridge Intelligence's guide to graph visualization UX](https://cambridge-intelligence.com/graph-visualization-ux-how-to-avoid-wrecking-your-graph-visualization/) identifies three deadly visualization patterns: **hairballs** (too many connections), **snowstorms** (too many disconnected nodes), and **starbursts** (one node connected to everything). All three must be avoided.

The most effective approach, per [yFiles' knowledge graph visualization guide](https://www.yfiles.com/resources/how-to/guide-to-visualizing-knowledge-graphs), is interactive expansion: start with top-level parent groups and allow users to dive deeper through interactive expansion, with automatic layout algorithms keeping things arranged when groups expand or merge. [MIT Lincoln Laboratory and Tufts University research](https://arxiv.org/html/2304.01311v4) found that the critical challenge for KG practitioners is bridging the gap between creation and exploration -- most tools serve one but not the other.

### Metaphors That Work

**The City-Building Metaphor** (strongest candidate for Onto_Wiz):
- Each domain of expertise is a "district" (e.g., Market Access, Clinical Development, Regulatory)
- Each concept is a "building" that grows taller with more expert validation and usage
- Connections between concepts are "roads" that get wider with more traffic (usage in intelligence packets)
- New contributions cause buildings to "rise" with a subtle animation
- The SME's own contributions are highlighted in a distinct color (their "signature")
- This maps directly to GitHub's 3D isometric contribution view but applied to knowledge rather than code

**The Ecosystem Metaphor**:
- Contributions are seeds that grow into plants
- Plants that get validated by other experts bloom
- Plants that get used in intelligence packets bear fruit
- The garden grows over time, with seasonal "health" checks
- Dead branches (unused patterns) gently fade but remain visible

**The Constellation Metaphor** (best for showing connections):
- Each expert's contributions are stars
- When two experts' contributions connect (e.g., both identify access friction as a driver), a line connects those stars into a constellation
- Over time, well-validated patterns become named constellations
- The SME can see their stars in the night sky of collective intelligence

### Concrete Interaction Design

**The "Knowledge Pulse" Visualization**:
- A real-time, low-fidelity heartbeat animation on the dashboard showing the ontology's activity
- NOT a full graph view (which overwhelms). Instead: a simplified radial view where the center is "core ontology" and rings expand outward
- The SME's contributions pulse gently in their signature color when they are being used downstream
- Clicking any pulsing node shows: who contributed it, when, how many times it has been used, and what it connects to
- New additions animate in from the edge with a gentle "landing" effect (not jarring -- think iOS notification animations)
- This avoids the [common pitfalls identified by Cambridge Intelligence](https://cambridge-intelligence.com/graph-visualization-ux-how-to-avoid-wrecking-your-graph-visualization/): overcrowding (solved by abstraction), unclear labels (solved by tooltips on hover), unfamiliar interactions (solved by using established gesture conventions)

---

## 3. Feedback Loops in Expert Systems

### The Cadence Problem

[Smashing Magazine's research on feedback loops](https://www.smashingmagazine.com/2013/02/designing-great-feedback-loops/) identifies a critical principle: "The longer it takes for feedback to arrive, the less it will influence future decisions." This is operant conditioning's "immediacy" principle and is related to hyperbolic discounting. But for expert systems, there is a tension: expert judgments may take weeks or months to be validated by downstream usage.

The [KCS (Knowledge-Centered Service) framework](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/020/050) addresses this with the "Evolve Loop": knowledge domain experts extract learning from patterns in the system, and the closed-loop nature of the workflow makes it easy to monitor and maintain effectiveness through continual sharing of best practices.

[Knoco's knowledge cycle model](http://www.nickmilton.com/2018/02/feedback-loops-in-knowledge-cycle.html) identifies three feedback points: (1) after finding -- did you find what you needed? (2) after applying -- was the knowledge actually applied? (3) after problem resolution -- how much difference did the knowledge make? Each feeds different information back to the contributor.

### The Right Cadence: Three Tiers

Based on the research, here is a concrete cadence model for when an SME says "access friction is the likely driver":

**Tier 1: Immediate Acknowledgment (within seconds)**
- "Your judgment has been captured: access friction flagged as likely driver for [scenario]"
- This is the equivalent of Wikipedia's "Your edit has been published" -- immediate confirmation that the system heard you
- Visual: a subtle toast notification with a checkmark

**Tier 2: Integration Notification (within 24-48 hours)**
- "Your access friction judgment has been woven into the [Market Access / US Oncology] pattern library"
- Show what it connects to: "This links to 4 existing patterns around payer dynamics and formulary barriers"
- This is the equivalent of getting your first upvote on Stack Overflow -- someone (or the system) has validated that your contribution fits

**Tier 3: Downstream Impact Report (weekly digest + milestone triggers)**
- Weekly: "This week, your access friction pattern was referenced in 3 intelligence packets for [Client X context]"
- Milestone: "Your pattern has now been used 25 times -- you are one of the top contributors to the Market Access domain"
- Validation: "2 other senior analysts independently flagged access friction as a driver in similar scenarios this month"
- This is the equivalent of Stack Overflow's "Your answer was accepted" + "X people found this helpful"

**Tier 4: Retrospective Impact (quarterly)**
- Spotify Wrapped-style: "This quarter, your expertise shaped 142 intelligence outputs. Your most influential contribution was [access friction pattern], which appeared in work for 7 different client engagements."
- Calibration feedback: "Of the 15 patterns you flagged as 'likely drivers,' 12 were independently confirmed by other experts (80% validation rate)"

### The Granularity Problem

The feedback must answer these questions without requiring the SME to dig:
1. **Was I heard?** (Tier 1 -- answered immediately)
2. **Was I useful?** (Tier 2 -- answered within days)
3. **Did I matter?** (Tier 3 -- answered weekly)
4. **Am I getting better?** (Tier 4 -- answered quarterly)

Each tier should be a single sentence by default, expandable to full detail. This follows the [Interaction Design Foundation's principle](https://www.interaction-design.org/literature/topics/progressive-disclosure) that progressive disclosure moves from "abstract to specific" and from "simple to complex actions."

---

## 4. "Your Knowledge Matters" UX Patterns -- Lessons from Prediction Markets

### How Prediction Markets Show Forecaster Impact

**Metaculus** provides each forecaster with a personal track record. [Metaculus's own documentation](https://www.metaculus.com/help/prediction-resources/) describes their aggregation method: the "Metaculus prediction" gives more weight to forecasters with strong track records. They are introducing global leaderboards and a new "Consumer view" that emphasizes reasoning transparency alongside the existing "Forecaster view." This dual-view approach -- one for the expert, one for the consumer of their expertise -- is directly relevant to Onto_Wiz.

**[Brier.fyi](https://brier.fyi/)** is the gold standard for personal calibration visualization. It shows:
- A **calibration plot**: predicted probabilities (x-axis) vs. observed frequencies (y-axis), with perfect calibration being the diagonal line
- **Brier scores** for every market, plus logarithmic, spherical, and relative scores
- Benchmarks: 0.25 is a coin flip, 0.15 is superforecaster-level, 0.10-0.20 is aggregated prediction market level
- Time-series view of how your score evolves

The [Good Judgment Project](https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/) found that superforecasters had a calibration of 0.01 -- the average difference between their probability and actual frequency was just one percentage point. Their accuracy actually decreased when predictions were rounded, proving that granularity matters even at the tails.

### Translation to Ontology Contribution

The prediction market model translates surprisingly well to expert ontology contribution. Instead of "your 70% prediction resolved to true," the system tracks:

**Calibration equivalent**: "When you flag something as a 'likely driver,' how often do other experts independently confirm it?"
- Show this as a simple accuracy percentage, not a Brier score
- Visualization: a confidence gauge showing "Your pattern-flagging accuracy: 82% (based on 45 contributions)"
- Benchmark: "Average expert in this domain: 71%"

**Impact equivalent**: "How much did your contribution move the aggregate?"
- In Metaculus, the community prediction shifts when a strong forecaster weighs in. Similarly: "Before your contribution, the system had no pattern linking access friction to this therapy class. Now it does, and it has been used in 23 outputs."
- This is the equivalent of showing a prediction market price moving after your trade

**Track record over time**:
- A simple line chart showing contributions per month and validation rate per month
- Not a full Brier decomposition -- SMEs are not statisticians
- Instead: "Your contributions this quarter were confirmed at a higher rate than last quarter (85% vs. 72%)"
- Trend arrows (up/down) are sufficient for most users

### Concrete Interaction Design

**The "Expert Scorecard"** (quarterly, Spotify Wrapped-style):
```
Your Q3 2025 Knowledge Impact
================================
Contributions: 34 judgment calls across 6 domains
Validation Rate: 82% (up from 75% last quarter)
Most Impactful: "Access friction as primary barrier in specialty pharmacy"
  -- Used in 47 intelligence packets
  -- Independently confirmed by 5 other experts
Unique Insight: You were the first to flag "prior auth burden
  as a proxy for access friction" -- this is now a standard pattern
Domains You Shaped: Market Access (primary), Payer (secondary)
```

This draws directly from:
- Spotify Wrapped's positive framing and identity reinforcement
- Metaculus's calibration tracking and benchmarking
- Stack Overflow's "your answer helped X people" impact messaging
- GitHub Unwrapped's activity summaries

---

## 5. Progressive Revelation of Complexity

### Research Findings

[Nielsen Norman Group](https://www.nngroup.com/articles/progressive-disclosure/) established the foundational principle: progressive disclosure reduces cognitive load by moving from abstract to specific. [SAP's Fiori design system for Explainable AI](https://experience.sap.com/fiori-design-web/explainable-ai/) is the most directly applicable commercial example. Their approach to explaining AI supplier rankings uses layered disclosure:

- **Level 0**: A simple icon or a few words (e.g., a green checkmark with "High confidence")
- **Level 1**: A one-sentence explanation ("Access friction was flagged as the primary driver because 3 experts identified it independently")
- **Level 2**: Supporting detail with emphasis on important parts ("Expert A flagged it on [date] in [context]. Expert B confirmed it in [scenario]. Usage data shows 47 downstream references.")
- **Level 3 (optional)**: The raw ontology structure for the technically curious

[ACM's research on progressive disclosure for algorithmic transparency](https://dl.acm.org/doi/abs/10.1145/3374218) found a counterintuitive result: **too much transparency upfront can actually harm user understanding**. Users benefit from initially simplified feedback that hides potential system errors and helps them build working heuristics about system operation. Only after they have a mental model should deeper details be revealed.

[Userpilot's analysis of progressive disclosure in SaaS products](https://userpilot.com/blog/progressive-disclosure-examples/) recommends keeping disclosure to **2-3 layers maximum** with clear navigation paths. More than three layers is a sign that content needs reorganizing.

### How to Apply This to Ontology Terms

The SME should never see `owl:ObjectProperty`, `rdfs:subClassOf`, or `skos:broader`. Instead:

**Layer 0 -- Natural Language Surface (default view)**:
```
"Access friction is a type of Market Barrier, related to Payer Dynamics
 and Prior Authorization Burden."
```
This is a sentence. No graph, no technical notation. Just English.

**Layer 1 -- Visual Relationship Map (one click away)**:
```
[Access Friction] ---is a type of---> [Market Barrier]
        |
        |---related to---> [Payer Dynamics]
        |---related to---> [Prior Auth Burden]
        |---flagged by---> [Expert A, Expert B, Expert C]
        |---used in---> [47 intelligence packets]
```
This is a mini-graph with natural language labels. No ontology notation. Think of Google's Knowledge Panel -- when you search for a person, you see structured information in a card, not a database schema.

**Layer 2 -- "How This Works" (for the curious, behind a "Show me how" link)**:
```
"Behind the scenes, your judgment was captured as a relationship in our
 knowledge graph. 'Access friction' is formally classified as a subtype
 of 'Market Barrier' in the ontology. When intelligence agents look for
 explanations of market dynamics, they traverse this relationship to find
 relevant patterns. Your specific judgment that 'access friction is the
 likely driver' was stored with a confidence score and has been validated
 by peer confirmation."
```
This is a paragraph of plain English explaining the mechanism, inspired by [Wolfram Alpha's step-by-step computational explanations](https://writings.stephenwolfram.com/2023/01/wolframalpha-as-the-way-to-bring-computational-knowledge-superpowers-to-chatgpt/).

**Layer 3 -- Raw Structure (hidden by default, accessible via "View technical details")**:
```
onto:AccessFriction rdf:type onto:MarketBarrier ;
    onto:relatedTo onto:PayerDynamics ;
    onto:relatedTo onto:PriorAuthBurden ;
    onto:flaggedBy :ExpertA, :ExpertB, :ExpertC ;
    onto:confidenceScore "0.87"^^xsd:float ;
    onto:validationCount "5"^^xsd:integer .
```
Only for developers or ontology engineers. Never shown to SMEs unless they explicitly request it.

### The Google Search Model

Google Search's "About this result" panel is the closest analogy. When you click the three dots next to a search result, you see: why this result was shown, the source's Wikipedia entry, and when Google first indexed it. This is progressive disclosure of search algorithm reasoning -- exactly the pattern Onto_Wiz needs for ontology reasoning.

---

## 6. Social Proof and Collective Intelligence Visualization

### Research Foundation

[Nielsen Norman Group's social proof article](https://www.nngroup.com/articles/social-proof-ux/) identifies the core principle: people follow the actions of others when making decisions, placing weight on those actions to assume "the correct decision." [The Interaction Design Foundation](https://www.interaction-design.org/literature/article/making-use-of-the-crowd-social-proof-and-the-user-experience) distinguishes between expert social proof (authority endorsement) and wisdom of crowds (popularity signals), noting we are more likely to act on information communicated by a credible, authoritative source.

[Strava's community research](https://sensortower.com/blog/beyond-workouts-stravas-social-transformation-of-fitness-tracking) demonstrates the flywheel: 83% of respondents were more motivated to exercise because of Strava's community. Users open the app over 35 times per month (versus under 15 for competitors) driven primarily by social features. The mechanism: seeing a friend's run in your feed makes you think "I'd love to get out there too."

However, there is a critical caution from [UX Planet's social proof analysis](https://uxplanet.org/how-to-design-a-social-proof-user-experience-9eac26a825c3): groupthink risk. People are less likely to conform to a group's behavior if they perceive themselves as better advised about a situation. For SMEs -- who are experts -- you must frame social proof as **peer validation**, not conformity pressure.

### Concrete Patterns for Onto_Wiz

**Pattern 1: Peer Convergence Notification**
```
"3 other Market Access experts independently flagged access friction
 as a driver in specialty pharma scenarios this quarter."
 [See who] [See their reasoning]
```
Key design choice: show the count first, names on click. This protects independence (the SME sees the convergence without being anchored to specific names) while allowing exploration. This follows prediction market best practice where forecasters see the aggregate before seeing individual predictions.

**Pattern 2: Usage Counter (Stack Overflow-style)**
```
"Your access friction pattern"
 Used in: 47 intelligence packets this month
 Confirmed by: 5 experts
 First contributed: March 2025
 [View full history]
```
This is a compact card that can appear in the dashboard or as a tooltip when hovering over the pattern in any context. The numbers do the talking -- no persuasive language needed.

**Pattern 3: Domain Health Indicator**
```
"Market Access domain: 89% coverage (up from 72% last quarter)"
 Your contribution: 14% of new patterns
 Top contributors: [You], [Expert B], [Expert C]
 Most active area: Payer Dynamics (23 new patterns)
```
This shows collective progress while highlighting individual contribution. It is the ontology equivalent of GitHub's repository contribution graph showing who contributed what percentage.

**Pattern 4: Consensus Strength Indicator**
When showing a pattern to any user of the system:
```
[Access friction as primary driver]
 Confidence: HIGH (5 experts, 47 uses)
 ████████████░░ 85% expert agreement
```
This serves two audiences: consumers of the intelligence see that it is well-validated, and the contributing SMEs see that their judgment has been absorbed into the system's confidence.

**Pattern 5: The "First Spotter" Badge**
```
"You were the first expert to identify prior auth burden as
 a proxy for access friction. This pattern has since been
 confirmed by 4 other experts and used in 31 intelligence packets."
```
This taps into Wikipedia's barnstar psychology -- [research shows](https://blog.reputationx.com/wikipedia-barnstar) that barnstars motivate contributors by acknowledging specific achievements, and the "Editor of the Week" recognition drives retention. For SMEs, being recognized as the originator of a pattern that proves valuable is a powerful intrinsic motivator.

### Anti-Patterns to Avoid

1. **Do not show raw counts without context**: "47 uses" means nothing without "this month" or "in specialty pharma engagements"
2. **Do not create leaderboards between SMEs**: Unlike Duolingo where competition is the point, expert knowledge contribution should not be a zero-sum game. Show individual progress, not rankings. [Research on gamification pitfalls](https://medium.com/design-bootcamp/when-and-how-is-gamification-harmful-8e37c076d4f5) warns that poorly designed gamification alienates users who do not buy into it
3. **Do not show validation before it exists**: If no other expert has confirmed a pattern yet, say "Awaiting peer confirmation" rather than showing zero confirmations, which feels like rejection
4. **Do not notify too frequently**: [LinkedIn's Air Traffic Controller system](https://engineering.linkedin.com/blog/2018/05/concourse--generating-personalized-content-notifications-in-near) found that excessive notifications cut member complaints in half and doubled engagement when properly throttled. The cadence model from Section 3 (immediate/48h/weekly/quarterly) is the right rhythm

---

## Summary of Key Design Principles

| Principle | Source Platform | Application to Onto_Wiz |
|---|---|---|
| Immediate acknowledgment | Wikipedia "edit published" | Toast notification when judgment is captured |
| Delayed impact metrics | Stack Overflow "X people helped" | Weekly digest of downstream usage |
| Identity-reinforcing summaries | Spotify Wrapped | Quarterly "Your Knowledge Impact" report |
| Calibration tracking | Metaculus/Brier.fyi | Validation rate over time (not Brier scores) |
| Progressive disclosure (2-3 layers) | SAP Fiori XAI, Google Search | Natural language > visual map > explanation > raw ontology |
| Peer convergence (not conformity) | Prediction markets, Strava | "3 other experts independently flagged this" |
| Loss aversion via streaks | Duolingo | Contribution streaks with flexible forgiveness |
| First-spotter recognition | Wikipedia barnstars | "You were the first to identify this pattern" |
| Positive framing | Spotify Wrapped | "Your expertise shaped 142 outputs" not "you made 34 entries" |
| Anti-hairball visualization | Cambridge Intelligence | Abstracted radial view, not full graph |

---

## Sources

- [XTools - MediaWiki](https://www.mediawiki.org/wiki/XTools)
- [Signals Matter: Stack Overflow Impact Study](https://tuhat.helsinki.fi/ws/portalfiles/portal/161057963/3308558.3313583.pdf)
- [GitHub Contribution Visualizations](https://dev.to/github/your-github-year-in-review-10-fun-ways-to-visualize-your-contributions-392o)
- [Cambridge Intelligence - Graph Visualization UX](https://cambridge-intelligence.com/graph-visualization-ux-how-to-avoid-wrecking-your-graph-visualization/)
- [Knowledge Graphs in Practice - MIT/Tufts Study](https://arxiv.org/html/2304.01311v4)
- [Metaculus Prediction Resources](https://www.metaculus.com/help/prediction-resources/)
- [Brier.fyi - Prediction Market Scoring](https://brier.fyi/)
- [Good Judgment Project Forecasting Practices](https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/)
- [Nielsen Norman Group - Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- [SAP Fiori - Explainable AI](https://experience.sap.com/fiori-design-web/explainable-ai/)
- [ACM - Progressive Disclosure for Algorithmic Transparency](https://dl.acm.org/doi/abs/10.1145/3374218)
- [Nielsen Norman Group - Social Proof in UX](https://www.nngroup.com/articles/social-proof-ux/)
- [Strava Social Fitness Transformation](https://sensortower.com/blog/beyond-workouts-stravas-social-transformation-of-fitness-tracking)
- [Smashing Magazine - Designing Great Feedback Loops](https://www.smashingmagazine.com/2013/02/designing-great-feedback-loops/)
- [KCS Closed Loop Feedback](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/020/050)
- [Spotify Wrapped UX Psychology](https://medium.com/design-bootcamp/why-were-hooked-on-spotify-wrapped-the-perfect-blend-of-ux-and-psychology-b4aa06c9b81f)
- [Duolingo Streak Psychology](https://blog.duolingo.com/how-duolingo-streak-builds-habit/)
- [Wikipedia Barnstar Recognition](https://blog.reputationx.com/wikipedia-barnstar)
- [Wikipedia Thank Button](https://en.wikipedia.org/wiki/Help:Notifications/Thanks)
- [LinkedIn Notification Engineering](https://engineering.linkedin.com/blog/2018/05/concourse--generating-personalized-content-notifications-in-near)
- [Gamification Pitfalls](https://medium.com/design-bootcamp/when-and-how-is-gamification-harmful-8e37c076d4f5)
- [yFiles Knowledge Graph Visualization Guide](https://www.yfiles.com/resources/how-to/guide-to-visualizing-knowledge-graphs)
- [Userpilot Progressive Disclosure Examples](https://userpilot.com/blog/progressive-disclosure-examples/)
- [Wikipedia Editor Retention Study](https://www.higherlogic.com/blog/the-wikipedia-effect-why-people-volunteer/)
