"""
Context Assembler — the main entry point for knowledge orchestration.

Orchestrates: query + agent_type + budget -> ContextPackage

Priority ordering for token budget:
  guardrails (never cut) > patterns (by score) > jargon > few-shots (cut first)
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.core.models import ArtifactStatus, Guardrail, JudgmentPattern
from src.core.stores import JudgmentStore
from src.core.semantic_store import SemanticStore
from src.core.graph_store import GraphStore

from .models import ContextPackage
from .few_shot_store import FewShotStore

logger = logging.getLogger(__name__)


class ContextAssembler:
    """
    Assembles a ContextPackage for an agent query within a token budget.

    Steps:
    1. Parse query, resolve terms via SemanticStore.resolve_to_canonical()
    2. Find patterns via JudgmentStore.find_matching_patterns()
    3. Get guardrails from JudgmentStore.get_active_guardrails()
    4. Get few-shots from FewShotStore.find_by_tags()
    5. Build jargon map from SemanticStore.get_all_variants()
    6. Pack into ContextPackage within token budget
    """

    def __init__(
        self,
        judgment_store: JudgmentStore,
        semantic_store: SemanticStore,
        graph_store: Optional[GraphStore] = None,
        few_shot_store: Optional[FewShotStore] = None,
    ) -> None:
        self._judgment_store = judgment_store
        self._semantic_store = semantic_store
        self._graph_store = graph_store
        self._few_shot_store = few_shot_store

    def assemble(
        self,
        query: str,
        agent_type: str = "general",
        max_tokens: int = 4000,
    ) -> ContextPackage:
        """Assemble a ContextPackage for the given query."""
        if max_tokens < 100:
            raise ValueError("max_tokens must be >= 100")

        # 1. Resolve tags from query
        tags = self._resolve_tags(query)

        # 2. Build context dict for pattern matching
        context = {"agent_type": agent_type}
        for key, values in tags.items():
            if values:
                context[key] = values[0]

        # 3. Gather raw signals from query words
        query_terms = [t.strip() for t in query.replace(",", " ").split() if t.strip()]

        # 4. Find matching patterns
        pattern_matches = self._judgment_store.find_matching_patterns(
            signals=query_terms,
            context=context,
            min_score=0.1,
        )
        patterns_data = [
            self._pattern_to_dict(p, score) for p, score in pattern_matches
        ]

        # 5. Get active guardrails (never cut)
        guardrails = self._judgment_store.get_active_guardrails()
        guardrails_data = [self._guardrail_to_dict(g) for g in guardrails]

        # 6. Get few-shot examples
        few_shots_data: List[Dict[str, Any]] = []
        if self._few_shot_store:
            if tags:
                examples = self._few_shot_store.find_by_tags(tags, limit=5)
            else:
                examples = []
            few_shots_data = [
                {
                    "id": ex.id,
                    "task_type": ex.task_type,
                    "input": ex.input_text,
                    "output": ex.output_text,
                }
                for ex in examples
            ]

        # 7. Build jargon map
        jargon = self._build_jargon_map(query_terms)

        # 8. Build entity context from graph
        entity_context = self._build_entity_context(query_terms)

        # 9. Pack within token budget using priority ordering
        package = self._pack_within_budget(
            query=query,
            patterns=patterns_data,
            guardrails=guardrails_data,
            few_shots=few_shots_data,
            jargon=jargon,
            entity_context=entity_context,
            tags_matched=tags,
            max_tokens=max_tokens,
            agent_type=agent_type,
        )
        return package

    # ------------------------------------------------------------------
    # Tag resolution
    # ------------------------------------------------------------------

    def _resolve_tags(self, query: str) -> Dict[str, List[str]]:
        """Extract tags from query by resolving terms via SemanticStore."""
        tags: Dict[str, List[str]] = {}
        words = query.replace(",", " ").split()
        resolved_terms: List[str] = []

        for word in words:
            word = word.strip()
            if not word:
                continue
            canonical = self._semantic_store.resolve_to_canonical(word)
            if canonical:
                resolved_terms.append(canonical.term)
                # Build tag from canonical's domains
                for domain in canonical.domains:
                    domain_key = domain.value
                    if domain_key not in tags:
                        tags[domain_key] = []
                    if canonical.term not in tags[domain_key]:
                        tags[domain_key].append(canonical.term)

        if resolved_terms:
            tags["resolved_terms"] = resolved_terms

        return tags

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def _pattern_to_dict(
        self, pattern: JudgmentPattern, score: float
    ) -> Dict[str, Any]:
        return {
            "id": pattern.id,
            "signals": pattern.applies_when_signals,
            "context": pattern.applies_when_context,
            "drivers": [
                {"driver": d.driver, "confidence": d.prior_confidence}
                for d in pattern.typical_drivers
            ],
            "disallowed_drivers": pattern.disallowed_drivers,
            "match_score": round(score, 3),
        }

    def _guardrail_to_dict(self, guardrail: Guardrail) -> Dict[str, Any]:
        return {
            "id": guardrail.id,
            "blocks_action_types": guardrail.blocks_action_types,
            "blocks_drivers": guardrail.blocks_drivers,
            "unless_evidence": guardrail.unless_evidence,
            "applies_to_personas": guardrail.applies_to_personas,
        }

    # ------------------------------------------------------------------
    # Jargon and entity context
    # ------------------------------------------------------------------

    def _build_jargon_map(self, query_terms: List[str]) -> Dict[str, str]:
        """Build a jargon map: canonical_term -> comma-separated variants."""
        jargon: Dict[str, str] = {}
        seen_canonicals: set = set()

        for term in query_terms:
            canonical = self._semantic_store.resolve_to_canonical(term)
            if canonical and canonical.id not in seen_canonicals:
                seen_canonicals.add(canonical.id)
                variants = self._semantic_store.get_all_variants(canonical.id)
                if variants:
                    jargon[canonical.term] = ", ".join(variants)

        return jargon

    def _build_entity_context(self, query_terms: List[str]) -> Dict[str, Any]:
        """Build entity context from GraphStore if available."""
        if not self._graph_store:
            return {}

        entity_context: Dict[str, Any] = {}
        for term in query_terms:
            node = self._graph_store.get_node_by_label(term)
            if node:
                entity_context[node.label] = {
                    "type": node.type.value,
                    "properties": node.properties,
                    "confidence": node.confidence,
                }
        return entity_context

    # ------------------------------------------------------------------
    # Token budgeting
    # ------------------------------------------------------------------

    def _estimate_tokens(self, obj: Any) -> int:
        """Estimate token count: len(json.dumps(obj)) // 4."""
        try:
            return len(json.dumps(obj, default=str)) // 4
        except (TypeError, ValueError):
            return 0

    def _pack_within_budget(
        self,
        query: str,
        patterns: List[Dict[str, Any]],
        guardrails: List[Dict[str, Any]],
        few_shots: List[Dict[str, Any]],
        jargon: Dict[str, str],
        entity_context: Dict[str, Any],
        tags_matched: Dict[str, List[str]],
        max_tokens: int,
        agent_type: str,
    ) -> ContextPackage:
        """
        Pack context into ContextPackage within token budget.

        Priority: guardrails (never cut) > patterns (by score) > jargon > few-shots (cut first)
        """
        # Start with guardrails — these are never cut
        base = {
            "query": query,
            "guardrails": guardrails,
            "tags_matched": tags_matched,
            "metadata": {"agent_type": agent_type},
        }
        used = self._estimate_tokens(base)
        remaining = max_tokens - used

        # Add patterns (already sorted by score from JudgmentStore)
        included_patterns: List[Dict[str, Any]] = []
        for p in patterns:
            cost = self._estimate_tokens(p)
            if cost <= remaining:
                included_patterns.append(p)
                remaining -= cost

        # Add jargon
        included_jargon: Dict[str, str] = {}
        for key, val in jargon.items():
            cost = self._estimate_tokens({key: val})
            if cost <= remaining:
                included_jargon[key] = val
                remaining -= cost

        # Add entity context
        included_entities: Dict[str, Any] = {}
        for key, val in entity_context.items():
            cost = self._estimate_tokens({key: val})
            if cost <= remaining:
                included_entities[key] = val
                remaining -= cost

        # Add few-shots last (cut first when budget is tight)
        included_few_shots: List[Dict[str, Any]] = []
        for fs in few_shots:
            cost = self._estimate_tokens(fs)
            if cost <= remaining:
                included_few_shots.append(fs)
                remaining -= cost

        package = ContextPackage(
            query=query,
            patterns=included_patterns,
            guardrails=guardrails,
            few_shots=included_few_shots,
            jargon_context=included_jargon,
            entity_context=included_entities,
            tags_matched=tags_matched,
            max_tokens=max_tokens,
            metadata={"agent_type": agent_type},
        )
        package.token_estimate = package.estimate_tokens()
        return package
