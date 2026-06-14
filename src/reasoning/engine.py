from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.stores import JudgmentStore

@dataclass
class ScenarioContext:
    account_id: str
    brand_id: str

@dataclass
class ReasoningResponse:
    confidence_score: float
    identified_risks: List[str]
    supporting_evidence_tags: List[str]
    verdict: str

class ReasoningEngine:
    LEARNED_PRIORITY_BASE: int = 50

    def __init__(
        self,
        ontology: Dict[str, Any],
        data: Dict[str, Any],
        judgment_store: Optional["JudgmentStore"] = None,
    ):
        self.ontology = ontology
        self.data_store = data
        self.judgment_store = judgment_store

    def reason(self, question: str, context: ScenarioContext) -> ReasoningResponse:
        """
        Main entry point for reasoning.
        1. Filters signals by context.
        2. Evaluates ontology rules dynamically.
        3. Returns the highest priority verdict.
        """
        active_tags, signal_scores, evidence_map = self._filter_signals(context)
        winning_rule = self._find_winning_rule(active_tags)

        if winning_rule is None:
            return ReasoningResponse(0.1, [], [], "No significant risks detected.")

        return self._build_response(winning_rule, signal_scores, active_tags)

    def _filter_signals(
        self, context: ScenarioContext
    ) -> Tuple[Set[str], List[float], Dict[str, list]]:
        """Retrieve signals for context and extract tags, scores, evidence."""
        all_signals = self.data_store.get("market_context", {}).get("dark_data_signals", [])
        signals = [s for s in all_signals if s.get("account_id") == context.account_id]

        active_tags: Set[str] = set()
        signal_scores: List[float] = []
        evidence_map: Dict[str, list] = {}

        for s in signals:
            for tag in s.get("tags", []):
                active_tags.add(tag)
                if tag not in evidence_map:
                    evidence_map[tag] = []
                evidence_map[tag].append(s)
            signal_scores.append(s.get("confidence", 0.5))

        return active_tags, signal_scores, evidence_map

    def _pattern_to_rule(self, pattern, score: float) -> Dict[str, Any]:
        """Convert a JudgmentPattern + match_score into a rule dict.

        The synthetic rule uses the pattern's signals as tag_match conditions
        and derives priority from ``score * LEARNED_PRIORITY_BASE``.
        A ``_source`` marker lets ``_build_response`` distinguish learned
        rules from static YAML rules.
        """
        conditions = []
        if pattern.applies_when_signals:
            conditions.append({
                "name": "learned_signals",
                "pattern": "tag_match",
                "args": list(pattern.applies_when_signals),
            })

        # Build consequence from driver data
        drivers = pattern.typical_drivers
        risk = drivers[0].driver if drivers else "Risk:Learned"
        verdict = f"Learned: {risk}"

        return {
            "id": pattern.id,
            "priority": score * self.LEARNED_PRIORITY_BASE,
            "conditions": conditions,
            "logic": "learned_signals",
            "consequence": {
                "risk": risk,
                "verdict": verdict,
                "confidence_modifier": "average",
            },
            "_source": "judgment_store",
            "_pattern": pattern,
            "_score": score,
        }

    def _find_winning_rule(self, active_tags: Set[str]) -> Optional[Dict[str, Any]]:
        """Evaluate ontology rules and return the highest-priority match.

        When a ``judgment_store`` is present, learned patterns are converted
        to synthetic rules via ``_pattern_to_rule`` and compete alongside
        static YAML rules in a single priority-ranked evaluation.
        """
        ontology_body = self.ontology.get("ontology", self.ontology)
        rules = list(ontology_body.get("inference_rules", []))

        # Merge learned patterns from JudgmentStore
        if self.judgment_store is not None:
            matched = self.judgment_store.find_matching_patterns(
                signals=list(active_tags),
                context={},
                min_score=0.3,
            )
            for pattern, score in matched:
                rules.append(self._pattern_to_rule(pattern, score))

        rules = sorted(rules, key=lambda x: x.get("priority", 0), reverse=True)

        for rule in rules:
            if self._check_rule_conditions(rule, active_tags):
                return rule
        return None

    def _check_rule_conditions(
        self, rule: Dict[str, Any], active_tags: Set[str]
    ) -> bool:
        """Evaluate a single rule's conditions against active tags."""
        conditions = rule.get("conditions", [])
        logic = rule.get("logic", "AND")

        cond_results: Dict[str, bool] = {}
        for cond in conditions:
            c_name = cond.get("name")
            c_pattern = cond.get("pattern")
            c_args = cond.get("args", [])

            match = False
            if c_pattern == "tag_match":
                for arg in c_args:
                    if arg in active_tags:
                        match = True
                        break
            cond_results[c_name] = match

        required_conds = [x.strip() for x in logic.split(" AND ")]
        return all(cond_results.get(rc, False) for rc in required_conds)

    def _build_response(
        self,
        winning_rule: Dict[str, Any],
        signal_scores: List[float],
        active_tags: Set[str],
    ) -> ReasoningResponse:
        """Construct a ReasoningResponse from the winning rule.

        For learned rules (``_source == "judgment_store"``), confidence is
        derived from the pattern's match score blended with signal scores,
        and risks are enriched with driver attributions.
        """
        cons = winning_rule.get("consequence", {})
        is_learned = winning_rule.get("_source") == "judgment_store"

        # --- confidence ---
        modifier = cons.get("confidence_modifier", "average")
        final_score = 0.5
        if is_learned:
            match_score = winning_rule.get("_score", 0.5)
            signal_avg = (sum(signal_scores) / len(signal_scores)) if signal_scores else 0.5
            final_score = 0.6 * match_score + 0.4 * signal_avg
        elif signal_scores:
            if modifier == "max":
                final_score = max(signal_scores)
            elif modifier == "average":
                final_score = sum(signal_scores) / len(signal_scores)

        # --- risks ---
        if is_learned:
            pattern = winning_rule.get("_pattern")
            risks = [d.driver for d in pattern.typical_drivers] if pattern and pattern.typical_drivers else [cons.get("risk")]
        else:
            risks = [cons.get("risk")]

        # --- evidence tags ---
        used_evidence_tags: List[str] = []
        for cond in winning_rule.get("conditions", []):
            for arg in cond.get("args", []):
                if arg in active_tags:
                    used_evidence_tags.append(arg)

        return ReasoningResponse(
            confidence_score=final_score,
            identified_risks=risks,
            supporting_evidence_tags=used_evidence_tags,
            verdict=cons.get("verdict"),
        )
