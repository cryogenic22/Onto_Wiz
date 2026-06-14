# Deep UX Research: Gamification Patterns for Expert/SME Knowledge Capture Systems

## Table of Contents
1. [Duolingo-Style Gamification: What Translates to Expert Knowledge Capture](#1-duolingo-style-gamification-deep-mechanics--translation-to-expert-knowledge-capture)
2. [Expert Knowledge Elicitation UX Patterns](#2-expert-knowledge-elicitation-ux-patterns)
3. [Chat-Based Knowledge Capture](#3-chat-based-knowledge-capture)
4. [Gamification Anti-Patterns for Experts](#4-gamification-anti-patterns-for-experts)
5. [Session Pacing: Sub-7-Minute Expert Sessions](#5-session-pacing-sub-7-minute-expert-sessions)
6. [Real Examples: Systems That Gamify Expert Knowledge Capture](#6-real-examples-systems-that-gamify-expert-knowledge-capture)

---

## 1. Duolingo-Style Gamification: Deep Mechanics & Translation to Expert Knowledge Capture

### Duolingo's Core Mechanics (Deconstructed)

Duolingo's gamification is not a layer on top of learning -- it IS the product architecture. Every mechanic serves one behavioral goal: **complete one short lesson every day**.

#### Mechanic 1: Streaks (Loss Aversion Engine)
- **How it works:** A flame icon + day count displayed front-and-center. Consecutive days of completing at least one lesson. Streak freezes allow one missed day without breaking the chain.
- **Psychology:** Pure loss aversion. Users who maintain 7-day streaks are 3.6x more likely to stay long-term. Streak freezes reduced churn by 21%.
- **Widget integration:** Home screen widget acts as a persistent ambient reminder -- no notification needed.
- **Forgiveness design:** Streak freezes, streak repairs, and "streak society" (social reinforcement at 7+ days) prevent catastrophic dropout from a single miss.

#### Mechanic 2: XP (Variable Reward Currency)
- **How it works:** Points earned per lesson, with variable bonuses (perfect score, speed, difficulty). Time-limited XP boosts ("Double XP Weekend") create urgency.
- **Psychology:** Variable ratio reinforcement schedule (slot machine psychology). Users never know exactly what reward is coming.
- **Engagement data:** Limited-time XP boosts drive 50% surge in activity.

#### Mechanic 3: Leagues & Leaderboards (Social Competition)
- **How it works:** 10-tier weekly league system (Bronze through Diamond). ~30 users per league. Top 10 promote, bottom 5 demote. Resets weekly.
- **Psychology:** Manufactured social competition with small cohorts. Users who engage with leaderboards complete 40% more lessons/week.
- **Key design choice:** Small cohort size (30) makes competition feel achievable, not overwhelming.

#### Mechanic 4: Skill Tree / Path (Progress Visualization)
- **How it works:** Linear path with branching optional nodes. Each node = a lesson cluster. Crown/gold system shows mastery depth per node.
- **Psychology:** Makes invisible progress tangible. Progress bars within lessons + overall path position create dual-level progress feedback.

#### Mechanic 5: Micro-Lessons (Cognitive Chunking)
- **How it works:** 3-5 minute lessons with 10-15 exercises each. Single concept per lesson. Immediate feedback on every answer.
- **Psychology:** Aligns with cognitive load theory. Each lesson = one "chunk" within working memory limits (Miller's 7 +/- 2).

#### Mechanic 6: Hearts (Scarcity/Stakes)
- **How it works:** 5 hearts = 5 allowed mistakes before session ends. Hearts regenerate over time or via practice.
- **Psychology:** Creates real stakes per answer. Transforms passive consumption into active engagement with consequences.

### What Translates to Expert Knowledge Capture (and What Does NOT)

| Duolingo Mechanic | Translates? | Expert Knowledge Capture Equivalent |
|---|---|---|
| **Streaks** | YES (modified) | "Contribution streaks" -- consecutive days/weeks of knowledge contributions. But frame as "momentum" not "don't break the chain." Experts respond to momentum metaphors, not fear-of-loss framing. |
| **XP** | PARTIALLY | Replace with "Impact Score" or "Influence Metrics" -- how many decisions your knowledge informed, how many colleagues referenced your input. Experts care about impact, not arbitrary points. |
| **Leagues/Leaderboards** | NO for public ranking | YES for private calibration. Show experts how their predictions/assessments compare to outcomes. Calibration scores (like Good Judgment Project's Brier scores) appeal to expert identity. Public leaderboards feel juvenile. |
| **Skill Tree** | YES (reframed) | "Knowledge Map" -- visual representation of which domains the expert has contributed to, which areas remain uncovered. Appeals to completionist instinct AND shows organizational value. |
| **Micro-Lessons** | YES (inverted) | "Micro-contributions" -- 3-5 minute knowledge capture sessions. Single question/scenario per session. Immediate feedback on how contribution was used. |
| **Hearts** | NO | Scarcity/stakes mechanics feel game-like and patronizing. Replace with "confidence calibration" -- ask experts to rate their own confidence, then show calibration accuracy over time. |

### Key Translation Principle
Duolingo optimizes for **daily habit formation in novices**. Expert knowledge capture must optimize for **high-quality episodic contributions from time-scarce professionals**. The core insight to borrow is not the specific mechanics but Duolingo's **single-behavior focus** and **immediate feedback loops**.

---

## 2. Expert Knowledge Elicitation UX Patterns

### The Fundamental Challenge
Knowledge elicitation is recognized as "the bottleneck" in expert system development. The principal difficulty is eliciting **tacit knowledge** -- expertise that has been proceduralized to the point where experts struggle to explicitly describe their reasoning. Experts with more domain experience change their mental representations and preferred articulation methods.

### Pattern 1: Structured Expert Elicitation (SEE) Protocols

Five established protocols, each with distinct UX implications:

| Protocol | UX Model | Interaction Mode | Best For |
|---|---|---|---|
| **Sheffield Elicitation Framework (SHELF)** | Facilitator-guided probability elicitation with visual aids (probability wheels, chip-and-bin) | Individual then group | Quantitative uncertainty ranges |
| **Cooke's Classical Model** | Seed questions with known answers to calibrate expert accuracy, then weight responses by calibration | Individual, asynchronous | Weighting expert opinions by demonstrated accuracy |
| **IDEA (Investigate-Discuss-Estimate-Aggregate)** | Four-phase cycle: private research, group discussion, private re-estimation, mathematical aggregation | Hybrid individual/group | Reducing groupthink while enabling learning |
| **Modified Delphi** | Iterative anonymous rounds with statistical feedback between rounds | Asynchronous, anonymous | Consensus-building without social pressure |
| **RAND ExpertLens** | Online modified-Delphi with real-time aggregation and anonymous commenting | Fully online, asynchronous | Remote expert panels across time zones |

### Pattern 2: Think-Aloud / Protocol Analysis
- **How it works:** Expert narrates their reasoning while solving a representative problem. Recording is transcribed and converted to decision rules.
- **UX implementation:** Present the expert with a realistic scenario (case study, patient presentation, market analysis). Use progressive disclosure -- reveal information step by step, asking "what would you do next and why?" at each stage.
- **Visual design:** Split-screen with scenario on left, structured reasoning capture on right. Timeline visualization of decision points.

### Pattern 3: Card Sorting & Taxonomy Building
- **How it works:** Present concepts/entities as draggable cards. Ask expert to group, label, and explain groupings.
- **UX implementation:** Drag-and-drop interface with nested grouping capability. Allow experts to create their own category labels (not pre-defined). Capture not just the groupings but the rationale for each.
- **Real-world example:** The Ziva system uses card-sorting UX where domain experts first group examples by topic (atmosphere, food, service), then subdivide into specific attributes.

### Pattern 4: Scenario-Based Elicitation with Decomposition
- **How it works:** Break complex judgments into smaller, more tractable sub-questions (Fermi-ization, as practiced by superforecasters).
- **UX implementation:** Present the big question, then walk the expert through 3-5 sub-components. Each sub-component gets its own mini-assessment. System aggregates sub-assessments into overall judgment.
- **Why it works:** "Disaggregating or decomposing a variable makes the questions clearer and the elicitation easier for experts." Experts can apply rigorous reasoning to each sub-component rather than making holistic gut judgments.

### Pattern 5: Labeling-with-Justification
- **How it works:** Present the expert with a specific instance (a data point, case, scenario). Ask for a label/classification AND a justification.
- **UX implementation:** Show the instance with all relevant data. Provide a simple classification UI (radio buttons, slider, or forced-choice). Below classification, require a free-text or structured justification. Capture both the answer AND the reasoning as first-class data.
- **Key insight:** "If eliciting justification is difficult, data scientists would not get a reliable result." The justification interface must be low-friction.

### Design Principles Across All Patterns
1. **Questions must be clear and well-defined** with neutral wording
2. **Context on the modeling** must be provided -- experts need to understand how their input will be used
3. **Elicit only when uncertainty matters** -- don't waste expert time on questions where the answer doesn't affect outcomes
4. **Document everything** -- the elicitation questions, individual responses, aggregated results, rationales, and procedures

---

## 3. Chat-Based Knowledge Capture

### Why Conversational UI Works for Knowledge Capture

Conversational interfaces reduce the "form fatigue" that traditional knowledge capture suffers from. The key UX advantages:

1. **One-thing-at-a-time focus** -- reduces cognitive load compared to seeing a full form/survey
2. **Adaptive branching** -- conversation can follow the expert's expertise, skipping irrelevant areas
3. **Natural language capture** -- experts can articulate reasoning in their own words before structured extraction
4. **Social presence** -- even with a bot, conversational framing activates social communication norms (more detailed, more honest responses)

### Typeform's Conversational Model (Deconstructed)

Typeform's core innovation is "one question at a time" with transitions that feel like conversation rather than interrogation.

**Specific UX elements that reduce fatigue:**
- **Single-question viewport:** Only one question visible at a time. No scrolling through a long form.
- **Micro-break cues:** Subtle formatting/content pauses between topic transitions. These act as "rest stops" that reduce cognitive fatigue.
- **Logic jumps:** Conditional branching that personalizes the path. Experts only see questions relevant to their expertise.
- **Progress indication:** Percentage or step counter (but NOT a long progress bar that makes the survey look endless).
- **Visual design:** Custom fonts, colors, backgrounds, and transitions create a "calm, approachable environment that lowers resistance."

**Key finding:** Forms with fewer than 10 questions see the highest completion rates.

**Limitation for experts:** "For longer surveys, the one-question-at-a-time approach might feel tedious to respondents." Experienced users may prefer to see more context at once. **Implication: Allow experts to toggle between conversational and overview modes.**

### Chat-Based Capture: What Makes It "Fun" vs. "Survey Fatigue"

| Fun Pattern | Fatigue Pattern |
|---|---|
| Conversational tone that respects expertise | Corporate-speak or overly casual "Hey buddy!" tone |
| Adaptive follow-ups based on answers | Rigid question sequence regardless of answers |
| Immediate feedback on how input was valuable | Black hole -- input disappears with no acknowledgment |
| Expert can see their reasoning taking shape | No visible output or structure being built |
| Ability to elaborate or correct | Forced into rigid categories |
| Session feels like it "goes somewhere" | Circular or repetitive questioning |
| Clear time commitment upfront ("~4 minutes") | Unknown or deceptive time estimates |
| Moments of insight for the expert ("I hadn't thought about it that way") | Expert feels they're just being mined for data |

### Hybrid Chat + Structured Input Pattern (Recommended)

The most effective approach combines free-form conversational capture with structured data extraction:

1. **Opening:** Chat asks an open-ended question about the expert's reasoning on a specific scenario
2. **Capture:** Expert responds in natural language
3. **Structuring:** System extracts structured elements (entities, relationships, confidence levels) from the response
4. **Confirmation:** Chat presents the extracted structure back: "So you're saying X causes Y with high confidence, but Z is uncertain -- is that right?"
5. **Refinement:** Expert corrects/confirms the structured output
6. **Closure:** System shows the expert's contribution integrated into the larger knowledge structure

This pattern gives experts the freedom of natural expression while producing the structured data needed for knowledge systems.

---

## 4. Gamification Anti-Patterns for Experts

### The Core Problem
Gamification research consistently finds that **roughly half of users prefer non-gamified versions** of the same tool. For senior professionals, this split skews further against gamification. The risk is not just disengagement but active alienation.

### Anti-Pattern 1: Infantilizing Visual Language
- **What it looks like:** Cartoon characters, celebration animations, confetti, "Great job!" messages, emoji-heavy interfaces
- **Why it fails:** Senior professionals (PhDs, SVPs, MDs) have strong professional identity. Childish visual language signals "this tool doesn't understand who I am."
- **Alternative:** Clean, data-rich interfaces. Use visualization and information density as the "reward." Think Bloomberg Terminal aesthetics, not Candy Crush.

### Anti-Pattern 2: Public Leaderboards
- **What it looks like:** Ranking experts against each other on contribution volume, speed, or "points"
- **Why it fails:** Creates perverse incentives (quantity over quality). Senior people have reputation to protect -- being publicly "ranked" feels risky. Competition between peers can damage collaborative relationships.
- **Alternative:** Private calibration dashboards showing personal accuracy over time. Benchmarking against aggregated (anonymous) peer performance, not individual ranking.

### Anti-Pattern 3: Trivial Badges and Achievements
- **What it looks like:** "Knowledge Champion!" badge, "First Contribution!" achievement, bronze/silver/gold tiers
- **Why it fails:** Pew Research found gamification is "likely to be perceived as an insult to intelligence." Badges that anyone can earn don't signal competence. Achievement systems designed for consumer apps feel cheap in professional contexts.
- **Alternative:** Recognition tied to real outcomes: "Your assessment of X risk was cited in 3 board-level decisions." Impact-based recognition, not participation trophies.

### Anti-Pattern 4: Mandatory Participation
- **What it looks like:** Required gamified training, mandatory "fun" engagement, gamification as compliance mechanism
- **Why it fails:** "Making participation a requirement is unlikely to make coworkers happy about joining in." Senior professionals value autonomy above almost everything else (Self-Determination Theory). Forced play is the opposite of play.
- **Alternative:** Opt-in engagement with clear value proposition. Let experts choose when, how much, and on what topics they contribute.

### Anti-Pattern 5: Extrinsic Rewards Crowding Out Intrinsic Motivation
- **What it looks like:** Points, prizes, or monetary rewards for knowledge contributions
- **Why it fails:** "If extrinsic rewards such as prizes or money are large enough that they supersede intrinsic motivation, then all the unintended behaviors are likely to occur and the benefits of gamification are lost." Experts contribute knowledge because they care about truth, impact, and professional legacy. External rewards can actually reduce willingness to contribute.
- **Alternative:** Amplify intrinsic motivators: show impact of contributions, provide intellectual challenge, create opportunities for peer recognition (not system-assigned badges).

### Anti-Pattern 6: Oversimplified Feedback
- **What it looks like:** "Correct!" / "Incorrect!" binary feedback, green checkmarks and red X's
- **Why it fails:** Experts operate in domains of uncertainty and nuance. Binary feedback ignores the complexity they deal with daily.
- **Alternative:** Probabilistic feedback with calibration. Show how confident they were vs. how accurate they were. Provide Brier scores or calibration curves over time. This appeals to the expert identity -- "I want to be well-calibrated" is a more compelling motivation than "I want to be correct."

### What DOES Work for Senior Professionals

Based on Self-Determination Theory (SDT), the three core psychological needs:

1. **Autonomy:** Let experts choose what to contribute on, when, and how much. No forced paths.
2. **Competence/Mastery:** Show calibration accuracy over time. Provide genuinely challenging scenarios. Let them see themselves improving at structured reasoning.
3. **Relatedness:** Show how their contributions connect to real outcomes and real colleagues' work. Community of practice, not a game lobby.

**The Microsoft Case Study:** Microsoft's Director of Test, Ross Smith, created a successful gamified quality assurance system using zero extrinsic rewards -- purely intrinsic motivation (challenge, social connection, meaning). This demonstrates that gamification for experts must lean entirely on intrinsic motivators.

---

## 5. Session Pacing: Sub-7-Minute Expert Sessions

### Evidence Base for Session Length

- Cognitive load research places the optimal microlearning session at **5-15 minutes**
- Sessions under 5 minutes "may lack sufficient depth for meaningful learning"
- Average adult focused attention span is 10-18 minutes, but for **knowledge capture** (production, not consumption), fatigue sets in faster
- For expert knowledge elicitation specifically, **5-7 minutes per session** is the sweet spot: long enough for a meaningful contribution, short enough to fit between meetings

### Micro-Session Architecture (Recommended 6-Minute Flow)

```
MINUTE 0:00-0:30  |  PRIME (30 sec)
                  |  - Show the scenario/question with all relevant context
                  |  - Display time estimate: "~5 minutes"
                  |  - Single-screen context load (no scrolling)
                  |
MINUTE 0:30-1:30  |  ORIENT (60 sec)
                  |  - Expert reads scenario
                  |  - System asks one framing question: "What's your initial read?"
                  |  - Quick-select or slider for initial assessment
                  |
MINUTE 1:30-3:30  |  ELICIT (120 sec)
                  |  - 2-3 targeted follow-up questions based on initial response
                  |  - Mix of structured (slider, multiple choice) and free-text
                  |  - Progressive disclosure: each question builds on prior answers
                  |  - This is the core knowledge capture window
                  |
MINUTE 3:30-5:00  |  STRUCTURE (90 sec)
                  |  - System shows extracted reasoning as structured representation
                  |  - "Here's what I captured -- does this look right?"
                  |  - Expert confirms, corrects, or elaborates
                  |  - Drag-and-drop or inline editing for corrections
                  |
MINUTE 5:00-5:30  |  CALIBRATE (30 sec)
                  |  - "How confident are you in this assessment?" (0-100 slider)
                  |  - "What would change your mind?" (optional free-text)
                  |
MINUTE 5:30-6:00  |  CLOSE (30 sec)
                  |  - Show impact: "This will inform [specific decision/model]"
                  |  - Show cumulative contribution: "You've assessed 12 scenarios this month"
                  |  - Optional: "Want to do one more?" (never pressure)
```

### Pacing Principles

1. **Front-load context, don't drip-feed it.** Experts can process complex scenarios quickly. Give them everything upfront rather than revealing information slowly (which feels condescending).

2. **Respect the expert's processing speed.** Don't enforce time delays or animation speeds. Let experts move through at their own pace. Some will finish in 3 minutes, some in 7. Both are fine.

3. **Use structured inputs to accelerate capture.** Sliders, forced-choice, and matrix inputs are faster than free-text for structured data. Reserve free-text for reasoning/justification only.

4. **Single-concept sessions.** Each session = one scenario, one assessment, one reasoning chain. Never bundle multiple unrelated questions.

5. **No "save and continue later."** Sessions should be atomic -- completable in one sitting. If an expert is interrupted, they restart fresh rather than resuming a half-done session (stale context degrades quality).

6. **Show the clock.** A subtle progress indicator (not a countdown timer, which creates anxiety) that shows "Step 3 of 5" or a progress bar. Experts want to know how much is left.

7. **End with impact, not celebration.** Instead of "Congratulations!" show "Your input on [topic] will be incorporated into [specific model/decision]. 3 colleagues have assessed this same scenario -- your perspective adds to the aggregate."

### Chunking Strategy (Cognitive Load Theory Applied)

- **Miller's Law:** Working memory holds 7 +/- 2 items. Each question/interaction should involve no more than 5-7 pieces of information.
- **Natural breakpoints:** Chunk sessions around natural reasoning stages: (1) situation assessment, (2) hypothesis formation, (3) evidence weighting, (4) confidence calibration.
- **Spaced repetition for expertise:** If capturing knowledge over time, space sessions to revisit prior assessments when new information emerges. Show experts their previous assessment alongside new data and ask for updates. This is both better for knowledge capture quality AND more engaging.

---

## 6. Real Examples: Systems That Gamify Expert Knowledge Capture

### Example 1: Metaculus (Forecasting Platform)
- **What it is:** A reputation-based prediction platform where experts assign probabilities to future events. Not a prediction market (no money at stake).
- **Expert-appropriate gamification:**
  - **Calibration scoring:** Experts earn reputation based on Brier score accuracy over hundreds of predictions. This is meaningful -- it measures genuine forecasting skill.
  - **Track record visualization:** Personal calibration curves showing predicted probability vs. actual outcome frequency. Experts can see if they're systematically overconfident or underconfident.
  - **Community prediction aggregation:** Individual forecasts combine into a crowd estimate. Experts can see where their view diverges from consensus.
  - **Question decomposition:** Complex forecasting questions can be broken into sub-questions, supporting the Fermi decomposition approach.
- **UX design notes:** Clean, data-rich interface. No cartoon characters or celebrations. Progress is measured in prediction accuracy, not points.
- **Key lesson:** Reputation earned through demonstrated calibration accuracy is the most expert-appropriate "gamification." It aligns with how experts already think about professional credibility.

### Example 2: Good Judgment Project / Good Judgment Open
- **What it is:** The research project that identified "superforecasters" -- people in the top 1-2% of forecasting accuracy.
- **Expert-appropriate gamification:**
  - **Calibration-as-game:** Superforecasters are scored on Brier scores. Their remarkable precision (accuracy degrades when rounding predictions to nearest 5%) becomes a source of professional pride.
  - **Seed questions:** Cooke's Classical Model uses questions with known answers to calibrate expert accuracy, then weights their judgments on uncertain questions proportionally. Experts find this intellectually satisfying -- your influence scales with demonstrated accuracy.
  - **Fermi decomposition interface:** System encourages breaking big questions into sub-components, finding base rates, then adjusting. This structured reasoning process itself is engaging for analytically-minded experts.
- **Key lesson:** The "game" for experts is improving their own calibration. Superforecasters were 30% more accurate than intelligence analysts with classified information -- not because of better data, but better reasoning processes. Showing experts they can improve their reasoning is deeply motivating.

### Example 3: RAND ExpertLens
- **What it is:** An online modified-Delphi tool for structured expert elicitation.
- **Expert-appropriate gamification:**
  - **Iterative refinement:** Experts see anonymized group results between rounds and can update their estimates. This creates a natural "am I right?" engagement loop.
  - **Anonymous but social:** Experts can see and respond to anonymized qualitative comments from other panelists. Social learning without social pressure.
  - **Asynchronous flexibility:** Participants reported the online format was "extremely efficient and conducive to participation across time zones."
- **Key lesson:** The Delphi structure itself is a form of gamification -- iterative rounds with feedback create a natural engagement loop. Experts are motivated to refine their estimates when they see how others assessed the same question.

### Example 4: Prediction Markets (Polymarket, Manifold)
- **What it is:** Markets where participants buy/sell contracts on future events, with prices reflecting crowd probability estimates.
- **Expert-appropriate gamification:**
  - **Skin in the game:** Real or play-money stakes create genuine engagement (though this can also be an anti-pattern for some professional contexts).
  - **Portfolio performance:** Track record of profitable predictions serves as a meaningful performance metric.
  - **Market-making:** Experts can create new questions/markets, giving them agency over what knowledge is captured.
- **Anti-pattern warning:** Monetary incentives can attract noise traders and crowd out thoughtful expert engagement. Reputation-based systems (Metaculus) often produce higher-quality expert inputs than money-based markets.

### Example 5: Clinical Decision Support Systems (CDSS)
- **What it is:** Systems like DXplain, CaDet, and Body Interact that capture and apply clinical reasoning.
- **Expert-appropriate gamification:**
  - **Body Interact:** Virtual patient simulations where clinicians make real-time diagnostic and treatment decisions. Risk-free practice with realistic scenarios.
  - **Gamified Decision-Making Cards (DMCs):** A study found that gamified clinical reasoning exercises "improved clinical decision-making confidence and learning motivation" in medical professionals.
  - **Expert-augmented ML:** Systems that combine machine learning predictions with expert knowledge (e.g., ICU mortality prediction) show experts that their knowledge measurably improves algorithmic performance. This "your expertise made the model better" feedback is profoundly motivating.
- **Key lesson:** Experts are most engaged when they can see their knowledge having measurable impact on real decisions. Showing "your assessment improved model accuracy by X%" is more motivating than any badge.

### Example 6: Welphi & eDelphi (Delphi Method Software)
- **What it is:** Purpose-built software for conducting Delphi studies with expert panels.
- **Expert-appropriate gamification:**
  - **Anonymity-preserved iteration:** Experts submit independently, see aggregated results, then re-assess. The "gap between my estimate and the group" creates natural curiosity and engagement.
  - **Automated feedback loops:** Statistical summaries (means, medians, quartile ranges) presented between rounds give experts quantitative feedback on where they stand.
  - **Priority management (HalnyX):** Novel UX that manages and prioritizes expert involvement, so they can "focus on priority tasks whenever they revisit the study."
- **Key lesson:** The iterative reveal pattern (submit, see group, revise) is inherently engaging for experts because it creates an intellectual puzzle: "Why does the group see this differently than I do?"

### Example 7: Schacht & Maedche Knowledge Management System (2015)
- **What it is:** A gamified in-house knowledge management system studied in enterprise settings.
- **Findings:**
  - Achievement-oriented features (points, status) work when they "indicate competence to others" -- but only within a professional community where the status is meaningful.
  - Features that reward evaluating others' contributions (not just creating your own) drove higher engagement.
  - The key insight: **gamify the evaluation of knowledge, not just the contribution**. Asking experts to assess and improve each other's contributions is more engaging than asking them to create from scratch.

---

## Synthesis: Design Principles for Expert Knowledge Capture Gamification

### The Expert Motivation Stack (What Actually Drives Senior Professionals)

```
LEVEL 4 (Highest)  |  LEGACY & IMPACT
                   |  "My expertise shaped real decisions"
                   |  "I built something that outlasts me"
                   |
LEVEL 3            |  CALIBRATION & MASTERY
                   |  "I'm getting better at structured reasoning"
                   |  "My predictions are well-calibrated"
                   |
LEVEL 2            |  PEER RECOGNITION & COMMUNITY
                   |  "Other experts value my perspective"
                   |  "I'm part of a community of practice"
                   |
LEVEL 1 (Base)     |  AUTONOMY & RESPECT
                   |  "I choose when and how to contribute"
                   |  "The system respects my time and intelligence"
```

### The Golden Rules

1. **Replace points with impact metrics.** Show experts how their knowledge was used, not how many points they earned.

2. **Replace leaderboards with calibration dashboards.** Private accuracy tracking over time is compelling; public ranking is alienating.

3. **Replace badges with contribution maps.** Visual representations of which knowledge domains the expert has contributed to, showing coverage and depth.

4. **Replace streaks with momentum indicators.** "You've contributed to 8 assessments this month, covering 3 new topic areas" is better than "Day 15 streak!"

5. **Replace celebrations with evidence of impact.** "Your risk assessment of compound X was cited in the Phase II decision" beats "Congratulations! You earned the Gold Contributor badge!"

6. **Make the structured reasoning process itself rewarding.** Scenario decomposition, hypothesis testing, and calibration tracking are inherently satisfying for analytical minds. The "game" is becoming a better reasoner, not collecting rewards.

7. **Design for episodic excellence, not daily habit.** Unlike Duolingo (which needs daily returns), expert knowledge capture needs high-quality periodic contributions. Optimize for quality per session, not session frequency.

8. **Show the knowledge structure being built.** Experts should see their contributions assembling into a larger knowledge graph, ontology, or decision model. Watching a complex structure emerge from individual contributions is deeply satisfying -- like watching a puzzle complete.

---

## Sources

- [Duolingo Gamification Secrets - Orizon](https://www.orizon.co/blog/duolingos-gamification-secrets)
- [Duolingo Streak System Detailed Breakdown - Premjit Singha](https://medium.com/@salamprem49/duolingo-streak-system-detailed-breakdown-design-flow-886f591c953f)
- [Duolingo's Gamified Growth - Medium](https://medium.com/@productbrief/duolingos-gamified-growth-how-a-green-owl-turned-language-learning-into-a-14-billion-habit-d47d9fa30a77)
- [Duolingo Case Study 2025 - Young Urban Project](https://www.youngurbanproject.com/duolingo-case-study/)
- [Duolingo Gamification Case Study - Trophy](https://trophy.so/blog/duolingo-gamification-case-study)
- [How to Design Like Duolingo - UIKits](https://www.uinkits.com/blog-post/how-to-design-like-duolingo-gamification-engagement)
- [Duolingo's Shallow Learning Trap - DEV Community](https://dev.to/yaptech/duolingos-shallow-learning-trap-gamified-streaks-harmful-habits-4134)
- [Knowledge Elicitation Methods, Tools and Techniques - Shadbolt & Smart](https://www.semanticscholar.org/paper/Knowledge-Elicitation:-Methods,-Tools-and-Shadbolt-Smart/505753e9af30a73212f1775decd8d3c7ff665c99)
- [Structured Expert Elicitation Protocols - NCBI](https://www.ncbi.nlm.nih.gov/books/NBK571059/)
- [ISPOR Task Force on Structured Expert Elicitation - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1098301524028432)
- [Facilitating Knowledge Sharing from Domain Experts - ACM](https://dl.acm.org/doi/fullHtml/10.1145/3397481.3450637)
- [Pew Research on Gamification Experts](https://www.pewresearch.org/internet/wp-content/uploads/sites/9/media/Files/Reports/2012/PIP_Future_of_Internet_2012_Gamification.pdf)
- [Gamification Side Effects and Ethics - Springer](https://link.springer.com/article/10.1007/s11023-024-09661-5)
- [Typeform Conversational Forms - Product Overview](https://www.typeform.com/product-overview/)
- [Typeform HX Design Philosophy - Salesflare Blog](https://blog.salesflare.com/iconic-product-typeform-e17f49419c56)
- [Reduce Drop-Off in Typeform - Sivo Insights](https://mrx.sivoinsights.com/blog/how-to-reduce-drop-off-in-typeform-surveys-with-better-section-planning)
- [Metaculus Platform](https://www.metaculus.com/)
- [Metaculus vs Markets](https://www.metaculus.com/notebooks/38198/metaculus-and-markets-whats-the-difference/)
- [Why I Reject the Comparison of Metaculus to Prediction Markets - Medium](https://metaculus.medium.com/why-i-reject-the-comparison-of-metaculus-to-prediction-markets-4175553bcbb8)
- [Good Judgment Project - Wikipedia](https://en.wikipedia.org/wiki/The_Good_Judgment_Project)
- [Good Judgment - Superforecasting](https://goodjudgment.com/about/the-science-of-superforecasting/)
- [Good Judgment Open](https://www.gjopen.com/)
- [Good Forecasting Practices from GJP - AI Impacts](https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project-an-accompanying-blog-post/)
- [RAND ExpertLens](https://www.rand.org/pubs/tools/expertlens.html)
- [Welphi Delphi Method Software](https://www.welphi.com/delphi-method-survey-software/)
- [eDelphi Platform](https://www.edelphi.org/)
- [Prediction Market-Based Gamified Knowledge Sharing - ResearchGate](https://www.researchgate.net/publication/335209173_A_Prediction_Market-Based_Gamified_Approach_to_Enhance_Knowledge_Sharing_in_Organizations)
- [Expert-Augmented CDSS - Springer](https://link.springer.com/article/10.1007/s13218-023-00808-7)
- [Gamification and Medical Decision Making - BMC Medical Education](https://bmcmededuc.biomedcentral.com/articles/10.1186/s12909-023-04808-x)
- [Incentive Design and Gamification for Knowledge Management - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0148296319300992)
- [Enterprise Gamification Top 10 - Yu-kai Chou](https://yukaichou.com/gamification-examples/top-10-enterprise-gamification-cases-employees-productive/)
- [Beyond Gamification Through Playfulness - SHRM](https://www.shrm.org/enterprise-solutions/insights/beyond-gamification-unlock-true-engagement-through)
- [Gamification Intrinsic Motivation and Task Performance - Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/0144929X.2023.2297280)
- [Cognitive Load Theory and Microlearning - Learning Guild](https://www.learningguild.com/articles/designing-microlearning-that-works-applying-cognitive-load-theory-in-practice)
- [Microlearning in 2025 - eLearning Industry](https://elearningindustry.com/microlearning-in-2025-the-basics-science-trends-and-more)
- [Adaptive Microlearning - Nature Scientific Reports](https://www.nature.com/articles/s41598-024-77122-1)
- [Dashboard Design UX Best Practices - UXPin](https://www.uxpin.com/studio/blog/dashboard-design-principles/)
- [Impact Mapping](https://www.impactmapping.org/)
